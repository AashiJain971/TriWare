"""
Vitals and Medical Device Data Models.

This module defines data models for vital signs, device readings,
and medical measurements with FHIR compliance.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, Field, validator
from enum import Enum

from app.db.base_class import Base
from app.models.patient import Patient


class VitalType(str, Enum):
    """Types of vital sign measurements."""
    BLOOD_PRESSURE = "blood_pressure"
    HEART_RATE = "heart_rate"
    TEMPERATURE = "temperature"
    OXYGEN_SATURATION = "oxygen_saturation"
    RESPIRATORY_RATE = "respiratory_rate"
    WEIGHT = "weight"
    HEIGHT = "height"
    BMI = "bmi"
    GLUCOSE = "glucose"
    PAIN_SCORE = "pain_score"


class MeasurementStatus(str, Enum):
    """Status of vital sign measurement."""
    NORMAL = "normal"
    ABNORMAL = "abnormal"
    CRITICAL = "critical"
    ERROR = "error"
    PRELIMINARY = "preliminary"
    FINAL = "final"


# Database Models
class VitalSigns(Base):
    """Vital signs database model."""
    
    __tablename__ = "vital_signs"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    device_id = Column(String, nullable=True)  # Medical device that took the measurement
    
    # Measurement details
    vital_type = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    reference_range = Column(JSON, nullable=True)  # {"min": 60, "max": 100}
    
    # Measurement context
    measurement_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    measurement_method = Column(String, nullable=True)  # "automatic", "manual", "estimated"
    body_position = Column(String, nullable=True)  # "sitting", "standing", "lying"
    measurement_status = Column(String, nullable=False, default="preliminary")
    
    # Quality and validation
    quality_score = Column(Float, nullable=True)  # 0-1 quality indicator
    validated_by = Column(String, nullable=True)  # Healthcare provider who validated
    validation_date = Column(DateTime, nullable=True)
    
    # Additional data
    notes = Column(Text, nullable=True)
    metadata = Column(JSON, nullable=True)  # Additional measurement metadata
    
    # FHIR compliance
    fhir_observation_id = Column(String, nullable=True, unique=True)
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String, nullable=True)
    
    # Relationships
    patient = relationship("Patient", back_populates="vital_signs")
    
    def __repr__(self):
        return f"<VitalSigns(patient_id={self.patient_id}, type={self.vital_type}, value={self.value})>"
    
    @property
    def is_normal(self) -> Optional[bool]:
        """Check if vital sign is within normal range."""
        if not self.reference_range:
            return None
        
        min_val = self.reference_range.get("min")
        max_val = self.reference_range.get("max")
        
        if min_val is not None and self.value < min_val:
            return False
        if max_val is not None and self.value > max_val:
            return False
        
        return True
    
    def to_fhir_observation(self) -> Dict[str, Any]:
        """Convert to FHIR Observation resource."""
        observation = {
            "resourceType": "Observation",
            "id": self.fhir_observation_id or str(self.id),
            "status": self._map_status_to_fhir(),
            "category": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                            "code": "vital-signs",
                            "display": "Vital Signs"
                        }
                    ]
                }
            ],
            "code": self._get_fhir_code(),
            "subject": {
                "reference": f"Patient/{self.patient_id}"
            },
            "effectiveDateTime": self.measurement_date.isoformat(),
            "valueQuantity": {
                "value": self.value,
                "unit": self.unit,
                "system": "http://unitsofmeasure.org"
            }
        }
        
        # Add reference range if available
        if self.reference_range:
            observation["referenceRange"] = [
                {
                    "low": {"value": self.reference_range.get("min"), "unit": self.unit},
                    "high": {"value": self.reference_range.get("max"), "unit": self.unit}
                }
            ]
        
        # Add device information if available
        if self.device_id:
            observation["device"] = {
                "reference": f"Device/{self.device_id}"
            }
        
        return observation
    
    def _map_status_to_fhir(self) -> str:
        """Map measurement status to FHIR status."""
        status_mapping = {
            "preliminary": "preliminary",
            "final": "final",
            "error": "entered-in-error",
            "normal": "final",
            "abnormal": "final",
            "critical": "final"
        }
        return status_mapping.get(self.measurement_status, "preliminary")
    
    def _get_fhir_code(self) -> Dict[str, Any]:
        """Get FHIR LOINC code for vital type."""
        loinc_codes = {
            "blood_pressure": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "85354-9",
                        "display": "Blood pressure panel with all children optional"
                    }
                ]
            },
            "heart_rate": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "8867-4",
                        "display": "Heart rate"
                    }
                ]
            },
            "temperature": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "8310-5",
                        "display": "Body temperature"
                    }
                ]
            },
            "oxygen_saturation": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "2708-6",
                        "display": "Oxygen saturation in Arterial blood"
                    }
                ]
            },
            "respiratory_rate": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "9279-1",
                        "display": "Respiratory rate"
                    }
                ]
            },
            "weight": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "29463-7",
                        "display": "Body weight"
                    }
                ]
            },
            "height": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "8302-2",
                        "display": "Body height"
                    }
                ]
            }
        }
        
        return loinc_codes.get(self.vital_type, {
            "text": self.vital_type.replace("_", " ").title()
        })


class DeviceReading(Base):
    """Medical device reading database model."""
    
    __tablename__ = "device_readings"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Device information
    device_id = Column(String, nullable=False, index=True)
    device_type = Column(String, nullable=False)
    device_name = Column(String, nullable=True)
    
    # Patient association (optional - may be system readings)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)
    
    # Reading data
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    values = Column(JSON, nullable=False)  # Measurement values as JSON
    unit = Column(String, nullable=False)
    quality_score = Column(Float, nullable=True)  # 0-1 quality indicator
    
    # Reading context
    reading_type = Column(String, nullable=True)  # "manual", "automatic", "continuous"
    calibration_status = Column(String, nullable=True)
    environmental_conditions = Column(JSON, nullable=True)
    
    # Processing status
    processed = Column(Boolean, default=False)
    processed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Raw data and metadata
    raw_data = Column(Text, nullable=True)  # Raw device data
    metadata = Column(JSON, nullable=True)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    patient = relationship("Patient", back_populates="device_readings")
    
    def __repr__(self):
        return f"<DeviceReading(device_id={self.device_id}, type={self.device_type}, timestamp={self.timestamp})>"


# Pydantic Models for API
class VitalSignBase(BaseModel):
    """Base model for vital signs."""
    vital_type: VitalType
    value: float = Field(..., description="Measured value")
    unit: str = Field(..., description="Unit of measurement")
    measurement_method: Optional[str] = Field(None, description="How the measurement was taken")
    body_position: Optional[str] = Field(None, description="Patient position during measurement")
    notes: Optional[str] = None


class VitalSignCreate(VitalSignBase):
    """Model for creating vital signs."""
    patient_id: int
    device_id: Optional[str] = None
    reference_range: Optional[Dict[str, float]] = None
    quality_score: Optional[float] = Field(None, ge=0, le=1)
    metadata: Optional[Dict[str, Any]] = None


class VitalSignUpdate(BaseModel):
    """Model for updating vital signs."""
    value: Optional[float] = None
    unit: Optional[str] = None
    measurement_status: Optional[MeasurementStatus] = None
    notes: Optional[str] = None
    validated_by: Optional[str] = None


class VitalSignResponse(VitalSignBase):
    """Model for vital sign responses."""
    id: int
    patient_id: int
    device_id: Optional[str] = None
    measurement_date: datetime
    measurement_status: MeasurementStatus
    quality_score: Optional[float] = None
    reference_range: Optional[Dict[str, float]] = None
    is_normal: Optional[bool] = None
    validated_by: Optional[str] = None
    validation_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class VitalSignsPanel(BaseModel):
    """Complete vital signs panel."""
    patient_id: int
    measurement_date: datetime
    blood_pressure_systolic: Optional[float] = None
    blood_pressure_diastolic: Optional[float] = None
    heart_rate: Optional[float] = None
    temperature: Optional[float] = None
    oxygen_saturation: Optional[float] = None
    respiratory_rate: Optional[float] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    bmi: Optional[float] = None
    pain_score: Optional[int] = Field(None, ge=0, le=10)
    
    @validator('bmi', always=True)
    def calculate_bmi(cls, v, values):
        """Calculate BMI if weight and height are provided."""
        if v is not None:
            return v
        
        weight = values.get('weight')
        height = values.get('height')
        
        if weight and height and height > 0:
            # Convert height from cm to m if needed
            height_m = height / 100 if height > 3 else height
            return round(weight / (height_m ** 2), 1)
        
        return v


class DeviceReadingBase(BaseModel):
    """Base model for device readings."""
    device_id: str
    device_type: str
    values: Dict[str, Any]
    unit: str
    quality_score: Optional[float] = Field(None, ge=0, le=1)
    reading_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class DeviceReadingCreate(DeviceReadingBase):
    """Model for creating device readings."""
    patient_id: Optional[int] = None
    timestamp: Optional[datetime] = None
    raw_data: Optional[str] = None


class DeviceReadingResponse(DeviceReadingBase):
    """Model for device reading responses."""
    id: int
    patient_id: Optional[int] = None
    timestamp: datetime
    processed: bool
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class VitalsStatistics(BaseModel):
    """Vital signs statistics."""
    vital_type: VitalType
    patient_id: int
    period_days: int
    count: int
    mean: Optional[float] = None
    median: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    std_dev: Optional[float] = None
    trend: Optional[str] = None  # "increasing", "decreasing", "stable"
    last_measurement: Optional[datetime] = None


class VitalsTrend(BaseModel):
    """Vital signs trend data."""
    vital_type: VitalType
    patient_id: int
    measurements: List[Dict[str, Any]]  # List of {timestamp, value} pairs
    trend_direction: str  # "up", "down", "stable"
    trend_strength: float  # 0-1, strength of trend
    correlation_coefficient: Optional[float] = None
