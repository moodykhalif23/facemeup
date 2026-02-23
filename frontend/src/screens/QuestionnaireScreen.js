import { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView } from 'react-native';
import { AntDesign, MaterialIcons } from '@expo/vector-icons';

const QUESTIONS = [
  {
    id: 'skin_feel',
    title: 'How does your skin feel?',
    subtitle: 'Think about how your skin feels throughout the day',
    type: 'single',
    icon: 'face',
    options: [
      { value: 'oily', label: 'Oily', description: 'Shiny, greasy, especially in T-zone', icon: 'water-drop' },
      { value: 'dry', label: 'Dry', description: 'Tight, flaky, rough texture', icon: 'grain' },
      { value: 'normal', label: 'Normal', description: 'Balanced, not too oily or dry', icon: 'check-circle' },
      { value: 'combination', label: 'Combination', description: 'Oily T-zone, dry cheeks', icon: 'compare' },
    ],
  },
  {
    id: 'routine',
    title: 'What\'s your skincare routine?',
    subtitle: 'How many steps do you typically follow?',
    type: 'single',
    icon: 'spa',
    options: [
      { value: 'none', label: 'No Routine', description: 'I don\'t have a regular routine', icon: 'block' },
      { value: 'basic', label: 'Basic', description: 'Cleanser and moisturizer', icon: 'looks-one' },
      { value: 'moderate', label: 'Moderate', description: '3-5 products daily', icon: 'looks-3' },
      { value: 'advanced', label: 'Advanced', description: '6+ products, multi-step routine', icon: 'looks-6' },
    ],
  },
  {
    id: 'concerns',
    title: 'What are your main concerns?',
    subtitle: 'Select all that apply',
    type: 'multiple',
    icon: 'healing',
    options: [
      { value: 'acne', label: 'Acne', description: 'Breakouts, pimples, blemishes', icon: 'warning' },
      { value: 'wrinkles', label: 'Wrinkles', description: 'Fine lines, aging signs', icon: 'timeline' },
      { value: 'dark_spots', label: 'Dark Spots', description: 'Hyperpigmentation, uneven tone', icon: 'brightness-medium' },
      { value: 'dryness', label: 'Dryness', description: 'Dehydration, flakiness', icon: 'opacity' },
      { value: 'sensitivity', label: 'Sensitivity', description: 'Redness, irritation', icon: 'local-fire-department' },
      { value: 'large_pores', label: 'Large Pores', description: 'Visible, enlarged pores', icon: 'blur-on' },
    ],
  },
  {
    id: 'sun_exposure',
    title: 'How much sun exposure do you get?',
    subtitle: 'On a typical day',
    type: 'single',
    icon: 'wb-sunny',
    options: [
      { value: 'minimal', label: 'Minimal', description: 'Mostly indoors', icon: 'home' },
      { value: 'moderate', label: 'Moderate', description: '1-2 hours outdoors', icon: 'wb-cloudy' },
      { value: 'high', label: 'High', description: '3+ hours outdoors', icon: 'wb-sunny' },
    ],
  },
];

