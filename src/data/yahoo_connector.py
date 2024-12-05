import yfinance as yf
import pandas as pd
from typing import Dict
import logging
from datetime import datetime, timedelta
from .base_connector import BaseExchangeConnector
import ta

logger = logging.getLogger(__name__)

class YahooConnector(BaseExchangeConnector):
    def __init__(self, api_key: str = "", api_secret: str = "", testnet: bool = False):
        super().__init__(api_key, api_secret, testnet)
        self.trading_pairs = {
            "BTCUSDT": "BTC-USD",
            "ETHUSDT": "ETH-USD",
            "SOLUSDT": "SOL-USD"
        }
        
    def test_connection(self) -> bool:
        """Prueba la conexión con Yahoo Finance"""
        try:
            symbol = "BTC-USD"
            yf.download(symbol, period="1d")
            logger.info("Conexión exitosa con Yahoo Finance")
            return True
        except Exception as e:
            logger.error(f"Error testing connection: {str(e)}")
            return False
            
    async def get_kline_data(self, symbol: str, interval: str = "1d") -> pd.DataFrame:
        """Obtiene datos de velas para un par"""
        try:
            yahoo_symbol = self.trading_pairs.get(symbol)
            if not yahoo_symbol:
                raise ValueError(f"Unsupported symbol: {symbol}")
                
            df = yf.download(
                yahoo_symbol,
                start=(datetime.now() - timedelta(days=365)),
                end=datetime.now(),
                interval=interval
            )
            
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