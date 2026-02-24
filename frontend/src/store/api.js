import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

const API_BASE_URL = 'http://localhost:8000/api/v1';

export const api = createApi({
  reducerPath: 'api',
  baseQuery: fetchBaseQuery({
    baseUrl: API_BASE_URL,
    prepareHeaders: (headers, { getState }) => {
      const token = getState().auth.token;
      if (token) {
        headers.set('authorization', `Bearer ${token}`);
      }
      return headers;
    },
  }),
  tagTypes: ['Analysis', 'Profile', 'Products', 'Loyalty'],
  endpoints: (builder) => ({
    // Auth endpoints
    login: builder.mutation({
      query: (credentials) => ({
        url: '/auth/login',
        method: 'POST',
        body: credentials,
      }),
    }),
    signup: builder.mutation({
      query: (userData) => ({
        url: '/auth/signup',
        method: 'POST',
        body: userData,
      }),
    }),
    
    // Analysis endpoints
    analyze: builder.mutation({
      query: (data) => ({
        url: '/analyze',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['Analysis', 'Profile'],
    }),
    
    // Recommendations
    getRecommendations: builder.mutation({
      query: (data) => ({
        url: '/recommend',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['Products'],
    }),
    
    // Profile
    getProfile: builder.query({
      query: (userId) => `/profile/${userId}`,
      providesTags: ['Profile'],
    }),
    
    // Products (for future implementation)
    getProducts: builder.query({
      query: () => '/products',
      providesTags: ['Products'],
    }),
    
    // Loyalty (for future implementation)
    getLoyaltyData: builder.query({
      query: (userId) => `/loyalty/${userId}`,
      providesTags: ['Loyalty'],
    }),
  }),
});

export const {
  useLoginMutation,
  useSignupMutation,
  useAnalyzeMutation,
  useGetRecommendationsMutation,
  useGetProfileQuery,
  useGetProductsQuery,
  useGetLoyaltyDataQuery,
} = api;