export default function QuestionnaireScreen({ navigation, route }) {
  const { imageBase64, token } = route.params || {};
  const [currentStep, setCurrentStep] = useState(0);
  const [answers, setAnswers] = useState({});

  const currentQuestion = QUESTIONS[currentStep];
  const isLastQuestion = currentStep === QUESTIONS.length - 1;
  const canProceed = answers[currentQuestion.id] !== undefined;

  const handleSelectOption = (value) => {
    if (currentQuestion.type === 'single') {
      setAnswers({ ...answers, [currentQuestion.id]: value });
    } else {
      // Multiple selection
      const current = answers[currentQuestion.id] || [];
      const newSelection = current.includes(value)
        ? current.filter(v => v !== value)
        : [...current, value];
      setAnswers({ ...answers, [currentQuestion.id]: newSelection });
    }
  };

  const isSelected = (value) => {
    if (currentQuestion.type === 'single') {
      return answers[currentQuestion.id] === value;
    } else {
      return (answers[currentQuestion.id] || []).includes(value);
    }
  };

  const handleNext = () => {
    if (isLastQuestion) {
      handleComplete();
    } else {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    } else {
      navigation.goBack();
    }
  };

  const handleComplete = () => {
    // Navigate to camera or analysis with questionnaire data
    if (imageBase64) {
      // Already have image, go to analysis
      navigation.navigate('AnalysisResults', {
        profile: {
          skin_type: mapAnswersToSkinType(answers),
          conditions: mapAnswersToConcerns(answers),
          confidence: 0.85,
        },
        inferenceMode: 'questionnaire',
        questionnaire: answers,
      });
    } else {
      // Need to take photo
      navigation.navigate('Camera', {
        questionnaire: answers,
        token,
      });
    }
  };

  const mapAnswersToSkinType = (answers) => {
    const skinFeel = answers.skin_feel;
    const mapping = {
      'oily': 'Oily',
      'dry': 'Dry',
      'normal': 'Normal',
      'combination': 'Combination',
    };
    return mapping[skinFeel] || 'Normal';
  };

  const mapAnswersToConcerns = (answers) => {
    const concerns = answers.concerns || [];
    const mapping = {
      'acne': 'Acne',
      'wrinkles': 'Aging',
      'dark_spots': 'Hyperpigmentation',
      'dryness': 'Dehydration',
      'sensitivity': 'Sensitivity',
      'large_pores': 'Large Pores',
    };
    return concerns.map(c => mapping[c]).filter(Boolean);
  };

  return (
    <View style={styles.container}>
      {/* Progress Bar */}
      <View style={styles.progressContainer}>
        <View style={styles.progressBar}>
          <View 
            style={[
              styles.progressFill, 
              { width: `${((currentStep + 1) / QUESTIONS.length) * 100}%` }
            ]} 
          />
        </View>
        <Text style={styles.progressText}>
          Question {currentStep + 1} of {QUESTIONS.length}
        </Text>
      </View>

      <ScrollView 
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
        {/* Question Header */}
        <View style={styles.questionHeader}>
          <View style={styles.iconContainer}>
            <MaterialIcons name={currentQuestion.icon} size={32} color="#3B82F6" />
          </View>
          <Text style={styles.questionTitle}>{currentQuestion.title}</Text>
          <Text style={styles.questionSubtitle}>{currentQuestion.subtitle}</Text>
        </View>

        {/* Options */}
        <View style={styles.optionsContainer}>
          {currentQuestion.options.map((option) => (
            <TouchableOpacity
              key={option.value}
              style={[
                styles.optionCard,
                isSelected(option.value) && styles.optionCardSelected,
              ]}
              onPress={() => handleSelectOption(option.value)}
              activeOpacity={0.7}
            >
              <View style={styles.optionHeader}>
                <View style={styles.optionIconContainer}>
                  <MaterialIcons 
                    name={option.icon} 
                    size={24} 
                    color={isSelected(option.value) ? '#3B82F6' : '#6B7280'} 
                  />
                </View>
                <View style={styles.optionTextContainer}>
                  <Text style={[
                    styles.optionLabel,
                    isSelected(option.value) && styles.optionLabelSelected,
                  ]}>
                    {option.label}
                  </Text>
                  <Text style={styles.optionDescription}>
                    {option.description}
                  </Text>
                </View>
                <View style={styles.checkContainer}>
                  {isSelected(option.value) ? (
                    <AntDesign name="checkcircle" size={24} color="#3B82F6" />
                  ) : (
                    <View style={styles.uncheckedCircle} />
                  )}
                </View>
              </View>
            </TouchableOpacity>
          ))}
        </View>

        {/* Helper Text */}
        {currentQuestion.type === 'multiple' && (
          <View style={styles.helperContainer}>
            <AntDesign name="infocirlceo" size={16} color="#6B7280" />
            <Text style={styles.helperText}>
              You can select multiple options
            </Text>
          </View>
        )}
      </ScrollView>

      {/* Navigation Buttons */}
      <View style={styles.navigationContainer}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={handleBack}
        >
          <AntDesign name="arrowleft" size={20} color="#6B7280" />
          <Text style={styles.backButtonText}>Back</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[
            styles.nextButton,
            !canProceed && styles.nextButtonDisabled,
          ]}
          onPress={handleNext}
          disabled={!canProceed}
        >
          <Text style={styles.nextButtonText}>
            {isLastQuestion ? 'Complete' : 'Next'}
          </Text>
          <AntDesign name="arrowright" size={20} color="#FFFFFF" />
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FAFAFA',
  },
  progressContainer: {
    paddingHorizontal: 20,
    paddingTop: 20,
    paddingBottom: 16,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  progressBar: {
    height: 4,
    backgroundColor: '#E5E7EB',
    borderRadius: 2,
    overflow: 'hidden',
    marginBottom: 8,
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#3B82F6',
    borderRadius: 2,
  },
  progressText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#6B7280',
    textAlign: 'center',
  },
  content: {
    padding: 20,
    paddingBottom: 100,
  },
  questionHeader: {
    alignItems: 'center',
    marginBottom: 32,
  },
  iconContainer: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: '#EFF6FF',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  questionTitle: {
    fontSize: 24,
    fontWeight: '800',
    color: '#1F2937',
    textAlign: 'center',
    marginBottom: 8,
  },
  questionSubtitle: {
    fontSize: 14,
    color: '#6B7280',
    textAlign: 'center',
  },
  optionsContainer: {
    gap: 12,
  },
  optionCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    borderWidth: 2,
    borderColor: '#E5E7EB',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  optionCardSelected: {
    borderColor: '#3B82F6',
    backgroundColor: '#EFF6FF',
  },
  optionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  optionIconContainer: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#F9FAFB',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  optionTextContainer: {
    flex: 1,
  },
  optionLabel: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1F2937',
    marginBottom: 4,
  },
  optionLabelSelected: {
    color: '#3B82F6',
  },
  optionDescription: {
    fontSize: 13,
    color: '#6B7280',
    lineHeight: 18,
  },
  checkContainer: {
    marginLeft: 8,
  },
  uncheckedCircle: {
    width: 24,
    height: 24,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#D1D5DB',
  },
  helperContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 16,
    gap: 8,
  },
  helperText: {
    fontSize: 13,
    color: '#6B7280',
  },
  navigationContainer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    flexDirection: 'row',
    padding: 20,
    backgroundColor: '#FFFFFF',
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
    gap: 12,
  },
  backButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    borderRadius: 12,
    backgroundColor: '#F9FAFB',
    borderWidth: 1,
    borderColor: '#E5E7EB',
    gap: 8,
  },
  backButtonText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#6B7280',
  },
  nextButton: {
    flex: 2,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    borderRadius: 12,
    backgroundColor: '#3B82F6',
    gap: 8,
    shadowColor: '#3B82F6',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
  },
  nextButtonDisabled: {
    backgroundColor: '#93C5FD',
    opacity: 0.6,
  },
  nextButtonText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FFFFFF',
  },
});
