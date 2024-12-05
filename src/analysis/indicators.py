import pandas as pd
import numpy as np
from typing import Dict, Tuple, List, Optional
from dataclasses import dataclass

@dataclass
class RSIResult:
    value: float
    overbought: bool
    oversold: bool

@dataclass
class MACDResult:
    macd: float
    signal: float
    histogram: float
    bullish_crossover: bool
    bearish_crossover: bool

class TechnicalIndicators:
    def __init__(self):
        self.rsi_overbought = 70
        self.rsi_oversold = 30
        
    def calculate_rsi(self, data: pd.Series, period: int = 14) -> RSIResult:
        """
        Calcula el RSI (Relative Strength Index)
        
        Args:
            data: Serie de precios de cierre
            period: Período para el cálculo
        """
        delta = data.diff()
        
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = float(rsi.iloc[-1])
        
        return RSIResult(
            value=current_rsi,
            overbought=current_rsi > self.rsi_overbought,
            oversold=current_rsi < self.rsi_oversold
        )
    
    def calculate_macd(
        self, 
        data: pd.Series,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> MACDResult:
        """
        Calcula el MACD (Moving Average Convergence Divergence)
        
        Args:
            data: Serie de precios de cierre
            fast_period: Período para la media móvil rápida
            slow_period: Período para la media móvil lenta
            signal_period: Período para la línea de señal
        """
        exp1 = data.ewm(span=fast_period, adjust=False).mean()
        exp2 = data.ewm(span=slow_period, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=signal_period, adjust=False).mean()
        histogram = macd - signal
        
        # Detectar cruces
        prev_macd = macd.iloc[-2]
        prev_signal = signal.iloc[-2]
        curr_macd = macd.iloc[-1]
        curr_signal = signal.iloc[-1]
        
        bullish_crossover = prev_macd < prev_signal and curr_macd > curr_signal
        bearish_crossover = prev_macd > prev_signal and curr_macd < curr_signal
        
        return MACDResult(
            macd=float(curr_macd),
            signal=float(curr_signal),
            histogram=float(histogram.iloc[-1]),
            bullish_crossover=bullish_crossover,
            bearish_crossover=bearish_crossover
        )
    
    def calculate_bollinger_bands(
        self, 
        data: pd.Series,
        period: int = 20,
        std_dev: float = 2.0
    ) -> Dict[str, pd.Series]:
        """
        Calcula las Bandas de Bollinger
        
        Args:
            data: Serie de precios de cierre
            period: Período para la media móvil
            std_dev: Número de desviaciones estándar
        """
        middle_band = data.rolling(window=period).mean()
        std = data.rolling(window=period).std()
        
        upper_band = middle_band + (std * std_dev)
        lower_band = middle_band - (std * std_dev)
        
        return {
            'middle': middle_band,
            'upper': upper_band,
            'lower': lower_band
        }
    
    def find_support_resistance(
        self, 
        data: pd.DataFrame,
        window: int = 20,
        threshold: float = 0.02
    ) -> Tuple[List[float], List[float]]:
        """
        Encuentra niveles de soporte y resistencia
        
        Args:
            data: DataFrame con OHLC
            window: Ventana para buscar pivotes
            threshold: Umbral para considerar un nivel válido
        """
        highs = data['high'].rolling(window=window, center=True).apply(
            lambda x: self._is_pivot_high(x, threshold)
        )
        lows = data['low'].rolling(window=window, center=True).apply(
            lambda x: self._is_pivot_low(x, threshold)
        )
        
        resistance_levels = data.loc[highs.fillna(False), 'high'].tolist()
        support_levels = data.loc[lows.fillna(False), 'low'].tolist()
        
        return support_levels, resistance_levels
    
    def _is_pivot_high(self, prices: pd.Series, threshold: float) -> bool:
        """Identifica si un punto es un pivote alto"""
        if len(prices) < 3:
            return False
            
        mid_point = len(prices) // 2
        mid_price = prices[mid_point]
        
        left_prices = prices[:mid_point]
        right_prices = prices[mid_point + 1:]
        
        return all(price < mid_price * (1 + threshold) for price in left_prices) and \
               all(price < mid_price * (1 + threshold) for price in right_prices)
    
    def _is_pivot_low(self, prices: pd.Series, threshold: float) -> bool:
        """Identifica si un punto es un pivote bajo"""
        if len(prices) < 3:
            return False
            
        mid_point = len(prices) // 2
        mid_price = prices[mid_point]
        
        left_prices = prices[:mid_point]
        right_prices = prices[mid_point + 1:]
        
        return all(price > mid_price * (1 - threshold) for price in left_prices) and \
               all(price > mid_price * (1 - threshold) for price in right_prices) 