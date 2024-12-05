import pandas as pd
import numpy as np
from typing import Dict, Any
from .base_agent import BaseAgent
from ..analysis.indicators import TechnicalIndicators
from ..analysis.patterns import CandlePatternAnalyzer
from ..alerts.alert_manager import AlertManager, AlertPriority

class TechnicalAnalyst(BaseAgent):
    def __init__(self, name: str, trading_pair: str):
        super().__init__(name)
        self.trading_pair = trading_pair
        self.indicators = TechnicalIndicators()
        self.pattern_analyzer = CandlePatternAnalyzer()
        self.alert_manager = AlertManager()

    async def analyze(self, market_data: pd.DataFrame) -> Dict[str, Any]:
        """Realiza análisis técnico completo"""
        analysis = await super().analyze(market_data)
        
        # Verificar condiciones para alertas
        await self._check_alerts(market_data, analysis)
        
        return analysis
        
    async def _check_alerts(self, market_data: pd.DataFrame, analysis: Dict[str, Any]):
        """Verifica condiciones para generar alertas"""
        current_price = market_data['close'].iloc[-1]
        
        # Alertas de precio
        await self.alert_manager.check_price_alerts(
            self.trading_pair,
            current_price,
            self.get_price_alerts_config()
        )
        
        # Alertas de volatilidad
        volatility = analysis['indicators'].get('volatility', 0)
        await self.alert_manager.check_volatility_alerts(
            self.trading_pair,
            volatility
        )
        
        # Alertas de volumen
        volume_analysis = analysis['volume_analysis']
        await self.alert_manager.check_volume_alerts(
            self.trading_pair,
            volume_analysis['current_volume'],
            volume_analysis['avg_volume']
        )
        
        # Alertas de patrones
        pattern_analysis = analysis['pattern']
        await self.alert_manager.check_pattern_alerts(
            self.trading_pair,
            pattern_analysis
        )
        
    def get_price_alerts_config(self) -> Dict[str, Any]:
        """Obtiene configuración de alertas de precio"""
        # Aquí podrías cargar la configuración desde un archivo o base de datos
        return {
            'price_levels': [
                {'price': 50000, 'type': 'resistance'},
                {'price': 45000, 'type': 'support'}
            ]
        }

    def _analyze_trend(self, df: pd.DataFrame) -> str:
        """Determina la tendencia actual"""
        sma20 = df['close'].rolling(window=20).mean().iloc[-1]
        sma50 = df['close'].rolling(window=50).mean().iloc[-1]
        current_price = df['close'].iloc[-1]
        
        if current_price > sma20 and sma20 > sma50:
            return "bullish"
        elif current_price < sma20 and sma20 < sma50:
            return "bearish"
        return "neutral"

    def _calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> Dict[str, Any]:
        """Calcula el RSI y su interpretación"""
        rsi_result = self.indicators.calculate_rsi(df['close'], period)
        
        return {
            'value': rsi_result.value,
            'overbought': rsi_result.overbought,
            'oversold': rsi_result.oversold
        }

    def _calculate_macd(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calcula el MACD y su interpretación"""
        macd_result = self.indicators.calculate_macd(df['close'])
        
        return {
            'macd': macd_result.macd,
            'signal': macd_result.signal,
            'histogram': macd_result.histogram,
            'signal_type': 'buy' if macd_result.bullish_crossover else \
                         'sell' if macd_result.bearish_crossover else 'neutral'
        }

    def _calculate_support_resistance(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calcula niveles de soporte y resistencia"""
        support_levels, resistance_levels = self.indicators.find_support_resistance(df)
        
        # Obtener los niveles más cercanos al precio actual
        current_price = df['close'].iloc[-1]
        
        closest_support = min(
            (level for level in support_levels if level < current_price),
            default=current_price * 0.95
        )
        
        closest_resistance = min(
            (level for level in resistance_levels if level > current_price),
            default=current_price * 1.05
        )
        
        return {
            'support': float(closest_support),
            'resistance': float(closest_resistance)
        }

    def _analyze_volume(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analiza el volumen y su tendencia"""
        avg_volume = df['volume'].rolling(window=20).mean().iloc[-1]
        current_volume = df['volume'].iloc[-1]
        volume_trend = "high" if current_volume > avg_volume * 1.5 else \
                      "low" if current_volume < avg_volume * 0.5 else "normal"
        
        return {
            'current_volume': float(current_volume),
            'avg_volume': float(avg_volume),
            'volume_trend': volume_trend
        }

    def _identify_pattern(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Identifica patrones de velas japonesas"""
        pattern_analysis = self.pattern_analyzer.analyze_candles(df)
        
        # Calcular la fuerza del patrón si se encontró uno
        if pattern_analysis['pattern'] != 'No Pattern':
            pattern_strength = self.pattern_analyzer.calculate_pattern_strength(
                pattern_analysis['pattern'],
                df
            )
            pattern_analysis['strength'] = pattern_strength
        
        return pattern_analysis

    async def evaluate_performance(self) -> float:
        """Evalúa la precisión histórica del agente"""
        if not self.analysis_history:
            return 0.0
            
        correct_predictions = 0
        total_predictions = len(self.analysis_history) - 1
        
        for i in range(total_predictions):
            current_analysis = self.analysis_history[i]['analysis']
            next_analysis = self.analysis_history[i + 1]['analysis']
            
            # Compara la predicción con el resultado real
            if current_analysis['trend'] == 'bullish' and \
               next_analysis['indicators']['rsi']['overbought']:
                correct_predictions += 1
            elif current_analysis['trend'] == 'bearish' and \
                 next_analysis['indicators']['rsi']['oversold']:
                correct_predictions += 1
                
        return correct_predictions / total_predictions if total_predictions > 0 else 0.0