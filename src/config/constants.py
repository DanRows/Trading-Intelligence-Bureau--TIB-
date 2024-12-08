from enum import Enum
from typing import Dict, Any

class TimeFrame(Enum):
    """Intervalos de tiempo soportados."""
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"

class TradingConstants:
    """Constantes relacionadas con trading."""
    MAX_LEVERAGE = 20
    DEFAULT_TIMEFRAME = TimeFrame.H1
    COMMISSION_RATE = 0.001
    MIN_TRADE_AMOUNT = 10.0
    MAX_TRADES_PER_DAY = 50
    
class CacheConstants:
    """Constantes para el manejo de caché."""
    DEFAULT_TTL = 300  # segundos
    MAX_ENTRIES = 1000
    REDIS_PREFIX = "tib:"
    
class MLConstants:
    """Constantes para modelos de ML."""
    SEQUENCE_LENGTH = 60
    BATCH_SIZE = 32
    EPOCHS = 100
    TRAIN_TEST_SPLIT = 0.8
    VALIDATION_SPLIT = 0.1

class Indicators(Enum):
    """Indicadores técnicos soportados."""
    RSI = "rsi"
    MACD = "macd"
    EMA = "ema"
    SMA = "sma"
    BBANDS = "bbands" 