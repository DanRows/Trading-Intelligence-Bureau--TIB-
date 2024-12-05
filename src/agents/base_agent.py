from abc import ABC, abstractmethod
from typing import Dict, Any
import pandas as pd

class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name
        self.analysis_history = []

    @abstractmethod
    async def analyze(self, market_data: pd.DataFrame) -> Dict[str, Any]:
        """Método abstracto para análisis específico del agente"""
        pass

    def store_analysis(self, analysis: Dict[str, Any]):
        """Almacena el análisis para aprendizaje futuro"""
        self.analysis_history.append({
            'timestamp': pd.Timestamp.now(),
            'analysis': analysis
        })

    @abstractmethod
    async def evaluate_performance(self) -> float:
        """Evalúa la precisión histórica del agente"""
        pass 