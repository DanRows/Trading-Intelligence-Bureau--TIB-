import pandas as pd
from typing import Dict
import logging
from datetime import datetime, timedelta
from .base_connector import BaseExchangeConnector
import ta
import ccxt

logger = logging.getLogger(__name__)

class BinanceConnector(BaseExchangeConnector):
    def __init__(self, api_key: str = "", api_secret: str = "", testnet: bool = False):
        super().__init__(api_key, api_secret, testnet)
        self.exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot'
            }
        })
        if testnet:
            self.exchange.set_sandbox_mode(True)
        
    def test_connection(self) -> bool:
        """Prueba la conexión con Binance"""
        try:
            self.exchange.fetch_ticker('BTC/USDT')
            logger.info("Conexión exitosa con Binance")
            return True
        except Exception as e:
            logger.error(f"Error testing connection: {str(e)}")
            return False
            
    async def get_kline_data(self, symbol: str, interval: str = "1d") -> pd.DataFrame:
        """Obtiene datos de velas para un par"""
        try:
            # Convertir el símbolo al formato de CCXT
            ccxt_symbol = symbol.replace('USDT', '/USDT')
            
            # Obtener datos
            ohlcv = self.exchange.fetch_ohlcv(
                ccxt_symbol,
                interval,
                limit=365  # 1 año de datos
            )
            
            # Convertir a DataFrame
            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']
            )
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # Calcular indicadores técnicos
            df['RSI'] = ta.momentum.RSIIndicator(df['Close']).rsi()
            
            macd = ta.trend.MACD(df['Close'])
            df['MACD'] = macd.macd()
            df['MACD_signal'] = macd.macd_signal()
            
            bollinger = ta.volatility.BollingerBands(df['Close'])
            df['BB_high'] = bollinger.bollinger_hband()
            df['BB_low'] = bollinger.bollinger_lband()
            df['BB_mid'] = bollinger.bollinger_mavg()
            
            # Promedios Móviles
            df['SMA_20'] = ta.trend.sma_indicator(df['Close'], window=20)
            df['SMA_50'] = ta.trend.sma_indicator(df['Close'], window=50)
            df['SMA_200'] = ta.trend.sma_indicator(df['Close'], window=200)
            
            return df
            
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