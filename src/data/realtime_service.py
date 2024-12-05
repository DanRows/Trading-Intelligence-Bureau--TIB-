import requests
import logging
from typing import Dict, Any, List
from datetime import datetime
import asyncio
import aiohttp
from aiohttp import ClientTimeout

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
        self.timeout = ClientTimeout(total=10)  # 10 segundos de timeout
        
    async def get_current_price(self, symbol: str) -> Dict[str, Any]:
        """Obtiene el precio actual de un símbolo"""
        try:
            crypto_symbol = self.symbols.get(symbol)
            if not crypto_symbol:
                logger.warning(f"Símbolo no soportado: {symbol}")
                return {}
                
            url = f"{self.base_url}/price"
            params = {
                "fsym": crypto_symbol,
                "tsyms": "USD",
                "e": "Binance"
            }
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'USD' in data:
                            return {
                                'price': data['USD'],
                                'timestamp': datetime.now(),
                                'symbol': symbol
                            }
                    else:
                        logger.error(f"Error en la API: {response.status} - {await response.text()}")
            return {}
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout obteniendo precio para {symbol}")
            return {}
        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {str(e)}")
            return {}
            
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
                "tsyms": "USD",
                "e": "Binance"
            }
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
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
                    else:
                        logger.error(f"Error en la API: {response.status} - {await response.text()}")
            return {}
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout obteniendo datos para {symbol}")
            return {}
        except Exception as e:
            logger.error(f"Error getting full data for {symbol}: {str(e)}")
            return {}
            
    async def update_all_symbols(self) -> Dict[str, Dict[str, Any]]:
        """Actualiza los datos de todos los símbolos"""
        try:
            tasks = []
            for symbol in self.symbols:
                tasks.append(self.get_full_data(symbol))
                
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for symbol, data in zip(self.symbols, results):
                if isinstance(data, Exception):
                    logger.error(f"Error updating {symbol}: {str(data)}")
                    continue
                if data:
                    self.realtime_data[symbol] = data
                    
            return self.realtime_data
            
        except Exception as e:
            logger.error(f"Error updating all symbols: {str(e)}")
            return {}
        
    def get_available_symbols(self) -> List[str]:
        """Retorna la lista de símbolos disponibles"""
        return list(self.symbols.keys())
        
    def get_last_data(self, symbol: str) -> Dict[str, Any]:
        """Retorna los últimos datos almacenados para un símbolo"""
        return self.realtime_data.get(symbol, {})