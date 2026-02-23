import { View, Text, TouchableOpacity, StyleSheet, ScrollView } from 'react-native';
import { MaterialIcons, FontAwesome5 } from '@expo/vector-icons';

export default function OrderTrackingScreen({ route, navigation }) {
  const { orderId, cartItems, deliveryInfo, total, paymentMethod, status } = route.params;

  const orderStatuses = [
    { key: 'pending', label: 'Order Placed', icon: 'check-circle', completed: true },
    { key: 'confirmed', label: 'Confirmed', icon: 'verified', completed: status !== 'pending' },
    { key: 'processing', label: 'Processing', icon: 'inventory', completed: false },
    { key: 'shipped', label: 'Shipped', icon: 'local-shipping', completed: false },
    { key: 'delivered', label: 'Delivered', icon: 'home', completed: false },
  ];

  const currentStatusIndex = orderStatuses.findIndex(s => s.key === status);

  const getStatusColor = (index) => {
    if (index <= currentStatusIndex) return '#10B981';
    return '#D1D5DB';
  };

  return (
    <View style={styles.container}>
      <ScrollView 
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
        {/* Success Header */}
        <View style={styles.successHeader}>
          <View style={styles.successIcon}>
            <MaterialIcons name="check-circle" size={64} color="#10B981" />
          </View>
          <Text style={styles.successTitle}>Order Placed Successfully!</Text>
          <Text style={styles.successSubtitle}>
            Your order has been received and is being processed
          </Text>
        </View>

        {/* Order ID */}
        <View style={styles.section}>
          <View style={styles.orderIdContainer}>
            <Text style={styles.orderIdLabel}>Order ID</Text>
            <Text style={styles.orderIdValue}>{orderId}</Text>
          </View>
        </View>

        {/* Order Status Timeline */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Order Status</Text>
          
          <View style={styles.timeline}>
            {orderStatuses.map((statusItem, index) => (
              <View key={statusItem.key} style={styles.timelineItem}>
                <View style={styles.timelineIconContainer}>
                  <View style={[
                    styles.timelineIcon,
                    { backgroundColor: getStatusColor(index) }
                  ]}>
                    <MaterialIcons 
                      name={statusItem.icon} 
                      size={20} 
                      color="#FFFFFF" 
                    />
                  </View>
                  {index < orderStatuses.length - 1 && (
                    <View style={[
                      styles.timelineLine,
                      { backgroundColor: getStatusColor(index + 1) }
                    ]} />
                  )}
                </View>
                
                <View style={styles.timelineContent}>
                  <Text style={[
                    styles.timelineLabel,
                    { color: statusItem.completed ? '#1F2937' : '#9CA3AF' }
                  ]}>
                    {statusItem.label}
                  </Text>
                  {statusItem.completed && (
                    <Text style={styles.timelineTime}>
                      {index === 0 ? 'Just now' : ''}
                    </Text>
                  )}
                </View>
              </View>
            ))}
          </View>
        </View>

        {/* Delivery Information */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Delivery Information</Text>
          
          <View style={styles.infoRow}>
            <MaterialIcons name="person" size={20} color="#6B7280" />
            <Text style={styles.infoText}>{deliveryInfo.fullName}</Text>
          </View>

          <View style={styles.infoRow}>
            <MaterialIcons name="phone" size={20} color="#6B7280" />
            <Text style={styles.infoText}>{deliveryInfo.phone}</Text>
          </View>

          <View style={styles.infoRow}>
            <MaterialIcons name="location-on" size={20} color="#6B7280" />
            <Text style={styles.infoText}>
              {deliveryInfo.address}, {deliveryInfo.city}
            </Text>
          </View>

          {deliveryInfo.notes && (
            <View style={styles.infoRow}>
              <MaterialIcons name="note" size={20} color="#6B7280" />
              <Text style={styles.infoText}>{deliveryInfo.notes}</Text>
            </View>
          )}
        </View>

        {/* Order Items */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Order Items ({cartItems.length})</Text>
          
          {cartItems.map((item, index) => {
            const price = item.type === 'wholesale' && item.quantity >= 6 
              ? item.price * 0.85 
              : item.price;
            return (
              <View key={index} style={styles.orderItem}>
                <View style={styles.itemInfo}>
                  <Text style={styles.itemName}>{item.name}</Text>
                  <Text style={styles.itemDetails}>
                    {item.quantity} x KES {price.toLocaleString()}
                  </Text>
                </View>
                <Text style={styles.itemTotal}>
                  KES {(price * item.quantity).toLocaleString()}
                </Text>
              </View>
            );
          })}
        </View>

        {/* Payment Summary */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Payment Summary</Text>
          
          <View style={styles.summaryRow}>
            <Text style={styles.summaryLabel}>Payment Method</Text>
            <View style={styles.paymentMethodBadge}>
              <MaterialIcons 
                name={paymentMethod === 'mpesa' ? 'phone-android' : 'credit-card'} 
                size={16} 
                color="#3B82F6" 
              />
              <Text style={styles.paymentMethodText}>
                {paymentMethod === 'mpesa' ? 'M-Pesa' : 'Card'}
              </Text>
            </View>
          </View>

          <View style={styles.divider} />

          <View style={styles.summaryRow}>
            <Text style={styles.totalLabel}>Total Paid</Text>
            <Text style={styles.totalValue}>
              KES {total.toLocaleString()}
            </Text>
          </View>
        </View>

        {/* Help Section */}
        <View style={styles.helpSection}>
          <MaterialIcons name="help-outline" size={20} color="#6B7280" />
          <Text style={styles.helpText}>
            Need help with your order? Contact our support team
          </Text>
        </View>
      </ScrollView>

      {/* Bottom Actions */}
      <View style={styles.bottomBar}>
        <TouchableOpacity
          style={styles.secondaryButton}
          onPress={() => navigation.navigate('Home')}
        >
          <MaterialIcons name="home" size={20} color="#3B82F6" />
          <Text style={styles.secondaryButtonText}>Back to Home</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.primaryButton}
          onPress={() => navigation.navigate('Recommendations')}
        >
          <MaterialIcons name="shopping-bag" size={20} color="#FFFFFF" />
          <Text style={styles.primaryButtonText}>Continue Shopping</Text>
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
  successHeader: {
    alignItems: 'center',
    paddingVertical: 32,
    marginBottom: 16,
  },
  successIcon: {
    marginBottom: 16,
  },
  successTitle: {
    fontSize: 24,
    fontWeight: '800',
    color: '#1F2937',
    marginBottom: 8,
    textAlign: 'center',
  },
  successSubtitle: {
    fontSize: 14,
    color: '#6B7280',
    textAlign: 'center',
    paddingHorizontal: 32,
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
  orderIdContainer: {
    alignItems: 'center',
  },
  orderIdLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 4,
  },
  orderIdValue: {
    fontSize: 18,
    fontWeight: '700',
    color: '#3B82F6',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1F2937',
    marginBottom: 16,
  },
  timeline: {
    paddingLeft: 8,
  },
  timelineItem: {
    flexDirection: 'row',
    marginBottom: 8,
  },
  timelineIconContainer: {
    alignItems: 'center',
    marginRight: 16,
  },
  timelineIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
  timelineLine: {
    width: 2,
    flex: 1,
    marginTop: 4,
    marginBottom: 4,
  },
  timelineContent: {
    flex: 1,
    paddingTop: 8,
    paddingBottom: 16,
  },
  timelineLabel: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 4,
  },
  timelineTime: {
    fontSize: 12,
    color: '#6B7280',
  },
  infoRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 12,
    gap: 12,
  },
  infoText: {
    flex: 1,
    fontSize: 14,
    color: '#1F2937',
    lineHeight: 20,
  },
  orderItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  itemInfo: {
    flex: 1,
    marginRight: 12,
  },
  itemName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1F2937',
    marginBottom: 4,
  },
  itemDetails: {
    fontSize: 12,
    color: '#6B7280',
  },
  itemTotal: {
    fontSize: 14,
    fontWeight: '700',
    color: '#3B82F6',
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
  paymentMethodBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#EFF6FF',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
    gap: 6,
  },
  paymentMethodText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#3B82F6',
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
    color: '#10B981',
  },
  helpSection: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    backgroundColor: '#F9FAFB',
    borderRadius: 8,
    gap: 8,
  },
  helpText: {
    fontSize: 12,
    color: '#6B7280',
  },
  bottomBar: {
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
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 8,
  },
  secondaryButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 14,
    borderRadius: 12,
    backgroundColor: '#EFF6FF',
    gap: 6,
  },
  secondaryButtonText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#3B82F6',
  },
  primaryButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 14,
    borderRadius: 12,
    backgroundColor: '#3B82F6',
    gap: 6,
  },
  primaryButtonText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#FFFFFF',
  },
});
