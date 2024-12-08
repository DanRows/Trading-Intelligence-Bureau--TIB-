import pandas as pd
import aiohttp
import logging
from typing import Dict, Any, List, Optional
from src.config.settings import Settings

logger = logging.getLogger(__name__)

class CoingeckoConnector:
    """Conector para la API de Coingecko."""
    
    def __init__(self, settings: Settings):
        """
        Inicializa el conector de Coingecko.
        
        Args:
            settings: Configuración global
        """
        self.settings = settings
        self.base_url = "https://api.coingecko.com/api/v3"
        
    async def search_coins(self, query: str) -> List[Dict[str, Any]]:
        """
        Busca criptomonedas por nombre o símbolo.
        
        Args:
            query: Término de búsqueda
            
        Returns:
            Lista de monedas encontradas
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/search",
                    params={"query": query}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data['coins']
                    else:
                        logger.error(f"Error en búsqueda: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error buscando monedas: {str(e)}")
            return []
            
    async def get_coin_data(self, coin_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene datos detallados de una criptomoneda.
        
        Args:
            coin_id: ID de la moneda en Coingecko
            
        Returns:
            Dict con datos de la moneda
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/coins/{coin_id}",
                    params={
                        "localization": "false",
                        "tickers": "false",
                        "market_data": "true",
                        "community_data": "false",
                        "developer_data": "false"
                    }
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Error obteniendo datos: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error obteniendo datos de moneda: {str(e)}")
            return None
            
    async def get_coin_history(self, coin_id: str, days: int = 30) -> Optional[pd.DataFrame]:
        """
        Obtiene historial de precios de una criptomoneda.
        
        Args:
            coin_id: ID de la moneda
            days: Número de días de historial
            
        Returns:
            DataFrame con historial de precios
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/coins/{coin_id}/market_chart",
                    params={
                        "vs_currency": "usd",
                        "days": days,
                        "interval": "daily"
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Convertir a DataFrame
                        df = pd.DataFrame(data['prices'], columns=['timestamp', 'price'])
                        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                        df.set_index('timestamp', inplace=True)
                        
                        return df
                    else:
                        logger.error(f"Error obteniendo historial: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error obteniendo historial: {str(e)}")
            return None