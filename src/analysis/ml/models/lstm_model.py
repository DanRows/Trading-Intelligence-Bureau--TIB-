import numpy as np
import pandas as pd
from typing import Dict, Any
import tensorflow as tf
import joblib
from pathlib import Path
from ..base_model import BaseMLModel

class LSTMPricePredictor(BaseMLModel):
    """Predictor de precios usando LSTM."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.sequence_length = config.get('sequence_length', 60)
        self.features = config.get('features', ['close', 'volume', 'rsi'])
        self.batch_size = config.get('batch_size', 32)
        self.epochs = config.get('epochs', 100)
        self._build_model()
        
    def _build_model(self) -> None:
        """Construye la arquitectura del modelo LSTM."""
        self.model = tf.keras.Sequential([
            tf.keras.layers.LSTM(50, return_sequences=True, 
                               input_shape=(self.sequence_length, len(self.features))),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.LSTM(50, return_sequences=False),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(1)
        ])
        
        self.model.compile(
            optimizer='adam',
            loss='mse',
            metrics=['mae']
        )
        
    async def preprocess(self, data: pd.DataFrame) -> np.ndarray:
        """
        Preprocesa los datos para el LSTM.
        
        Args:
            data: DataFrame con los datos crudos
            
        Returns:
            np.ndarray: Datos preprocesados
        """
        # Verificar features requeridos
        missing_features = [f for f in self.features if f not in data.columns]
        if missing_features:
            raise ValueError(f"Missing features: {missing_features}")
            
        # Normalización
        scaled_data = {}
        for feature in self.features:
            mean = data[feature].mean()
            std = data[feature].std()
            scaled_data[feature] = (data[feature] - mean) / std
            
        # Crear secuencias
        sequences = []
        targets = []
        for i in range(len(data) - self.sequence_length):
            seq = [scaled_data[f][i:(i + self.sequence_length)] 
                  for f in self.features]
            sequences.append(np.column_stack(seq))
            targets.append(scaled_data['close'][i + self.sequence_length])
            
        return np.array(sequences), np.array(targets)
        
    async def train(self, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """
        Entrena el modelo LSTM.
        
        Args:
            X: Datos de entrenamiento
            y: Valores objetivo
            
        Returns:
            Dict con historial de entrenamiento
        """
        # Validación
        validation_split = self.config.get('validation_split', 0.2)
        
        # Callbacks
        callbacks = [
            tf.keras.callbacks.EarlyStopping(
                monitor='val_loss',
                patience=10,
                restore_best_weights=True
            ),
            tf.keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=5,
                min_lr=1e-6
            )
        ]
        
        # Entrenamiento
        history = self.model.fit(
            X, y,
            batch_size=self.batch_size,
            epochs=self.epochs,
            validation_split=validation_split,
            callbacks=callbacks,
            verbose=1
        )
        
        self.is_trained = True
        return history.history
        
    async def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Realiza predicciones.
        
        Args:
            X: Datos de entrada
            
        Returns:
            np.ndarray: Predicciones
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
            
        predictions = self.model.predict(X)
        
        # Desnormalizar predicciones
        mean = self.config.get('close_mean', 0)
        std = self.config.get('close_std', 1)
        return predictions * std + mean
        
    def _save_model(self, path: str) -> None:
        """
        Guarda el modelo y sus configuraciones.
        
        Args:
            path: Ruta donde guardar el modelo
        """
        save_path = Path(path)
        
        # Guardar pesos del modelo
        weights_path = save_path.parent / f"{save_path.stem}_weights.h5"
        self.model.save_weights(str(weights_path))
        
        # Guardar configuración y otros datos
        config_data = {
            'config': self.config,
            'sequence_length': self.sequence_length,
            'features': self.features,
            'is_trained': self.is_trained
        }
        
        joblib.dump(config_data, path)
        
    def _load_model(self, path: str) -> None:
        """
        Carga el modelo y sus configuraciones.
        
        Args:
            path: Ruta del modelo guardado
        """
        load_path = Path(path)
        
        # Cargar configuración
        config_data = joblib.load(path)
        self.config = config_data['config']
        self.sequence_length = config_data['sequence_length']
        self.features = config_data['features']
        self.is_trained = config_data['is_trained']
        
        # Reconstruir modelo
        self._build_model()
        
        # Cargar pesos
        weights_path = load_path.parent / f"{load_path.stem}_weights.h5"
        self.model.load_weights(str(weights_path)) 