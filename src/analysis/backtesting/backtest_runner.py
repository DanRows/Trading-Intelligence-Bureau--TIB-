from typing import Dict, Any, List, Optional
import pandas as pd
import logging
import asyncio
from datetime import datetime
from pathlib import Path
import json
from .base_strategy import BaseStrategy, BacktestResult
from ...config.constants import TradingConstants
from ...data.base_connector import BaseExchangeConnector

logger = logging.getLogger(__name__)

class BacktestRunner:
    """Ejecutor de backtesting para estrategias."""
    
    def __init__(self, connector: BaseExchangeConnector):
        """
        Inicializa el ejecutor de backtesting.
        
        Args:
            connector: Conector para obtener datos históricos
        """
        self.connector = connector
        self.results_dir = Path("results/backtests")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
    async def run_backtest(self,
                          strategy: BaseStrategy,
                          symbol: str,
                          start_date: str,
                          end_date: str,
                          timeframe: str = "1h") -> BacktestResult:
        """
        Ejecuta backtesting de una estrategia.
        
        Args:
            strategy: Estrategia a probar
            symbol: Par de trading
            start_date: Fecha inicial (YYYY-MM-DD)
            end_date: Fecha final (YYYY-MM-DD)
            timeframe: Intervalo de tiempo
            
        Returns:
            BacktestResult con resultados del backtesting
        """
        try:
            # Obtener datos históricos
            data = await self._get_historical_data(symbol, start_date, end_date, timeframe)
            
            # Ejecutar backtesting
            logger.info(f"Iniciando backtesting para {symbol} desde {start_date} hasta {end_date}")
            result = await strategy.backtest(data)
            
            # Guardar resultados
            self._save_results(result, strategy, symbol, start_date, end_date)
            
            return result
            
        except Exception as e:
            logger.error(f"Error ejecutando backtesting: {str(e)}", exc_info=True)
            raise
            
    async def _get_historical_data(self,
                                 symbol: str,
                                 start_date: str,
                                 end_date: str,
                                 timeframe: str) -> pd.DataFrame:
        """Obtiene datos históricos del conector."""
        try:
            data = await self.connector.get_kline_data(
                symbol=symbol,
                interval=timeframe,
                start_time=pd.Timestamp(start_date),
                end_time=pd.Timestamp(end_date)
            )
            
            if data.empty:
                raise ValueError(f"No hay datos disponibles para {symbol}")
                
            return data
            
        except Exception as e:
            logger.error(f"Error obteniendo datos históricos: {str(e)}")
            raise
            
    def _save_results(self,
                     result: BacktestResult,
                     strategy: BaseStrategy,
                     symbol: str,
                     start_date: str,
                     end_date: str) -> None:
        """Guarda resultados del backtesting."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"backtest_{symbol}_{timestamp}.json"
            filepath = self.results_dir / filename
            
            # Preparar datos para guardar
            results_dict = {
                'metadata': {
                    'symbol': symbol,
                    'strategy': strategy.__class__.__name__,
                    'start_date': start_date,
                    'end_date': end_date,
                    'timestamp': timestamp
                },
                'results': result.to_dict()
            }
            
            # Guardar a archivo
            with open(filepath, 'w') as f:
                json.dump(results_dict, f, indent=4, default=str)
                
            logger.info(f"Resultados guardados en {filepath}")
            
        except Exception as e:
            logger.error(f"Error guardando resultados: {str(e)}")
            
    def load_results(self, filename: str) -> Dict[str, Any]:
        """Carga resultados de un backtest anterior."""
        try:
            filepath = self.results_dir / filename
            if not filepath.exists():
                raise FileNotFoundError(f"Archivo no encontrado: {filename}")
                
            with open(filepath, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Error cargando resultados: {str(e)}")
            raise
            
    def get_available_results(self) -> List[str]:
        """Obtiene lista de backtests disponibles."""
        return [f.name for f in self.results_dir.glob("backtest_*.json")] 