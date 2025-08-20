"""
Calibration and Health Monitoring for Medical Devices.

This module provides calibration procedures, health checks,
and quality assurance for connected medical devices.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from app.devices.ble_manager import DeviceManager, DeviceType, DeviceStatus, DeviceInfo
from app.core.config import settings


class CalibrationStatus(Enum):
    """Device calibration status."""
    UNKNOWN = "unknown"
    CALIBRATED = "calibrated"
    NEEDS_CALIBRATION = "needs_calibration"
    CALIBRATING = "calibrating"
    CALIBRATION_FAILED = "calibration_failed"
    OUT_OF_SPEC = "out_of_spec"


class HealthStatus(Enum):
    """Device health status."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    OFFLINE = "offline"
    MAINTENANCE_REQUIRED = "maintenance_required"


@dataclass
class CalibrationRecord:
    """Record of device calibration."""
    device_id: str
    calibration_date: datetime
    calibration_type: str  # "factory", "user", "automated"
    reference_values: Dict[str, float]
    measured_values: Dict[str, float]
    deviation_values: Dict[str, float]
    status: CalibrationStatus
    technician_id: Optional[str] = None
    notes: Optional[str] = None
    next_calibration_due: Optional[datetime] = None
    certificate_number: Optional[str] = None


@dataclass
class HealthMetrics:
    """Device health and performance metrics."""
    device_id: str
    timestamp: datetime
    battery_level: Optional[int] = None
    signal_strength: Optional[int] = None
    measurement_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    uptime: Optional[timedelta] = None
    firmware_version: Optional[str] = None
    quality_score: float = 1.0


