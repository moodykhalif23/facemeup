import { useState } from "react";
import { View, Text, StyleSheet, ScrollView } from "react-native";
import { Card, Button, WhiteSpace, WingBlank, ActivityIndicator, Toast, Progress } from '@ant-design/react-native';
import { analyze } from "../api";

export default function AnalysisScreen({ token }) {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleAnalyze = async () => {
    setLoading(true);
    try {
      const data = await analyze(token);
      setAnalysis(data.profile);
      Toast.success("Analysis complete!", 1);
    } catch (err) {
      Toast.fail(err?.response?.data?.error?.message || "Analysis failed", 2);
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <WingBlank size="lg">
          <View style={styles.header}>
            <Text style={styles.title}>Skin Analysis</Text>
            <Text style={styles.subtitle}>AI-powered skin type detection</Text>
          </View>

          <WhiteSpace size="xl" />

          {!analysis && !loading && (
            <View style={styles.emptyState}>
              <Text style={styles.emptyIcon}>🔍</Text>
              <Text style={styles.emptyTitle}>Ready to analyze</Text>
              <Text style={styles.emptyText}>
                Tap the button below to start your skin analysis
              </Text>
            </View>
          )}

          {loading && (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color="#3B82F6" />
              <WhiteSpace size="lg" />
              <Text style={styles.loadingText}>Analyzing your skin...</Text>
            </View>
          )}

          {analysis && (
            <>
              <Card>
                <Card.Header
                  title={
                    <View style={styles.cardHeader}>
                      <Text style={styles.cardIcon}>🎯</Text>
                      <Text style={styles.cardTitle}>Analysis Results</Text>
                    </View>
                  }
                />
                <Card.Body>
                  <View style={styles.resultSection}>
                    <Text style={styles.resultLabel}>Skin Type</Text>
                    <WhiteSpace size="sm" />
                    <View style={styles.badge}>
                      <Text style={styles.badgeText}>{analysis.skin_type}</Text>
                    </View>
                  </View>

                  <WhiteSpace size="lg" />

                  <View style={styles.resultSection}>
                    <Text style={styles.resultLabel}>Conditions</Text>
                    <WhiteSpace size="sm" />
                    <Text style={styles.resultValue}>{analysis.conditions.join(", ")}</Text>
                  </View>

                  <WhiteSpace size="lg" />

                  <View style={styles.resultSection}>
                    <Text style={styles.resultLabel}>Confidence</Text>
                    <WhiteSpace size="sm" />
                    <Progress
                      percent={analysis.confidence * 100}
                      position="normal"
                      unfilled
                      style={styles.progress}
                    />
                    <WhiteSpace size="sm" />
                    <Text style={styles.confidenceText}>
                      {Math.round(analysis.confidence * 100)}% confident
                    </Text>
                  </View>
                </Card.Body>
              </Card>
              <WhiteSpace size="lg" />
            </>
          )}

          <Button
            type="primary"
            onPress={handleAnalyze}
            loading={loading}
            disabled={loading}
            style={styles.button}
          >
            {analysis ? "Analyze Again" : "Start Analysis"}
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
  resultSection: {
    paddingVertical: 8,
  },
  resultLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6B7280',
  },
  resultValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1F2937',
  },
  badge: {
    backgroundColor: '#DBEAFE',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
    alignSelf: 'flex-start',
  },
  badgeText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#1E40AF',
    textTransform: 'capitalize',
  },
  progress: {
    borderRadius: 4,
  },
  confidenceText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#10B981',
  },
  button: {
    borderRadius: 12,
    height: 48,
  },
});
