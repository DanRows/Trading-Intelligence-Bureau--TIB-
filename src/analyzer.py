import pandas as pd
import numpy as np
from typing import Dict, Any
from alerts.alert_system import AlertSystem
from analysis.indicators import TechnicalIndicators

class MarketAnalyzer:
    def __init__(self):
        self.alert_system = AlertSystem()
        self.indicators = TechnicalIndicators()
    
    def analyze_market(self, market_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Analiza los datos del mercado"""
        analyses = {}
        
        for pair, data in market_data.items():
            # Calcular indicadores
            macd = self.indicators.calculate_macd(data['close'])
            bb = self.indicators.calculate_bollinger_bands(data['close'])
            k_line, d_line = self.indicators.calculate_stochastic(
                data['high'], data['low'], data['close']
            )
            
            analysis = {
                'pair': pair,
                'timestamp': pd.Timestamp.now(),
                'trend': self._analyze_trend(data),
                'rsi': self._calculate_rsi(data),
                'volume_analysis': self._analyze_volume(data),
                'indicators': {
                    'macd': {
                        'value': float(macd['macd'].iloc[-1]),
                        'signal': float(macd['signal'].iloc[-1]),
                        'histogram': float(macd['histogram'].iloc[-1])
                    },
                    'bollinger_bands': {
                        'upper': float(bb['upper'].iloc[-1]),
                        'middle': float(bb['middle'].iloc[-1]),
                        'lower': float(bb['lower'].iloc[-1])
                    },
                    'stochastic': {
                        'k': float(k_line.iloc[-1]),
                        'd': float(d_line.iloc[-1])
                    }
                }
            }
            analyses[pair] = analysis
        
        # Procesar alertas
        alerts = self.alert_system.process_market_data(
            market_data,
            {pair: analysis for pair, analysis in analyses.items()}
        )
        
        # Agregar alertas al análisis
        for pair in analyses:
            pair_alerts = [
                alert for alert in alerts
                if alert.pair == pair
            ]
            analyses[pair]['alerts'] = pair_alerts
        
        return analyses
    
    def _analyze_trend(self, df: pd.DataFrame) -> str:
        """Determina la tendencia usando SMAs"""
        sma20 = df['close'].rolling(window=20).mean().iloc[-1]
        sma50 = df['close'].rolling(window=50).mean().iloc[-1]
        current_price = df['close'].iloc[-1]
        
        if current_price > sma20 and sma20 > sma50:
            return "bullish"
        elif current_price < sma20 and sma20 < sma50:
            return "bearish"
        return "neutral"
    
    def _calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> float:
        """Calcula el RSI"""
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1])
    
    def _analyze_volume(self, df: pd.DataFrame) -> Dict[str, float]:
        """Analiza el volumen"""
        avg_volume = df['volume'].rolling(window=20).mean().iloc[-1]
        current_volume = df['volume'].iloc[-1]
        
        return {
            'current_volume': float(current_volume),
            'avg_volume': float(avg_volume),
            'volume_ratio': float(current_volume / avg_volume)
        } 