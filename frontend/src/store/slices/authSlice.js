import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  token: null,
  refreshToken: null,
  user: null,
};

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setCredentials: (state, action) => {
      state.token = action.payload.access_token;
      state.refreshToken = action.payload.refresh_token;
      state.user = {
        id: action.payload.user_id,
        email: action.payload.email,
        role: action.payload.role,
      };
    },
    logout: (state) => {
      state.token = null;
      state.refreshToken = null;
      state.user = null;
    },
  },
});

export const { setCredentials, logout } = authSlice.actions;
export default authSlice.reducer;
