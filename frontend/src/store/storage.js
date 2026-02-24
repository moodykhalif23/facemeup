import { Preferences } from '@capacitor/preferences';
import { Capacitor } from '@capacitor/core';

const isNative = Capacitor.isNativePlatform();

const storage = {
  async getItem(key) {
    if (isNative) {
      const { value } = await Preferences.get({ key });
      return value;
    }
    return localStorage.getItem(key);
  },

  async setItem(key, value) {
    if (isNative) {
      await Preferences.set({ key, value });
    } else {
      localStorage.setItem(key, value);
    }
  },

  async removeItem(key) {
    if (isNative) {
      await Preferences.remove({ key });
    } else {
      localStorage.removeItem(key);
    }
  },
};

export default storage;
