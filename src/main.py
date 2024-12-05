import asyncio
import logging
from typing import Dict, Any
import json
from datetime import datetime
import os
from dotenv import load_dotenv

from data.bybit_connector import BybitConnector
from reporting.report_generator import ReportGenerator
from reporting.dashboard import TradingDashboard

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crypto_analysis.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class CryptoAnalysisSystem:
    def __init__(self):
        # Cargar variables de entorno
        load_dotenv()
        
        # Inicializar componentes
        self.api_key = os.getenv('BYBIT_API_KEY')
        self.api_secret = os.getenv('BYBIT_API_SECRET')
        
        if not self.api_key or not self.api_secret:
            raise ValueError("API keys no encontradas en variables de entorno")
            
        self.connector = BybitConnector(self.api_key, self.api_secret)
        self.report_generator = ReportGenerator(self.connector)
        self.dashboard = TradingDashboard(self.api_key, self.api_secret)
        
        # Control de estado
        self.is_running = False
        self.analysis_interval = 300  # 5 minutos por defecto
        
    async def start(self):
        """Inicia el sistema de análisis"""
        logger.info("Iniciando sistema de análisis de criptomonedas...")
        self.is_running = True
        
        try:
            while self.is_running:
                await self._run_analysis_cycle()
                await asyncio.sleep(self.analysis_interval)
                
        except Exception as e:
            logger.error(f"Error en el ciclo principal: {str(e)}")
            self.stop()
            raise
            
    def stop(self):
        """Detiene el sistema"""
        logger.info("Deteniendo sistema...")
        self.is_running = False
        
    async def _run_analysis_cycle(self):
        """Ejecuta un ciclo completo de análisis"""
        try:
            # Generar reporte
            report = await self.report_generator.generate_market_report()
            
            # Guardar reporte
            await self._save_report(report)
            
            # Actualizar dashboard (si está activo)
            if hasattr(self, 'dashboard_task'):
                self.dashboard_task.cancel()
                
            logger.info("Ciclo de análisis completado exitosamente")
            
        except Exception as e:
            logger.error(f"Error en ciclo de análisis: {str(e)}")
            
    async def _save_report(self, report: Dict[str, Any]):
        """Guarda el reporte en archivo"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reports/report_{timestamp}.json"
        
        os.makedirs("reports", exist_ok=True)
        
        try:
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Reporte guardado: {filename}")
            
        except Exception as e:
            logger.error(f"Error guardando reporte: {str(e)}")
            
    def set_analysis_interval(self, seconds: int):
        """Configura el intervalo entre análisis"""
        if seconds < 60:
            raise ValueError("El intervalo mínimo es de 60 segundos")
            
        self.analysis_interval = seconds
        logger.info(f"Intervalo de análisis actualizado a {seconds} segundos")
        
    async def run_dashboard(self):
        """Ejecuta el dashboard en un proceso separado"""
        try:
            self.dashboard_task = asyncio.create_task(
                self.dashboard.run()
            )
            await self.dashboard_task
            
        except Exception as e:
            logger.error(f"Error en dashboard: {str(e)}")
            
    async def add_trading_pair(self, symbol: str):
        """Agrega un nuevo par de trading al análisis"""
        try:
            self.connector.add_trading_pair(symbol)
            logger.info(f"Par de trading agregado: {symbol}")
            
        except Exception as e:
            logger.error(f"Error agregando par de trading: {str(e)}")
            raise
            
    async def remove_trading_pair(self, symbol: str):
        """Elimina un par de trading del análisis"""
        try:
            self.connector.remove_trading_pair(symbol)
            logger.info(f"Par de trading eliminado: {symbol}")
            
        except Exception as e:
            logger.error(f"Error eliminando par de trading: {str(e)}")
            raise

async def main():
    """Función principal"""
    system = CryptoAnalysisSystem()
    
    try:
        # Iniciar dashboard en background
        dashboard_task = asyncio.create_task(system.run_dashboard())
        
        # Iniciar sistema principal
        await system.start()
        
    except KeyboardInterrupt:
        logger.info("Deteniendo sistema por interrupción del usuario...")
        system.stop()
        
    except Exception as e:
        logger.error(f"Error fatal en el sistema: {str(e)}")
        raise
        
    finally:
        # Asegurar que el dashboard se detenga
        if 'dashboard_task' in locals():
            dashboard_task.cancel()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nSistema detenido por el usuario")
    except Exception as e:
        print(f"\nError fatal: {str(e)}") 