import pandas as pd
from typing import Dict, Any
import logging
from pybit.unified_trading import HTTP
from src.data.base_connector import BaseConnector
from src.config.settings import Settings

logger = logging.getLogger(__name__)

class BybitConnector(BaseConnector):
    """Conector para Bybit."""
    
    def __init__(self, settings: Settings):
        super().__init__(settings)
        self.client = HTTP(
            testnet=settings.USE_TESTNET,
            api_key=settings.BYBIT_API_KEY,
            api_secret=settings.BYBIT_API_SECRET
        )
        
    async def get_market_data(self, symbol: str) -> pd.DataFrame:
        """Obtiene datos de mercado para un símbolo."""
        try:
            response = self.client.get_kline(
                category="spot",
                symbol=symbol,
                interval="15",
                limit=100
            )
            
            df = pd.DataFrame(response['result']['list'])
            df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover']
            df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            return df.sort_values('timestamp')
            
        except Exception as e:
            logger.error(f"Error obteniendo datos de mercado: {str(e)}")
            raise