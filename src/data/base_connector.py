from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class BaseExchangeConnector(ABC):
    """Clase base para conectores de exchanges"""
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = False):
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.trading_pairs = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
        
    @abstractmethod
    def test_connection(self) -> bool:
        """Prueba la conexión con el exchange"""
        pass
        
    @abstractmethod
    async def get_kline_data(self, symbol: str, interval: str = "15") -> pd.DataFrame:
        """Obtiene datos de velas para un par"""
        pass
        
    @abstractmethod
    async def get_market_data(self) -> Dict[str, pd.DataFrame]:
        """Obtiene datos de todos los pares"""
        pass 