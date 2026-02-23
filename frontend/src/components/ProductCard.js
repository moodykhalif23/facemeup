import { View, Text, TouchableOpacity, StyleSheet, Image } from 'react-native';
import { AntDesign, MaterialIcons } from '@expo/vector-icons';

export default function ProductCard({ product, onPress }) {
  const { sku, name, price, stock, image, matchScore } = product;

  return (
    <TouchableOpacity
      style={styles.card}
      onPress={() => onPress(product)}
      activeOpacity={0.7}
    >
      {/* Product Image */}
      <View style={styles.imageContainer}>
        {image ? (
          <Image source={{ uri: image }} style={styles.image} />
        ) : (
          <View style={styles.imagePlaceholder}>
            <MaterialIcons name="shopping-bag" size={48} color="#D1D5DB" />
          </View>
        )}
        {matchScore && (
          <View style={styles.matchBadge}>
            <AntDesign name="star" size={12} color="#FFFFFF" />
            <Text style={styles.matchText}>{Math.round(matchScore * 100)}% Match</Text>
          </View>
        )}
      </View>

      {/* Product Info */}
      <View style={styles.info}>
        <Text style={styles.name} numberOfLines={2}>{name}</Text>
        <Text style={styles.sku}>SKU: {sku}</Text>
        
        <View style={styles.footer}>
          <View>
            <Text style={styles.price}>KES {price?.toLocaleString() || '0'}</Text>
            <Text style={styles.stock}>
              {stock > 0 ? `${stock} in stock` : 'Out of stock'}
            </Text>
          </View>
          <View style={styles.addButton}>
            <AntDesign name="plus" size={20} color="#FFFFFF" />
          </View>
        </View>
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    overflow: 'hidden',
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 3,
  },
  imageContainer: {
    width: '100%',
    height: 200,
    backgroundColor: '#F9FAFB',
    position: 'relative',
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
  matchBadge: {
    position: 'absolute',
    top: 12,
    right: 12,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#10B981',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 20,
    gap: 4,
  },
  matchText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  info: {
    padding: 16,
  },
  name: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1F2937',
    marginBottom: 4,
    lineHeight: 22,
  },
  sku: {
    fontSize: 12,
    color: '#9CA3AF',
    marginBottom: 12,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-end',
  },
  price: {
    fontSize: 20,
    fontWeight: '800',
    color: '#3B82F6',
    marginBottom: 4,
  },
  stock: {
    fontSize: 12,
    color: '#6B7280',
  },
  addButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#3B82F6',
    justifyContent: 'center',
    alignItems: 'center',
  },
});
