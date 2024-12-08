import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, Any
import logging
import asyncio
from src.config.settings import Settings
from src.data.base_connector import BaseConnector
from src.data.market_data_service import MarketDataService
from src.analyzer import MarketAnalyzer

logger = logging.getLogger(__name__)

class Dashboard:
    """Dashboard principal de la aplicación."""
    
    def __init__(self, settings: Settings, exchange: BaseConnector):
        """
        Inicializa el dashboard.
        
        Args:
            settings: Configuración global
            exchange: Conector del exchange
        """
        self.settings = settings
        self.exchange = exchange
        self.market_data = MarketDataService(settings)
        self.analyzer = MarketAnalyzer(settings)
        
    async def render(self):
        """Renderiza el dashboard completo."""
        try:
            st.title("Trading Intelligence Bureau")
            
            # Sidebar
            await self._render_sidebar()
            
            # Tabs principales
            tab1, tab2, tab3 = st.tabs([
                "Análisis de Mercado",
                "Backtesting",
                "Portfolio"
            ])
            
            with tab1:
                await self._render_market_analysis()
            with tab2:
                await self._render_backtesting()
            with tab3:
                await self._render_portfolio()
                
        except Exception as e:
            logger.error(f"Error renderizando dashboard: {str(e)}")
            st.error(f"Error: {str(e)}")
            
    async def _render_sidebar(self):
        """Renderiza la barra lateral."""
        with st.sidebar:
            st.header("Configuración")
            
            # Selección de exchange
            exchange = st.selectbox(
                "Exchange",
                options=["Bybit", "Binance"],
                index=0
            )
            
            # Selección de par
            trading_pairs = await self.exchange.get_trading_pairs()
            symbol = st.selectbox(
                "Par de Trading",
                options=trading_pairs
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
                
            # Modo de trading
            trading_mode = st.radio(
                "Modo de Trading",
                options=["Spot", "Futuros"],
                index=0
            )
            
            # Configuración de riesgo
            st.subheader("Gestión de Riesgo")
            leverage = st.slider(
                "Apalancamiento",
                min_value=1,
                max_value=20,
                value=1,
                disabled=trading_mode=="Spot"
            )
            
            risk_per_trade = st.slider(
                "Riesgo por Trade (%)",
                min_value=0.1,
                max_value=5.0,
                value=1.0,
                step=0.1
            )
            
            # Guardar estado
            st.session_state.update({
                'exchange': exchange,
                'symbol': symbol,
                'timeframe': timeframe,
                'auto_refresh': auto_refresh,
                'refresh_rate': refresh_rate if auto_refresh else None,
                'trading_mode': trading_mode,
                'leverage': leverage,
                'risk_per_trade': risk_per_trade
            })
            
    async def _render_market_analysis(self):
        """Renderiza la sección de análisis de mercado."""
        try:
            symbol = st.session_state.symbol
            
            # Obtener datos del mercado
            market_data = await self.exchange.get_market_data(symbol)
            if market_data is None or market_data.empty:
                st.error("No se pudieron obtener datos del mercado")
                return
                
            # Analizar datos
            analysis = await self.analyzer.analyze_market_data(market_data)
            if not analysis:
                st.error("No se pudo realizar el análisis de mercado")
                return
            
            # Mostrar métricas principales
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Precio Actual",
                    f"${float(market_data['close'].iloc[-1]):,.2f}",
                    f"{float(market_data['close'].pct_change().iloc[-1]):.2%}"
                )
                
            with col2:
                st.metric(
                    "Volumen 24h",
                    f"${float(market_data['volume'].iloc[-1]):,.0f}"
                )
                
            with col3:
                st.metric(
                    "RSI",
                    f"{float(analysis['indicators']['rsi']):,.2f}"
                )
                
            with col4:
                st.metric(
                    "Volatilidad",
                    f"{float(analysis['metrics']['volatility']):.2%}"
                )
                
            # Gráfico de precios
            st.subheader("Análisis Técnico")
            fig = await self._create_price_chart(market_data)
            st.plotly_chart(fig, use_container_width=True)
            
            # Orderbook y profundidad de mercado
            st.subheader("Profundidad de Mercado")
            orderbook = await self.exchange.get_orderbook(symbol)
            if orderbook:
                await self._render_orderbook(orderbook)
            else:
                st.error("No se pudo obtener el orderbook")
            
            # Trades recientes
            st.subheader("Trades Recientes")
            trades = await self.exchange.get_recent_trades(symbol)
            if trades is not None and not trades.empty:
                await self._render_trades_table(trades)
            else:
                st.error("No se pudieron obtener los trades recientes")
            
        except Exception as e:
            logger.error(f"Error en análisis de mercado: {str(e)}")
            st.error(f"Error: {str(e)}")
            raise
            
    async def _render_orderbook(self, orderbook: Dict[str, Any]):
        """Renderiza el orderbook."""
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Bids (Compra)")
            bids_df = pd.DataFrame(orderbook['bids'], columns=['Precio', 'Cantidad'])
            st.dataframe(bids_df, hide_index=True)
            
        with col2:
            st.markdown("### Asks (Venta)")
            asks_df = pd.DataFrame(orderbook['asks'], columns=['Precio', 'Cantidad'])
            st.dataframe(asks_df, hide_index=True)
            
    async def _render_trades_table(self, trades: pd.DataFrame):
        """Renderiza la tabla de trades recientes."""
        trades = trades[['timestamp', 'price', 'size', 'side']].copy()
        trades.columns = ['Timestamp', 'Precio', 'Cantidad', 'Lado']
        st.dataframe(trades, hide_index=True)
        
    async def _create_price_chart(self, data: pd.DataFrame) -> go.Figure:
        """Crea el gráfico de precios."""
        fig = go.Figure()
        
        # Candlestick chart
        fig.add_trace(go.Candlestick(
            x=data.index,
            open=data['open'],
            high=data['high'],
            low=data['low'],
            close=data['close'],
            name="OHLC"
        ))
        
        # Configuración del layout
        fig.update_layout(
            title=f"{st.session_state.symbol} - {st.session_state.timeframe}",
            yaxis_title="Precio",
            xaxis_title="Fecha",
            template="plotly_dark"
        )
        
        return fig
        
    async def _render_backtesting(self):
        """Renderiza la sección de backtesting."""
        st.info("Sección de backtesting en desarrollo")
        
    async def _render_portfolio(self):
        """Renderiza la sección de portfolio."""
        st.info("Sección de portfolio en desarrollo")