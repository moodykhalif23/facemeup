import { useState } from 'react';
import FaceMeshCapture from './FaceMeshCapture';
import { useNavigate } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import { setAnalysisResult } from '../store/slices/analysisSlice';
import api from '../services/api';

const FaceMeshAnalysis = () => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [landmarks, setLandmarks] = useState(null);
  const navigate = useNavigate();
  const dispatch = useDispatch();

  const handleFaceDetected = (detectedLandmarks) => {
    setLandmarks(detectedLandmarks);
  };

  const handleCapture = async (blob) => {
    setIsAnalyzing(true);

    try {
      // Convert blob to base64
      const reader = new FileReader();
      reader.readAsDataURL(blob);
      
      reader.onloadend = async () => {
        const base64Image = reader.result.split(',')[1];

        // Send to backend for analysis
        const response = await api.post('/analyze', {
          image_base64: base64Image,
          questionnaire: {},
          landmarks: landmarks ? landmarks.map(lm => ({
            x: lm.x,
            y: lm.y,
            z: lm.z
          })) : null
        });

        // Store result and navigate
        dispatch(setAnalysisResult(response.data));
        navigate('/results');
      };
    } catch (error) {
      console.error('Analysis failed:', error);
      alert('Analysis failed. Please try again.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="face-mesh-analysis">
      <h2>Face Analysis with MediaPipe</h2>
      <p>Position your face in the frame for automatic detection</p>
      
      {isAnalyzing ? (
        <div className="analyzing-overlay">
          <div className="spinner"></div>
          <p>Analyzing your skin...</p>
        </div>
      ) : (
        <FaceMeshCapture
          onCapture={handleCapture}
          onFaceDetected={handleFaceDetected}
        />
      )}

      <div className="instructions">
        <h3>Tips for Best Results:</h3>
        <ul>
          <li>Ensure good lighting on your face</li>
          <li>Remove glasses if possible</li>
          <li>Look directly at the camera</li>
          <li>Keep your face centered in the frame</li>
          <li>Wait for the green border (face detected)</li>
        </ul>
      </div>

      <style jsx>{`
        .face-mesh-analysis {
          max-width: 800px;
          margin: 0 auto;
          padding: 2rem;
        }

        .analyzing-overlay {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          min-height: 400px;
        }

        .spinner {
          border: 4px solid #f3f3f3;
          border-top: 4px solid #3498db;
          border-radius: 50%;
          width: 50px;
          height: 50px;
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }

        .instructions {
          margin-top: 2rem;
          padding: 1rem;
          background: #f5f5f5;
          border-radius: 8px;
        }

        .instructions ul {
          margin-top: 0.5rem;
          padding-left: 1.5rem;
        }

        .instructions li {
          margin: 0.5rem 0;
        }
      `}</style>
    </div>
  );
};

export default FaceMeshAnalysis;
