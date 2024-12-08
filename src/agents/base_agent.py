from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import pandas as pd
from datetime import datetime
import logging
import json
import asyncio
from pathlib import Path

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Clase base para todos los agentes de análisis."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.analysis_history: List[Dict[str, Any]] = []
        self.logger = logging.getLogger(f"agent.{name}")
        self.max_history = config.get('max_history', 1000)
        self.metrics: Dict[str, List[float]] = {
            'execution_time': [],
            'accuracy': []
        }

    async def analyze(self, 
                     market_data: pd.DataFrame, 
                     additional_data: Optional[Dict[str, pd.DataFrame]] = None) -> Dict[str, Any]:
        """
        Realiza análisis técnico completo.
        
        Args:
            market_data: DataFrame principal con datos de mercado
            additional_data: Datos adicionales opcionales (otros timeframes, etc.)
        """
        try:
            start_time = datetime.utcnow()
            
            # Combinar datos si es necesario
            data = await self._prepare_data(market_data, additional_data)
            
            # Realizar análisis
            analysis = {
                'timestamp': pd.Timestamp.now(),
                'trend': await self._analyze_trend(data),
                'indicators': await self._calculate_indicators(data),
                'signals': await self._generate_signals(data),
                'metadata': {
                    'agent': self.name,
                    'data_points': len(data),
                    'timeframe': data.index.freq if hasattr(data.index, 'freq') else None
                }
            }
            
            # Calcular métricas
            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds()
            self.metrics['execution_time'].append(execution_time)
            analysis['execution_time'] = execution_time
            
            # Almacenar análisis
            await self._store_analysis(analysis)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error en análisis: {str(e)}", exc_info=True)
            raise

    async def _prepare_data(self, 
                          market_data: pd.DataFrame,
                          additional_data: Optional[Dict[str, pd.DataFrame]] = None) -> pd.DataFrame:
        """Prepara y combina los datos para el análisis."""
        try:
            data = market_data.copy()
            
            if additional_data:
                for name, df in additional_data.items():
                    # Asegurar que los índices son compatibles
                    df = df.reindex(data.index, method='ffill')
                    # Agregar sufijo para evitar conflictos de nombres
                    data = data.join(df.add_suffix(f'_{name}'))
                    
            return data
            
        except Exception as e:
            self.logger.error(f"Error preparando datos: {str(e)}")
            raise

    async def _store_analysis(self, analysis: Dict[str, Any]) -> None:
        """Almacena el análisis en el historial."""
        try:
            self.analysis_history.append({
                'timestamp': datetime.utcnow(),
                'analysis': analysis
            })
            
            # Mantener límite de historial
            if len(self.analysis_history) > self.max_history:
                self.analysis_history = self.analysis_history[-self.max_history:]
                
        except Exception as e:
            self.logger.error(f"Error almacenando análisis: {str(e)}")
            raise

    async def export_analysis(self, filepath: str, format: str = "json") -> None:
        """
        Exporta el historial de análisis.
        
        Args:
            filepath: Ruta donde guardar el archivo
            format: Formato de exportación ('json' o 'csv')
        """
        try:
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            if format.lower() == "json":
                with open(path, 'w') as f:
                    json.dump({
                        'agent': self.name,
                        'config': self.config,
                        'metrics': self.metrics,
                        'history': self.analysis_history
                    }, f, default=str, indent=4)
                    
            elif format.lower() == "csv":
                # Aplanar el historial para CSV
                rows = []
                for entry in self.analysis_history:
                    row = {
                        'timestamp': entry['timestamp'],
                        'agent': self.name
                    }
                    row.update(self._flatten_dict(entry['analysis']))
                    rows.append(row)
                    
                pd.DataFrame(rows).to_csv(path, index=False)
                
            else:
                raise ValueError(f"Formato no soportado: {format}")
                
            self.logger.info(f"Análisis exportado a {filepath}")
            
        except Exception as e:
            self.logger.error(f"Error exportando análisis: {str(e)}")
            raise

    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '') -> Dict[str, Any]:
        """Aplana un diccionario anidado."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}_{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Retorna un resumen de las métricas del agente."""
        return {
            'name': self.name,
            'analyses_count': len(self.analysis_history),
            'avg_execution_time': sum(self.metrics['execution_time']) / len(self.metrics['execution_time'])
            if self.metrics['execution_time'] else 0,
            'last_analysis': self.analysis_history[-1]['timestamp'] if self.analysis_history else None
        }

    @abstractmethod
    async def _analyze_trend(self, df: pd.DataFrame) -> str:
        """Analiza la tendencia actual del mercado."""
        pass
        
    @abstractmethod
    async def _calculate_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calcula indicadores técnicos."""
        pass
        
    @abstractmethod
    async def _generate_signals(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Genera señales de trading."""
        pass