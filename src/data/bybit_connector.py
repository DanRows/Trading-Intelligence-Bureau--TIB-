import pandas as pd
from typing import Dict, Any, Optional
import logging
import asyncio
from pybit.unified_trading import HTTP
from src.data.base_connector import BaseConnector
from src.config.settings import Settings

logger = logging.getLogger(__name__)

class BybitConnector(BaseConnector):
    """Conector para Bybit."""
    
    def __init__(self, settings: Settings):
        """
        Inicializa el conector de Bybit.
        
        Args:
            settings: Configuración global
        """
        super().__init__(settings)
        self.client = HTTP(
            testnet=settings.USE_TESTNET,
            api_key=settings.BYBIT_API_KEY,
            api_secret=settings.BYBIT_API_SECRET
        )
        
    async def get_market_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Obtiene datos de mercado para un símbolo."""
        try:
            # Ejecutar la llamada HTTP en un thread separado para no bloquear
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.get_kline(
                    category="spot",
                    symbol=symbol,
                    interval="15",
                    limit=100
                )
            )
            
            if not response or 'result' not in response or 'list' not in response['result']:
                logger.error(f"Respuesta inválida del API de Bybit: {response}")
                return None
            
            df = pd.DataFrame(response['result']['list'])
            if df.empty:
                logger.warning(f"No hay datos disponibles para {symbol}")
                return None
                
            df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover']
            df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            return df.sort_values('timestamp')
            
        except Exception as e:
            logger.error(f"Error obteniendo datos de mercado: {str(e)}")
            return None
            
    async def get_orderbook(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Obtiene el libro de órdenes para un símbolo."""
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.get_orderbook(
                    category="spot",
                    symbol=symbol,
                    limit=20
                )
            )
            
            if not response or 'result' not in response:
                logger.error(f"Respuesta inválida del API de Bybit: {response}")
                return None
                
            return {
                'bids': response['result']['b'],
                'asks': response['result']['a']
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo orderbook: {str(e)}")
            return None
            
    async def get_recent_trades(self, symbol: str) -> Optional[pd.DataFrame]:
        """Obtiene trades recientes para un símbolo."""
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.get_public_trade_history(
                    category="spot",
                    symbol=symbol,
                    limit=20
                )
            )
            
            if not response or 'result' not in response or 'list' not in response['result']:
                logger.error(f"Respuesta inválida del API de Bybit: {response}")
                return None
                
            df = pd.DataFrame(response['result']['list'])
            if df.empty:
                logger.warning(f"No hay trades recientes para {symbol}")
                return None
                
            df.columns = ['timestamp', 'price', 'size', 'side']
            df[['price', 'size']] = df[['price', 'size']].astype(float)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            return df
            
        except Exception as e:
            logger.error(f"Error obteniendo trades recientes: {str(e)}")
            return None
            
    async def get_trading_pairs(self) -> list:
        """Obtiene la lista de pares de trading disponibles."""
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.get_instruments_info(
                    category="spot"
                )
            )
            
            if not response or 'result' not in response or 'list' not in response['result']:
                logger.error(f"Respuesta inválida del API de Bybit: {response}")
                return self.trading_pairs
                
            pairs = [item['symbol'] for item in response['result']['list']]
            return pairs if pairs else self.trading_pairs
            
        except Exception as e:
            logger.error(f"Error obteniendo pares de trading: {str(e)}")
            return self.trading_pairs