import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, Any
import logging
from src.config.settings import Settings
from src.data.market_data_service import MarketDataService
from src.analyzer import MarketAnalyzer

logger = logging.getLogger(__name__)

class Dashboard:
    """Dashboard principal de la aplicación."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.market_data = MarketDataService()
        self.analyzer = MarketAnalyzer(settings)
        
    def render(self):
        """Renderiza el dashboard completo."""
        try:
            st.title("Trading Intelligence Bureau")
            
            # Sidebar
            self._render_sidebar()
            
            # Tabs principales
            tab1, tab2, tab3 = st.tabs([
                "Análisis de Mercado",
                "Backtesting",
                "Portfolio"
            ])
            
            with tab1:
                self._render_market_analysis()
            with tab2:
                self._render_backtesting()
            with tab3:
                self._render_portfolio()
                
        except Exception as e:
            logger.error(f"Error renderizando dashboard: {str(e)}")
            st.error(f"Error: {str(e)}")
            
    def _render_sidebar(self):
        """Renderiza la barra lateral."""
        with st.sidebar:
            st.header("Configuración")
            
            # Selección de par
            symbol = st.selectbox(
                "Par de Trading",
                options=self.settings.TRADING_PAIRS
            )
            
            # Timeframe
            timeframe = st.selectbox(
                "Intervalo",
                options=["1m", "5m", "15m", "1h", "4h", "1d"]
            )
            
            # Actualización automática
            auto_refresh = st.checkbox("Actualización Automática", value=True)
            if auto_refresh:
                refresh_rate = st.slider(
                    "Intervalo (segundos)",
                    min_value=5,
                    max_value=300,
                    value=60
                )
                
            st.session_state.update({
                'symbol': symbol,
                'timeframe': timeframe,
                'auto_refresh': auto_refresh,
                'refresh_rate': refresh_rate if auto_refresh else None
            })
            
    def _render_market_analysis(self):
        """Renderiza la sección de análisis de mercado."""
        try:
            symbol = st.session_state.symbol
            
            # Obtener y analizar datos
            data = self.market_data.get_market_data(symbol)
            analysis = self.analyzer.analyze_market_data(data)
            
            # Mostrar métricas principales
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Precio Actual",
                    f"${data['close'].iloc[-1]:,.2f}",
                    f"{data['close'].pct_change().iloc[-1]:.2%}"
                )
                
            with col2:
                st.metric(
                    "Volumen 24h",
                    f"${data['volume'].iloc[-1]:,.0f}"
                )
                
            with col3:
                st.metric(
                    "RSI",
                    f"{analysis['indicators']['rsi']:.2f}"
                )
                
            with col4:
                st.metric(
                    "Volatilidad",
                    f"{analysis['metrics']['volatility']:.2%}"
                )
                
            # Gráfico de precios
            fig = self._create_price_chart(data)
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            logger.error(f"Error en análisis de mercado: {str(e)}")
            st.error(f"Error: {str(e)}")
            
    def _create_price_chart(self, data: pd.DataFrame) -> go.Figure:
        """Crea gráfico de precios con indicadores."""
        fig = go.Figure()
        
        # Velas
        fig.add_trace(go.Candlestick(
            x=data.index,
            open=data['open'],
            high=data['high'],
            low=data['low'],
            close=data['close'],
            name="OHLC"
        ))
        
        # Volumen
        fig.add_trace(go.Bar(
            x=data.index,
            y=data['volume'],
            name="Volumen",
            yaxis="y2"
        ))
        
        # Layout
        fig.update_layout(
            title=f"{st.session_state.symbol} - {st.session_state.timeframe}",
            yaxis_title="Precio",
            yaxis2=dict(
                title="Volumen",
                overlaying="y",
                side="right"
            ),
            xaxis_rangeslider_visible=False
        )
        
        return fig