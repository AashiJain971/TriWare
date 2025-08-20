// Device Integration Components for Smart Triage Kiosk
// This file provides React components for BLE medical device management

import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  Grid,
  Chip,
  LinearProgress,
  Alert,
  AlertTitle,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  IconButton,
  CircularProgress,
  Tooltip,
  Badge,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Divider
} from '@mui/material';
import {
  Bluetooth as BluetoothIcon,
  BluetoothConnected as BluetoothConnectedIcon,
  BluetoothDisabled as BluetoothDisabledIcon,
  DeviceHub as DeviceHubIcon,
  MonitorHeart as MonitorIcon,
  Thermostat as ThermometerIcon,
  Speed as PressureIcon,
  Scale as ScaleIcon,
  Height as HeightIcon,
  Refresh as RefreshIcon,
  Settings as SettingsIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  CheckCircle as CheckIcon,
  Battery90 as BatteryIcon,
  SignalWifi4Bar as SignalIcon,
  Timeline as TrendIcon,
  Calibrate as CalibrateIcon,
  PlayArrow as StartIcon,
  Stop as StopIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';
import { format } from 'date-fns';

// Type definitions
interface DeviceInfo {
  device_id: string;
  name: string;
  manufacturer: string;
  model: string;
  device_type: 'blood_pressure' | 'pulse_oximeter' | 'thermometer' | 'weight_scale' | 'height_meter';
  mac_address: string;
  rssi: number;
  battery_level?: number;
  last_seen?: string;
  is_paired: boolean;
}

interface DeviceStatus {
  device_id: string;
  device_name: string;
  device_type: string;
  connection_status: 'connected' | 'connecting' | 'disconnected' | 'error';
  health_status: 'healthy' | 'warning' | 'critical' | 'offline';
  calibration_status: 'calibrated' | 'needs_calibration' | 'calibrating' | 'out_of_spec';
  battery_level?: number;
  last_reading?: string;
  uptime?: string;
}

interface DeviceReading {
  device_id: string;
  device_type: string;
  timestamp: string;
  values: Record<string, number>;
  unit: string;
  quality_score: number;
  metadata?: Record<string, any>;
}

interface CalibrationData {
  device_id: string;
  device_type: string;
  reference_values: Record<string, number>;
  technician_id?: string;
  notes?: string;
}

// Device type icons mapping
const getDeviceIcon = (deviceType: string) => {
  switch (deviceType) {
    case 'blood_pressure':
      return <PressureIcon />;
    case 'pulse_oximeter':
      return <MonitorIcon />;
    case 'thermometer':
      return <ThermometerIcon />;
    case 'weight_scale':
      return <ScaleIcon />;
    case 'height_meter':
      return <HeightIcon />;
    default:
      return <DeviceHubIcon />;
  }
};

// Status colors
const getStatusColor = (status: string, theme: any) => {
  switch (status) {
    case 'connected':
    case 'healthy':
    case 'calibrated':
      return theme.palette.success.main;
    case 'connecting':
    case 'calibrating':
    case 'warning':
      return theme.palette.warning.main;
    case 'disconnected':
    case 'needs_calibration':
      return theme.palette.info.main;
    case 'error':
    case 'critical':
    case 'out_of_spec':
      return theme.palette.error.main;
    default:
      return theme.palette.grey[500];
  }
};

// Device Discovery Component
export const DeviceDiscovery: React.FC = () => {
  const [scanning, setScanning] = useState(false);
  const [discoveredDevices, setDiscoveredDevices] = useState<DeviceInfo[]>([]);
  const [scanDuration, setScanDuration] = useState(10);
  const [error, setError] = useState<string | null>(null);
  const theme = useTheme();

  const startDeviceDiscovery = async () => {
    setScanning(true);
    setError(null);
    setDiscoveredDevices([]);

    try {
      const response = await fetch('/api/v1/devices/discover', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ duration: scanDuration })
      });

      if (!response.ok) {
        throw new Error('Failed to discover devices');
      }

      const data = await response.json();
      setDiscoveredDevices(data.devices || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Device discovery failed');
    } finally {
      setScanning(false);
    }
  };

  const connectDevice = async (deviceId: string, autoCalibrate: boolean = false) => {
    try {
      const response = await fetch('/api/v1/devices/connect', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          device_id: deviceId,
          auto_calibrate: autoCalibrate
        })
      });

      if (!response.ok) {
        throw new Error('Failed to connect device');
      }

      const result = await response.json();
      // Refresh device list or show success message
      console.log('Device connected:', result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Device connection failed');
    }
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          <BluetoothIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          Device Discovery
        </Typography>
        
        <Box sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
          <TextField
            label="Scan Duration (seconds)"
            type="number"
            value={scanDuration}
            onChange={(e) => setScanDuration(Math.max(5, Math.min(60, Number(e.target.value))))}
            size="small"
            sx={{ width: 200 }}
          />
          
          <Button
            variant="contained"
            onClick={startDeviceDiscovery}
            disabled={scanning}
            startIcon={scanning ? <CircularProgress size={20} /> : <RefreshIcon />}
          >
            {scanning ? 'Scanning...' : 'Start Scan'}
          </Button>
        </Box>

        {scanning && (
          <Box sx={{ mb: 2 }}>
            <LinearProgress />
            <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
              Scanning for medical devices...
            </Typography>
          </Box>
        )}

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            <AlertTitle>Discovery Failed</AlertTitle>
            {error}
          </Alert>
        )}

        {discoveredDevices.length > 0 && (
          <List>
            {discoveredDevices.map((device) => (
              <ListItem key={device.device_id} divider>
                <ListItemIcon>
                  {getDeviceIcon(device.device_type)}
                </ListItemIcon>
                
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {device.name}
                      <Chip
                        label={device.device_type.replace('_', ' ')}
                        size="small"
                        color="primary"
                      />
                      {device.battery_level && (
                        <Chip
                          label={`${device.battery_level}%`}
                          size="small"
                          icon={<BatteryIcon />}
                          color={device.battery_level > 20 ? 'success' : 'warning'}
                        />
                      )}
                    </Box>
                  }
                  secondary={
                    <Typography variant="body2" color="textSecondary">
                      {device.manufacturer} {device.model} • Signal: {device.rssi}dBm
                      {device.last_seen && ` • Last seen: ${format(new Date(device.last_seen), 'HH:mm:ss')}`}
                    </Typography>
                  }
                />
                
                <ListItemSecondaryAction>
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={() => connectDevice(device.device_id, false)}
                    >
                      Connect
                    </Button>
                    <Button
                      variant="contained"
                      size="small"
                      onClick={() => connectDevice(device.device_id, true)}
                    >
                      Connect & Calibrate
                    </Button>
                  </Box>
                </ListItemSecondaryAction>
              </ListItem>
            ))}
          </List>
        )}

        {!scanning && discoveredDevices.length === 0 && (
          <Alert severity="info">
            No medical devices found. Make sure devices are powered on and in pairing mode.
          </Alert>
        )}
      </CardContent>
    </Card>
  );
};

