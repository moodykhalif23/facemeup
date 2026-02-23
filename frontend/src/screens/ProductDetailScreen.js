import { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView, Image } from 'react-native';
import { AntDesign, MaterialIcons } from '@expo/vector-icons';

export default function ProductDetailScreen({ route, navigation }) {
  const { product } = route.params;
  const [quantity, setQuantity] = useState(1);
  const [selectedType, setSelectedType] = useState('retail'); // retail or wholesale

  const handleAddToCart = () => {
    // TODO: Add to cart logic
    navigation.navigate('Cart', {
      item: {
        ...product,
        quantity,
        type: selectedType,
      },
    });
  };

  const incrementQuantity = () => {
    if (quantity < product.stock) {
      setQuantity(quantity + 1);
    }
  };

  const decrementQuantity = () => {
    if (quantity > 1) {
      setQuantity(quantity - 1);
    }
  };

  const getPrice = () => {
    const basePrice = product.price || 0;
    if (selectedType === 'wholesale' && quantity >= 6) {
      return basePrice * 0.85; // 15% discount for wholesale
    }
    return basePrice;
  };

  const getTotalPrice = () => {
    return getPrice() * quantity;
  };

  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        {/* Product Image */}
        <View style={styles.imageContainer}>
          {product.image ? (
            <Image source={{ uri: product.image }} style={styles.image} />
          ) : (
            <View style={styles.imagePlaceholder}>
              <MaterialIcons name="shopping-bag" size={80} color="#D1D5DB" />
            </View>
          )}
          {product.matchScore && (
            <View style={styles.matchBadge}>
              <AntDesign name="star" size={16} color="#FFFFFF" />
              <Text style={styles.matchText}>{Math.round(product.matchScore * 100)}% Match for You</Text>
            </View>
          )}
        </View>

        {/* Product Info */}
        <View style={styles.infoSection}>
          <Text style={styles.name}>{product.name}</Text>
          <Text style={styles.sku}>SKU: {product.sku}</Text>
          
          {/* Price */}
          <View style={styles.priceContainer}>
            <Text style={styles.price}>KES {getPrice().toLocaleString()}</Text>
            {selectedType === 'wholesale' && quantity >= 6 && (
              <View style={styles.discountBadge}>
                <Text style={styles.discountText}>15% OFF</Text>
              </View>
            )}
          </View>

          {/* Stock Status */}
          <View style={styles.stockContainer}>
            <MaterialIcons 
              name={product.stock > 0 ? "check-circle" : "cancel"} 
              size={20} 
              color={product.stock > 0 ? "#10B981" : "#EF4444"} 
            />
            <Text style={[
              styles.stockText,
              { color: product.stock > 0 ? "#10B981" : "#EF4444" }
            ]}>
              {product.stock > 0 ? `${product.stock} in stock` : 'Out of stock'}
            </Text>
          </View>

          {/* Type Selector */}
          <View style={styles.typeSection}>
            <Text style={styles.sectionTitle}>Purchase Type</Text>
            <View style={styles.typeButtons}>
              <TouchableOpacity
                style={[
                  styles.typeButton,
                  selectedType === 'retail' && styles.typeButtonActive,
                ]}
                onPress={() => setSelectedType('retail')}
              >
                <MaterialIcons 
                  name="shopping-cart" 
                  size={20} 
                  color={selectedType === 'retail' ? '#3B82F6' : '#6B7280'} 
                />
                <Text style={[
                  styles.typeButtonText,
                  selectedType === 'retail' && styles.typeButtonTextActive,
                ]}>
                  Retail
                </Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[
                  styles.typeButton,
                  selectedType === 'wholesale' && styles.typeButtonActive,
                ]}
                onPress={() => setSelectedType('wholesale')}
              >
                <MaterialIcons 
                  name="store" 
                  size={20} 
                  color={selectedType === 'wholesale' ? '#3B82F6' : '#6B7280'} 
                />
                <Text style={[
                  styles.typeButtonText,
                  selectedType === 'wholesale' && styles.typeButtonTextActive,
                ]}>
                  Wholesale
                </Text>
                {quantity >= 6 && (
                  <View style={styles.saveBadge}>
                    <Text style={styles.saveText}>Save 15%</Text>
                  </View>
                )}
              </TouchableOpacity>
            </View>
            {selectedType === 'wholesale' && quantity < 6 && (
              <Text style={styles.helperText}>
                Order 6+ items for wholesale pricing (15% off)
              </Text>
            )}
          </View>

          {/* Quantity Selector */}
          <View style={styles.quantitySection}>
            <Text style={styles.sectionTitle}>Quantity</Text>
            <View style={styles.quantityControls}>
              <TouchableOpacity
                style={[styles.quantityButton, quantity === 1 && styles.quantityButtonDisabled]}
                onPress={decrementQuantity}
                disabled={quantity === 1}
              >
                <AntDesign name="minus" size={20} color={quantity === 1 ? '#D1D5DB' : '#3B82F6'} />
              </TouchableOpacity>
              
              <View style={styles.quantityDisplay}>
                <Text style={styles.quantityText}>{quantity}</Text>
              </View>
              
              <TouchableOpacity
                style={[styles.quantityButton, quantity >= product.stock && styles.quantityButtonDisabled]}
                onPress={incrementQuantity}
                disabled={quantity >= product.stock}
              >
                <AntDesign name="plus" size={20} color={quantity >= product.stock ? '#D1D5DB' : '#3B82F6'} />
              </TouchableOpacity>
            </View>
          </View>

          {/* Description */}
          {product.description && (
            <View style={styles.descriptionSection}>
              <Text style={styles.sectionTitle}>Description</Text>
              <Text style={styles.description}>{product.description}</Text>
            </View>
          )}

          {/* Ingredients */}
          {product.ingredients && product.ingredients.length > 0 && (
            <View style={styles.ingredientsSection}>
              <Text style={styles.sectionTitle}>Key Ingredients</Text>
              <View style={styles.ingredientsList}>
                {product.ingredients.map((ingredient, index) => (
                  <View key={index} style={styles.ingredientChip}>
                    <Text style={styles.ingredientText}>{ingredient}</Text>
                  </View>
                ))}
              </View>
            </View>
          )}
        </View>
      </ScrollView>

      {/* Bottom Bar */}
      <View style={styles.bottomBar}>
        <View style={styles.totalContainer}>
          <Text style={styles.totalLabel}>Total</Text>
          <Text style={styles.totalPrice}>KES {getTotalPrice().toLocaleString()}</Text>
        </View>
        <TouchableOpacity
          style={[styles.addToCartButton, product.stock === 0 && styles.addToCartButtonDisabled]}
          onPress={handleAddToCart}
          disabled={product.stock === 0}
        >
          <MaterialIcons name="shopping-cart" size={20} color="#FFFFFF" />
          <Text style={styles.addToCartText}>Add to Cart</Text>
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
    paddingBottom: 100,
  },
  imageContainer: {
    width: '100%',
    height: 300,
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
    bottom: 16,
    left: 16,
    right: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#10B981',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 12,
    gap: 8,
  },
  matchText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  infoSection: {
    padding: 20,
  },
  name: {
    fontSize: 24,
    fontWeight: '800',
    color: '#1F2937',
    marginBottom: 8,
    lineHeight: 32,
  },
  sku: {
    fontSize: 14,
    color: '#9CA3AF',
    marginBottom: 16,
  },
  priceContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
    gap: 12,
  },
  price: {
    fontSize: 28,
    fontWeight: '800',
    color: '#3B82F6',
  },
  discountBadge: {
    backgroundColor: '#FEF2F2',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
  },
  discountText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#EF4444',
  },
  stockContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 24,
    gap: 8,
  },
  stockText: {
    fontSize: 14,
    fontWeight: '600',
  },
  typeSection: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1F2937',
    marginBottom: 12,
  },
  typeButtons: {
    flexDirection: 'row',
    gap: 12,
  },
  typeButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    borderRadius: 12,
    backgroundColor: '#F9FAFB',
    borderWidth: 2,
    borderColor: '#E5E7EB',
    gap: 8,
    position: 'relative',
  },
  typeButtonActive: {
    backgroundColor: '#EFF6FF',
    borderColor: '#3B82F6',
  },
  typeButtonText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#6B7280',
  },
  typeButtonTextActive: {
    color: '#3B82F6',
  },
  saveBadge: {
    position: 'absolute',
    top: -8,
    right: -8,
    backgroundColor: '#10B981',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  saveText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  helperText: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 8,
  },
  quantitySection: {
    marginBottom: 24,
  },
  quantityControls: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
  },
  quantityButton: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#EFF6FF',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#3B82F6',
  },
  quantityButtonDisabled: {
    backgroundColor: '#F9FAFB',
    borderColor: '#E5E7EB',
  },
  quantityDisplay: {
    flex: 1,
    height: 48,
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  quantityText: {
    fontSize: 20,
    fontWeight: '800',
    color: '#1F2937',
  },
  descriptionSection: {
    marginBottom: 24,
  },
  description: {
    fontSize: 14,
    color: '#6B7280',
    lineHeight: 22,
  },
  ingredientsSection: {
    marginBottom: 24,
  },
  ingredientsList: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  ingredientChip: {
    backgroundColor: '#EFF6FF',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 20,
  },
  ingredientText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#3B82F6',
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
    gap: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 8,
  },
  totalContainer: {
    flex: 1,
    justifyContent: 'center',
  },
  totalLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 4,
  },
  totalPrice: {
    fontSize: 20,
    fontWeight: '800',
    color: '#1F2937',
  },
  addToCartButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    borderRadius: 12,
    backgroundColor: '#3B82F6',
    gap: 8,
  },
  addToCartButtonDisabled: {
    backgroundColor: '#93C5FD',
    opacity: 0.6,
  },
  addToCartText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FFFFFF',
  },
});
