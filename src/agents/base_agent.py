from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import pandas as pd
from datetime import datetime
import logging

class BaseAgent(ABC):
    """Clase base abstracta para todos los agentes de análisis"""
    def __init__(self, name: str):
        self.name = name
        self.analysis_history: List[Dict[str, Any]] = []
        self.logger = logging.getLogger(f"agent.{name}")

    async def analyze(self, market_data: pd.DataFrame) -> Dict[str, Any]:
        """Realiza análisis técnico completo"""
        try:
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
            
        except Exception as e:
            self.logger.error(f"Error en análisis: {str(e)}")
            raise

    def store_analysis(self, analysis: Dict[str, Any]) -> None:
        """Almacena el análisis en el historial"""
        try:
            self.analysis_history.append({
                'timestamp': datetime.utcnow(),
                'analysis': analysis
            })
            
            # Mantener solo los últimos 1000 análisis
            if len(self.analysis_history) > 1000:
                self.analysis_history = self.analysis_history[-1000:]
                
        except Exception as e:
            self.logger.error(f"Error almacenando análisis: {str(e)}")
            raise

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

    def get_last_analysis(self) -> Optional[Dict[str, Any]]:
        """Obtiene el último análisis realizado"""
        try:
            if not self.analysis_history:
                return None
            return self.analysis_history[-1]['analysis']
        except Exception as e:
            self.logger.error(f"Error obteniendo último análisis: {str(e)}")
            return None

    def get_analysis_history(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtiene el historial de análisis filtrado por tiempo
        
        Args:
            start_time: Tiempo inicial para filtrar
            end_time: Tiempo final para filtrar
            
        Returns:
            Lista de análisis filtrados por tiempo
        """
        try:
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
            
        except Exception as e:
            self.logger.error(f"Error obteniendo historial: {str(e)}")
            return []