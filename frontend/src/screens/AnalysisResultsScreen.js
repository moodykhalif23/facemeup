import { View, Text, TouchableOpacity, StyleSheet, ScrollView } from 'react-native';
import { AntDesign, MaterialIcons } from '@expo/vector-icons';

export default function AnalysisResultsScreen({ route, navigation }) {
  const { profile, inferenceMode } = route.params;

  const getConditionIcon = (condition) => {
    const icons = {
      'Acne': 'warning',
      'Hyperpigmentation': 'brightness-medium',
      'Uneven tone': 'palette',
      'Dehydration': 'water',
      'None detected': 'check-circle',
    };
    return icons[condition] || 'info';
  };

  const getConditionColor = (condition) => {
    const colors = {
      'Acne': '#EF4444',
      'Hyperpigmentation': '#F59E0B',
      'Uneven tone': '#8B5CF6',
      'Dehydration': '#3B82F6',
      'None detected': '#10B981',
    };
    return colors[condition] || '#6B7280';
  };

  const getSkinTypeColor = (skinType) => {
    const colors = {
      'Oily': '#3B82F6',
      'Dry': '#F59E0B',
      'Combination': '#8B5CF6',
      'Normal': '#10B981',
      'Sensitive': '#EF4444',
    };
    return colors[skinType] || '#6B7280';
  };

  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        {/* Success Header */}
        <View style={styles.successHeader}>
          <View style={styles.successIconContainer}>
            <AntDesign name="checkcircle" size={64} color="#10B981" />
          </View>
          <Text style={styles.successTitle}>Analysis Complete!</Text>
          <Text style={styles.successSubtitle}>
            {inferenceMode === 'on_device' ? 'Analyzed on your device' : 'Analyzed by our AI'}
          </Text>
        </View>

        {/* Skin Type Card */}
        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <MaterialIcons name="face" size={24} color={getSkinTypeColor(profile.skin_type)} />
            <Text style={styles.cardTitle}>Your Skin Type</Text>
          </View>
          <View style={[styles.skinTypeBadge, { backgroundColor: getSkinTypeColor(profile.skin_type) + '20' }]}>
            <Text style={[styles.skinTypeText, { color: getSkinTypeColor(profile.skin_type) }]}>
              {profile.skin_type}
            </Text>
          </View>
          <View style={styles.confidenceContainer}>
            <Text style={styles.confidenceLabel}>Confidence</Text>
            <View style={styles.progressBar}>
              <View 
                style={[
                  styles.progressFill, 
                  { 
                    width: `${profile.confidence * 100}%`,
                    backgroundColor: getSkinTypeColor(profile.skin_type)
                  }
                ]} 
              />
            </View>
            <Text style={[styles.confidenceText, { color: getSkinTypeColor(profile.skin_type) }]}>
              {Math.round(profile.confidence * 100)}%
            </Text>
          </View>
        </View>

        {/* Conditions Card */}
        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <MaterialIcons name="healing" size={24} color="#6B7280" />
            <Text style={styles.cardTitle}>Detected Conditions</Text>
          </View>
          <View style={styles.conditionsContainer}>
            {profile.conditions.map((condition, index) => (
              <View 
                key={index} 
                style={[
                  styles.conditionChip,
                  { backgroundColor: getConditionColor(condition) + '15' }
                ]}
              >
                <MaterialIcons 
                  name={getConditionIcon(condition)} 
                  size={18} 
                  color={getConditionColor(condition)} 
                />
                <Text style={[styles.conditionText, { color: getConditionColor(condition) }]}>
                  {condition}
                </Text>
              </View>
            ))}
          </View>
        </View>

        {/* Recommendations Card */}
        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <AntDesign name="star" size={24} color="#F59E0B" />
            <Text style={styles.cardTitle}>What's Next?</Text>
          </View>
          <View style={styles.recommendationItem}>
            <View style={styles.recommendationIcon}>
              <MaterialIcons name="shopping-bag" size={20} color="#3B82F6" />
            </View>
            <View style={styles.recommendationContent}>
              <Text style={styles.recommendationTitle}>Get Product Recommendations</Text>
              <Text style={styles.recommendationText}>
                Discover products tailored to your {profile.skin_type.toLowerCase()} skin
              </Text>
            </View>
          </View>
          <View style={styles.recommendationItem}>
            <View style={styles.recommendationIcon}>
              <MaterialIcons name="history" size={20} color="#8B5CF6" />
            </View>
            <View style={styles.recommendationContent}>
              <Text style={styles.recommendationTitle}>Track Your Progress</Text>
              <Text style={styles.recommendationText}>
                View your skin analysis history and see improvements over time
              </Text>
            </View>
          </View>
        </View>

        {/* Action Buttons */}
        <TouchableOpacity
          style={styles.primaryButton}
          onPress={() => navigation.navigate('Recommendations')}
        >
          <MaterialIcons name="shopping-bag" size={20} color="#FFFFFF" />
          <Text style={styles.primaryButtonText}>View Recommendations</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.secondaryButton}
          onPress={() => navigation.navigate('Profile')}
        >
          <MaterialIcons name="history" size={20} color="#3B82F6" />
          <Text style={styles.secondaryButtonText}>View History</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.textButton}
          onPress={() => navigation.navigate('Home')}
        >
          <Text style={styles.textButtonText}>Back to Home</Text>
        </TouchableOpacity>
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
    padding: 20,
    paddingBottom: 40,
  },
  successHeader: {
    alignItems: 'center',
    paddingVertical: 32,
  },
  successIconContainer: {
    marginBottom: 16,
  },
  successTitle: {
    fontSize: 28,
    fontWeight: '800',
    color: '#1F2937',
    marginBottom: 8,
  },
  successSubtitle: {
    fontSize: 14,
    color: '#6B7280',
  },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 24,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 3,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1F2937',
    marginLeft: 12,
  },
  skinTypeBadge: {
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 12,
    alignSelf: 'flex-start',
    marginBottom: 20,
  },
  skinTypeText: {
    fontSize: 24,
    fontWeight: '800',
    textTransform: 'capitalize',
  },
  confidenceContainer: {
    marginTop: 8,
  },
  confidenceLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6B7280',
    marginBottom: 8,
  },
  progressBar: {
    height: 8,
    backgroundColor: '#E5E7EB',
    borderRadius: 4,
    overflow: 'hidden',
    marginBottom: 8,
  },
  progressFill: {
    height: '100%',
    borderRadius: 4,
  },
  confidenceText: {
    fontSize: 14,
    fontWeight: '700',
  },
  conditionsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  conditionChip: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 20,
    gap: 6,
  },
  conditionText: {
    fontSize: 14,
    fontWeight: '600',
  },
  recommendationItem: {
    flexDirection: 'row',
    marginBottom: 20,
  },
  recommendationIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#EFF6FF',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  recommendationContent: {
    flex: 1,
  },
  recommendationTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1F2937',
    marginBottom: 4,
  },
  recommendationText: {
    fontSize: 14,
    color: '#6B7280',
    lineHeight: 20,
  },
  primaryButton: {
    flexDirection: 'row',
    backgroundColor: '#3B82F6',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
    gap: 8,
    shadowColor: '#3B82F6',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
  },
  primaryButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
  },
  secondaryButton: {
    flexDirection: 'row',
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
    gap: 8,
    borderWidth: 2,
    borderColor: '#3B82F6',
  },
  secondaryButtonText: {
    color: '#3B82F6',
    fontSize: 16,
    fontWeight: '700',
  },
  textButton: {
    padding: 12,
    alignItems: 'center',
  },
  textButtonText: {
    color: '#6B7280',
    fontSize: 14,
    fontWeight: '600',
  },
});
