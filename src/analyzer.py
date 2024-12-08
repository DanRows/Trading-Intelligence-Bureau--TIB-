import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List
from src.config.settings import Settings
from src.data.market_data_service import MarketDataService

logger = logging.getLogger(__name__)

class MarketAnalyzer:
    """Analizador de mercado."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.market_data = MarketDataService(settings)
        
    def analyze_market_data(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Analiza datos de mercado.
        
        Args:
            data: DataFrame con datos OHLCV
            
        Returns:
            Dict con resultados del análisis
        """
        try:
            results = {
                'timestamp': pd.Timestamp.now(),
                'metrics': self._calculate_metrics(data),
                'indicators': self._calculate_indicators(data),
                'patterns': self._detect_patterns(data)
            }
            return results
            
        except Exception as e:
            logger.error(f"Error analizando datos: {str(e)}")
            return {}
            
    def _calculate_metrics(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calcula métricas básicas."""
        return {
            'volatility': data['close'].pct_change().std() * np.sqrt(252),
            'daily_return': data['close'].pct_change().mean(),
            'volume_ma': data['volume'].rolling(20).mean().iloc[-1]
        }
        
    def _calculate_indicators(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calcula indicadores técnicos."""
        return {
            'rsi': self._calculate_rsi(data['close']),
            'macd': self._calculate_macd(data['close']),
            'bollinger': self._calculate_bollinger_bands(data['close'])
        }
        
    def _detect_patterns(self, data: pd.DataFrame) -> List[str]:
        """Detecta patrones de velas."""
        patterns = []
        # Implementar detección de patrones
        return patterns 