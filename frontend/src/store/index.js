import { configureStore } from '@reduxjs/toolkit';
import { setupListeners } from '@reduxjs/toolkit/query';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { persistStore, persistReducer, FLUSH, REHYDRATE, PAUSE, PERSIST, PURGE, REGISTER } from 'redux-persist';
import { combineReducers } from 'redux';

import authReducer from './slices/authSlice';
import analysisReducer from './slices/analysisSlice';
import cartReducer from './slices/cartSlice';
import offlineReducer from './slices/offlineSlice';
import { api } from './api';

const persistConfig = {
  key: 'root',
  version: 1,
  storage: AsyncStorage,
  whitelist: ['auth', 'cart', 'offline'], // Only persist these reducers
};

const rootReducer = combineReducers({
  auth: authReducer,
  analysis: analysisReducer,
  cart: cartReducer,
  offline: offlineReducer,
  [api.reducerPath]: api.reducer,
});

const persistedReducer = persistReducer(persistConfig, rootReducer);

export const store = configureStore({
  reducer: persistedReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: [FLUSH, REHYDRATE, PAUSE, PERSIST, PURGE, REGISTER],
      },
    }).concat(api.middleware),
});

export const persistor = persistStore(store);

// Enable refetchOnFocus/refetchOnReconnect behaviors
setupListeners(store.dispatch);
