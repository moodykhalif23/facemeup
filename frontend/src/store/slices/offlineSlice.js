import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  isOnline: true,
  syncQueue: [],
  lastSync: null,
  pendingActions: 0,
};

const offlineSlice = createSlice({
  name: 'offline',
  initialState,
  reducers: {
    setOnlineStatus: (state, action) => {
      state.isOnline = action.payload;
    },
    addToSyncQueue: (state, action) => {
      state.syncQueue.push({
        id: Date.now(),
        action: action.payload.action,
        data: action.payload.data,
        timestamp: new Date().toISOString(),
      });
      state.pendingActions = state.syncQueue.length;
    },
    removeFromSyncQueue: (state, action) => {
      state.syncQueue = state.syncQueue.filter(item => item.id !== action.payload);
      state.pendingActions = state.syncQueue.length;
    },
    clearSyncQueue: (state) => {
      state.syncQueue = [];
      state.pendingActions = 0;
      state.lastSync = new Date().toISOString();
    },
    setLastSync: (state, action) => {
      state.lastSync = action.payload;
    },
  },
});

export const {
  setOnlineStatus,
  addToSyncQueue,
  removeFromSyncQueue,
  clearSyncQueue,
  setLastSync,
} = offlineSlice.actions;

export const selectIsOnline = (state) => state.offline.isOnline;
export const selectSyncQueue = (state) => state.offline.syncQueue;
export const selectPendingActions = (state) => state.offline.pendingActions;
export const selectLastSync = (state) => state.offline.lastSync;

export default offlineSlice.reducer;
