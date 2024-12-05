import requests
import pandas as pd
from typing import Dict, Any
import logging
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

class RealtimeDataService:
    def __init__(self):
        self.cryptocompare_url = "https://min-api.cryptocompare.com/data/pricemultifull"
        self.coingecko_url = "https://api.coingecko.com/api/v3"
        self.symbols = {
            "BTCUSDT": {"cryptocompare": "BTC", "coingecko": "bitcoin"},
            "ETHUSDT": {"cryptocompare": "ETH", "coingecko": "ethereum"},
            "SOLUSDT": {"cryptocompare": "SOL", "coingecko": "solana"}
        }
        
    async def get_realtime_prices(self) -> Dict[str, Any]:
        """Obtiene precios en tiempo real de CryptoCompare"""
        try:
            symbols = ",".join([s["cryptocompare"] for s in self.symbols.values()])
            params = {
                "fsyms": symbols,
                "tsyms": "USD"
            }
            
            response = requests.get(self.cryptocompare_url, params=params)
            data = response.json()
            
            if "RAW" not in data:
                raise Exception("No data received from CryptoCompare")
                
            realtime_data = {}
            for pair, info in self.symbols.items():
                symbol = info["cryptocompare"]
                if symbol in data["RAW"] and "USD" in data["RAW"][symbol]:
                    raw_data = data["RAW"][symbol]["USD"]
                    realtime_data[pair] = {
                        "price": raw_data["PRICE"],
                        "change_24h": raw_data["CHANGEPCT24HOUR"],
                        "volume_24h": raw_data["VOLUME24HOUR"],
                        "high_24h": raw_data["HIGH24HOUR"],
                        "low_24h": raw_data["LOW24HOUR"],
                        "last_update": datetime.fromtimestamp(raw_data["LASTUPDATE"])
                    }
                    
            return realtime_data
            
        except Exception as e:
            logger.error(f"Error getting realtime prices: {str(e)}")
            return {}
            
    async def get_market_info(self) -> Dict[str, Any]:
        """Obtiene información de mercado de CoinGecko"""
        try:
            coin_ids = ",".join([s["coingecko"] for s in self.symbols.values()])
            url = f"{self.coingecko_url}/simple/price"
            params = {
                "ids": coin_ids,
                "vs_currencies": "usd",
                "include_market_cap": "true",
                "include_24hr_vol": "true",
                "include_24hr_change": "true",
                "include_last_updated_at": "true"
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            market_data = {}
            for pair, info in self.symbols.items():
                coin_id = info["coingecko"]
                if coin_id in data:
                    coin_data = data[coin_id]
                    market_data[pair] = {
                        "market_cap": coin_data["usd_market_cap"],
                        "volume": coin_data["usd_24h_vol"],
                        "change_24h": coin_data["usd_24h_change"],
                        "last_update": datetime.fromtimestamp(coin_data["last_updated_at"])
                    }
                    
            return market_data
            
        except Exception as e:
            logger.error(f"Error getting market info: {str(e)}")
            return {}
            
    async def update_realtime_data(self) -> Dict[str, Any]:
        """Actualiza todos los datos en tiempo real"""
        prices = await self.get_realtime_prices()
        market = await self.get_market_info()
        
        combined_data = {}
        for pair in self.symbols:
            combined_data[pair] = {
                **prices.get(pair, {}),
                **market.get(pair, {})
            }
            
        return combined_data 