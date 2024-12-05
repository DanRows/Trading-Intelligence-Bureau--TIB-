import pandas as pd
import numpy as np
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class MarketCondition:
    sentiment: str  # bullish, bearish, neutral
    volatility: float  # 0-1
    strength: float   # 0-1
    description: str

class MarketAnalyzer:
    def __init__(self):
        self.volatility_window = 20
        self.trend_window = 50
        self.volume_window = 14
        
    async def analyze_market_conditions(
        self,
        market_data: Dict[str, pd.DataFrame]
    ) -> MarketCondition:
        """
        Analiza las condiciones generales del mercado
        
        Args:
            market_data: Diccionario de DataFrames con datos OHLCV por par
        """
        # Calcular métricas agregadas
        volatility = self._calculate_market_volatility(market_data)
        sentiment = self._analyze_market_sentiment(market_data)
        strength = self._calculate_market_strength(market_data)
        
        description = self._generate_market_description(
            sentiment,
            volatility,
            strength
        )
        
        return MarketCondition(
            sentiment=sentiment,
            volatility=volatility,
            strength=strength,
            description=description
        )
        
    def _calculate_market_volatility(self, market_data: Dict[str, pd.DataFrame]) -> float:
        """Calcula la volatilidad promedio del mercado"""
        volatilities = []
        
        for pair, data in market_data.items():
            # Calcular True Range
            high = data['high']
            low = data['low']
            close = data['close'].shift(1)
            
            tr1 = high - low
            tr2 = abs(high - close)
            tr3 = abs(low - close)
            
            true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = true_range.rolling(window=self.volatility_window).mean()
            
            # Normalizar por el precio
            normalized_atr = atr / data['close']
            volatilities.append(normalized_atr.iloc[-1])
            
        return float(np.mean(volatilities))
        
    def _analyze_market_sentiment(self, market_data: Dict[str, pd.DataFrame]) -> str:
        """Analiza el sentimiento general del mercado"""
        bullish_count = 0
        bearish_count = 0
        
        for pair, data in market_data.items():
            # Calcular tendencia usando EMAs
            ema20 = data['close'].ewm(span=20, adjust=False).mean()
            ema50 = data['close'].ewm(span=50, adjust=False).mean()
            
            if ema20.iloc[-1] > ema50.iloc[-1]:
                bullish_count += 1
            else:
                bearish_count += 1
                
        total_pairs = len(market_data)
        bullish_percentage = bullish_count / total_pairs
        
        if bullish_percentage > 0.6:
            return "bullish"
        elif bullish_percentage < 0.4:
            return "bearish"
        return "neutral"
        
    def _calculate_market_strength(self, market_data: Dict[str, pd.DataFrame]) -> float:
        """Calcula la fuerza del mercado basada en volumen y momentum"""
        strengths = []
        
        for pair, data in market_data.items():
            # Análisis de volumen
            avg_volume = data['volume'].rolling(window=self.volume_window).mean()
            volume_strength = data['volume'].iloc[-1] / avg_volume.iloc[-1]
            
            # Análisis de momentum
            returns = data['close'].pct_change()
            momentum = returns.rolling(window=self.trend_window).mean()
            
            # Combinar métricas
            pair_strength = (volume_strength + abs(momentum.iloc[-1])) / 2
            strengths.append(pair_strength)
            
        return float(np.mean(strengths))
        
    def calculate_correlation_impact(
        self,
        market_data: Dict[str, pd.DataFrame]
    ) -> Dict[str, float]:
        """
        Calcula el impacto de las correlaciones en el mercado
        
        Returns:
            Dict con pares y su impacto en el mercado
        """
        # Crear matriz de correlación
        close_prices = pd.DataFrame()
        for pair, data in market_data.items():
            close_prices[pair] = data['close']
            
        correlation_matrix = close_prices.corr()
        
        # Calcular impacto por par
        impact_scores = {}
        for pair in market_data.keys():
            # Promedio de correlaciones absolutas con otros pares
            correlations = correlation_matrix[pair].abs()
            impact_scores[pair] = float(correlations.mean())
            
        return impact_scores
        
    def _generate_market_description(
        self,
        sentiment: str,
        volatility: float,
        strength: float
    ) -> str:
        """Genera una descripción textual del estado del mercado"""
        vol_desc = "alta" if volatility > 0.7 else \
                  "moderada" if volatility > 0.3 else "baja"
                  
        strength_desc = "fuerte" if strength > 0.7 else \
                       "moderada" if strength > 0.3 else "débil"
                       
        sentiment_desc = {
            "bullish": "alcista",
            "bearish": "bajista",
            "neutral": "neutral"
        }[sentiment]
        
        return (
            f"Mercado {sentiment_desc} con tendencia {strength_desc} "
            f"y volatilidad {vol_desc}. "
            f"Fuerza de mercado: {strength:.2%}"
        )
        
    def detect_market_extremes(
        self,
        market_data: Dict[str, pd.DataFrame],
        threshold: float = 2.0
    ) -> List[Dict[str, Any]]:
        """
        Detecta movimientos extremos en el mercado
        
        Args:
            market_data: Datos de mercado
            threshold: Número de desviaciones estándar para considerar extremo
        """
        extremes = []
        
        for pair, data in market_data.items():
            returns = data['close'].pct_change()
            mean = returns.mean()
            std = returns.std()
            
            last_return = returns.iloc[-1]
            z_score = (last_return - mean) / std
            
            if abs(z_score) > threshold:
                extremes.append({
                    'pair': pair,
                    'movement': 'up' if z_score > 0 else 'down',
                    'magnitude': abs(z_score),
                    'return': float(last_return)
                })
                
        return extremes 