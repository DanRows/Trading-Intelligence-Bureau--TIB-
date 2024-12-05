from pybit.unified_trading import HTTP
import pandas as pd
from typing import Dict, Optional, List
import logging
import asyncio
from datetime import datetime

class BybitConnector:
    def __init__(self, api_key: str, api_secret: str, testnet: bool = False):
        self.session = HTTP(
            testnet=testnet,
            api_key=api_key,
            api_secret=api_secret
        )
        self.trading_pairs = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
        self.logger = logging.getLogger(__name__)
        self.rate_limit_delay = 0.1  # 100ms entre llamadas
        
    async def test_connection(self) -> bool:
        """Prueba la conexión con Bybit"""
        try:
            await asyncio.sleep(self.rate_limit_delay)
            response = self.session.get_tickers(
                category="spot",
                symbol="BTCUSDT"
            )
            return response['retCode'] == 0
        except Exception as e:
            self.logger.error(f"Error testing connection: {str(e)}")
            return False

    async def get_kline_data(
        self, 
        symbol: str, 
        interval: str = "15",
        limit: int = 100
    ) -> pd.DataFrame:
        """
        Obtiene datos de velas para un par específico
        
        Args:
            symbol: Par de trading (ej: 'BTCUSDT')
            interval: Intervalo de tiempo ('1', '5', '15', '30', '60', '240', 'D')
            limit: Número de velas a obtener
        """
        try:
            await asyncio.sleep(self.rate_limit_delay)  # Rate limiting
            response = self.session.get_kline(
                category="spot",
                symbol=symbol,
                interval=interval,
                limit=limit
            )
            
            if response['retCode'] != 0:
                error_msg = f"Error from Bybit API: {response['retMsg']}"
                self.logger.error(error_msg)
                raise Exception(error_msg)
                
            df = pd.DataFrame(response['result']['list'])
            if df.empty:
                self.logger.warning(f"No data received for {symbol}")
                return pd.DataFrame()
                
            df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover']
            df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            return df.sort_values('timestamp')
            
        except Exception as e:
            self.logger.error(f"Error getting kline data for {symbol}: {str(e)}")
            raise

    async def get_market_data(self) -> Dict[str, pd.DataFrame]:
        """Obtiene datos de todos los pares configurados"""
        market_data = {}
        errors = []
        
        for pair in self.trading_pairs:
            try:
                market_data[pair] = await self.get_kline_data(pair)
            except Exception as e:
                self.logger.error(f"Error getting market data for {pair}: {str(e)}")
                errors.append(f"{pair}: {str(e)}")
                continue
        
        if errors and len(errors) == len(self.trading_pairs):
            raise Exception(f"Failed to get data for all pairs: {', '.join(errors)}")
            
        return market_data

    def add_trading_pair(self, symbol: str) -> None:
        """Agrega un nuevo par de trading"""
        if symbol not in self.trading_pairs:
            self.trading_pairs.append(symbol)
            self.logger.info(f"Added trading pair: {symbol}")

    def remove_trading_pair(self, symbol: str) -> None:
        """Elimina un par de trading"""
        if symbol in self.trading_pairs:
            self.trading_pairs.remove(symbol)
            self.logger.info(f"Removed trading pair: {symbol}")