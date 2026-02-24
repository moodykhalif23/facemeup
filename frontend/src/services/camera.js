import { Camera, CameraResultType, CameraSource } from '@capacitor/camera';
import { Capacitor } from '@capacitor/core';

export const takePicture = async () => {
  try {
    // On web, use file input with camera capture
    if (Capacitor.getPlatform() === 'web') {
      return await captureFromWebCamera();
    }
    
    // On native platforms, use Capacitor Camera
    const image = await Camera.getPhoto({
      quality: 80,
      allowEditing: false,
      resultType: CameraResultType.Base64,
      source: CameraSource.Camera,
      width: 1024,
      height: 1024,
      correctOrientation: true,
    });

    return image.base64String;
  } catch (error) {
    console.error('Camera error:', error);
    throw error;
  }
};

// Web-specific camera capture using file input
const captureFromWebCamera = () => {
  return new Promise((resolve, reject) => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.capture = 'environment'; // Use back camera on mobile web
    
    input.onchange = async (e) => {
      const file = e.target.files?.[0];
      if (!file) {
        reject(new Error('No file selected'));
        return;
      }

      try {
        const base64 = await fileToBase64(file);
        resolve(base64);
      } catch (error) {
        reject(error);
      }
    };

    input.oncancel = () => {
      reject(new Error('User cancelled'));
    };

    input.click();
  });
};

// Convert file to base64
const fileToBase64 = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => {
      const base64 = reader.result.split(',')[1];
      resolve(base64);
    };
    reader.onerror = (error) => reject(error);
  });
};

export const pickImage = async () => {
  try {
    const image = await Camera.getPhoto({
      quality: 80,
      allowEditing: true,
      resultType: CameraResultType.Base64,
      source: CameraSource.Photos,
      width: 1024,
      height: 1024,
    });

    return image.base64String;
  } catch (error) {
    console.error('Image picker error:', error);
    throw error;
  }
};
