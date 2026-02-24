import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import { Layout, Card, Button, Form, Select, Checkbox, Typography, Space, App, Spin } from 'antd';
import { CameraOutlined, PictureOutlined, ArrowLeftOutlined } from '@ant-design/icons';
import { takePicture, pickImage } from '../services/camera';
import { analyzeImage } from '../services/api';
import { setCurrentAnalysis, addToHistory } from '../store/slices/analysisSlice';

const { Header, Content } = Layout;
const { Title, Text } = Typography;

export default function Analysis() {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [imageData, setImageData] = useState(null);
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { message } = App.useApp();

  const handleTakePhoto = async () => {
    try {
      const base64 = await takePicture();
      setImageData(base64);
      message.success('Photo captured!');
    } catch (error) {
      message.error('Failed to capture photo');
    }
  };

  const handlePickImage = async () => {
    try {
      const base64 = await pickImage();
      setImageData(base64);
      message.success('Image selected!');
    } catch (error) {
      message.error('Failed to select image');
    }
  };

  const onFinish = async (values) => {
    if (!imageData) {
      message.warning('Please capture or select an image first');
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
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ 
        background: '#fff', 
        padding: '0 24px',
        display: 'flex',
        alignItems: 'center',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
      }}>
        <Button 
          icon={<ArrowLeftOutlined />} 
          onClick={() => navigate('/')}
          type="text"
        />
        <Title level={3} style={{ margin: '0 0 0 16px' }}>Skin Analysis</Title>
      </Header>

      <Content style={{ padding: '24px' }}>
        <div style={{ maxWidth: 600, margin: '0 auto' }}>
          <Card>
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              <div style={{ textAlign: 'center' }}>
                <Title level={4}>Capture Your Skin</Title>
                <Text type="secondary">
                  Take a clear photo of your face in good lighting
                </Text>
              </div>

              {imageData && (
                <div style={{ textAlign: 'center' }}>
                  <img 
                    src={`data:image/jpeg;base64,${imageData}`}
                    alt="Captured"
                    style={{ 
                      maxWidth: '100%', 
                      maxHeight: 300,
                      borderRadius: 8,
                      border: '2px solid #e5e7eb'
                    }}
                  />
                </div>
              )}

              <Space style={{ width: '100%' }}>
                <Button
                  icon={<CameraOutlined />}
                  onClick={handleTakePhoto}
                  size="large"
                  block
                >
                  Take Photo
                </Button>
                <Button
                  icon={<PictureOutlined />}
                  onClick={handlePickImage}
                  size="large"
                  block
                >
                  Choose from Gallery
                </Button>
              </Space>

              <Form
                form={form}
                layout="vertical"
                onFinish={onFinish}
              >
                <Form.Item
                  label="How does your skin feel?"
                  name="skinFeel"
                  rules={[{ required: true, message: 'Please select an option' }]}
                >
                  <Select size="large" placeholder="Select...">
                    <Select.Option value="oily">Oily</Select.Option>
                    <Select.Option value="dry">Dry</Select.Option>
                    <Select.Option value="combination">Combination</Select.Option>
                    <Select.Option value="normal">Normal</Select.Option>
                  </Select>
                </Form.Item>

                <Form.Item
                  label="Current skincare routine"
                  name="routine"
                  rules={[{ required: true, message: 'Please select an option' }]}
                >
                  <Select size="large" placeholder="Select...">
                    <Select.Option value="none">None</Select.Option>
                    <Select.Option value="basic">Basic (cleanser + moisturizer)</Select.Option>
                    <Select.Option value="moderate">Moderate (3-5 products)</Select.Option>
                    <Select.Option value="extensive">Extensive (6+ products)</Select.Option>
                  </Select>
                </Form.Item>

                <Form.Item
                  label="Skin concerns"
                  name="concerns"
                >
                  <Checkbox.Group>
                    <Space direction="vertical">
                      <Checkbox value="acne">Acne</Checkbox>
                      <Checkbox value="wrinkles">Wrinkles</Checkbox>
                      <Checkbox value="dark_spots">Dark Spots</Checkbox>
                      <Checkbox value="redness">Redness</Checkbox>
                      <Checkbox value="dryness">Dryness</Checkbox>
                      <Checkbox value="oiliness">Oiliness</Checkbox>
                    </Space>
                  </Checkbox.Group>
                </Form.Item>

                <Form.Item>
                  <Button 
                    type="primary" 
                    htmlType="submit" 
                    size="large"
                    block
                    loading={loading}
                    disabled={!imageData}
                  >
                    {loading ? <Spin /> : 'Analyze My Skin'}
                  </Button>
                </Form.Item>
              </Form>
            </Space>
          </Card>
        </div>
      </Content>
    </Layout>
  );
}
