import { useRef, useState, useEffect } from 'react';
import { Modal, Button, Space } from 'antd';
import { CameraOutlined, CloseOutlined, ReloadOutlined } from '@ant-design/icons';

export default function WebCamera({ visible, onCapture, onCancel }) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [stream, setStream] = useState(null);
  const [facingMode, setFacingMode] = useState('user');

  useEffect(() => {
    if (visible) {
      startCamera();
    } else {
      stopCamera();
    }

    return () => {
      stopCamera();
    };
  }, [visible, facingMode]);

  const startCamera = async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: facingMode,
          width: { ideal: 1280 },
          height: { ideal: 720 }
        },
        audio: false
      });

      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
        setStream(mediaStream);
      }
    } catch (error) {
      console.error('Error accessing camera:', error);
      alert('Unable to access camera. Please check permissions.');
    }
  };

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
    }
  };

  const capturePhoto = () => {
    if (!videoRef.current || !canvasRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    const context = canvas.getContext('2d');
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    // Convert to base64
    canvas.toBlob((blob) => {
      const reader = new FileReader();
      reader.readAsDataURL(blob);
      reader.onloadend = () => {
        const base64 = reader.result.split(',')[1];
        stopCamera();
        onCapture(base64);
      };
    }, 'image/jpeg', 0.8);
  };

  const switchCamera = () => {
    setFacingMode(prev => prev === 'user' ? 'environment' : 'user');
  };

  const handleCancel = () => {
    stopCamera();
    onCancel();
  };

  return (
    <Modal
      open={visible}
      onCancel={handleCancel}
      footer={null}
      width="100%"
      style={{ top: 0, maxWidth: '100vw', padding: 0 }}
      styles={{
        body: { padding: 0, height: '100vh' }
      }}
      closable={false}
    >
      <div style={{
        position: 'relative',
        width: '100%',
        height: '100vh',
        background: '#000',
        display: 'flex',
        flexDirection: 'column'
      }}>
        {/* Video Preview */}
        <div style={{
          flex: 1,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          overflow: 'hidden'
        }}>
          <video
            ref={videoRef}
            autoPlay
            playsInline
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover'
            }}
          />
        </div>

        {/* Hidden canvas for capture */}
        <canvas ref={canvasRef} style={{ display: 'none' }} />

        {/* Controls */}
        <div style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          padding: '24px',
          background: 'linear-gradient(to top, rgba(0,0,0,0.7), transparent)',
          display: 'flex',
          justifyContent: 'space-around',
          alignItems: 'center'
        }}>
          <Button
            icon={<CloseOutlined />}
            onClick={handleCancel}
            size="large"
            shape="circle"
            style={{
              width: 56,
              height: 56,
              background: 'rgba(255,255,255,0.2)',
              border: 'none',
              color: '#fff'
            }}
          />

          <Button
            icon={<CameraOutlined />}
            onClick={capturePhoto}
            type="primary"
            size="large"
            shape="circle"
            style={{
              width: 72,
              height: 72,
              fontSize: 32
            }}
          />

          <Button
            icon={<ReloadOutlined />}
            onClick={switchCamera}
            size="large"
            shape="circle"
            style={{
              width: 56,
              height: 56,
              background: 'rgba(255,255,255,0.2)',
              border: 'none',
              color: '#fff'
            }}
          />
        </div>

        {/* Instructions */}
        <div style={{
          position: 'absolute',
          top: 24,
          left: 0,
          right: 0,
          textAlign: 'center',
          padding: '0 24px'
        }}>
          <div style={{
            background: 'rgba(0,0,0,0.6)',
            padding: '12px 20px',
            borderRadius: 6,
            display: 'inline-block'
          }}>
            <p style={{ color: '#fff', margin: 0, fontSize: 14 }}>
              Position your face in the center
            </p>
          </div>
        </div>
      </div>
    </Modal>
  );
}

