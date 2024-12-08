import pandas as pd
import numpy as np
from typing import Dict, Any
import logging
from src.config.settings import Settings
from src.backtesting.strategy_base import StrategyBase

logger = logging.getLogger(__name__)

class Backtester:
    """Clase para ejecutar backtesting de estrategias."""
    
    def __init__(self, settings: Settings):
        """
        Inicializa el backtester.
        
        Args:
            settings: Configuración global
        """
        self.settings = settings
        
    async def run(self, strategy: StrategyBase) -> Dict[str, Any]:
        """
        Ejecuta el backtesting de una estrategia.
        
        Args:
            strategy: Instancia de la estrategia a probar
            
        Returns:
            Dict con resultados del backtest
        """
        try:
            # Ejecutar estrategia
            trades = await strategy.run()
            
            if not trades:
                logger.warning("La estrategia no generó trades")
                return {}
                
            # Calcular métricas
            results = await self._calculate_metrics(strategy)
            results['trades'] = trades
            
            return results
            
        except Exception as e:
            logger.error(f"Error ejecutando backtest: {str(e)}")
            return {}
            
    async def _calculate_metrics(self, strategy: StrategyBase) -> Dict[str, Any]:
        """Calcula métricas de rendimiento."""
        try:
            # Obtener datos de la estrategia
            equity_curve = strategy.get_equity_curve()
            returns = equity_curve.pct_change().dropna()
            
            # Calcular métricas básicas
            total_return = (equity_curve.iloc[-1] / equity_curve.iloc[0]) - 1
            daily_returns = returns.mean() * 252
            daily_vol = returns.std() * np.sqrt(252)
            sharpe_ratio = daily_returns / daily_vol if daily_vol != 0 else 0
            
            # Calcular drawdown
            rolling_max = equity_curve.expanding().max()
            drawdown = (equity_curve - rolling_max) / rolling_max
            max_drawdown = drawdown.min()
            
            # Calcular win rate
            trades = strategy.get_trades()
            if trades.empty:
                win_rate = 0
            else:
                wins = len(trades[trades['profit'] > 0])
                total_trades = len(trades)
                win_rate = wins / total_trades if total_trades > 0 else 0
            
            return {
                'total_return': total_return,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'win_rate': win_rate,
                'equity_curve': equity_curve
            }
            
        except Exception as e:
            logger.error(f"Error calculando métricas: {str(e)}")
            return {} 