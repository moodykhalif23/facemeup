import { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView, TextInput, ActivityIndicator } from 'react-native';
import { MaterialIcons, FontAwesome5 } from '@expo/vector-icons';

export default function PaymentScreen({ route, navigation }) {
  const { cartItems, deliveryInfo, total } = route.params;
  const [selectedMethod, setSelectedMethod] = useState('mpesa');
  const [mpesaPhone, setMpesaPhone] = useState('');
  const [cardDetails, setCardDetails] = useState({
    number: '',
    expiry: '',
    cvv: '',
    name: '',
  });
  const [isProcessing, setIsProcessing] = useState(false);

  const handlePayment = async () => {
    // Validate payment details
    if (selectedMethod === 'mpesa' && !mpesaPhone) {
      alert('Please enter your M-Pesa phone number');
      return;
    }

    if (selectedMethod === 'card') {
      if (!cardDetails.number || !cardDetails.expiry || !cardDetails.cvv || !cardDetails.name) {
        alert('Please fill in all card details');
        return;
      }
    }

    setIsProcessing(true);

    // Simulate payment processing
    setTimeout(() => {
      setIsProcessing(false);
      
      // Navigate to order tracking with order details
      navigation.navigate('OrderTracking', {
        orderId: `ORD-${Date.now()}`,
        cartItems,
        deliveryInfo,
        total,
        paymentMethod: selectedMethod,
        status: 'pending',
      });
    }, 2000);
  };

  return (
    <View style={styles.container}>
      <ScrollView 
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
        {/* Payment Method Selection */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Select Payment Method</Text>
          
          <TouchableOpacity
            style={[
              styles.methodCard,
              selectedMethod === 'mpesa' && styles.methodCardActive,
            ]}
            onPress={() => setSelectedMethod('mpesa')}
          >
            <View style={styles.methodHeader}>
              <View style={styles.methodIcon}>
                <MaterialIcons name="phone-android" size={24} color="#10B981" />
              </View>
              <View style={styles.methodInfo}>
                <Text style={styles.methodName}>M-Pesa</Text>
                <Text style={styles.methodDescription}>Pay via M-Pesa STK Push</Text>
              </View>
              <View style={[
                styles.radioButton,
                selectedMethod === 'mpesa' && styles.radioButtonActive,
              ]}>
                {selectedMethod === 'mpesa' && (
                  <View style={styles.radioButtonInner} />
                )}
              </View>
            </View>

            {selectedMethod === 'mpesa' && (
              <View style={styles.methodDetails}>
                <Text style={styles.label}>M-Pesa Phone Number</Text>
                <TextInput
                  style={styles.input}
                  placeholder="0712345678"
                  keyboardType="phone-pad"
                  value={mpesaPhone}
                  onChangeText={setMpesaPhone}
                  maxLength={10}
                />
                <Text style={styles.helperText}>
                  You will receive an STK push prompt on your phone
                </Text>
              </View>
            )}
          </TouchableOpacity>

          <TouchableOpacity
            style={[
              styles.methodCard,
              selectedMethod === 'card' && styles.methodCardActive,
            ]}
            onPress={() => setSelectedMethod('card')}
          >
            <View style={styles.methodHeader}>
              <View style={styles.methodIcon}>
                <FontAwesome5 name="credit-card" size={20} color="#3B82F6" />
              </View>
              <View style={styles.methodInfo}>
                <Text style={styles.methodName}>Credit/Debit Card</Text>
                <Text style={styles.methodDescription}>Visa, Mastercard accepted</Text>
              </View>
              <View style={[
                styles.radioButton,
                selectedMethod === 'card' && styles.radioButtonActive,
              ]}>
                {selectedMethod === 'card' && (
                  <View style={styles.radioButtonInner} />
                )}
              </View>
            </View>

            {selectedMethod === 'card' && (
              <View style={styles.methodDetails}>
                <View style={styles.inputGroup}>
                  <Text style={styles.label}>Card Number</Text>
                  <TextInput
                    style={styles.input}
                    placeholder="1234 5678 9012 3456"
                    keyboardType="number-pad"
                    value={cardDetails.number}
                    onChangeText={(text) => setCardDetails({ ...cardDetails, number: text })}
                    maxLength={19}
                  />
                </View>

                <View style={styles.row}>
                  <View style={[styles.inputGroup, { flex: 1, marginRight: 8 }]}>
                    <Text style={styles.label}>Expiry Date</Text>
                    <TextInput
                      style={styles.input}
                      placeholder="MM/YY"
                      keyboardType="number-pad"
                      value={cardDetails.expiry}
                      onChangeText={(text) => setCardDetails({ ...cardDetails, expiry: text })}
                      maxLength={5}
                    />
                  </View>

                  <View style={[styles.inputGroup, { flex: 1, marginLeft: 8 }]}>
                    <Text style={styles.label}>CVV</Text>
                    <TextInput
                      style={styles.input}
                      placeholder="123"
                      keyboardType="number-pad"
                      secureTextEntry
                      value={cardDetails.cvv}
                      onChangeText={(text) => setCardDetails({ ...cardDetails, cvv: text })}
                      maxLength={3}
                    />
                  </View>
                </View>

                <View style={styles.inputGroup}>
                  <Text style={styles.label}>Cardholder Name</Text>
                  <TextInput
                    style={styles.input}
                    placeholder="Name on card"
                    value={cardDetails.name}
                    onChangeText={(text) => setCardDetails({ ...cardDetails, name: text })}
                  />
                </View>
              </View>
            )}
          </TouchableOpacity>
        </View>

        {/* Order Summary */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Payment Summary</Text>
          
          <View style={styles.summaryRow}>
            <Text style={styles.summaryLabel}>Order Total</Text>
            <Text style={styles.summaryValue}>
              KES {total.toLocaleString()}
            </Text>
          </View>

          <View style={styles.divider} />

          <View style={styles.summaryRow}>
            <Text style={styles.totalLabel}>Amount to Pay</Text>
            <Text style={styles.totalValue}>
              KES {total.toLocaleString()}
            </Text>
          </View>
        </View>

        {/* Security Notice */}
        <View style={styles.securityNotice}>
          <MaterialIcons name="lock" size={16} color="#10B981" />
          <Text style={styles.securityText}>
            Your payment information is secure and encrypted
          </Text>
        </View>
      </ScrollView>

      <View style={styles.bottomBar}>
        <TouchableOpacity
          style={[styles.payButton, isProcessing && styles.payButtonDisabled]}
          onPress={handlePayment}
          disabled={isProcessing}
        >
          {isProcessing ? (
            <>
              <ActivityIndicator color="#FFFFFF" />
              <Text style={styles.payButtonText}>Processing...</Text>
            </>
          ) : (
            <>
              <MaterialIcons name="payment" size={20} color="#FFFFFF" />
              <Text style={styles.payButtonText}>
                Pay KES {total.toLocaleString()}
              </Text>
            </>
          )}
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
  content: {
    padding: 20,
    paddingBottom: 100,
  },
  section: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 20,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1F2937',
    marginBottom: 16,
  },
  methodCard: {
    borderWidth: 2,
    borderColor: '#E5E7EB',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
  },
  methodCardActive: {
    borderColor: '#3B82F6',
    backgroundColor: '#EFF6FF',
  },
  methodHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  methodIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#F9FAFB',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  methodInfo: {
    flex: 1,
  },
  methodName: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1F2937',
    marginBottom: 4,
  },
  methodDescription: {
    fontSize: 12,
    color: '#6B7280',
  },
  radioButton: {
    width: 24,
    height: 24,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#D1D5DB',
    justifyContent: 'center',
    alignItems: 'center',
  },
  radioButtonActive: {
    borderColor: '#3B82F6',
  },
  radioButtonInner: {
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: '#3B82F6',
  },
  methodDetails: {
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
  },
  inputGroup: {
    marginBottom: 16,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1F2937',
    marginBottom: 8,
  },
  input: {
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#E5E7EB',
    borderRadius: 8,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 14,
    color: '#1F2937',
  },
  helperText: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 8,
  },
  row: {
    flexDirection: 'row',
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  summaryLabel: {
    fontSize: 14,
    color: '#6B7280',
  },
  summaryValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1F2937',
  },
  divider: {
    height: 1,
    backgroundColor: '#E5E7EB',
    marginVertical: 12,
  },
  totalLabel: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1F2937',
  },
  totalValue: {
    fontSize: 20,
    fontWeight: '800',
    color: '#3B82F6',
  },
  securityNotice: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 12,
    backgroundColor: '#F0FDF4',
    borderRadius: 8,
    gap: 8,
  },
  securityText: {
    fontSize: 12,
    color: '#10B981',
    fontWeight: '600',
  },
  bottomBar: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    padding: 20,
    backgroundColor: '#FFFFFF',
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 8,
  },
  payButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    borderRadius: 12,
    backgroundColor: '#10B981',
    gap: 8,
  },
  payButtonDisabled: {
    opacity: 0.6,
  },
  payButtonText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FFFFFF',
  },
});
