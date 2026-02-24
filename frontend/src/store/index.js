import { configureStore } from '@reduxjs/toolkit';
import { persistStore, persistReducer, FLUSH, REHYDRATE, PAUSE, PERSIST, PURGE, REGISTER } from 'redux-persist';
import storage from './storage';
import authReducer from './slices/authSlice';
import analysisReducer from './slices/analysisSlice';
import cartReducer from './slices/cartSlice';

const persistConfig = {
  key: 'root',
  version: 1,
  storage,
  whitelist: ['auth', 'cart'],
};

const rootReducer = {
  auth: persistReducer({ ...persistConfig, key: 'auth' }, authReducer),
  analysis: analysisReducer,
  cart: persistReducer({ ...persistConfig, key: 'cart' }, cartReducer),
};

export const store = configureStore({
  reducer: rootReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: [FLUSH, REHYDRATE, PAUSE, PERSIST, PURGE, REGISTER],
      },
    }),
});

export const persistor = persistStore(store);
