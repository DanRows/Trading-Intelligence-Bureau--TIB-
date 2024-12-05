from typing import Optional
from .base_connector import BaseExchangeConnector
from .bybit_connector import BybitConnector
from .binance_connector import BinanceConnector
from .coingecko_connector import CoinGeckoConnector

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
            exchange: Nombre del exchange ('bybit', 'binance', 'coingecko')
            api_key: API key (opcional para CoinGecko)
            api_secret: API secret (opcional para CoinGecko)
            testnet: Si se debe usar testnet
        """
        exchange = exchange.lower()
        
        if exchange == 'bybit':
            return BybitConnector(api_key, api_secret, testnet)
        elif exchange == 'binance':
            return BinanceConnector(api_key, api_secret, testnet)
        elif exchange == 'coingecko':
            return CoinGeckoConnector()
        else:
            return None 