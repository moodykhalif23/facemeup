import { Camera, CameraResultType, CameraSource } from '@capacitor/camera';

export const takePicture = async () => {
  try {
    const image = await Camera.getPhoto({
      quality: 80,
      allowEditing: false,
      resultType: CameraResultType.Base64,
      source: CameraSource.Camera, // Force camera, not file picker
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
