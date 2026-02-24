import { useState } from "react";
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from "react-native";
import { Card, Button, WhiteSpace, WingBlank, ActivityIndicator, Toast, List } from '@ant-design/react-native';
import { analyze, recommend } from "../api";

export default function RecommendationsScreen({ token, navigation }) {
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleRecommend = async () => {
    setLoading(true);
    try {
      // First get analysis
      const analysisData = await analyze(token);
      const { skin_type, conditions } = analysisData.profile;
      
      // Then get recommendations
      const data = await recommend(token, skin_type, conditions);
      setRecommendations(data.products || []);
      Toast.success("Recommendations loaded!", 1);
    } catch (err) {
      Toast.fail(err?.response?.data?.error?.message || "Failed to get recommendations", 2);
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <WingBlank size="lg">
          <View style={styles.header}>
            <Text style={styles.title}>Product Recommendations</Text>
            <Text style={styles.subtitle}>Personalized for your skin</Text>
          </View>

          <WhiteSpace size="xl" />

          {!recommendations.length && !loading && (
            <View style={styles.emptyState}>
              <Text style={styles.emptyIcon}>✨</Text>
              <Text style={styles.emptyTitle}>Get Recommendations</Text>
              <Text style={styles.emptyText}>
                Discover products tailored to your skin type and needs
              </Text>
            </View>
          )}

          {loading && (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color="#3B82F6" />
              <WhiteSpace size="lg" />
              <Text style={styles.loadingText}>Finding perfect products...</Text>
            </View>
          )}

          {recommendations.length > 0 && (
            <>
              <List>
                {recommendations.map((product) => (
                  <View key={product.sku}>
                    <TouchableOpacity
                      onPress={() => navigation.navigate('ProductDetail', { 
                        product: {
                          ...product,
                          price: 2500,
                          stock: 50,
                          description: 'Premium skincare product formulated for your skin type',
                          ingredients: ['Hyaluronic Acid', 'Vitamin C', 'Niacinamide'],
                          matchScore: product.score,
                        }
                      })}
                    >
                      <Card>
                        <Card.Body>
                          <View style={styles.productCard}>
                            <View style={styles.productHeader}>
                              <Text style={styles.productName}>{product.name}</Text>
                              <View style={styles.scoreContainer}>
                                <Text style={styles.scoreText}>
                                  {Math.round(product.score * 100)}%
                                </Text>
                              </View>
                            </View>
                            
                            <WhiteSpace size="sm" />
                            
                            <Text style={styles.productSku}>SKU: {product.sku}</Text>
                            
                            <WhiteSpace size="sm" />
                            
                            <Text style={styles.viewDetails}>Tap to view details →</Text>
                          </View>
                        </Card.Body>
                      </Card>
                    </TouchableOpacity>
                    <WhiteSpace size="md" />
                  </View>
                ))}
              </List>
            </>
          )}

          <Button
            type="primary"
            onPress={handleRecommend}
            loading={loading}
            disabled={loading}
            style={styles.button}
          >
            {recommendations.length ? "Refresh" : "Get Recommendations"}
          </Button>
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
  loadingContainer: {
    alignItems: 'center',
    paddingVertical: 60,
  },
  loadingText: {
    fontSize: 16,
    color: '#6B7280',
  },
  productCard: {
    paddingVertical: 8,
  },
  productHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  productName: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1F2937',
    flex: 1,
    marginRight: 12,
  },
  scoreContainer: {
    backgroundColor: '#10B981',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  scoreText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  productSku: {
    fontSize: 12,
    color: '#9CA3AF',
    fontWeight: '500',
  },
  viewDetails: {
    fontSize: 12,
    color: '#3B82F6',
    fontWeight: '600',
  },
  button: {
    borderRadius: 12,
    height: 48,
  },
});
