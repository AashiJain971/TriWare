"""
Triage assessment API endpoints.

This module handles the core triage functionality including symptom assessment,
AI-powered risk scoring, and clinical decision support integration.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any, AsyncGenerator
import structlog
import json
from uuid import UUID
from datetime import datetime, timedelta

from app.core.security import get_current_user, require_staff
from app.core.config import settings, RED_FLAG_SYMPTOMS
from app.db.session import get_db
from app.models.triage import TriageAssessment, TriageCategory
from app.models.patient import Patient
from app.models.user import User
from app.schemas.triage import (
    TriageAssessmentCreate,
    TriageAssessmentUpdate,
    TriageAssessmentResponse,
    SymptomInput,
    TriageDecision,
    RiskScoreResponse,
    TriageStats
)
from app.services.triage import TriageService
from app.services.ml_inference import MLInferenceService
from app.services.clinical_rules import ClinicalRulesEngine
from app.services.queue import QueueService
from app.services.notification import NotificationService
from app.services.audit import AuditService
from app.utils.validation import validate_vital_signs
from app.core.celery_app import celery_app

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.post("/assess", response_model=TriageAssessmentResponse, status_code=status.HTTP_201_CREATED)
async def create_triage_assessment(
    *,
    db: AsyncSession = Depends(get_db),
    assessment_data: TriageAssessmentCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    request: Request,
    auto_assign_queue: bool = Query(True)
) -> TriageAssessment:
    """
    Create comprehensive triage assessment with AI-powered risk scoring.
    
    This endpoint performs the complete triage workflow:
    1. Symptom analysis and red flag detection
    2. Vital signs validation and scoring
    3. AI-powered risk assessment
    4. Rules-based clinical decision support
    5. Triage category assignment
    6. Queue management integration
    """
    logger.info("Creating triage assessment", 
               patient_id=assessment_data.patient_id,
               user_id=current_user.id)
    
    triage_service = TriageService(db)
    
    try:
        # Validate patient exists
        if not await triage_service.patient_exists(assessment_data.patient_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found"
            )
        
        # Validate vital signs if provided
        if assessment_data.vitals:
            validation_result = validate_vital_signs(assessment_data.vitals)
            if not validation_result.is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid vital signs: {validation_result.errors}"
                )
        
        # Create initial assessment
        assessment = await triage_service.create_assessment(
            assessment_data=assessment_data,
            created_by=current_user.id
        )
        
        # Run AI risk scoring in background
        background_tasks.add_task(
            run_ai_risk_assessment,
            assessment.id,
            str(db.bind.url)
        )
        
        # Check for red flag symptoms
        red_flags = check_red_flag_symptoms(assessment_data.symptoms)
        if red_flags:
            logger.warning("Red flag symptoms detected", 
                         assessment_id=assessment.assessment_id,
                         red_flags=red_flags)
            
            # Auto-assign to RED category for red flags
            assessment.triage_category = TriageCategory.RED
            assessment.red_flags = red_flags
            assessment.red_flag_score = 10.0
            
            # Immediate notification for critical cases
            background_tasks.add_task(
                send_critical_alert,
                assessment.id,
                red_flags
            )
        
        # Apply clinical rules engine
        rules_engine = ClinicalRulesEngine(db)
        rules_result = await rules_engine.evaluate_assessment(assessment)
        
        if rules_result.override_category:
            assessment.triage_category = rules_result.override_category
            assessment.triage_priority = rules_result.priority
        
        # Calculate NEWS score if vitals available
        if assessment_data.vitals:
            news_score = assessment.calculate_news_score()
            if news_score >= 7:  # High NEWS score
                assessment.triage_category = TriageCategory.ORANGE
                logger.warning("High NEWS score detected", 
                             assessment_id=assessment.assessment_id,
                             news_score=news_score)
        
        # Save updated assessment
        await triage_service.update_assessment(assessment)
        
        # Auto-assign to queue if requested
        if auto_assign_queue:
            queue_service = QueueService(db)
            await queue_service.add_to_queue(
                patient_id=assessment.patient_id,
                triage_category=assessment.triage_category,
                priority=assessment.triage_priority,
                assessment_id=assessment.id
            )
        
        # Log for audit
        audit_service = AuditService(db)
        await audit_service.log_triage_action(
            user_id=current_user.id,
            patient_id=assessment.patient_id,
            assessment_id=assessment.id,
            action="create_triage_assessment",
            details={
                "category": assessment.triage_category.value,
                "priority": assessment.triage_priority,
                "red_flags": red_flags
            },
            request=request
        )
        
        logger.info("Triage assessment created", 
                   assessment_id=assessment.assessment_id,
                   category=assessment.triage_category.value)
        
        return assessment
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create triage assessment", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create triage assessment"
        )


@router.get("/{assessment_id}", response_model=TriageAssessmentResponse)
async def get_triage_assessment(
    *,
    db: AsyncSession = Depends(get_db),
    assessment_id: str,
    current_user: User = Depends(require_staff),
    include_ai_details: bool = Query(False)
) -> TriageAssessment:
    """Get detailed triage assessment by ID."""
    
    logger.info("Getting triage assessment", 
               assessment_id=assessment_id, 
               user_id=current_user.id)
    
    triage_service = TriageService(db)
    
    try:
        assessment = await triage_service.get_by_assessment_id(
            assessment_id=assessment_id,
            include_symptoms=True,
            include_ai_details=include_ai_details
        )
        
        if not assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Triage assessment not found"
            )
        
        return assessment
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get triage assessment", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve triage assessment"
        )


@router.put("/{assessment_id}", response_model=TriageAssessmentResponse)
async def update_triage_assessment(
    *,
    db: AsyncSession = Depends(get_db),
    assessment_id: str,
    assessment_update: TriageAssessmentUpdate,
    current_user: User = Depends(require_staff),
    request: Request
) -> TriageAssessment:
    """Update triage assessment with clinician review."""
    
    logger.info("Updating triage assessment", 
               assessment_id=assessment_id, 
               user_id=current_user.id)
    
    triage_service = TriageService(db)
    
    try:
        assessment = await triage_service.get_by_assessment_id(assessment_id)
        if not assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Triage assessment not found"
            )
        
        # Track changes for audit
        original_category = assessment.triage_category
        
        # Update assessment
        updated_assessment = await triage_service.update_assessment_with_review(
            assessment=assessment,
            update_data=assessment_update,
            reviewed_by=current_user.id
        )
        
        # If category changed, update queue
        if updated_assessment.triage_category != original_category:
            queue_service = QueueService(db)
            await queue_service.update_priority(
                patient_id=assessment.patient_id,
                new_category=updated_assessment.triage_category,
                new_priority=updated_assessment.triage_priority
            )
        
        # Log update for audit
        audit_service = AuditService(db)
        await audit_service.log_triage_action(
            user_id=current_user.id,
            patient_id=assessment.patient_id,
            assessment_id=assessment.id,
            action="update_triage_assessment",
            details={
                "original_category": original_category.value,
                "new_category": updated_assessment.triage_category.value,
                "reviewer_notes": assessment_update.review_notes
            },
            request=request
        )
        
        logger.info("Triage assessment updated", 
                   assessment_id=assessment_id,
                   reviewed_by=current_user.id)
        
        return updated_assessment
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update triage assessment", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update triage assessment"
        )


@router.post("/{assessment_id}/risk-score", response_model=RiskScoreResponse)
async def calculate_risk_score(
    *,
    db: AsyncSession = Depends(get_db),
    assessment_id: str,
    current_user: User = Depends(require_staff),
    force_recalculate: bool = Query(False)
) -> Dict[str, Any]:
    """Calculate or recalculate AI risk score for assessment."""
    
    logger.info("Calculating risk score", 
               assessment_id=assessment_id, 
               user_id=current_user.id)
    
    triage_service = TriageService(db)
    ml_service = MLInferenceService()
    
    try:
        assessment = await triage_service.get_by_assessment_id(assessment_id)
        if not assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Triage assessment not found"
            )
        
        # Check if already calculated and not forcing recalculation
        if assessment.ai_risk_score is not None and not force_recalculate:
            return {
                "assessment_id": assessment_id,
                "risk_score": assessment.ai_risk_score,
                "confidence": assessment.ai_confidence,
                "model_version": assessment.ai_model_version,
                "explanation": assessment.ai_explanation,
                "calculated_at": assessment.updated_at,
                "cached": True
            }
        
        # Prepare features for ML model
        features = await prepare_ml_features(assessment)
        
        # Get AI prediction
        prediction_result = await ml_service.predict_risk(
            features=features,
            model_type="triage_classifier"
        )
        
        # Update assessment with AI results
        assessment.ai_risk_score = prediction_result["risk_score"]
        assessment.ai_confidence = prediction_result["confidence"]
        assessment.ai_model_version = prediction_result["model_version"]
        assessment.ai_explanation = prediction_result["explanation"]
        
        # Adjust triage category based on AI score if needed
        if prediction_result["risk_score"] >= 90 and assessment.triage_category not in [TriageCategory.RED]:
            assessment.triage_category = TriageCategory.RED
            logger.warning("AI model suggests higher urgency", 
                         assessment_id=assessment_id,
                         ai_score=prediction_result["risk_score"])
        
        await triage_service.update_assessment(assessment)
        
        return {
            "assessment_id": assessment_id,
            "risk_score": assessment.ai_risk_score,
            "confidence": assessment.ai_confidence,
            "model_version": assessment.ai_model_version,
            "explanation": assessment.ai_explanation,
            "calculated_at": datetime.utcnow(),
            "cached": False
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to calculate risk score", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate risk score"
        )


@router.get("/patient/{patient_id}/history")
async def get_patient_triage_history(
    *,
    db: AsyncSession = Depends(get_db),
    patient_id: str,
    current_user: User = Depends(require_staff),
    days: int = Query(90, ge=1, le=365),
    limit: int = Query(20, ge=1, le=100)
) -> Dict[str, Any]:
    """Get patient's triage history."""
    
    logger.info("Getting patient triage history", 
               patient_id=patient_id, 
               user_id=current_user.id)
    
    triage_service = TriageService(db)
    
    try:
        history = await triage_service.get_patient_history(
            patient_id=patient_id,
            days=days,
            limit=limit
        )
        
        return {
            "patient_id": patient_id,
            "assessments": history,
            "total": len(history),
            "period_days": days
        }
        
    except Exception as e:
        logger.error("Failed to get triage history", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve triage history"
        )


