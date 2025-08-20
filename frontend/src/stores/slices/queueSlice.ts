/**
 * Queue Slice
 * Manages patient queue and wait times
 */

import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface QueuedPatient {
  id: string;
  patientId: string;
  patientName: string;
  priority: 'critical' | 'urgent' | 'semi-urgent' | 'non-urgent';
  estimatedWaitTime: number;
  checkedInAt: string;
  triageCompletedAt?: string;
  status: 'waiting' | 'in-progress' | 'completed' | 'missed';
  queuePosition: number;
  roomAssigned?: string;
}

interface QueueStats {
  totalPatients: number;
  averageWaitTime: number;
  criticalCount: number;
  urgentCount: number;
  semiUrgentCount: number;
  nonUrgentCount: number;
}

interface QueueState {
  queue: QueuedPatient[];
  stats: QueueStats;
  isLoading: boolean;
  error: string | null;
  lastUpdated: string;
}

const initialState: QueueState = {
  queue: [],
  stats: {
    totalPatients: 0,
    averageWaitTime: 0,
    criticalCount: 0,
    urgentCount: 0,
    semiUrgentCount: 0,
    nonUrgentCount: 0,
  },
  isLoading: false,
  error: null,
  lastUpdated: new Date().toISOString(),
};

const queueSlice = createSlice({
  name: 'queue',
  initialState,
  reducers: {
    addToQueue: (state, action: PayloadAction<Omit<QueuedPatient, 'queuePosition'>>) => {
      const newPatient = {
        ...action.payload,
        queuePosition: state.queue.length + 1,
      };
      state.queue.push(newPatient);
      state.lastUpdated = new Date().toISOString();
      queueSlice.caseReducers.updateStats(state);
    },
    removeFromQueue: (state, action: PayloadAction<string>) => {
      state.queue = state.queue.filter(p => p.id !== action.payload);
      // Recalculate positions
      state.queue.forEach((patient, index) => {
        patient.queuePosition = index + 1;
      });
      state.lastUpdated = new Date().toISOString();
      queueSlice.caseReducers.updateStats(state);
    },
    updateQueuedPatient: (state, action: PayloadAction<{ id: string; updates: Partial<QueuedPatient> }>) => {
      const { id, updates } = action.payload;
      const index = state.queue.findIndex(p => p.id === id);
      if (index !== -1) {
        state.queue[index] = { ...state.queue[index], ...updates };
      }
      state.lastUpdated = new Date().toISOString();
      queueSlice.caseReducers.updateStats(state);
    },
    movePatientUp: (state, action: PayloadAction<string>) => {
      const index = state.queue.findIndex(p => p.id === action.payload);
      if (index > 0) {
        // Swap with previous patient
        [state.queue[index - 1], state.queue[index]] = [state.queue[index], state.queue[index - 1]];
        // Update positions
        state.queue.forEach((patient, i) => {
          patient.queuePosition = i + 1;
        });
      }
      state.lastUpdated = new Date().toISOString();
    },
    movePatientDown: (state, action: PayloadAction<string>) => {
      const index = state.queue.findIndex(p => p.id === action.payload);
      if (index < state.queue.length - 1 && index !== -1) {
        // Swap with next patient
        [state.queue[index], state.queue[index + 1]] = [state.queue[index + 1], state.queue[index]];
        // Update positions
        state.queue.forEach((patient, i) => {
          patient.queuePosition = i + 1;
        });
      }
      state.lastUpdated = new Date().toISOString();
    },
    sortQueueByPriority: (state) => {
      const priorityOrder = { critical: 0, urgent: 1, 'semi-urgent': 2, 'non-urgent': 3 };
      state.queue.sort((a, b) => {
        const priorityDiff = priorityOrder[a.priority] - priorityOrder[b.priority];
        if (priorityDiff !== 0) return priorityDiff;
        // If same priority, sort by check-in time
        return new Date(a.checkedInAt).getTime() - new Date(b.checkedInAt).getTime();
      });
      // Update positions
      state.queue.forEach((patient, index) => {
        patient.queuePosition = index + 1;
      });
      state.lastUpdated = new Date().toISOString();
    },
    updateStats: (state) => {
      state.stats = {
        totalPatients: state.queue.length,
        averageWaitTime: state.queue.length > 0 
          ? state.queue.reduce((sum, p) => sum + p.estimatedWaitTime, 0) / state.queue.length 
          : 0,
        criticalCount: state.queue.filter(p => p.priority === 'critical').length,
        urgentCount: state.queue.filter(p => p.priority === 'urgent').length,
        semiUrgentCount: state.queue.filter(p => p.priority === 'semi-urgent').length,
        nonUrgentCount: state.queue.filter(p => p.priority === 'non-urgent').length,
      };
    },
    setQueue: (state, action: PayloadAction<QueuedPatient[]>) => {
      state.queue = action.payload;
      state.lastUpdated = new Date().toISOString();
      queueSlice.caseReducers.updateStats(state);
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
  addToQueue,
  removeFromQueue,
  updateQueuedPatient,
  movePatientUp,
  movePatientDown,
  sortQueueByPriority,
  updateStats,
  setQueue,
  setLoading,
  setError,
  clearError,
} = queueSlice.actions;

export default queueSlice.reducer;
