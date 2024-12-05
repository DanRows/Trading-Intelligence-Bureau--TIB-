import websocket
import json
import logging
from typing import Dict, Any, Callable
import threading
from queue import Queue
import time

logger = logging.getLogger(__name__)

class WebSocketService:
    def __init__(self):
        self.ws = None
        self.data_queue = Queue()
        self.subscriptions = {}
        self.is_connected = False
        self.reconnect_delay = 5  # segundos
        
    def connect(self, on_data: Callable[[Dict[str, Any]], None]):
        """Inicia la conexión websocket"""
        def on_message(ws, message):
            try:
                data = json.loads(message)
                self.data_queue.put(data)
                on_data(data)
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")

        def on_error(ws, error):
            logger.error(f"WebSocket error: {str(error)}")
            self.is_connected = False

        def on_close(ws, close_status_code, close_msg):
            logger.info("WebSocket connection closed")
            self.is_connected = False
            # Intentar reconexión
            time.sleep(self.reconnect_delay)
            self.connect(on_data)

        def on_open(ws):
            logger.info("WebSocket connection established")
            self.is_connected = True
            # Suscribirse a los símbolos
            for symbol in self.subscriptions:
                self.subscribe(symbol)

        # Configurar websocket
        self.ws = websocket.WebSocketApp(
            "wss://streamer.finance.yahoo.com/",
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_open=on_open
        )

        # Iniciar websocket en un hilo separado
        ws_thread = threading.Thread(target=self.ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()

    def subscribe(self, symbol: str):
        """Suscribe a un símbolo"""
        if not self.is_connected:
            self.subscriptions[symbol] = True
            return

        try:
            subscribe_message = {
                "subscribe": [f"{symbol}"]
            }
            self.ws.send(json.dumps(subscribe_message))
            logger.info(f"Subscribed to {symbol}")
        except Exception as e:
            logger.error(f"Error subscribing to {symbol}: {str(e)}")

    def unsubscribe(self, symbol: str):
        """Cancela la suscripción a un símbolo"""
        if symbol in self.subscriptions:
            del self.subscriptions[symbol]

        if self.is_connected:
            try:
                unsubscribe_message = {
                    "unsubscribe": [f"{symbol}"]
                }
                self.ws.send(json.dumps(unsubscribe_message))
                logger.info(f"Unsubscribed from {symbol}")
            except Exception as e:
                logger.error(f"Error unsubscribing from {symbol}: {str(e)}")

    def close(self):
        """Cierra la conexión websocket"""
        if self.ws:
            self.ws.close()
            self.is_connected = False 