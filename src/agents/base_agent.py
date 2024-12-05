from abc import ABC, abstractmethod
from typing import Dict, Any, List
import pandas as pd
from datetime import datetime

class BaseAgent(ABC):
    """
    Clase base abstracta para todos los agentes de análisis.
    Define la interfaz común que todos los agentes deben implementar.
    """
    def __init__(self, name: str):
        self.name = name
        self.analysis_history: List[Dict[str, Any]] = []

    async def analyze(self, market_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Método base para realizar análisis. Implementa la estructura común
        que todos los agentes deben seguir.
        
        Args:
            market_data: DataFrame con datos OHLCV del mercado
        """
        analysis = {
            'timestamp': pd.Timestamp.now(),
            'trend': self._analyze_trend(market_data),
            'support_resistance': self._calculate_support_resistance(market_data),
            'indicators': {
                'rsi': self._calculate_rsi(market_data),
                'macd': self._calculate_macd(market_data)
            },
            'volume_analysis': self._analyze_volume(market_data),
            'pattern': self._identify_pattern(market_data)
        }
        
        self.store_analysis(analysis)
        return analysis

    def store_analysis(self, analysis: Dict[str, Any]):
        """
        Almacena el análisis en el historial para aprendizaje y evaluación
        
        Args:
            analysis: Diccionario con los resultados del análisis
        """
        self.analysis_history.append({
            'timestamp': datetime.utcnow(),
            'analysis': analysis
        })
        
        # Mantener solo los últimos 1000 análisis
        if len(self.analysis_history) > 1000:
            self.analysis_history = self.analysis_history[-1000:]

    @abstractmethod
    def _analyze_trend(self, df: pd.DataFrame) -> str:
        """Analiza la tendencia actual del mercado"""
        pass

    @abstractmethod
    def _calculate_support_resistance(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calcula niveles de soporte y resistencia"""
        pass

    @abstractmethod
    def _calculate_rsi(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calcula el RSI y su interpretación"""
        pass

    @abstractmethod
    def _calculate_macd(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calcula el MACD y su interpretación"""
        pass

    @abstractmethod
    def _analyze_volume(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analiza el volumen y su tendencia"""
        pass

    @abstractmethod
    def _identify_pattern(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Identifica patrones en los datos"""
        pass

    @abstractmethod
    async def evaluate_performance(self) -> float:
        """Evalúa el rendimiento histórico del agente"""
        pass

    def get_last_analysis(self) -> Dict[str, Any]:
        """Obtiene el último análisis realizado"""
        if not self.analysis_history:
            return {}
        return self.analysis_history[-1]['analysis']

    def get_analysis_history(
        self,
        start_time: datetime = None,
        end_time: datetime = None
    ) -> List[Dict[str, Any]]:
        """
        Obtiene el historial de análisis filtrado por tiempo
        
        Args:
            start_time: Tiempo inicial para filtrar
            end_time: Tiempo final para filtrar
        """
        filtered_history = self.analysis_history

        if start_time:
            filtered_history = [
                h for h in filtered_history 
                if h['timestamp'] >= start_time
            ]

        if end_time:
            filtered_history = [
                h for h in filtered_history 
                if h['timestamp'] <= end_time
            ]

        return filtered_history