class DeviceCalibrator:
    """Handles device calibration procedures."""
    
    def __init__(self, device_manager: DeviceManager):
        self.device_manager = device_manager
        self.logger = logging.getLogger("device_calibrator")
        self.calibration_records: Dict[str, List[CalibrationRecord]] = {}
        
        # Calibration intervals (in days)
        self.calibration_intervals = {
            DeviceType.BLOOD_PRESSURE: 365,  # Annually
            DeviceType.PULSE_OXIMETER: 180,  # Semi-annually
            DeviceType.THERMOMETER: 90,      # Quarterly
            DeviceType.WEIGHT_SCALE: 180,    # Semi-annually
            DeviceType.GLUCOSE_METER: 90,    # Quarterly
        }
        
        # Acceptable deviation thresholds
        self.deviation_thresholds = {
            DeviceType.BLOOD_PRESSURE: {"systolic": 3, "diastolic": 3},  # ±3 mmHg
            DeviceType.PULSE_OXIMETER: {"spo2": 2, "pulse_rate": 3},     # ±2%, ±3 bpm
            DeviceType.THERMOMETER: {"temperature": 0.1},                # ±0.1°C
            DeviceType.WEIGHT_SCALE: {"weight": 0.1},                   # ±0.1 kg
        }
    
    async def check_calibration_status(self, device_id: str) -> CalibrationStatus:
        """Check if device needs calibration."""
        try:
            if device_id not in self.calibration_records:
                return CalibrationStatus.UNKNOWN
            
            records = self.calibration_records[device_id]
            if not records:
                return CalibrationStatus.NEEDS_CALIBRATION
            
            latest_record = max(records, key=lambda r: r.calibration_date)
            
            # Check if calibration is still valid
            device = self.device_manager.devices.get(device_id)
            if not device:
                return CalibrationStatus.UNKNOWN
            
            device_type = device.device_info.device_type
            interval_days = self.calibration_intervals.get(device_type, 180)
            
            days_since_calibration = (datetime.utcnow() - latest_record.calibration_date).days
            
            if days_since_calibration > interval_days:
                return CalibrationStatus.NEEDS_CALIBRATION
            
            return latest_record.status
            
        except Exception as e:
            self.logger.error(f"Error checking calibration status: {e}")
            return CalibrationStatus.UNKNOWN
    
    async def calibrate_blood_pressure_monitor(self, device_id: str, 
                                             reference_systolic: float,
                                             reference_diastolic: float) -> CalibrationRecord:
        """Calibrate blood pressure monitor against reference values."""
        device = self.device_manager.devices.get(device_id)
        if not device or device.device_info.device_type != DeviceType.BLOOD_PRESSURE:
            raise ValueError("Invalid blood pressure device")
        
        self.logger.info(f"Starting BP calibration for device {device_id}")
        
        try:
            # Take multiple readings for accuracy
            readings = []
            for i in range(5):  # Take 5 readings
                self.logger.info(f"Taking BP reading {i+1}/5")
                reading = await device.read_data()
                if reading and "systolic" in reading.values and "diastolic" in reading.values:
                    readings.append(reading)
                await asyncio.sleep(60)  # Wait between readings
            
            if len(readings) < 3:
                raise Exception("Insufficient readings for calibration")
            
            # Calculate average measured values
            avg_systolic = sum(r.values["systolic"] for r in readings) / len(readings)
            avg_diastolic = sum(r.values["diastolic"] for r in readings) / len(readings)
            
            # Calculate deviations
            systolic_deviation = abs(avg_systolic - reference_systolic)
            diastolic_deviation = abs(avg_diastolic - reference_diastolic)
            
            # Determine calibration status
            thresholds = self.deviation_thresholds[DeviceType.BLOOD_PRESSURE]
            status = CalibrationStatus.CALIBRATED
            
            if (systolic_deviation > thresholds["systolic"] or 
                diastolic_deviation > thresholds["diastolic"]):
                status = CalibrationStatus.OUT_OF_SPEC
            
            # Create calibration record
            record = CalibrationRecord(
                device_id=device_id,
                calibration_date=datetime.utcnow(),
                calibration_type="user",
                reference_values={
                    "systolic": reference_systolic,
                    "diastolic": reference_diastolic
                },
                measured_values={
                    "systolic": avg_systolic,
                    "diastolic": avg_diastolic
                },
                deviation_values={
                    "systolic": systolic_deviation,
                    "diastolic": diastolic_deviation
                },
                status=status,
                next_calibration_due=datetime.utcnow() + timedelta(
                    days=self.calibration_intervals[DeviceType.BLOOD_PRESSURE]
                )
            )
            
            # Store calibration record
            if device_id not in self.calibration_records:
                self.calibration_records[device_id] = []
            self.calibration_records[device_id].append(record)
            
            self.logger.info(f"BP calibration completed: {status.value}")
            return record
            
        except Exception as e:
            self.logger.error(f"BP calibration failed: {e}")
            
            error_record = CalibrationRecord(
                device_id=device_id,
                calibration_date=datetime.utcnow(),
                calibration_type="user",
                reference_values={"systolic": reference_systolic, "diastolic": reference_diastolic},
                measured_values={},
                deviation_values={},
                status=CalibrationStatus.CALIBRATION_FAILED,
                notes=str(e)
            )
            
            if device_id not in self.calibration_records:
                self.calibration_records[device_id] = []
            self.calibration_records[device_id].append(error_record)
            
            return error_record
    
    async def calibrate_pulse_oximeter(self, device_id: str,
                                     reference_spo2: float,
                                     reference_pulse: int) -> CalibrationRecord:
        """Calibrate pulse oximeter against reference values."""
        device = self.device_manager.devices.get(device_id)
        if not device or device.device_info.device_type != DeviceType.PULSE_OXIMETER:
            raise ValueError("Invalid pulse oximeter device")
        
        self.logger.info(f"Starting pulse oximeter calibration for device {device_id}")
        
        try:
            # Take multiple readings
            readings = []
            for i in range(10):  # Take 10 readings over 2 minutes
                reading = await device.read_data()
                if reading and "spo2" in reading.values and "pulse_rate" in reading.values:
                    readings.append(reading)
                await asyncio.sleep(12)  # 12 seconds between readings
            
            if len(readings) < 5:
                raise Exception("Insufficient readings for calibration")
            
            # Calculate averages
            avg_spo2 = sum(r.values["spo2"] for r in readings) / len(readings)
            avg_pulse = sum(r.values["pulse_rate"] for r in readings) / len(readings)
            
            # Calculate deviations
            spo2_deviation = abs(avg_spo2 - reference_spo2)
            pulse_deviation = abs(avg_pulse - reference_pulse)
            
            # Determine status
            thresholds = self.deviation_thresholds[DeviceType.PULSE_OXIMETER]
            status = CalibrationStatus.CALIBRATED
            
            if (spo2_deviation > thresholds["spo2"] or 
                pulse_deviation > thresholds["pulse_rate"]):
                status = CalibrationStatus.OUT_OF_SPEC
            
            record = CalibrationRecord(
                device_id=device_id,
                calibration_date=datetime.utcnow(),
                calibration_type="user",
                reference_values={"spo2": reference_spo2, "pulse_rate": reference_pulse},
                measured_values={"spo2": avg_spo2, "pulse_rate": avg_pulse},
                deviation_values={"spo2": spo2_deviation, "pulse_rate": pulse_deviation},
                status=status,
                next_calibration_due=datetime.utcnow() + timedelta(
                    days=self.calibration_intervals[DeviceType.PULSE_OXIMETER]
                )
            )
            
            if device_id not in self.calibration_records:
                self.calibration_records[device_id] = []
            self.calibration_records[device_id].append(record)
            
            self.logger.info(f"Pulse oximeter calibration completed: {status.value}")
            return record
            
        except Exception as e:
            self.logger.error(f"Pulse oximeter calibration failed: {e}")
            
            error_record = CalibrationRecord(
                device_id=device_id,
                calibration_date=datetime.utcnow(),
                calibration_type="user",
                reference_values={"spo2": reference_spo2, "pulse_rate": reference_pulse},
                measured_values={},
                deviation_values={},
                status=CalibrationStatus.CALIBRATION_FAILED,
                notes=str(e)
            )
            
            if device_id not in self.calibration_records:
                self.calibration_records[device_id] = []
            self.calibration_records[device_id].append(error_record)
            
            return error_record
    
    async def get_calibration_history(self, device_id: str) -> List[CalibrationRecord]:
        """Get calibration history for a device."""
        return self.calibration_records.get(device_id, [])


