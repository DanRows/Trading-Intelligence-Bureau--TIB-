from typing import Dict, Any, Optional
import time
import redis
import logging
from ..config.settings import Settings

logger = logging.getLogger(__name__)

class CacheManager:
    """Gestor de caché con soporte para memoria local y Redis."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.local_cache: Dict[str, Dict[str, Any]] = {}
        self.redis_client = None
        
        if settings.USE_REDIS:
            try:
                self.redis_client = redis.Redis(
                    host=os.getenv("REDIS_HOST", "localhost"),
                    port=int(os.getenv("REDIS_PORT", "6379")),
                    db=0
                )
                logger.info("Redis cache initialized")
            except Exception as e:
                logger.error(f"Error initializing Redis: {e}")
                
    async def get(self, key: str) -> Optional[Any]:
        """Obtiene un valor del caché."""
        try:
            # Intentar Redis primero si está disponible
            if self.redis_client:
                value = self.redis_client.get(key)
                if value:
                    return json.loads(value)
                    
            # Fallback a caché local
            if key in self.local_cache:
                cache_data = self.local_cache[key]
                if time.time() < cache_data['expires_at']:
                    return cache_data['value']
                else:
                    del self.local_cache[key]
                    
            return None
            
        except Exception as e:
            logger.error(f"Error getting from cache: {e}")
            return None
            
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Guarda un valor en el caché."""
        try:
            ttl = ttl or self.settings.CACHE_TTL
            
            # Guardar en Redis si está disponible
            if self.redis_client:
                self.redis_client.setex(
                    key,
                    ttl,
                    json.dumps(value)
                )
                
            # Guardar en caché local
            self.local_cache[key] = {
                'value': value,
                'expires_at': time.time() + ttl
            }
            
        except Exception as e:
            logger.error(f"Error setting cache: {e}")
            
    async def invalidate(self, key: str) -> None:
        """Invalida una clave del caché."""
        try:
            if self.redis_client:
                self.redis_client.delete(key)
            if key in self.local_cache:
                del self.local_cache[key]
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}") 