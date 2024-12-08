from typing import Dict, Any
from dotenv import load_dotenv
import os

class Settings:
    """Configuración global de la aplicación."""
    
    def __init__(self):
        load_dotenv()
        
        # API Keys
        self.BYBIT_API_KEY = os.getenv("BYBIT_API_KEY")
        self.BYBIT_API_SECRET = os.getenv("BYBIT_API_SECRET")
        
        # Cache settings
        self.CACHE_TTL = int(os.getenv("CACHE_TTL", "300"))  # 5 minutos por defecto
        self.USE_REDIS = os.getenv("USE_REDIS", "false").lower() == "true"
        
        # ML settings
        self.ML_MODELS_PATH = os.getenv("ML_MODELS_PATH", "models")
        self.DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "lstm_model")
        
        # Trading settings
        self.TRADING_PAIRS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
        self.DEFAULT_TIMEFRAME = "1h"
        
    @property
    def as_dict(self) -> Dict[str, Any]:
        """Retorna la configuración como diccionario."""
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')} 