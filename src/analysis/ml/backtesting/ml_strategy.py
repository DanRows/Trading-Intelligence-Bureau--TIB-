from typing import Dict, Any
import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy
from ..base_model import BaseMLModel
import logging

logger = logging.getLogger(__name__)

class MLStrategy(BaseStrategy):
    """Estrategia de trading basada en predicciones de ML."""
    
    def __init__(self, config: Dict[str, Any], model: BaseMLModel):
        """
        Inicializa la estrategia ML.
        
        Args:
            config: Configuración de la estrategia
            model: Modelo ML entrenado
        """
        super().__init__(config)
        self.model = model
        self.threshold = config.get('threshold', 0.02)  # 2% de cambio mínimo
        
    async def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Genera señales basadas en predicciones del modelo.
        
        Args:
            data: DataFrame con datos históricos
            
        Returns:
            Series con señales de trading
        """
        try:
            # Preprocesar datos
            X, _ = await self.model.preprocess(data)
            
            # Obtener predicciones
            predictions = await self.model.predict(X)
            
            # Calcular retornos esperados
            current_prices = data['close'].iloc[:-1]  # Excluir último precio
            expected_returns = (predictions - current_prices) / current_prices
            
            # Generar señales
            signals = pd.Series(0, index=data.index[:-1])
            signals[expected_returns > self.threshold] = 1
            signals[expected_returns < -self.threshold] = -1
            
            return signals
            
        except Exception as e:
            logger.error(f"Error generando señales: {str(e)}")
            raise 