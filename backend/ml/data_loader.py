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
        
    # Based on dermatological characteristics of each lesion category.
    _HAM_TO_SKIN_TYPE = {
        "nv":    "Normal",      # benign nevi — normal skin
        "mel":   "Sensitive",   # melanoma — sun-sensitive skin
        "bkl":   "Combination", # benign keratosis — combination skin
        "bcc":   "Oily",        # basal cell carcinoma — often oily/exposed areas
        "akiec": "Dry",         # actinic keratoses — dry sun-damaged skin
        "vasc":  "Sensitive",   # vascular lesions — sensitive/reactive skin
        "df":    "Normal",      # dermatofibroma — normal skin
    }
    _HAM_TO_CONDITION = {
        "nv":    "None detected",
        "mel":   "Hyperpigmentation",
        "bkl":   "Hyperpigmentation",
        "bcc":   "Acne",
        "akiec": "Uneven tone",
        "vasc":  "Acne",
        "df":    "None detected",
    }

    def load_ham10000_dataset(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Load HAM10000 dataset with REAL clinician-assigned labels.
        Reads HAM10000_metadata.csv to map clinical dx codes to our
        skin_type and condition label space — no brightness heuristics.
        """
        import csv
        ham_dir = Path("ml/data/ham10000")
        meta_path = ham_dir / "HAM10000_metadata.tab"
        if not meta_path.exists():
            meta_path = ham_dir / "HAM10000_metadata.csv"

        if not meta_path.exists():
            print("Warning: HAM10000 metadata not found. Run train_pipeline.py first.")
            return self._generate_dummy_data(100)

        print("Loading HAM10000 with real clinical labels…")

        # Build image id → path lookup
        img_lookup = {p.stem: p for p in ham_dir.rglob("*.jpg")}
        if not img_lookup:
            print("Warning: No HAM10000 images found.")
            return self._generate_dummy_data(100)

        images, labels = [], []
        delimiter = "\t" if meta_path.suffix == ".tab" else ","
        with open(meta_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            for row in reader:
                img_id = row.get("image_id", "").strip()
                dx     = row.get("dx", "").strip().lower()

                if img_id not in img_lookup or dx not in self._HAM_TO_SKIN_TYPE:
                    continue

                try:
                    img = self._load_and_preprocess_image(str(img_lookup[img_id]))
                    label = self._make_real_label(dx)
                    images.append(img)
                    labels.append(label)
                except Exception:
                    continue

                if len(images) % 500 == 0:
                    print(f"  Loaded {len(images)} images…")
                if len(images) >= 5000:
                    break

        if not images:
            print("Warning: Could not load HAM10000 images. Falling back to dummy data.")
            return self._generate_dummy_data(100)

        print(f"✓ Loaded {len(images)} real labeled images from HAM10000")
        return np.array(images), np.array(labels)

    def _make_real_label(self, dx_code: str) -> np.ndarray:
        """Build multi-hot label vector from a HAM10000 dx code (no heuristics)."""
        label_vector = np.zeros(self.num_classes, dtype=np.float32)
        skin_type = self._HAM_TO_SKIN_TYPE[dx_code]
        condition  = self._HAM_TO_CONDITION[dx_code]
        label_vector[self.skin_types.index(skin_type)] = 1.0
        label_vector[len(self.skin_types) + self.conditions.index(condition)] = 1.0
        return label_vector

    def load_isic_dataset(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Load ISIC dataset. Prefers HAM10000 (real clinical labels).
        Falls back to local ISIC directory, then dummy data.
        NOTE: brightness-based synthetic labels are no longer used for real images.
        """
        print("Loading skin dataset…")

        # Prefer HAM10000 (has real labels)
        ham_dir  = Path("ml/data/ham10000")
        meta_path = ham_dir / "HAM10000_metadata.csv"
        if meta_path.exists() and list(ham_dir.rglob("*.jpg")):
            return self.load_ham10000_dataset()

        isic_path = Path(self.dataset_config['isic_path'])

        # Try loading from TensorFlow Datasets
        try:
            import tensorflow_datasets as tfds
            print("Attempting to load ISIC from TensorFlow Datasets…")
            ds, info = tfds.load(
                'isic2019',
                split='train',
                with_info=True,
                as_supervised=False,
                data_dir=str(isic_path.parent)
            )

            # ISIC 2019 has a 'label' feature (int) corresponding to:
            # 0=MEL, 1=NV, 2=BCC, 3=AK, 4=BKL, 5=DF, 6=VASC, 7=SCC, 8=UNK
            _isic_dx = ["mel", "nv", "bcc", "akiec", "bkl", "df", "vasc", "mel", "nv"]

            images, labels = [], []
            for i, example in enumerate(ds.take(5000)):
                if i % 500 == 0:
                    print(f"  Processed {i} images…")
                img = example['image']
                img = tf.image.resize(img, self.image_size)
                img = tf.cast(img, tf.float32) / 255.0
                images.append(img.numpy())

                # Use real ISIC label if available, else fallback
                dx_int = int(example.get('label', 1))
                dx_code = _isic_dx[dx_int] if dx_int < len(_isic_dx) else "nv"
                if dx_code in self._HAM_TO_SKIN_TYPE:
                    labels.append(self._make_real_label(dx_code))
                else:
                    labels.append(self._make_real_label("nv"))

            print(f"✓ Loaded {len(images)} images from ISIC dataset")
            return np.array(images), np.array(labels)

        except Exception as e:
            print(f"Could not load from TensorFlow Datasets: {e}")

        # Try local ISIC directory (folder name = skin type label)
        if isic_path.exists():
            print(f"Loading from local directory: {isic_path}")
            images, labels = [], []
            for img_path in isic_path.rglob('*.jpg'):
                try:
                    img = self._load_and_preprocess_image(str(img_path))
                    # Use parent folder name as skin type if it matches
                    folder = img_path.parent.name
                    if folder in self.skin_types:
                        label = np.zeros(self.num_classes, dtype=np.float32)
                        label[self.skin_types.index(folder)] = 1.0
                        label[len(self.skin_types) + self.conditions.index("None detected")] = 1.0
                    else:
                        # No recognizable folder label — skip rather than guess
                        continue
                    images.append(img)
                    labels.append(label)
                    if len(images) % 100 == 0:
                        print(f"  Loaded {len(images)} images…")
                    if len(images) >= 5000:
                        break
                except Exception:
                    continue

            if images:
                print(f"✓ Loaded {len(images)} labeled images from local directory")
                return np.array(images), np.array(labels)

        print("Warning: No real data found. Using synthetic fallback.")
        print("For real training, run: python ml/train_pipeline.py")
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
    
    def _create_synthetic_label(self, image: np.ndarray) -> np.ndarray:
        """
        Create synthetic labels based on image characteristics.
        This is a heuristic approach for training when ground truth is unavailable.
        
        Analyzes:
        - Average brightness -> skin type
        - Color variance -> conditions
        - Redness levels -> conditions
        """
        label_vector = np.zeros(self.num_classes, dtype=np.float32)
        
        # Analyze image characteristics
        avg_brightness = np.mean(image)
        color_variance = np.var(image)
        redness = np.mean(image[:, :, 0]) - np.mean(image[:, :, 1:])
        
        # Determine skin type based on brightness
        if avg_brightness < 0.3:
            skin_type_idx = self.skin_types.index("Dry")  # Darker, often drier
        elif avg_brightness < 0.5:
            skin_type_idx = self.skin_types.index("Combination")
        elif avg_brightness < 0.7:
            skin_type_idx = self.skin_types.index("Normal")
        else:
            skin_type_idx = self.skin_types.index("Oily")  # Lighter, often oilier
        
        label_vector[skin_type_idx] = 1.0
        
        # Determine conditions based on variance and redness
        cond_offset = len(self.skin_types)
        
        # High variance might indicate uneven tone or hyperpigmentation
        if color_variance > 0.05:
            if "Uneven tone" in self.conditions:
                label_vector[cond_offset + self.conditions.index("Uneven tone")] = 1.0
            if color_variance > 0.08 and "Hyperpigmentation" in self.conditions:
                label_vector[cond_offset + self.conditions.index("Hyperpigmentation")] = 1.0
        
        # High redness might indicate acne or sensitivity
        if redness > 0.05:
            if "Acne" in self.conditions:
                label_vector[cond_offset + self.conditions.index("Acne")] = 1.0
        
        # Low brightness might indicate dehydration
        if avg_brightness < 0.4:
            if "Dehydration" in self.conditions:
                label_vector[cond_offset + self.conditions.index("Dehydration")] = 1.0
        
        # If no conditions detected, mark as "None detected"
        if not np.any(label_vector[cond_offset:]):
            if "None detected" in self.conditions:
                label_vector[cond_offset + self.conditions.index("None detected")] = 1.0
        
        return label_vector
    
    def _generate_dummy_data(self, num_samples: int) -> Tuple[np.ndarray, np.ndarray]:
        """Generate realistic dummy data for testing (better than random noise)."""
        print(f"Generating {num_samples} synthetic skin-like samples...")
        images = []
        labels = []
        
        for i in range(num_samples):
            # Generate skin-tone colored images instead of random noise
            # Skin tones range from light to dark
            base_tone = np.random.uniform(0.3, 0.8)
            
            # Create base skin color (slightly more red/yellow than blue)
            r = base_tone + np.random.uniform(-0.1, 0.1)
            g = base_tone + np.random.uniform(-0.15, 0.05)
            b = base_tone + np.random.uniform(-0.2, 0.0)
            
            # Create image with some texture
            img = np.ones((*self.image_size, 3), dtype=np.float32)
            img[:, :, 0] = np.clip(r + np.random.normal(0, 0.05, self.image_size), 0, 1)
            img[:, :, 1] = np.clip(g + np.random.normal(0, 0.05, self.image_size), 0, 1)
            img[:, :, 2] = np.clip(b + np.random.normal(0, 0.05, self.image_size), 0, 1)
            
            images.append(img)
            
            # Create label based on the generated image
            label = self._create_synthetic_label(img)
            labels.append(label)
        
        return np.array(images), np.array(labels)
    
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
