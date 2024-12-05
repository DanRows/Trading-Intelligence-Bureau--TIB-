import requests
import pandas as pd
from typing import Dict
import logging
from datetime import datetime
from .base_connector import BaseExchangeConnector
import ta

logger = logging.getLogger(__name__)

class CoinGeckoConnector(BaseExchangeConnector):
    def __init__(self, api_key: str = "", api_secret: str = "", testnet: bool = False):
        super().__init__(api_key, api_secret, testnet)
        self.base_url = "https://api.coingecko.com/api/v3"
        self.crypto_ids = {
            "BTCUSDT": "bitcoin",
            "ETHUSDT": "ethereum",
            "SOLUSDT": "solana"
        }
        
    def test_connection(self) -> bool:
        """Prueba la conexión con CoinGecko"""
        try:
            response = requests.get(f"{self.base_url}/ping")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error testing connection: {str(e)}")
            return False
            
    async def get_kline_data(self, symbol: str, interval: str = "15") -> pd.DataFrame:
        """Obtiene datos de velas para un par"""
        try:
            crypto_id = self.crypto_ids.get(symbol)
            if not crypto_id:
                raise ValueError(f"Unsupported symbol: {symbol}")
                
            url = f"{self.base_url}/coins/{crypto_id}/market_chart"
            params = {
                "vs_currency": "usd",
                "days": 90,
                "interval": "daily"
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            df = pd.DataFrame(data['prices'], columns=['timestamp', 'close'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['volume'] = [x[1] for x in data['total_volumes']]
            
            # Calcular OHLC simulado (ya que CoinGecko solo da precios de cierre)
            df['open'] = df['close'].shift(1)
            df['high'] = df['close'] * 1.001  # Simulado
            df['low'] = df['close'] * 0.999   # Simulado
            
            # Calcular indicadores técnicos
            df['RSI'] = ta.momentum.RSIIndicator(df['close']).rsi()
            macd = ta.trend.MACD(df['close'])
            df['MACD'] = macd.macd()
            df['MACD_signal'] = macd.macd_signal()
            
            bollinger = ta.volatility.BollingerBands(df['close'])
            df['BB_high'] = bollinger.bollinger_hband()
            df['BB_low'] = bollinger.bollinger_lband()
            df['BB_mid'] = bollinger.bollinger_mavg()
            
            return df.set_index('timestamp')
            
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