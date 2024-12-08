"""Módulo de backtesting."""
from .base_strategy import BaseStrategy
from .technical_strategy import TechnicalStrategy
from .backtest_runner import BacktestRunner
from .backtest_visualizer import BacktestVisualizer

__all__ = [
    'BaseStrategy',
    'TechnicalStrategy',
    'BacktestRunner',
    'BacktestVisualizer'
] 