from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
import logging
from .base_agent import BaseAgent
from ..analysis.indicators import TechnicalIndicators
from ..config.constants import Indicators, TimeFrame

logger = logging.getLogger(__name__)

class TechnicalAnalyst(BaseAgent):
    """Agente que analiza datos usando indicadores técnicos."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Inicializa el analista técnico.
        
        Args:
            name: Nombre del analista
            config: Configuración del analista
        """
        super().__init__(name, config)
        self.indicators = TechnicalIndicators()
        self.rsi_overbought = config.get('rsi_overbought', 70)
        self.rsi_oversold = config.get('rsi_oversold', 30)
        self.metrics['signals'] = []  # Tracking de señales generadas
        
    async def analyze(self, 
                     market_data: pd.DataFrame, 
                     additional_data: Optional[Dict[str, pd.DataFrame]] = None) -> Dict[str, Any]:
        """
        Realiza análisis técnico completo.
        
        Args:
            market_data: DataFrame principal con datos de mercado
            additional_data: Datos adicionales opcionales (otros timeframes, etc.)
        """
        try:
            # Preparar datos
            data = await self._prepare_data(market_data, additional_data)
            
            # Realizar análisis
            trend = await self._analyze_trend(data)
            indicators = await self._calculate_indicators(data)
            signals = await self._generate_signals(data)
            
            analysis = {
                'timestamp': pd.Timestamp.now(),
                'trend': trend,
                'indicators': indicators,
                'signals': signals,
                'metadata': {
                    'agent': self.name,
                    'data_points': len(data),
                    'timeframe': data.index.freq if hasattr(data.index, 'freq') else None
                }
            }
            
            # Almacenar análisis
            await self._store_analysis(analysis)
            
            # Actualizar métricas
            if signals['action'] != 'hold':
                self.metrics['signals'].append({
                    'timestamp': analysis['timestamp'],
                    'action': signals['action'],
                    'confidence': signals['confidence']
                })
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error en análisis: {str(e)}", exc_info=True)
            raise
            
    async def _analyze_trend(self, df: pd.DataFrame) -> str:
        """Analiza la tendencia del mercado usando EMAs."""
        try:
            # Calcular EMAs
            ema_short = df['close'].ewm(span=9, adjust=False).mean()
            ema_medium = df['close'].ewm(span=21, adjust=False).mean()
            ema_long = df['close'].ewm(span=55, adjust=False).mean()
            
            # Obtener últimos valores
            current_price = df['close'].iloc[-1]
            current_short = ema_short.iloc[-1]
            current_medium = ema_medium.iloc[-1]
            current_long = ema_long.iloc[-1]
            
            # Determinar tendencia
            if current_short > current_medium > current_long and current_price > current_short:
                return "alcista"
            elif current_short < current_medium < current_long and current_price < current_short:
                return "bajista"
            else:
                return "lateral"
                
        except Exception as e:
            logger.error(f"Error analizando tendencia: {str(e)}")
            return "indefinido"
            
    async def _calculate_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calcula indicadores técnicos."""
        try:
            # Calcular todos los indicadores
            results = self.indicators.calculate_all(df)
            
            # Agregar interpretaciones
            last_values = {
                'rsi': float(results['rsi'].iloc[-1]),
                'macd': float(results['macd'].iloc[-1]),
                'macd_signal': float(results['signal'].iloc[-1]),
                'bb_upper': float(results['upper'].iloc[-1]),
                'bb_lower': float(results['lower'].iloc[-1]),
                'current_price': float(df['close'].iloc[-1])
            }
            
            # Interpretar RSI
            last_values['rsi_condition'] = (
                'sobrecompra' if last_values['rsi'] > self.rsi_overbought
                else 'sobreventa' if last_values['rsi'] < self.rsi_oversold
                else 'neutral'
            )
            
            # Interpretar MACD
            last_values['macd_cross'] = (
                'bullish' if last_values['macd'] > last_values['macd_signal']
                else 'bearish' if last_values['macd'] < last_values['macd_signal']
                else 'neutral'
            )
            
            # Interpretar Bollinger Bands
            last_values['bb_position'] = (
                'superior' if last_values['current_price'] > last_values['bb_upper']
                else 'inferior' if last_values['current_price'] < last_values['bb_lower']
                else 'dentro'
            )
            
            return last_values
            
        except Exception as e:
            logger.error(f"Error calculando indicadores: {str(e)}")
            return {}
            
    async def _generate_signals(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Genera señales de trading basadas en indicadores."""
        try:
            indicators = await self._calculate_indicators(df)
            trend = await self._analyze_trend(df)
            
            # Sistema de puntos para señales
            points = 0
            max_points = 5
            reasons = []
            
            # RSI
            if indicators['rsi_condition'] == 'sobreventa':
                points += 1
                reasons.append("RSI indica sobreventa")
            elif indicators['rsi_condition'] == 'sobrecompra':
                points -= 1
                reasons.append("RSI indica sobrecompra")
                
            # MACD
            if indicators['macd_cross'] == 'bullish':
                points += 1
                reasons.append("Cruce alcista MACD")
            elif indicators['macd_cross'] == 'bearish':
                points -= 1
                reasons.append("Cruce bajista MACD")
                
            # Tendencia
            if trend == "alcista":
                points += 2
                reasons.append("Tendencia alcista")
            elif trend == "bajista":
                points -= 2
                reasons.append("Tendencia bajista")
                
            # Bollinger Bands
            if indicators['bb_position'] == 'inferior':
                points += 1
                reasons.append("Precio bajo banda inferior")
            elif indicators['bb_position'] == 'superior':
                points -= 1
                reasons.append("Precio sobre banda superior")
                
            # Determinar señal y confianza
            confidence = abs(points) / max_points
            
            if points > 0:
                action = "buy"
            elif points < 0:
                action = "sell"
            else:
                action = "hold"
                confidence = 0
                
            return {
                'action': action,
                'confidence': round(confidence, 2),
                'points': points,
                'reasons': reasons,
                'indicators': indicators
            }
            
        except Exception as e:
            logger.error(f"Error generando señales: {str(e)}")
            return {
                'action': 'hold',
                'confidence': 0,
                'points': 0,
                'reasons': [f"Error: {str(e)}"],
                'indicators': {}
            }

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Retorna un resumen de las métricas del agente."""
        summary = super().get_metrics_summary()
        
        # Agregar métricas específicas del analista técnico
        if self.metrics['signals']:
            summary.update({
                'total_signals': len(self.metrics['signals']),
                'buy_signals': sum(1 for s in self.metrics['signals'] if s['action'] == 'buy'),
                'sell_signals': sum(1 for s in self.metrics['signals'] if s['action'] == 'sell'),
                'avg_confidence': sum(s['confidence'] for s in self.metrics['signals']) / len(self.metrics['signals'])
            })
            
        return summary