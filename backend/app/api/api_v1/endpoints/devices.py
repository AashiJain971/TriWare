"""
Device Integration API Endpoints.

This module provides REST API endpoints for medical device
discovery, connection, calibration, and data collection.
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import json

from app.core.security import get_current_user
from app.models.user import User
from app.devices.ble_manager import (
    device_manager, DeviceInfo, DeviceType, 
    DeviceStatus, DeviceReading
)
from app.devices.calibration import (
    get_device_calibrator, get_device_health_monitor,
    CalibrationRecord, CalibrationStatus, HealthStatus, HealthMetrics
)


router = APIRouter(prefix="/devices", tags=["device-integration"])


# Request/Response Models
class DeviceDiscoveryResponse(BaseModel):
    devices: List[Dict[str, Any]]
    scan_duration: int
    timestamp: datetime


class DeviceConnectionRequest(BaseModel):
    device_id: str
    auto_calibrate: bool = Field(default=False)


class DeviceConnectionResponse(BaseModel):
    device_id: str
    status: str
    connected: bool
    message: str


class CalibrationRequest(BaseModel):
    device_id: str
    device_type: DeviceType
    reference_values: Dict[str, float] = Field(
        description="Reference values for calibration (e.g., {'systolic': 120, 'diastolic': 80})"
    )
    technician_id: Optional[str] = None
    notes: Optional[str] = None


class CalibrationResponse(BaseModel):
    calibration_id: str
    device_id: str
    status: CalibrationStatus
    reference_values: Dict[str, float]
    measured_values: Dict[str, float]
    deviation_values: Dict[str, float]
    calibration_date: datetime
    next_calibration_due: Optional[datetime]
    passed: bool


class DeviceStatusResponse(BaseModel):
    device_id: str
    device_name: str
    device_type: DeviceType
    connection_status: DeviceStatus
    health_status: HealthStatus
    calibration_status: CalibrationStatus
    battery_level: Optional[int]
    last_reading: Optional[datetime]
    uptime: Optional[str]


class DeviceReadingsResponse(BaseModel):
    device_id: str
    readings: List[Dict[str, Any]]
    total_count: int
    time_range: Dict[str, datetime]


# Device Discovery Endpoints
@router.post("/discover", response_model=DeviceDiscoveryResponse)
async def discover_devices(
    duration: int = Query(default=10, ge=5, le=60, description="Scan duration in seconds"),
    current_user: User = Depends(get_current_user)
):
    """
    Discover available medical devices via Bluetooth.
    
    Scans for BLE medical devices including:
    - Blood pressure monitors
    - Pulse oximeters  
    - Digital thermometers
    - Weight scales
    - Height measurement devices
    """
    try:
        discovered_devices = await device_manager.start_discovery(duration)
        
        devices_data = []
        for device in discovered_devices:
            devices_data.append({
                "device_id": device.device_id,
                "name": device.name,
                "manufacturer": device.manufacturer,
                "model": device.model,
                "device_type": device.device_type.value,
                "mac_address": device.mac_address,
                "rssi": device.rssi,
                "battery_level": device.battery_level,
                "last_seen": device.last_seen.isoformat() if device.last_seen else None,
                "is_paired": device.is_paired
            })
        
        return DeviceDiscoveryResponse(
            devices=devices_data,
            scan_duration=duration,
            timestamp=datetime.utcnow()
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Device discovery failed: {str(e)}"
        )


# Device Connection Endpoints
@router.post("/connect", response_model=DeviceConnectionResponse)
async def connect_device(
    request: DeviceConnectionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Connect to a discovered medical device.
    
    Establishes BLE connection and optionally performs automatic calibration.
    """
    try:
        # Find device info (would typically be stored from discovery)
        # For now, we'll need the device info to be passed or stored
        
        # This would normally retrieve from a device registry
        device_info = await _get_device_info(request.device_id)
        if not device_info:
            raise HTTPException(
                status_code=404, 
                detail=f"Device not found: {request.device_id}"
            )
        
        # Attempt connection
        success = await device_manager.connect_device(device_info)
        
        if success:
            # Start health monitoring if not already running
            health_monitor = get_device_health_monitor(device_manager)
            if not health_monitor.monitoring_active:
                background_tasks.add_task(health_monitor.start_monitoring)
            
            # Perform auto-calibration if requested
            if request.auto_calibrate:
                calibrator = get_device_calibrator(device_manager)
                background_tasks.add_task(
                    _auto_calibrate_device, 
                    request.device_id, 
                    device_info.device_type
                )
            
            return DeviceConnectionResponse(
                device_id=request.device_id,
                status="connected",
                connected=True,
                message=f"Successfully connected to {device_info.name}"
            )
        else:
            return DeviceConnectionResponse(
                device_id=request.device_id,
                status="failed",
                connected=False,
                message=f"Failed to connect to {device_info.name}"
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Connection failed: {str(e)}"
        )


