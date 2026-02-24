import { useState, useEffect } from "react";
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Image, Dimensions } from "react-native";
import { Card, Button, WhiteSpace, WingBlank, Modal, Toast, Switch } from '@ant-design/react-native';
import { MaterialIcons, Ionicons } from '@expo/vector-icons';
import * as ImagePicker from 'expo-image-picker';

const { width } = Dimensions.get('window');
const PHOTO_SIZE = (width - 60) / 3;

export default function ProgressPhotosScreen({ token, userId, navigation }) {
  const [photos, setPhotos] = useState([]);
  const [viewMode, setViewMode] = useState('grid'); // 'grid' or 'timeline'
  const [selectedPhoto, setSelectedPhoto] = useState(null);
  const [compareMode, setCompareMode] = useState(false);
  const [comparePhotos, setComparePhotos] = useState([null, null]);
  const [isPrivate, setIsPrivate] = useState(true);

  // Mock data - in production, this would come from API
  const mockPhotos = [
    {
      id: 1,
      uri: null,
      date: '2024-02-20',
      note: 'Starting my skincare journey',
      tags: ['baseline', 'front'],
      isPrivate: true,
    },
    {
      id: 2,
      uri: null,
      date: '2024-02-15',
      note: 'After 1 week of new routine',
      tags: ['progress', 'front'],
      isPrivate: true,
    },
    {
      id: 3,
      uri: null,
      date: '2024-02-10',
      note: 'Side view - checking texture',
      tags: ['progress', 'side'],
      isPrivate: true,
    },
    {
      id: 4,
      uri: null,
      date: '2024-02-05',
      note: 'Close-up of problem area',
      tags: ['detail', 'front'],
      isPrivate: true,
    },
  ];

  useEffect(() => {
    loadPhotos();
  }, []);

  const loadPhotos = async () => {
    // Simulate API call
    setTimeout(() => {
      setPhotos(mockPhotos);
    }, 500);
  };

  const requestCameraPermission = async () => {
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    if (status !== 'granted') {
      Toast.fail('Camera permission is required', 2);
      return false;
    }
    return true;
  };


  const handleTakePhoto = async () => {
    const hasPermission = await requestCameraPermission();
    if (!hasPermission) return;

    const result = await ImagePicker.launchCameraAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      aspect: [3, 4],
      quality: 0.8,
    });

    if (!result.canceled) {
      const newPhoto = {
        id: Date.now(),
        uri: result.assets[0].uri,
        date: new Date().toISOString().split('T')[0],
        note: '',
        tags: ['progress'],
        isPrivate: true,
      };
      setPhotos([newPhoto, ...photos]);
      Toast.success('Photo added!', 1);
      
      // Open modal to add note
      setSelectedPhoto(newPhoto);
    }
  };

  const handleSelectFromGallery = async () => {
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      aspect: [3, 4],
      quality: 0.8,
    });

    if (!result.canceled) {
      const newPhoto = {
        id: Date.now(),
        uri: result.assets[0].uri,
        date: new Date().toISOString().split('T')[0],
        note: '',
        tags: ['progress'],
        isPrivate: true,
      };
      setPhotos([newPhoto, ...photos]);
      Toast.success('Photo added!', 1);
      setSelectedPhoto(newPhoto);
    }
  };

  const handlePhotoPress = (photo) => {
    if (compareMode) {
      if (!comparePhotos[0]) {
        setComparePhotos([photo, null]);
        Toast.info('Select second photo to compare', 1);
      } else if (!comparePhotos[1]) {
        setComparePhotos([comparePhotos[0], photo]);
      }
    } else {
      setSelectedPhoto(photo);
    }
  };

  const handleDeletePhoto = (photoId) => {
    Modal.alert(
      'Delete Photo',
      'Are you sure you want to delete this photo?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: () => {
            setPhotos(photos.filter(p => p.id !== photoId));
            setSelectedPhoto(null);
            Toast.success('Photo deleted', 1);
          },
        },
      ]
    );
  };

  const toggleCompareMode = () => {
    setCompareMode(!compareMode);
    setComparePhotos([null, null]);
    if (!compareMode) {
      Toast.info('Select two photos to compare', 2);
    }
  };

  const renderPhotoGrid = () => (
    <View style={styles.photoGrid}>
      {photos.map((photo) => (
        <TouchableOpacity
          key={photo.id}
          style={[
            styles.photoItem,
            comparePhotos.includes(photo) && styles.photoItemSelected,
          ]}
          onPress={() => handlePhotoPress(photo)}
        >
          {photo.uri ? (
            <Image source={{ uri: photo.uri }} style={styles.photoImage} />
          ) : (
            <View style={styles.photoPlaceholder}>
              <MaterialIcons name="image" size={40} color="#D1D5DB" />
            </View>
          )}
          <View style={styles.photoOverlay}>
            <Text style={styles.photoDate}>
              {new Date(photo.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
            </Text>
          </View>
          {comparePhotos.includes(photo) && (
            <View style={styles.selectedBadge}>
              <MaterialIcons name="check-circle" size={24} color="#10B981" />
            </View>
          )}
        </TouchableOpacity>
      ))}
    </View>
  );


  const renderTimeline = () => (
    <View style={styles.timeline}>
      {photos.map((photo, index) => (
        <View key={photo.id}>
          <TouchableOpacity
            style={styles.timelineItem}
            onPress={() => handlePhotoPress(photo)}
          >
            <View style={styles.timelineDate}>
              <Text style={styles.timelineDateText}>
                {new Date(photo.date).toLocaleDateString('en-US', {
                  month: 'short',
                  day: 'numeric',
                  year: 'numeric',
                })}
              </Text>
            </View>
            
            <View style={styles.timelineDot} />
            
            <View style={styles.timelineContent}>
              <Card>
                <Card.Body>
                  <View style={styles.timelineCard}>
                    {photo.uri ? (
                      <Image source={{ uri: photo.uri }} style={styles.timelineImage} />
                    ) : (
                      <View style={styles.timelineImagePlaceholder}>
                        <MaterialIcons name="image" size={60} color="#D1D5DB" />
                      </View>
                    )}
                    {photo.note && (
                      <>
                        <WhiteSpace size="sm" />
                        <Text style={styles.timelineNote}>{photo.note}</Text>
                      </>
                    )}
                    <WhiteSpace size="xs" />
                    <View style={styles.timelineTags}>
                      {photo.tags.map((tag, idx) => (
                        <View key={idx} style={styles.tag}>
                          <Text style={styles.tagText}>{tag}</Text>
                        </View>
                      ))}
                    </View>
                  </View>
                </Card.Body>
              </Card>
            </View>
          </TouchableOpacity>
          {index < photos.length - 1 && <View style={styles.timelineLine} />}
        </View>
      ))}
    </View>
  );

  const renderCompareView = () => (
    <View style={styles.compareContainer}>
      <Text style={styles.compareTitle}>Before & After Comparison</Text>
      <WhiteSpace size="lg" />
      
      <View style={styles.comparePhotos}>
        <View style={styles.comparePhotoContainer}>
          <Text style={styles.compareLabel}>Before</Text>
          {comparePhotos[0] ? (
            <>
              {comparePhotos[0].uri ? (
                <Image source={{ uri: comparePhotos[0].uri }} style={styles.compareImage} />
              ) : (
                <View style={styles.compareImagePlaceholder}>
                  <MaterialIcons name="image" size={60} color="#D1D5DB" />
                </View>
              )}
              <Text style={styles.compareDate}>
                {new Date(comparePhotos[0].date).toLocaleDateString()}
              </Text>
            </>
          ) : (
            <View style={styles.compareImagePlaceholder}>
              <MaterialIcons name="add-photo-alternate" size={60} color="#9CA3AF" />
              <Text style={styles.comparePlaceholderText}>Select photo</Text>
            </View>
          )}
        </View>

        <View style={styles.compareArrow}>
          <MaterialIcons name="arrow-forward" size={32} color="#3B82F6" />
        </View>

        <View style={styles.comparePhotoContainer}>
          <Text style={styles.compareLabel}>After</Text>
          {comparePhotos[1] ? (
            <>
              {comparePhotos[1].uri ? (
                <Image source={{ uri: comparePhotos[1].uri }} style={styles.compareImage} />
              ) : (
                <View style={styles.compareImagePlaceholder}>
                  <MaterialIcons name="image" size={60} color="#D1D5DB" />
                </View>
              )}
              <Text style={styles.compareDate}>
                {new Date(comparePhotos[1].date).toLocaleDateString()}
              </Text>
            </>
          ) : (
            <View style={styles.compareImagePlaceholder}>
              <MaterialIcons name="add-photo-alternate" size={60} color="#9CA3AF" />
              <Text style={styles.comparePlaceholderText}>Select photo</Text>
            </View>
          )}
        </View>
      </View>

      <WhiteSpace size="lg" />
      
      <Button
        type="ghost"
        onPress={toggleCompareMode}
        style={styles.exitCompareButton}
      >
        Exit Compare Mode
      </Button>
    </View>
  );


  if (photos.length === 0) {
    return (
      <View style={styles.emptyContainer}>
        <WingBlank size="lg">
          <View style={styles.emptyContent}>
            <Text style={styles.emptyIcon}>📸</Text>
            <Text style={styles.emptyTitle}>No Progress Photos Yet</Text>
            <Text style={styles.emptyText}>
              Start tracking your skincare journey by taking your first photo
            </Text>
            
            <WhiteSpace size="xl" />
            
            <Button
              type="primary"
              onPress={handleTakePhoto}
              style={styles.button}
            >
              <MaterialIcons name="camera-alt" size={16} color="#FFFFFF" />
              <Text style={styles.buttonText}> Take Photo</Text>
            </Button>
            
            <WhiteSpace size="md" />
            
            <Button
              type="ghost"
              onPress={handleSelectFromGallery}
              style={styles.button}
            >
              <MaterialIcons name="photo-library" size={16} color="#3B82F6" />
              <Text style={styles.ghostButtonText}> Choose from Gallery</Text>
            </Button>
          </View>
        </WingBlank>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <WingBlank size="lg">
          {/* Header Controls */}
          <Card>
            <Card.Body>
              <View style={styles.controls}>
                <View style={styles.viewModeToggle}>
                  <TouchableOpacity
                    style={[styles.viewModeButton, viewMode === 'grid' && styles.viewModeButtonActive]}
                    onPress={() => setViewMode('grid')}
                  >
                    <MaterialIcons
                      name="grid-view"
                      size={20}
                      color={viewMode === 'grid' ? '#3B82F6' : '#6B7280'}
                    />
                  </TouchableOpacity>
                  
                  <TouchableOpacity
                    style={[styles.viewModeButton, viewMode === 'timeline' && styles.viewModeButtonActive]}
                    onPress={() => setViewMode('timeline')}
                  >
                    <MaterialIcons
                      name="timeline"
                      size={20}
                      color={viewMode === 'timeline' ? '#3B82F6' : '#6B7280'}
                    />
                  </TouchableOpacity>
                </View>

                <TouchableOpacity
                  style={[styles.compareButton, compareMode && styles.compareButtonActive]}
                  onPress={toggleCompareMode}
                >
                  <Ionicons
                    name="git-compare"
                    size={20}
                    color={compareMode ? '#FFFFFF' : '#3B82F6'}
                  />
                  <Text style={[
                    styles.compareButtonText,
                    compareMode && styles.compareButtonTextActive
                  ]}>
                    Compare
                  </Text>
                </TouchableOpacity>
              </View>
            </Card.Body>
          </Card>

          <WhiteSpace size="lg" />

          {/* Privacy Toggle */}
          <Card>
            <Card.Body>
              <View style={styles.privacyControl}>
                <View style={styles.privacyInfo}>
                  <MaterialIcons name="lock" size={20} color="#6B7280" />
                  <Text style={styles.privacyLabel}>Keep photos private</Text>
                </View>
                <Switch
                  checked={isPrivate}
                  onChange={setIsPrivate}
                />
              </View>
              <WhiteSpace size="xs" />
              <Text style={styles.privacyDescription}>
                Private photos are only visible to you
              </Text>
            </Card.Body>
          </Card>

          <WhiteSpace size="lg" />

          {/* Photo Count */}
          <Text style={styles.photoCount}>
            {photos.length} {photos.length === 1 ? 'photo' : 'photos'}
          </Text>
          
          <WhiteSpace size="md" />

          {/* Content */}
          {compareMode && comparePhotos[0] && comparePhotos[1] ? (
            renderCompareView()
          ) : viewMode === 'grid' ? (
            renderPhotoGrid()
          ) : (
            renderTimeline()
          )}

          <WhiteSpace size="xl" />

          {/* Action Buttons */}
          {!compareMode && (
            <View style={styles.actionButtons}>
              <Button
                type="primary"
                onPress={handleTakePhoto}
                style={[styles.button, { flex: 1, marginRight: 8 }]}
              >
                <MaterialIcons name="camera-alt" size={16} color="#FFFFFF" />
                <Text style={styles.buttonText}> Take Photo</Text>
              </Button>
              
              <Button
                type="ghost"
                onPress={handleSelectFromGallery}
                style={[styles.button, { flex: 1, marginLeft: 8 }]}
              >
                <MaterialIcons name="photo-library" size={16} color="#3B82F6" />
              </Button>
            </View>
          )}
        </WingBlank>
      </ScrollView>

      {/* Photo Detail Modal */}
      <Modal
        visible={!!selectedPhoto && !compareMode}
        transparent
        onClose={() => setSelectedPhoto(null)}
        animationType="slide-up"
      >
        {selectedPhoto && (
          <View style={styles.modalContent}>
            {selectedPhoto.uri ? (
              <Image source={{ uri: selectedPhoto.uri }} style={styles.modalImage} />
            ) : (
              <View style={styles.modalImagePlaceholder}>
                <MaterialIcons name="image" size={80} color="#D1D5DB" />
              </View>
            )}
            
            <WhiteSpace size="lg" />
            
            <Text style={styles.modalDate}>
              {new Date(selectedPhoto.date).toLocaleDateString('en-US', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric',
              })}
            </Text>
            
            {selectedPhoto.note && (
              <>
                <WhiteSpace size="md" />
                <Text style={styles.modalNote}>{selectedPhoto.note}</Text>
              </>
            )}
            
            <WhiteSpace size="lg" />
            
            <View style={styles.modalActions}>
              <Button
                type="ghost"
                onPress={() => handleDeletePhoto(selectedPhoto.id)}
                style={styles.deleteButton}
              >
                <MaterialIcons name="delete" size={16} color="#EF4444" />
                <Text style={styles.deleteButtonText}> Delete</Text>
              </Button>
              
              <Button
                type="primary"
                onPress={() => setSelectedPhoto(null)}
                style={styles.closeButton}
              >
                Close
              </Button>
            </View>
          </View>
        )}
      </Modal>
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
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    backgroundColor: '#FAFAFA',
  },
  emptyContent: {
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
  controls: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  viewModeToggle: {
    flexDirection: 'row',
    backgroundColor: '#F9FAFB',
    borderRadius: 8,
    padding: 4,
  },
  viewModeButton: {
    padding: 8,
    borderRadius: 6,
  },
  viewModeButtonActive: {
    backgroundColor: '#FFFFFF',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  compareButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#3B82F6',
    gap: 6,
  },
  compareButtonActive: {
    backgroundColor: '#3B82F6',
  },
  compareButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#3B82F6',
  },
  compareButtonTextActive: {
    color: '#FFFFFF',
  },
  privacyControl: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  privacyInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  privacyLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1F2937',
  },
  privacyDescription: {
    fontSize: 12,
    color: '#6B7280',
  },
  photoCount: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6B7280',
  },
  photoGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  photoItem: {
    width: PHOTO_SIZE,
    height: PHOTO_SIZE,
    borderRadius: 8,
    overflow: 'hidden',
    position: 'relative',
  },
  photoItemSelected: {
    borderWidth: 3,
    borderColor: '#10B981',
  },
  photoImage: {
    width: '100%',
    height: '100%',
    resizeMode: 'cover',
  },
  photoPlaceholder: {
    width: '100%',
    height: '100%',
    backgroundColor: '#F3F4F6',
    justifyContent: 'center',
    alignItems: 'center',
  },
  photoOverlay: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
    padding: 6,
  },
  photoDate: {
    fontSize: 10,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  selectedBadge: {
    position: 'absolute',
    top: 4,
    right: 4,
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
  },
  timeline: {
    paddingLeft: 8,
  },
  timelineItem: {
    flexDirection: 'row',
    position: 'relative',
  },
  timelineDate: {
    width: 80,
    paddingTop: 8,
  },
  timelineDateText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#6B7280',
  },
  timelineDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: '#3B82F6',
    marginTop: 12,
    marginHorizontal: 12,
  },
  timelineLine: {
    position: 'absolute',
    left: 97,
    top: 24,
    bottom: -16,
    width: 2,
    backgroundColor: '#E5E7EB',
  },
  timelineContent: {
    flex: 1,
  },
  timelineCard: {
    paddingVertical: 8,
  },
  timelineImage: {
    width: '100%',
    height: 200,
    borderRadius: 8,
    resizeMode: 'cover',
  },
  timelineImagePlaceholder: {
    width: '100%',
    height: 200,
    backgroundColor: '#F3F4F6',
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  timelineNote: {
    fontSize: 14,
    color: '#1F2937',
    lineHeight: 20,
  },
  timelineTags: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  tag: {
    backgroundColor: '#EFF6FF',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  tagText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#3B82F6',
  },
  compareContainer: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 20,
  },
  compareTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1F2937',
    textAlign: 'center',
  },
  comparePhotos: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  comparePhotoContainer: {
    flex: 1,
    alignItems: 'center',
  },
  compareLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#6B7280',
    marginBottom: 8,
  },
  compareImage: {
    width: '100%',
    height: 180,
    borderRadius: 8,
    resizeMode: 'cover',
  },
  compareImagePlaceholder: {
    width: '100%',
    height: 180,
    backgroundColor: '#F3F4F6',
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  comparePlaceholderText: {
    fontSize: 12,
    color: '#9CA3AF',
    marginTop: 8,
  },
  compareDate: {
    fontSize: 11,
    color: '#6B7280',
    marginTop: 6,
  },
  compareArrow: {
    paddingHorizontal: 12,
  },
  exitCompareButton: {
    borderRadius: 8,
  },
  actionButtons: {
    flexDirection: 'row',
  },
  button: {
    borderRadius: 8,
    height: 44,
  },
  buttonText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  ghostButtonText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#3B82F6',
  },
  modalContent: {
    padding: 20,
  },
  modalImage: {
    width: '100%',
    height: 300,
    borderRadius: 12,
    resizeMode: 'cover',
  },
  modalImagePlaceholder: {
    width: '100%',
    height: 300,
    backgroundColor: '#F3F4F6',
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalDate: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1F2937',
    textAlign: 'center',
  },
  modalNote: {
    fontSize: 14,
    color: '#6B7280',
    textAlign: 'center',
    lineHeight: 20,
  },
  modalActions: {
    flexDirection: 'row',
    gap: 12,
  },
  deleteButton: {
    flex: 1,
    borderRadius: 8,
    borderColor: '#FEE2E2',
  },
  deleteButtonText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#EF4444',
  },
  closeButton: {
    flex: 1,
    borderRadius: 8,
  },
});
