import { View, Text, StyleSheet, ScrollView } from "react-native";
import { Card, WingBlank, WhiteSpace, Button, Grid } from '@ant-design/react-native';

export default function HomeScreen({ navigation, user, onLogout }) {
  const menuItems = [
    {
      icon: '📋',
      title: 'Questionnaire',
      description: 'Answer questions for accurate analysis',
      route: 'Questionnaire',
      color: '#EFF6FF',
    },
    {
      icon: '📸',
      title: 'Camera Analysis',
      description: 'Take a photo for instant AI analysis',
      route: 'Camera',
      color: '#F0FDF4',
    },
    {
      icon: '🔍',
      title: 'Skin Analysis',
      description: 'Get AI-powered skin type detection',
      route: 'Analysis',
      color: '#FEF3C7',
    },
    {
      icon: '✨',
      title: 'Recommendations',
      description: 'Discover personalized products',
      route: 'Recommendations',
      color: '#FCE7F3',
    },
    {
      icon: '🎁',
      title: 'Loyalty & Rewards',
      description: 'Earn points and redeem rewards',
      route: 'Loyalty',
      color: '#FEF3C7',
    },
    {
      icon: '📊',
      title: 'Profile History',
      description: 'Track your skin journey',
      route: 'Profile',
      color: '#E0E7FF',
    },
  ];

  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <WingBlank size="lg">
          <View style={styles.header}>
            <View>
              <Text style={styles.greeting}>Hello! 👋</Text>
              <Text style={styles.role}>{user.role || "User"}</Text>
            </View>
            <Button
              type="ghost"
              size="small"
              onPress={onLogout}
              style={styles.logoutButton}
            >
              <Text style={styles.logoutText}>Logout</Text>
            </Button>
          </View>

          <WhiteSpace size="xl" />

          {menuItems.map((item, index) => (
            <View key={index}>
              <Card>
                <Card.Header
                  title={
                    <View style={styles.cardHeader}>
                      <Text style={styles.cardIcon}>{item.icon}</Text>
                      <Text style={styles.cardTitle}>{item.title}</Text>
                    </View>
                  }
                />
                <Card.Body>
                  <View style={styles.cardBody}>
                    <Text style={styles.cardDescription}>{item.description}</Text>
                    <WhiteSpace size="md" />
                    <Button
                      type="primary"
                      size="small"
                      onPress={() => navigation.navigate(item.route)}
                      style={styles.cardButton}
                    >
                      Get Started
                    </Button>
                  </View>
                </Card.Body>
              </Card>
              <WhiteSpace size="lg" />
            </View>
          ))}
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
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: 20,
  },
  greeting: {
    fontSize: 28,
    fontWeight: '800',
    color: '#1F2937',
  },
  role: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 4,
    textTransform: 'capitalize',
  },
  logoutButton: {
    borderColor: '#E5E7EB',
    borderWidth: 1.5,
    borderRadius: 8,
  },
  logoutText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#EF4444',
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  cardIcon: {
    fontSize: 24,
    marginRight: 12,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1F2937',
  },
  cardBody: {
    paddingVertical: 8,
  },
  cardDescription: {
    fontSize: 14,
    color: '#6B7280',
    lineHeight: 20,
  },
  cardButton: {
    borderRadius: 8,
  },
});
