"""
Model builder for EfficientNetB0 skin analysis classifier.
"""

import yaml
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, models
from typing import Tuple


class SkinAnalysisModel:
    """Build and configure EfficientNetB0 model for skin analysis."""
    
    def __init__(self, config_path: str = "ml/config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.model_config = self.config['model']
        self.arch_config = self.config['architecture']
        self.input_size = self.model_config['input_size']
        
        # Calculate number of classes
        self.num_skin_types = len(self.model_config['skin_types'])
        self.num_conditions = len(self.model_config['conditions'])
        self.num_classes = self.num_skin_types + self.num_conditions
    
    def build_model(self, phase: int = 1) -> keras.Model:
        """
        Build EfficientNetB0 model.
        
        Args:
            phase: 1 for feature extraction, 2 for fine-tuning
        
        Returns:
            Compiled Keras model
        """
        print(f"\nBuilding model for Phase {phase}...")
        
        # Input layer
        inputs = layers.Input(shape=(self.input_size, self.input_size, 3))
        
        # Load pre-trained EfficientNetB0
        base_model = keras.applications.EfficientNetB0(
            include_top=self.model_config['include_top'],
            weights=self.model_config['weights'],
            input_tensor=inputs,
            pooling=None
        )
        
        # Freeze/unfreeze layers based on phase
        if phase == 1:
            # Phase 1: Freeze all base layers
            base_model.trainable = False
            print(f"Phase 1: All base layers frozen")
        else:
            # Phase 2: Unfreeze top layers
            base_model.trainable = True
            unfreeze_layers = self.config['training']['phase2']['unfreeze_layers']
            
            # Freeze all layers first
            for layer in base_model.layers:
                layer.trainable = False
            
            # Unfreeze top N layers
            for layer in base_model.layers[-unfreeze_layers:]:
                layer.trainable = True
            
            trainable_count = sum([1 for layer in base_model.layers if layer.trainable])
            print(f"Phase 2: Unfroze top {trainable_count} layers")
        
        # Get base model output
        x = base_model.output
        
        # Custom classification head
        x = self._build_classification_head(x)
        
        # Create model
        model = models.Model(inputs=inputs, outputs=x, name="EfficientNetB0_SkinAnalysis")
        
        # Compile model
        model = self._compile_model(model, phase)
        
        # Print summary
        print(f"\nModel built successfully!")
        print(f"Total parameters: {model.count_params():,}")
        trainable_params = sum([tf.size(w).numpy() for w in model.trainable_weights])
        print(f"Trainable parameters: {trainable_params:,}")
        
        return model
    
    def _build_classification_head(self, x: tf.Tensor) -> tf.Tensor:
        """Build custom classification head."""
        # Global pooling
        if self.arch_config['global_pooling'] == 'average':
            x = layers.GlobalAveragePooling2D(name='global_avg_pool')(x)
        else:
            x = layers.GlobalMaxPooling2D(name='global_max_pool')(x)
        
        # Batch normalization
        if self.arch_config['batch_normalization']:
            x = layers.BatchNormalization(name='bn_head')(x)
        
        # Dense layer
        x = layers.Dense(
            self.arch_config['dense_units'],
            activation=self.arch_config['dense_activation'],
            name='dense_head'
        )(x)
        
        # Dropout
        if self.arch_config['dropout_rate'] > 0:
            x = layers.Dropout(self.arch_config['dropout_rate'], name='dropout_head')(x)
        
        # Output layer (multi-label classification)
        outputs = layers.Dense(
            self.num_classes,
            activation=self.arch_config['output_activation'],
            name='output'
        )(x)
        
        return outputs
    
    def _compile_model(self, model: keras.Model, phase: int) -> keras.Model:
        """Compile model with appropriate optimizer and loss."""
        # Get training config for phase
        if phase == 1:
            train_config = self.config['training']['phase1']
        else:
            train_config = self.config['training']['phase2']
        
        # Optimizer
        if train_config['optimizer'].lower() == 'adam':
            optimizer = keras.optimizers.Adam(learning_rate=train_config['learning_rate'])
        elif train_config['optimizer'].lower() == 'sgd':
            optimizer = keras.optimizers.SGD(
                learning_rate=train_config['learning_rate'],
                momentum=0.9
            )
        else:
            raise ValueError(f"Unknown optimizer: {train_config['optimizer']}")
        
        # Loss function
        loss_config = self.config['loss']
        if loss_config['function'] == 'categorical_crossentropy':
            loss = keras.losses.CategoricalCrossentropy()
        elif loss_config['function'] == 'binary_crossentropy':
            loss = keras.losses.BinaryCrossentropy()
        else:
            loss = loss_config['function']
        
        # Metrics
        metrics = []
        for metric_name in self.config['metrics']:
            if metric_name == 'accuracy':
                metrics.append(keras.metrics.CategoricalAccuracy(name='accuracy'))
            elif metric_name == 'precision':
                metrics.append(keras.metrics.Precision(name='precision'))
            elif metric_name == 'recall':
                metrics.append(keras.metrics.Recall(name='recall'))
        
        # Compile
        model.compile(
            optimizer=optimizer,
            loss=loss,
            metrics=metrics
        )
        
        print(f"\nModel compiled with:")
        print(f"  Optimizer: {train_config['optimizer']} (lr={train_config['learning_rate']})")
        print(f"  Loss: {loss_config['function']}")
        print(f"  Metrics: {self.config['metrics']}")
        
        return model
    
    def get_callbacks(self, phase: int) -> list:
        """Get training callbacks."""
        # Get training config for phase
        if phase == 1:
            train_config = self.config['training']['phase1']
        else:
            train_config = self.config['training']['phase2']
        
        log_config = self.config['logging']
        
        callbacks = []
        
        # Model checkpoint
        checkpoint_path = f"{log_config['checkpoint_dir']}/phase{phase}_best_model.h5"
        callbacks.append(
            keras.callbacks.ModelCheckpoint(
                checkpoint_path,
                monitor='val_loss',
                save_best_only=log_config['save_best_only'],
                mode='min',
                verbose=log_config['verbose']
            )
        )
        
        # Early stopping
        callbacks.append(
            keras.callbacks.EarlyStopping(
                monitor='val_loss',
                patience=train_config['early_stopping_patience'],
                restore_best_weights=True,
                verbose=log_config['verbose']
            )
        )
        
        # Reduce learning rate on plateau
        callbacks.append(
            keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=train_config['reduce_lr_factor'],
                patience=train_config['reduce_lr_patience'],
                min_lr=1e-7,
                verbose=log_config['verbose']
            )
        )
        
        # TensorBoard
        tensorboard_dir = f"{log_config['tensorboard_dir']}/phase{phase}"
        callbacks.append(
            keras.callbacks.TensorBoard(
                log_dir=tensorboard_dir,
                histogram_freq=1,
                write_graph=True,
                write_images=False
            )
        )
        
        # CSV logger
        csv_path = f"{log_config['checkpoint_dir']}/phase{phase}_training.csv"
        callbacks.append(
            keras.callbacks.CSVLogger(csv_path)
        )
        
        print(f"\nCallbacks configured:")
        print(f"  - ModelCheckpoint: {checkpoint_path}")
        print(f"  - EarlyStopping (patience={train_config['early_stopping_patience']})")
        print(f"  - ReduceLROnPlateau (patience={train_config['reduce_lr_patience']})")
        print(f"  - TensorBoard: {tensorboard_dir}")
        print(f"  - CSVLogger: {csv_path}")
        
        return callbacks


if __name__ == "__main__":
    # Test model builder
    builder = SkinAnalysisModel()
    
    # Build Phase 1 model
    model_phase1 = builder.build_model(phase=1)
    print("\n" + "="*80)
    print("PHASE 1 MODEL SUMMARY")
    print("="*80)
    model_phase1.summary()
    
    # Build Phase 2 model
    model_phase2 = builder.build_model(phase=2)
    print("\n" + "="*80)
    print("PHASE 2 MODEL SUMMARY")
    print("="*80)
    model_phase2.summary()