@router.post("/disconnect/{device_id}")
async def disconnect_device(
    device_id: str,
    current_user: User = Depends(get_current_user)
):
    """Disconnect from a medical device."""
    try:
        success = await device_manager.disconnect_device(device_id)
        
        if success:
            return {"message": f"Device {device_id} disconnected successfully"}
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Device not found or already disconnected: {device_id}"
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Disconnection failed: {str(e)}"
        )


# Device Status and Health Endpoints
@router.get("/status", response_model=List[DeviceStatusResponse])
async def get_devices_status(
    current_user: User = Depends(get_current_user)
):
    """Get status of all connected devices."""
    try:
        devices_status = []
        
        calibrator = get_device_calibrator(device_manager)
        health_monitor = get_device_health_monitor(device_manager)
        
        for device_id, device in device_manager.devices.items():
            health_status = await health_monitor.get_device_health(device_id)
            calibration_status = await calibrator.check_calibration_status(device_id)
            
            # Get recent metrics for additional info
            recent_metrics = await health_monitor.get_health_metrics(device_id, 1)
            battery_level = None
            if recent_metrics:
                battery_level = recent_metrics[-1].battery_level
            
            devices_status.append(DeviceStatusResponse(
                device_id=device_id,
                device_name=device.device_info.name,
                device_type=device.device_info.device_type,
                connection_status=device.status,
                health_status=health_status,
                calibration_status=calibration_status,
                battery_level=battery_level,
                last_reading=None,  # Would get from readings database
                uptime=None  # Would calculate from connection time
            ))
        
        return devices_status
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get device status: {str(e)}"
        )


@router.get("/status/{device_id}", response_model=DeviceStatusResponse)
async def get_device_status(
    device_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get detailed status of a specific device."""
    try:
        if device_id not in device_manager.devices:
            raise HTTPException(
                status_code=404,
                detail=f"Device not found: {device_id}"
            )
        
        device = device_manager.devices[device_id]
        
        calibrator = get_device_calibrator(device_manager)
        health_monitor = get_device_health_monitor(device_manager)
        
        health_status = await health_monitor.get_device_health(device_id)
        calibration_status = await calibrator.check_calibration_status(device_id)
        
        # Get recent metrics
        recent_metrics = await health_monitor.get_health_metrics(device_id, 1)
        battery_level = None
        if recent_metrics:
            battery_level = recent_metrics[-1].battery_level
        
        return DeviceStatusResponse(
            device_id=device_id,
            device_name=device.device_info.name,
            device_type=device.device_info.device_type,
            connection_status=device.status,
            health_status=health_status,
            calibration_status=calibration_status,
            battery_level=battery_level,
            last_reading=None,
            uptime=None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get device status: {str(e)}"
        )


# Device Calibration Endpoints
@router.post("/calibrate", response_model=CalibrationResponse)
async def calibrate_device(
    request: CalibrationRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Calibrate a medical device against reference values.
    
    Performs device calibration by comparing device readings
    with known reference values and calculating deviations.
    """
    try:
        if request.device_id not in device_manager.devices:
            raise HTTPException(
                status_code=404,
                detail=f"Device not found: {request.device_id}"
            )
        
        calibrator = get_device_calibrator(device_manager)
        
        # Perform calibration based on device type
        if request.device_type == DeviceType.BLOOD_PRESSURE:
            if "systolic" not in request.reference_values or "diastolic" not in request.reference_values:
                raise HTTPException(
                    status_code=400,
                    detail="Blood pressure calibration requires 'systolic' and 'diastolic' reference values"
                )
            
            record = await calibrator.calibrate_blood_pressure_monitor(
                request.device_id,
                request.reference_values["systolic"],
                request.reference_values["diastolic"]
            )
        
        elif request.device_type == DeviceType.PULSE_OXIMETER:
            if "spo2" not in request.reference_values or "pulse_rate" not in request.reference_values:
                raise HTTPException(
                    status_code=400,
                    detail="Pulse oximeter calibration requires 'spo2' and 'pulse_rate' reference values"
                )
            
            record = await calibrator.calibrate_pulse_oximeter(
                request.device_id,
                request.reference_values["spo2"],
                int(request.reference_values["pulse_rate"])
            )
        
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Calibration not implemented for device type: {request.device_type.value}"
            )
        
        return CalibrationResponse(
            calibration_id=f"cal_{device_id}_{int(record.calibration_date.timestamp())}",
            device_id=record.device_id,
            status=record.status,
            reference_values=record.reference_values,
            measured_values=record.measured_values,
            deviation_values=record.deviation_values,
            calibration_date=record.calibration_date,
            next_calibration_due=record.next_calibration_due,
            passed=(record.status == CalibrationStatus.CALIBRATED)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Calibration failed: {str(e)}"
        )


