import asyncio
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class RateLimiter:
    """Implementación de rate limiting usando Token Bucket."""
    
    def __init__(self, max_requests: int, time_window: float):
        self.max_requests = max_requests
        self.time_window = time_window
        self.tokens = max_requests
        self.last_update = time.monotonic()
        self.lock = asyncio.Lock()
        
    async def acquire(self) -> None:
        """Adquiere un token para realizar una petición."""
        async with self.lock:
            now = time.monotonic()
            
            # Rellenar tokens basado en tiempo transcurrido
            time_passed = now - self.last_update
            self.tokens = min(
                self.max_requests,
                self.tokens + (time_passed * self.max_requests / self.time_window)
            )
            self.last_update = now
            
            if self.tokens < 1:
                wait_time = (1 - self.tokens) * (self.time_window / self.max_requests)
                logger.debug(f"Rate limit: esperando {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
                self.tokens = 1
                
            self.tokens -= 1
            
    async def __aenter__(self):
        await self.acquire()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass 