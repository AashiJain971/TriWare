"""
FHIR-compliant Patient model for the Smart Triage Kiosk System.

This model represents patient demographic and clinical information
following HL7 FHIR R4 specifications for interoperability.
"""

from sqlalchemy import Column, String, Integer, Date, DateTime, Boolean, JSON, Text, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from datetime import datetime, date
from typing import Optional, List, Dict, Any

from app.db.base_class import Base


class Patient(Base):
    """
    FHIR Patient resource representation.
    
    Stores patient demographic information, identifiers, and contact details
    in compliance with FHIR R4 Patient resource structure.
    """
    __tablename__ = "patients"
    
    # Core identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    patient_id = Column(String(50), unique=True, index=True, nullable=False)  # External ID
    aadhaar = Column(String(12), unique=True, index=True, nullable=True)
    mrn = Column(String(20), unique=True, index=True, nullable=True)  # Medical Record Number
    
    # Name (FHIR HumanName structure)
    name = Column(JSON, nullable=False)  # {"given": ["John"], "family": "Doe", "prefix": ["Mr"]}
    
    # Demographics
    birth_date = Column(Date, nullable=True)
    gender = Column(String(10), nullable=True)  # male, female, other, unknown
    
    # Contact information (FHIR ContactPoint)
    telecom = Column(JSON, nullable=True)  # [{"system": "phone", "value": "+91...", "use": "mobile"}]
    
    # Address (FHIR Address)
    address = Column(JSON, nullable=True)  # [{"line": ["123 Main St"], "city": "Delhi", "state": "DL", "postalCode": "110001", "country": "IN"}]
    
    # Clinical information
    allergies = Column(JSON, nullable=True)  # List of known allergies
    medical_history = Column(JSON, nullable=True)  # Past medical history
    current_medications = Column(JSON, nullable=True)  # Current medications
    emergency_contact = Column(JSON, nullable=True)  # Emergency contact details
    
    # Special populations
    pregnancy_status = Column(String(20), nullable=True)  # pregnant, not_pregnant, unknown
    estimated_due_date = Column(Date, nullable=True)
    
    # Language and communication
    preferred_language = Column(String(10), default="en")
    communication_needs = Column(JSON, nullable=True)  # Accessibility requirements
    
    # Insurance and financial
    insurance_info = Column(JSON, nullable=True)
    
    # Consent and privacy
    consent_given = Column(Boolean, default=False)
    privacy_preferences = Column(JSON, nullable=True)
    
    # System metadata
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Data source and sync
    source_system = Column(String(50), default="kiosk")  # kiosk, his, external
    sync_status = Column(String(20), default="pending")  # pending, synced, error
    last_sync = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    encounters = relationship("Encounter", back_populates="patient", cascade="all, delete-orphan")
    vitals = relationship("VitalSigns", back_populates="patient", cascade="all, delete-orphan")
    triage_assessments = relationship("TriageAssessment", back_populates="patient")
    
    def __repr__(self):
        return f"<Patient(id={self.id}, patient_id={self.patient_id})>"
    
    @property
    def full_name(self) -> str:
        """Get formatted full name."""
        if not self.name:
            return "Unknown"
        
        name_parts = []
        if self.name.get("prefix"):
            name_parts.extend(self.name["prefix"])
        if self.name.get("given"):
            name_parts.extend(self.name["given"])
        if self.name.get("family"):
            name_parts.append(self.name["family"])
        
        return " ".join(name_parts)
    
    @property
    def age(self) -> Optional[int]:
        """Calculate age from birth date."""
        if not self.birth_date:
            return None
        
        today = date.today()
        age = today.year - self.birth_date.year
        
        if today.month < self.birth_date.month or \
           (today.month == self.birth_date.month and today.day < self.birth_date.day):
            age -= 1
        
        return age
    
    @property
    def primary_phone(self) -> Optional[str]:
        """Get primary phone number."""
        if not self.telecom:
            return None
        
        for contact in self.telecom:
            if contact.get("system") == "phone" and contact.get("use") in ["mobile", "home"]:
                return contact.get("value")
        
        return None
    
    @property
    def primary_address(self) -> Optional[Dict[str, Any]]:
        """Get primary address."""
        if not self.address:
            return None
        
        for addr in self.address:
            if addr.get("use") in ["home", "temp"] or not addr.get("use"):
                return addr
        
        return self.address[0] if self.address else None
    
    def get_known_allergies(self) -> List[str]:
        """Get list of known allergies."""
        if not self.allergies:
            return []
        
        allergy_list = []
        for allergy in self.allergies:
            if isinstance(allergy, dict):
                allergy_list.append(allergy.get("substance", "Unknown"))
            else:
                allergy_list.append(str(allergy))
        
        return allergy_list
    
    def has_chronic_conditions(self) -> bool:
        """Check if patient has chronic conditions."""
        if not self.medical_history:
            return False
        
        chronic_conditions = [
            "diabetes", "hypertension", "heart_disease", "asthma", "copd",
            "kidney_disease", "liver_disease", "cancer", "autoimmune"
        ]
        
        for condition in self.medical_history:
            if isinstance(condition, dict):
                condition_name = condition.get("condition", "").lower()
            else:
                condition_name = str(condition).lower()
            
            if any(chronic in condition_name for chronic in chronic_conditions):
                return True
        
        return False
    
    def is_high_risk(self) -> bool:
        """Determine if patient is high risk based on demographics and history."""
        if self.age and self.age >= 65:
            return True
        
        if self.pregnancy_status == "pregnant":
            return True
        
        if self.has_chronic_conditions():
            return True
        
        return False
    
    def to_fhir_dict(self) -> Dict[str, Any]:
        """Convert to FHIR Patient resource format."""
        fhir_patient = {
            "resourceType": "Patient",
            "id": str(self.id),
            "identifier": [
                {
                    "use": "usual",
                    "type": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                                "code": "MR",
                                "display": "Medical Record Number"
                            }
                        ]
                    },
                    "value": self.patient_id
                }
            ],
            "active": self.active,
            "name": [self.name] if self.name else [],
            "telecom": self.telecom or [],
            "gender": self.gender,
            "birthDate": self.birth_date.isoformat() if self.birth_date else None,
            "address": self.address or [],
            "communication": [
                {
                    "language": {
                        "coding": [
                            {
                                "system": "urn:ietf:bcp:47",
                                "code": self.preferred_language
                            }
                        ]
                    }
                }
            ]
        }
        
        # Add Aadhaar identifier if present
        if self.aadhaar:
            fhir_patient["identifier"].append({
                "use": "official",
                "type": {
                    "coding": [
                        {
                            "system": "https://uidai.gov.in/",
                            "code": "AADHAAR",
                            "display": "Aadhaar"
                        }
                    ]
                },
                "value": self.aadhaar
            })
        
        return fhir_patient


