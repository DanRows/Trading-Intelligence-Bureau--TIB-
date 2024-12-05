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
        ["Bybit", "Binance"],
        help="Selecciona el exchange que deseas usar"
    )
    
    # Intentar obtener credenciales de la sesión
    api_key = st.session_state.get(f'{exchange.upper()}_API_KEY', '')
    api_secret = st.session_state.get(f'{exchange.upper()}_API_SECRET', '')
    
    # Si no hay credenciales en la sesión, mostrar formulario
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
    try:
        exchange, api_key, api_secret = get_credentials()
        if not all([exchange, api_key, api_secret]):
            st.warning("⚠️ Configura tus credenciales para comenzar")
            return
        
        connector = ExchangeFactory.create_connector(exchange, api_key, api_secret)
        if not connector:
            st.error(f"❌ Exchange {exchange} no soportado")
            return
            
        # Debug
        st.write("Métodos disponibles:", dir(connector))
        
        # Probar conexión
        with st.spinner('Verificando conexión con Bybit...'):
            if not connector.test_connection():
                st.error("❌ No se pudo conectar con Bybit. Verifica tus credenciales.")
                # Limpiar credenciales inválidas
                if 'BYBIT_API_KEY' in st.session_state:
                    del st.session_state['BYBIT_API_KEY']
                if 'BYBIT_API_SECRET' in st.session_state:
                    del st.session_state['BYBIT_API_SECRET']
                return
            
            st.sidebar.success("✅ Conectado a Bybit!")
        
        analyzer = MarketAnalyzer()
        
        with st.spinner('Obteniendo datos del mercado...'):
            market_data = await connector.get_market_data()
            if not market_data:
                st.error("No se pudieron obtener datos del mercado")
                return
                
            analyses = analyzer.analyze_market(market_data)
        
        dashboard = Dashboard(market_data, analyses)
        dashboard.render()
        
    except Exception as e:
        error_msg = f"Error en la aplicación: {str(e)}"
        logger.error(error_msg)
        st.error(error_msg)

def main():
    """Punto de entrada principal"""
    try:
        st.set_page_config(
            page_title="Trading Intelligence Bureau",
            page_icon="",
            layout="wide"
        )
        
        # Ejecutar la aplicación asíncrona
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(init_app())
        
    except Exception as e:
        logger.error(f"Error fatal: {str(e)}")
        st.error("Error fatal en la aplicación. Por favor, revisa los logs.")

if __name__ == "__main__":
    main() 