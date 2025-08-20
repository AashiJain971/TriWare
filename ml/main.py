"""
Smart Triage ML Service - Main Application

FastAPI service providing AI-powered triage risk assessment,
symptom classification, and clinical decision support.
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
import structlog
import asyncio
import numpy as np
from datetime import datetime
import os

# ML Components
from src.inference.triage_classifier import TriageClassifier
from src.inference.symptom_analyzer import SymptomAnalyzer
from src.inference.red_flag_detector import RedFlagDetector
from src.features.feature_engine import FeatureEngine
from src.evaluation.model_monitor import ModelMonitor

# Utilities
from src.utils.config import settings
from src.utils.logging import setup_logging
from src.utils.metrics import MetricsCollector

# Setup logging
setup_logging()
logger = structlog.get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Smart Triage ML Service",
    description="AI-powered triage risk assessment and clinical decision support",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
triage_classifier = None
symptom_analyzer = None
red_flag_detector = None
feature_engine = None
model_monitor = None
metrics_collector = MetricsCollector()


# Pydantic Models
class PatientData(BaseModel):
    """Patient demographic and clinical data."""
    age: Optional[int] = Field(None, ge=0, le=120)
    gender: Optional[str] = Field(None, regex="^(male|female|other|unknown)$")
    pregnancy_status: Optional[str] = None
    medical_history: List[str] = Field(default_factory=list)
    current_medications: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    chronic_conditions: List[str] = Field(default_factory=list)


class VitalSigns(BaseModel):
    """Patient vital signs."""
    temperature: Optional[float] = Field(None, ge=30.0, le=45.0)  # Celsius
    heart_rate: Optional[int] = Field(None, ge=20, le=250)
    systolic_bp: Optional[int] = Field(None, ge=50, le=300)
    diastolic_bp: Optional[int] = Field(None, ge=30, le=200)
    respiratory_rate: Optional[int] = Field(None, ge=5, le=60)
    oxygen_saturation: Optional[float] = Field(None, ge=50.0, le=100.0)
    weight: Optional[float] = Field(None, ge=0.5, le=500.0)  # kg
    height: Optional[float] = Field(None, ge=20.0, le=250.0)  # cm


class Symptom(BaseModel):
    """Individual symptom description."""
    name: str
    severity: str = Field(regex="^(mild|moderate|severe|critical)$")
    duration_hours: Optional[float] = Field(None, ge=0)
    location: Optional[str] = None
    quality: Optional[str] = None
    triggers: List[str] = Field(default_factory=list)
    associated_symptoms: List[str] = Field(default_factory=list)
    patient_description: Optional[str] = None


class TriageInput(BaseModel):
    """Complete triage assessment input."""
    patient: PatientData
    vitals: Optional[VitalSigns] = None
    symptoms: List[Symptom]
    chief_complaint: str
    pain_score: Optional[int] = Field(None, ge=0, le=10)
    onset_datetime: Optional[datetime] = None
    clinical_context: Dict[str, Any] = Field(default_factory=dict)


class RiskScore(BaseModel):
    """AI risk assessment output."""
    risk_score: float = Field(..., ge=0.0, le=100.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    triage_category: str
    priority: int = Field(..., ge=1, le=5)
    explanation: Dict[str, Any]
    model_version: str
    computed_at: datetime


class TriageResult(BaseModel):
    """Complete triage assessment result."""
    risk_assessment: RiskScore
    red_flags: List[str]
    clinical_alerts: List[str]
    recommended_pathway: str
    estimated_wait_time: Optional[int] = None
    differential_diagnosis: List[str]
    recommended_tests: List[str]
    severity_indicators: Dict[str, float]


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize ML models and services on startup."""
    global triage_classifier, symptom_analyzer, red_flag_detector
    global feature_engine, model_monitor
    
    logger.info("Starting Smart Triage ML Service...")
    
    try:
        # Initialize feature engineering pipeline
        feature_engine = FeatureEngine()
        await feature_engine.initialize()
        
        # Load ML models
        triage_classifier = TriageClassifier()
        await triage_classifier.load_model(settings.TRIAGE_MODEL_PATH)
        
        symptom_analyzer = SymptomAnalyzer()
        await symptom_analyzer.load_model(settings.SYMPTOM_MODEL_PATH)
        
        red_flag_detector = RedFlagDetector()
        await red_flag_detector.initialize()
        
        # Initialize model monitoring
        model_monitor = ModelMonitor()
        await model_monitor.initialize()
        
        logger.info("ML Service startup complete",
                   models_loaded=["triage_classifier", "symptom_analyzer", "red_flag_detector"])
        
    except Exception as e:
        logger.error("Failed to initialize ML service", error=str(e), exc_info=True)
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Smart Triage ML Service...")
    
    # Save any pending model updates
    if model_monitor:
        await model_monitor.save_metrics()
    
    logger.info("ML Service shutdown complete")


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check for load balancers."""
    try:
        # Check if models are loaded
        models_ready = all([
            triage_classifier is not None,
            symptom_analyzer is not None,
            red_flag_detector is not None,
            feature_engine is not None
        ])
        
        if not models_ready:
            raise HTTPException(status_code=503, detail="Models not ready")
        
        # Quick model validation
        test_input = np.array([[0.5, 0.3, 0.7, 0.1, 0.9]])
        test_result = await triage_classifier.predict_proba(test_input)
        
        return {
            "status": "healthy",
            "models_loaded": models_ready,
            "timestamp": datetime.utcnow(),
            "version": "1.0.0"
        }
    
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )


# Model information endpoints
@app.get("/models/info")
async def get_model_info():
    """Get information about loaded models."""
    try:
        info = {
            "triage_classifier": {
                "version": triage_classifier.model_version if triage_classifier else None,
                "accuracy": triage_classifier.accuracy if triage_classifier else None,
                "last_updated": triage_classifier.last_updated if triage_classifier else None
            },
            "symptom_analyzer": {
                "version": symptom_analyzer.model_version if symptom_analyzer else None,
                "accuracy": symptom_analyzer.accuracy if symptom_analyzer else None,
                "last_updated": symptom_analyzer.last_updated if symptom_analyzer else None
            },
            "red_flag_detector": {
                "version": red_flag_detector.version if red_flag_detector else None,
                "sensitivity": red_flag_detector.sensitivity if red_flag_detector else None,
                "last_updated": red_flag_detector.last_updated if red_flag_detector else None
            }
        }
        
        return info
    
    except Exception as e:
        logger.error("Failed to get model info", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve model information")


# Main triage assessment endpoint
@app.post("/assess", response_model=TriageResult)
async def assess_triage(
    triage_input: TriageInput,
    background_tasks: BackgroundTasks,
    include_explanations: bool = True
) -> TriageResult:
    """
    Perform comprehensive AI-powered triage assessment.
    
    This endpoint combines multiple ML models to provide:
    - Risk scoring and triage category assignment
    - Red flag symptom detection
    - Clinical decision support recommendations
    - Explainable AI insights
    """
    start_time = datetime.utcnow()
    logger.info("Starting triage assessment", patient_age=triage_input.patient.age)
    
    try:
        # Extract and engineer features
        features = await feature_engine.extract_features(triage_input)
        
        # Run red flag detection first (critical path)
        red_flags = await red_flag_detector.detect(triage_input)
        
        # If critical red flags detected, fast-track to highest priority
        if red_flags and any(flag["severity"] == "critical" for flag in red_flags):
            logger.warning("Critical red flags detected", red_flags=red_flags)
            
            return TriageResult(
                risk_assessment=RiskScore(
                    risk_score=100.0,
                    confidence=1.0,
                    triage_category="red",
                    priority=1,
                    explanation={"red_flags": "Critical symptoms detected"},
                    model_version="red_flag_override",
                    computed_at=datetime.utcnow()
                ),
                red_flags=[flag["name"] for flag in red_flags],
                clinical_alerts=["IMMEDIATE MEDICAL ATTENTION REQUIRED"],
                recommended_pathway="emergency",
                estimated_wait_time=0,
                differential_diagnosis=[],
                recommended_tests=["immediate_assessment"],
                severity_indicators={"critical": 1.0}
            )
        
        # Run main triage classification
        risk_result = await triage_classifier.predict(
            features=features,
            include_explanation=include_explanations
        )
        
        # Analyze symptom severity
        symptom_analysis = await symptom_analyzer.analyze(triage_input.symptoms)
        
        # Generate clinical recommendations
        recommendations = await generate_clinical_recommendations(
            triage_input, risk_result, symptom_analysis
        )
        
        # Log prediction for monitoring
        background_tasks.add_task(
            log_prediction,
            triage_input.dict(),
            risk_result,
            symptom_analysis
        )
        
        # Build final result
        result = TriageResult(
            risk_assessment=RiskScore(
                risk_score=risk_result["risk_score"],
                confidence=risk_result["confidence"],
                triage_category=risk_result["category"],
                priority=risk_result["priority"],
                explanation=risk_result.get("explanation", {}),
                model_version=triage_classifier.model_version,
                computed_at=datetime.utcnow()
            ),
            red_flags=[flag["name"] for flag in red_flags],
            clinical_alerts=recommendations["alerts"],
            recommended_pathway=recommendations["pathway"],
            estimated_wait_time=recommendations["wait_time"],
            differential_diagnosis=recommendations["differential"],
            recommended_tests=recommendations["tests"],
            severity_indicators=symptom_analysis["severity_scores"]
        )
        
        # Record metrics
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        metrics_collector.record_prediction(
            category=result.risk_assessment.triage_category,
            confidence=result.risk_assessment.confidence,
            processing_time=processing_time
        )
        
        logger.info("Triage assessment completed",
                   category=result.risk_assessment.triage_category,
                   risk_score=result.risk_assessment.risk_score,
                   processing_time=processing_time)
        
        return result
    
    except Exception as e:
        logger.error("Triage assessment failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Triage assessment failed: {str(e)}"
        )


# Batch assessment endpoint
@app.post("/assess/batch")
async def assess_batch(
    assessments: List[TriageInput],
    background_tasks: BackgroundTasks
) -> List[TriageResult]:
    """Process multiple triage assessments in batch (for mass casualty events)."""
    
    if len(assessments) > 50:
        raise HTTPException(
            status_code=400,
            detail="Maximum 50 assessments per batch request"
        )
    
    logger.info("Starting batch assessment", count=len(assessments))
    
    try:
        # Process all assessments concurrently
        tasks = [assess_triage(assessment, background_tasks, False) 
                for assessment in assessments]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions
        successful_results = []
        errors = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                errors.append({"index": i, "error": str(result)})
            else:
                successful_results.append(result)
        
        if errors:
            logger.warning("Batch assessment had errors", 
                         successful=len(successful_results),
                         failed=len(errors))
        
        return successful_results
    
    except Exception as e:
        logger.error("Batch assessment failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Batch assessment failed: {str(e)}"
        )


# Model feedback and learning
@app.post("/feedback")
async def provide_feedback(
    assessment_id: str,
    actual_category: str,
    clinical_outcome: str,
    feedback_notes: Optional[str] = None
):
    """Provide feedback for model improvement and continuous learning."""
    
    logger.info("Received model feedback", 
               assessment_id=assessment_id,
               actual_category=actual_category)
    
    try:
        # Store feedback for model retraining
        await model_monitor.record_feedback(
            assessment_id=assessment_id,
            actual_category=actual_category,
            clinical_outcome=clinical_outcome,
            feedback_notes=feedback_notes
        )
        
        return {"status": "feedback_recorded", "assessment_id": assessment_id}
    
    except Exception as e:
        logger.error("Failed to record feedback", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to record feedback")


# Model metrics and monitoring
@app.get("/metrics")
async def get_metrics():
    """Get model performance metrics and monitoring data."""
    try:
        metrics = await model_monitor.get_current_metrics()
        return metrics
    except Exception as e:
        logger.error("Failed to get metrics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics")


# Helper functions
async def generate_clinical_recommendations(
    triage_input: TriageInput,
    risk_result: Dict[str, Any],
    symptom_analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate clinical recommendations based on assessment results."""
    
    recommendations = {
        "alerts": [],
        "pathway": "standard",
        "wait_time": None,
        "differential": [],
        "tests": []
    }
    
    # Determine pathway based on risk score
    risk_score = risk_result["risk_score"]
    category = risk_result["category"]
    
    if category == "red":
        recommendations["pathway"] = "emergency"
        recommendations["wait_time"] = 0
        recommendations["alerts"].append("IMMEDIATE ATTENTION REQUIRED")
    elif category == "orange":
        recommendations["pathway"] = "urgent"
        recommendations["wait_time"] = 15
        recommendations["alerts"].append("Urgent evaluation needed")
    elif category == "yellow":
        recommendations["pathway"] = "standard"
        recommendations["wait_time"] = 60
    else:
        recommendations["pathway"] = "routine"
        recommendations["wait_time"] = 240
    
    # Add specific clinical alerts
    if triage_input.vitals:
        vitals = triage_input.vitals
        
        # Temperature alerts
        if vitals.temperature and vitals.temperature >= 38.5:
            recommendations["alerts"].append("High fever detected")
        
        # Blood pressure alerts
        if vitals.systolic_bp and vitals.systolic_bp >= 180:
            recommendations["alerts"].append("Severe hypertension")
        elif vitals.systolic_bp and vitals.systolic_bp <= 90:
            recommendations["alerts"].append("Hypotension")
        
        # Oxygen saturation alerts
        if vitals.oxygen_saturation and vitals.oxygen_saturation <= 92:
            recommendations["alerts"].append("Low oxygen saturation")
    
    # Symptom-specific recommendations
    for symptom in triage_input.symptoms:
        if "chest_pain" in symptom.name.lower():
            recommendations["tests"].append("ECG")
            recommendations["tests"].append("Troponin")
            recommendations["differential"].append("Acute coronary syndrome")
        
        if "shortness_of_breath" in symptom.name.lower():
            recommendations["tests"].append("Chest X-ray")
            recommendations["tests"].append("ABG")
            recommendations["differential"].append("Respiratory distress")
    
    return recommendations


async def log_prediction(
    input_data: Dict[str, Any],
    prediction: Dict[str, Any],
    analysis: Dict[str, Any]
):
    """Log prediction data for model monitoring and improvement."""
    try:
        await model_monitor.log_prediction(
            timestamp=datetime.utcnow(),
            input_data=input_data,
            prediction=prediction,
            analysis=analysis
        )
    except Exception as e:
        logger.error("Failed to log prediction", error=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_config=None
    )
