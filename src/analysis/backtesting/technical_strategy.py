from typing import Dict, Any
import pandas as pd
import logging
from .base_strategy import BaseStrategy
from ...agents.technical_analyst import TechnicalAnalyst
from ...config.constants import TradingConstants

logger = logging.getLogger(__name__)

class TechnicalStrategy(BaseStrategy):
    """Estrategia de trading basada en análisis técnico."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa la estrategia técnica.
        
        Args:
            config: Configuración que incluye:
                   - analyst_config: Configuración para el TechnicalAnalyst
                   - confidence_threshold: Umbral mínimo de confianza para trades
                   - initial_capital: Capital inicial
                   - commission: Comisión por trade
        """
        super().__init__(config)
        
        # Configurar analista técnico
        analyst_config = config.get('analyst_config', {})
        self.analyst = TechnicalAnalyst(
            name="backtest_analyst",
            config=analyst_config
        )
        
        # Configuración específica de la estrategia
        self.confidence_threshold = config.get('confidence_threshold', 0.7)
        
        logger.info(f"TechnicalStrategy inicializada con umbral de confianza: {self.confidence_threshold}")
        
    async def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Genera señales de trading basadas en análisis técnico.
        
        Args:
            data: DataFrame con datos históricos
            
        Returns:
            Series con señales (-1: sell, 0: hold, 1: buy)
        """
        try:
            signals = pd.Series(0, index=data.index)
            
            # Analizar cada punto en el tiempo
            for i in range(len(data)):
                # Usar solo datos hasta el punto actual para evitar look-ahead bias
                current_data = data.iloc[:i+1]
                if len(current_data) < 50:  # Necesitamos suficientes datos para el análisis
                    continue
                    
                # Realizar análisis técnico
                analysis = await self.analyst.analyze(current_data)
                
                # Extraer señal y confianza
                signal_data = analysis['signals']
                action = signal_data['action']
                confidence = signal_data['confidence']
                
                # Generar señal solo si supera el umbral de confianza
                if confidence >= self.confidence_threshold:
                    if action == 'buy':
                        signals.iloc[i] = 1
                    elif action == 'sell':
                        signals.iloc[i] = -1
                        
            logger.debug(f"Generadas {len(signals[signals != 0])} señales")
            return signals
            
        except Exception as e:
            logger.error(f"Error generando señales: {str(e)}", exc_info=True)
            raise
            
    async def backtest(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Ejecuta backtesting con análisis técnico.
        
        Args:
            data: DataFrame con datos históricos
            
        Returns:
            Dict con resultados del backtesting y análisis
        """
        try:
            # Ejecutar backtesting base
            results = await super().backtest(data)
            
            # Agregar métricas específicas del análisis técnico
            analysis_metrics = await self._calculate_analysis_metrics(data)
            results['analysis_metrics'] = analysis_metrics
            
            return results
            
        except Exception as e:
            logger.error(f"Error en backtesting técnico: {str(e)}", exc_info=True)
            raise
            
    async def _calculate_analysis_metrics(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Calcula métricas específicas del análisis técnico.
        
        Args:
            data: DataFrame con datos históricos
            
        Returns:
            Dict con métricas adicionales
        """
        try:
            # Realizar análisis final
            final_analysis = await self.analyst.analyze(data)
            
            # Extraer métricas relevantes
            metrics = {
                'final_trend': final_analysis['trend'],
                'indicators': final_analysis['indicators'],
                'signal_distribution': {
                    'buy': len([t for t in self.trades if t.get('position', 0) == 1]),
                    'sell': len([t for t in self.trades if t.get('position', 0) == -1])
                },
                'avg_confidence': sum(t['confidence'] for t in self.trades if 'confidence' in t) / \
                                len([t for t in self.trades if 'confidence' in t]) \
                                if self.trades else 0
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculando métricas de análisis: {str(e)}")
            return {} 