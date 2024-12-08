from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
import logging
import joblib
from pathlib import Path

logger = logging.getLogger(__name__)

class BaseMLModel(ABC):
    """Clase base para modelos de ML."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa el modelo base.
        
        Args:
            config: Diccionario de configuración del modelo
        """
        self.config = config
        self.model = None
        self.is_trained = False
        self.scaler = None
        
    @abstractmethod
    async def preprocess(self, data: pd.DataFrame) -> np.ndarray:
        """
        Preprocesa los datos para el modelo.
        
        Args:
            data: DataFrame con los datos crudos
            
        Returns:
            np.ndarray: Datos preprocesados
        """
        pass
        
    @abstractmethod
    async def postprocess(self, predictions: np.ndarray) -> np.ndarray:
        """
        Postprocesa las predicciones del modelo.
        
        Args:
            predictions: Predicciones crudas del modelo
            
        Returns:
            np.ndarray: Predicciones procesadas
        """
        pass
        
    @abstractmethod
    async def train(
        self, 
        X_train: np.ndarray, 
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """
        Entrena el modelo.
        
        Args:
            X_train: Datos de entrenamiento
            y_train: Etiquetas de entrenamiento
            X_val: Datos de validación
            y_val: Etiquetas de validación
            
        Returns:
            Dict con métricas del entrenamiento
        """
        pass
        
    @abstractmethod
    async def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Realiza predicciones.
        
        Args:
            X: Datos de entrada
            
        Returns:
            np.ndarray: Predicciones
        """
        pass
        
    async def save(self, path: str) -> None:
        """
        Guarda el modelo entrenado.
        
        Args:
            path: Ruta donde guardar el modelo
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before saving")
            
        try:
            save_path = Path(path)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            model_data = {
                'model': self.model,
                'config': self.config,
                'scaler': self.scaler,
                'is_trained': self.is_trained
            }
            
            joblib.dump(model_data, save_path)
            logger.info(f"Model saved to {path}")
            
        except Exception as e:
            logger.error(f"Error saving model: {e}")
            raise
            
    async def load(self, path: str) -> None:
        """
        Carga un modelo guardado.
        
        Args:
            path: Ruta del modelo guardado
        """
        try:
            model_data = joblib.load(path)
            
            self.model = model_data['model']
            self.config = model_data['config']
            self.scaler = model_data['scaler']
            self.is_trained = model_data['is_trained']
            
            logger.info(f"Model loaded from {path}")
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise 