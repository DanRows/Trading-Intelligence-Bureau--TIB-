import asyncio
import os
from dotenv import load_dotenv
import streamlit as st
from connector import BybitConnector
from analyzer import MarketAnalyzer
from dashboard import Dashboard

async def main():
    # Cargar configuración
    load_dotenv()
    api_key = os.getenv('BYBIT_API_KEY')
    api_secret = os.getenv('BYBIT_API_SECRET')
    
    if not api_key or not api_secret:
        st.error("API keys no encontradas. Configura el archivo .env")
        return
    
    try:
        # Inicializar componentes
        connector = BybitConnector(api_key, api_secret)
        analyzer = MarketAnalyzer()
        
        # Obtener y analizar datos
        market_data = await connector.get_market_data()
        analyses = analyzer.analyze_market(market_data)
        
        # Renderizar dashboard
        dashboard = Dashboard(market_data, analyses)
        dashboard.render()
        
    except Exception as e:
        st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 