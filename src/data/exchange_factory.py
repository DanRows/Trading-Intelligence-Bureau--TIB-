from typing import Optional
from .base_connector import BaseExchangeConnector
from .bybit_connector import BybitConnector
from .yahoo_connector import YahooConnector
from .binance_connector import BinanceConnector

class ExchangeFactory:
    @staticmethod
    def create_connector(
        exchange: str,
        api_key: str = "",
        api_secret: str = "",
        testnet: bool = False
    ) -> Optional[BaseExchangeConnector]:
        """
        Crea un conector para el exchange especificado
        
        Args:
            exchange: Nombre del exchange ('bybit', 'binance', 'yahoo')
            api_key: API key (opcional para Yahoo)
            api_secret: API secret (opcional para Yahoo)
            testnet: Si se debe usar testnet
        """
        exchange = exchange.lower()
        
        if exchange == 'bybit':
            return BybitConnector(api_key, api_secret, testnet)
        elif exchange == 'binance':
            return BinanceConnector(api_key, api_secret, testnet)
        elif exchange == 'yahoo':
            return YahooConnector()
        else:
            return None 