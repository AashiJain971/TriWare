/**
 * Patient Slice
 * Manages patient data and registration state
 */

import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface VitalSigns {
  heartRate?: number;
  bloodPressure?: {
    systolic: number;
    diastolic: number;
  };
  temperature?: number;
  oxygenSaturation?: number;
  respiratoryRate?: number;
  glucose?: number;
  timestamp: Date;
}

interface Patient {
  id: string;
  firstName: string;
  lastName: string;
  dateOfBirth: string;
  gender: 'male' | 'female' | 'other';
  phone?: string;
  email?: string;
  emergencyContact: {
    name: string;
    phone: string;
    relationship: string;
  };
  medicalHistory: {
    conditions: string[];
    medications: string[];
    allergies: string[];
  };
  vitals: VitalSigns[];
  triageScore?: number;
  priority?: 'critical' | 'urgent' | 'semi-urgent' | 'non-urgent';
  status: 'registered' | 'triaged' | 'waiting' | 'in-progress' | 'completed';
  createdAt: string;
  updatedAt: string;
}

interface PatientState {
  patients: Patient[];
  currentPatient: Patient | null;
  isLoading: boolean;
  error: string | null;
  registrationStep: number;
}

const initialState: PatientState = {
  patients: [],
  currentPatient: null,
  isLoading: false,
  error: null,
  registrationStep: 0,
};

const patientSlice = createSlice({
  name: 'patients',
  initialState,
  reducers: {
    setCurrentPatient: (state, action: PayloadAction<Patient | null>) => {
      state.currentPatient = action.payload;
    },
    addPatient: (state, action: PayloadAction<Patient>) => {
      state.patients.push(action.payload);
    },
    updatePatient: (state, action: PayloadAction<{ id: string; updates: Partial<Patient> }>) => {
      const { id, updates } = action.payload;
      const index = state.patients.findIndex(p => p.id === id);
      if (index !== -1) {
        state.patients[index] = { ...state.patients[index], ...updates };
      }
      if (state.currentPatient?.id === id) {
        state.currentPatient = { ...state.currentPatient, ...updates };
      }
    },
    removePatient: (state, action: PayloadAction<string>) => {
      state.patients = state.patients.filter(p => p.id !== action.payload);
      if (state.currentPatient?.id === action.payload) {
        state.currentPatient = null;
      }
    },
    setRegistrationStep: (state, action: PayloadAction<number>) => {
      state.registrationStep = action.payload;
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
});

export const {
  setCurrentPatient,
  addPatient,
  updatePatient,
  removePatient,
  setRegistrationStep,
  setLoading,
  setError,
  clearError,
} = patientSlice.actions;

export default patientSlice.reducer;