@router.get("/stats/daily", response_model=TriageStats)
async def get_daily_triage_stats(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
    date: Optional[datetime] = Query(None),
    department: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """Get daily triage statistics and metrics."""
    
    if not date:
        date = datetime.utcnow().date()
    
    logger.info("Getting triage stats", date=date, user_id=current_user.id)
    
    triage_service = TriageService(db)
    
    try:
        stats = await triage_service.get_daily_stats(
            date=date,
            department=department
        )
        
        return stats
        
    except Exception as e:
        logger.error("Failed to get triage stats", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve triage statistics"
        )


@router.post("/bulk-assess")
async def bulk_triage_assessment(
    *,
    db: AsyncSession = Depends(get_db),
    assessments: List[TriageAssessmentCreate],
    current_user: User = Depends(require_staff),
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """Process multiple triage assessments in bulk (for mass casualty events)."""
    
    logger.info("Processing bulk triage assessments", 
               count=len(assessments), 
               user_id=current_user.id)
    
    if len(assessments) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 50 assessments per bulk request"
        )
    
    results = []
    errors = []
    
    triage_service = TriageService(db)
    
    for idx, assessment_data in enumerate(assessments):
        try:
            # Quick triage for mass casualty scenarios
            assessment = await triage_service.create_quick_assessment(
                assessment_data=assessment_data,
                created_by=current_user.id
            )
            
            results.append({
                "index": idx,
                "assessment_id": assessment.assessment_id,
                "category": assessment.triage_category.value,
                "priority": assessment.triage_priority
            })
            
            # Process AI scoring in background
            background_tasks.add_task(
                run_ai_risk_assessment,
                assessment.id,
                str(db.bind.url)
            )
            
        except Exception as e:
            logger.error("Failed to process bulk assessment", 
                        index=idx, error=str(e))
            errors.append({
                "index": idx,
                "error": str(e),
                "patient_id": assessment_data.patient_id
            })
    
    return {
        "processed": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors
    }


# Helper functions

def check_red_flag_symptoms(symptoms: List[SymptomInput]) -> List[str]:
    """Check for red flag symptoms that require immediate attention."""
    detected_flags = []
    
    for symptom in symptoms:
        if symptom.name.lower() in RED_FLAG_SYMPTOMS:
            detected_flags.append(symptom.name)
        
        # Check for severe symptoms
        if symptom.severity == "severe" or symptom.severity == "critical":
            if any(critical in symptom.name.lower() for critical in [
                "chest_pain", "breathing", "consciousness", "bleeding", "pain"
            ]):
                detected_flags.append(f"severe_{symptom.name}")
    
    return detected_flags


async def prepare_ml_features(assessment: TriageAssessment) -> Dict[str, Any]:
    """Prepare features for ML model inference."""
    features = {
        # Demographics (from patient)
        "age": assessment.patient.age if assessment.patient else None,
        "gender": assessment.patient.gender if assessment.patient else None,
        
        # Vital signs
        "temperature": assessment.temperature,
        "heart_rate": assessment.heart_rate,
        "systolic_bp": assessment.systolic_bp,
        "diastolic_bp": assessment.diastolic_bp,
        "respiratory_rate": assessment.respiratory_rate,
        "oxygen_saturation": assessment.oxygen_saturation,
        
        # Symptoms
        "symptom_count": len(assessment.presenting_symptoms) if assessment.presenting_symptoms else 0,
        "pain_score": assessment.pain_score,
        "symptom_duration": assessment.symptom_duration_hours,
        
        # Red flags
        "red_flag_count": len(assessment.red_flags) if assessment.red_flags else 0,
        "red_flag_score": assessment.red_flag_score,
        
        # Clinical scores
        "news_score": assessment.calculate_news_score(),
        
        # Historical factors
        "has_chronic_conditions": assessment.patient.has_chronic_conditions() if assessment.patient else False,
        "is_high_risk": assessment.patient.is_high_risk() if assessment.patient else False,
    }
    
    return features


@celery_app.task
def run_ai_risk_assessment(assessment_id: UUID, db_url: str):
    """Background task for AI risk assessment."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        triage_service = TriageService(db)
        ml_service = MLInferenceService()
        
        assessment = triage_service.get_by_id(assessment_id)
        if not assessment:
            return
        
        features = prepare_ml_features(assessment)
        prediction_result = ml_service.predict_risk(
            features=features,
            model_type="triage_classifier"
        )
        
        assessment.ai_risk_score = prediction_result["risk_score"]
        assessment.ai_confidence = prediction_result["confidence"]
        assessment.ai_model_version = prediction_result["model_version"]
        assessment.ai_explanation = prediction_result["explanation"]
        
        db.commit()
        
        logger.info("AI risk assessment completed", 
                   assessment_id=str(assessment_id),
                   risk_score=assessment.ai_risk_score)
        
    except Exception as e:
        logger.error("AI risk assessment failed", 
                    assessment_id=str(assessment_id), 
                    error=str(e))
        db.rollback()
    finally:
        db.close()


@celery_app.task
def send_critical_alert(assessment_id: UUID, red_flags: List[str]):
    """Send critical patient alert to medical staff."""
    try:
        notification_service = NotificationService()
        
        message = f"CRITICAL PATIENT ALERT: Red flag symptoms detected - {', '.join(red_flags)}"
        
        # Send to on-duty staff
        notification_service.send_critical_alert(
            message=message,
            assessment_id=str(assessment_id),
            priority="immediate"
        )
        
        logger.info("Critical alert sent", 
                   assessment_id=str(assessment_id),
                   red_flags=red_flags)
        
    except Exception as e:
        logger.error("Failed to send critical alert", 
                    assessment_id=str(assessment_id), 
                    error=str(e))
