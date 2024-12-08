import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any
import logging
from ..config.constants import Indicators

logger = logging.getLogger(__name__)

class TechnicalIndicators:
    """Clase para cálculo de indicadores técnicos."""
    
    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """
        Calcula el RSI (Relative Strength Index).
        
        Args:
            prices: Serie de precios
            period: Período para el cálculo
            
        Returns:
            Serie con valores RSI
        """
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            return 100 - (100 / (1 + rs))
        except Exception as e:
            logger.error(f"Error calculando RSI: {str(e)}")
            return pd.Series(index=prices.index)
            
    @staticmethod
    def calculate_macd(prices: pd.Series, 
                      fast_period: int = 12,
                      slow_period: int = 26,
                      signal_period: int = 9) -> Dict[str, pd.Series]:
        """
        Calcula MACD (Moving Average Convergence Divergence).
        
        Args:
            prices: Serie de precios
            fast_period: Período EMA rápida
            slow_period: Período EMA lenta
            signal_period: Período línea de señal
            
        Returns:
            Dict con 'macd', 'signal' e 'histogram'
        """
        try:
            exp1 = prices.ewm(span=fast_period, adjust=False).mean()
            exp2 = prices.ewm(span=slow_period, adjust=False).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=signal_period, adjust=False).mean()
            hist = macd - signal
            
            return {
                'macd': macd,
                'signal': signal,
                'histogram': hist
            }
        except Exception as e:
            logger.error(f"Error calculando MACD: {str(e)}")
            return {
                'macd': pd.Series(index=prices.index),
                'signal': pd.Series(index=prices.index),
                'histogram': pd.Series(index=prices.index)
            }
            
    @staticmethod
    def calculate_bollinger_bands(prices: pd.Series,
                                period: int = 20,
                                std_dev: float = 2.0) -> Dict[str, pd.Series]:
        """
        Calcula Bandas de Bollinger.
        
        Args:
            prices: Serie de precios
            period: Período para la media móvil
            std_dev: Número de desviaciones estándar
            
        Returns:
            Dict con 'upper', 'middle' y 'lower'
        """
        try:
            middle = prices.rolling(window=period).mean()
            std = prices.rolling(window=period).std()
            
            upper = middle + (std * std_dev)
            lower = middle - (std * std_dev)
            
            return {
                'upper': upper,
                'middle': middle,
                'lower': lower
            }
        except Exception as e:
            logger.error(f"Error calculando Bollinger Bands: {str(e)}")
            return {
                'upper': pd.Series(index=prices.index),
                'middle': pd.Series(index=prices.index),
                'lower': pd.Series(index=prices.index)
            }
            
    def calculate_all(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calcula todos los indicadores soportados.
        
        Args:
            df: DataFrame con datos OHLCV
            
        Returns:
            Dict con todos los indicadores calculados
        """
        try:
            results = {}
            
            # RSI
            results['rsi'] = self.calculate_rsi(df['close'])
            
            # MACD
            results.update(self.calculate_macd(df['close']))
            
            # Bollinger Bands
            results.update(self.calculate_bollinger_bands(df['close']))
            
            # EMAs
            results['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()
            results['ema_21'] = df['close'].ewm(span=21, adjust=False).mean()
            results['ema_55'] = df['close'].ewm(span=55, adjust=False).mean()
            
            return results
            
        except Exception as e:
            logger.error(f"Error calculando indicadores: {str(e)}")
            return {}