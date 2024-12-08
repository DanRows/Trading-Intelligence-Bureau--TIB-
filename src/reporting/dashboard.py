import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any, Optional
import asyncio
from datetime import datetime, timedelta
from ..data.bybit_connector import BybitConnector
from .report_generator import ReportGenerator
import logging
from ..config.settings import Settings
from ..data.base_connector import BaseExchangeConnector
from ..agents.technical_analyst import TechnicalAnalyst
from ..data.realtime_service import RealtimeService
from .backtest_report import BacktestReport

logger = logging.getLogger(__name__)

class TradingDashboard:
    def __init__(self, settings: Settings, connector: BaseExchangeConnector):
        self.settings = settings
        self.connector = connector
        self.realtime_service = None
        self.analyst = TechnicalAnalyst(
            name="main_analyst",
            config=settings.as_dict
        )
        self.backtest_report = BacktestReport(settings, connector)
        
    async def initialize(self):
        """Inicializa servicios necesarios."""
        try:
            self.realtime_service = await RealtimeService(self.settings).initialize()
            logger.info("Dashboard inicializado correctamente")
            return self
        except Exception as e:
            logger.error(f"Error inicializando dashboard: {str(e)}")
            raise
            
    def render(self):
        """Renderiza el dashboard completo."""
        try:
            self._setup_page()
            self._render_sidebar()
            
            # Tabs principales
            tab1, tab2, tab3 = st.tabs([
                "📊 Análisis en Tiempo Real",
                "🔄 Backtesting",
                "📈 Portfolio"
            ])
            
            with tab1:
                self._render_realtime_analysis()
                
            with tab2:
                self.backtest_report.render()
                
            with tab3:
                self._render_portfolio()
                
        except Exception as e:
            logger.error(f"Error renderizando dashboard: {str(e)}")
            st.error(f"Error: {str(e)}")
            
    def _setup_page(self):
        """Configura la página de Streamlit."""
        st.set_page_config(
            page_title="Trading Intelligence Bureau",
            page_icon="📊",
            layout="wide"
        )
        
        # Título principal
        st.title("Trading Intelligence Bureau")
        st.markdown("---")
        
    def _render_sidebar(self):
        """Renderiza la barra lateral."""
        with st.sidebar:
            st.header("⚙️ Configuración")
            
            # Selección de exchange
            exchange = st.selectbox(
                "Exchange",
                options=["Bybit", "Binance", "Yahoo"],
                help="Selecciona el exchange para operar"
            )
            
            # Selección de par
            symbol = st.selectbox(
                "Par de Trading",
                options=self.connector.trading_pairs,
                help="Selecciona el par para analizar"
            )
            
            # Timeframe
            timeframe = st.selectbox(
                "Timeframe",
                options=["1m", "5m", "15m", "1h", "4h", "1d"],
                help="Intervalo de tiempo para el análisis"
            )
            
            # Actualización automática
            auto_refresh = st.checkbox(
                "Actualización Automática",
                value=True,
                help="Actualizar datos automáticamente"
            )
            
            if auto_refresh:
                refresh_interval = st.slider(
                    "Intervalo (segundos)",
                    min_value=5,
                    max_value=300,
                    value=60
                )
                
            # Guardar en session state
            st.session_state.update({
                'exchange': exchange,
                'symbol': symbol,
                'timeframe': timeframe,
                'auto_refresh': auto_refresh,
                'refresh_interval': refresh_interval if auto_refresh else None
            })
            
            # Información del sistema
            st.markdown("---")
            st.markdown("### 📊 Estado del Sistema")
            
            if self.realtime_service:
                st.success("✅ Servicio en tiempo real activo")
            else:
                st.error("❌ Servicio en tiempo real inactivo")
                
    async def _render_realtime_analysis(self):
        """Renderiza el análisis en tiempo real."""
        try:
            symbol = st.session_state.symbol
            
            # Obtener datos en tiempo real
            data = await self.realtime_service.get_full_data(symbol)
            
            # Mostrar precio actual
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Precio Actual",
                    f"${data['price']:,.2f}",
                    f"{data['change_24h']:.2%}"
                )
                
            with col2:
                st.metric(
                    "Volumen 24h",
                    f"${data['volume_24h']:,.0f}"
                )
                
            with col3:
                st.metric(
                    "Máximo 24h",
                    f"${data['high_24h']:,.2f}"
                )
                
            with col4:
                st.metric(
                    "Mínimo 24h",
                    f"${data['low_24h']:,.2f}"
                )
                
            # Análisis técnico
            market_data = await self.connector.get_kline_data(
                symbol,
                interval=st.session_state.timeframe
            )
            
            analysis = await self.analyst.analyze(market_data)
            
            # Mostrar análisis
            st.markdown("### 📈 Análisis Técnico")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Gráfico de precios (implementar con plotly)
                pass
                
            with col2:
                # Señales y recomendaciones
                st.markdown(f"**Tendencia:** {analysis['trend']}")
                st.markdown(f"**RSI:** {analysis['indicators']['rsi']:.2f}")
                
                signal = analysis['signals']
                if signal['action'] != 'hold':
                    st.info(
                        f"Señal: {signal['action'].upper()} "
                        f"(Confianza: {signal['confidence']:.2%})"
                    )
                    
                    with st.expander("Ver Razones"):
                        for reason in signal['reasons']:
                            st.write(f"• {reason}")
                            
        except Exception as e:
            logger.error(f"Error en análisis en tiempo real: {str(e)}")
            st.error(f"Error: {str(e)}")
            
    def _render_portfolio(self):
        """Renderiza la sección de portfolio."""
        st.info("Sección de Portfolio en desarrollo")
        
    async def cleanup(self):
        """Limpia recursos y cierra conexiones."""
        try:
            if self.realtime_service:
                await self.realtime_service.close()
            logger.info("Recursos liberados correctamente")
        except Exception as e:
            logger.error(f"Error liberando recursos: {str(e)}") 