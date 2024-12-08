import pandas as pd
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)

class MarketDataService:
    """Servicio para procesamiento de datos de mercado."""
    
    REQUIRED_COLUMNS = ['open', 'high', 'low', 'close', 'volume']
    
    @staticmethod
    def validate_dataframe(df: pd.DataFrame) -> bool:
        """
        Valida que el DataFrame tenga la estructura esperada.
        
        Args:
            df: DataFrame a validar
            
        Returns:
            bool: True si el DataFrame es válido
        """
        try:
            # Verificar columnas requeridas
            missing_cols = [col for col in MarketDataService.REQUIRED_COLUMNS 
                          if col not in df.columns]
            
            if missing_cols:
                logger.error(f"Columnas faltantes en DataFrame: {missing_cols}")
                return False
                
            # Verificar que no haya datos nulos
            null_counts = df[MarketDataService.REQUIRED_COLUMNS].isnull().sum()
            if null_counts.any():
                logger.error(f"Datos nulos encontrados: {null_counts[null_counts > 0]}")
                return False
                
            # Verificar tipos de datos
            if not pd.api.types.is_numeric_dtype(df['close']):
                logger.error("La columna 'close' no es numérica")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error validando DataFrame: {str(e)}")
            return False
            
    @staticmethod
    def process_market_data(data: Dict[str, Any]) -> Optional[pd.DataFrame]:
        """
        Procesa datos de mercado y los convierte a DataFrame.
        
        Args:
            data: Datos de mercado en formato diccionario
            
        Returns:
            DataFrame procesado o None si hay error
        """
        try:
            # Convertir a DataFrame
            df = pd.DataFrame(data)
            
            # Validar estructura
            if not MarketDataService.validate_dataframe(df):
                return None
                
            # Procesar índice temporal
            if 'timestamp' in df.columns:
                df.set_index('timestamp', inplace=True)
                df.index = pd.to_datetime(df.index)
                
            # Calcular campos adicionales
            df['returns'] = df['close'].pct_change()
            df['volatility'] = df['returns'].rolling(window=20).std() * np.sqrt(252)
            df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
            
            # Limpiar datos
            df = df.replace([np.inf, -np.inf], np.nan)
            df = df.fillna(method='ffill').fillna(method='bfill')
            
            return df
            
        except Exception as e:
            logger.error(f"Error procesando datos de mercado: {str(e)}")
            return None
            
    @staticmethod
    def resample_data(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        """
        Remuestrea datos a un timeframe diferente.
        
        Args:
            df: DataFrame con datos OHLCV
            timeframe: Nuevo intervalo (e.g., '1H', '4H', '1D')
            
        Returns:
            DataFrame remuestreado
        """
        try:
            resampled = pd.DataFrame()
            
            # Reglas de agregación por columna
            resampled['open'] = df['open'].resample(timeframe).first()
            resampled['high'] = df['high'].resample(timeframe).max()
            resampled['low'] = df['low'].resample(timeframe).min()
            resampled['close'] = df['close'].resample(timeframe).last()
            resampled['volume'] = df['volume'].resample(timeframe).sum()
            
            # Recalcular campos derivados
            resampled['returns'] = resampled['close'].pct_change()
            resampled['volatility'] = resampled['returns'].rolling(window=20).std() * np.sqrt(252)
            resampled['typical_price'] = (resampled['high'] + resampled['low'] + resampled['close']) / 3
            
            return resampled
            
        except Exception as e:
            logger.error(f"Error remuestreando datos: {str(e)}")
            raise 