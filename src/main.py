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

async def init_app():
    """Inicializa la aplicación"""
    try:
        load_dotenv()
        api_key = os.getenv('BYBIT_API_KEY')
        api_secret = os.getenv('BYBIT_API_SECRET')
        
        if not api_key or not api_secret:
            st.error("API keys no encontradas. Configura el archivo .env")
            return
        
        connector = BybitConnector(api_key, api_secret)
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