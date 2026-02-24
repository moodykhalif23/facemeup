import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  currentAnalysis: null,
  history: [],
};

const analysisSlice = createSlice({
  name: 'analysis',
  initialState,
  reducers: {
    setCurrentAnalysis: (state, action) => {
      state.currentAnalysis = action.payload;
    },
    addToHistory: (state, action) => {
      state.history.unshift(action.payload);
      if (state.history.length > 10) {
        state.history = state.history.slice(0, 10);
      }
    },
    clearAnalysis: (state) => {
      state.currentAnalysis = null;
    },
  },
});

export const { setCurrentAnalysis, addToHistory, clearAnalysis } = analysisSlice.actions;
export default analysisSlice.reducer;
