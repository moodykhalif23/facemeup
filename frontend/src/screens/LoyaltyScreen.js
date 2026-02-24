import { useState, useEffect } from "react";
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Share } from "react-native";
import { Card, Button, WhiteSpace, WingBlank, ActivityIndicator, Toast, List, Modal } from '@ant-design/react-native';
import { MaterialIcons, FontAwesome5 } from '@expo/vector-icons';

export default function LoyaltyScreen({ token, userId }) {
  const [loyaltyData, setLoyaltyData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [redeemModalVisible, setRedeemModalVisible] = useState(false);

  // Mock data - in production, this would come from API
  const mockLoyaltyData = {
    points: 2450,
    tier: 'Gold',
    referralCode: 'SKIN2024',
    referralCount: 5,
    transactions: [
      { id: 1, type: 'earned', amount: 500, description: 'Purchase - Hydrating Serum', date: '2024-02-20' },
      { id: 2, type: 'earned', amount: 100, description: 'Referral Bonus', date: '2024-02-18' },
      { id: 3, type: 'redeemed', amount: -200, description: 'Discount Applied', date: '2024-02-15' },
      { id: 4, type: 'earned', amount: 750, description: 'Purchase - Vitamin C Cream', date: '2024-02-10' },
      { id: 5, type: 'earned', amount: 50, description: 'Profile Completion Bonus', date: '2024-02-05' },
    ],
    rewards: [
      { id: 1, name: '10% Off Next Purchase', points: 500, description: 'Valid for 30 days' },
      { id: 2, name: 'Free Shipping', points: 300, description: 'On orders over KES 2000' },
      { id: 3, name: '20% Off Premium Products', points: 1000, description: 'Valid for 60 days' },
      { id: 4, name: 'Free Sample Pack', points: 750, description: '3 product samples' },
    ],
  };

  const loadLoyaltyData = async () => {
    setLoading(true);
    try {
      // Simulate API call
      setTimeout(() => {
        setLoyaltyData(mockLoyaltyData);
        setLoading(false);
        Toast.success("Loyalty data loaded!", 1);
      }, 1000);
    } catch (err) {
      Toast.fail("Failed to load loyalty data", 2);
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLoyaltyData();
  }, []);

  const handleShareReferral = async () => {
    try {
      await Share.share({
        message: `Join SkinCare AI and get personalized skincare recommendations! Use my referral code: ${loyaltyData.referralCode}`,
      });
    } catch (error) {
      Toast.fail("Failed to share", 1);
    }
  };

  const handleRedeem = (reward) => {
    if (loyaltyData.points >= reward.points) {
      Modal.alert(
        'Redeem Reward',
        `Redeem ${reward.name} for ${reward.points} points?`,
        [
          { text: 'Cancel', style: 'cancel' },
          {
            text: 'Redeem',
            onPress: () => {
              Toast.success(`${reward.name} redeemed!`, 2);
              setLoyaltyData({
                ...loyaltyData,
                points: loyaltyData.points - reward.points,
              });
            },
          },
        ]
      );
    } else {
      Toast.fail(`You need ${reward.points - loyaltyData.points} more points`, 2);
    }
  };

  const getTierColor = (tier) => {
    switch (tier) {
      case 'Gold': return '#F59E0B';
      case 'Silver': return '#9CA3AF';
      case 'Bronze': return '#CD7F32';
      default: return '#3B82F6';
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#3B82F6" />
        <WhiteSpace size="lg" />
        <Text style={styles.loadingText}>Loading loyalty data...</Text>
      </View>
    );
  }

  if (!loyaltyData) {
    return (
      <View style={styles.emptyContainer}>
        <Text style={styles.emptyIcon}>🎁</Text>
        <Text style={styles.emptyTitle}>No Loyalty Data</Text>
        <Button type="primary" onPress={loadLoyaltyData}>
          Load Data
        </Button>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <WingBlank size="lg">
          {/* Points Balance Card */}
          <Card>
            <Card.Body>
              <View style={styles.balanceCard}>
                <View style={styles.balanceHeader}>
                  <Text style={styles.balanceLabel}>Your Points</Text>
                  <View style={[styles.tierBadge, { backgroundColor: getTierColor(loyaltyData.tier) }]}>
                    <MaterialIcons name="star" size={16} color="#FFFFFF" />
                    <Text style={styles.tierText}>{loyaltyData.tier}</Text>
                  </View>
                </View>
                
                <WhiteSpace size="md" />
                
                <Text style={styles.pointsAmount}>{loyaltyData.points.toLocaleString()}</Text>
                <Text style={styles.pointsLabel}>Loyalty Points</Text>
                
                <WhiteSpace size="lg" />
                
                <View style={styles.statsRow}>
                  <View style={styles.statItem}>
                    <MaterialIcons name="people" size={24} color="#3B82F6" />
                    <Text style={styles.statValue}>{loyaltyData.referralCount}</Text>
                    <Text style={styles.statLabel}>Referrals</Text>
                  </View>
                  
                  <View style={styles.statDivider} />
                  
                  <View style={styles.statItem}>
                    <MaterialIcons name="card-giftcard" size={24} color="#10B981" />
                    <Text style={styles.statValue}>{loyaltyData.rewards.length}</Text>
                    <Text style={styles.statLabel}>Rewards</Text>
                  </View>
                </View>
              </View>
            </Card.Body>
          </Card>

          <WhiteSpace size="lg" />

          {/* Referral Card */}
          <Card>
            <Card.Header
              title={
                <View style={styles.cardHeader}>
                  <MaterialIcons name="share" size={20} color="#3B82F6" />
                  <Text style={styles.cardTitle}>Refer & Earn</Text>
                </View>
              }
            />
            <Card.Body>
              <Text style={styles.referralDescription}>
                Share your referral code and earn 100 points for each friend who signs up!
              </Text>
              
              <WhiteSpace size="md" />
              
              <View style={styles.referralCodeContainer}>
                <Text style={styles.referralCodeLabel}>Your Code</Text>
                <Text style={styles.referralCode}>{loyaltyData.referralCode}</Text>
              </View>
              
              <WhiteSpace size="md" />
              
              <Button
                type="primary"
                onPress={handleShareReferral}
                style={styles.shareButton}
              >
                <MaterialIcons name="share" size={16} color="#FFFFFF" />
                <Text style={styles.shareButtonText}> Share Code</Text>
              </Button>
            </Card.Body>
          </Card>

          <WhiteSpace size="lg" />

          {/* Available Rewards */}
          <Card>
            <Card.Header
              title={
                <View style={styles.cardHeader}>
                  <MaterialIcons name="redeem" size={20} color="#10B981" />
                  <Text style={styles.cardTitle}>Available Rewards</Text>
                </View>
              }
            />
            <Card.Body>
              {loyaltyData.rewards.map((reward) => (
                <View key={reward.id}>
                  <View style={styles.rewardItem}>
                    <View style={styles.rewardInfo}>
                      <Text style={styles.rewardName}>{reward.name}</Text>
                      <Text style={styles.rewardDescription}>{reward.description}</Text>
                      <View style={styles.rewardPoints}>
                        <MaterialIcons name="stars" size={16} color="#F59E0B" />
                        <Text style={styles.rewardPointsText}>{reward.points} points</Text>
                      </View>
                    </View>
                    
                    <TouchableOpacity
                      style={[
                        styles.redeemButton,
                        loyaltyData.points < reward.points && styles.redeemButtonDisabled,
                      ]}
                      onPress={() => handleRedeem(reward)}
                      disabled={loyaltyData.points < reward.points}
                    >
                      <Text style={[
                        styles.redeemButtonText,
                        loyaltyData.points < reward.points && styles.redeemButtonTextDisabled,
                      ]}>
                        Redeem
                      </Text>
                    </TouchableOpacity>
                  </View>
                  <WhiteSpace size="md" />
                </View>
              ))}
            </Card.Body>
          </Card>

          <WhiteSpace size="lg" />

          {/* Transaction History */}
          <Card>
            <Card.Header
              title={
                <View style={styles.cardHeader}>
                  <MaterialIcons name="history" size={20} color="#6B7280" />
                  <Text style={styles.cardTitle}>Transaction History</Text>
                </View>
              }
            />
            <Card.Body>
              <List>
                {loyaltyData.transactions.map((transaction) => (
                  <View key={transaction.id}>
                    <View style={styles.transactionItem}>
                      <View style={[
                        styles.transactionIcon,
                        { backgroundColor: transaction.type === 'earned' ? '#D1FAE5' : '#FEE2E2' }
                      ]}>
                        <MaterialIcons
                          name={transaction.type === 'earned' ? 'add' : 'remove'}
                          size={20}
                          color={transaction.type === 'earned' ? '#10B981' : '#EF4444'}
                        />
                      </View>
                      
                      <View style={styles.transactionInfo}>
                        <Text style={styles.transactionDescription}>{transaction.description}</Text>
                        <Text style={styles.transactionDate}>
                          {new Date(transaction.date).toLocaleDateString('en-US', {
                            month: 'short',
                            day: 'numeric',
                            year: 'numeric',
                          })}
                        </Text>
                      </View>
                      
                      <Text style={[
                        styles.transactionAmount,
                        { color: transaction.type === 'earned' ? '#10B981' : '#EF4444' }
                      ]}>
                        {transaction.type === 'earned' ? '+' : ''}{transaction.amount}
                      </Text>
                    </View>
                    <WhiteSpace size="sm" />
                  </View>
                ))}
              </List>
            </Card.Body>
          </Card>

          <WhiteSpace size="lg" />

          {/* How to Earn Points */}
          <Card>
            <Card.Header
              title={
                <View style={styles.cardHeader}>
                  <MaterialIcons name="info" size={20} color="#3B82F6" />
                  <Text style={styles.cardTitle}>How to Earn Points</Text>
                </View>
              }
            />
            <Card.Body>
              <View style={styles.earnRule}>
                <MaterialIcons name="shopping-bag" size={20} color="#3B82F6" />
                <Text style={styles.earnRuleText}>Earn 10 points for every KES 100 spent</Text>
              </View>
              
              <WhiteSpace size="sm" />
              
              <View style={styles.earnRule}>
                <MaterialIcons name="people" size={20} color="#10B981" />
                <Text style={styles.earnRuleText}>Earn 100 points for each referral</Text>
              </View>
              
              <WhiteSpace size="sm" />
              
              <View style={styles.earnRule}>
                <MaterialIcons name="rate-review" size={20} color="#F59E0B" />
                <Text style={styles.earnRuleText}>Earn 50 points for product reviews</Text>
              </View>
              
              <WhiteSpace size="sm" />
              
              <View style={styles.earnRule}>
                <MaterialIcons name="account-circle" size={20} color="#8B5CF6" />
                <Text style={styles.earnRuleText}>Earn 50 points for profile completion</Text>
              </View>
            </Card.Body>
          </Card>

          <WhiteSpace size="xl" />
        </WingBlank>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FAFAFA',
  },
  content: {
    paddingVertical: 20,
    paddingBottom: 40,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#FAFAFA',
  },
  loadingText: {
    fontSize: 16,
    color: '#6B7280',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
    backgroundColor: '#FAFAFA',
  },
  emptyIcon: {
    fontSize: 64,
    marginBottom: 16,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1F2937',
    marginBottom: 24,
  },
  balanceCard: {
    paddingVertical: 8,
  },
  balanceHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  balanceLabel: {
    fontSize: 14,
    color: '#6B7280',
    fontWeight: '600',
  },
  tierBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    gap: 4,
  },
  tierText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  pointsAmount: {
    fontSize: 48,
    fontWeight: '800',
    color: '#1F2937',
  },
  pointsLabel: {
    fontSize: 14,
    color: '#6B7280',
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
  },
  statItem: {
    alignItems: 'center',
    flex: 1,
  },
  statDivider: {
    width: 1,
    height: 40,
    backgroundColor: '#E5E7EB',
  },
  statValue: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1F2937',
    marginTop: 8,
  },
  statLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 4,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1F2937',
  },
  referralDescription: {
    fontSize: 14,
    color: '#6B7280',
    lineHeight: 20,
  },
  referralCodeContainer: {
    backgroundColor: '#F9FAFB',
    padding: 16,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#E5E7EB',
    borderStyle: 'dashed',
    alignItems: 'center',
  },
  referralCodeLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 4,
  },
  referralCode: {
    fontSize: 24,
    fontWeight: '800',
    color: '#3B82F6',
    letterSpacing: 2,
  },
  shareButton: {
    borderRadius: 8,
    height: 44,
  },
  shareButtonText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  rewardItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
  },
  rewardInfo: {
    flex: 1,
    marginRight: 12,
  },
  rewardName: {
    fontSize: 14,
    fontWeight: '700',
    color: '#1F2937',
    marginBottom: 4,
  },
  rewardDescription: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 6,
  },
  rewardPoints: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  rewardPointsText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#F59E0B',
  },
  redeemButton: {
    backgroundColor: '#10B981',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
  },
  redeemButtonDisabled: {
    backgroundColor: '#E5E7EB',
  },
  redeemButtonText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  redeemButtonTextDisabled: {
    color: '#9CA3AF',
  },
  transactionItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
  },
  transactionIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  transactionInfo: {
    flex: 1,
  },
  transactionDescription: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1F2937',
    marginBottom: 4,
  },
  transactionDate: {
    fontSize: 12,
    color: '#9CA3AF',
  },
  transactionAmount: {
    fontSize: 16,
    fontWeight: '700',
  },
  earnRule: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  earnRuleText: {
    fontSize: 14,
    color: '#6B7280',
    flex: 1,
  },
});
