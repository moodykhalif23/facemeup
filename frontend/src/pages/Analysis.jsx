import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import { Layout, Card, Button, Form, Select, Checkbox, Typography, Space, App, Spin } from 'antd';
import { ScanOutlined } from '@ant-design/icons';
import { setCurrentAnalysis, addToHistory } from '../store/slices/analysisSlice';
import AppHeader from '../components/AppHeader';
import FaceMeshCapture from '../components/FaceMeshCapture';
import api from '../services/api';

const { Content } = Layout;
const { Title, Text } = Typography;

export default function Analysis() {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [capturedImage, setCapturedImage] = useState(null);
  const [landmarks, setLandmarks] = useState(null);
  const [faceDetected, setFaceDetected] = useState(false);
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { message } = App.useApp();

  const handleFaceDetected = (detectedLandmarks) => {
    setLandmarks(detectedLandmarks);
    setFaceDetected(true);
  };

  const handleCapture = (blob) => {
    setCapturedImage(blob);
    message.success('Face captured! Please complete the questionnaire.');
  };

  const onFinish = async (values) => {
    if (!capturedImage || !landmarks) {
      message.warning('Please capture your face first');
      return;
    }

    setLoading(true);
    try {
      // Convert blob to base64
      const reader = new FileReader();
      reader.readAsDataURL(capturedImage);
      
      reader.onloadend = async () => {
        const base64Image = reader.result.split(',')[1];

        const questionnaire = {
          skin_feel: values.skinFeel,
          routine: values.routine,
          concerns: values.concerns || [],
        };

        // Send to backend for analysis
        const response = await api.post('/analyze', {
          image_base64: base64Image,
          questionnaire,
          landmarks: landmarks.map(lm => ({
            x: lm.x,
            y: lm.y,
            z: lm.z
          }))
        });

        // Store result and navigate
        dispatch(setCurrentAnalysis(response.data));
        dispatch(addToHistory(response.data));
        try {
          await api.post('/training/submit', {
            image_base64: base64Image,
            skin_type: response.data.profile.skin_type,
            conditions: response.data.profile.conditions || [],
          });
        } catch (trainErr) {
          console.warn('Training submission failed:', trainErr);
        }

        navigate('/results');
      };
    } catch (error) {
      console.error('Analysis failed:', error);
      message.error(error.response?.data?.error?.message || 'Analysis failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout style={{ minHeight: '100vh', background: '#f5f5f5' }}>
      <AppHeader title="AI Skin Analysis" showBack />

      <Content style={{ padding: '16px' }}>
        <div style={{ maxWidth: 600, margin: '0 auto' }}>
          <Card 
            style={{ 
              borderRadius: 16,
              boxShadow: '0 2px 12px rgba(0,0,0,0.08)'
            }}
            styles={{
              body: { padding: 24 }
            }}
          >
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              <div style={{ textAlign: 'center' }}>
                <ScanOutlined style={{ fontSize: 48, color: '#1890ff', marginBottom: 16 }} />
                <Title level={4} style={{ marginBottom: 8 }}>AI Face Detection</Title>
                <Text type="secondary">
                  Position your face in the frame for automatic detection and analysis
                </Text>
              </div>

              {!capturedImage ? (
                <FaceMeshCapture
                  onCapture={handleCapture}
                  onFaceDetected={handleFaceDetected}
                />
              ) : (
                <>
                  <div style={{ 
                    textAlign: 'center',
                    padding: '16px 0'
                  }}>
                    <img 
                      src={URL.createObjectURL(capturedImage)}
                      alt="Captured Face"
                      style={{ 
                        maxWidth: '100%', 
                        maxHeight: 300,
                        borderRadius: 12,
                        border: '2px solid #52c41a',
                        objectFit: 'cover'
                      }}
                    />
                    <div style={{ marginTop: 12 }}>
                      <Text type="success" strong>✓ Face Captured Successfully</Text>
                    </div>
                  </div>

                  <Form
                    form={form}
                    layout="vertical"
                    onFinish={onFinish}
                    requiredMark="optional"
                  >
                    <Form.Item
                      label={<Text strong>How does your skin feel?</Text>}
                      name="skinFeel"
                      rules={[{ required: true, message: 'Please select an option' }]}
                    >
                      <Select 
                        size="large" 
                        placeholder="Select..."
                        style={{ borderRadius: 8 }}
                      >
                        <Select.Option value="oily">Oily</Select.Option>
                        <Select.Option value="dry">Dry</Select.Option>
                        <Select.Option value="combination">Combination</Select.Option>
                        <Select.Option value="normal">Normal</Select.Option>
                      </Select>
                    </Form.Item>

                    <Form.Item
                      label={<Text strong>Current skincare routine</Text>}
                      name="routine"
                      rules={[{ required: true, message: 'Please select an option' }]}
                    >
                      <Select 
                        size="large" 
                        placeholder="Select..."
                        style={{ borderRadius: 8 }}
                      >
                        <Select.Option value="none">None</Select.Option>
                        <Select.Option value="basic">Basic (cleanser + moisturizer)</Select.Option>
                        <Select.Option value="moderate">Moderate (3-5 products)</Select.Option>
                        <Select.Option value="extensive">Extensive (6+ products)</Select.Option>
                      </Select>
                    </Form.Item>

                    <Form.Item
                      label={<Text strong>Skin concerns</Text>}
                      name="concerns"
                    >
                      <Checkbox.Group style={{ width: '100%' }}>
                        <Space direction="vertical" style={{ width: '100%' }}>
                          <Checkbox value="acne" style={{ fontSize: 15 }}>Acne</Checkbox>
                          <Checkbox value="wrinkles" style={{ fontSize: 15 }}>Wrinkles</Checkbox>
                          <Checkbox value="dark_spots" style={{ fontSize: 15 }}>Dark Spots</Checkbox>
                          <Checkbox value="redness" style={{ fontSize: 15 }}>Redness</Checkbox>
                          <Checkbox value="dryness" style={{ fontSize: 15 }}>Dryness</Checkbox>
                          <Checkbox value="oiliness" style={{ fontSize: 15 }}>Oiliness</Checkbox>
                        </Space>
                      </Checkbox.Group>
                    </Form.Item>

                    <Space direction="vertical" style={{ width: '100%' }} size="middle">
                      <Button 
                        type="primary" 
                        htmlType="submit" 
                        size="large"
                        block
                        loading={loading}
                        style={{
                          height: 56,
                          fontSize: 16,
                          fontWeight: 600,
                          borderRadius: 12
                        }}
                      >
                        {loading ? <Spin /> : 'Analyze My Skin'}
                      </Button>

                      <Button 
                        size="large"
                        block
                        onClick={() => {
                          setCapturedImage(null);
                          setLandmarks(null);
                          setFaceDetected(false);
                          form.resetFields();
                        }}
                        style={{
                          height: 48,
                          borderRadius: 12
                        }}
                      >
                        Retake Photo
                      </Button>
                    </Space>
                  </Form>
                </>
              )}

              {!capturedImage && (
                <div className="instructions">
                  <Title level={5}>Tips for Best Results:</Title>
                  <ul style={{ paddingLeft: 20, margin: '8px 0' }}>
                    <li>Ensure good lighting on your face</li>
                    <li>Remove glasses if possible</li>
                    <li>Look directly at the camera</li>
                    <li>Keep your face centered in the frame</li>
                    <li>Wait for the green border (face detected)</li>
                  </ul>
                </div>
              )}
            </Space>
          </Card>
        </div>
      </Content>
    </Layout>
  );
}
