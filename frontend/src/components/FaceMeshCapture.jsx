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
  const isProcessingRef = useRef(false);

  useEffect(() => {
    let mounted = true;

    const initializeFaceMesh = async () => {
      try {
        if (!videoRef.current || !canvasRef.current) {
          return;
        }

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
          if (!mounted || !canvasRef.current) return;
          
          const canvas = canvasRef.current;
          const ctx = canvas.getContext('2d');
          
          // Clear canvas
          ctx.clearRect(0, 0, canvas.width, canvas.height);
          
          // Draw video frame
          if (results.image) {
            try {
              ctx.drawImage(results.image, 0, 0, canvas.width, canvas.height);
            } catch (e) {
              console.warn('Failed to draw image:', e);
              return;
            }
          }

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
          
          isProcessingRef.current = false;
        });

        faceMeshRef.current = faceMesh;

        // Initialize camera
        const video = videoRef.current;
        
        const camera = new Camera(video, {
          onFrame: async () => {
            if (!mounted || !video || isProcessingRef.current) return;
            
            // Check if video is ready
            if (video.readyState < 2) {
              return;
            }
            
            try {
              isProcessingRef.current = true;
              await faceMesh.send({ image: video });
            } catch (e) {
              console.warn('Failed to process frame:', e);
              isProcessingRef.current = false;
            }
          },
          width: 640,
          height: 480
        });

        cameraRef.current = camera;
        
        // Start camera
        await camera.start();
        
        if (!mounted) return;
        
        setIsInitialized(true);
      } catch (err) {
        console.error('Failed to initialize Face Mesh:', err);
        if (mounted) {
          setError(err.message || 'Failed to initialize camera');
        }
      }
    };

    initializeFaceMesh();

    // Cleanup
    return () => {
      mounted = false;
      if (cameraRef.current) {
        try {
          cameraRef.current.stop();
        } catch (e) {
          console.warn('Error stopping camera:', e);
        }
      }
      if (faceMeshRef.current) {
        try {
          faceMeshRef.current.close();
        } catch (e) {
          console.warn('Error closing face mesh:', e);
        }
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

  if (error) {
    return (
      <div className="face-mesh-error" style={{ 
        padding: '2rem', 
        textAlign: 'center',
        color: '#ff4d4f'
      }}>
        <p style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>Error initializing camera</p>
        <p style={{ fontSize: '0.9rem', color: '#666' }}>{error}</p>
        <p style={{ fontSize: '0.9rem', color: '#666', marginTop: '1rem' }}>
          Please ensure camera permissions are granted and try refreshing the page.
        </p>
      </div>
    );
  }

  return (
    <div className="face-mesh-container">
      <video
        ref={videoRef}
        style={{ display: 'none' }}
        playsInline
        autoPlay
      />
      <canvas
        ref={canvasRef}
        width={640}
        height={480}
        style={{
          width: '100%',
          maxWidth: '640px',
          border: faceDetected ? '3px solid #52c41a' : '3px solid #ff4d4f',
          borderRadius: '8px',
          backgroundColor: '#000'
        }}
      />
      <div className="face-mesh-status" style={{ 
        marginTop: '1rem',
        textAlign: 'center'
      }}>
        {!isInitialized && (
          <p style={{ color: '#1890ff' }}>Initializing camera...</p>
        )}
        {isInitialized && (
          <p style={{ 
            color: faceDetected ? '#52c41a' : '#ff4d4f',
            fontSize: '1.1rem',
            fontWeight: 500
          }}>
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
          backgroundColor: faceDetected ? '#52c41a' : '#d9d9d9',
          color: 'white',
          border: 'none',
          borderRadius: '8px',
          cursor: faceDetected ? 'pointer' : 'not-allowed',
          width: '100%',
          fontWeight: 600,
          transition: 'all 0.3s'
        }}
      >
        Capture Face
      </button>
    </div>
  );
};

export default FaceMeshCapture;
