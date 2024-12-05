from pybit.unified_trading import HTTP
import pandas as pd
from typing import Dict
import logging
import time

logger = logging.getLogger(__name__)

class BybitConnector:
    def __init__(self, api_key: str, api_secret: str):
        self.session = HTTP(
            testnet=False,
            api_key=api_key,
            api_secret=api_secret
        )
        self.trading_pairs = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
        self.last_request_time = 0
        self.min_request_interval = 0.5  # 500ms entre solicitudes
        
    def _rate_limit(self):
        """Implementa rate limiting básico"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()

    def test_connection(self) -> bool:
        """Prueba la conexión con Bybit"""
        try:
            self._rate_limit()
            response = self.session.get_tickers(
                category="spot",
                symbol="BTCUSDT"
            )
            is_connected = response.get('retCode') == 0
            if is_connected:
                logger.info("Conexión exitosa con Bybit")
            else:
                logger.error(f"Error de conexión: {response.get('retMsg')}")
            return is_connected
        except Exception as e:
            logger.error(f"Error testing connection: {str(e)}")
            return False

    async def get_kline_data(self, symbol: str, interval: str = "15") -> pd.DataFrame:
        """Obtiene datos de velas para un par"""
        try:
            self._rate_limit()
            response = self.session.get_kline(
                category="spot",
                symbol=symbol,
                interval=interval,
                limit=100
            )
            
            if response.get('retCode') != 0:
                error_msg = f"Error from Bybit API: {response.get('retMsg')}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
            df = pd.DataFrame(response['result']['list'])
            if df.empty:
                logger.warning(f"No data received for {symbol}")
                return pd.DataFrame()
                
            df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover']
            df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            return df.sort_values('timestamp')
            
        except Exception as e:
            logger.error(f"Error getting kline data for {symbol}: {str(e)}")
            raise

    async def get_market_data(self) -> Dict[str, pd.DataFrame]:
        """Obtiene datos de todos los pares"""
        market_data = {}
        errors = []
        
        for pair in self.trading_pairs:
            try:
                self._rate_limit()
                market_data[pair] = await self.get_kline_data(pair)
            except Exception as e:
                logger.error(f"Error getting market data for {pair}: {str(e)}")
                errors.append(f"{pair}: {str(e)}")
                continue
        
        if errors and len(errors) == len(self.trading_pairs):
            raise Exception(f"Failed to get data for all pairs: {', '.join(errors)}")
            
        return market_data