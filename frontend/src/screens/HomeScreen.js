import { View, Text, TouchableOpacity, StyleSheet, ScrollView } from "react-native";

export default function HomeScreen({ navigation, user, onLogout }) {
  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.header}>
          <View>
            <Text style={styles.greeting}>Hello! 👋</Text>
            <Text style={styles.role}>{user.role || "User"}</Text>
          </View>
          <TouchableOpacity style={styles.logoutButton} onPress={onLogout}>
            <Text style={styles.logoutText}>Logout</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.card}>
          <Text style={styles.cardTitle}>📋 Questionnaire</Text>
          <Text style={styles.cardDescription}>
            Answer a few questions for more accurate skin analysis
          </Text>
          <TouchableOpacity 
            style={styles.cardButton} 
            onPress={() => navigation.navigate('Questionnaire')}
          >
            <Text style={styles.cardButtonText}>Start Questionnaire</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.card}>
          <Text style={styles.cardTitle}>📸 Camera Analysis</Text>
          <Text style={styles.cardDescription}>
            Take a photo for instant AI-powered skin analysis
          </Text>
          <TouchableOpacity 
            style={styles.cardButton} 
            onPress={() => navigation.navigate('Camera')}
          >
            <Text style={styles.cardButtonText}>Open Camera</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.card}>
          <Text style={styles.cardTitle}>🔍 Skin Analysis</Text>
          <Text style={styles.cardDescription}>
            Get AI-powered analysis of your skin type and conditions
          </Text>
          <TouchableOpacity 
            style={styles.cardButton} 
            onPress={() => navigation.navigate('Analysis')}
          >
            <Text style={styles.cardButtonText}>Start Analysis</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.card}>
          <Text style={styles.cardTitle}>✨ Recommendations</Text>
          <Text style={styles.cardDescription}>
            Discover personalized product recommendations for your skin
          </Text>
          <TouchableOpacity 
            style={styles.cardButton} 
            onPress={() => navigation.navigate('Recommendations')}
          >
            <Text style={styles.cardButtonText}>View Products</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.card}>
          <Text style={styles.cardTitle}>📊 Profile History</Text>
          <Text style={styles.cardDescription}>
            Track your skin analysis history and progress
          </Text>
          <TouchableOpacity 
            style={styles.cardButton} 
            onPress={() => navigation.navigate('Profile')}
          >
            <Text style={styles.cardButtonText}>View History</Text>
          </TouchableOpacity>
        </View>
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
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 32,
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
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
    borderWidth: 1.5,
    borderColor: '#E5E7EB',
  },
  logoutText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#EF4444',
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
  cardTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1F2937',
    marginBottom: 8,
  },
  cardDescription: {
    fontSize: 14,
    color: '#6B7280',
    lineHeight: 20,
    marginBottom: 16,
  },
  cardButton: {
    backgroundColor: '#3B82F6',
    borderRadius: 10,
    padding: 14,
    alignItems: 'center',
  },
  cardButtonText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '700',
  },
});
