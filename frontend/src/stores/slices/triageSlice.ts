/**
 * Triage Slice
 * Manages triage assessment state and scoring
 */

import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface Symptom {
  id: string;
  name: string;
  severity: number; // 1-10 scale
  duration: string;
  category: 'pain' | 'respiratory' | 'cardiovascular' | 'neurological' | 'gastrointestinal' | 'other';
}

interface TriageAssessment {
  patientId: string;
  symptoms: Symptom[];
  vitalSigns: {
    heartRate?: number;
    bloodPressure?: { systolic: number; diastolic: number };
    temperature?: number;
    oxygenSaturation?: number;
    respiratoryRate?: number;
  };
  painScore: number; // 0-10 scale
  consciousnessLevel: 'alert' | 'verbal' | 'pain' | 'unresponsive';
  mobility: 'independent' | 'assisted' | 'wheelchair' | 'stretcher';
  riskFactors: {
    age: number;
    pregnancy: boolean;
    chronicConditions: string[];
    currentMedications: string[];
    allergies: string[];
  };
  triageScore: number;
  priority: 'critical' | 'urgent' | 'semi-urgent' | 'non-urgent';
  recommendation: string;
  estimatedWaitTime: number; // minutes
  assessedBy?: string;
  timestamp: string;
}

interface TriageState {
  currentAssessment: TriageAssessment | null;
  assessments: TriageAssessment[];
  isAssessing: boolean;
  currentStep: number;
  totalSteps: number;
  isLoading: boolean;
  error: string | null;
}

const initialState: TriageState = {
  currentAssessment: null,
  assessments: [],
  isAssessing: false,
  currentStep: 0,
  totalSteps: 6,
  isLoading: false,
  error: null,
};

const triageSlice = createSlice({
  name: 'triage',
  initialState,
  reducers: {
    startAssessment: (state, action: PayloadAction<string>) => {
      state.currentAssessment = {
        patientId: action.payload,
        symptoms: [],
        vitalSigns: {},
        painScore: 0,
        consciousnessLevel: 'alert',
        mobility: 'independent',
        riskFactors: {
          age: 0,
          pregnancy: false,
          chronicConditions: [],
          currentMedications: [],
          allergies: [],
        },
        triageScore: 0,
        priority: 'non-urgent',
        recommendation: '',
        estimatedWaitTime: 0,
        timestamp: new Date().toISOString(),
      };
      state.isAssessing = true;
      state.currentStep = 0;
    },
    updateAssessment: (state, action: PayloadAction<Partial<TriageAssessment>>) => {
      if (state.currentAssessment) {
        state.currentAssessment = { ...state.currentAssessment, ...action.payload };
      }
    },
    addSymptom: (state, action: PayloadAction<Symptom>) => {
      if (state.currentAssessment) {
        state.currentAssessment.symptoms.push(action.payload);
      }
    },
    removeSymptom: (state, action: PayloadAction<string>) => {
      if (state.currentAssessment) {
        state.currentAssessment.symptoms = state.currentAssessment.symptoms.filter(
          s => s.id !== action.payload
        );
      }
    },
    updateVitalSigns: (state, action: PayloadAction<TriageAssessment['vitalSigns']>) => {
      if (state.currentAssessment) {
        state.currentAssessment.vitalSigns = { ...state.currentAssessment.vitalSigns, ...action.payload };
      }
    },
    calculateTriageScore: (state) => {
      if (state.currentAssessment) {
        // Simple triage scoring algorithm (this would be more complex in reality)
        let score = 0;
        
        // Vital signs scoring
        const vitals = state.currentAssessment.vitalSigns;
        if (vitals.heartRate) {
          if (vitals.heartRate > 100 || vitals.heartRate < 60) score += 2;
        }
        if (vitals.bloodPressure) {
          if (vitals.bloodPressure.systolic > 140 || vitals.bloodPressure.systolic < 90) score += 2;
        }
        if (vitals.temperature && vitals.temperature > 38) score += 3;
        if (vitals.oxygenSaturation && vitals.oxygenSaturation < 95) score += 4;
        
        // Symptoms scoring
        const maxSymptomSeverity = Math.max(...state.currentAssessment.symptoms.map(s => s.severity), 0);
        score += maxSymptomSeverity;
        
        // Pain score
        score += state.currentAssessment.painScore;
        
        // Consciousness level
        if (state.currentAssessment.consciousnessLevel !== 'alert') score += 5;
        
        // Age factor
        if (state.currentAssessment.riskFactors.age > 65) score += 2;
        if (state.currentAssessment.riskFactors.age < 2) score += 3;
        
        state.currentAssessment.triageScore = score;
        
        // Determine priority based on score
        if (score >= 15) {
          state.currentAssessment.priority = 'critical';
          state.currentAssessment.estimatedWaitTime = 0;
        } else if (score >= 10) {
          state.currentAssessment.priority = 'urgent';
          state.currentAssessment.estimatedWaitTime = 15;
        } else if (score >= 5) {
          state.currentAssessment.priority = 'semi-urgent';
          state.currentAssessment.estimatedWaitTime = 60;
        } else {
          state.currentAssessment.priority = 'non-urgent';
          state.currentAssessment.estimatedWaitTime = 120;
        }
      }
    },
    completeAssessment: (state) => {
      if (state.currentAssessment) {
        state.assessments.push(state.currentAssessment);
        state.currentAssessment = null;
        state.isAssessing = false;
        state.currentStep = 0;
      }
    },
    nextStep: (state) => {
      if (state.currentStep < state.totalSteps - 1) {
        state.currentStep++;
      }
    },
    previousStep: (state) => {
      if (state.currentStep > 0) {
        state.currentStep--;
      }
    },
    setStep: (state, action: PayloadAction<number>) => {
      if (action.payload >= 0 && action.payload < state.totalSteps) {
        state.currentStep = action.payload;
      }
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
  startAssessment,
  updateAssessment,
  addSymptom,
  removeSymptom,
  updateVitalSigns,
  calculateTriageScore,
  completeAssessment,
  nextStep,
  previousStep,
  setStep,
  setLoading,
  setError,
  clearError,
} = triageSlice.actions;

export default triageSlice.reducer;
