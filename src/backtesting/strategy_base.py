import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class StrategyBase(ABC):
    """Clase base para estrategias de trading."""
    
    def __init__(self, data: pd.DataFrame, initial_capital: float = 10000, commission: float = 0.001):
        """
        Inicializa la estrategia base.
        
        Args:
            data: DataFrame con datos OHLCV
            initial_capital: Capital inicial
            commission: Comisión por trade (porcentaje)
        """
        self.data = data
        self.initial_capital = initial_capital
        self.commission = commission
        
        # Estado interno
        self.position = 0  # 1: long, -1: short, 0: neutral
        self.entry_price = 0
        self.capital = initial_capital
        self.trades = []
        self.equity_curve = []
        
    @abstractmethod
    async def generate_signals(self) -> pd.Series:
        """
        Genera señales de trading.
        
        Returns:
            Series con señales (1: compra, -1: venta, 0: mantener)
        """
        pass
        
    async def run(self) -> pd.DataFrame:
        """
        Ejecuta la estrategia sobre los datos históricos.
        
        Returns:
            DataFrame con historial de trades
        """
        try:
            # Generar señales
            signals = await self.generate_signals()
            
            # Simular trading
            for i in range(1, len(self.data)):
                current_price = self.data['close'].iloc[i]
                signal = signals.iloc[i]
                
                # Procesar señal
                if signal == 1 and self.position <= 0:  # Comprar
                    await self._enter_long(current_price, self.data.index[i])
                    
                elif signal == -1 and self.position >= 0:  # Vender
                    await self._enter_short(current_price, self.data.index[i])
                    
                # Actualizar equity
                self.equity_curve.append(self._calculate_equity(current_price))
                
            # Cerrar posición final si existe
            if self.position != 0:
                await self._close_position(current_price, self.data.index[-1])
                
            # Crear DataFrame de trades
            trades_df = pd.DataFrame(self.trades)
            if not trades_df.empty:
                trades_df.columns = [
                    'entry_time', 'exit_time', 'entry_price', 'exit_price',
                    'position', 'profit', 'commission'
                ]
                
            return trades_df
            
        except Exception as e:
            logger.error(f"Error ejecutando estrategia: {str(e)}")
            return pd.DataFrame()
            
    async def _enter_long(self, price: float, timestamp: pd.Timestamp):
        """Entra en posición larga."""
        if self.position == -1:
            await self._close_position(price, timestamp)
            
        self.position = 1
        self.entry_price = price
        commission = price * self.commission
        self.capital -= commission
        
    async def _enter_short(self, price: float, timestamp: pd.Timestamp):
        """Entra en posición corta."""
        if self.position == 1:
            await self._close_position(price, timestamp)
            
        self.position = -1
        self.entry_price = price
        commission = price * self.commission
        self.capital -= commission
        
    async def _close_position(self, price: float, timestamp: pd.Timestamp):
        """Cierra la posición actual."""
        if self.position == 0:
            return
            
        # Calcular profit/loss
        if self.position == 1:
            profit = price - self.entry_price
        else:
            profit = self.entry_price - price
            
        # Aplicar comisión
        commission = price * self.commission
        self.capital += (profit - commission)
        
        # Registrar trade
        self.trades.append([
            self.data.index[self.position_opened],
            timestamp,
            self.entry_price,
            price,
            self.position,
            profit,
            commission
        ])
        
        self.position = 0
        self.entry_price = 0
        
    def _calculate_equity(self, current_price: float) -> float:
        """Calcula el valor actual del portfolio."""
        if self.position == 0:
            return self.capital
            
        # Calcular profit/loss no realizado
        if self.position == 1:
            unrealized_pnl = current_price - self.entry_price
        else:
            unrealized_pnl = self.entry_price - current_price
            
        return self.capital + unrealized_pnl
        
    def get_equity_curve(self) -> pd.Series:
        """Retorna la curva de equity."""
        return pd.Series(self.equity_curve, index=self.data.index[1:])
        
    def get_trades(self) -> pd.DataFrame:
        """Retorna el historial de trades."""
        return pd.DataFrame(self.trades, columns=[
            'entry_time', 'exit_time', 'entry_price', 'exit_price',
            'position', 'profit', 'commission'
        ]) 