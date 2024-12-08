from typing import Dict, Any, List
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import logging
from pathlib import Path
from .backtest_runner import BacktestRunner
from ...config.constants import TradingConstants

logger = logging.getLogger(__name__)

class BacktestVisualizer:
    """Visualizador de resultados de backtesting."""
    
    def __init__(self):
        """Inicializa el visualizador."""
        self.output_dir = Path("results/visualizations")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def create_performance_chart(self, 
                               results: Dict[str, Any],
                               show_trades: bool = True) -> go.Figure:
        """
        Crea gráfico de rendimiento del backtest.
        
        Args:
            results: Resultados del backtest
            show_trades: Si mostrar marcadores de trades
            
        Returns:
            Figura de Plotly
        """
        try:
            # Crear figura con subplots
            fig = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.03,
                subplot_titles=('Portfolio Value', 'Trades'),
                row_heights=[0.7, 0.3]
            )
            
            # Datos de portfolio
            portfolio_values = pd.DataFrame(results['results']['portfolio_values'])
            portfolio_values['timestamp'] = pd.to_datetime(portfolio_values['timestamp'])
            
            # Línea de valor del portfolio
            fig.add_trace(
                go.Scatter(
                    x=portfolio_values['timestamp'],
                    y=portfolio_values['portfolio_value'],
                    name='Portfolio Value',
                    line=dict(color='blue')
                ),
                row=1, col=1
            )
            
            # Agregar trades si se solicita
            if show_trades and results['results']['trades']:
                trades_df = pd.DataFrame(results['results']['trades'])
                
                # Entradas
                entries = trades_df[trades_df['position'].notna()]
                fig.add_trace(
                    go.Scatter(
                        x=pd.to_datetime(entries['entry_time']),
                        y=entries['entry_price'],
                        mode='markers',
                        name='Entry',
                        marker=dict(
                            symbol='triangle-up',
                            size=10,
                            color='green'
                        )
                    ),
                    row=1, col=1
                )
                
                # Salidas
                exits = trades_df[trades_df['exit_price'].notna()]
                fig.add_trace(
                    go.Scatter(
                        x=pd.to_datetime(exits['exit_time']),
                        y=exits['exit_price'],
                        mode='markers',
                        name='Exit',
                        marker=dict(
                            symbol='triangle-down',
                            size=10,
                            color='red'
                        )
                    ),
                    row=1, col=1
                )
                
                # Gráfico de PnL
                fig.add_trace(
                    go.Bar(
                        x=pd.to_datetime(exits['exit_time']),
                        y=exits['pnl'],
                        name='Trade PnL',
                        marker_color=exits['pnl'].apply(
                            lambda x: 'green' if x > 0 else 'red'
                        )
                    ),
                    row=2, col=1
                )
            
            # Actualizar layout
            fig.update_layout(
                title=f"Backtest Results - {results['metadata']['symbol']}",
                xaxis_title="Date",
                yaxis_title="Value",
                height=800,
                showlegend=True,
                template='plotly_dark'
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creando gráfico: {str(e)}")
            raise
            
    def create_metrics_summary(self, results: Dict[str, Any]) -> go.Figure:
        """
        Crea gráfico resumen de métricas.
        
        Args:
            results: Resultados del backtest
            
        Returns:
            Figura de Plotly
        """
        try:
            metrics = results['results']['metrics']
            
            # Preparar datos para el gráfico
            metrics_to_show = {
                'Total Return': f"{metrics['total_return']:.2%}",
                'Win Rate': f"{metrics['win_rate']:.2%}",
                'Sharpe Ratio': f"{metrics['sharpe_ratio']:.2f}",
                'Max Drawdown': f"{metrics['max_drawdown']:.2%}",
                'Total Trades': str(metrics['total_trades']),
                'Avg Duration (h)': f"{metrics['avg_trade_duration']:.1f}"
            }
            
            # Crear figura
            fig = go.Figure(data=[
                go.Table(
                    header=dict(
                        values=['Metric', 'Value'],
                        fill_color='darkblue',
                        align='left',
                        font=dict(color='white', size=12)
                    ),
                    cells=dict(
                        values=[
                            list(metrics_to_show.keys()),
                            list(metrics_to_show.values())
                        ],
                        fill_color='darkslategray',
                        align='left',
                        font=dict(color='white', size=11)
                    )
                )
            ])
            
            fig.update_layout(
                title=f"Performance Metrics - {results['metadata']['symbol']}",
                height=400,
                template='plotly_dark'
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creando resumen de métricas: {str(e)}")
            raise
            
    def save_visualization(self, fig: go.Figure, filename: str) -> str:
        """
        Guarda la visualización en HTML.
        
        Args:
            fig: Figura de Plotly
            filename: Nombre del archivo
            
        Returns:
            Ruta del archivo guardado
        """
        try:
            filepath = self.output_dir / f"{filename}.html"
            fig.write_html(filepath)
            logger.info(f"Visualización guardada en {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error guardando visualización: {str(e)}")
            raise 