class DeviceHealthMonitor:
    """Monitors device health and performance."""
    
    def __init__(self, device_manager: DeviceManager):
        self.device_manager = device_manager
        self.logger = logging.getLogger("device_health")
        self.health_metrics: Dict[str, List[HealthMetrics]] = {}
        self.monitoring_active = False
    
    async def start_monitoring(self):
        """Start continuous health monitoring."""
        self.monitoring_active = True
        self.logger.info("Starting device health monitoring")
        
        # Start monitoring task
        asyncio.create_task(self._monitoring_loop())
    
    async def stop_monitoring(self):
        """Stop health monitoring."""
        self.monitoring_active = False
        self.logger.info("Stopping device health monitoring")
    
    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.monitoring_active:
            try:
                # Check health of all connected devices
                for device_id, device in self.device_manager.devices.items():
                    await self._check_device_health(device_id, device)
                
                # Wait before next check
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)
    
    async def _check_device_health(self, device_id: str, device):
        """Check health of a specific device."""
        try:
            # Collect health metrics
            metrics = HealthMetrics(
                device_id=device_id,
                timestamp=datetime.utcnow()
            )
            
            # Check device status
            if device.status == DeviceStatus.ERROR:
                metrics.quality_score = 0.0
            elif device.status == DeviceStatus.DISCONNECTED:
                metrics.quality_score = 0.0
            elif device.status == DeviceStatus.CONNECTED:
                metrics.quality_score = 0.8
            else:
                metrics.quality_score = 0.6
            
            # Try to get battery level (if supported)
            try:
                if hasattr(device, 'get_battery_level'):
                    metrics.battery_level = await device.get_battery_level()
            except:
                pass
            
            # Store metrics
            if device_id not in self.health_metrics:
                self.health_metrics[device_id] = []
            
            self.health_metrics[device_id].append(metrics)
            
            # Keep only recent metrics (last 24 hours)
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            self.health_metrics[device_id] = [
                m for m in self.health_metrics[device_id] 
                if m.timestamp > cutoff_time
            ]
            
        except Exception as e:
            self.logger.error(f"Error checking device health: {e}")
    
    async def get_device_health(self, device_id: str) -> Optional[HealthStatus]:
        """Get current health status of a device."""
        if device_id not in self.health_metrics:
            return HealthStatus.OFFLINE
        
        recent_metrics = self.health_metrics[device_id]
        if not recent_metrics:
            return HealthStatus.OFFLINE
        
        latest_metric = recent_metrics[-1]
        
        # Determine health status
        if latest_metric.quality_score >= 0.8:
            return HealthStatus.HEALTHY
        elif latest_metric.quality_score >= 0.6:
            return HealthStatus.WARNING
        else:
            return HealthStatus.CRITICAL
    
    async def get_health_metrics(self, device_id: str, 
                               hours: int = 24) -> List[HealthMetrics]:
        """Get health metrics for a device over specified time period."""
        if device_id not in self.health_metrics:
            return []
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return [
            m for m in self.health_metrics[device_id] 
            if m.timestamp > cutoff_time
        ]
    
    async def generate_health_report(self) -> Dict[str, Any]:
        """Generate comprehensive health report for all devices."""
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "devices": {},
            "summary": {
                "total_devices": len(self.device_manager.devices),
                "healthy": 0,
                "warning": 0,
                "critical": 0,
                "offline": 0
            }
        }
        
        for device_id, device in self.device_manager.devices.items():
            health_status = await self.get_device_health(device_id)
            recent_metrics = await self.get_health_metrics(device_id, 1)  # Last hour
            
            device_report = {
                "device_info": asdict(device.device_info),
                "health_status": health_status.value,
                "current_status": device.status.value,
                "recent_metrics": [asdict(m) for m in recent_metrics[-10:]]  # Last 10 metrics
            }
            
            report["devices"][device_id] = device_report
            
            # Update summary
            if health_status == HealthStatus.HEALTHY:
                report["summary"]["healthy"] += 1
            elif health_status == HealthStatus.WARNING:
                report["summary"]["warning"] += 1
            elif health_status == HealthStatus.CRITICAL:
                report["summary"]["critical"] += 1
            else:
                report["summary"]["offline"] += 1
        
        return report


# Global instances
_device_calibrator = None
_device_health_monitor = None


def get_device_calibrator(device_manager: DeviceManager) -> DeviceCalibrator:
    """Get global device calibrator instance."""
    global _device_calibrator
    if _device_calibrator is None:
        _device_calibrator = DeviceCalibrator(device_manager)
    return _device_calibrator


def get_device_health_monitor(device_manager: DeviceManager) -> DeviceHealthMonitor:
    """Get global device health monitor instance."""
    global _device_health_monitor
    if _device_health_monitor is None:
        _device_health_monitor = DeviceHealthMonitor(device_manager)
    return _device_health_monitor
