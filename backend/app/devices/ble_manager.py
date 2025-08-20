"""
Bluetooth Low Energy (BLE) Device Manager for Medical Devices.

This module handles connectivity, data collection, and calibration
for various medical devices including blood pressure monitors,
pulse oximeters, thermometers, and scales.
"""

import asyncio
import json
import logging
import struct
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

# BLE and Device Communication
try:
    import bleak
    from bleak import BleakClient, BleakScanner, BleakGATTCharacteristic
    from bleak.exc import BleakError
    BLE_AVAILABLE = True
except ImportError:
    BLE_AVAILABLE = False
    logging.warning("Bleak BLE library not available. Device integration will be disabled.")

from app.core.config import settings
from app.models.vitals import VitalSigns
from app.services.vitals import VitalsService


class DeviceType(Enum):
    """Supported medical device types."""
    BLOOD_PRESSURE = "blood_pressure"
    PULSE_OXIMETER = "pulse_oximeter"
    THERMOMETER = "thermometer"
    WEIGHT_SCALE = "weight_scale"
    HEIGHT_METER = "height_meter"
    GLUCOSE_METER = "glucose_meter"


class DeviceStatus(Enum):
    """Device connection status."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    READING = "reading"
    ERROR = "error"
    CALIBRATING = "calibrating"


@dataclass
class DeviceInfo:
    """Device information and capabilities."""
    device_id: str
    name: str
    manufacturer: str
    model: str
    device_type: DeviceType
    mac_address: str
    rssi: int
    battery_level: Optional[int] = None
    firmware_version: Optional[str] = None
    last_seen: Optional[datetime] = None
    is_paired: bool = False
    calibration_status: str = "unknown"


@dataclass
class DeviceReading:
    """Medical device reading data."""
    device_id: str
    device_type: DeviceType
    timestamp: datetime
    values: Dict[str, Union[float, int, str]]
    unit: str
    quality_score: float  # 0-1, data quality indicator
    metadata: Dict[str, Any]


class DeviceDriver:
    """Base class for medical device drivers."""
    
    def __init__(self, device_info: DeviceInfo):
        self.device_info = device_info
        self.status = DeviceStatus.DISCONNECTED
        self.client: Optional[BleakClient] = None
        self.callbacks: List[Callable[[DeviceReading], None]] = []
        self.logger = logging.getLogger(f"device.{device_info.device_type.value}")
    
    async def connect(self) -> bool:
        """Connect to the device."""
        raise NotImplementedError
    
    async def disconnect(self) -> None:
        """Disconnect from the device."""
        raise NotImplementedError
    
    async def read_data(self) -> Optional[DeviceReading]:
        """Read data from the device."""
        raise NotImplementedError
    
    async def calibrate(self) -> bool:
        """Calibrate the device."""
        raise NotImplementedError
    
    def add_callback(self, callback: Callable[[DeviceReading], None]) -> None:
        """Add callback for data notifications."""
        self.callbacks.append(callback)
    
    def _notify_callbacks(self, reading: DeviceReading) -> None:
        """Notify all registered callbacks."""
        for callback in self.callbacks:
            try:
                callback(reading)
            except Exception as e:
                self.logger.error(f"Callback error: {e}")


class BloodPressureDriver(DeviceDriver):
    """Driver for Bluetooth blood pressure monitors."""
    
    # Standard BLE service UUIDs for blood pressure
    BP_SERVICE_UUID = "00001810-0000-1000-8000-00805f9b34fb"
    BP_MEASUREMENT_UUID = "00002a35-0000-1000-8000-00805f9b34fb"
    BP_FEATURE_UUID = "00002a49-0000-1000-8000-00805f9b34fb"
    
    def __init__(self, device_info: DeviceInfo):
        super().__init__(device_info)
        self.systolic = None
        self.diastolic = None
        self.mean_pressure = None
        self.heart_rate = None
    
    async def connect(self) -> bool:
        """Connect to blood pressure monitor."""
        if not BLE_AVAILABLE:
            self.logger.error("BLE not available")
            return False
        
        try:
            self.status = DeviceStatus.CONNECTING
            self.client = BleakClient(self.device_info.mac_address)
            
            await self.client.connect()
            
            # Subscribe to BP measurements
            await self.client.start_notify(
                self.BP_MEASUREMENT_UUID,
                self._handle_bp_measurement
            )
            
            self.status = DeviceStatus.CONNECTED
            self.logger.info(f"Connected to BP monitor: {self.device_info.name}")
            return True
            
        except Exception as e:
            self.status = DeviceStatus.ERROR
            self.logger.error(f"Failed to connect to BP monitor: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from blood pressure monitor."""
        if self.client and self.client.is_connected:
            try:
                await self.client.stop_notify(self.BP_MEASUREMENT_UUID)
                await self.client.disconnect()
                self.status = DeviceStatus.DISCONNECTED
                self.logger.info("Disconnected from BP monitor")
            except Exception as e:
                self.logger.error(f"Error disconnecting BP monitor: {e}")
    
    def _handle_bp_measurement(self, sender: BleakGATTCharacteristic, data: bytearray):
        """Handle blood pressure measurement notification."""
        try:
            # Parse BP measurement according to BLE spec
            flags = data[0]
            
            # Check if values are in mmHg or kPa (bit 0 of flags)
            unit_kpa = flags & 0x01
            unit = "kPa" if unit_kpa else "mmHg"
            
            # Parse systolic, diastolic, mean pressure (16-bit values)
            systolic = struct.unpack('<H', data[1:3])[0]
            diastolic = struct.unpack('<H', data[3:5])[0]
            mean_pressure = struct.unpack('<H', data[5:7])[0]
            
            # Convert from IEEE-11073 format if needed
            if unit_kpa:
                systolic = systolic / 1000.0
                diastolic = diastolic / 1000.0
                mean_pressure = mean_pressure / 1000.0
            
            # Check for timestamp (bit 1 of flags)
            timestamp_present = flags & 0x02
            pulse_rate_present = flags & 0x04
            
            offset = 7
            timestamp = datetime.utcnow()
            pulse_rate = None
            
            if timestamp_present:
                # Parse IEEE-11073 date/time (7 bytes)
                offset += 7
            
            if pulse_rate_present and len(data) > offset:
                pulse_rate = struct.unpack('<H', data[offset:offset+2])[0]
            
            # Create reading
            reading = DeviceReading(
                device_id=self.device_info.device_id,
                device_type=DeviceType.BLOOD_PRESSURE,
                timestamp=timestamp,
                values={
                    "systolic": systolic,
                    "diastolic": diastolic,
                    "mean_pressure": mean_pressure,
                    "pulse_rate": pulse_rate
                },
                unit=unit,
                quality_score=self._calculate_quality_score(systolic, diastolic),
                metadata={
                    "flags": flags,
                    "raw_data": data.hex()
                }
            )
            
            self.logger.info(f"BP reading: {systolic}/{diastolic} {unit}, HR: {pulse_rate}")
            self._notify_callbacks(reading)
            
        except Exception as e:
            self.logger.error(f"Error parsing BP measurement: {e}")
    
    def _calculate_quality_score(self, systolic: float, diastolic: float) -> float:
        """Calculate data quality score based on physiological ranges."""
        # Basic validation
        if not (50 <= systolic <= 250) or not (30 <= diastolic <= 150):
            return 0.3  # Low quality - outside normal ranges
        
        if systolic <= diastolic:
            return 0.4  # Low quality - impossible reading
        
        # Check for reasonable pulse pressure
        pulse_pressure = systolic - diastolic
        if pulse_pressure < 20 or pulse_pressure > 100:
            return 0.6  # Medium quality - unusual pulse pressure
        
        return 0.9  # High quality
    
    async def read_data(self) -> Optional[DeviceReading]:
        """Trigger a manual blood pressure reading."""
        if self.status != DeviceStatus.CONNECTED:
            return None
        
        try:
            self.status = DeviceStatus.READING
            # Most BP monitors automatically start measurement when cuff is inflated
            # Wait for measurement notification
            await asyncio.sleep(30)  # Typical BP measurement time
            self.status = DeviceStatus.CONNECTED
            return None  # Data comes via notification
            
        except Exception as e:
            self.logger.error(f"Error reading BP data: {e}")
            self.status = DeviceStatus.ERROR
            return None
    
    async def calibrate(self) -> bool:
        """Calibrate blood pressure monitor."""
        # Most BP monitors are factory calibrated
        # This could trigger a self-test or calibration check
        try:
            self.logger.info("BP monitor calibration check")
            # Implementation depends on specific device capabilities
            return True
        except Exception as e:
            self.logger.error(f"BP calibration failed: {e}")
            return False


