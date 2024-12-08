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
        
    async def render(self):
        """Renderiza el dashboard completo."""
        try:
            st.title("Trading Intelligence Bureau")
            
            # Sidebar
            await self._render_sidebar()
            
            # Tabs principales
            tab1, tab2, tab3, tab4 = st.tabs([
                "Análisis de Mercado",
                "Backtesting",
                "Portfolio",
                "Alertas"
            ])
            
            with tab1:
                await self._render_market_analysis()
            with tab2:
                await self._render_backtesting()
            with tab3:
                await self._render_portfolio()
            with tab4:
                await self._render_alerts()
                
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
        try:
            st.header("Backtesting")
            
            # Configuración del backtest
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Configuración")
                
                # Selección de estrategia
                strategy = st.selectbox(
                    "Estrategia",
                    options=["SMA Crossover", "RSI", "MACD"],
                    index=0
                )
                
                # Parámetros según la estrategia
                if strategy == "SMA Crossover":
                    fast_period = st.slider("SMA Rápida", 5, 50, 20)
                    slow_period = st.slider("SMA Lenta", 10, 200, 50)
                    strategy_params = {
                        "fast_period": fast_period,
                        "slow_period": slow_period
                    }
                    strategy_class = SimpleMovingAverageCrossover
                    
                elif strategy == "RSI":
                    rsi_period = st.slider("Periodo RSI", 5, 30, 14)
                    oversold = st.slider("Sobreventa", 20, 40, 30)
                    overbought = st.slider("Sobrecompra", 60, 80, 70)
                    strategy_params = {
                        "period": rsi_period,
                        "oversold": oversold,
                        "overbought": overbought
                    }
                    strategy_class = RSIStrategy
                    
                else:  # MACD
                    fast_period = st.slider("MACD Rápido", 5, 20, 12)
                    slow_period = st.slider("MACD Lento", 10, 40, 26)
                    signal_period = st.slider("Señal", 5, 20, 9)
                    strategy_params = {
                        "fast_period": fast_period,
                        "slow_period": slow_period,
                        "signal_period": signal_period
                    }
                    strategy_class = MACDStrategy
                
                # Parámetros generales
                initial_capital = st.number_input(
                    "Capital Inicial",
                    min_value=100,
                    max_value=1000000,
                    value=10000,
                    step=100
                )
                
                commission = st.slider(
                    "Comisión (%)",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.1,
                    step=0.01
                )
                
            with col2:
                st.subheader("Periodo de Prueba")
                
                # Fechas de inicio y fin
                start_date = st.date_input(
                    "Fecha Inicio",
                    value=pd.Timestamp.now() - pd.Timedelta(days=30)
                )
                
                end_date = st.date_input(
                    "Fecha Fin",
                    value=pd.Timestamp.now()
                )
                
                # Botón para ejecutar
                if st.button("Ejecutar Backtest"):
                    with st.spinner("Ejecutando backtest..."):
                        # Obtener datos históricos
                        symbol = st.session_state.symbol
                        data = await self.market_data.get_historical_data(
                            symbol,
                            start_date,
                            end_date
                        )
                        
                        if data is None or data.empty:
                            st.error("No se pudieron obtener datos históricos")
                            return
                            
                        # Crear y ejecutar estrategia
                        strategy_instance = strategy_class(
                            data,
                            initial_capital=initial_capital,
                            commission=commission/100,
                            **strategy_params
                        )
                        
                        results = await self.backtester.run(strategy_instance)
                        
                        # Mostrar resultados
                        await self._render_backtest_results(results)
                        
    async def _render_backtest_results(self, results: Dict[str, Any]):
        """Renderiza los resultados del backtest."""
        if not results:
            st.error("No hay resultados para mostrar")
            return
            
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Retorno Total",
                f"{results['total_return']:.2%}"
            )
            
        with col2:
            st.metric(
                "Ratio Sharpe",
                f"{results['sharpe_ratio']:.2f}"
            )
            
        with col3:
            st.metric(
                "Máximo Drawdown",
                f"{results['max_drawdown']:.2%}"
            )
            
        with col4:
            st.metric(
                "Trades Exitosos",
                f"{results['win_rate']:.2%}"
            )
            
        # Gráfico de equity
        st.subheader("Curva de Equity")
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=results['equity_curve'].index,
            y=results['equity_curve'],
            name="Equity",
            line=dict(color='blue')
        ))
        
        fig.update_layout(
            title="Evolución del Capital",
            yaxis_title="Capital",
            xaxis_title="Fecha",
            template="plotly_dark"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabla de trades
        st.subheader("Historial de Trades")
        if 'trades' in results and not results['trades'].empty:
            st.dataframe(results['trades'], hide_index=True)
        else:
            st.info("No hay trades para mostrar")
            
    async def _render_alerts(self):
        """Renderiza la sección de alertas."""
        st.header("Alertas y Notificaciones")
        
        # Configuración de alertas
        st.subheader("Configurar Nueva Alerta")
        
        col1, col2 = st.columns(2)
        
        with col1:
            alert_type = st.selectbox(
                "Tipo de Alerta",
                options=["Precio", "Indicador Técnico", "Volumen", "Patrón"]
            )
            
            if alert_type == "Precio":
                condition = st.selectbox(
                    "Condición",
                    options=["Mayor que", "Menor que", "Cruce arriba", "Cruce abajo"]
                )
                price = st.number_input("Precio", min_value=0.0, step=0.1)
                
            elif alert_type == "Indicador Técnico":
                indicator = st.selectbox(
                    "Indicador",
                    options=["RSI", "MACD", "Bollinger Bands"]
                )
                
                if indicator == "RSI":
                    level = st.slider("Nivel", 0, 100, (30, 70))
                    
            elif alert_type == "Volumen":
                volume_condition = st.selectbox(
                    "Condición",
                    options=["Mayor al promedio", "Spike", "Tendencia"]
                )
                
            else:  # Patrón
                pattern = st.selectbox(
                    "Patrón",
                    options=["Doble Techo", "Doble Suelo", "Hombro-Cabeza-Hombro"]
                )
                
        with col2:
            st.subheader("Notificaciones")
            
            notify_email = st.checkbox("Email")
            if notify_email:
                email = st.text_input("Dirección de Email")
                
            notify_telegram = st.checkbox("Telegram")
            if notify_telegram:
                telegram_id = st.text_input("ID de Telegram")
                
            notify_webhook = st.checkbox("Webhook")
            if notify_webhook:
                webhook_url = st.text_input("URL del Webhook")
                
        if st.button("Crear Alerta"):
            st.success("Alerta creada exitosamente")
            
        # Lista de alertas activas
        st.subheader("Alertas Activas")
        
        alerts_df = pd.DataFrame({
            'Tipo': ['Precio', 'RSI', 'Volumen'],
            'Condición': ['> 50000', '> 70', '> 1M'],
            'Estado': ['Activa', 'Activa', 'Pausada']
        })
        
        st.dataframe(alerts_df, hide_index=True)
        
    async def _render_portfolio(self):
        """Renderiza la sección de portfolio."""
        try:
            st.header("Portfolio y Órdenes")
            
            # Resumen del portfolio
            portfolio = await self.portfolio_manager.get_portfolio_summary()
            
            if not portfolio:
                st.error("No se pudo obtener información del portfolio")
                return
                
            # Métricas principales
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Equity Total",
                    f"${portfolio['total_equity']:,.2f}"
                )
                
            with col2:
                st.metric(
                    "Disponible",
                    f"${portfolio['available']:,.2f}"
                )
                
            with col3:
                st.metric(
                    "Margen Usado",
                    f"${portfolio['margin_used']:,.2f}"
                )
                
            with col4:
                st.metric(
                    "P&L Total",
                    f"${portfolio['total_pnl']:,.2f}"
                )
                
            # Posiciones abiertas
            st.subheader("Posiciones Abiertas")
            if portfolio['positions']:
                positions_df = pd.DataFrame(portfolio['positions'])
                st.dataframe(positions_df, hide_index=True)
            else:
                st.info("No hay posiciones abiertas")
                
            # Nueva orden
            st.subheader("Nueva Orden")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Parámetros básicos
                symbol = st.selectbox(
                    "Símbolo",
                    options=self.settings.TRADING_PAIRS
                )
                
                side = st.radio(
                    "Lado",
                    options=["Compra", "Venta"]
                )
                
                order_type = st.selectbox(
                    "Tipo de Orden",
                    options=["Mercado", "Límite", "Stop Market", "Stop Límite"]
                )
                
                quantity = st.number_input(
                    "Cantidad",
                    min_value=0.0,
                    step=0.001
                )
                
            with col2:
                # Parámetros adicionales según tipo
                if order_type in ["Límite", "Stop Límite"]:
                    price = st.number_input(
                        "Precio Límite",
                        min_value=0.0,
                        step=0.1
                    )
                    
                if order_type in ["Stop Market", "Stop Límite"]:
                    stop_price = st.number_input(
                        "Precio Stop",
                        min_value=0.0,
                        step=0.1
                    )
                    
                # Take Profit y Stop Loss
                take_profit = st.number_input(
                    "Take Profit",
                    min_value=0.0,
                    step=0.1
                )
                
                stop_loss = st.number_input(
                    "Stop Loss",
                    min_value=0.0,
                    step=0.1
                )
                
            # Botón para enviar orden
            if st.button("Enviar Orden"):
                # Construir parámetros
                order_params = {
                    'symbol': symbol,
                    'side': 'buy' if side == "Compra" else 'sell',
                    'type': order_type.lower().replace(' ', '_'),
                    'quantity': quantity
                }
                
                if order_type in ["Límite", "Stop Límite"]:
                    order_params['price'] = price
                    
                if order_type in ["Stop Market", "Stop Límite"]:
                    order_params['stop_price'] = stop_price
                    
                if take_profit:
                    order_params['take_profit'] = take_profit
                    
                if stop_loss:
                    order_params['stop_loss'] = stop_loss
                    
                # Enviar orden
                with st.spinner("Enviando orden..."):
                    success = await self.portfolio_manager.place_order(order_params)
                    if success:
                        st.success("Orden enviada exitosamente")
                    else:
                        st.error("Error enviando la orden")
                        
            # Órdenes abiertas
            st.subheader("Órdenes Abiertas")
            open_orders = await self.portfolio_manager.get_open_orders()
            
            if open_orders:
                orders_df = pd.DataFrame(open_orders)
                
                # Agregar botón de cancelar para cada orden
                def cancel_button(order_id):
                    if st.button(f"Cancelar {order_id}"):
                        asyncio.create_task(self.portfolio_manager.cancel_order(order_id))
                        st.experimental_rerun()
                        
                orders_df['Acción'] = orders_df['id'].apply(cancel_button)
                st.dataframe(orders_df, hide_index=True)
            else:
                st.info("No hay órdenes abiertas")
                
            # Historial de órdenes
            st.subheader("Historial de Órdenes")
            history = await self.portfolio_manager.get_order_history()
            
            if history:
                history_df = pd.DataFrame(history)
                st.dataframe(history_df, hide_index=True)
            else:
                st.info("No hay historial de órdenes")