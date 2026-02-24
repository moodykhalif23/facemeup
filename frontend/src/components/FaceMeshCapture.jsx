import { useEffect, useRef, useState } from 'react';
import { FaceMesh } from '@mediapipe/face_mesh';
import { Camera } from '@mediapipe/camera_utils';

const FaceMeshCapture = ({ onCapture, onFaceDetected }) => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [isInitialized, setIsInitialized] = useState(false);
  const [faceDetected, setFaceDetected] = useState(false);
  const [error, setError] = useState(null);
  const faceMeshRef = useRef(null);
  const cameraRef = useRef(null);

  useEffect(() => {
    const initializeFaceMesh = async () => {
      try {
        // Initialize Face Mesh
        const faceMesh = new FaceMesh({
          locateFile: (file) => {
            return `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${file}`;
          }
        });

        faceMesh.setOptions({
          maxNumFaces: 1,
          refineLandmarks: true,
          minDetectionConfidence: 0.5,
          minTrackingConfidence: 0.5
        });

        // Process results
        faceMesh.onResults((results) => {
          const canvas = canvasRef.current;
          const ctx = canvas.getContext('2d');
          
          // Clear canvas
          ctx.clearRect(0, 0, canvas.width, canvas.height);
          
          // Draw video frame
          ctx.drawImage(results.image, 0, 0, canvas.width, canvas.height);

          if (results.multiFaceLandmarks && results.multiFaceLandmarks.length > 0) {
            setFaceDetected(true);
            
            // Draw face mesh
            const landmarks = results.multiFaceLandmarks[0];
            drawFaceMesh(ctx, landmarks, canvas.width, canvas.height);
            
            // Notify parent component
            if (onFaceDetected) {
              onFaceDetected(landmarks);
            }
          } else {
            setFaceDetected(false);
          }
        });

        faceMeshRef.current = faceMesh;

        // Initialize camera
        if (videoRef.current) {
          const camera = new Camera(videoRef.current, {
            onFrame: async () => {
              await faceMesh.send({ image: videoRef.current });
            },
            width: 640,
            height: 480
          });

          await camera.start();
          cameraRef.current = camera;
          setIsInitialized(true);
        }
      } catch (err) {
        console.error('Failed to initialize Face Mesh:', err);
        setError(err.message);
      }
    };

    initializeFaceMesh();

    // Cleanup
    return () => {
      if (cameraRef.current) {
        cameraRef.current.stop();
      }
    };
  }, [onFaceDetected]);

  const drawFaceMesh = (ctx, landmarks, width, height) => {
    ctx.fillStyle = '#00FF00';
    ctx.strokeStyle = '#00FF00';
    ctx.lineWidth = 1;

    // Draw landmarks
    landmarks.forEach((landmark) => {
      const x = landmark.x * width;
      const y = landmark.y * height;
      ctx.beginPath();
      ctx.arc(x, y, 1, 0, 2 * Math.PI);
      ctx.fill();
    });

    // Draw face contour
    const faceOval = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136, 172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109];
    
    ctx.beginPath();
    faceOval.forEach((index, i) => {
      const landmark = landmarks[index];
      const x = landmark.x * width;
      const y = landmark.y * height;
      if (i === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });
    ctx.closePath();
    ctx.stroke();
  };

  const captureFace = () => {
    if (!faceDetected) {
      alert('No face detected. Please position your face in the frame.');
      return;
    }

    const canvas = canvasRef.current;
    canvas.toBlob((blob) => {
      if (onCapture) {
        onCapture(blob);
      }
    }, 'image/jpeg', 0.95);
  };

  const extractFaceRegion = () => {
    if (!faceDetected || !faceMeshRef.current) {
      return null;
    }

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    // Get current frame
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    
    return imageData;
  };

  if (error) {
    return (
      <div className="face-mesh-error">
        <p>Error initializing camera: {error}</p>
        <p>Please ensure camera permissions are granted.</p>
      </div>
    );
  }

  return (
    <div className="face-mesh-container">
      <video
        ref={videoRef}
        style={{ display: 'none' }}
        playsInline
      />
      <canvas
        ref={canvasRef}
        width={640}
        height={480}
        style={{
          width: '100%',
          maxWidth: '640px',
          border: faceDetected ? '3px solid #00FF00' : '3px solid #FF0000',
          borderRadius: '8px'
        }}
      />
      <div className="face-mesh-status">
        {!isInitialized && <p>Initializing camera...</p>}
        {isInitialized && (
          <p style={{ color: faceDetected ? '#00FF00' : '#FF0000' }}>
            {faceDetected ? '✓ Face Detected' : '✗ No Face Detected'}
          </p>
        )}
      </div>
      <button
        onClick={captureFace}
        disabled={!faceDetected}
        style={{
          marginTop: '1rem',
          padding: '0.75rem 1.5rem',
          fontSize: '1rem',
          backgroundColor: faceDetected ? '#4CAF50' : '#ccc',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: faceDetected ? 'pointer' : 'not-allowed'
        }}
      >
        Capture Face
      </button>
    </div>
  );
};

export default FaceMeshCapture;
