import { useState, useRef, useEffect } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Alert, ActivityIndicator } from 'react-native';
import { Camera } from 'expo-camera';
import { AntDesign, MaterialIcons } from '@expo/vector-icons';
import { analyze } from '../api';

export default function CameraScreen({ navigation, token }) {
  const [hasPermission, setHasPermission] = useState(null);
  const [type, setType] = useState(Camera.Constants.Type.front);
  const [isCapturing, setIsCapturing] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const cameraRef = useRef(null);

  useEffect(() => {
    (async () => {
      const { status } = await Camera.requestCameraPermissionsAsync();
      setHasPermission(status === 'granted');
    })();
  }, []);

  const handleCapture = async () => {
    if (!cameraRef.current || isCapturing) return;

    try {
      setIsCapturing(true);

      // Capture photo
      const photo = await cameraRef.current.takePictureAsync({
        quality: 0.8,
        base64: true,
        skipProcessing: false,
      });

      // Analyze the photo
      await handleAnalyze(photo.base64);

    } catch (error) {
      console.error('Capture error:', error);
      Alert.alert('Error', 'Failed to capture photo. Please try again.');
    } finally {
      setIsCapturing(false);
    }
  };

  const handleAnalyze = async (imageBase64) => {
    setIsAnalyzing(true);

    try {
      // TODO: Add on-device TFLite inference here
      // For now, send to backend
      const result = await analyze(token, imageBase64);

      // Navigate to results
      navigation.navigate('AnalysisResults', {
        profile: result.profile,
        inferenceMode: result.inference_mode,
      });

    } catch (error) {
      console.error('Analysis error:', error);
      Alert.alert(
        'Analysis Failed',
        error?.response?.data?.error?.message || 'Failed to analyze image. Please try again.'
      );
    } finally {
      setIsAnalyzing(false);
    }
  };

  const toggleCameraType = () => {
    setType(
      type === Camera.Constants.Type.back
        ? Camera.Constants.Type.front
        : Camera.Constants.Type.back
    );
  };

  if (hasPermission === null) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color="#3B82F6" />
        <Text style={styles.loadingText}>Requesting camera permission...</Text>
      </View>
    );
  }

  if (hasPermission === false) {
    return (
      <View style={styles.container}>
        <AntDesign name="camerao" size={64} color="#9CA3AF" />
        <Text style={styles.permissionTitle}>Camera Access Required</Text>
        <Text style={styles.permissionText}>
          We need camera access to analyze your skin. Please enable camera permissions in your device settings.
        </Text>
        <TouchableOpacity
          style={styles.settingsButton}
          onPress={() => navigation.goBack()}
        >
          <Text style={styles.settingsButtonText}>Go Back</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Camera
        ref={cameraRef}
        style={styles.camera}
        type={type}
        ratio="16:9"
      >
        {/* Guided Overlay */}
        <View style={styles.overlay}>
          {/* Top Instructions */}
          <View style={styles.topSection}>
            <View style={styles.instructionCard}>
              <Text style={styles.instructionTitle}>Position Your Face</Text>
              <Text style={styles.instructionText}>
                • Center your face in the oval{'\n'}
                • Ensure good lighting{'\n'}
                • Remove glasses if possible{'\n'}
                • Keep face straight
              </Text>
            </View>
          </View>

          {/* Center Oval Guide */}
          <View style={styles.centerSection}>
            <View style={styles.ovalContainer}>
              <View style={styles.oval} />
              <View style={styles.ovalBorder} />
            </View>
          </View>

          {/* Bottom Controls */}
          <View style={styles.bottomSection}>
            {/* Flip Camera Button */}
            <TouchableOpacity
              style={styles.controlButton}
              onPress={toggleCameraType}
              disabled={isCapturing || isAnalyzing}
            >
              <MaterialIcons name="flip-camera-ios" size={32} color="#FFFFFF" />
            </TouchableOpacity>

            {/* Capture Button */}
            <TouchableOpacity
              style={[
                styles.captureButton,
                (isCapturing || isAnalyzing) && styles.captureButtonDisabled
              ]}
              onPress={handleCapture}
              disabled={isCapturing || isAnalyzing}
            >
              {isCapturing || isAnalyzing ? (
                <ActivityIndicator size="large" color="#FFFFFF" />
              ) : (
                <View style={styles.captureButtonInner} />
              )}
            </TouchableOpacity>

            {/* Close Button */}
            <TouchableOpacity
              style={styles.controlButton}
              onPress={() => navigation.goBack()}
              disabled={isCapturing || isAnalyzing}
            >
              <AntDesign name="close" size={32} color="#FFFFFF" />
            </TouchableOpacity>
          </View>

          {/* Analyzing Overlay */}
          {isAnalyzing && (
            <View style={styles.analyzingOverlay}>
              <View style={styles.analyzingCard}>
                <ActivityIndicator size="large" color="#3B82F6" />
                <Text style={styles.analyzingText}>Analyzing your skin...</Text>
                <Text style={styles.analyzingSubtext}>This may take a few seconds</Text>
              </View>
            </View>
          )}
        </View>
      </Camera>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    color: '#FFFFFF',
    fontSize: 16,
    marginTop: 16,
  },
  permissionTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: '#FFFFFF',
    marginTop: 24,
    marginBottom: 12,
  },
  permissionText: {
    fontSize: 16,
    color: '#9CA3AF',
    textAlign: 'center',
    paddingHorizontal: 40,
    lineHeight: 24,
    marginBottom: 32,
  },
  settingsButton: {
    backgroundColor: '#3B82F6',
    paddingHorizontal: 32,
    paddingVertical: 16,
    borderRadius: 12,
  },
  settingsButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
  },
  camera: {
    flex: 1,
    width: '100%',
  },
  overlay: {
    flex: 1,
    backgroundColor: 'transparent',
  },
  topSection: {
    flex: 1,
    justifyContent: 'flex-start',
    alignItems: 'center',
    paddingTop: 60,
  },
  instructionCard: {
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    borderRadius: 16,
    padding: 20,
    marginHorizontal: 20,
  },
  instructionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 12,
    textAlign: 'center',
  },
  instructionText: {
    fontSize: 14,
    color: '#E5E7EB',
    lineHeight: 22,
  },
  centerSection: {
    flex: 2,
    justifyContent: 'center',
    alignItems: 'center',
  },
  ovalContainer: {
    width: 280,
    height: 360,
    justifyContent: 'center',
    alignItems: 'center',
  },
  oval: {
    width: 260,
    height: 340,
    borderRadius: 130,
    backgroundColor: 'transparent',
    borderWidth: 3,
    borderColor: '#3B82F6',
    borderStyle: 'dashed',
  },
  ovalBorder: {
    position: 'absolute',
    width: 280,
    height: 360,
    borderRadius: 140,
    backgroundColor: 'transparent',
    borderWidth: 2,
    borderColor: 'rgba(59, 130, 246, 0.3)',
  },
  bottomSection: {
    flex: 1,
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
    paddingBottom: 40,
    paddingHorizontal: 20,
  },
  controlButton: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  captureButton: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#3B82F6',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 4,
    borderColor: '#FFFFFF',
    shadowColor: '#3B82F6',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.5,
    shadowRadius: 8,
    elevation: 8,
  },
  captureButtonDisabled: {
    backgroundColor: '#93C5FD',
    opacity: 0.7,
  },
  captureButtonInner: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: '#FFFFFF',
  },
  analyzingOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  analyzingCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 32,
    alignItems: 'center',
    minWidth: 280,
  },
  analyzingText: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1F2937',
    marginTop: 20,
  },
  analyzingSubtext: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 8,
  },
});
