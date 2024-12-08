from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd
import logging
import time
import asyncio
from ..config.settings import Settings

logger = logging.getLogger(__name__)

class RateLimitError(Exception):
    """Error específico para rate limiting."""
    pass

class BaseConnector(ABC):
    """Clase base para conectores de exchanges."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.trading_pairs = settings.TRADING_PAIRS
        
        # Rate limiting
        self.request_counts: Dict[str, int] = {}
        self.last_request_time: Dict[str, float] = {}
        self.rate_limits = {
            'default': {'requests': 60, 'period': 60},  # 60 requests por minuto
            'market_data': {'requests': 120, 'period': 60},  # 120 requests por minuto
            'trading': {'requests': 30, 'period': 60}  # 30 requests por minuto
        }
        
    async def _rate_limit(self, endpoint_type: str = 'default') -> None:
        """
        Implementa rate limiting para las peticiones.
        
        Args:
            endpoint_type: Tipo de endpoint ('default', 'market_data', 'trading')
        """
        try:
            now = time.time()
            limit = self.rate_limits.get(endpoint_type, self.rate_limits['default'])
            
            # Inicializar contadores si no existen
            if endpoint_type not in self.request_counts:
                self.request_counts[endpoint_type] = 0
                self.last_request_time[endpoint_type] = now
                
            # Reiniciar contador si ha pasado el período
            if now - self.last_request_time[endpoint_type] >= limit['period']:
                self.request_counts[endpoint_type] = 0
                self.last_request_time[endpoint_type] = now
                
            # Verificar límite
            if self.request_counts[endpoint_type] >= limit['requests']:
                wait_time = limit['period'] - (now - self.last_request_time[endpoint_type])
                if wait_time > 0:
                    logger.warning(f"Rate limit alcanzado para {endpoint_type}, esperando {wait_time:.2f}s")
                    await asyncio.sleep(wait_time)
                    # Reiniciar después de esperar
                    self.request_counts[endpoint_type] = 0
                    self.last_request_time[endpoint_type] = time.time()
                    
            # Incrementar contador
            self.request_counts[endpoint_type] += 1
            
        except Exception as e:
            logger.error(f"Error en rate limiting: {str(e)}")
            raise
            
    async def _make_request(self, 
                           endpoint_type: str,
                           request_func: callable,
                           *args,
                           max_retries: int = 3,
                           **kwargs) -> Any:
        """
        Realiza una petición con rate limiting y reintentos.
        
        Args:
            endpoint_type: Tipo de endpoint
            request_func: Función que realiza la petición
            max_retries: Número máximo de reintentos
            
        Returns:
            Respuesta de la petición
        """
        retries = 0
        while retries < max_retries:
            try:
                await self._rate_limit(endpoint_type)
                return await request_func(*args, **kwargs)
                
            except RateLimitError:
                wait_time = (2 ** retries) * 10  # Backoff exponencial
                logger.warning(f"Rate limit alcanzado, reintento {retries + 1}/{max_retries} en {wait_time}s")
                await asyncio.sleep(wait_time)
                retries += 1
                
            except Exception as e:
                logger.error(f"Error en petición: {str(e)}")
                raise
                
        raise RateLimitError(f"Máximo de reintentos alcanzado para {endpoint_type}")
        
    @abstractmethod
    def test_connection(self) -> bool:
        """Prueba la conexión con el exchange"""
        pass
        
    @abstractmethod
    async def get_kline_data(self, symbol: str, interval: str = "15") -> pd.DataFrame:
        """Obtiene datos de velas para un par"""
        pass
        
    @abstractmethod
    async def get_market_data(self) -> Dict[str, pd.DataFrame]:
        """Obtiene datos de todos los pares"""
        pass 