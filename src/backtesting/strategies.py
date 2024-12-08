import pandas as pd
import numpy as np
from typing import Dict, Any
import logging
from src.backtesting.strategy_base import StrategyBase

logger = logging.getLogger(__name__)

class SimpleMovingAverageCrossover(StrategyBase):
    """Estrategia de cruce de medias móviles."""
    
    def __init__(self, data: pd.DataFrame, fast_period: int = 20, slow_period: int = 50, **kwargs):
        """
        Inicializa la estrategia.
        
        Args:
            data: DataFrame con datos OHLCV
            fast_period: Periodo de la media rápida
            slow_period: Periodo de la media lenta
        """
        super().__init__(data, **kwargs)
        self.fast_period = fast_period
        self.slow_period = slow_period
        
    async def generate_signals(self) -> pd.Series:
        """Genera señales basadas en cruce de medias móviles."""
        try:
            # Calcular medias móviles
            fast_ma = self.data['close'].rolling(window=self.fast_period).mean()
            slow_ma = self.data['close'].rolling(window=self.slow_period).mean()
            
            # Generar señales
            signals = pd.Series(0, index=self.data.index)
            signals[fast_ma > slow_ma] = 1  # Señal de compra
            signals[fast_ma < slow_ma] = -1  # Señal de venta
            
            return signals
            
        except Exception as e:
            logger.error(f"Error generando señales SMA: {str(e)}")
            return pd.Series(0, index=self.data.index)
            
class RSIStrategy(StrategyBase):
    """Estrategia basada en RSI."""
    
    def __init__(self, data: pd.DataFrame, period: int = 14, oversold: int = 30, overbought: int = 70, **kwargs):
        """
        Inicializa la estrategia.
        
        Args:
            data: DataFrame con datos OHLCV
            period: Periodo del RSI
            oversold: Nivel de sobreventa
            overbought: Nivel de sobrecompra
        """
        super().__init__(data, **kwargs)
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        
    async def generate_signals(self) -> pd.Series:
        """Genera señales basadas en RSI."""
        try:
            # Calcular RSI
            delta = self.data['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=self.period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            # Generar señales
            signals = pd.Series(0, index=self.data.index)
            signals[rsi < self.oversold] = 1  # Señal de compra
            signals[rsi > self.overbought] = -1  # Señal de venta
            
            return signals
            
        except Exception as e:
            logger.error(f"Error generando señales RSI: {str(e)}")
            return pd.Series(0, index=self.data.index)
            
class MACDStrategy(StrategyBase):
    """Estrategia basada en MACD."""
    
    def __init__(self, data: pd.DataFrame, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9, **kwargs):
        """
        Inicializa la estrategia.
        
        Args:
            data: DataFrame con datos OHLCV
            fast_period: Periodo EMA rápida
            slow_period: Periodo EMA lenta
            signal_period: Periodo de la señal
        """
        super().__init__(data, **kwargs)
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        
    async def generate_signals(self) -> pd.Series:
        """Genera señales basadas en MACD."""
        try:
            # Calcular MACD
            exp1 = self.data['close'].ewm(span=self.fast_period, adjust=False).mean()
            exp2 = self.data['close'].ewm(span=self.slow_period, adjust=False).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=self.signal_period, adjust=False).mean()
            
            # Generar señales
            signals = pd.Series(0, index=self.data.index)
            signals[macd > signal] = 1  # Señal de compra
            signals[macd < signal] = -1  # Señal de venta
            
            return signals
            
        except Exception as e:
            logger.error(f"Error generando señales MACD: {str(e)}")
            return pd.Series(0, index=self.data.index) 