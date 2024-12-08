import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import asyncio
import aiohttp
from aiohttp import ClientTimeout, ClientSession
from collections import OrderedDict
import json
from ..config.settings import Settings
from ..data.base_connector import RateLimiter, RateLimitError
from ..data.market_data_service import MarketDataService
import pandas as pd

logger = logging.getLogger(__name__)

class CacheEntry:
    """Entrada de caché con tiempo de expiración."""
    def __init__(self, data: Dict[str, Any], ttl_seconds: int = 60):
        self.data = data
        self.timestamp = datetime.utcnow()
        self.expires_at = self.timestamp + timedelta(seconds=ttl_seconds)
        
    @property
    def is_valid(self) -> bool:
        """Verifica si la entrada sigue siendo válida."""
        return datetime.utcnow() < self.expires_at

class RealtimeService:
    """Servicio de datos en tiempo real."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.base_url = "https://min-api.cryptocompare.com/data"
        self._session: Optional[ClientSession] = None
        self.rate_limiter = RateLimiter(
            max_requests=50,
            time_window=60
        )
        
        # Configuración de caché
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.cache_ttl = settings.CACHE_TTL
        self.cache_max_size = 100
        
        # Control de reconexión
        self.max_retries = 3
        self.retry_delay = 5
        self.last_error_time: Optional[datetime] = None
        self.error_count = 0
        
        # Tarea de actualización periódica
        self.update_task: Optional[asyncio.Task] = None
        self.update_interval = 60  # segundos
        
        self.market_data_service = MarketDataService()
        
    async def initialize(self):
        """Inicializa el servicio."""
        logger.info("Inicializando servicio de datos en tiempo real")
        try:
            await self._ensure_session()
            await self._test_connection()
            
            # Iniciar actualizaciones periódicas si está configurado
            if self.settings.get('ENABLE_AUTO_UPDATES', True):
                await self.start_periodic_updates()
                
            logger.info("Servicio inicializado correctamente")
            return self
            
        except Exception as e:
            logger.error(f"Error inicializando servicio: {str(e)}")
            raise
            
    async def _ensure_session(self) -> ClientSession:
        """Asegura que existe una sesión HTTP válida."""
        if self._session is None or self._session.closed:
            self._session = ClientSession(
                timeout=ClientTimeout(total=10),
                headers={'User-Agent': 'TIB/1.0'}
            )
        return self._session
        
    async def _test_connection(self) -> bool:
        """Prueba la conexión con la API."""
        try:
            session = await self._ensure_session()
            async with session.get(f"{self.base_url}/price?fsym=BTC&tsyms=USD") as response:
                if response.status == 200:
                    return True
                raise Exception(f"API error: {response.status}")
        except Exception as e:
            logger.error(f"Error en prueba de conexión: {str(e)}")
            raise
            
    async def get_full_data(self, symbol: str) -> Dict[str, Any]:
        """Obtiene datos completos con rate limiting."""
        async with self.rate_limiter:
            try:
                return await self._fetch_data(symbol)
            except RateLimitError:
                logger.warning("Rate limit alcanzado, usando caché si está disponible")
                return await self._get_cached_data(symbol)
            
    async def _fetch_data(self, symbol: str) -> Dict[str, Any]:
        """Obtiene datos frescos de la API."""
        if symbol not in self.symbols:
            raise ValueError(f"Símbolo no soportado: {symbol}")
            
        session = await self._ensure_session()
        url = f"{self.base_url}/pricemultifull"
        params = {
            "fsyms": self.symbols[symbol],
            "tsyms": "USD"
        }
        
        async with session.get(url, params=params) as response:
            if response.status != 200:
                raise Exception(f"Error API ({response.status})")
                
            data = await response.json()
            if 'RAW' not in data:
                raise Exception("Datos no disponibles")
                
            raw_data = data['RAW'][self.symbols[symbol]]['USD']
            return {
                'symbol': symbol,
                'price': raw_data.get('PRICE', 0),
                'volume_24h': raw_data.get('VOLUME24HOUR', 0),
                'high_24h': raw_data.get('HIGH24HOUR', 0),
                'low_24h': raw_data.get('LOW24HOUR', 0),
                'change_24h': raw_data.get('CHANGEPCT24HOUR', 0),
                'market_cap': raw_data.get('MKTCAP', 0),
                'last_update': datetime.fromtimestamp(raw_data.get('LASTUPDATE', 0)),
                'source': 'api'
            }
            
    async def _handle_error(self, error: Exception, symbol: str) -> Dict[str, Any]:
        """Maneja errores con reintentos y fallback a caché."""
        self.error_count += 1
        self.last_error_time = datetime.utcnow()
        
        logger.error(f"Error obteniendo datos para {symbol}: {str(error)}")
        
        # Intentar obtener datos antiguos de caché como fallback
        cache_key = f"full_data_{symbol}"
        cached = self._get_from_cache(cache_key, ignore_ttl=True)
        if cached:
            logger.warning(f"Usando datos antiguos de caché para {symbol}")
            cached['source'] = 'cache_expired'
            return cached
            
        raise error
        
    def _get_from_cache(self, key: str, ignore_ttl: bool = False) -> Optional[Dict[str, Any]]:
        """Obtiene datos de la caché."""
        if key in self.cache:
            entry = self.cache[key]
            if ignore_ttl or entry.is_valid:
                return entry.data
        return None
        
    def _add_to_cache(self, key: str, data: Dict[str, Any]) -> None:
        """Agrega datos a la caché."""
        self.cache[key] = CacheEntry(data, self.cache_ttl)
        
        # Mantener tamaño máximo de caché
        while len(self.cache) > self.cache_max_size:
            self.cache.popitem(last=False)
            
    async def start_periodic_updates(self):
        """Inicia actualizaciones periódicas."""
        if self.update_task is None or self.update_task.done():
            self.update_task = asyncio.create_task(self._update_loop())
            logger.info("Iniciadas actualizaciones periódicas")
            
    async def _update_loop(self):
        """Loop de actualización periódica."""
        while True:
            try:
                for symbol in self.symbols:
                    await self.get_full_data(symbol)
                await asyncio.sleep(self.update_interval)
            except Exception as e:
                logger.error(f"Error en actualización periódica: {str(e)}")
                await asyncio.sleep(self.retry_delay)
                
    async def close(self):
        """Cierra el servicio y libera recursos."""
        logger.info("Cerrando servicio de datos en tiempo real")
        
        if self.update_task and not self.update_task.done():
            self.update_task.cancel()
            
        if self._session and not self._session.closed:
            await self._session.close()
            
        self._session = None
        logger.info("Servicio cerrado correctamente")
        
    async def get_market_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Obtiene datos de mercado con validación."""
        try:
            data = await self._fetch_data(symbol)
            if not data:
                return None
                
            df = self.market_data_service.process_market_data(data)
            if df is not None:
                return df
                
            logger.error(f"Error procesando datos para {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo datos de mercado: {str(e)}")
            return None