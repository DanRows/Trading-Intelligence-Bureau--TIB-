from pybit.unified_trading import HTTP
import pandas as pd
from typing import Dict
import logging
from datetime import datetime

class BybitConnector:
    def __init__(self, api_key: str, api_secret: str):
        self.client = HTTP(
            testnet=False,
            api_key=api_key,
            api_secret=api_secret
        )
        self.trading_pairs = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
        
    async def get_kline_data(self, symbol: str, interval: str = "15") -> pd.DataFrame:
        """Obtiene datos de velas para un par"""
        response = self.client.get_kline(
            category="spot",
            symbol=symbol,
            interval=interval,
            limit=100
        )
        
        df = pd.DataFrame(response['result']['list'])
        df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover']
        df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        return df.sort_values('timestamp')

    async def get_market_data(self) -> Dict[str, pd.DataFrame]:
        """Obtiene datos de todos los pares"""
        market_data = {}
        for pair in self.trading_pairs:
            market_data[pair] = await self.get_kline_data(pair)
        return market_data 