from typing import Dict, Type
import logging
from src.config.settings import Settings
from src.data.base_connector import BaseConnector
from src.data.bybit_connector import BybitConnector

logger = logging.getLogger(__name__)

class ExchangeFactory:
    """Factory para crear conectores de exchanges."""
    
    _connectors: Dict[str, Type[BaseConnector]] = {
        'bybit': BybitConnector
    }
    
    @staticmethod
    def create_exchange(settings: Settings) -> BaseConnector:
        """
        Crea una instancia del conector apropiado.
        
        Args:
            settings: Configuración global
            
        Returns:
            Instancia de BaseConnector
        
        Raises:
            ValueError: Si el exchange no está soportado
        """
        try:
            exchange_name = settings.get('EXCHANGE', 'bybit').lower()
            
            if exchange_name not in ExchangeFactory._connectors:
                raise ValueError(f"Exchange no soportado: {exchange_name}")
                
            connector_class = ExchangeFactory._connectors[exchange_name]
            return connector_class(settings)
            
        except Exception as e:
            logger.error(f"Error creando conector: {str(e)}")
            raise