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

/** Convert a Blob to a base64 string (without the data: prefix). */
const blobToBase64 = (blob) =>
  new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(blob);
    reader.onloadend = () => resolve(reader.result.split(',')[1]);
    reader.onerror   = reject;
  });

export default function Analysis() {
  const [form] = Form.useForm();
  const [loading, setLoading]           = useState(false);
  const [capturedImage, setCapturedImage] = useState(null);
  const [allCaptures, setAllCaptures]   = useState([]);
  const [landmarks, setLandmarks]       = useState(null);
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { message } = App.useApp();

  const handleCapture = (mainBlob, captures = []) => {
    setCapturedImage(mainBlob);
    setAllCaptures(captures);
    message.success(`${captures.length} pose${captures.length !== 1 ? 's' : ''} captured! Complete the questionnaire below.`);
  };

  /** Called on every frame — keeps the latest landmarks for the analysis request. */
  const handleFaceDetected = (detectedLandmarks) => {
    setLandmarks(detectedLandmarks);
  };

  const onFinish = async (values) => {
    if (!capturedImage || !landmarks) {
      message.warning('Please capture your face first');
      return;
    }
    if (loading) return;

    setLoading(true);
    try {
      const base64Image = await blobToBase64(capturedImage);

      const questionnaire = {
        skin_feel: values.skinFeel,
        routine:   values.routine,
        concerns:  values.concerns || [],
      };

      const response = await api.post('/analyze', {
        image_base64: base64Image,
        questionnaire,
        landmarks: landmarks.map(({ x, y, z }) => ({ x, y, z })),
      });

      dispatch(setCurrentAnalysis(response.data));
      dispatch(addToHistory(response.data));

      const captures = allCaptures.length > 0 ? allCaptures : [{ blob: capturedImage }];

      const trainingPayload = {
        skin_type:  response.data.profile.skin_type,
        conditions: response.data.profile.conditions || [],
      };

      await Promise.allSettled(
        captures.map(async (capture) => {
          try {
            const img = await blobToBase64(capture.blob);
            await api.post('/training/submit', { image_base64: img, ...trainingPayload });
          } catch (e) {
            console.warn(`Training submit failed for phase "${capture.phase ?? 'main'}":`, e);
          }
        })
      );

      navigate('/results');
    } catch (error) {
      console.error('Analysis failed:', error);
      message.error(error.response?.data?.error?.message || 'Analysis failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout style={{ minHeight: '100vh', background: 'var(--background)' }}>
      <AppHeader title="AI Skin Analysis" showBack />

      <Content style={{ padding: '16px' }}>
        <div style={{ maxWidth: 600, margin: '0 auto' }}>
          <Card
            style={{
              borderRadius: 12,
              boxShadow: 'var(--card-shadow)',
              border: '1px solid var(--border)',
              background: 'var(--card)',
            }}
            styles={{ body: { padding: 24 } }}
          >
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              <div style={{ textAlign: 'center' }}>
                <ScanOutlined style={{ fontSize: 48, color: 'var(--primary)', marginBottom: 16 }} />
                <Title level={4} style={{ marginBottom: 8, color: 'var(--card-foreground)' }}>
                  AI Face Detection
                </Title>
                <Text style={{ color: 'var(--muted-foreground)' }}>
                  Follow the on-screen prompts to capture 5 poses for a complete skin analysis.
                  The system will auto-capture each pose when you hold it steady.
                </Text>
              </div>

              {/* ── Capture phase ── */}
              {!capturedImage ? (
                <FaceMeshCapture
                  onCapture={handleCapture}
                  onFaceDetected={handleFaceDetected}
                />
              ) : (
                <>
                  {/* Preview + summary */}
                  <div style={{ textAlign: 'center', padding: '8px 0' }}>
                    <img
                      src={URL.createObjectURL(capturedImage)}
                      alt="Captured Face"
                      style={{
                        maxWidth: '100%',
                        maxHeight: 260,
                        borderRadius: 12,
                        border: '2px solid #10B981',
                        objectFit: 'contain',
                        background: 'var(--muted)',
                      }}
                    />
                    <div style={{ marginTop: 10 }}>
                      <Text type="success" strong>
                        ✓ {allCaptures.length > 0 ? `${allCaptures.length} poses` : 'Face'} captured
                      </Text>
                    </div>
                    {allCaptures.length > 1 && (
                      <div style={{ display: 'flex', justifyContent: 'center', gap: 6, marginTop: 8, flexWrap: 'wrap' }}>
                        {allCaptures.map((c) => (
                          <span
                            key={c.phase}
                            style={{
                              fontSize: 11,
                              padding: '2px 8px',
                              borderRadius: 10,
                              background: 'var(--muted)',
                              border: '1px solid var(--border)',
                              color: 'var(--muted-foreground)',
                            }}
                          >
                            {c.phase}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* ── Questionnaire ── */}
                  <Form
                    form={form}
                    layout="vertical"
                    onFinish={onFinish}
                    requiredMark="optional"
                  >
                    <Form.Item
                      label={<Text strong style={{ color: 'var(--card-foreground)' }}>How does your skin feel?</Text>}
                      name="skinFeel"
                      rules={[{ required: true, message: 'Please select an option' }]}
                    >
                      <Select size="large" placeholder="Select…">
                        <Select.Option value="oily">Oily</Select.Option>
                        <Select.Option value="dry">Dry</Select.Option>
                        <Select.Option value="combination">Combination</Select.Option>
                        <Select.Option value="normal">Normal</Select.Option>
                      </Select>
                    </Form.Item>

                    <Form.Item
                      label={<Text strong style={{ color: 'var(--card-foreground)' }}>Current skincare routine</Text>}
                      name="routine"
                      rules={[{ required: true, message: 'Please select an option' }]}
                    >
                      <Select size="large" placeholder="Select…">
                        <Select.Option value="none">None</Select.Option>
                        <Select.Option value="basic">Basic (cleanser + moisturiser)</Select.Option>
                        <Select.Option value="moderate">Moderate (3–5 products)</Select.Option>
                        <Select.Option value="extensive">Extensive (6+ products)</Select.Option>
                      </Select>
                    </Form.Item>

                    <Form.Item
                      label={<Text strong style={{ color: 'var(--card-foreground)' }}>Skin concerns</Text>}
                      name="concerns"
                    >
                      <Checkbox.Group style={{ width: '100%' }}>
                        <Space direction="vertical" style={{ width: '100%' }}>
                          <Checkbox value="acne"       style={{ fontSize: 15 }}>Acne</Checkbox>
                          <Checkbox value="wrinkles"   style={{ fontSize: 15 }}>Wrinkles</Checkbox>
                          <Checkbox value="dark_spots" style={{ fontSize: 15 }}>Dark Spots</Checkbox>
                          <Checkbox value="redness"    style={{ fontSize: 15 }}>Redness</Checkbox>
                          <Checkbox value="dryness"    style={{ fontSize: 15 }}>Dryness</Checkbox>
                          <Checkbox value="oiliness"   style={{ fontSize: 15 }}>Oiliness</Checkbox>
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
                        style={{ height: 56, fontSize: 16, fontWeight: 600 }}
                      >
                        {loading ? 'Analysing…' : 'Analyse My Skin'}
                      </Button>

                      <Button
                        size="large"
                        block
                        onClick={() => {
                          setCapturedImage(null);
                          setAllCaptures([]);
                          setLandmarks(null);
                          form.resetFields();
                        }}
                        style={{ height: 48 }}
                      >
                        Retake Photos
                      </Button>
                    </Space>
                  </Form>
                </>
              )}

              {!capturedImage && (
                <div style={{
                  padding: '16px',
                  borderRadius: 8,
                  background: 'var(--muted)',
                  border: '1px solid var(--border)',
                }}>
                  <Title level={5} style={{ color: 'var(--card-foreground)', marginBottom: 8 }}>
                    Tips for Best Results:
                  </Title>
                  <ul style={{ paddingLeft: 20, margin: 0, color: 'var(--muted-foreground)', lineHeight: 1.8 }}>
                    <li>Good even lighting — avoid harsh shadows</li>
                    <li>Remove glasses if possible</li>
                    <li>Hold each pose steady until the ring completes</li>
                    <li>Tilt slowly — the guide arrow shows the target direction</li>
                    <li>Use <strong>Capture Now</strong> or <strong>Skip</strong> if stuck on a pose</li>
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
