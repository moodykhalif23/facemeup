import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  currentAnalysis: null,
  history: [],
  loading: false,
  error: null,
  lastUpdated: null,
};

const analysisSlice = createSlice({
  name: 'analysis',
  initialState,
  reducers: {
    setCurrentAnalysis: (state, action) => {
      state.currentAnalysis = action.payload;
      state.lastUpdated = new Date().toISOString();
      state.error = null;
      
      // Add to history if not already present
      const exists = state.history.some(
        item => item.timestamp === action.payload.timestamp
      );
      if (!exists && action.payload.timestamp) {
        state.history.unshift(action.payload);
        // Keep only last 20 analyses
        if (state.history.length > 20) {
          state.history = state.history.slice(0, 20);
        }
      }
    },
    setAnalysisLoading: (state, action) => {
      state.loading = action.payload;
    },
    setAnalysisError: (state, action) => {
      state.error = action.payload;
      state.loading = false;
    },
    clearCurrentAnalysis: (state) => {
      state.currentAnalysis = null;
    },
    clearAnalysisError: (state) => {
      state.error = null;
    },
    setAnalysisHistory: (state, action) => {
      state.history = action.payload;
    },
  },
});

export const {
  setCurrentAnalysis,
  setAnalysisLoading,
  setAnalysisError,
  clearCurrentAnalysis,
  clearAnalysisError,
  setAnalysisHistory,
} = analysisSlice.actions;

export const selectCurrentAnalysis = (state) => state.analysis.currentAnalysis;
export const selectAnalysisHistory = (state) => state.analysis.history;
export const selectAnalysisLoading = (state) => state.analysis.loading;
export const selectAnalysisError = (state) => state.analysis.error;

export default analysisSlice.reducer;
