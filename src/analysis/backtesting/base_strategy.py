from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
import logging
from datetime import datetime
from ...config.constants import TradingConstants

logger = logging.getLogger(__name__)

class BacktestResult:
    """Clase para almacenar resultados del backtesting."""
    def __init__(self, 
                 trades: List[Dict[str, Any]],
                 portfolio_values: List[Dict[str, Any]],
                 metrics: Dict[str, Any]):
        self.trades = trades
        self.portfolio_values = portfolio_values
        self.metrics = metrics
        self.timestamp = datetime.utcnow()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el resultado a diccionario."""
        return {
            'timestamp': self.timestamp,
            'trades': self.trades,
            'portfolio_values': self.portfolio_values,
            'metrics': self.metrics
        }

class BaseStrategy(ABC):
    """Clase base para estrategias de backtesting."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa la estrategia.
        
        Args:
            config: Configuración de la estrategia incluyendo:
                   - initial_capital: Capital inicial
                   - commission: Comisión por trade
                   - use_stop_loss: Si usar stop loss
                   - stop_loss_pct: Porcentaje de stop loss
        """
        self.config = config
        self.initial_capital = config.get('initial_capital', TradingConstants.MIN_TRADE_AMOUNT)
        self.commission = config.get('commission', TradingConstants.COMMISSION_RATE)
        self.use_stop_loss = config.get('use_stop_loss', False)
        self.stop_loss_pct = config.get('stop_loss_pct', 0.02)
        
        # Estado del backtesting
        self.position = 0  # -1: short, 0: neutral, 1: long
        self.trades: List[Dict[str, Any]] = []
        self.portfolio_values: List[Dict[str, Any]] = []
        
        # Logging
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        
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
        
    async def backtest(self, data: pd.DataFrame) -> BacktestResult:
        """
        Ejecuta backtesting de la estrategia.
        
        Args:
            data: DataFrame con datos históricos
            
        Returns:
            BacktestResult con resultados del backtesting
        """
        try:
            self._validate_data(data)
            self._reset_state()
            
            signals = await self.generate_signals(data)
            capital = self.initial_capital
            position = 0
            entry_price = 0
            stop_loss = 0
            
            for i in range(len(data)-1):
                current_bar = data.iloc[i]
                next_bar = data.iloc[i+1]
                signal = signals.iloc[i]
                timestamp = data.index[i]
                
                # Verificar stop loss
                if self.use_stop_loss and position != 0:
                    if self._check_stop_loss(position, entry_price, current_bar):
                        # Cerrar posición por stop loss
                        pnl = self._calculate_pnl(entry_price, current_bar['close'], position)
                        capital += pnl
                        self._record_trade(timestamp, current_bar['close'], pnl, 'stop_loss')
                        position = 0
                
                # Procesar señal si no estamos en stop loss
                if signal != position and position == 0:
                    if signal != 0:  # Abrir nueva posición
                        entry_price = current_bar['close']
                        position = signal
                        stop_loss = self._calculate_stop_loss(position, entry_price)
                        self._record_entry(timestamp, entry_price, position)
                    
                elif signal != position and position != 0:  # Cerrar posición existente
                    pnl = self._calculate_pnl(entry_price, current_bar['close'], position)
                    capital += pnl
                    self._record_trade(timestamp, current_bar['close'], pnl, 'signal')
                    position = 0
                
                # Registrar valor del portfolio
                portfolio_value = self._calculate_portfolio_value(
                    capital, position, entry_price, next_bar['close']
                )
                self._record_portfolio_value(timestamp, capital, portfolio_value, position)
            
            # Cerrar posición final si existe
            if position != 0:
                final_price = data['close'].iloc[-1]
                pnl = self._calculate_pnl(entry_price, final_price, position)
                capital += pnl
                self._record_trade(data.index[-1], final_price, pnl, 'final')
            
            # Calcular métricas finales
            metrics = self._calculate_metrics()
            
            return BacktestResult(
                trades=self.trades,
                portfolio_values=self.portfolio_values,
                metrics=metrics
            )
            
        except Exception as e:
            self.logger.error(f"Error en backtesting: {str(e)}", exc_info=True)
            raise
            
    def _validate_data(self, data: pd.DataFrame) -> None:
        """Valida el DataFrame de entrada."""
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            raise ValueError(f"Columnas faltantes en DataFrame: {missing_columns}")
            
    def _reset_state(self) -> None:
        """Reinicia el estado del backtesting."""
        self.position = 0
        self.trades = []
        self.portfolio_values = []
        
    def _calculate_pnl(self, entry_price: float, exit_price: float, position: int) -> float:
        """Calcula el P&L de un trade."""
        size = self._calculate_position_size(self.initial_capital, entry_price)
        gross_pnl = (exit_price - entry_price) * position * size
        commission = (entry_price + exit_price) * size * self.commission
        return gross_pnl - commission
        
    def _calculate_position_size(self, capital: float, price: float) -> float:
        """Calcula el tamaño de la posición."""
        return (capital * 0.95) / price  # Usar 95% del capital
        
    def _calculate_stop_loss(self, position: int, entry_price: float) -> float:
        """Calcula el nivel de stop loss."""
        if not self.use_stop_loss:
            return 0
        return entry_price * (1 - position * self.stop_loss_pct)
        
    def _check_stop_loss(self, position: int, entry_price: float, bar: pd.Series) -> bool:
        """Verifica si se ha alcanzado el stop loss."""
        if not self.use_stop_loss:
            return False
        stop_level = self._calculate_stop_loss(position, entry_price)
        return (position == 1 and bar['low'] <= stop_level) or \
               (position == -1 and bar['high'] >= stop_level)
               
    def _calculate_portfolio_value(self, capital: float, position: int, 
                                 entry_price: float, current_price: float) -> float:
        """Calcula el valor actual del portfolio."""
        if position == 0:
            return capital
        unrealized_pnl = (current_price - entry_price) * position * \
                        self._calculate_position_size(self.initial_capital, entry_price)
        return capital + unrealized_pnl
        
    def _record_trade(self, timestamp: datetime, price: float, 
                     pnl: float, reason: str) -> None:
        """Registra un trade completado."""
        self.trades.append({
            'exit_time': timestamp,
            'exit_price': price,
            'pnl': pnl,
            'exit_reason': reason
        })
        
    def _record_entry(self, timestamp: datetime, price: float, position: int) -> None:
        """Registra una entrada en el mercado."""
        self.trades.append({
            'entry_time': timestamp,
            'entry_price': price,
            'position': position,
            'size': self._calculate_position_size(self.initial_capital, price)
        })
        
    def _record_portfolio_value(self, timestamp: datetime, capital: float, 
                              portfolio_value: float, position: int) -> None:
        """Registra el valor del portfolio."""
        self.portfolio_values.append({
            'timestamp': timestamp,
            'capital': capital,
            'portfolio_value': portfolio_value,
            'position': position
        })
        
    def _calculate_metrics(self) -> Dict[str, Any]:
        """Calcula métricas del backtesting."""
        if not self.portfolio_values:
            return {}
            
        values = pd.Series([p['portfolio_value'] for p in self.portfolio_values])
        returns = values.pct_change().dropna()
        
        winning_trades = [t for t in self.trades if t.get('pnl', 0) > 0]
        
        return {
            'initial_capital': self.initial_capital,
            'final_capital': values.iloc[-1],
            'total_return': (values.iloc[-1] / self.initial_capital) - 1,
            'total_trades': len(self.trades) // 2,
            'win_rate': len(winning_trades) / (len(self.trades) // 2) if self.trades else 0,
            'sharpe_ratio': returns.mean() / returns.std() * np.sqrt(252) if len(returns) > 0 else 0,
            'max_drawdown': (values / values.cummax() - 1).min(),
            'avg_trade_duration': self._calculate_avg_duration()
        }
        
    def _calculate_avg_duration(self) -> float:
        """Calcula la duración promedio de los trades."""
        if not self.trades:
            return 0
            
        durations = []
        for i in range(0, len(self.trades), 2):
            if i + 1 < len(self.trades):
                entry = pd.Timestamp(self.trades[i]['entry_time'])
                exit = pd.Timestamp(self.trades[i+1]['exit_time'])
                duration = (exit - entry).total_seconds() / 3600  # en horas
                durations.append(duration)
                
        return sum(durations) / len(durations) if durations else 0