from dataclasses import dataclass
from typing import List, Dict, Optional
import pandas as pd
import numpy as np

@dataclass
class CandlePattern:
    name: str
    bullish: bool
    reliability: float
    description: str

class CandlePatternAnalyzer:
    def __init__(self):
        self.patterns = {
            'doji': CandlePattern(
                name='Doji',
                bullish=None,  # Neutral
                reliability=0.6,
                description='Indecisión en el mercado'
            ),
            'hammer': CandlePattern(
                name='Hammer',
                bullish=True,
                reliability=0.7,
                description='Posible reversión alcista'
            ),
            'shooting_star': CandlePattern(
                name='Shooting Star',
                bullish=False,
                reliability=0.7,
                description='Posible reversión bajista'
            ),
            'engulfing_bullish': CandlePattern(
                name='Engulfing Alcista',
                bullish=True,
                reliability=0.8,
                description='Señal de reversión alcista fuerte'
            ),
            'engulfing_bearish': CandlePattern(
                name='Engulfing Bajista',
                bullish=False,
                reliability=0.8,
                description='Señal de reversión bajista fuerte'
            )
        }

    def analyze_candles(self, df: pd.DataFrame, window: int = 3) -> Dict[str, Any]:
        """
        Analiza las últimas velas en busca de patrones
        
        Args:
            df: DataFrame con datos OHLCV
            window: Número de velas a analizar
        """
        last_candles = df.iloc[-window:]
        patterns_found = []
        
        # Verificar cada patrón
        if self._is_doji(last_candles.iloc[-1]):
            patterns_found.append('doji')
            
        if self._is_hammer(last_candles.iloc[-1]):
            patterns_found.append('hammer')
            
        if self._is_shooting_star(last_candles.iloc[-1]):
            patterns_found.append('shooting_star')
            
        if len(last_candles) >= 2:
            if self._is_engulfing(last_candles.iloc[-2:], bullish=True):
                patterns_found.append('engulfing_bullish')
            elif self._is_engulfing(last_candles.iloc[-2:], bullish=False):
                patterns_found.append('engulfing_bearish')
        
        # Obtener el patrón más significativo
        if patterns_found:
            main_pattern = max(patterns_found, 
                             key=lambda x: self.patterns[x].reliability)
            pattern_info = self.patterns[main_pattern]
            
            return {
                'pattern': pattern_info.name,
                'bullish': pattern_info.bullish,
                'reliability': pattern_info.reliability,
                'description': pattern_info.description
            }
        
        return {
            'pattern': 'No Pattern',
            'bullish': None,
            'reliability': 0.0,
            'description': 'No se encontraron patrones significativos'
        }

    def _is_doji(self, candle: pd.Series, threshold: float = 0.1) -> bool:
        """Identifica un patrón Doji"""
        body_size = abs(candle['open'] - candle['close'])
        total_size = candle['high'] - candle['low']
        
        return body_size <= (total_size * threshold)

    def _is_hammer(self, candle: pd.Series) -> bool:
        """Identifica un patrón Hammer"""
        body_size = abs(candle['open'] - candle['close'])
        lower_shadow = min(candle['open'], candle['close']) - candle['low']
        upper_shadow = candle['high'] - max(candle['open'], candle['close'])
        
        return (lower_shadow > body_size * 2) and (upper_shadow < body_size * 0.5)

    def _is_shooting_star(self, candle: pd.Series) -> bool:
        """Identifica un patrón Shooting Star"""
        body_size = abs(candle['open'] - candle['close'])
        lower_shadow = min(candle['open'], candle['close']) - candle['low']
        upper_shadow = candle['high'] - max(candle['open'], candle['close'])
        
        return (upper_shadow > body_size * 2) and (lower_shadow < body_size * 0.5)

    def _is_engulfing(self, candles: pd.DataFrame, bullish: bool) -> bool:
        """Identifica un patrón Engulfing"""
        prev_candle = candles.iloc[0]
        curr_candle = candles.iloc[1]
        
        if bullish:
            return (prev_candle['close'] < prev_candle['open'] and  # Vela previa roja
                   curr_candle['close'] > curr_candle['open'] and  # Vela actual verde
                   curr_candle['open'] < prev_candle['close'] and  # Abre por debajo
                   curr_candle['close'] > prev_candle['open'])     # Cierra por encima
        else:
            return (prev_candle['close'] > prev_candle['open'] and  # Vela previa verde
                   curr_candle['close'] < curr_candle['open'] and  # Vela actual roja
                   curr_candle['open'] > prev_candle['close'] and  # Abre por encima
                   curr_candle['close'] < prev_candle['open'])     # Cierra por debajo

    def calculate_pattern_strength(self, pattern: str, candles: pd.DataFrame) -> float:
        """
        Calcula la fuerza del patrón basado en el contexto
        
        Args:
            pattern: Nombre del patrón identificado
            candles: DataFrame con datos históricos
        """
        base_reliability = self.patterns[pattern].reliability
        
        # Factores que pueden aumentar la confiabilidad
        volume_factor = self._calculate_volume_factor(candles)
        trend_factor = self._calculate_trend_factor(candles)
        
        # Ajustar la confiabilidad base
        adjusted_reliability = base_reliability * volume_factor * trend_factor
        
        return min(adjusted_reliability, 1.0)

    def _calculate_volume_factor(self, candles: pd.DataFrame) -> float:
        """Calcula factor de volumen"""
        avg_volume = candles['volume'].mean()
        last_volume = candles['volume'].iloc[-1]
        
        return min(last_volume / avg_volume, 2.0) if avg_volume > 0 else 1.0

    def _calculate_trend_factor(self, candles: pd.DataFrame) -> float:
        """Calcula factor de tendencia"""
        sma20 = candles['close'].rolling(window=20).mean()
        current_price = candles['close'].iloc[-1]
        
        if current_price > sma20.iloc[-1]:
            return 1.2  # Tendencia alcista
        elif current_price < sma20.iloc[-1]:
            return 0.8  # Tendencia bajista
        return 1.0     # Neutral 