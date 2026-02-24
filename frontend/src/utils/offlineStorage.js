import AsyncStorage from '@react-native-async-storage/async-storage';

const KEYS = {
  PROFILE_CACHE: '@skincare/profile_cache',
  ANALYSIS_CACHE: '@skincare/analysis_cache',
  PHOTOS_CACHE: '@skincare/photos_cache',
  PRODUCTS_CACHE: '@skincare/products_cache',
};

// Profile caching
export const cacheProfile = async (userId, profileData) => {
  try {
    const key = `${KEYS.PROFILE_CACHE}_${userId}`;
    await AsyncStorage.setItem(key, JSON.stringify({
      data: profileData,
      timestamp: new Date().toISOString(),
    }));
  } catch (error) {
    console.error('Failed to cache profile:', error);
  }
};

export const getCachedProfile = async (userId) => {
  try {
    const key = `${KEYS.PROFILE_CACHE}_${userId}`;
    const cached = await AsyncStorage.getItem(key);
    if (cached) {
      const { data, timestamp } = JSON.parse(cached);
      // Check if cache is less than 24 hours old
      const age = Date.now() - new Date(timestamp).getTime();
      if (age < 24 * 60 * 60 * 1000) {
        return data;
      }
    }
    return null;
  } catch (error) {
    console.error('Failed to get cached profile:', error);
    return null;
  }
};

// Analysis caching
export const cacheAnalysis = async (userId, analysisData) => {
  try {
    const key = `${KEYS.ANALYSIS_CACHE}_${userId}`;
    const existing = await AsyncStorage.getItem(key);
    let analyses = existing ? JSON.parse(existing) : [];
    
    analyses.unshift({
      ...analysisData,
      cachedAt: new Date().toISOString(),
    });
    
    // Keep only last 10 analyses
    if (analyses.length > 10) {
      analyses = analyses.slice(0, 10);
    }
    
    await AsyncStorage.setItem(key, JSON.stringify(analyses));
  } catch (error) {
    console.error('Failed to cache analysis:', error);
  }
};

export const getCachedAnalyses = async (userId) => {
  try {
    const key = `${KEYS.ANALYSIS_CACHE}_${userId}`;
    const cached = await AsyncStorage.getItem(key);
    return cached ? JSON.parse(cached) : [];
  } catch (error) {
    console.error('Failed to get cached analyses:', error);
    return [];
  }
};

// Photos caching
export const cachePhotos = async (userId, photos) => {
  try {
    const key = `${KEYS.PHOTOS_CACHE}_${userId}`;
    await AsyncStorage.setItem(key, JSON.stringify(photos));
  } catch (error) {
    console.error('Failed to cache photos:', error);
  }
};

export const getCachedPhotos = async (userId) => {
  try {
    const key = `${KEYS.PHOTOS_CACHE}_${userId}`;
    const cached = await AsyncStorage.getItem(key);
    return cached ? JSON.parse(cached) : [];
  } catch (error) {
    console.error('Failed to get cached photos:', error);
    return [];
  }
};

// Products caching
export const cacheProducts = async (products) => {
  try {
    await AsyncStorage.setItem(KEYS.PRODUCTS_CACHE, JSON.stringify({
      data: products,
      timestamp: new Date().toISOString(),
    }));
  } catch (error) {
    console.error('Failed to cache products:', error);
  }
};

export const getCachedProducts = async () => {
  try {
    const cached = await AsyncStorage.getItem(KEYS.PRODUCTS_CACHE);
    if (cached) {
      const { data, timestamp } = JSON.parse(cached);
      // Check if cache is less than 1 hour old
      const age = Date.now() - new Date(timestamp).getTime();
      if (age < 60 * 60 * 1000) {
        return data;
      }
    }
    return null;
  } catch (error) {
    console.error('Failed to get cached products:', error);
    return null;
  }
};

// Clear all caches
export const clearAllCaches = async () => {
  try {
    const keys = await AsyncStorage.getAllKeys();
    const cacheKeys = keys.filter(key => 
      key.startsWith('@skincare/')
    );
    await AsyncStorage.multiRemove(cacheKeys);
  } catch (error) {
    console.error('Failed to clear caches:', error);
  }
};
