import os
import sys
import asyncio
import streamlit as st
from pathlib import Path

# Agregar el directorio src al PYTHONPATH
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from src.config import Settings
from src.data.exchange_factory import ExchangeFactory
from src.reporting.dashboard import TradingDashboard

async def main():
    """Función principal de la aplicación."""
    try:
        # Inicializar configuración
        settings = Settings()
        
        # Crear conector
        exchange = ExchangeFactory.create_exchange(
            exchange_name=st.session_state.get('exchange', 'Bybit'),
            settings=settings
        )
        
        # Inicializar y renderizar dashboard
        dashboard = await TradingDashboard(settings, exchange).initialize()
        dashboard.render()
        
    except Exception as e:
        st.error(f"Error inicializando la aplicación: {str(e)}")
        raise

if __name__ == "__main__":
    # Configurar página
    st.set_page_config(
        page_title="Trading Intelligence Bureau",
        page_icon="📊",
        layout="wide"
    )
    
    # Ejecutar aplicación
    asyncio.run(main()) 