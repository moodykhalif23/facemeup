# MediaPipe Face Mesh Integration Guide

## Overview

This document describes the MediaPipe Face Mesh integration for real-time face detection and enhanced skin analysis in the skincare application.

## Features

- Real-time face detection with 468 facial landmarks
- Automatic face region extraction and cropping
- Face quality scoring for better analysis accuracy
- Visual feedback with face mesh overlay
- Seamless integration with existing analysis pipeline

## Architecture

### Frontend Components

#### 1. FaceMeshCapture Component
Location: `frontend/src/components/FaceMeshCapture.jsx`

Handles real-time face detection and capture:
- Initializes MediaPipe Face Mesh with optimal settings
- Processes video stream for face landmarks
- Draws visual feedback (face mesh overlay)
- Captures face image when detected
- Provides face detection status

**Key Features:**
- 468 landmark points detection
- Real-time visual feedback (green border when face detected)
- Automatic face quality validation
- Canvas-based rendering for performance

#### 2. FaceMeshAnalysis Component
Location: `frontend/src/components/FaceMeshAnalysis.jsx`

Integrates face detection with analysis workflow:
- Manages capture and analysis flow
- Sends landmarks to backend for processing
- Handles loading states and errors
- Provides user instructions

### Backend Services

#### 1. Face Processor Service
Location: `backend/app/services/face_processor.py`

Core face processing functionality:

**FaceProcessor Class Methods:**

- `extract_face_region(image, landmarks)`: Extracts face region using landmarks with 20% padding
- `preprocess_for_model(face_image)`: Resizes and normalizes for model input
- `decode_base64_image(base64_string)`: Converts base64 to numpy array
- `process_image_with_landmarks(base64_image, landmarks)`: Complete pipeline
- `get_face_quality_score(landmarks)`: Calculates quality score (0-1)
- `extract_face_features(landmarks)`: Extracts useful features from landmarks

**Face Quality Scoring:**
- Size score (60%): Larger faces = better quality
- Centering score (40%): Centered faces = better quality
- Combined score ranges from 0.0 to 1.0

#### 2. Enhanced Inference Service
Location: `backend/app/services/inference.py`

Updated to support landmark-based preprocessing:
- Accepts optional landmarks parameter
- Uses face processor when landmarks provided
- Falls back to standard preprocessing without landmarks
- Includes face quality score in response

### API Updates

#### Analyze Endpoint
Location: `backend/app/api/v1/endpoints/analyze.py`

**Request Schema:**
```json
{
  "image_base64": "string",
  "questionnaire": {
    "skin_feel": "string",
    "routine": "string",
    "concerns": ["string"]
  },
  "landmarks": [
    {
      "x": 0.5,
      "y": 0.5,
      "z": 0.0
    }
  ]
}
```

**Response Schema:**
```json
{
  "profile": {
    "skin_type": "string",
    "conditions": ["string"],
    "confidence": 0.85,
    "face_quality_score": 0.92
  },
  "inference_mode": "server_savedmodel"
}
```

## Installation

### Frontend Dependencies

```bash
cd frontend
npm install @mediapipe/face_mesh @mediapipe/camera_utils
```

### Backend Dependencies

```bash
cd backend
pip install opencv-python>=4.8.0
```

Or rebuild Docker container:
```bash
docker-compose build backend
docker-compose up -d
```

## Usage

### User Flow

1. Navigate to Analysis page
2. Select "AI Face Detection" tab
3. Allow camera permissions
4. Position face in frame
5. Wait for green border (face detected)
6. Click "Capture Face" button
7. Analysis runs automatically with landmarks
8. View results with quality score

### Developer Integration

#### Using FaceMeshCapture Component

```javascript
import FaceMeshCapture from '../components/FaceMeshCapture';

function MyComponent() {
  const handleCapture = (blob) => {
    // Handle captured image
    console.log('Captured:', blob);
  };

  const handleFaceDetected = (landmarks) => {
    // Handle face detection
    console.log('Face detected with', landmarks.length, 'landmarks');
  };

  return (
    <FaceMeshCapture
      onCapture={handleCapture}
      onFaceDetected={handleFaceDetected}
    />
  );
}
```

