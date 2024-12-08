import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any

class Settings:
    """Configuración global de la aplicación."""
    
    def __init__(self):
        # Cargar variables de entorno
        load_dotenv()
        
        # Rutas del proyecto
        self.PROJECT_ROOT = Path(__file__).parent.parent.parent
        self.SRC_PATH = self.PROJECT_ROOT / "src"
        self.DATA_PATH = self.SRC_PATH / "data"
        self.MODELS_PATH = self.PROJECT_ROOT / "models"
        self.RESULTS_PATH = self.PROJECT_ROOT / "results"
        
        # Crear directorios necesarios
        self.MODELS_PATH.mkdir(parents=True, exist_ok=True)
        self.RESULTS_PATH.mkdir(parents=True, exist_ok=True)
        
        # Configuración de API
        self.BYBIT_API_KEY = os.getenv("BYBIT_API_KEY", "")
        self.BYBIT_API_SECRET = os.getenv("BYBIT_API_SECRET", "")
        self.USE_TESTNET = os.getenv("USE_TESTNET", "true").lower() == "true"
        
        # Configuración de trading
        self.TRADING_PAIRS = os.getenv("TRADING_PAIRS", "BTCUSDT,ETHUSDT").split(",")
        self.DEFAULT_TIMEFRAME = os.getenv("DEFAULT_TIMEFRAME", "1h")
        self.INITIAL_CAPITAL = float(os.getenv("INITIAL_CAPITAL", "10000"))
        self.COMMISSION_RATE = float(os.getenv("COMMISSION_RATE", "0.001"))
        
        # Configuración de caché
        self.CACHE_TTL = int(os.getenv("CACHE_TTL", "300"))
        self.USE_REDIS = os.getenv("USE_REDIS", "false").lower() == "true"
        self.REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
        self.REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
        
    def get(self, key: str, default: Any = None) -> Any:
        """Obtiene un valor de configuración."""
        return getattr(self, key, default)
        
    @property
    def as_dict(self) -> Dict[str, Any]:
        """Retorna la configuración como diccionario."""
        return {k: v for k, v in self.__dict__.items() 
                if not k.startswith('_')}
        
    def setup_credentials(self):
        """Configura las credenciales a través de la interfaz de usuario."""
        st.sidebar.subheader("Configuración de APIs")
        
        # Bybit
        with st.sidebar.expander("Bybit", expanded=not bool(self.BYBIT_API_KEY)):
            new_bybit_key = st.text_input(
                "API Key",