import requests
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
import aiohttp
from aiohttp import ClientTimeout, ClientSession, ClientError, ServerDisconnectedError
from functools import wraps
import backoff

logger = logging.getLogger(__name__)

def retry_on_error(max_tries=3, delay=1):
    """Decorador para reintentar operaciones con backoff exponencial"""
    def decorator(func):
        @backoff.on_exception(
            backoff.expo,
            (ClientError, ServerDisconnectedError, asyncio.TimeoutError),
            max_tries=max_tries,
            on_backoff=lambda details: logger.warning(
                f"Reintentando {func.__name__} después de {details['wait']} segundos..."
            )
        )
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error en {func.__name__}: {str(e)}", exc_info=True)
                raise
        return wrapper
    return decorator

class RealtimeService:
    def __init__(self):
        logger.info("Inicializando RealtimeService")
        self.base_url = "https://min-api.cryptocompare.com/data"
        self.symbols = {
            "BTCUSDT": "BTC",
            "ETHUSDT": "ETH",
            "SOLUSDT": "SOL",
            "BNBUSDT": "BNB",
            "ADAUSDT": "ADA"
        }
        self.realtime_data = {}
        self._session: Optional[ClientSession] = None
        
    async def _ensure_session(self) -> ClientSession:
        """Asegura que existe una sesión válida"""
        if self._session is None or self._session.closed:
            logger.debug("Creando nueva sesión HTTP")
            self._session = ClientSession(
                timeout=ClientTimeout(total=10),
                raise_for_status=False
            )
        return self._session
        
    async def initialize(self):
        """Inicializa el servicio de manera asíncrona"""
        logger.info("Inicializando sesión HTTP")
        try:
            await self._ensure_session()
            logger.info("Sesión HTTP inicializada correctamente")
        except Exception as e:
            logger.error(f"Error inicializando sesión: {str(e)}", exc_info=True)
            raise
        return self
        
    @retry_on_error(max_tries=3)
    async def get_full_data(self, symbol: str) -> Dict[str, Any]:
        """Obtiene datos completos de un símbolo"""
        logger.debug(f"Obteniendo datos para {symbol}")
        try:
            session = await self._ensure_session()
            
            crypto_symbol = self.symbols.get(symbol)
            if not crypto_symbol:
                logger.warning(f"Símbolo no soportado: {symbol}")
                return {}
                
            url = f"{self.base_url}/pricemultifull"
            params = {
                "fsyms": crypto_symbol,
                "tsyms": "USD"
            }
            
            logger.debug(f"Realizando petición HTTP a {url}")
            try:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Error API ({response.status}): {error_text}")
                        return {}
                        
                    data = await response.json()
                    logger.debug(f"Respuesta recibida para {symbol}")
                    
                    if 'RAW' in data and crypto_symbol in data['RAW']:
                        raw_data = data['RAW'][crypto_symbol]['USD']
                        result = {
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
                        logger.debug(f"Datos procesados para {symbol}: {result}")
                        return result
                        
                    logger.warning(f"Datos no encontrados para {symbol}")
                    return {}
            except Exception as e:
                logger.error(f"Error en petición HTTP: {str(e)}", exc_info=True)
                # Recrear sesión en caso de error
                await self.close()
                return {}
                
        except asyncio.CancelledError:
            logger.warning(f"Operación cancelada para {symbol}")
            raise
        except Exception as e:
            logger.error(f"Error obteniendo datos para {symbol}: {str(e)}", exc_info=True)
            return {}
            
    async def close(self):
        """Cierra la sesión HTTP de manera segura"""
        logger.info("Cerrando sesión HTTP")
        if self._session:
            try:
                if not self._session.closed:
                    logger.debug("Iniciando cierre de sesión")
                    await self._session.close()
                    logger.info("Sesión cerrada correctamente")
            except Exception as e:
                logger.error(f"Error cerrando sesión: {str(e)}", exc_info=True)
            finally:
                self._session = None
                logger.debug("Referencia a sesión eliminada")