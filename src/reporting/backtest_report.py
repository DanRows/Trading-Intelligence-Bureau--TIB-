from typing import Dict, Any, List, Optional
import pandas as pd
import streamlit as st
import logging
from datetime import datetime, timedelta
from pathlib import Path
import asyncio
from ..analysis.backtesting.backtest_runner import BacktestRunner
from ..analysis.backtesting.technical_strategy import TechnicalStrategy
from ..analysis.backtesting.backtest_visualizer import BacktestVisualizer
from ..config.constants import TimeFrame, TradingConstants
from ..data.base_connector import BaseExchangeConnector
from ..config.settings import Settings

logger = logging.getLogger(__name__)

class BacktestReport:
    """Componente de backtesting para el dashboard."""
    
    def __init__(self, settings: Settings, connector: BaseExchangeConnector):
        """
        Inicializa el componente de backtesting.
        
        Args:
            settings: Configuración global
            connector: Conector para datos históricos
        """
        self.settings = settings
        self.connector = connector
        self.runner = BacktestRunner(connector)
        self.visualizer = BacktestVisualizer()
        
    def render(self):
        """Renderiza la sección de backtesting en el dashboard."""
        try:
            st.header(" Backtesting")
            
            # Configuración del backtest
            with st.expander("⚙️ Configuración", expanded=True):
                self._render_config_section()
                
            # Ejecutar backtest
            if st.button("🚀 Ejecutar Backtest"):
                asyncio.run(self._run_backtest())  # Usar asyncio.run
                
            # Mostrar resultados anteriores
            with st.expander("📜 Resultados Anteriores"):
                self._render_previous_results()
                
        except Exception as e:
            logger.error(f"Error renderizando backtest: {str(e)}")
            st.error(f"Error: {str(e)}")
            
    def _render_config_section(self):
        """Renderiza la sección de configuración del backtest."""
        # Selección de par
        st.selectbox(
            "Par de Trading",
            options=self.connector.trading_pairs,
            key="backtest_symbol",
            help="Selecciona el par para hacer backtest"
        )
        
        # Timeframe
        st.selectbox(
            "Timeframe",
            options=[tf.value for tf in TimeFrame],
            key="backtest_timeframe",
            help="Intervalo de tiempo para el análisis"
        )
        
        # Período predefinido o personalizado
        period_type = st.radio(
            "Selección de Período",
            options=["Predefinido", "Personalizado"]
        )
        
        if period_type == "Predefinido":
            period = st.selectbox(
                "Período",
                options=["1 Mes", "3 Meses", "6 Meses", "1 Año"],
                key="backtest_period"
            )
            end_date = datetime.now()
            if period == "1 Mes":
                start_date = end_date - timedelta(days=30)
            elif period == "3 Meses":
                start_date = end_date - timedelta(days=90)
            elif period == "6 Meses":
                start_date = end_date - timedelta(days=180)
            else:
                start_date = end_date - timedelta(days=365)
                
            st.session_state.backtest_start_date = start_date
            st.session_state.backtest_end_date = end_date
        else:
            st.date_input(
                "Fecha Inicial",
                key="backtest_start_date"
            )
            st.date_input(
                "Fecha Final",
                key="backtest_end_date"
            )
        
        # Parámetros de estrategia
        st.subheader("Parámetros de Estrategia")
        
        st.number_input(
            "Capital Inicial",
            min_value=100,
            value=self.settings.INITIAL_CAPITAL,
            step=100,
            key="backtest_capital",
            help="Capital inicial para el backtest"
        )
        
        st.number_input(
            "Comisión (%)",
            min_value=0.0,
            max_value=1.0,
            value=self.settings.COMMISSION_RATE * 100,
            step=0.01,
            key="backtest_commission",
            help="Comisión por operación en porcentaje"
        )
        
        st.number_input(
            "Umbral de Confianza",
            min_value=0.1,
            max_value=1.0,
            value=0.7,
            step=0.1,
            key="backtest_confidence",
            help="Nivel mínimo de confianza para tomar posiciones"
        )
        
        # Gestión de riesgo
        st.subheader("Gestión de Riesgo")
        
        use_stop_loss = st.checkbox(
            "Usar Stop Loss",
            value=True,
            key="backtest_use_stop_loss"
        )
        
        if use_stop_loss:
            st.number_input(
                "Stop Loss (%)",
                min_value=0.1,
                max_value=10.0,
                value=2.0,
                step=0.1,
                key="backtest_stop_loss"
            )
            
    async def _run_backtest(self):
        """Ejecuta el backtest con la configuración actual."""
        try:
            with st.spinner("Ejecutando backtest..."):
                # Preparar configuración
                config = {
                    'initial_capital': st.session_state.backtest_capital,
                    'commission': st.session_state.backtest_commission / 100,
                    'use_stop_loss': st.session_state.backtest_use_stop_loss,
                    'stop_loss_pct': st.session_state.get('backtest_stop_loss', 2.0) / 100,
                    'confidence_threshold': st.session_state.backtest_confidence,
                }
                
                # Crear estrategia
                strategy = TechnicalStrategy(config)
                
                # Ejecutar backtest
                results = await self.runner.run_backtest(
                    strategy=strategy,
                    symbol=st.session_state.backtest_symbol,
                    start_date=st.session_state.backtest_start_date.strftime("%Y-%m-%d"),
                    end_date=st.session_state.backtest_end_date.strftime("%Y-%m-%d"),
                    timeframe=st.session_state.backtest_timeframe
                )
                
                # Guardar resultados en sesión
                st.session_state.current_results = results
                
                # Mostrar resultados
                self._display_results(results)
                
        except Exception as e:
            logger.error(f"Error ejecutando backtest: {str(e)}", exc_info=True)
            st.error(f"Error: {str(e)}")
            
    def _display_results(self, results: Dict[str, Any]):
        """Muestra resultados del backtest."""
        try:
            # Métricas principales
            metrics = results['results']['metrics']  # Corregido: acceso a diccionario
            
            cols = st.columns(4)
            with cols[0]:
                st.metric(
                    "Retorno Total",
                    f"{metrics['total_return']:.2%}",
                    help="Retorno total del período"
                )
                
            with cols[1]:
                st.metric(
                    "Win Rate",
                    f"{metrics['win_rate']:.2%}",
                    help="Porcentaje de operaciones ganadoras"
                )
                
            with cols[2]:
                st.metric(
                    "Sharpe Ratio",
                    f"{metrics['sharpe_ratio']:.2f}",
                    help="Ratio de Sharpe (rendimiento ajustado por riesgo)"
                )
                
            with cols[3]:
                st.metric(
                    "Max Drawdown",
                    f"{metrics['max_drawdown']:.2%}",
                    help="Máxima caída desde máximos"
                )
                
            # Gráficos
            st.plotly_chart(
                self.visualizer.create_performance_chart(results),
                use_container_width=True
            )
            
            # Detalles adicionales en expander
            with st.expander("📊 Detalles Adicionales"):
                st.plotly_chart(
                    self.visualizer.create_metrics_summary(results),
                    use_container_width=True
                )
                
                # Tabla de operaciones
                if results['results']['trades']:  # Corregido: acceso a diccionario
                    st.subheader("Operaciones")
                    trades_df = pd.DataFrame(results['results']['trades'])
                    st.dataframe(trades_df)
                
        except Exception as e:
            logger.error(f"Error mostrando resultados: {str(e)}", exc_info=True)
            st.error(f"Error: {str(e)}")
            
    def _render_previous_results(self):
        """Muestra resultados de backtests anteriores."""
        try:
            results = self.runner.get_available_results()
            if not results:
                st.info("No hay resultados anteriores disponibles")
                return
                
            selected = st.selectbox(
                "Seleccionar Backtest",
                options=results,
                format_func=lambda x: f"{x.split('_')[1]} - {x.split('_')[2].replace('.json', '')}"
            )
            
            if selected:
                result_data = self.runner.load_results(selected)
                self._display_results(result_data)
                
        except Exception as e:
            logger.error(f"Error mostrando resultados anteriores: {str(e)}", exc_info=True)
            st.error(f"Error: {str(e)}") 