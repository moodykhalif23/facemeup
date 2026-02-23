import { View, Text, TouchableOpacity, StyleSheet, Image } from 'react-native';
import { AntDesign, MaterialIcons } from '@expo/vector-icons';

export default function CartItem({ item, onUpdateQuantity, onRemove }) {
  const getPrice = () => {
    const basePrice = item.price || 0;
    if (item.type === 'wholesale' && item.quantity >= 6) {
      return basePrice * 0.85;
    }
    return basePrice;
  };

  const getTotalPrice = () => {
    return getPrice() * item.quantity;
  };

  return (
    <View style={styles.container}>
      <View style={styles.imageContainer}>
        {item.image ? (
          <Image source={{ uri: item.image }} style={styles.image} />
        ) : (
          <View style={styles.imagePlaceholder}>
            <MaterialIcons name="shopping-bag" size={32} color="#D1D5DB" />
          </View>
        )}
      </View>

      <View style={styles.details}>
        <Text style={styles.name} numberOfLines={2}>{item.name}</Text>
        <Text style={styles.type}>
          {item.type === 'wholesale' ? 'Wholesale' : 'Retail'}
          {item.type === 'wholesale' && item.quantity >= 6 && ' • 15% OFF'}
        </Text>
        
        <View style={styles.priceRow}>
          <Text style={styles.price}>KES {getPrice().toLocaleString()}</Text>
          <View style={styles.quantityControls}>
            <TouchableOpacity
              style={styles.quantityButton}
              onPress={() => onUpdateQuantity(item.id, item.quantity - 1)}
              disabled={item.quantity === 1}
            >
              <AntDesign 
                name="minus" 
                size={14} 
                color={item.quantity === 1 ? '#D1D5DB' : '#3B82F6'} 
              />
            </TouchableOpacity>
            
            <Text style={styles.quantity}>{item.quantity}</Text>
            
            <TouchableOpacity
              style={styles.quantityButton}
              onPress={() => onUpdateQuantity(item.id, item.quantity + 1)}
              disabled={item.quantity >= item.stock}
            >
              <AntDesign 
                name="plus" 
                size={14} 
                color={item.quantity >= item.stock ? '#D1D5DB' : '#3B82F6'} 
              />
            </TouchableOpacity>
          </View>
        </View>

        <Text style={styles.subtotal}>
          Subtotal: KES {getTotalPrice().toLocaleString()}
        </Text>
      </View>

      <TouchableOpacity
        style={styles.removeButton}
        onPress={() => onRemove(item.id)}
      >
        <MaterialIcons name="close" size={20} color="#EF4444" />
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 12,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  imageContainer: {
    width: 80,
    height: 80,
    borderRadius: 8,
    backgroundColor: '#F9FAFB',
    overflow: 'hidden',
  },
  image: {
    width: '100%',
    height: '100%',
    resizeMode: 'cover',
  },
  imagePlaceholder: {
    width: '100%',
    height: '100%',
    justifyContent: 'center',
    alignItems: 'center',
  },
  details: {
    flex: 1,
    marginLeft: 12,
    justifyContent: 'space-between',
  },
  name: {
    fontSize: 14,
    fontWeight: '700',
    color: '#1F2937',
    marginBottom: 4,
  },
  type: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 8,
  },
  priceRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  price: {
    fontSize: 14,
    fontWeight: '700',
    color: '#3B82F6',
  },
  quantityControls: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  quantityButton: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: '#EFF6FF',
    justifyContent: 'center',
    alignItems: 'center',
  },
  quantity: {
    fontSize: 14,
    fontWeight: '700',
    color: '#1F2937',
    minWidth: 20,
    textAlign: 'center',
  },
  subtotal: {
    fontSize: 12,
    fontWeight: '600',
    color: '#1F2937',
  },
  removeButton: {
    padding: 4,
  },
});
