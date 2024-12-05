from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np

@dataclass
class Alert:
    timestamp: datetime
    pair: str
    type: str  # price, volume, technical
    message: str
    severity: str  # low, medium, high
    data: Dict[str, Any]

class AlertSystem:
    def __init__(self):
        self.alerts: List[Alert] = []
        self.price_thresholds = {
            'high': 0.05,  # 5% de movimiento
            'medium': 0.03,  # 3% de movimiento
            'low': 0.01     # 1% de movimiento
        }
        
    def check_price_movement(
        self,
        pair: str,
        data: pd.DataFrame,
        lookback_periods: int = 3
    ) -> Optional[Alert]:
        """Detecta movimientos significativos de precio"""
        if len(data) < lookback_periods:
            return None
            
        # Calcular cambio porcentual
        price_change = (
            data['close'].iloc[-1] - data['close'].iloc[-lookback_periods]
        ) / data['close'].iloc[-lookback_periods]
        
        # Determinar severidad
        severity = 'low'
        for level, threshold in self.price_thresholds.items():
            if abs(price_change) >= threshold:
                severity = level
                break
                
        if severity != 'low' or abs(price_change) >= self.price_thresholds['low']:
            direction = "subida" if price_change > 0 else "bajada"
            return Alert(
                timestamp=datetime.now(),
                pair=pair,
                type='price',
                message=f"Movimiento de precio significativo: {direction} de {price_change:.2%}",
                severity=severity,
                data={
                    'price_change': price_change,
                    'current_price': float(data['close'].iloc[-1]),
                    'previous_price': float(data['close'].iloc[-lookback_periods])
                }
            )
        return None
        
    def check_volume_spike(
        self,
        pair: str,
        data: pd.DataFrame,
        std_multiplier: float = 2.0
    ) -> Optional[Alert]:
        """Detecta picos inusuales de volumen"""
        volume = data['volume']
        mean_volume = volume.rolling(window=20).mean()
        std_volume = volume.rolling(window=20).std()
        
        current_volume = volume.iloc[-1]
        current_mean = mean_volume.iloc[-1]
        current_std = std_volume.iloc[-1]
        
        if current_volume > current_mean + (std_multiplier * current_std):
            severity = 'high' if current_volume > current_mean + (3 * current_std) else 'medium'
            
            return Alert(
                timestamp=datetime.now(),
                pair=pair,
                type='volume',
                message=f"Pico de volumen detectado: {current_volume/current_mean:.1f}x promedio",
                severity=severity,
                data={
                    'current_volume': float(current_volume),
                    'mean_volume': float(current_mean),
                    'std_volume': float(current_std)
                }
            )
        return None
        
    def check_technical_signals(
        self,
        pair: str,
        data: pd.DataFrame,
        rsi_value: float
    ) -> Optional[Alert]:
        """Detecta señales técnicas importantes"""
        if rsi_value >= 70 or rsi_value <= 30:
            condition = "sobrecompra" if rsi_value >= 70 else "sobreventa"
            severity = 'medium'
            
            return Alert(
                timestamp=datetime.now(),
                pair=pair,
                type='technical',
                message=f"Condición de {condition} detectada (RSI: {rsi_value:.1f})",
                severity=severity,
                data={
                    'rsi': rsi_value,
                    'condition': condition
                }
            )
        return None
        
    def process_market_data(
        self,
        market_data: Dict[str, pd.DataFrame],
        technical_data: Dict[str, Any]
    ) -> List[Alert]:
        """Procesa datos del mercado y genera alertas"""
        new_alerts = []
        
        for pair, data in market_data.items():
            # Verificar movimientos de precio
            price_alert = self.check_price_movement(pair, data)
            if price_alert:
                new_alerts.append(price_alert)
            
            # Verificar picos de volumen
            volume_alert = self.check_volume_spike(pair, data)
            if volume_alert:
                new_alerts.append(volume_alert)
            
            # Verificar señales técnicas
            if pair in technical_data:
                rsi = technical_data[pair]['rsi']
                technical_alert = self.check_technical_signals(pair, data, rsi)
                if technical_alert:
                    new_alerts.append(technical_alert)
        
        # Actualizar lista de alertas
        self.alerts.extend(new_alerts)
        
        # Mantener solo las últimas 100 alertas
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]
            
        return new_alerts
        
    def get_active_alerts(
        self,
        min_severity: str = 'low',
        alert_types: Optional[List[str]] = None
    ) -> List[Alert]:
        """Obtiene alertas activas filtradas por severidad y tipo"""
        severity_levels = ['low', 'medium', 'high']
        min_severity_index = severity_levels.index(min_severity)
        
        filtered_alerts = [
            alert for alert in self.alerts
            if severity_levels.index(alert.severity) >= min_severity_index
        ]
        
        if alert_types:
            filtered_alerts = [
                alert for alert in filtered_alerts
                if alert.type in alert_types
            ]
            
        return filtered_alerts 