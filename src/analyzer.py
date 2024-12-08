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
        
    async def analyze_market_data(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Analiza datos de mercado.
        
        Args:
            data: DataFrame con datos OHLCV
            
        Returns:
            Dict con resultados del análisis
        """
        try:
            metrics = await self._calculate_metrics(data)
            indicators = await self._calculate_indicators(data)
            patterns = await self._detect_patterns(data)
            
            results = {
                'timestamp': pd.Timestamp.now(),
                'metrics': metrics,
                'indicators': indicators,
                'patterns': patterns
            }
            return results
            
        except Exception as e:
            logger.error(f"Error analizando datos: {str(e)}")
            return {}
            
    async def _calculate_metrics(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calcula métricas básicas."""
        return {
            'volatility': data['close'].pct_change().std() * np.sqrt(252),
            'daily_return': data['close'].pct_change().mean(),
            'volume_ma': data['volume'].rolling(20).mean().iloc[-1]
        }
        
    async def _calculate_indicators(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calcula indicadores técnicos."""
        close = data['close']
        high = data['high']
        low = data['low']
        volume = data['volume']
        
        # Medias móviles
        sma_20 = close.rolling(window=20).mean()
        sma_50 = close.rolling(window=50).mean()
        
        # RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return {
            'sma_20': sma_20.iloc[-1],
            'sma_50': sma_50.iloc[-1],
            'rsi': rsi.iloc[-1],
            'trend': 'alcista' if sma_20.iloc[-1] > sma_50.iloc[-1] else 'bajista'
        }
        
    async def _detect_patterns(self, data: pd.DataFrame) -> List[str]:
        """Detecta patrones de velas."""
        patterns = []
        
        # Implementar detección de patrones aquí
        # Por ahora retornamos una lista vacía
        return patterns