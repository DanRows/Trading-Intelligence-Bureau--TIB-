from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd
import logging
import time
import asyncio
from src.config.settings import Settings
from src.utils.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

class BaseConnector(ABC):
    """Clase base para conectores de exchanges."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.trading_pairs = settings.TRADING_PAIRS
        self.rate_limiter = RateLimiter(
            max_requests=60,
            time_window=60
        )
        
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