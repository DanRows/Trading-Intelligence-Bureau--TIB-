import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, Any, Optional
import logging
import asyncio
from src.config.settings import Settings
from src.data.base_connector import BaseConnector
from src.data.market_data_service import MarketDataService
from src.analyzer import MarketAnalyzer
from src.backtesting.backtester import Backtester
from src.backtesting.strategies import SimpleMovingAverageCrossover, RSIStrategy, MACDStrategy
from src.data.coingecko_connector import CoingeckoConnector
from src.data.yahoo_connector import YahooConnector

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
        self.backtester = Backtester(settings)
        self.coingecko = CoingeckoConnector(settings)
        self.yahoo = YahooConnector(settings)
        
    def _check_credentials(self) -> bool:
        """Verifica si las credenciales están configuradas."""
        if 'credentials_configured' not in st.session_state:
            st.session_state.credentials_configured = False
            
        return st.session_state.credentials_configured
        
    def _setup_credentials(self):
        """Configura las credenciales de los exchanges."""
        st.title("Configuración Inicial")
        
        with st.form("credentials_form"):
            st.subheader("Credenciales de Bybit")
            
            # API Key y Secret
            api_key = st.text_input(
                "API Key",
                type="password",
                value=self.settings.BYBIT_API_KEY or ""
            )
            
            api_secret = st.text_input(
                "API Secret",
                type="password",
                value=self.settings.BYBIT_API_SECRET or ""
            )
            
            # Modo de operación
            use_testnet = st.checkbox(
                "Usar Testnet",
                value=self.settings.USE_TESTNET
            )
            
            st.subheader("Fuentes de Datos Adicionales")
            
            # Coingecko
            use_coingecko = st.checkbox(
                "Habilitar Coingecko",
                value=True
            )
            
            # Yahoo Finance
            use_yahoo = st.checkbox(
                "Habilitar Yahoo Finance",
                value=True
            )
            
            # Botón para guardar
            submitted = st.form_submit_button("Guardar Configuración")
            
            if submitted:
                try:
                    # Actualizar configuración
                    self.settings.BYBIT_API_KEY = api_key
                    self.settings.BYBIT_API_SECRET = api_secret
                    self.settings.USE_TESTNET = use_testnet
                    self.settings.USE_COINGECKO = use_coingecko
                    self.settings.USE_YAHOO = use_yahoo
                    
                    # Guardar en .env
                    with open(".env", "w") as f:
                        f.write(f"BYBIT_API_KEY={api_key}\n")
                        f.write(f"BYBIT_API_SECRET={api_secret}\n")
                        f.write(f"USE_TESTNET={'true' if use_testnet else 'false'}\n")
                        f.write(f"USE_COINGECKO={'true' if use_coingecko else 'false'}\n")
                        f.write(f"USE_YAHOO={'true' if use_yahoo else 'false'}\n")
                    
                    st.success("Configuración guardada exitosamente")
                    st.session_state.credentials_configured = True
                    
                except Exception as e:
                    logger.error(f"Error guardando configuración: {str(e)}")
                    st.error("Error guardando la configuración")
        
    async def render(self):
        """Renderiza el dashboard completo."""
        try:
            # Verificar credenciales
            if not self._check_credentials():
                self._setup_credentials()
                return
                
            st.title("Trading Intelligence Bureau")
            
            # Sidebar
            await self._render_sidebar()
            
            # Tabs principales
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "Análisis de Mercado",
                "Datos Externos",
                "Backtesting",
                "Portfolio",
                "Alertas"
            ])
            
            with tab1:
                await self._render_market_analysis()
            with tab2:
                await self._render_external_data()
            with tab3:
                await self._render_backtesting()
            with tab4:
                await self._render_portfolio()
            with tab5:
                await self._render_alerts()
                
        except Exception as e:
            logger.error(f"Error renderizando dashboard: {str(e)}")
            st.error(f"Error: {str(e)}")
            
    async def _render_external_data(self):
        """Renderiza la sección de datos externos."""
        try:
            st.header("Datos de Fuentes Externas")
            
            # Selector de fuente
            data_source = st.selectbox(
                "Fuente de Datos",
                options=["Coingecko", "Yahoo Finance"]
            )
            
            if data_source == "Coingecko":
                await self._render_coingecko_data()
            else:
                await self._render_yahoo_data()
                
        except Exception as e:
            logger.error(f"Error mostrando datos externos: {str(e)}")
            st.error(f"Error: {str(e)}")
            
    async def _render_coingecko_data(self):
        """Renderiza datos de Coingecko."""
        try:
            # Búsqueda de criptomonedas
            search = st.text_input("Buscar Criptomoneda", value="bitcoin")
            
            if search:
                coins = await self.coingecko.search_coins(search)
                
                if not coins:
                    st.warning("No se encontraron resultados")
                    return
                    
                # Selector de moneda
                selected_coin = st.selectbox(
                    "Seleccionar Moneda",
                    options=[coin['id'] for coin in coins],
                    format_func=lambda x: next(coin['name'] for coin in coins if coin['id'] == x)
                )
                
                # Obtener datos detallados
                coin_data = await self.coingecko.get_coin_data(selected_coin)
                
                if not coin_data:
                    st.error("No se pudieron obtener los datos")
                    return
                    
                # Mostrar información
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "Precio USD",
                        f"${coin_data['market_data']['current_price']['usd']:,.2f}",
                        f"{coin_data['market_data']['price_change_percentage_24h']:.2f}%"
                    )
                    
                with col2:
                    st.metric(
                        "Cap. de Mercado",
                        f"${coin_data['market_data']['market_cap']['usd']:,.0f}"
                    )
                    
                with col3:
                    st.metric(
                        "Volumen 24h",
                        f"${coin_data['market_data']['total_volume']['usd']:,.0f}"
                    )
                    
                with col4:
                    st.metric(
                        "Ranking",
                        f"#{coin_data['market_cap_rank']}"
                    )
                    
                # Gráfico de precios
                st.subheader("Histórico de Precios")
                price_data = await self.coingecko.get_coin_history(selected_coin)
                
                if price_data:
                    fig = go.Figure()
                    
                    fig.add_trace(go.Scatter(
                        x=price_data.index,
                        y=price_data['price'],
                        name="Precio",
                        line=dict(color='blue')
                    ))
                    
                    fig.update_layout(
                        title=f"Precio de {coin_data['name']}",
                        yaxis_title="Precio USD",
                        xaxis_title="Fecha",
                        template="plotly_dark"
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                # Información adicional
                st.subheader("Información Adicional")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Descripción**: {coin_data['description']['en'][:500]}...")
                    st.markdown(f"**Página Web**: {coin_data['links']['homepage'][0]}")
                    
                with col2:
                    st.markdown(f"**GitHub**: {coin_data['links']['repos_url']['github'][0] if coin_data['links']['repos_url']['github'] else 'N/A'}")
                    st.markdown(f"**Twitter**: {coin_data['links']['twitter_screen_name']}")
                    
        except Exception as e:
            logger.error(f"Error mostrando datos de Coingecko: {str(e)}")
            st.error(f"Error: {str(e)}")
            
    async def _render_yahoo_data(self):
        """Renderiza datos de Yahoo Finance."""
        try:
            # Búsqueda de símbolos
            search = st.text_input("Buscar Símbolo", value="AAPL")
            
            if search:
                # Obtener datos del símbolo
                symbol_data = await self.yahoo.get_quote(search)
                
                if not symbol_data:
                    st.warning("No se encontraron datos para el símbolo")
                    return
                    
                # Mostrar información
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "Precio",
                        f"${symbol_data['regularMarketPrice']:,.2f}",
                        f"{symbol_data['regularMarketChangePercent']:.2f}%"
                    )
                    
                with col2:
                    st.metric(
                        "Apertura",
                        f"${symbol_data['regularMarketOpen']:,.2f}"
                    )
                    
                with col3:
                    st.metric(
                        "Máximo",
                        f"${symbol_data['regularMarketDayHigh']:,.2f}"
                    )
                    
                with col4:
                    st.metric(
                        "Mínimo",
                        f"${symbol_data['regularMarketDayLow']:,.2f}"
                    )
                    
                # Gráfico de precios
                st.subheader("Histórico de Precios")
                history = await self.yahoo.get_history(search)
                
                if not history.empty:
                    fig = go.Figure()
                    
                    fig.add_trace(go.Candlestick(
                        x=history.index,
                        open=history['Open'],
                        high=history['High'],
                        low=history['Low'],
                        close=history['Close'],
                        name="OHLC"
                    ))
                    
                    fig.update_layout(
                        title=f"{search} - Precio Histórico",
                        yaxis_title="Precio",
                        xaxis_title="Fecha",
                        template="plotly_dark"
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                # Información financiera
                st.subheader("Información Financiera")
                
                # Obtener datos financieros
                financials = await self.yahoo.get_financials(search)
                
                if financials:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("### Balance General")
                        st.dataframe(financials['balance_sheet'].head(), hide_index=True)
                        
                    with col2:
                        st.markdown("### Estado de Resultados")
                        st.dataframe(financials['income_statement'].head(), hide_index=True)
                        
                    st.markdown("### Flujo de Efectivo")
                    st.dataframe(financials['cash_flow'].head(), hide_index=True)
                    
        except Exception as e:
            logger.error(f"Error mostrando datos de Yahoo: {str(e)}")
            st.error(f"Error: {str(e)}")