@router.get("/calibration/{device_id}")
async def get_calibration_history(
    device_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get calibration history for a device."""
    try:
        calibrator = get_device_calibrator(device_manager)
        records = await calibrator.get_calibration_history(device_id)
        
        return {
            "device_id": device_id,
            "calibration_records": [
                {
                    "calibration_date": record.calibration_date.isoformat(),
                    "calibration_type": record.calibration_type,
                    "status": record.status.value,
                    "reference_values": record.reference_values,
                    "measured_values": record.measured_values,
                    "deviation_values": record.deviation_values,
                    "next_calibration_due": record.next_calibration_due.isoformat() if record.next_calibration_due else None,
                    "technician_id": record.technician_id,
                    "notes": record.notes
                }
                for record in records
            ]
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get calibration history: {str(e)}"
        )


# Data Collection Endpoints
@router.post("/read/{device_id}")
async def trigger_device_reading(
    device_id: str,
    current_user: User = Depends(get_current_user)
):
    """Trigger a manual reading from a medical device."""
    try:
        if device_id not in device_manager.devices:
            raise HTTPException(
                status_code=404,
                detail=f"Device not found: {device_id}"
            )
        
        device = device_manager.devices[device_id]
        reading = await device.read_data()
        
        if reading:
            return {
                "device_id": reading.device_id,
                "device_type": reading.device_type.value,
                "timestamp": reading.timestamp.isoformat(),
                "values": reading.values,
                "unit": reading.unit,
                "quality_score": reading.quality_score,
                "metadata": reading.metadata
            }
        else:
            return {
                "message": "Reading initiated - data will be available via notifications",
                "device_id": device_id
            }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read device data: {str(e)}"
        )


@router.get("/readings/{device_id}", response_model=DeviceReadingsResponse)
async def get_device_readings(
    device_id: str,
    hours: int = Query(default=24, ge=1, le=168, description="Hours of history to retrieve"),
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum number of readings"),
    current_user: User = Depends(get_current_user)
):
    """Get historical readings from a device."""
    try:
        # This would typically query the database for stored readings
        # For now, return placeholder response
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        return DeviceReadingsResponse(
            device_id=device_id,
            readings=[],  # Would be populated from database
            total_count=0,
            time_range={
                "start": start_time,
                "end": end_time
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get device readings: {str(e)}"
        )


# Real-time Data Streaming
@router.get("/stream/{device_id}")
async def stream_device_data(
    device_id: str,
    current_user: User = Depends(get_current_user)
):
    """Stream real-time data from a medical device."""
    if device_id not in device_manager.devices:
        raise HTTPException(
            status_code=404,
            detail=f"Device not found: {device_id}"
        )
    
    async def generate_stream():
        """Generate real-time data stream."""
        try:
            while True:
                # This would typically read from a real-time data queue
                # For demonstration, we'll send periodic status updates
                
                device = device_manager.devices.get(device_id)
                if not device:
                    break
                
                data = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "device_id": device_id,
                    "status": device.status.value,
                    "type": "status_update"
                }
                
                yield f"data: {json.dumps(data)}\n\n"
                await asyncio.sleep(5)  # Send update every 5 seconds
                
        except Exception as e:
            error_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "type": "error"
            }
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )


# Health Monitoring Endpoints
@router.get("/health/report")
async def get_health_report(
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive health report for all devices."""
    try:
        health_monitor = get_device_health_monitor(device_manager)
        report = await health_monitor.generate_health_report()
        return report
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate health report: {str(e)}"
        )


# Utility Functions
async def _get_device_info(device_id: str) -> Optional[DeviceInfo]:
    """Get device info from registry (placeholder implementation)."""
    # This would typically query a device registry database
    # For now, return None to trigger device discovery
    return None


async def _auto_calibrate_device(device_id: str, device_type: DeviceType):
    """Perform automatic calibration with default reference values."""
    try:
        calibrator = get_device_calibrator(device_manager)
        
        # Use default reference values for auto-calibration
        if device_type == DeviceType.BLOOD_PRESSURE:
            # Use standard reference values
            await calibrator.calibrate_blood_pressure_monitor(
                device_id, 120.0, 80.0  # Standard BP reference
            )
        elif device_type == DeviceType.PULSE_OXIMETER:
            await calibrator.calibrate_pulse_oximeter(
                device_id, 98.0, 72  # Standard SpO2 and HR reference
            )
        
    except Exception as e:
        # Log error but don't fail the connection
        import logging
        logger = logging.getLogger("device_calibration")
        logger.error(f"Auto-calibration failed for device {device_id}: {e}")


# Include router in main API
def get_device_router() -> APIRouter:
    """Get the device integration router."""
    return router
