from pybit.unified_trading import HTTP
import pandas as pd
from typing import List, Dict, Optional
import asyncio
from datetime import datetime, timedelta
import logging

class BybitConnector:
    def __init__(self, api_key: str, api_secret: str, testnet: bool = False):
        self.client = HTTP(
            testnet=testnet,
            api_key=api_key,
            api_secret=api_secret
        )
        self.trading_pairs = ["BTCUSDT", "ETHUSDT", "XRPUSDT", "SOLUSDT", "ADAUSDT"]
        self.logger = logging.getLogger(__name__)
        
    async def get_kline_data(
        self, 
        symbol: str, 
        interval: str = "15", 
        limit: int = 100,
        start_time: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Obtiene datos de velas para un par específico
        
        Args:
            symbol: Par de trading (ej: 'BTCUSDT')
            interval: Intervalo de tiempo ('1', '5', '15', '30', '60', '240', 'D')
            limit: Número de velas a obtener
            start_time: Tiempo de inicio opcional
        """
        try:
            params = {
                "category": "spot",
                "symbol": symbol,
                "interval": interval,
                "limit": limit
            }
            
            if start_time:
                params["start_time"] = int(start_time.timestamp() * 1000)
            
            response = self.client.get_kline(**params)
            
            if not response.get('result', {}).get('list'):
                self.logger.error(f"No data received for {symbol}")
                return pd.DataFrame()
            
            df = pd.DataFrame(response['result']['list'])
            df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover']
            
            # Convertir tipos de datos
            numeric_columns = ['open', 'high', 'low', 'close', 'volume', 'turnover']
            df[numeric_columns] = df[numeric_columns].astype(float)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            return df.sort_values('timestamp')
            
        except Exception as e:
            self.logger.error(f"Error getting kline data for {symbol}: {str(e)}")
            raise

    async def get_market_data(self, interval: str = "15") -> Dict[str, pd.DataFrame]:
        """
        Obtiene datos de mercado para todos los pares configurados
        
        Args:
            interval: Intervalo de tiempo para las velas
        """
        tasks = []
        for pair in self.trading_pairs:
            tasks.append(self.get_kline_data(pair, interval=interval))
            
        try:
            results = await asyncio.gather(*tasks)
            return dict(zip(self.trading_pairs, results))
        except Exception as e:
            self.logger.error(f"Error getting market data: {str(e)}")
            raise

    async def get_ticker_info(self, symbol: str) -> Dict[str, float]:
        """
        Obtiene información actual del ticker
        
        Args:
            symbol: Par de trading (ej: 'BTCUSDT')
        """
        try:
            response = self.client.get_tickers(
                category="spot",
                symbol=symbol
            )
            
            ticker_data = response['result']
            return {
                'last_price': float(ticker_data['last_price']),
                'high_24h': float(ticker_data['high_24h']),
                'low_24h': float(ticker_data['low_24h']),
                'volume_24h': float(ticker_data['volume_24h']),
                'price_change_24h': float(ticker_data['price_24h_pcnt'])
            }
            
        except Exception as e:
            self.logger.error(f"Error getting ticker info for {symbol}: {str(e)}")
            raise

    async def get_order_book(self, symbol: str, limit: int = 50) -> Dict[str, List]:
        """
        Obtiene el libro de órdenes actual
        
        Args:
            symbol: Par de trading
            limit: Número de niveles a obtener
        """
        try:
            response = self.client.get_orderbook(
                category="spot",
                symbol=symbol,
                limit=limit
            )
            
            return {
                'bids': [[float(price), float(qty)] for price, qty in response['result']['bids']],
                'asks': [[float(price), float(qty)] for price, qty in response['result']['asks']]
            }
            
        except Exception as e:
            self.logger.error(f"Error getting order book for {symbol}: {str(e)}")
            raise

    def add_trading_pair(self, symbol: str) -> None:
        """Agrega un nuevo par de trading a la lista de monitoreo"""
        if symbol not in self.trading_pairs:
            self.trading_pairs.append(symbol)
            self.logger.info(f"Added new trading pair: {symbol}")

    def remove_trading_pair(self, symbol: str) -> None:
        """Elimina un par de trading de la lista de monitoreo"""
        if symbol in self.trading_pairs:
            self.trading_pairs.remove(symbol)
            self.logger.info(f"Removed trading pair: {symbol}")