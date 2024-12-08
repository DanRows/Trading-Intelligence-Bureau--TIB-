import json
import logging
import websockets
import asyncio
from typing import Dict, Any, Optional, Callable
from datetime import datetime

logger = logging.getLogger(__name__)

class WebSocketService:
    """Servicio de WebSocket para datos en tiempo real."""
    
    def __init__(self, url: str, on_message: Callable[[Dict[str, Any]], None]):
        self.url = url
        self.on_message = on_message
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.is_connected = False
        self.last_message_time: Optional[datetime] = None
        self.reconnect_delay = 5  # segundos
        self.max_reconnect_delay = 300  # 5 minutos
        
    async def connect(self):
        """Establece conexión WebSocket con reintentos."""
        while True:
            try:
                async with websockets.connect(self.url) as websocket:
                    self.ws = websocket
                    self.is_connected = True
                    logger.info("Conexión WebSocket establecida")
                    await self._handle_messages()
                    
            except websockets.exceptions.ConnectionClosed:
                logger.warning("Conexión WebSocket cerrada, reintentando...")
                await self._handle_reconnection()
                
            except Exception as e:
                logger.error(f"Error en WebSocket: {str(e)}")
                await self._handle_reconnection()
                
    async def _handle_messages(self):
        """Procesa mensajes entrantes del WebSocket."""
        try:
            async for message in self.ws:
                try:
                    # Validar que el mensaje no esté vacío
                    if not message:
                        logger.warning("Mensaje WebSocket vacío recibido")
                        continue
                        
                    # Intentar parsear el JSON
                    data = json.loads(message)
                    
                    # Validar estructura básica
                    if not isinstance(data, dict):
                        logger.warning(f"Formato de mensaje inesperado: {type(data)}")
                        continue
                        
                    # Procesar mensaje
                    self.last_message_time = datetime.utcnow()
                    await self.on_message(data)
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Error decodificando mensaje JSON: {str(e)}")
                    continue
                    
                except Exception as e:
                    logger.error(f"Error procesando mensaje: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error en el loop de mensajes: {str(e)}")
            self.is_connected = False
            raise
            
    async def _handle_reconnection(self):
        """Maneja la reconexión con backoff exponencial."""
        self.is_connected = False
        delay = self.reconnect_delay
        
        while not self.is_connected:
            logger.info(f"Reintentando conexión en {delay} segundos...")
            await asyncio.sleep(delay)
            
            try:
                await self.connect()
                self.reconnect_delay = 5  # Reset delay on successful connection
                break
                
            except Exception as e:
                logger.error(f"Error en reconexión: {str(e)}")
                delay = min(delay * 2, self.max_reconnect_delay)
                
    async def send(self, data: Dict[str, Any]):
        """Envía datos por el WebSocket."""
        if not self.is_connected:
            raise ConnectionError("WebSocket no conectado")
            
        try:
            await self.ws.send(json.dumps(data))
        except Exception as e:
            logger.error(f"Error enviando mensaje: {str(e)}")
            self.is_connected = False
            raise
            
    async def close(self):
        """Cierra la conexión WebSocket."""
        if self.ws:
            await self.ws.close()
        self.is_connected = False
        logger.info("Conexión WebSocket cerrada") 