class PulseOximeterDriver(DeviceDriver):
    """Driver for Bluetooth pulse oximeters."""
    
    # Standard BLE service UUIDs for pulse oximetry
    PLX_SERVICE_UUID = "00001822-0000-1000-8000-00805f9b34fb"
    PLX_SPOT_CHECK_UUID = "00002a5e-0000-1000-8000-00805f9b34fb"
    PLX_CONTINUOUS_UUID = "00002a5f-0000-1000-8000-00805f9b34fb"
    
    def __init__(self, device_info: DeviceInfo):
        super().__init__(device_info)
        self.spo2 = None
        self.pulse_rate = None
    
    async def connect(self) -> bool:
        """Connect to pulse oximeter."""
        if not BLE_AVAILABLE:
            return False
        
        try:
            self.status = DeviceStatus.CONNECTING
            self.client = BleakClient(self.device_info.mac_address)
            await self.client.connect()
            
            # Subscribe to continuous measurements
            await self.client.start_notify(
                self.PLX_CONTINUOUS_UUID,
                self._handle_plx_measurement
            )
            
            self.status = DeviceStatus.CONNECTED
            self.logger.info(f"Connected to pulse oximeter: {self.device_info.name}")
            return True
            
        except Exception as e:
            self.status = DeviceStatus.ERROR
            self.logger.error(f"Failed to connect to pulse oximeter: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from pulse oximeter."""
        if self.client and self.client.is_connected:
            try:
                await self.client.stop_notify(self.PLX_CONTINUOUS_UUID)
                await self.client.disconnect()
                self.status = DeviceStatus.DISCONNECTED
            except Exception as e:
                self.logger.error(f"Error disconnecting pulse oximeter: {e}")
    
    def _handle_plx_measurement(self, sender: BleakGATTCharacteristic, data: bytearray):
        """Handle pulse oximetry measurement notification."""
        try:
            flags = data[0]
            
            # Parse SpO2 and pulse rate (16-bit values)
            spo2 = struct.unpack('<H', data[1:3])[0] / 100.0  # Convert to percentage
            pulse_rate = struct.unpack('<H', data[3:5])[0]
            
            reading = DeviceReading(
                device_id=self.device_info.device_id,
                device_type=DeviceType.PULSE_OXIMETER,
                timestamp=datetime.utcnow(),
                values={
                    "spo2": spo2,
                    "pulse_rate": pulse_rate
                },
                unit="percent/%",
                quality_score=self._calculate_plx_quality(spo2, pulse_rate),
                metadata={
                    "flags": flags,
                    "signal_quality": self._get_signal_quality(data)
                }
            )
            
            self.logger.info(f"SpO2: {spo2}%, HR: {pulse_rate}")
            self._notify_callbacks(reading)
            
        except Exception as e:
            self.logger.error(f"Error parsing PLX measurement: {e}")
    
    def _calculate_plx_quality(self, spo2: float, pulse_rate: int) -> float:
        """Calculate pulse oximetry data quality."""
        if not (70 <= spo2 <= 100) or not (30 <= pulse_rate <= 200):
            return 0.3
        
        if spo2 < 85:  # Critically low SpO2
            return 0.8  # Still good quality, but concerning value
        
        return 0.9
    
    def _get_signal_quality(self, data: bytearray) -> str:
        """Extract signal quality from device data."""
        # Implementation depends on specific device protocol
        # Many devices include signal quality indicators
        return "good"  # Placeholder


class ThermometerDriver(DeviceDriver):
    """Driver for Bluetooth thermometers."""
    
    # Standard BLE service UUIDs for health thermometer
    HTS_SERVICE_UUID = "00001809-0000-1000-8000-00805f9b34fb"
    TEMPERATURE_MEASUREMENT_UUID = "00002a1c-0000-1000-8000-00805f9b34fb"
    
    async def connect(self) -> bool:
        """Connect to thermometer."""
        if not BLE_AVAILABLE:
            return False
        
        try:
            self.status = DeviceStatus.CONNECTING
            self.client = BleakClient(self.device_info.mac_address)
            await self.client.connect()
            
            await self.client.start_notify(
                self.TEMPERATURE_MEASUREMENT_UUID,
                self._handle_temperature_measurement
            )
            
            self.status = DeviceStatus.CONNECTED
            return True
            
        except Exception as e:
            self.status = DeviceStatus.ERROR
            self.logger.error(f"Failed to connect to thermometer: {e}")
            return False
    
    def _handle_temperature_measurement(self, sender: BleakGATTCharacteristic, data: bytearray):
        """Handle temperature measurement notification."""
        try:
            flags = data[0]
            
            # Check temperature unit (bit 0: 0=Celsius, 1=Fahrenheit)
            fahrenheit = flags & 0x01
            unit = "°F" if fahrenheit else "°C"
            
            # Parse temperature (IEEE-11073 32-bit float)
            temp_data = struct.unpack('<f', data[1:5])[0]
            
            # Convert to Celsius for internal storage
            if fahrenheit:
                temperature = (temp_data - 32) * 5/9
                unit_internal = "°C"
            else:
                temperature = temp_data
                unit_internal = "°C"
            
            reading = DeviceReading(
                device_id=self.device_info.device_id,
                device_type=DeviceType.THERMOMETER,
                timestamp=datetime.utcnow(),
                values={"temperature": temperature},
                unit=unit_internal,
                quality_score=self._calculate_temp_quality(temperature),
                metadata={
                    "original_unit": unit,
                    "original_value": temp_data
                }
            )
            
            self.logger.info(f"Temperature: {temperature:.1f}°C")
            self._notify_callbacks(reading)
            
        except Exception as e:
            self.logger.error(f"Error parsing temperature: {e}")
    
    def _calculate_temp_quality(self, temperature: float) -> float:
        """Calculate temperature reading quality."""
        if not (32 <= temperature <= 45):  # Realistic human temperature range
            return 0.2
        
        return 0.9


class DeviceManager:
    """Central manager for all medical devices."""
    
    def __init__(self):
        self.devices: Dict[str, DeviceDriver] = {}
        self.scanner: Optional[BleakScanner] = None
        self.vitals_service = VitalsService()
        self.logger = logging.getLogger("device_manager")
        
        # Device discovery patterns
        self.device_patterns = {
            "omron": DeviceType.BLOOD_PRESSURE,
            "nonin": DeviceType.PULSE_OXIMETER,
            "braun": DeviceType.THERMOMETER,
            "withings": DeviceType.WEIGHT_SCALE,
        }
    
    async def start_discovery(self, duration: int = 10) -> List[DeviceInfo]:
        """Discover available medical devices."""
        if not BLE_AVAILABLE:
            self.logger.error("BLE not available for device discovery")
            return []
        
        try:
            discovered_devices = []
            
            self.logger.info(f"Starting device discovery for {duration}s")
            
            # Scan for BLE devices
            devices = await BleakScanner.discover(timeout=duration)
            
            for device in devices:
                device_info = await self._identify_medical_device(device)
                if device_info:
                    discovered_devices.append(device_info)
            
            self.logger.info(f"Discovered {len(discovered_devices)} medical devices")
            return discovered_devices
            
        except Exception as e:
            self.logger.error(f"Device discovery failed: {e}")
            return []
    
    async def _identify_medical_device(self, ble_device) -> Optional[DeviceInfo]:
        """Identify if BLE device is a medical device."""
        try:
            device_name = ble_device.name or ""
            device_name_lower = device_name.lower()
            
            # Check for known medical device patterns
            device_type = None
            manufacturer = "Unknown"
            
            for pattern, dev_type in self.device_patterns.items():
                if pattern in device_name_lower:
                    device_type = dev_type
                    manufacturer = pattern.title()
                    break
            
            # Check service UUIDs
            if not device_type and ble_device.metadata.get("uuids"):
                uuids = ble_device.metadata["uuids"]
                
                if BloodPressureDriver.BP_SERVICE_UUID in uuids:
                    device_type = DeviceType.BLOOD_PRESSURE
                elif PulseOximeterDriver.PLX_SERVICE_UUID in uuids:
                    device_type = DeviceType.PULSE_OXIMETER
                elif ThermometerDriver.HTS_SERVICE_UUID in uuids:
                    device_type = DeviceType.THERMOMETER
            
            if device_type:
                return DeviceInfo(
                    device_id=str(uuid.uuid4()),
                    name=device_name,
                    manufacturer=manufacturer,
                    model=device_name,
                    device_type=device_type,
                    mac_address=ble_device.address,
                    rssi=ble_device.rssi or 0,
                    last_seen=datetime.utcnow()
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error identifying device: {e}")
            return None
    
    async def connect_device(self, device_info: DeviceInfo) -> bool:
        """Connect to a medical device."""
        try:
            # Create appropriate driver
            driver = self._create_driver(device_info)
            
            if await driver.connect():
                self.devices[device_info.device_id] = driver
                
                # Set up data callback to store readings
                driver.add_callback(self._handle_device_reading)
                
                self.logger.info(f"Connected to device: {device_info.name}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to connect device: {e}")
            return False
    
    def _create_driver(self, device_info: DeviceInfo) -> DeviceDriver:
        """Create appropriate driver for device type."""
        if device_info.device_type == DeviceType.BLOOD_PRESSURE:
            return BloodPressureDriver(device_info)
        elif device_info.device_type == DeviceType.PULSE_OXIMETER:
            return PulseOximeterDriver(device_info)
        elif device_info.device_type == DeviceType.THERMOMETER:
            return ThermometerDriver(device_info)
        else:
            return DeviceDriver(device_info)  # Base driver
    
    async def _handle_device_reading(self, reading: DeviceReading):
        """Handle incoming device reading."""
        try:
            self.logger.info(f"Device reading: {reading.device_type.value} - {reading.values}")
            
            # Store reading in database
            await self.vitals_service.store_device_reading(reading)
            
            # Could trigger real-time notifications or alerts here
            
        except Exception as e:
            self.logger.error(f"Error handling device reading: {e}")
    
    async def disconnect_device(self, device_id: str) -> bool:
        """Disconnect a medical device."""
        if device_id in self.devices:
            try:
                await self.devices[device_id].disconnect()
                del self.devices[device_id]
                return True
            except Exception as e:
                self.logger.error(f"Error disconnecting device: {e}")
                return False
        return False
    
    async def get_device_status(self, device_id: str) -> Optional[DeviceStatus]:
        """Get current status of a device."""
        if device_id in self.devices:
            return self.devices[device_id].status
        return None
    
    async def calibrate_device(self, device_id: str) -> bool:
        """Calibrate a medical device."""
        if device_id in self.devices:
            try:
                return await self.devices[device_id].calibrate()
            except Exception as e:
                self.logger.error(f"Device calibration failed: {e}")
                return False
        return False
    
    async def shutdown(self):
        """Disconnect all devices and cleanup."""
        self.logger.info("Shutting down device manager")
        
        for device_id in list(self.devices.keys()):
            await self.disconnect_device(device_id)
        
        self.devices.clear()


# Global device manager instance
device_manager = DeviceManager()
