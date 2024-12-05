from pybit.unified_trading import HTTP
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import asyncio
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from enum import Enum

class TimeFrame(Enum):
    M1 = "1"    # 1 minuto
    M5 = "5"    # 5 minutos
    M15 = "15"  # 15 minutos
    M30 = "30"  # 30 minutos
    H1 = "60"   # 1 hora
    H4 = "240"  # 4 horas
    D1 = "D"    # 1 día

@dataclass
class MarketSummary:
    last_price: float
    high_24h: float
    low_24h: float
    volume_24h: float
    price_change_24h: float
    bid: float
    ask: float
    spread: float

class BybitConnector:
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        testnet: bool = False,
        default_timeframe: TimeFrame = TimeFrame.M15
    ):
        self.client = HTTP(
            testnet=testnet,
            api_key=api_key,
            api_secret=api_secret
        )
        self.trading_pairs = ["BTCUSDT", "ETHUSDT", "XRPUSDT", "SOLUSDT", "ADAUSDT"]
        self.logger = logging.getLogger(__name__)
        self.default_timeframe = default_timeframe
        self.rate_limit_delay = 0.1  # 100ms entre llamadas
        
    async def get_kline_data(
        self, 
        symbol: str, 
        interval: TimeFrame = None,
        limit: int = 100,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Obtiene datos de velas para un par específico
        
        Args:
            symbol: Par de trading (ej: 'BTCUSDT')
            interval: Intervalo de tiempo
            limit: Número de velas a obtener
            start_time: Tiempo de inicio opcional
            end_time: Tiempo final opcional
        """
        try:
            interval = interval or self.default_timeframe
            params = {
                "category": "spot",
                "symbol": symbol,
                "interval": interval.value,
                "limit": limit
            }
            
            if start_time:
                params["start_time"] = int(start_time.timestamp() * 1000)
            if end_time:
                params["end_time"] = int(end_time.timestamp() * 1000)
            
            await asyncio.sleep(self.rate_limit_delay)  # Respetar rate limit
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

    async def get_market_data(
        self,
        interval: TimeFrame = None,
        pairs: List[str] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        Obtiene datos de mercado para los pares especificados
        
        Args:
            interval: Intervalo de tiempo para las velas
            pairs: Lista de pares a consultar (opcional)
        """
        pairs = pairs or self.trading_pairs
        tasks = []
        
        for pair in pairs:
            tasks.append(self.get_kline_data(pair, interval=interval))
            
        try:
            results = await asyncio.gather(*tasks)
            return dict(zip(pairs, results))
        except Exception as e:
            self.logger.error(f"Error getting market data: {str(e)}")
            raise

    async def get_market_summary(self, symbol: str) -> MarketSummary:
        """
        Obtiene resumen del mercado para un par
        
        Args:
            symbol: Par de trading
        """
        try:
            ticker = await self.get_ticker_info(symbol)
            orderbook = await self.get_order_book(symbol, limit=1)
            
            return MarketSummary(
                last_price=ticker['last_price'],
                high_24h=ticker['high_24h'],
                low_24h=ticker['low_24h'],
                volume_24h=ticker['volume_24h'],
                price_change_24h=ticker['price_change_24h'],
                bid=orderbook['bids'][0][0] if orderbook['bids'] else 0,
                ask=orderbook['asks'][0][0] if orderbook['asks'] else 0,
                spread=orderbook['asks'][0][0] - orderbook['bids'][0][0] if orderbook['asks'] and orderbook['bids'] else 0
            )
            
        except Exception as e:
            self.logger.error(f"Error getting market summary for {symbol}: {str(e)}")
            raise

    async def get_ticker_info(self, symbol: str) -> Dict[str, float]:
        """Obtiene información del ticker"""
        try:
            await asyncio.sleep(self.rate_limit_delay)
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

    async def get_order_book(
        self,
        symbol: str,
        limit: int = 50
    ) -> Dict[str, List[List[float]]]:
        """Obtiene el libro de órdenes"""
        try:
            await asyncio.sleep(self.rate_limit_delay)
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
        """Agrega un nuevo par de trading"""
        if symbol not in self.trading_pairs:
            self.trading_pairs.append(symbol)
            self.logger.info(f"Added new trading pair: {symbol}")

    def remove_trading_pair(self, symbol: str) -> None:
        """Elimina un par de trading"""
        if symbol in self.trading_pairs:
            self.trading_pairs.remove(symbol)
            self.logger.info(f"Removed trading pair: {symbol}")

    async def validate_trading_pair(self, symbol: str) -> bool:
        """Valida si un par de trading existe y está activo"""
        try:
            await self.get_ticker_info(symbol)
            return True
        except Exception:
            return False