class PatientIdentifier(Base):
    """Additional patient identifiers for cross-system integration."""
    __tablename__ = "patient_identifiers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    
    # Identifier details
    system = Column(String(100), nullable=False)  # System that assigned the identifier
    value = Column(String(100), nullable=False)
    use = Column(String(20), nullable=False)  # usual, official, temp, secondary
    type_code = Column(String(10), nullable=False)  # MR, SS, DL, etc.
    type_display = Column(String(100), nullable=True)
    
    # Validity
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)
    
    # System metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    patient = relationship("Patient", back_populates="identifiers")


# Add the identifiers relationship to Patient
Patient.identifiers = relationship("PatientIdentifier", back_populates="patient", cascade="all, delete-orphan")


class PatientConsent(Base):
    """Track patient consent for data usage and sharing."""
    __tablename__ = "patient_consents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    
    # Consent details
    consent_type = Column(String(50), nullable=False)  # treatment, data_sharing, research, etc.
    status = Column(String(20), nullable=False)  # active, inactive, withdrawn
    
    # Scope of consent
    purpose = Column(JSON, nullable=True)  # What the data can be used for
    data_categories = Column(JSON, nullable=True)  # What data is covered
    recipients = Column(JSON, nullable=True)  # Who can access the data
    
    # Consent metadata
    given_at = Column(DateTime(timezone=True), nullable=False)
    withdrawn_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Legal basis
    legal_basis = Column(String(100), nullable=True)
    witness_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Digital signature/proof
    signature_data = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    patient = relationship("Patient")
    witness = relationship("User", foreign_keys=[witness_id])
