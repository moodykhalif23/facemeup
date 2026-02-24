import NetInfo from '@react-native-community/netinfo';
import { store } from '../store';
import { setOnlineStatus, clearSyncQueue } from '../store/slices/offlineSlice';

let unsubscribe = null;

export const startNetworkMonitoring = () => {
  // Subscribe to network state updates
  unsubscribe = NetInfo.addEventListener(state => {
    const isOnline = state.isConnected && state.isInternetReachable;
    store.dispatch(setOnlineStatus(isOnline));
    
    // If back online, attempt to sync queued actions
    if (isOnline) {
      syncQueuedActions();
    }
  });
};

export const stopNetworkMonitoring = () => {
  if (unsubscribe) {
    unsubscribe();
  }
};

export const checkNetworkStatus = async () => {
  const state = await NetInfo.fetch();
  const isOnline = state.isConnected && state.isInternetReachable;
  store.dispatch(setOnlineStatus(isOnline));
  return isOnline;
};

const syncQueuedActions = async () => {
  const state = store.getState();
  const { syncQueue } = state.offline;
  
  if (syncQueue.length === 0) return;
  
  console.log(`Syncing ${syncQueue.length} queued actions...`);
  
  // Process each queued action
  for (const item of syncQueue) {
    try {
      // Here you would dispatch the actual API calls
      // For now, we'll just clear the queue
      console.log('Syncing action:', item.action);
      
      // Remove from queue after successful sync
      // store.dispatch(removeFromSyncQueue(item.id));
    } catch (error) {
      console.error('Failed to sync action:', error);
      // Keep in queue for retry
    }
  }
  
  // Clear queue after successful sync
  store.dispatch(clearSyncQueue());
};
