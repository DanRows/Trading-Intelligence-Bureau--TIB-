import requests
import logging
from typing import Dict, Any, List
from datetime import datetime
import asyncio
import aiohttp
from aiohttp import ClientTimeout, ClientSession

logger = logging.getLogger(__name__)

class RealtimeService:
    def __init__(self):
        self.base_url = "https://min-api.cryptocompare.com/data"
        self.symbols = {
            "BTCUSDT": "BTC",
            "ETHUSDT": "ETH",
            "SOLUSDT": "SOL",
            "BNBUSDT": "BNB",
            "ADAUSDT": "ADA"
        }
        self.realtime_data = {}
        self._session = None
        
    @property
    def session(self) -> ClientSession:
        """Obtiene o crea una sesión HTTP"""
        if self._session is None or self._session.closed:
            self._session = ClientSession(
                timeout=ClientTimeout(total=10),
                raise_for_status=False
            )
        return self._session
        
    async def initialize(self):
        """Inicializa el servicio de manera asíncrona"""
        if self._session is None:
            self._session = self.session
        return self
        
    async def get_full_data(self, symbol: str) -> Dict[str, Any]:
        """Obtiene datos completos de un símbolo"""
        try:
            crypto_symbol = self.symbols.get(symbol)
            if not crypto_symbol:
                logger.warning(f"Símbolo no soportado: {symbol}")
                return {}
                
            url = f"{self.base_url}/pricemultifull"
            params = {
                "fsyms": crypto_symbol,
                "tsyms": "USD"
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    logger.error(f"Error API ({response.status}): {await response.text()}")
                    return {}
                    
                data = await response.json()
                if 'RAW' in data and crypto_symbol in data['RAW']:
                    raw_data = data['RAW'][crypto_symbol]['USD']
                    return {
                        'symbol': symbol,
                        'price': raw_data.get('PRICE', 0),
                        'volume_24h': raw_data.get('VOLUME24HOUR', 0),
                        'high_24h': raw_data.get('HIGH24HOUR', 0),
                        'low_24h': raw_data.get('LOW24HOUR', 0),
                        'change_24h': raw_data.get('CHANGEPCT24HOUR', 0),
                        'market_cap': raw_data.get('MKTCAP', 0),
                        'last_update': datetime.fromtimestamp(raw_data.get('LASTUPDATE', 0)),
                        'supply': raw_data.get('SUPPLY', 0)
                    }
                return {}
                
        except Exception as e:
            logger.error(f"Error getting data for {symbol}: {str(e)}")
            return {}
            
    async def close(self):
        """Cierra la sesión HTTP de manera segura"""
        if self._session and not self._session.closed:
            try:
                await self._session.close()
            except Exception as e:
                logger.error(f"Error closing session: {str(e)}")
            finally:
                self._session = None