// Connected Devices Status Component
export const ConnectedDevices: React.FC = () => {
  const [devices, setDevices] = useState<DeviceStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDevice, setSelectedDevice] = useState<DeviceStatus | null>(null);
  const [calibrationDialog, setCalibrationDialog] = useState(false);
  const theme = useTheme();

  const fetchConnectedDevices = useCallback(async () => {
    try {
      const response = await fetch('/api/v1/devices/status', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch device status');
      }

      const data = await response.json();
      setDevices(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load devices');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchConnectedDevices();
    // Set up periodic refresh
    const interval = setInterval(fetchConnectedDevices, 30000); // Every 30 seconds
    return () => clearInterval(interval);
  }, [fetchConnectedDevices]);

  const disconnectDevice = async (deviceId: string) => {
    try {
      const response = await fetch(`/api/v1/devices/disconnect/${deviceId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to disconnect device');
      }

      // Refresh device list
      fetchConnectedDevices();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Disconnect failed');
    }
  };

  const triggerReading = async (deviceId: string) => {
    try {
      const response = await fetch(`/api/v1/devices/read/${deviceId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to trigger reading');
      }

      const result = await response.json();
      console.log('Reading triggered:', result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Reading failed');
    }
  };

  if (loading) {
    return (
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
            <CircularProgress />
          </Box>
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            <BluetoothConnectedIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
            Connected Devices ({devices.length})
          </Typography>

          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          {devices.length === 0 ? (
            <Alert severity="info">
              No devices connected. Use Device Discovery to find and connect medical devices.
            </Alert>
          ) : (
            <TableContainer component={Paper} variant="outlined">
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Device</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Connection</TableCell>
                    <TableCell>Health</TableCell>
                    <TableCell>Calibration</TableCell>
                    <TableCell>Battery</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {devices.map((device) => (
                    <TableRow key={device.device_id} hover>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          {getDeviceIcon(device.device_type)}
                          <Typography variant="body2" fontWeight="medium">
                            {device.device_name}
                          </Typography>
                        </Box>
                      </TableCell>
                      
                      <TableCell>
                        <Chip
                          label={device.device_type.replace('_', ' ')}
                          size="small"
                          variant="outlined"
                        />
                      </TableCell>
                      
                      <TableCell>
                        <Chip
                          label={device.connection_status}
                          size="small"
                          sx={{
                            bgcolor: getStatusColor(device.connection_status, theme),
                            color: 'white'
                          }}
                        />
                      </TableCell>
                      
                      <TableCell>
                        <Chip
                          label={device.health_status}
                          size="small"
                          sx={{
                            bgcolor: getStatusColor(device.health_status, theme),
                            color: 'white'
                          }}
                        />
                      </TableCell>
                      
                      <TableCell>
                        <Chip
                          label={device.calibration_status.replace('_', ' ')}
                          size="small"
                          sx={{
                            bgcolor: getStatusColor(device.calibration_status, theme),
                            color: 'white'
                          }}
                        />
                      </TableCell>
                      
                      <TableCell>
                        {device.battery_level ? (
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <BatteryIcon
                              color={device.battery_level > 20 ? 'success' : 'warning'}
                            />
                            <Typography variant="body2">
                              {device.battery_level}%
                            </Typography>
                          </Box>
                        ) : (
                          <Typography variant="body2" color="textSecondary">
                            N/A
                          </Typography>
                        )}
                      </TableCell>
                      
                      <TableCell>
                        <Box sx={{ display: 'flex', gap: 0.5 }}>
                          <Tooltip title="Take Reading">
                            <IconButton
                              size="small"
                              onClick={() => triggerReading(device.device_id)}
                              disabled={device.connection_status !== 'connected'}
                            >
                              <StartIcon />
                            </IconButton>
                          </Tooltip>
                          
                          <Tooltip title="Calibrate">
                            <IconButton
                              size="small"
                              onClick={() => {
                                setSelectedDevice(device);
                                setCalibrationDialog(true);
                              }}
                              disabled={device.connection_status !== 'connected'}
                            >
                              <CalibrateIcon />
                            </IconButton>
                          </Tooltip>
                          
                          <Tooltip title="Device Info">
                            <IconButton
                              size="small"
                              onClick={() => setSelectedDevice(device)}
                            >
                              <InfoIcon />
                            </IconButton>
                          </Tooltip>
                          
                          <Tooltip title="Disconnect">
                            <IconButton
                              size="small"
                              color="error"
                              onClick={() => disconnectDevice(device.device_id)}
                            >
                              <StopIcon />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>

      {/* Device Calibration Dialog */}
      <DeviceCalibrationDialog
        device={selectedDevice}
        open={calibrationDialog}
        onClose={() => {
          setCalibrationDialog(false);
          setSelectedDevice(null);
        }}
        onCalibrated={fetchConnectedDevices}
      />
    </>
  );
};

// Device Calibration Dialog Component
interface CalibrationDialogProps {
  device: DeviceStatus | null;
  open: boolean;
  onClose: () => void;
  onCalibrated: () => void;
}

export const DeviceCalibrationDialog: React.FC<CalibrationDialogProps> = ({
  device,
  open,
  onClose,
  onCalibrated
}) => {
  const [calibrating, setCalibrating] = useState(false);
  const [referenceValues, setReferenceValues] = useState<Record<string, number>>({});
  const [notes, setNotes] = useState('');
  const [error, setError] = useState<string | null>(null);

  // Reset form when device changes
  useEffect(() => {
    if (device) {
      setReferenceValues({});
      setNotes('');
      setError(null);
    }
  }, [device]);

  const getReferenceFields = (deviceType: string) => {
    switch (deviceType) {
      case 'blood_pressure':
        return [
          { key: 'systolic', label: 'Systolic BP (mmHg)', min: 70, max: 200 },
          { key: 'diastolic', label: 'Diastolic BP (mmHg)', min: 40, max: 120 }
        ];
      case 'pulse_oximeter':
        return [
          { key: 'spo2', label: 'SpO2 (%)', min: 85, max: 100 },
          { key: 'pulse_rate', label: 'Pulse Rate (bpm)', min: 30, max: 200 }
        ];
      case 'thermometer':
        return [
          { key: 'temperature', label: 'Temperature (°C)', min: 35, max: 42 }
        ];
      case 'weight_scale':
        return [
          { key: 'weight', label: 'Weight (kg)', min: 0.5, max: 300 }
        ];
      default:
        return [];
    }
  };

  const handleCalibrate = async () => {
    if (!device) return;

    setCalibrating(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/devices/calibrate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          device_id: device.device_id,
          device_type: device.device_type,
          reference_values: referenceValues,
          notes: notes || undefined
        })
      });

      if (!response.ok) {
        throw new Error('Calibration failed');
      }

      const result = await response.json();
      console.log('Calibration result:', result);
      
      onCalibrated();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Calibration failed');
    } finally {
      setCalibrating(false);
    }
  };

  if (!device) return null;

  const referenceFields = getReferenceFields(device.device_type);
  const isFormValid = referenceFields.every(field => 
    referenceValues[field.key] !== undefined && 
    referenceValues[field.key] >= field.min && 
    referenceValues[field.key] <= field.max
  );

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <CalibrateIcon />
          Calibrate {device.device_name}
        </Box>
      </DialogTitle>
      
      <DialogContent>
        <Typography variant="body2" color="textSecondary" gutterBottom>
          Enter reference values for device calibration. These should be known accurate values
          from a certified reference device or standard.
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Grid container spacing={2} sx={{ mt: 1 }}>
          {referenceFields.map((field) => (
            <Grid item xs={12} sm={6} key={field.key}>
              <TextField
                fullWidth
                label={field.label}
                type="number"
                value={referenceValues[field.key] || ''}
                onChange={(e) => setReferenceValues(prev => ({
                  ...prev,
                  [field.key]: Number(e.target.value)
                }))}
                inputProps={{
                  min: field.min,
                  max: field.max,
                  step: field.key === 'temperature' ? 0.1 : 1
                }}
                helperText={`Range: ${field.min} - ${field.max}`}
              />
            </Grid>
          ))}
          
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Notes (optional)"
              multiline
              rows={2}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Additional calibration notes..."
            />
          </Grid>
        </Grid>
      </DialogContent>
      
      <DialogActions>
        <Button onClick={onClose} disabled={calibrating}>
          Cancel
        </Button>
        <Button
          onClick={handleCalibrate}
          disabled={calibrating || !isFormValid}
          variant="contained"
          startIcon={calibrating ? <CircularProgress size={20} /> : <CalibrateIcon />}
        >
          {calibrating ? 'Calibrating...' : 'Start Calibration'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

// Main Device Integration Dashboard
export const DeviceIntegrationDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Medical Device Integration
      </Typography>
      
      <Typography variant="body1" color="textSecondary" paragraph>
        Manage Bluetooth Low Energy (BLE) medical devices including blood pressure monitors,
        pulse oximeters, thermometers, and scales.
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <DeviceDiscovery />
        </Grid>
        
        <Grid item xs={12}>
          <ConnectedDevices />
        </Grid>
      </Grid>
    </Box>
  );
};

export default DeviceIntegrationDashboard;
