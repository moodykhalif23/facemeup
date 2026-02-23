"""
Data loader for skin analysis dataset.
Handles ISIC dataset, Bitmoji exports, and preprocessing.
"""

import os
import yaml
import numpy as np
from pathlib import Path
from typing import Tuple, List
import tensorflow as tf
from tensorflow import keras


class SkinDataLoader:
    """Load and preprocess skin analysis training data."""
    
    def __init__(self, config_path: str = "ml/config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.dataset_config = self.config['dataset']
        self.model_config = self.config['model']
        self.image_size = tuple(self.dataset_config['image_size'])
        self.batch_size = self.dataset_config['batch_size']
        
        # Class labels
        self.skin_types = self.model_config['skin_types']
        self.conditions = self.model_config['conditions']
        self.num_classes = len(self.skin_types) + len(self.conditions)
        
    def load_isic_dataset(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Load ISIC dataset.
        For now, returns dummy data. Replace with actual ISIC loading.
        """
        print("Loading ISIC dataset...")
        isic_path = Path(self.dataset_config['isic_path'])
        
        if not isic_path.exists():
            print(f"Warning: ISIC path {isic_path} not found. Using dummy data.")
            return self._generate_dummy_data(100)
        
        # TODO: Implement actual ISIC dataset loading
        # This is a placeholder - replace with real implementation
        images = []
        labels = []
        
        # Example: Load images from directory structure
        # for class_dir in isic_path.iterdir():
        #     if class_dir.is_dir():
        #         for img_path in class_dir.glob('*.jpg'):
        #             img = self._load_and_preprocess_image(str(img_path))
        #             images.append(img)
        #             labels.append(self._encode_label(class_dir.name))
        
        return self._generate_dummy_data(100)
    
    def load_bitmoji_dataset(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Load Bitmoji analyzer exports.
        For now, returns dummy data. Replace with actual Bitmoji loading.
        """
        print("Loading Bitmoji dataset...")
        bitmoji_path = Path(self.dataset_config['bitmoji_path'])
        
        if not bitmoji_path.exists():
            print(f"Warning: Bitmoji path {bitmoji_path} not found. Using dummy data.")
            return self._generate_dummy_data(50)
        
        # TODO: Implement actual Bitmoji dataset loading
        return self._generate_dummy_data(50)
    
    def _generate_dummy_data(self, num_samples: int) -> Tuple[np.ndarray, np.ndarray]:
        """Generate dummy data for testing."""
        print(f"Generating {num_samples} dummy samples...")
        images = np.random.rand(num_samples, *self.image_size, 3).astype(np.float32)
        labels = np.random.randint(0, self.num_classes, size=(num_samples, self.num_classes))
        labels = (labels > 0.5).astype(np.float32)  # Multi-label binary
        return images, labels
    
    def _load_and_preprocess_image(self, image_path: str) -> np.ndarray:
        """Load and preprocess a single image."""
        img = tf.io.read_file(image_path)
        img = tf.image.decode_jpeg(img, channels=3)
        img = tf.image.resize(img, self.image_size)
        img = tf.cast(img, tf.float32) / 255.0
        return img.numpy()
    
    def _encode_label(self, label_str: str) -> np.ndarray:
        """Encode string label to multi-hot vector."""
        label_vector = np.zeros(self.num_classes, dtype=np.float32)
        
        # Check skin type
        if label_str in self.skin_types:
            idx = self.skin_types.index(label_str)
            label_vector[idx] = 1.0
        
        # Check conditions
        for condition in self.conditions:
            if condition.lower() in label_str.lower():
                idx = len(self.skin_types) + self.conditions.index(condition)
                label_vector[idx] = 1.0
        
        return label_vector
    
    def create_datasets(self) -> Tuple[tf.data.Dataset, tf.data.Dataset, tf.data.Dataset]:
        """Create train, validation, and test datasets."""
        print("\nCreating datasets...")
        
        # Load all data
        isic_images, isic_labels = self.load_isic_dataset()
        bitmoji_images, bitmoji_labels = self.load_bitmoji_dataset()
        
        # Combine datasets
        all_images = np.concatenate([isic_images, bitmoji_images], axis=0)
        all_labels = np.concatenate([isic_labels, bitmoji_labels], axis=0)
        
        # Shuffle
        indices = np.random.permutation(len(all_images))
        all_images = all_images[indices]
        all_labels = all_labels[indices]
        
        # Split
        train_split = self.dataset_config['train_split']
        val_split = self.dataset_config['val_split']
        
        n_train = int(len(all_images) * train_split)
        n_val = int(len(all_images) * val_split)
        
        train_images = all_images[:n_train]
        train_labels = all_labels[:n_train]
        
        val_images = all_images[n_train:n_train + n_val]
        val_labels = all_labels[n_train:n_train + n_val]
        
        test_images = all_images[n_train + n_val:]
        test_labels = all_labels[n_train + n_val:]
        
        print(f"Train samples: {len(train_images)}")
        print(f"Validation samples: {len(val_images)}")
        print(f"Test samples: {len(test_images)}")
        
        # Create TensorFlow datasets
        train_ds = self._create_tf_dataset(train_images, train_labels, augment=True)
        val_ds = self._create_tf_dataset(val_images, val_labels, augment=False)
        test_ds = self._create_tf_dataset(test_images, test_labels, augment=False)
        
        return train_ds, val_ds, test_ds
    
    def _create_tf_dataset(self, images: np.ndarray, labels: np.ndarray, 
                          augment: bool = False) -> tf.data.Dataset:
        """Create TensorFlow dataset with optional augmentation."""
        dataset = tf.data.Dataset.from_tensor_slices((images, labels))
        
        if augment:
            dataset = dataset.map(self._augment, num_parallel_calls=tf.data.AUTOTUNE)
        
        dataset = dataset.shuffle(self.dataset_config['shuffle_buffer'])
        dataset = dataset.batch(self.batch_size)
        dataset = dataset.prefetch(tf.data.AUTOTUNE)
        
        return dataset
    
    def _augment(self, image: tf.Tensor, label: tf.Tensor) -> Tuple[tf.Tensor, tf.Tensor]:
        """Apply data augmentation."""
        aug_config = self.dataset_config['augmentation']
        
        # Random flip
        if aug_config['random_flip']:
            image = tf.image.random_flip_left_right(image)
        
        # Random rotation
        if aug_config['random_rotation']:
            angle = tf.random.uniform([], -aug_config['random_rotation'], 
                                     aug_config['random_rotation'])
            image = self._rotate_image(image, angle)
        
        # Random brightness
        if aug_config['random_brightness']:
            image = tf.image.random_brightness(image, aug_config['random_brightness'])
        
        # Random contrast
        if aug_config.get('random_contrast'):
            image = tf.image.random_contrast(image, 
                                            1 - aug_config['random_contrast'],
                                            1 + aug_config['random_contrast'])
        
        # Random zoom
        if aug_config.get('random_zoom'):
            image = self._random_zoom(image, aug_config['random_zoom'])
        
        # Clip values to [0, 1]
        image = tf.clip_by_value(image, 0.0, 1.0)
        
        return image, label
    
    def _rotate_image(self, image: tf.Tensor, angle: float) -> tf.Tensor:
        """Rotate image by angle (in radians)."""
        return tf.keras.preprocessing.image.apply_affine_transform(
            image.numpy(), theta=angle * 180 / np.pi, 
            channel_axis=2, fill_mode='nearest'
        )
    
    def _random_zoom(self, image: tf.Tensor, zoom_range: float) -> tf.Tensor:
        """Apply random zoom."""
        zoom = tf.random.uniform([], 1 - zoom_range, 1 + zoom_range)
        h, w = self.image_size
        new_h, new_w = int(h * zoom), int(w * zoom)
        image = tf.image.resize(image, [new_h, new_w])
        image = tf.image.resize_with_crop_or_pad(image, h, w)
        return image


if __name__ == "__main__":
    # Test data loader
    loader = SkinDataLoader()
    train_ds, val_ds, test_ds = loader.create_datasets()
    
    print("\nDataset created successfully!")
    print(f"Number of classes: {loader.num_classes}")
    print(f"Skin types: {loader.skin_types}")
    print(f"Conditions: {loader.conditions}")
    
    # Test batch
    for images, labels in train_ds.take(1):
        print(f"\nBatch shape: {images.shape}")
        print(f"Labels shape: {labels.shape}")
        print(f"Image range: [{images.numpy().min():.3f}, {images.numpy().max():.3f}]")
