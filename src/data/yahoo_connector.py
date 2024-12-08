import pandas as pd
import yfinance as yf
import logging
from typing import Dict, Any, Optional
from src.config.settings import Settings

logger = logging.getLogger(__name__)

class YahooConnector:
    """Conector para Yahoo Finance."""
    
    def __init__(self, settings: Settings):
        """
        Inicializa el conector de Yahoo Finance.
        
        Args:
            settings: Configuración global
        """
        self.settings = settings
        
    async def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene cotización actual de un símbolo.
        
        Args:
            symbol: Símbolo a consultar
            
        Returns:
            Dict con datos de la cotización
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                'regularMarketPrice': info.get('regularMarketPrice', 0),
                'regularMarketChangePercent': info.get('regularMarketChangePercent', 0),
                'regularMarketOpen': info.get('regularMarketOpen', 0),
                'regularMarketDayHigh': info.get('regularMarketDayHigh', 0),
                'regularMarketDayLow': info.get('regularMarketDayLow', 0),
                'volume': info.get('volume', 0),
                'marketCap': info.get('marketCap', 0),
                'fiftyTwoWeekHigh': info.get('fiftyTwoWeekHigh', 0),
                'fiftyTwoWeekLow': info.get('fiftyTwoWeekLow', 0)
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo cotización: {str(e)}")
            return None
            
    async def get_history(self, symbol: str, period: str = "1y") -> pd.DataFrame:
        """
        Obtiene historial de precios.
        
        Args:
            symbol: Símbolo a consultar
            period: Periodo de tiempo (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            
        Returns:
            DataFrame con historial de precios
        """
        try:
            ticker = yf.Ticker(symbol)
            history = ticker.history(period=period)
            return history
            
        except Exception as e:
            logger.error(f"Error obteniendo historial: {str(e)}")
            return pd.DataFrame()
            
    async def get_financials(self, symbol: str) -> Optional[Dict[str, pd.DataFrame]]:
        """
        Obtiene datos financieros de una empresa.
        
        Args:
            symbol: Símbolo a consultar
            
        Returns:
            Dict con balance, estado de resultados y flujo de efectivo
        """
        try:
            ticker = yf.Ticker(symbol)
            
            return {
                'balance_sheet': ticker.balance_sheet,
                'income_statement': ticker.income_stmt,
                'cash_flow': ticker.cashflow
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo datos financieros: {str(e)}")
            return None
            
    async def search_symbols(self, query: str) -> list:
        """
        Busca símbolos que coincidan con la consulta.
        
        Args:
            query: Término de búsqueda
            
        Returns:
            Lista de símbolos encontrados
        """
        try:
            tickers = yf.Tickers(query)
            return [ticker for ticker in tickers.tickers]
            
        except Exception as e:
            logger.error(f"Error buscando símbolos: {str(e)}")
            return []