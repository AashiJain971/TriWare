"""
Vitals Service for Medical Device Data Processing.

This service handles storing, processing, and analyzing
vital signs and device readings data.
"""

import asyncio
import statistics
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import numpy as np
from scipy import stats
import logging

from app.db.database import get_db
from app.models.vitals import (
    VitalSigns, DeviceReading, VitalType, MeasurementStatus,
    VitalSignCreate, VitalSignUpdate, VitalSignResponse,
    DeviceReadingCreate, DeviceReadingResponse,
    VitalsStatistics, VitalsTrend
)
from app.models.patient import Patient
from app.devices.ble_manager import DeviceReading as BLEDeviceReading
from app.core.config import settings


class VitalsService:
    """Service for managing vital signs and device readings."""
    
    def __init__(self):
        self.logger = logging.getLogger("vitals_service")
        
        # Normal ranges for vital signs
        self.normal_ranges = {
            VitalType.BLOOD_PRESSURE: {
                "systolic": {"min": 90, "max": 140, "unit": "mmHg"},
                "diastolic": {"min": 60, "max": 90, "unit": "mmHg"}
            },
            VitalType.HEART_RATE: {"min": 60, "max": 100, "unit": "bpm"},
            VitalType.TEMPERATURE: {"min": 36.1, "max": 37.2, "unit": "°C"},
            VitalType.OXYGEN_SATURATION: {"min": 95, "max": 100, "unit": "%"},
            VitalType.RESPIRATORY_RATE: {"min": 12, "max": 20, "unit": "/min"},
            VitalType.WEIGHT: {"min": 2, "max": 300, "unit": "kg"},
            VitalType.HEIGHT: {"min": 30, "max": 250, "unit": "cm"},
            VitalType.BMI: {"min": 15, "max": 40, "unit": "kg/m²"},
            VitalType.GLUCOSE: {"min": 70, "max": 140, "unit": "mg/dL"},
            VitalType.PAIN_SCORE: {"min": 0, "max": 10, "unit": "score"}
        }
    
    async def store_device_reading(self, ble_reading: BLEDeviceReading) -> DeviceReading:
        """Store a BLE device reading in the database."""
        try:
            db = next(get_db())
            
            # Create device reading record
            db_reading = DeviceReading(
                device_id=ble_reading.device_id,
                device_type=ble_reading.device_type.value,
                timestamp=ble_reading.timestamp,
                values=ble_reading.values,
                unit=ble_reading.unit,
                quality_score=ble_reading.quality_score,
                reading_type="automatic",
                metadata=ble_reading.metadata,
                raw_data=str(ble_reading.metadata) if ble_reading.metadata else None
            )
            
            db.add(db_reading)
            db.commit()
            db.refresh(db_reading)
            
            # Process reading into vital signs if associated with patient
            if db_reading.patient_id:
                await self._process_device_reading_to_vitals(db, db_reading)
            
            self.logger.info(f"Stored device reading: {db_reading.id}")
            return db_reading
            
        except Exception as e:
            self.logger.error(f"Error storing device reading: {e}")
            raise
        finally:
            db.close()
    
    async def create_vital_sign(self, db: Session, vital_data: VitalSignCreate) -> VitalSigns:
        """Create a new vital sign record."""
        try:
            # Get reference range for vital type
            reference_range = vital_data.reference_range
            if not reference_range and vital_data.vital_type in self.normal_ranges:
                reference_range = self.normal_ranges[vital_data.vital_type]
            
            # Create vital sign
            db_vital = VitalSigns(
                patient_id=vital_data.patient_id,
                device_id=vital_data.device_id,
                vital_type=vital_data.vital_type.value,
                value=vital_data.value,
                unit=vital_data.unit,
                reference_range=reference_range,
                measurement_method=vital_data.measurement_method,
                body_position=vital_data.body_position,
                quality_score=vital_data.quality_score,
                notes=vital_data.notes,
                metadata=vital_data.metadata
            )
            
            # Determine measurement status based on normal range
            if reference_range:
                is_normal = db_vital.is_normal
                if is_normal is False:
                    # Check if critically abnormal
                    if self._is_critical_value(vital_data.vital_type, vital_data.value):
                        db_vital.measurement_status = MeasurementStatus.CRITICAL.value
                    else:
                        db_vital.measurement_status = MeasurementStatus.ABNORMAL.value
                else:
                    db_vital.measurement_status = MeasurementStatus.NORMAL.value
            
            db.add(db_vital)
            db.commit()
            db.refresh(db_vital)
            
            self.logger.info(f"Created vital sign: {db_vital.id} for patient {vital_data.patient_id}")
            return db_vital
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error creating vital sign: {e}")
            raise
    
    async def update_vital_sign(self, db: Session, vital_id: int, 
                              update_data: VitalSignUpdate) -> Optional[VitalSigns]:
        """Update an existing vital sign record."""
        try:
            db_vital = db.query(VitalSigns).filter(VitalSigns.id == vital_id).first()
            if not db_vital:
                return None
            
            # Update fields
            for field, value in update_data.dict(exclude_unset=True).items():
                if hasattr(db_vital, field):
                    setattr(db_vital, field, value)
            
            db_vital.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(db_vital)
            
            return db_vital
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error updating vital sign: {e}")
            raise
    
    async def get_patient_vitals(self, db: Session, patient_id: int, 
                               vital_type: Optional[VitalType] = None,
                               hours: int = 24, limit: int = 100) -> List[VitalSigns]:
        """Get vital signs for a patient."""
        try:
            query = db.query(VitalSigns).filter(VitalSigns.patient_id == patient_id)
            
            if vital_type:
                query = query.filter(VitalSigns.vital_type == vital_type.value)
            
            # Filter by time range
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            query = query.filter(VitalSigns.measurement_date >= cutoff_time)
            
            # Order by most recent first
            query = query.order_by(VitalSigns.measurement_date.desc())
            
            # Limit results
            query = query.limit(limit)
            
            return query.all()
            
        except Exception as e:
            self.logger.error(f"Error getting patient vitals: {e}")
            raise
    
    async def get_latest_vitals(self, db: Session, patient_id: int) -> Dict[str, VitalSigns]:
        """Get latest vital sign of each type for a patient."""
        try:
            latest_vitals = {}
            
            # Get latest vital for each type
            for vital_type in VitalType:
                latest = (db.query(VitalSigns)
                         .filter(and_(
                             VitalSigns.patient_id == patient_id,
                             VitalSigns.vital_type == vital_type.value
                         ))
                         .order_by(VitalSigns.measurement_date.desc())
                         .first())
                
                if latest:
                    latest_vitals[vital_type.value] = latest
            
            return latest_vitals
            
        except Exception as e:
            self.logger.error(f"Error getting latest vitals: {e}")
            raise
    
    async def calculate_vitals_statistics(self, db: Session, patient_id: int,
                                        vital_type: VitalType, days: int = 30) -> VitalsStatistics:
        """Calculate statistics for a patient's vital signs."""
        try:
            # Get vital signs for the period
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            vitals = (db.query(VitalSigns)
                     .filter(and_(
                         VitalSigns.patient_id == patient_id,
                         VitalSigns.vital_type == vital_type.value,
                         VitalSigns.measurement_date >= cutoff_date
                     ))
                     .order_by(VitalSigns.measurement_date.asc())
                     .all())
            
            if not vitals:
                return VitalsStatistics(
                    vital_type=vital_type,
                    patient_id=patient_id,
                    period_days=days,
                    count=0
                )
            
            values = [v.value for v in vitals]
            
            # Calculate statistics
            stats = VitalsStatistics(
                vital_type=vital_type,
                patient_id=patient_id,
                period_days=days,
                count=len(values),
                mean=statistics.mean(values),
                median=statistics.median(values),
                min_value=min(values),
                max_value=max(values),
                std_dev=statistics.stdev(values) if len(values) > 1 else 0,
                last_measurement=vitals[-1].measurement_date
            )
            
            # Calculate trend
            if len(values) >= 3:
                stats.trend = self._calculate_trend(values)
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error calculating vitals statistics: {e}")
            raise
    
    async def detect_vital_trends(self, db: Session, patient_id: int,
                                vital_type: VitalType, days: int = 7) -> VitalsTrend:
        """Detect trends in vital signs over time."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            vitals = (db.query(VitalSigns)
                     .filter(and_(
                         VitalSigns.patient_id == patient_id,
                         VitalSigns.vital_type == vital_type.value,
                         VitalSigns.measurement_date >= cutoff_date
                     ))
                     .order_by(VitalSigns.measurement_date.asc())
                     .all())
            
            if len(vitals) < 3:
                return VitalsTrend(
                    vital_type=vital_type,
                    patient_id=patient_id,
                    measurements=[],
                    trend_direction="stable",
                    trend_strength=0.0
                )
            
            # Prepare data for trend analysis
            measurements = [
                {
                    "timestamp": v.measurement_date.isoformat(),
                    "value": v.value
                }
                for v in vitals
            ]
            
            # Calculate linear regression
            x = np.arange(len(vitals))
            y = np.array([v.value for v in vitals])
            
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
            
            # Determine trend direction and strength
            if abs(slope) < 0.1:  # Minimal slope
                trend_direction = "stable"
            elif slope > 0:
                trend_direction = "up"
            else:
                trend_direction = "down"
            
            # Use R² as trend strength
            trend_strength = r_value ** 2
            
            return VitalsTrend(
                vital_type=vital_type,
                patient_id=patient_id,
                measurements=measurements,
                trend_direction=trend_direction,
                trend_strength=trend_strength,
                correlation_coefficient=r_value
            )
            
        except Exception as e:
            self.logger.error(f"Error detecting vital trends: {e}")
            raise
    
    async def check_critical_vitals(self, db: Session, patient_id: int) -> List[Dict[str, Any]]:
        """Check for critical vital signs in the last 24 hours."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            
            critical_vitals = (db.query(VitalSigns)
                             .filter(and_(
                                 VitalSigns.patient_id == patient_id,
                                 VitalSigns.measurement_date >= cutoff_time,
                                 VitalSigns.measurement_status == MeasurementStatus.CRITICAL.value
                             ))
                             .order_by(VitalSigns.measurement_date.desc())
                             .all())
            
            alerts = []
            for vital in critical_vitals:
                alert = {
                    "vital_id": vital.id,
                    "vital_type": vital.vital_type,
                    "value": vital.value,
                    "unit": vital.unit,
                    "measurement_date": vital.measurement_date.isoformat(),
                    "severity": self._get_alert_severity(vital.vital_type, vital.value),
                    "message": self._generate_alert_message(vital.vital_type, vital.value, vital.unit)
                }
                alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            self.logger.error(f"Error checking critical vitals: {e}")
            raise
    
    async def _process_device_reading_to_vitals(self, db: Session, reading: DeviceReading):
        """Process device reading into vital signs records."""
        try:
            # Map device reading to vital signs
            if reading.device_type == "blood_pressure" and "systolic" in reading.values:
                # Create systolic BP vital
                systolic_vital = VitalSignCreate(
                    patient_id=reading.patient_id,
                    device_id=reading.device_id,
                    vital_type=VitalType.BLOOD_PRESSURE,
                    value=reading.values["systolic"],
                    unit="mmHg",
                    measurement_method="automatic",
                    quality_score=reading.quality_score
                )
                
                await self.create_vital_sign(db, systolic_vital)
                
                # Create diastolic BP vital if available
                if "diastolic" in reading.values:
                    diastolic_vital = VitalSignCreate(
                        patient_id=reading.patient_id,
                        device_id=reading.device_id,
                        vital_type=VitalType.BLOOD_PRESSURE,
                        value=reading.values["diastolic"],
                        unit="mmHg",
                        measurement_method="automatic",
                        quality_score=reading.quality_score
                    )
                    
                    await self.create_vital_sign(db, diastolic_vital)
            
            elif reading.device_type == "pulse_oximeter":
                # Create SpO2 vital
                if "spo2" in reading.values:
                    spo2_vital = VitalSignCreate(
                        patient_id=reading.patient_id,
                        device_id=reading.device_id,
                        vital_type=VitalType.OXYGEN_SATURATION,
                        value=reading.values["spo2"],
                        unit="%",
                        measurement_method="automatic",
                        quality_score=reading.quality_score
                    )
                    
                    await self.create_vital_sign(db, spo2_vital)
                
                # Create heart rate vital
                if "pulse_rate" in reading.values:
                    hr_vital = VitalSignCreate(
                        patient_id=reading.patient_id,
                        device_id=reading.device_id,
                        vital_type=VitalType.HEART_RATE,
                        value=reading.values["pulse_rate"],
                        unit="bpm",
                        measurement_method="automatic",
                        quality_score=reading.quality_score
                    )
                    
                    await self.create_vital_sign(db, hr_vital)
            
            elif reading.device_type == "thermometer" and "temperature" in reading.values:
                temp_vital = VitalSignCreate(
                    patient_id=reading.patient_id,
                    device_id=reading.device_id,
                    vital_type=VitalType.TEMPERATURE,
                    value=reading.values["temperature"],
                    unit="°C",
                    measurement_method="automatic",
                    quality_score=reading.quality_score
                )
                
                await self.create_vital_sign(db, temp_vital)
            
            # Mark reading as processed
            reading.processed = True
            reading.processed_at = datetime.utcnow()
            db.commit()
            
        except Exception as e:
            self.logger.error(f"Error processing device reading to vitals: {e}")
            raise
    
    def _is_critical_value(self, vital_type: VitalType, value: float) -> bool:
        """Check if a vital sign value is critically abnormal."""
        critical_ranges = {
            VitalType.BLOOD_PRESSURE: {
                "systolic": {"critical_high": 180, "critical_low": 70},
                "diastolic": {"critical_high": 120, "critical_low": 40}
            },
            VitalType.HEART_RATE: {"critical_high": 150, "critical_low": 40},
            VitalType.TEMPERATURE: {"critical_high": 39.5, "critical_low": 35.0},
            VitalType.OXYGEN_SATURATION: {"critical_high": None, "critical_low": 90},
            VitalType.RESPIRATORY_RATE: {"critical_high": 30, "critical_low": 8}
        }
        
        if vital_type not in critical_ranges:
            return False
        
        ranges = critical_ranges[vital_type]
        
        if isinstance(ranges, dict) and "critical_high" in ranges:
            if ranges["critical_high"] and value > ranges["critical_high"]:
                return True
            if ranges["critical_low"] and value < ranges["critical_low"]:
                return True
        
        return False
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from a series of values."""
        if len(values) < 3:
            return "stable"
        
        # Simple trend calculation using first and last values
        first_half_avg = statistics.mean(values[:len(values)//2])
        second_half_avg = statistics.mean(values[len(values)//2:])
        
        difference = second_half_avg - first_half_avg
        
        # Use 5% change as threshold
        threshold = first_half_avg * 0.05
        
        if abs(difference) < threshold:
            return "stable"
        elif difference > 0:
            return "increasing"
        else:
            return "decreasing"
    
    def _get_alert_severity(self, vital_type: str, value: float) -> str:
        """Get alert severity level for a critical vital sign."""
        # This could be expanded with more sophisticated severity assessment
        if vital_type == "temperature" and value > 40.0:
            return "emergency"
        elif vital_type == "oxygen_saturation" and value < 85:
            return "emergency"
        elif vital_type == "heart_rate" and (value > 180 or value < 30):
            return "emergency"
        else:
            return "critical"
    
    def _generate_alert_message(self, vital_type: str, value: float, unit: str) -> str:
        """Generate human-readable alert message."""
        vital_name = vital_type.replace("_", " ").title()
        return f"{vital_name} is critically abnormal: {value} {unit}"


# Global service instance
vitals_service = VitalsService()
