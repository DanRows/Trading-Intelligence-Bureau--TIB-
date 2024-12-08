import os
import sys
from pathlib import Path

# Agregar el directorio raíz al PYTHONPATH
ROOT_DIR = Path(__file__).parent
sys.path.append(str(ROOT_DIR))

import streamlit as st
from src.config import Settings
from src.reporting.dashboard import TradingDashboard
from src.data.exchange_factory import ExchangeFactory

def main():
    """Función principal de la aplicación."""
    try:
        # Configurar página
        st.set_page_config(
            page_title="Trading Intelligence Bureau",
            page_icon="📊",
            layout="wide"
        )
        
        # Inicializar configuración
        settings = Settings()
        
        # Crear conector
        exchange = ExchangeFactory.create_exchange(settings)
        
        # Inicializar y renderizar dashboard
        dashboard = TradingDashboard(settings, exchange)
        dashboard.render()
        
    except Exception as e:
        st.error(f"Error inicializando la aplicación: {str(e)}")
        raise

if __name__ == "__main__":
    main()