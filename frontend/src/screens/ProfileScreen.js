import { useState, useEffect } from "react";
import { View, Text, StyleSheet, ScrollView } from "react-native";
import { Card, Button, WhiteSpace, WingBlank, ActivityIndicator, Toast, List } from '@ant-design/react-native';
import { getProfile } from "../api";

const ListItem = List.Item;

export default function ProfileScreen({ token, userId }) {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadProfile = async () => {
    setLoading(true);
    try {
      const data = await getProfile(token, userId);
      setProfile(data);
      Toast.success("Profile loaded!", 1);
    } catch (err) {
      Toast.fail(err?.response?.data?.error?.message || "Failed to load profile", 2);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProfile();
  }, []);

  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <WingBlank size="lg">
          <View style={styles.header}>
            <Text style={styles.title}>Profile History</Text>
            <Text style={styles.subtitle}>Track your skin journey</Text>
          </View>

          <WhiteSpace size="xl" />

          {loading && (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color="#3B82F6" />
              <WhiteSpace size="lg" />
              <Text style={styles.loadingText}>Loading history...</Text>
            </View>
          )}

          {profile && profile.history && profile.history.length > 0 && (
            <>
              <Text style={styles.historyCount}>
                {profile.history.length} {profile.history.length === 1 ? 'entry' : 'entries'}
              </Text>
              <WhiteSpace size="md" />
              
              <List>
                {profile.history.map((entry, idx) => (
                  <View key={`${entry.timestamp}-${idx}`}>
                    <Card>
                      <Card.Body>
                        <View style={styles.historyCard}>
                          <View style={styles.historyHeader}>
                            <Text style={styles.historyType}>{entry.skin_type}</Text>
                            <View style={styles.confidenceBadge}>
                              <Text style={styles.confidenceText}>
                                {Math.round(entry.confidence * 100)}%
                              </Text>
                            </View>
                          </View>
                          
                          <WhiteSpace size="sm" />
                          
                          <Text style={styles.historyConditions}>
                            {entry.conditions.join(", ")}
                          </Text>
                          
                          {entry.timestamp && (
                            <>
                              <WhiteSpace size="sm" />
                              <Text style={styles.historyDate}>
                                {new Date(entry.timestamp).toLocaleDateString('en-US', {
                                  year: 'numeric',
                                  month: 'long',
                                  day: 'numeric',
                                })}
                              </Text>
                            </>
                          )}
                        </View>
                      </Card.Body>
                    </Card>
                    <WhiteSpace size="md" />
                  </View>
                ))}
              </List>
            </>
          )}

          {profile && profile.history && profile.history.length === 0 && (
            <View style={styles.emptyState}>
              <Text style={styles.emptyIcon}>📊</Text>
              <Text style={styles.emptyTitle}>No History Yet</Text>
              <Text style={styles.emptyText}>
                Start analyzing your skin to build your history
              </Text>
            </View>
          )}

          {!loading && (
            <>
              <WhiteSpace size="lg" />
              <Button
                type="primary"
                onPress={loadProfile}
                style={styles.button}
              >
                Refresh
              </Button>
            </>
          )}
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
    paddingTop: 20,
  },
  title: {
    fontSize: 28,
    fontWeight: '800',
    color: '#1F2937',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    color: '#6B7280',
  },
  loadingContainer: {
    alignItems: 'center',
    paddingVertical: 60,
  },
  loadingText: {
    fontSize: 16,
    color: '#6B7280',
  },
  historyCount: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6B7280',
  },
  historyCard: {
    paddingVertical: 8,
  },
  historyHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  historyType: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1F2937',
    textTransform: 'capitalize',
  },
  confidenceBadge: {
    backgroundColor: '#D1FAE5',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  confidenceText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#065F46',
  },
  historyConditions: {
    fontSize: 14,
    color: '#6B7280',
  },
  historyDate: {
    fontSize: 12,
    color: '#9CA3AF',
    fontWeight: '500',
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 60,
  },
  emptyIcon: {
    fontSize: 64,
    marginBottom: 16,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1F2937',
    marginBottom: 8,
  },
  emptyText: {
    fontSize: 14,
    color: '#6B7280',
    textAlign: 'center',
    paddingHorizontal: 40,
  },
  button: {
    borderRadius: 12,
    height: 48,
  },
});
