import yfinance as yf
import pandas as pd
from typing import Dict, List, Any
import logging
from datetime import datetime, timedelta
from .base_connector import BaseExchangeConnector
import ta
import asyncio
from .websocket_service import WebSocketService

logger = logging.getLogger(__name__)

class YahooConnector(BaseExchangeConnector):
    def __init__(self, api_key: str = None, api_secret: str = None, testnet: bool = False):
        super().__init__(api_key, api_secret, testnet)
        self.trading_pairs = {
            "BTCUSDT": "BTC-USD",
            "ETHUSDT": "ETH-USD",
            "SOLUSDT": "SOL-USD",
            "BNBUSDT": "BNB-USD",
            "ADAUSDT": "ADA-USD"
        }
        self.ws_service = WebSocketService()
        self.realtime_data = {}
        
        # Iniciar websocket
        self.ws_service.connect(self._handle_ws_data)
        
        # Suscribirse a todos los pares
        for yahoo_symbol in self.trading_pairs.values():
            self.ws_service.subscribe(yahoo_symbol)
            
    def _handle_ws_data(self, data: Dict[str, Any]):
        """Maneja los datos recibidos por websocket"""
        try:
            symbol = data.get('symbol')
            if not symbol:
                return
                
            # Convertir al formato USDT
            pair = next(
                (k for k, v in self.trading_pairs.items() if v == symbol),
                None
            )
            if not pair:
                return
                
            self.realtime_data[pair] = {
                'price': data.get('price', 0),
                'volume': data.get('volume', 0),
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error handling websocket data: {str(e)}")
            
    def get_realtime_data(self, symbol: str) -> Dict[str, Any]:
        """Obtiene datos en tiempo real para un símbolo"""
        return self.realtime_data.get(symbol, {})

    def test_connection(self) -> bool:
        """Prueba la conexión con Yahoo Finance"""
        try:
            # Intentar obtener datos de Bitcoin como prueba
            ticker = yf.Ticker("BTC-USD")
            ticker.info
            logger.info("Conexión exitosa con Yahoo Finance")
            return True
        except Exception as e:
            logger.error(f"Error testing connection: {str(e)}")
            return False
            
    async def get_kline_data(self, symbol: str, interval: str = "1d") -> pd.DataFrame:
        """Obtiene datos de velas para un par"""
        try:
            # Convertir el símbolo al formato de Yahoo
            yahoo_symbol = self.trading_pairs.get(symbol)
            if not yahoo_symbol:
                raise ValueError(f"Símbolo no soportado: {symbol}")
            
            # Obtener datos históricos
            ticker = yf.Ticker(yahoo_symbol)
            df = ticker.history(
                period="1y",
                interval=interval
            )
            
            # Renombrar columnas para mantener consistencia
            df = df.rename(columns={
                'Open': 'Open',
                'High': 'High',
                'Low': 'Low',
                'Close': 'Close',
                'Volume': 'Volume'
            })
            
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
            
            # Agregar información adicional
            info = ticker.info
            df['market_cap'] = info.get('marketCap', 0)
            df['volume_24h'] = info.get('volume24Hr', 0)
            
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
                await asyncio.sleep(0.5)  # Evitar sobrecarga de la API
                market_data[pair] = await self.get_kline_data(pair)
            except Exception as e:
                logger.error(f"Error getting market data for {pair}: {str(e)}")
                errors.append(f"{pair}: {str(e)}")
                continue
                
        if errors and len(errors) == len(self.trading_pairs):
            raise Exception(f"Failed to get data for all pairs: {', '.join(errors)}")
            
        return market_data

    def get_available_pairs(self) -> List[str]:
        """Retorna la lista de pares disponibles"""
        return list(self.trading_pairs.keys())

    def __del__(self):
        """Cleanup al destruir el objeto"""
        self.ws_service.close()