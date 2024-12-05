import asyncio
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from enum import Enum

class AlertPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class Alert:
    timestamp: datetime
    priority: AlertPriority
    message: str
    pair: str
    data: Dict[str, Any]
    acknowledged: bool = False

class AlertManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.alerts: List[Alert] = []
        self.handlers: Dict[AlertPriority, List[Callable]] = {
            priority: [] for priority in AlertPriority
        }
        
    async def create_alert(
        self,
        priority: AlertPriority,
        message: str,
        pair: str,
        data: Dict[str, Any]
    ) -> Alert:
        """Crea y procesa una nueva alerta"""
        alert = Alert(
            timestamp=datetime.utcnow(),
            priority=priority,
            message=message,
            pair=pair,
            data=data
        )
        
        self.alerts.append(alert)
        await self._process_alert(alert)
        
        return alert
        
    async def _process_alert(self, alert: Alert):
        """Procesa una alerta llamando a los handlers correspondientes"""
        try:
            handlers = self.handlers[alert.priority]
            
            for handler in handlers:
                try:
                    await handler(alert)
                except Exception as e:
                    self.logger.error(f"Error en handler de alerta: {str(e)}")
                    
        except Exception as e:
            self.logger.error(f"Error procesando alerta: {str(e)}")
            
    def add_handler(self, priority: AlertPriority, handler: Callable):
        """Agrega un nuevo handler para un nivel de prioridad"""
        if priority not in self.handlers:
            self.handlers[priority] = []
            
        self.handlers[priority].append(handler)
        
    def remove_handler(self, priority: AlertPriority, handler: Callable):
        """Elimina un handler"""
        if priority in self.handlers and handler in self.handlers[priority]:
            self.handlers[priority].remove(handler)
            
    async def check_price_alerts(
        self,
        pair: str,
        current_price: float,
        alerts_config: Dict[str, Any]
    ):
        """Verifica condiciones de precio para generar alertas"""
        if 'price_levels' in alerts_config:
            for level in alerts_config['price_levels']:
                if current_price >= level['price']:
                    await self.create_alert(
                        priority=AlertPriority.HIGH,
                        message=f"Precio de {pair} alcanzó nivel {level['price']}",
                        pair=pair,
                        data={
                            'price': current_price,
                            'level': level['price'],
                            'type': 'price_level'
                        }
                    )
                    
    async def check_volatility_alerts(
        self,
        pair: str,
        volatility: float,
        threshold: float = 0.02
    ):
        """Verifica condiciones de volatilidad para generar alertas"""
        if volatility > threshold:
            await self.create_alert(
                priority=AlertPriority.MEDIUM,
                message=f"Alta volatilidad detectada en {pair}",
                pair=pair,
                data={
                    'volatility': volatility,
                    'threshold': threshold,
                    'type': 'volatility'
                }
            )
            
    async def check_volume_alerts(
        self,
        pair: str,
        current_volume: float,
        avg_volume: float,
        multiplier: float = 2.0
    ):
        """Verifica condiciones de volumen para generar alertas"""
        if current_volume > avg_volume * multiplier:
            await self.create_alert(
                priority=AlertPriority.MEDIUM,
                message=f"Volumen inusual detectado en {pair}",
                pair=pair,
                data={
                    'current_volume': current_volume,
                    'avg_volume': avg_volume,
                    'multiplier': multiplier,
                    'type': 'volume'
                }
            )
            
    async def check_pattern_alerts(
        self,
        pair: str,
        pattern: Dict[str, Any],
        min_reliability: float = 0.7
    ):
        """Verifica patrones significativos para generar alertas"""
        if pattern['reliability'] >= min_reliability:
            await self.create_alert(
                priority=AlertPriority.LOW,
                message=f"Patrón {pattern['pattern']} detectado en {pair}",
                pair=pair,
                data={
                    'pattern': pattern['pattern'],
                    'reliability': pattern['reliability'],
                    'type': 'pattern'
                }
            )
            
    def get_active_alerts(
        self,
        priority: Optional[AlertPriority] = None,
        pair: Optional[str] = None
    ) -> List[Alert]:
        """Obtiene alertas activas con filtros opcionales"""
        filtered_alerts = self.alerts
        
        if priority:
            filtered_alerts = [
                alert for alert in filtered_alerts 
                if alert.priority == priority
            ]
            
        if pair:
            filtered_alerts = [
                alert for alert in filtered_alerts 
                if alert.pair == pair
            ]
            
        return filtered_alerts
        
    def acknowledge_alert(self, alert: Alert):
        """Marca una alerta como reconocida"""
        if alert in self.alerts:
            alert.acknowledged = True
            self.logger.info(f"Alerta reconocida: {alert.message}")
            
    def clear_old_alerts(self, hours: int = 24):
        """Limpia alertas antiguas"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        self.alerts = [
            alert for alert in self.alerts 
            if alert.timestamp > cutoff_time
        ] 