from binance.client import Client
import pandas as pd
from typing import Dict
import logging
import time
from datetime import datetime
from .base_connector import BaseExchangeConnector

logger = logging.getLogger(__name__)

class BinanceConnector(BaseExchangeConnector):
    def __init__(self, api_key: str, api_secret: str, testnet: bool = False):
        super().__init__(api_key, api_secret, testnet)
        self.client = Client(
            api_key,
            api_secret,
            testnet=testnet
        )
        self.last_request_time = {}
        self.min_request_interval = 1.0
        
    def test_connection(self) -> bool:
        """Prueba la conexión con Binance"""
        try:
            self.client.get_system_status()
            logger.info("Conexión exitosa con Binance")
            return True
        except Exception as e:
            logger.error(f"Error testing connection: {str(e)}")
            return False
            
    async def get_kline_data(self, symbol: str, interval: str = "15m") -> pd.DataFrame:
        """Obtiene datos de velas para un par"""
        try:
            klines = self.client.get_klines(
                symbol=symbol,
                interval=interval,
                limit=100
            )
            
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            logger.error(f"Error getting kline data for {symbol}: {str(e)}")
            raise
            
    async def get_market_data(self) -> Dict[str, pd.DataFrame]:
        """Obtiene datos de todos los pares"""
        market_data = {}
        errors = []
        
        for pair in self.trading_pairs:
            try:
                market_data[pair] = await self.get_kline_data(pair)
            except Exception as e:
                logger.error(f"Error getting market data for {pair}: {str(e)}")
                errors.append(f"{pair}: {str(e)}")
                continue
                
        if errors and len(errors) == len(self.trading_pairs):
            raise Exception(f"Failed to get data for all pairs: {', '.join(errors)}")
            
        return market_data 