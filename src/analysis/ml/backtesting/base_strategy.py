from abc import ABC, abstractmethod
from typing import Dict, Any, List
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

class BaseStrategy(ABC):
    """Clase base para estrategias de trading."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa la estrategia.
        
        Args:
            config: Configuración de la estrategia
        """
        self.config = config
        self.position = 0  # -1: short, 0: neutral, 1: long
        self.positions: List[Dict[str, Any]] = []
        self.cash = config.get('initial_cash', 10000)
        self.commission = config.get('commission', 0.001)
        
    @abstractmethod
    async def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Genera señales de trading.
        
        Args:
            data: DataFrame con datos históricos
            
        Returns:
            Series con señales (-1: sell, 0: hold, 1: buy)
        """
        pass
        
    async def execute_trades(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Ejecuta trades basados en señales.
        
        Args:
            data: DataFrame con datos históricos
            
        Returns:
            Dict con resultados del backtesting
        """
        signals = await self.generate_signals(data)
        portfolio_value = []
        trades = []
        
        for i, (timestamp, signal) in enumerate(signals.items()):
            price = data.loc[timestamp, 'close']
            
            # Procesar señal
            if signal != self.position:
                # Cerrar posición existente
                if self.position != 0:
                    pnl = self._calculate_pnl(
                        entry_price=self.positions[-1]['entry_price'],
                        exit_price=price,
                        position=self.position
                    )
                    trades.append({
                        'entry_time': self.positions[-1]['entry_time'],
                        'exit_time': timestamp,
                        'entry_price': self.positions[-1]['entry_price'],
                        'exit_price': price,
                        'position': self.position,
                        'pnl': pnl
                    })
                    self.cash += pnl
                
                # Abrir nueva posición
                if signal != 0:
                    self.positions.append({
                        'entry_time': timestamp,
                        'entry_price': price,
                        'position': signal
                    })
                    
                self.position = signal
            
            # Calcular valor del portfolio
            portfolio_value.append({
                'timestamp': timestamp,
                'cash': self.cash,
                'position_value': self._calculate_position_value(price),
                'total': self.cash + self._calculate_position_value(price)
            })
            
        return {
            'trades': trades,
            'portfolio_value': portfolio_value,
            'final_balance': portfolio_value[-1]['total'],
            'return': (portfolio_value[-1]['total'] / self.config['initial_cash']) - 1,
            'num_trades': len(trades)
        }
        
    def _calculate_pnl(self, entry_price: float, exit_price: float, position: int) -> float:
        """Calcula el P&L de un trade."""
        gross_pnl = (exit_price - entry_price) * position
        commission = entry_price * self.commission + exit_price * self.commission
        return gross_pnl - commission
        
    def _calculate_position_value(self, current_price: float) -> float:
        """Calcula el valor actual de la posición."""
        if not self.positions or self.position == 0:
            return 0
        return (current_price - self.positions[-1]['entry_price']) * self.position 