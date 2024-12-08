from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd
import logging
import time
import asyncio
from src.config.settings import Settings
from src.utils.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

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
            
    @abstractmethod
    async def get_market_data(self, symbol: str) -> pd.DataFrame:
        """Obtiene datos de mercado para un símbolo."""
        pass
        
    @abstractmethod
    async def get_orderbook(self, symbol: str) -> Dict[str, Any]:
        """Obtiene el libro de órdenes para un símbolo."""
        pass
        
    @abstractmethod
    async def get_recent_trades(self, symbol: str) -> pd.DataFrame:
        """Obtiene trades recientes para un símbolo."""
        pass