from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
import logging
from datetime import datetime
from src.config.settings import Settings
from src.data.market_data_service import MarketDataService

logger = logging.getLogger(__name__)

class BacktestResult:
    """Resultados de backtesting."""
    
    def __init__(self, 
                 trades: List[Dict[str, Any]],
                 metrics: Dict[str, Any],
                 equity_curve: pd.Series):
        self.trades = trades
        self.metrics = metrics
        self.equity_curve = equity_curve
        self.timestamp = datetime.utcnow()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convierte resultados a diccionario."""
        return {
            'timestamp': self.timestamp,
            'trades': self.trades,
            'metrics': self.metrics,
            'equity_curve': self.equity_curve.to_dict()
        }

class BaseStrategy(ABC):
    """Clase base para estrategias de backtesting."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.market_data = MarketDataService(settings)
        self.initial_capital = settings.INITIAL_CAPITAL
        self.commission = settings.COMMISSION_RATE
        
        # Estado del backtest
        self.position = 0  # -1: short, 0: neutral, 1: long
        self.trades: List[Dict[str, Any]] = []
        self.equity: List[float] = [self.initial_capital]
        
    @abstractmethod
    async def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Genera señales de trading (-1, 0, 1)."""
        pass
        
    @abstractmethod
    def calculate_position_size(self, price: float) -> float:
        """Calcula el tamaño de la posición."""
        pass