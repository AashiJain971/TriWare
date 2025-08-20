"""
Triage Assessment model for AI-powered risk scoring and decision support.

This module handles the core triage functionality with symptom assessment,
vital signs integration, and AI-based risk scoring.
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, JSON, Text, ForeignKey, Float, Enum
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
import enum

from app.db.base_class import Base


class TriageCategory(enum.Enum):
    """Triage category enumeration following emergency medicine standards."""
    RED = "red"          # Immediate - life-threatening
    ORANGE = "orange"    # Very Urgent - potential life threat
    YELLOW = "yellow"    # Urgent - serious but stable
    GREEN = "green"      # Routine - non-urgent
    BLUE = "blue"        # Non-urgent - minor conditions


class SymptomSeverity(enum.Enum):
    """Symptom severity levels."""
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"


class TriageAssessment(Base):
    """
    Comprehensive triage assessment with AI-powered risk scoring.
    
    Captures patient symptoms, vital signs, and generates triage
    recommendations using hybrid AI models.
    """
    __tablename__ = "triage_assessments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    assessment_id = Column(String(50), unique=True, index=True, nullable=False)
    
    # Patient and encounter linkage
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id"), nullable=True)
    
    # Chief complaint and presentation
    chief_complaint = Column(Text, nullable=False)
    chief_complaint_code = Column(String(20), nullable=True)  # ICD-10 or SNOMED code
    presenting_symptoms = Column(JSON, nullable=False)  # Structured symptom data
    
    # Pain assessment
    pain_score = Column(Integer, nullable=True)  # 0-10 scale
    pain_location = Column(JSON, nullable=True)  # Body locations
    pain_characteristics = Column(JSON, nullable=True)  # Sharp, dull, burning, etc.
    
    # Symptom onset and duration
    symptom_onset = Column(DateTime(timezone=True), nullable=True)
    symptom_duration_hours = Column(Float, nullable=True)
    symptom_progression = Column(String(20), nullable=True)  # improving, worsening, stable
    
    # Vital signs (latest readings)
    temperature = Column(Float, nullable=True)  # Celsius
    heart_rate = Column(Integer, nullable=True)  # BPM
    systolic_bp = Column(Integer, nullable=True)  # mmHg
    diastolic_bp = Column(Integer, nullable=True)  # mmHg
    respiratory_rate = Column(Integer, nullable=True)  # Per minute
    oxygen_saturation = Column(Float, nullable=True)  # Percentage
    
    # Additional assessments
    consciousness_level = Column(String(20), nullable=True)  # alert, confused, unconscious
    mobility_status = Column(String(20), nullable=True)  # ambulatory, wheelchair, stretcher
    
    # Red flag symptoms
    red_flags = Column(JSON, nullable=True)  # Critical symptoms detected
    red_flag_score = Column(Float, default=0.0)
    
    # AI Risk Scoring
    ai_risk_score = Column(Float, nullable=True)  # 0-100 risk score
    ai_confidence = Column(Float, nullable=True)  # Model confidence 0-1
    ai_model_version = Column(String(20), nullable=True)
    ai_explanation = Column(JSON, nullable=True)  # SHAP values and explanations
    
    # Triage Decision
    triage_category = Column(Enum(TriageCategory), nullable=False)
    triage_priority = Column(Integer, nullable=False)  # 1-5 priority
    recommended_pathway = Column(String(100), nullable=True)  # ED, urgent_care, GP
    estimated_wait_time = Column(Integer, nullable=True)  # Minutes
    
    # Clinical Decision Support
    differential_diagnosis = Column(JSON, nullable=True)  # Possible conditions
    recommended_tests = Column(JSON, nullable=True)  # Lab, imaging, etc.
    clinical_alerts = Column(JSON, nullable=True)  # Drug interactions, allergies
    
    # Assessment metadata
    assessment_method = Column(String(20), default="kiosk")  # kiosk, staff, hybrid
    language_used = Column(String(10), default="en")
    accessibility_used = Column(JSON, nullable=True)  # Voice, large text, etc.
    
    # Quality and review
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    review_notes = Column(Text, nullable=True)
    accuracy_feedback = Column(String(20), nullable=True)  # accurate, inaccurate, partial
    
    # System metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Data source and sync
    source_system = Column(String(50), default="kiosk")
    sync_status = Column(String(20), default="pending")
    
    # Relationships
    patient = relationship("Patient", back_populates="triage_assessments")
    encounter = relationship("Encounter", back_populates="triage_assessment")
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    symptoms = relationship("SymptomAssessment", back_populates="triage_assessment", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<TriageAssessment(id={self.assessment_id}, category={self.triage_category})>"
    
    @property
    def is_critical(self) -> bool:
        """Check if assessment indicates critical condition."""
        return self.triage_category in [TriageCategory.RED, TriageCategory.ORANGE]
    
    @property
    def requires_immediate_attention(self) -> bool:
        """Check if patient requires immediate medical attention."""
        return self.triage_category == TriageCategory.RED
    
    def get_vital_signs_dict(self) -> Dict[str, Optional[Union[float, int]]]:
        """Get vital signs as dictionary."""
        return {
            "temperature": self.temperature,
            "heart_rate": self.heart_rate,
            "systolic_bp": self.systolic_bp,
            "diastolic_bp": self.diastolic_bp,
            "respiratory_rate": self.respiratory_rate,
            "oxygen_saturation": self.oxygen_saturation
        }
    
    def has_abnormal_vitals(self) -> bool:
        """Check if any vital signs are outside normal ranges."""
        # Define normal ranges (these should be configurable)
        normal_ranges = {
            "heart_rate": (60, 100),
            "systolic_bp": (90, 140),
            "diastolic_bp": (60, 90),
            "temperature": (36.1, 37.2),  # Celsius
            "oxygen_saturation": (95, 100),
            "respiratory_rate": (12, 20)
        }
        
        vitals = self.get_vital_signs_dict()
        
        for vital, value in vitals.items():
            if value is not None and vital in normal_ranges:
                min_val, max_val = normal_ranges[vital]
                if value < min_val or value > max_val:
                    return True
        
        return False
    
    def calculate_news_score(self) -> int:
        """Calculate National Early Warning Score (NEWS2)."""
        score = 0
        
        # Respiratory rate scoring
        if self.respiratory_rate:
            if self.respiratory_rate <= 8:
                score += 3
            elif 9 <= self.respiratory_rate <= 11:
                score += 1
            elif 21 <= self.respiratory_rate <= 24:
                score += 2
            elif self.respiratory_rate >= 25:
                score += 3
        
        # Oxygen saturation scoring
        if self.oxygen_saturation:
            if self.oxygen_saturation <= 91:
                score += 3
            elif 92 <= self.oxygen_saturation <= 93:
                score += 2
            elif 94 <= self.oxygen_saturation <= 95:
                score += 1
        
        # Systolic blood pressure scoring
        if self.systolic_bp:
            if self.systolic_bp <= 90:
                score += 3
            elif 91 <= self.systolic_bp <= 100:
                score += 2
            elif 101 <= self.systolic_bp <= 110:
                score += 1
            elif self.systolic_bp >= 220:
                score += 3
        
        # Heart rate scoring
        if self.heart_rate:
            if self.heart_rate <= 40:
                score += 3
            elif 41 <= self.heart_rate <= 50:
                score += 1
            elif 91 <= self.heart_rate <= 110:
                score += 1
            elif 111 <= self.heart_rate <= 130:
                score += 2
            elif self.heart_rate >= 131:
                score += 3
        
        # Temperature scoring
        if self.temperature:
            if self.temperature <= 35.0:
                score += 3
            elif 35.1 <= self.temperature <= 36.0:
                score += 1
            elif 38.1 <= self.temperature <= 39.0:
                score += 1
            elif self.temperature >= 39.1:
                score += 2
        
        # Consciousness level scoring
        if self.consciousness_level and self.consciousness_level != "alert":
            score += 3
        
        return score
    
    def get_priority_color(self) -> str:
        """Get color code for triage category."""
        color_map = {
            TriageCategory.RED: "#FF0000",
            TriageCategory.ORANGE: "#FF8000",
            TriageCategory.YELLOW: "#FFFF00",
            TriageCategory.GREEN: "#00FF00",
            TriageCategory.BLUE: "#0080FF"
        }
        return color_map.get(self.triage_category, "#808080")


class SymptomAssessment(Base):
    """Detailed symptom assessment and classification."""
    __tablename__ = "symptom_assessments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    triage_assessment_id = Column(UUID(as_uuid=True), ForeignKey("triage_assessments.id"), nullable=False)
    
    # Symptom identification
    symptom_name = Column(String(100), nullable=False)
    symptom_code = Column(String(20), nullable=True)  # SNOMED CT code
    body_system = Column(String(50), nullable=True)  # cardiovascular, respiratory, etc.
    
    # Symptom details
    severity = Column(Enum(SymptomSeverity), nullable=False)
    onset_date = Column(DateTime(timezone=True), nullable=True)
    duration_hours = Column(Float, nullable=True)
    frequency = Column(String(20), nullable=True)  # constant, intermittent, episodic
    
    # Context and triggers
    triggers = Column(JSON, nullable=True)  # What makes it worse/better
    associated_symptoms = Column(JSON, nullable=True)  # Related symptoms
    location = Column(JSON, nullable=True)  # Body location/region
    
    # Patient description
    patient_description = Column(Text, nullable=True)  # Patient's own words
    quality_descriptors = Column(JSON, nullable=True)  # Sharp, dull, throbbing, etc.
    
    # Scoring and classification
    symptom_score = Column(Float, nullable=True)  # Severity score 0-10
    clinical_significance = Column(String(20), nullable=True)  # high, medium, low
    red_flag_indicator = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    triage_assessment = relationship("TriageAssessment", back_populates="symptoms")


class ClinicalGuideline(Base):
    """Clinical guidelines and protocols for decision support."""
    __tablename__ = "clinical_guidelines"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Guideline identification
    guideline_id = Column(String(50), unique=True, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    version = Column(String(20), nullable=False)
    
    # Clinical context
    condition = Column(String(100), nullable=False)
    condition_codes = Column(JSON, nullable=True)  # ICD-10, SNOMED codes
    specialty = Column(String(50), nullable=True)
    age_range = Column(JSON, nullable=True)  # {"min": 0, "max": 120}
    
    # Guideline content
    criteria = Column(JSON, nullable=False)  # Inclusion/exclusion criteria
    recommendations = Column(JSON, nullable=False)  # Structured recommendations
    evidence_level = Column(String(10), nullable=True)  # A, B, C, D
    
    # Implementation
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=1)  # Higher number = higher priority
    auto_trigger = Column(Boolean, default=False)  # Automatically suggest
    
    # Metadata
    source_organization = Column(String(100), nullable=True)
    publication_date = Column(DateTime(timezone=True), nullable=True)
    review_date = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class DrugInteraction(Base):
    """Drug interaction database for clinical decision support."""
    __tablename__ = "drug_interactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Drug information
    drug_a = Column(String(100), nullable=False)
    drug_a_code = Column(String(20), nullable=True)  # RxNorm code
    drug_b = Column(String(100), nullable=False)
    drug_b_code = Column(String(20), nullable=True)
    
    # Interaction details
    severity = Column(String(20), nullable=False)  # contraindicated, major, moderate, minor
    mechanism = Column(Text, nullable=True)  # How the interaction occurs
    clinical_effect = Column(Text, nullable=False)  # What happens
    management = Column(Text, nullable=True)  # How to manage
    
    # Evidence
    evidence_level = Column(String(20), nullable=True)
    references = Column(JSON, nullable=True)
    
    # System metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class TriageRule(Base):
    """Rules-based triage decision engine rules."""
    __tablename__ = "triage_rules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Rule identification
    rule_id = Column(String(50), unique=True, nullable=False)
    rule_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Rule logic
    conditions = Column(JSON, nullable=False)  # Conditions that trigger rule
    actions = Column(JSON, nullable=False)  # Actions to take
    priority = Column(Integer, default=1)
    
    # Triage assignment
    assigns_category = Column(Enum(TriageCategory), nullable=True)
    assigns_priority = Column(Integer, nullable=True)
    
    # Rule metadata
    is_active = Column(Boolean, default=True)
    is_mandatory = Column(Boolean, default=False)  # Cannot be overridden
    requires_confirmation = Column(Boolean, default=True)
    
    # Performance tracking
    times_triggered = Column(Integer, default=0)
    accuracy_rate = Column(Float, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))


# Predefined red flag rules
RED_FLAG_RULES = [
    {
        "rule_id": "chest_pain_critical",
        "rule_name": "Critical Chest Pain",
        "conditions": {
            "symptoms": ["chest_pain"],
            "severity": "severe",
            "additional_criteria": [
                "radiation_to_arm",
                "shortness_of_breath",
                "nausea_vomiting"
            ]
        },
        "actions": {
            "triage_category": "red",
            "alert_staff": True,
            "recommended_tests": ["ecg", "troponin"],
            "message": "Possible acute coronary syndrome - immediate evaluation required"
        }
    },
    {
        "rule_id": "stroke_symptoms",
        "rule_name": "Stroke Symptoms",
        "conditions": {
            "symptoms": ["facial_droop", "arm_weakness", "speech_difficulty"],
            "any_present": True
        },
        "actions": {
            "triage_category": "red",
            "alert_staff": True,
            "recommended_pathway": "stroke_center",
            "message": "Possible stroke - activate stroke protocol"
        }
    },
    {
        "rule_id": "severe_breathing_difficulty",
        "rule_name": "Severe Breathing Difficulty",
        "conditions": {
            "symptoms": ["severe_dyspnea"],
            "vitals": {
                "oxygen_saturation": {"max": 90},
                "respiratory_rate": {"min": 25}
            }
        },
        "actions": {
            "triage_category": "red",
            "alert_staff": True,
            "recommended_tests": ["abg", "chest_xray"],
            "message": "Severe respiratory distress - immediate attention required"
        }
    }
]
