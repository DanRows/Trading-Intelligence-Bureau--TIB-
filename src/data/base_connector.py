from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd
import logging
from src.config.settings import Settings

logger = logging.getLogger(__name__)

class BaseConnector(ABC):
    """Clase base para conectores de exchanges."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.trading_pairs = settings.TRADING_PAIRS
        
    @abstractmethod
    async def get_market_data(self, symbol: str) -> pd.DataFrame:
        """Obtiene datos de mercado para un símbolo."""
        pass
        
    @abstractmethod
    async def get_orderbook(self, symbol: str) -> Dict[str, Any]:
        """Obtiene el libro de órdenes para un símbolo."""
        pass
        
    @abstractmethod
    async def get_recent_trades(self, symbol: str) -> pd.DataFrame:
        """Obtiene trades recientes para un símbolo."""
        pass 