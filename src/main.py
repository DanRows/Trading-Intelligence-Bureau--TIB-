import asyncio
import os
import logging
from dotenv import load_dotenv
import streamlit as st
from connector import BybitConnector
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
    """Obtiene las credenciales de Bybit"""
    # Intentar obtener credenciales de la sesión
    api_key = st.session_state.get('BYBIT_API_KEY', '')
    api_secret = st.session_state.get('BYBIT_API_SECRET', '')
    
    # Si no hay credenciales en la sesión, mostrar formulario
    if not api_key or not api_secret:
        st.sidebar.header(" Configuración API")
        
        api_key = st.sidebar.text_input(
            "API Key",
            type="password",
            help="Ingresa tu API Key de Bybit"
        )
        
        api_secret = st.sidebar.text_input(
            "API Secret",
            type="password",
            help="Ingresa tu API Secret de Bybit"
        )
        
        if st.sidebar.button("Guardar Credenciales"):
            if api_key and api_secret:
                st.session_state['BYBIT_API_KEY'] = api_key
                st.session_state['BYBIT_API_SECRET'] = api_secret
                st.sidebar.success("✅ Credenciales guardadas!")
            else:
                st.sidebar.error("❌ Ambos campos son requeridos")
                return None, None
    
    return api_key, api_secret

async def init_app():
    """Inicializa la aplicación"""
    try:
        api_key, api_secret = get_credentials()
        if not api_key or not api_secret:
            st.warning("⚠️ Configura tus credenciales de Bybit para comenzar")
            return
        
        connector = BybitConnector(api_key, api_secret)
        
        # Probar conexión
        with st.spinner('Verificando conexión con Bybit...'):
            if not await connector.test_connection():
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
            page_icon="📊",
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