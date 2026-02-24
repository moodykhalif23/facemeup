import { Camera, CameraResultType, CameraSource } from '@capacitor/camera';

export const takePicture = async () => {
  try {
    const image = await Camera.getPhoto({
      quality: 80,
      allowEditing: true,
      resultType: CameraResultType.Base64,
      source: CameraSource.Camera,
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
    });

    return image.base64String;
  } catch (error) {
    console.error('Image picker error:', error);
    throw error;
  }
};
