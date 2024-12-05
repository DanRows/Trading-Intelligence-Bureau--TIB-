from pybit.unified_trading import HTTP
import pandas as pd
from typing import Dict
import logging
import time
from datetime import datetime, timedelta
from .base_connector import BaseExchangeConnector

logger = logging.getLogger(__name__)

class BybitConnector(BaseExchangeConnector):
    def __init__(self, api_key: str, api_secret: str, testnet: bool = False):
        super().__init__(api_key, api_secret, testnet)
        self.session = HTTP(
            testnet=testnet,
            api_key=api_key,
            api_secret=api_secret
        )
        self.last_request_time = {}
        self.min_request_interval = 2.0
        self.max_retries = 3
        
    def _rate_limit(self, endpoint: str):
        """
        Implementa rate limiting por endpoint
        
        Args:
            endpoint: Identificador del endpoint
        """
        current_time = time.time()
        last_time = self.last_request_time.get(endpoint, 0)
        elapsed = current_time - last_time
        
        if elapsed < self.min_request_interval:
            sleep_time = self.min_request_interval - elapsed
            logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s for {endpoint}")
            time.sleep(sleep_time)
            
        self.last_request_time[endpoint] = time.time()

    def _make_request(self, endpoint: str, func, *args, **kwargs) -> Dict:
        """
        Hace una solicitud con reintentos y rate limiting
        
        Args:
            endpoint: Identificador del endpoint
            func: Función a ejecutar
            args: Argumentos posicionales
            kwargs: Argumentos nombrados
        """
        for attempt in range(self.max_retries):
            try:
                self._rate_limit(endpoint)
                response = func(*args, **kwargs)
                
                if response.get('retCode') == 0:
                    return response
                elif 'rate limit' in str(response.get('retMsg', '')).lower():
                    wait_time = (attempt + 1) * self.min_request_interval
                    logger.warning(f"Rate limit hit, waiting {wait_time}s before retry")
                    time.sleep(wait_time)
                else:
                    raise Exception(response.get('retMsg', 'Unknown error'))
                    
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                logger.warning(f"Request failed (attempt {attempt + 1}/{self.max_retries}): {str(e)}")
                time.sleep(self.min_request_interval)
                
        raise Exception(f"Failed after {self.max_retries} attempts")

    def test_connection(self) -> bool:
        """Prueba la conexión con Bybit"""
        try:
            response = self._make_request(
                'test_connection',
                self.session.get_tickers,
                category="spot",
                symbol="BTCUSDT"
            )
            logger.info("Conexión exitosa con Bybit")
            return True
        except Exception as e:
            logger.error(f"Error testing connection: {str(e)}")
            return False

    async def get_kline_data(self, symbol: str, interval: str = "15") -> pd.DataFrame:
        """Obtiene datos de velas para un par"""
        try:
            response = self._make_request(
                f'kline_{symbol}',
                self.session.get_kline,
                category="spot",
                symbol=symbol,
                interval=interval,
                limit=100
            )
            
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
                market_data[pair] = await self.get_kline_data(pair)
            except Exception as e:
                logger.error(f"Error getting market data for {pair}: {str(e)}")
                errors.append(f"{pair}: {str(e)}")
                continue
        
        if errors and len(errors) == len(self.trading_pairs):
            raise Exception(f"Failed to get data for all pairs: {', '.join(errors)}")
            
        return market_data