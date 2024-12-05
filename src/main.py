import asyncio
import os
import logging
from dotenv import load_dotenv
import streamlit as st
from data.exchange_factory import ExchangeFactory
from analyzer import MarketAnalyzer
from dashboard import Dashboard

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_intelligence.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def get_credentials():
    """Obtiene las credenciales del exchange"""
    # Seleccionar exchange
    exchange = st.sidebar.selectbox(
        "Exchange",
        ["Yahoo", "Bybit", "Binance"],
        help="Selecciona el exchange que deseas usar"
    )
    
    # Si es Yahoo, no necesitamos credenciales
    if exchange.lower() == 'yahoo':
        return exchange.lower(), None, None
    
    # Para otros exchanges, necesitamos credenciales
    api_key = st.session_state.get(f'{exchange.upper()}_API_KEY', '')
    api_secret = st.session_state.get(f'{exchange.upper()}_API_SECRET', '')
    
    if not api_key or not api_secret:
        st.sidebar.header(" Configuración API")
        
        api_key = st.sidebar.text_input(
            "API Key",
            type="password",
            help=f"Ingresa tu API Key de {exchange}"
        )
        
        api_secret = st.sidebar.text_input(
            "API Secret",
            type="password",
            help=f"Ingresa tu API Secret de {exchange}"
        )
        
        if st.sidebar.button("Guardar Credenciales"):
            if api_key and api_secret:
                st.session_state[f'{exchange.upper()}_API_KEY'] = api_key
                st.session_state[f'{exchange.upper()}_API_SECRET'] = api_secret
                st.sidebar.success("✅ Credenciales guardadas!")
            else:
                st.sidebar.error("❌ Ambos campos son requeridos")
                return None, None, None
    
    return exchange.lower(), api_key, api_secret

async def init_app():
    """Inicializa la aplicación"""
    dashboard = None
    try:
        exchange, api_key, api_secret = get_credentials()
        if not exchange:
            st.warning("⚠️ Selecciona un exchange para comenzar")
            return
            
        if exchange != 'yahoo' and not all([api_key, api_secret]):
            st.warning("⚠️ Configura tus credenciales para comenzar")
            return
        
        connector = ExchangeFactory.create_connector(exchange, api_key, api_secret)
        if not connector:
            st.error(f"❌ Exchange {exchange} no soportado")
            return
        
        with st.spinner(f'Verificando conexión con {exchange.title()}...'):
            if not connector.test_connection():
                st.error(f"❌ No se pudo conectar con {exchange.title()}")
                if exchange != 'yahoo':
                    for key in [f'{exchange.upper()}_API_KEY', f'{exchange.upper()}_API_SECRET']:
                        if key in st.session_state:
                            del st.session_state[key]
                return
            st.sidebar.success(f"✅ Conectado a {exchange.title()}")
        
        analyzer = MarketAnalyzer()
        
        with st.spinner('Obteniendo datos del mercado...'):
            market_data = await connector.get_market_data()
            if not market_data:
                st.error("No se pudieron obtener datos del mercado")
                return
            analyses = analyzer.analyze_market(market_data)
        
        # Inicializar y renderizar dashboard
        dashboard = await Dashboard(market_data, analyses).initialize()
        dashboard.render()
        
    except Exception as e:
        error_msg = f"Error en la aplicación: {str(e)}"
        logger.error(error_msg)
        st.error(error_msg)
    finally:
        if dashboard:
            try:
                await dashboard.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up dashboard: {str(e)}")

def main():
    """Punto de entrada principal"""
    try:
        st.set_page_config(
            page_title="Trading Intelligence Bureau",
            page_icon="📊",
            layout="wide"
        )
        
        # Auto-refresh cada 60 segundos
        st.markdown(
            """
            <meta http-equiv="refresh" content="60">
            """,
            unsafe_allow_html=True
        )
        
        asyncio.run(init_app())
        
    except Exception as e:
        logger.error(f"Error fatal: {str(e)}")
        st.error("Error fatal en la aplicación. Por favor, revisa los logs.")

if __name__ == "__main__":
    main() 