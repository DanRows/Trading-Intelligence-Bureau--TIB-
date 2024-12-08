import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
import logging
from src.config.settings import Settings
from src.data.base_connector import BaseConnector

logger = logging.getLogger(__name__)

class PortfolioManager:
    """Gestor de portfolio y órdenes."""
    
    def __init__(self, settings: Settings, exchange: BaseConnector):
        """
        Inicializa el gestor de portfolio.
        
        Args:
            settings: Configuración global
            exchange: Conector del exchange
        """
        self.settings = settings
        self.exchange = exchange
        self.positions = {}  # symbol -> position_info
        self.orders = []  # Lista de órdenes
        
    async def get_portfolio_summary(self) -> Dict[str, Any]:
        """Obtiene resumen del portfolio."""
        try:
            # Obtener balance
            balance = await self.exchange.get_balance()
            
            # Obtener posiciones abiertas
            positions = await self.exchange.get_positions()
            
            # Calcular métricas
            total_equity = float(balance['total'])
            available = float(balance['free'])
            margin_used = float(balance['used'])
            
            # Calcular P&L
            total_pnl = 0
            position_info = []
            
            for pos in positions:
                symbol = pos['symbol']
                size = float(pos['size'])
                entry_price = float(pos['entry_price'])
                current_price = float(pos['mark_price'])
                unrealized_pnl = (current_price - entry_price) * size
                
                total_pnl += unrealized_pnl
                
                position_info.append({
                    'symbol': symbol,
                    'size': size,
                    'entry_price': entry_price,
                    'current_price': current_price,
                    'unrealized_pnl': unrealized_pnl,
                    'pnl_percent': (unrealized_pnl / (entry_price * size)) * 100
                })
            
            return {
                'total_equity': total_equity,
                'available': available,
                'margin_used': margin_used,
                'total_pnl': total_pnl,
                'positions': position_info
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo resumen del portfolio: {str(e)}")
            return {}
            
    async def place_order(self, order_params: Dict[str, Any]) -> bool:
        """
        Coloca una orden en el exchange.
        
        Args:
            order_params: Parámetros de la orden
            
        Returns:
            bool indicando si la orden se colocó exitosamente
        """
        try:
            # Validar parámetros
            required_params = ['symbol', 'side', 'type', 'quantity']
            if not all(param in order_params for param in required_params):
                logger.error("Faltan parámetros requeridos para la orden")
                return False
                
            # Aplicar reglas de gestión de riesgo
            if not self._validate_risk_rules(order_params):
                logger.warning("La orden no cumple con las reglas de riesgo")
                return False
                
            # Colocar orden
            order = await self.exchange.place_order(**order_params)
            
            if order:
                self.orders.append(order)
                logger.info(f"Orden colocada exitosamente: {order}")
                return True
            else:
                logger.error("Error colocando la orden")
                return False
                
        except Exception as e:
            logger.error(f"Error colocando orden: {str(e)}")
            return False
            
    async def cancel_order(self, order_id: str) -> bool:
        """Cancela una orden existente."""
        try:
            result = await self.exchange.cancel_order(order_id)
            if result:
                self.orders = [order for order in self.orders if order['id'] != order_id]
                logger.info(f"Orden {order_id} cancelada exitosamente")
                return True
            else:
                logger.error(f"Error cancelando orden {order_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error cancelando orden: {str(e)}")
            return False
            
    async def get_open_orders(self) -> List[Dict[str, Any]]:
        """Obtiene lista de órdenes abiertas."""
        try:
            return await self.exchange.get_open_orders()
        except Exception as e:
            logger.error(f"Error obteniendo órdenes abiertas: {str(e)}")
            return []
            
    async def get_order_history(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtiene historial de órdenes."""
        try:
            return await self.exchange.get_order_history(symbol)
        except Exception as e:
            logger.error(f"Error obteniendo historial de órdenes: {str(e)}")
            return []
            
    def _validate_risk_rules(self, order_params: Dict[str, Any]) -> bool:
        """
        Valida reglas de gestión de riesgo para una orden.
        
        Args:
            order_params: Parámetros de la orden
            
        Returns:
            bool indicando si la orden cumple con las reglas
        """
        try:
            symbol = order_params['symbol']
            quantity = float(order_params['quantity'])
            
            # Regla 1: Límite de posición por símbolo
            current_position = self.positions.get(symbol, 0)
            if current_position + quantity > self.settings.MAX_POSITION_SIZE:
                logger.warning(f"Orden excede el tamaño máximo de posición para {symbol}")
                return False
                
            # Regla 2: Límite de pérdida por trade
            if 'stop_loss' not in order_params:
                logger.warning("Orden no incluye stop loss")
                return False
                
            # Regla 3: Ratio riesgo/beneficio mínimo
            if 'take_profit' in order_params:
                entry_price = float(order_params.get('price', 0))
                stop_loss = float(order_params['stop_loss'])
                take_profit = float(order_params['take_profit'])
                
                risk = abs(entry_price - stop_loss)
                reward = abs(take_profit - entry_price)
                
                if reward / risk < self.settings.MIN_RISK_REWARD_RATIO:
                    logger.warning("Orden no cumple con el ratio mínimo de riesgo/beneficio")
                    return False
                    
            return True
            
        except Exception as e:
            logger.error(f"Error validando reglas de riesgo: {str(e)}")
            return False 