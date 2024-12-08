"""
Módulo de backtesting y estrategias
"""

from .backtester import Backtester
from .strategy_base import StrategyBase
from .strategies import (
    SimpleMovingAverageCrossover,
    RSIStrategy,
    MACDStrategy
)

__all__ = [
    'Backtester',
    'StrategyBase',
    'SimpleMovingAverageCrossover',
    'RSIStrategy',
    'MACDStrategy'
] 