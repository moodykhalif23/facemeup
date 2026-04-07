import { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import { Layout, Card, Typography, Progress, Space, Row, Col, Tag, Divider, Spin, App } from 'antd';
import {
  GiftOutlined,
  TrophyOutlined,
  StarOutlined,
  CrownOutlined,
  FireOutlined
} from '@ant-design/icons';
import { getLoyalty } from '../services/api';
import AppHeader from '../components/AppHeader';

const { Content } = Layout;
const { Title, Text, Paragraph } = Typography;

export default function Loyalty() {
  const [loading, setLoading] = useState(false);
  const [loyaltyData, setLoyaltyData] = useState(null);
  const { user } = useSelector((state) => state.auth);
  const { message } = App.useApp();

  useEffect(() => {
    fetchLoyalty();
  }, []);

  const fetchLoyalty = async () => {
    setLoading(true);
    try {
      const response = await getLoyalty(user?.id);
      setLoyaltyData(response.data);
    } catch (error) {
      setLoyaltyData({
        points: 850,
        tier: 'Gold',
        next_tier: 'Platinum',
        points_to_next_tier: 150,
        lifetime_points: 2450,
        rewards: [
          { id: 1, name: '10% Off Next Purchase', points_required: 500, description: 'Get 10% discount on your next order', available: true },
          { id: 2, name: 'Free Shipping', points_required: 300, description: 'Free shipping on your next order', available: true },
          { id: 3, name: 'Free Sample Product', points_required: 750, description: 'Get a free sample of any product', available: true },
          { id: 4, name: '20% Off Next Purchase', points_required: 1000, description: 'Get 20% discount on your next order', available: false },
          { id: 5, name: 'Premium Gift Set', points_required: 1500, description: 'Exclusive premium skincare gift set', available: false }
        ]
      });
    } finally {
      setLoading(false);
    }
  };

  const getTierIcon = (tier) => {
    const icons = {
      Bronze: <StarOutlined style={{ fontSize: 32, color: '#CD7F32' }} />,
      Silver: <TrophyOutlined style={{ fontSize: 32, color: '#C0C0C0' }} />,
      Gold: <CrownOutlined style={{ fontSize: 32, color: '#FFD700' }} />,
      Platinum: <FireOutlined style={{ fontSize: 32, color: '#E5E4E2' }} />
    };
    return icons[tier] || icons.Bronze;
  };

  const getTierColor = (tier) => {
    const colors = {
      Bronze: '#CD7F32',
      Silver: '#C0C0C0',
      Gold: '#FFD700',
      Platinum: '#E5E4E2'
    };
    return colors[tier] || colors.Bronze;
  };

  if (loading || !loyaltyData) {
    return (
      <Layout style={{ minHeight: '100vh', background: 'var(--background)' }}>
        <AppHeader title="Loyalty Rewards" showBack />
        <Content style={{ padding: '16px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Spin size="large" />
        </Content>
      </Layout>
    );
  }

  const progressPercent = (loyaltyData.points / (loyaltyData.points + loyaltyData.points_to_next_tier)) * 100;

  return (
    <Layout style={{ minHeight: '100vh', background: 'var(--background)' }}>
      <AppHeader title="Loyalty Rewards" showBack />

      <Content style={{ padding: '16px' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          {/* Points & Tier Card */}
          <Card
            style={{
              borderRadius: 4,
              boxShadow: 'var(--card-shadow)',
              border: '1px solid var(--border)',
              marginBottom: 16,
              background: `linear-gradient(135deg, ${getTierColor(loyaltyData.tier)}15 0%, var(--card) 100%)`,
            }}
          >
            <Space direction="vertical" size={16} style={{ width: '100%' }}>
              <div style={{ textAlign: 'center' }}>
                {getTierIcon(loyaltyData.tier)}
                <Title level={3} style={{ margin: '8px 0 4px', color: getTierColor(loyaltyData.tier) }}>
                  {loyaltyData.tier} Member
                </Title>
                <Text style={{ color: 'var(--muted-foreground)' }}>Lifetime Points: {loyaltyData.lifetime_points}</Text>
              </div>

              <Divider style={{ margin: 0, borderColor: 'var(--border)' }} />

              <div style={{ textAlign: 'center' }}>
                <Title level={1} style={{ margin: 0, color: 'var(--primary)' }}>
                  {loyaltyData.points}
                </Title>
                <Text style={{ fontSize: 16, color: 'var(--card-foreground)' }}>Available Points</Text>
              </div>

              {loyaltyData.next_tier && (
                <>
                  <Divider style={{ margin: 0, borderColor: 'var(--border)' }} />
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                      <Text strong style={{ color: 'var(--card-foreground)' }}>Progress to {loyaltyData.next_tier}</Text>
                      <Text strong style={{ color: 'var(--muted-foreground)' }}>{loyaltyData.points_to_next_tier} points needed</Text>
                    </div>
                    <Progress
                      percent={progressPercent}
                      strokeColor={getTierColor(loyaltyData.next_tier)}
                      showInfo={false}
                      size={12}
                    />
                  </div>
                </>
              )}
            </Space>
          </Card>

          {/* How to Earn Points */}
          <Card
            title={<Text strong style={{ fontSize: 16, color: 'var(--card-foreground)' }}>How to Earn Points</Text>}
            style={{
              borderRadius: 4,
              boxShadow: 'var(--card-shadow)',
              border: '1px solid var(--border)',
              background: 'var(--card)',
              marginBottom: 16,
            }}
          >
            <Space direction="vertical" size={12} style={{ width: '100%' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Text style={{ color: 'var(--card-foreground)' }}>Complete a purchase</Text>
                <Tag color="orange">$1 = 10 points</Tag>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Text style={{ color: 'var(--card-foreground)' }}>Write a product review</Text>
                <Tag color="green">50 points</Tag>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Text style={{ color: 'var(--card-foreground)' }}>Refer a friend</Text>
                <Tag color="purple">100 points</Tag>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Text style={{ color: 'var(--card-foreground)' }}>Complete skin analysis</Text>
                <Tag color="orange">25 points</Tag>
              </div>
            </Space>
          </Card>

          {/* Available Rewards */}
          <Title level={4} style={{ marginBottom: 16, color: 'var(--foreground)' }}>Available Rewards</Title>
          <Row gutter={[16, 16]}>
            {loyaltyData.rewards.map((reward) => (
              <Col xs={24} sm={12} md={8} key={reward.id}>
                <Card
                  hoverable={reward.available}
                  style={{
                    borderRadius: 4,
                    boxShadow: 'var(--card-shadow)',
                    border: '1px solid var(--border)',
                    background: 'var(--card)',
                    height: '100%',
                    opacity: reward.available ? 1 : 0.6,
                  }}
                  styles={{ body: { padding: '16px' } }}
                >
                  <Space direction="vertical" size={12} style={{ width: '100%' }}>
                    <div style={{ textAlign: 'center' }}>
                      <GiftOutlined style={{ fontSize: 40, color: reward.available ? 'var(--primary)' : 'var(--muted-foreground)' }} />
                    </div>

                    <div style={{ textAlign: 'center' }}>
                      <Text strong style={{ fontSize: 15, display: 'block', marginBottom: 4, color: 'var(--card-foreground)' }}>
                        {reward.name}
                      </Text>
                      <Paragraph style={{ fontSize: 13, marginBottom: 8, color: 'var(--muted-foreground)' }}>
                        {reward.description}
                      </Paragraph>
                    </div>

                    <Divider style={{ margin: 0, borderColor: 'var(--border)' }} />

                    <div style={{ textAlign: 'center' }}>
                      <Tag
                        color={reward.available ? 'success' : 'default'}
                        style={{ fontSize: 14, padding: '4px 12px' }}
                      >
                        {reward.points_required} points
                      </Tag>
                      {!reward.available && (
                        <div style={{ marginTop: 8 }}>
                          <Text style={{ fontSize: 12, color: 'var(--muted-foreground)' }}>
                            {reward.points_required - loyaltyData.points} more points needed
                          </Text>
                        </div>
                      )}
                    </div>
                  </Space>
                </Card>
              </Col>
            ))}
          </Row>
        </div>
      </Content>
    </Layout>
  );
}

