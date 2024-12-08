import os
from pathlib import Path
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

class Settings:
    """Configuración global de la aplicación."""
    
    def __init__(self):
        """Inicializa la configuración."""
        # Cargar variables de entorno
        load_dotenv()
        
        # Credenciales de Bybit
        self.BYBIT_API_KEY = os.getenv("BYBIT_API_KEY", "")
        self.BYBIT_API_SECRET = os.getenv("BYBIT_API_SECRET", "")
        self.USE_TESTNET = os.getenv("USE_TESTNET", "true").lower() == "true"
        
        # Fuentes de datos
        self.USE_COINGECKO = os.getenv("USE_COINGECKO", "true").lower() == "true"
        self.USE_YAHOO = os.getenv("USE_YAHOO", "true").lower() == "true"
        
        # Configuración de trading
        self.TRADING_PAIRS = [
            "BTCUSDT",
            "ETHUSDT",
            "SOLUSDT",
            "BNBUSDT",
            "ADAUSDT",
            "DOGEUSDT",
            "XRPUSDT",
            "DOTUSDT",
            "LINKUSDT",
            "MATICUSDT"
        ]
        
        self.TIMEFRAMES = [
            "1m",
            "5m",
            "15m",
            "30m",
            "1h",
            "4h",
            "1d"
        ]
        
        # Límites y gestión de riesgo
        self.MAX_POSITION_SIZE = float(os.getenv("MAX_POSITION_SIZE", "1.0"))
        self.MAX_LEVERAGE = int(os.getenv("MAX_LEVERAGE", "20"))
        self.MIN_RISK_REWARD_RATIO = float(os.getenv("MIN_RISK_REWARD_RATIO", "2.0"))
        self.MAX_DRAWDOWN = float(os.getenv("MAX_DRAWDOWN", "0.10"))
        self.STOP_LOSS_PCT = float(os.getenv("STOP_LOSS_PCT", "0.02"))
        self.TAKE_PROFIT_PCT = float(os.getenv("TAKE_PROFIT_PCT", "0.04"))
        
        # Notificaciones
        self.TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
        self.EMAIL_SMTP_SERVER = os.getenv("EMAIL_SMTP_SERVER", "smtp.gmail.com")
        self.EMAIL_SMTP_PORT = int(os.getenv("EMAIL_SMTP_PORT", "587"))
        self.EMAIL_USERNAME = os.getenv("EMAIL_USERNAME", "")
        self.EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
        
        # Configuración de backtesting
        self.INITIAL_CAPITAL = float(os.getenv("INITIAL_CAPITAL", "10000"))
        self.COMMISSION_RATE = float(os.getenv("COMMISSION_RATE", "0.001"))
        
        # Configuración de caché
        self.CACHE_DIR = Path("cache")
        self.CACHE_EXPIRY = int(os.getenv("CACHE_EXPIRY", "3600"))  # 1 hora
        
        # Crear directorio de caché si no existe
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        
    def validate(self) -> bool:
        """
        Valida la configuración.
        
        Returns:
            bool indicando si la configuración es válida
        """
        try:
            # Validar credenciales de Bybit
            if not self.BYBIT_API_KEY or not self.BYBIT_API_SECRET:
                logger.warning("Credenciales de Bybit no configuradas")
                return False
                
            # Validar límites
            if self.MAX_POSITION_SIZE <= 0:
                logger.error("MAX_POSITION_SIZE debe ser mayor que 0")
                return False
                
            if self.MAX_LEVERAGE <= 0:
                logger.error("MAX_LEVERAGE debe ser mayor que 0")
                return False
                
            if self.MIN_RISK_REWARD_RATIO <= 0:
                logger.error("MIN_RISK_REWARD_RATIO debe ser mayor que 0")
                return False
                
            if not 0 < self.MAX_DRAWDOWN < 1:
                logger.error("MAX_DRAWDOWN debe estar entre 0 y 1")
                return False
                
            if not 0 < self.STOP_LOSS_PCT < 1:
                logger.error("STOP_LOSS_PCT debe estar entre 0 y 1")
                return False
                
            if not 0 < self.TAKE_PROFIT_PCT < 1:
                logger.error("TAKE_PROFIT_PCT debe estar entre 0 y 1")
                return False
                
            # Validar configuración de backtesting
            if self.INITIAL_CAPITAL <= 0:
                logger.error("INITIAL_CAPITAL debe ser mayor que 0")
                return False
                
            if not 0 <= self.COMMISSION_RATE < 1:
                logger.error("COMMISSION_RATE debe estar entre 0 y 1")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error validando configuración: {str(e)}")
            return False
            
    def save(self):
        """Guarda la configuración en el archivo .env."""
        try:
            with open(".env", "w") as f:
                f.write(f"BYBIT_API_KEY={self.BYBIT_API_KEY}\n")
                f.write(f"BYBIT_API_SECRET={self.BYBIT_API_SECRET}\n")
                f.write(f"USE_TESTNET={'true' if self.USE_TESTNET else 'false'}\n")
                f.write(f"USE_COINGECKO={'true' if self.USE_COINGECKO else 'false'}\n")
                f.write(f"USE_YAHOO={'true' if self.USE_YAHOO else 'false'}\n")
                f.write(f"MAX_POSITION_SIZE={self.MAX_POSITION_SIZE}\n")
                f.write(f"MAX_LEVERAGE={self.MAX_LEVERAGE}\n")
                f.write(f"MIN_RISK_REWARD_RATIO={self.MIN_RISK_REWARD_RATIO}\n")
                f.write(f"MAX_DRAWDOWN={self.MAX_DRAWDOWN}\n")
                f.write(f"STOP_LOSS_PCT={self.STOP_LOSS_PCT}\n")
                f.write(f"TAKE_PROFIT_PCT={self.TAKE_PROFIT_PCT}\n")
                f.write(f"INITIAL_CAPITAL={self.INITIAL_CAPITAL}\n")
                f.write(f"COMMISSION_RATE={self.COMMISSION_RATE}\n")
                f.write(f"CACHE_EXPIRY={self.CACHE_EXPIRY}\n")
                
                # Guardar credenciales de notificaciones si están configuradas
                if self.TELEGRAM_BOT_TOKEN:
                    f.write(f"TELEGRAM_BOT_TOKEN={self.TELEGRAM_BOT_TOKEN}\n")
                if self.TELEGRAM_CHAT_ID:
                    f.write(f"TELEGRAM_CHAT_ID={self.TELEGRAM_CHAT_ID}\n")
                if self.EMAIL_USERNAME:
                    f.write(f"EMAIL_USERNAME={self.EMAIL_USERNAME}\n")
                if self.EMAIL_PASSWORD:
                    f.write(f"EMAIL_PASSWORD={self.EMAIL_PASSWORD}\n")
                    
            logger.info("Configuración guardada exitosamente")
            
        except Exception as e:
            logger.error(f"Error guardando configuración: {str(e)}")
            raise