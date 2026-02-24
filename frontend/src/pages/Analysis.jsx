import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import { Layout, Card, Button, Form, Select, Checkbox, Typography, Space, App, Spin, Tabs } from 'antd';
import { CameraOutlined, ScanOutlined } from '@ant-design/icons';
import { Capacitor } from '@capacitor/core';
import { takePicture } from '../services/camera';
import { analyzeImage } from '../services/api';
import { setCurrentAnalysis, addToHistory } from '../store/slices/analysisSlice';
import AppHeader from '../components/AppHeader';
import WebCamera from '../components/WebCamera';
import FaceMeshAnalysis from '../components/FaceMeshAnalysis';

const { Content } = Layout;
const { Title, Text } = Typography;

export default function Analysis() {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [imageData, setImageData] = useState(null);
  const [showCamera, setShowCamera] = useState(false);
  const [captureMode, setCaptureMode] = useState('standard'); // 'standard' or 'facemesh'
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { message } = App.useApp();

  const handleTakePhoto = async () => {
    // Use custom web camera for web platform
    if (Capacitor.getPlatform() === 'web') {
      setShowCamera(true);
      return;
    }

    // Use native camera for mobile
    try {
      const base64 = await takePicture();
      setImageData(base64);
      message.success('Photo captured!');
    } catch (error) {
      // Don't show error if user just cancelled
      if (error.message && !error.message.includes('cancel')) {
        message.error('Failed to capture photo');
      }
    }
  };

  const handleWebCameraCapture = (base64) => {
    setImageData(base64);
    setShowCamera(false);
    message.success('Photo captured!');
  };

  const handleWebCameraCancel = () => {
    setShowCamera(false);
  };

  const onFinish = async (values) => {
    if (!imageData) {
      message.warning('Please capture a photo first');
      return;
    }

    setLoading(true);
    try {
      const questionnaire = {
        skin_feel: values.skinFeel,
        routine: values.routine,
        concerns: values.concerns || [],
      };

      const response = await analyzeImage(imageData, questionnaire);
      
      dispatch(setCurrentAnalysis(response.data));
      dispatch(addToHistory(response.data));
      
      navigate('/results');
    } catch (error) {
      message.error(error.response?.data?.error?.message || 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout style={{ minHeight: '100vh', background: '#f5f5f5' }}>
      <AppHeader title="Skin Analysis" showBack />

      <WebCamera
        visible={showCamera}
        onCapture={handleWebCameraCapture}
        onCancel={handleWebCameraCancel}
      />

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
            <Tabs
              activeKey={captureMode}
              onChange={setCaptureMode}
              items={[
                {
                  key: 'standard',
                  label: (
                    <span>
                      <CameraOutlined /> Standard Camera
                    </span>
                  ),
                  children: (
                    <Space direction="vertical" size="large" style={{ width: '100%' }}>
                      <div style={{ textAlign: 'center' }}>
                        <Title level={4} style={{ marginBottom: 8 }}>Capture Your Skin</Title>
                        <Text type="secondary">
                          Take a clear photo of your face in good lighting
                        </Text>
                      </div>

                      {imageData && (
                        <div style={{ 
                          textAlign: 'center',
                          padding: '16px 0'
                        }}>
                          <img 
                            src={`data:image/jpeg;base64,${imageData}`}
                            alt="Captured"
                            style={{ 
                              maxWidth: '100%', 
                              maxHeight: 300,
                              borderRadius: 12,
                              border: '2px solid #e5e7eb',
                              objectFit: 'cover'
                            }}
                          />
                        </div>
                      )}

                      <Button
                        icon={<CameraOutlined />}
                        onClick={handleTakePhoto}
                        size="large"
                        block
                        style={{
                          height: 56,
                          fontSize: 16,
                          fontWeight: 500,
                          borderRadius: 12
                        }}
                      >
                        Take Photo
                      </Button>

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

                        <Form.Item style={{ marginBottom: 0 }}>
                          <Button 
                            type="primary" 
                            htmlType="submit" 
                            size="large"
                            block
                            loading={loading}
                            disabled={!imageData}
                            style={{
                              height: 56,
                              fontSize: 16,
                              fontWeight: 600,
                              borderRadius: 12
                            }}
                          >
                            {loading ? <Spin /> : 'Analyze My Skin'}
                          </Button>
                        </Form.Item>
                      </Form>
                    </Space>
                  ),
                },
                {
                  key: 'facemesh',
                  label: (
                    <span>
                      <ScanOutlined /> AI Face Detection
                    </span>
                  ),
                  children: <FaceMeshAnalysis />,
                },
              ]}
            />
          </Card>
        </div>
      </Content>
    </Layout>
  );
}
