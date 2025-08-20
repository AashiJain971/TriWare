/**
 * Device Slice
 * Manages BLE medical device connections and data
 */

import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface DeviceReading {
  type: 'heartRate' | 'bloodPressure' | 'temperature' | 'oxygenSaturation' | 'glucose';
  value: any;
  unit: string;
  timestamp: Date;
  deviceId: string;
}

interface ConnectedDevice {
  id: string;
  name: string;
  type: 'blood-pressure' | 'pulse-oximeter' | 'thermometer' | 'glucometer' | 'ecg';
  isConnected: boolean;
  batteryLevel?: number;
  lastReading?: DeviceReading;
  calibrationStatus: 'calibrated' | 'needs-calibration' | 'calibrating';
  firmware?: string;
  serialNumber?: string;
}

interface AvailableDevice {
  id: string;
  name: string;
  type: string;
}

interface DeviceState {
  availableDevices: AvailableDevice[];
  connectedDevices: ConnectedDevice[];
  isScanning: boolean;
  isConnecting: boolean;
  currentReadings: DeviceReading[];
  error: string | null;
  calibrationDialogOpen: boolean;
  selectedDevice: ConnectedDevice | null;
}

const initialState: DeviceState = {
  availableDevices: [],
  connectedDevices: [],
  isScanning: false,
  isConnecting: false,
  currentReadings: [],
  error: null,
  calibrationDialogOpen: false,
  selectedDevice: null,
};

const deviceSlice = createSlice({
  name: 'devices',
  initialState,
  reducers: {
    startScanning: (state) => {
      state.isScanning = true;
      state.error = null;
    },
    stopScanning: (state) => {
      state.isScanning = false;
    },
    setAvailableDevices: (state, action: PayloadAction<AvailableDevice[]>) => {
      state.availableDevices = action.payload;
    },
    startConnecting: (state) => {
      state.isConnecting = true;
      state.error = null;
    },
    connectDevice: (state, action: PayloadAction<ConnectedDevice>) => {
      state.connectedDevices.push(action.payload);
      state.isConnecting = false;
    },
    disconnectDevice: (state, action: PayloadAction<string>) => {
      state.connectedDevices = state.connectedDevices.filter(d => d.id !== action.payload);
    },
    updateDevice: (state, action: PayloadAction<{ id: string; updates: Partial<ConnectedDevice> }>) => {
      const { id, updates } = action.payload;
      const index = state.connectedDevices.findIndex(d => d.id === id);
      if (index !== -1) {
        state.connectedDevices[index] = { ...state.connectedDevices[index], ...updates };
      }
    },
    addReading: (state, action: PayloadAction<DeviceReading>) => {
      state.currentReadings.push(action.payload);
      // Update device last reading
      const device = state.connectedDevices.find(d => d.id === action.payload.deviceId);
      if (device) {
        device.lastReading = action.payload;
      }
    },
    clearReadings: (state) => {
      state.currentReadings = [];
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
      state.isScanning = false;
      state.isConnecting = false;
    },
    openCalibrationDialog: (state, action: PayloadAction<ConnectedDevice>) => {
      state.calibrationDialogOpen = true;
      state.selectedDevice = action.payload;
    },
    closeCalibrationDialog: (state) => {
      state.calibrationDialogOpen = false;
      state.selectedDevice = null;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
});

export const {
  startScanning,
  stopScanning,
  setAvailableDevices,
  startConnecting,
  connectDevice,
  disconnectDevice,
  updateDevice,
  addReading,
  clearReadings,
  setError,
  openCalibrationDialog,
  closeCalibrationDialog,
  clearError,
} = deviceSlice.actions;

export default deviceSlice.reducer;
