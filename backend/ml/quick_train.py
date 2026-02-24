#!/usr/bin/env python3
"""Quick training script with dummy data for testing the pipeline"""

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Reduce TF logging

import numpy as np
import tensorflow as tf
from pathlib import Path

print("=" * 60)
print("Quick ML Training - Dummy Data")
print("=" * 60)

# Configuration
IMG_SIZE = 224
BATCH_SIZE = 16
EPOCHS = 5
NUM_SAMPLES = 500

# Output classes
SKIN_TYPES = ["Oily", "Dry", "Combination", "Normal", "Sensitive"]
CONDITIONS = ["Acne", "Hyperpigmentation", "Uneven tone", "Dehydration", "None detected"]
NUM_CLASSES = len(SKIN_TYPES) + len(CONDITIONS)

print(f"\nConfiguration:")
print(f"  Image Size: {IMG_SIZE}x{IMG_SIZE}")
print(f"  Batch Size: {BATCH_SIZE}")
print(f"  Epochs: {EPOCHS}")
print(f"  Classes: {NUM_CLASSES} ({len(SKIN_TYPES)} skin types + {len(CONDITIONS)} conditions)")

# Create dummy dataset
print(f"\nGenerating {NUM_SAMPLES} dummy samples...")
X_train = np.random.rand(NUM_SAMPLES, IMG_SIZE, IMG_SIZE, 3).astype(np.float32)
y_train = tf.keras.utils.to_categorical(
    np.random.randint(0, NUM_CLASSES, NUM_SAMPLES),
    num_classes=NUM_CLASSES
)

X_val = np.random.rand(100, IMG_SIZE, IMG_SIZE, 3).astype(np.float32)
y_val = tf.keras.utils.to_categorical(
    np.random.randint(0, NUM_CLASSES, 100),
    num_classes=NUM_CLASSES
)

print(f"  Training samples: {len(X_train)}")
print(f"  Validation samples: {len(X_val)}")

# Build model
print("\nBuilding EfficientNetB0 model...")
base_model = tf.keras.applications.EfficientNetB0(
    include_top=False,
    weights='imagenet',
    input_shape=(IMG_SIZE, IMG_SIZE, 3)
)
base_model.trainable = False  # Freeze base model

model = tf.keras.Sequential([
    base_model,
    tf.keras.layers.GlobalAveragePooling2D(),
    tf.keras.layers.BatchNormalization(),
    tf.keras.layers.Dense(256, activation='relu'),
    tf.keras.layers.Dropout(0.4),
    tf.keras.layers.Dense(NUM_CLASSES, activation='softmax')
])

model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
    loss='categorical_crossentropy',
    metrics=['accuracy']
)

print(f"\nModel Summary:")
print(f"  Total params: {model.count_params():,}")
print(f"  Trainable params: {sum([tf.size(w).numpy() for w in model.trainable_weights]):,}")

# Train model
print(f"\nTraining for {EPOCHS} epochs...")
history = model.fit(
    X_train, y_train,
    validation_data=(X_val, y_val),
    batch_size=BATCH_SIZE,
    epochs=EPOCHS,
    verbose=1
)

# Save model
print("\nSaving model...")
checkpoint_dir = Path("ml/checkpoints")
checkpoint_dir.mkdir(parents=True, exist_ok=True)
model_path = checkpoint_dir / "quick_model.h5"
model.save(model_path)
print(f"  ✓ Saved to: {model_path}")

# Export to SavedModel
print("\nExporting to SavedModel format...")
saved_model_dir = Path("app/models_artifacts/saved_model")
saved_model_dir.mkdir(parents=True, exist_ok=True)
model.export(str(saved_model_dir))
print(f"  ✓ Exported to: {saved_model_dir}")

# Test inference
print("\nTesting inference...")
test_image = np.random.rand(1, IMG_SIZE, IMG_SIZE, 3).astype(np.float32)
predictions = model.predict(test_image, verbose=0)
print(f"  Prediction shape: {predictions.shape}")
print(f"  Sample probabilities: {predictions[0][:5]}")

print("\n" + "=" * 60)
print("Training Complete!")
print("=" * 60)
print(f"\nNext steps:")
print(f"1. Restart backend: docker-compose restart api")
print(f"2. Test analysis endpoint in the app")
print(f"3. For production: Train with real ISIC dataset")
print("=" * 60)