#### Backend Face Processing

```python
from app.services.face_processor import face_processor

# Process image with landmarks
landmarks = [{"x": 0.5, "y": 0.5, "z": 0.0}, ...]
processed_image = face_processor.process_image_with_landmarks(
    base64_image, 
    landmarks
)

# Get quality score
quality_score = face_processor.get_face_quality_score(landmarks)

# Extract features
features = face_processor.extract_face_features(landmarks)
```

## Configuration

### MediaPipe Settings

Located in `FaceMeshCapture.jsx`:

```javascript
faceMesh.setOptions({
  maxNumFaces: 1,              // Detect single face
  refineLandmarks: true,        // High precision landmarks
  minDetectionConfidence: 0.5,  // Detection threshold
  minTrackingConfidence: 0.5    // Tracking threshold
});
```

### Face Processor Settings

Located in `face_processor.py`:

```python
class FaceProcessor:
    def __init__(self):
        self.padding = 0.2          # 20% padding around face
        self.target_size = (224, 224)  # Model input size
```

## Benefits

### Improved Accuracy
- Precise face region extraction
- Consistent face cropping
- Better lighting normalization
- Reduced background noise

### Better User Experience
- Real-time visual feedback
- Automatic face detection
- Quality validation before capture
- Clear instructions and status

### Enhanced Analysis
- Face quality scoring
- Landmark-based features
- Consistent preprocessing
- Better model performance

## Performance Considerations

### Frontend
- MediaPipe runs efficiently in browser
- Canvas rendering for smooth visualization
- Minimal CPU usage with GPU acceleration
- Works on mobile and desktop

### Backend
- OpenCV for fast image processing
- Numpy for efficient array operations
- Cached model loading
- Sub-500ms inference time

## Troubleshooting

### Camera Not Working
- Check browser permissions
- Ensure HTTPS or localhost
- Try different browser
- Check camera availability

### Face Not Detected
- Improve lighting conditions
- Remove glasses/obstructions
- Center face in frame
- Move closer to camera
- Ensure face is clearly visible

### Low Quality Score
- Improve lighting
- Center face better
- Move closer to camera
- Remove obstructions
- Ensure clear visibility

### Backend Errors
- Check OpenCV installation
- Verify landmarks format
- Check image decoding
- Review error logs

## Future Enhancements

### Planned Features
1. Multi-face detection support
2. Face angle validation
3. Lighting quality assessment
4. Skin tone detection
5. Region-specific analysis (forehead, cheeks, etc.)
6. Historical quality tracking
7. Automatic retake suggestions

### Advanced Processing
1. Face alignment normalization
2. Skin texture analysis from landmarks
3. Wrinkle detection using depth (z-coordinate)
4. Symmetry analysis
5. Age estimation features

## Testing

### Frontend Testing
```bash
cd frontend
npm run dev
# Navigate to http://localhost:5173/analysis
# Test both Standard and AI Face Detection tabs
```

### Backend Testing
```bash
# Test face processor
docker exec skincare-api python -c "
from app.services.face_processor import face_processor
import numpy as np

# Test with dummy landmarks
landmarks = [{'x': 0.5, 'y': 0.5, 'z': 0.0} for _ in range(468)]
score = face_processor.get_face_quality_score(landmarks)
print(f'Quality score: {score}')
"
```

### API Testing
```bash
# Test analyze endpoint with landmarks
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "image_base64": "BASE64_IMAGE",
    "landmarks": [
      {"x": 0.5, "y": 0.5, "z": 0.0}
    ]
  }'
```

## References

- [MediaPipe Face Mesh](https://google.github.io/mediapipe/solutions/face_mesh.html)
- [MediaPipe JavaScript API](https://www.npmjs.com/package/@mediapipe/face_mesh)
- [OpenCV Python](https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html)
- [Face Mesh Landmarks](https://github.com/google/mediapipe/blob/master/mediapipe/modules/face_geometry/data/canonical_face_model_uv_visualization.png)

## Support

For issues or questions:
1. Check this documentation
2. Review error logs
3. Test with standard camera mode
4. Check browser console for errors
5. Verify backend logs for processing errors
