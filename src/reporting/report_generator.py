import pandas as pd
import json
from typing import List, Dict, Any
from datetime import datetime
import asyncio
from ..agents.technical_analyst import TechnicalAnalyst
from ..data.bybit_connector import BybitConnector
from ..analysis.market_analyzer import MarketAnalyzer

class ReportGenerator:
    def __init__(self, bybit_connector: BybitConnector):
        self.connector = bybit_connector
        self.agents: Dict[str, TechnicalAnalyst] = {}
        self.market_analyzer = MarketAnalyzer()
        self._initialize_agents()

    def _initialize_agents(self):
        """Inicializa un agente técnico para cada par de trading"""
        for pair in self.connector.trading_pairs:
            self.agents[pair] = TechnicalAnalyst(f"analyst_{pair}", pair)

    async def generate_market_report(self) -> Dict[str, Any]:
        """Genera un informe completo del mercado"""
        try:
            # Obtener datos del mercado
            market_data = await self.connector.get_market_data()
            
            # Analizar cada par con su agente correspondiente
            analyses = await self._analyze_all_pairs(market_data)
            
            # Calcular métricas generales del mercado
            market_overview = await self._calculate_market_overview()
            
            # Generar matriz de correlación
            correlation_matrix = self._calculate_correlation_matrix(market_data)
            
            # Construir el informe final
            report = {
                "timestamp": datetime.utcnow().isoformat(),
                "market_overview": market_overview,
                "individual_analyses": analyses,
                "correlation_matrix": correlation_matrix,
                "risk_assessment": await self._assess_market_risk(analyses)
            }
            
            return report
            
        except Exception as e:
            raise Exception(f"Error generating market report: {str(e)}")

    async def _analyze_all_pairs(self, market_data: Dict[str, pd.DataFrame]) -> List[Dict[str, Any]]:
        """Ejecuta el análisis para todos los pares en paralelo"""
        analyses = []
        tasks = []
        
        for pair, data in market_data.items():
            if pair in self.agents:
                tasks.append(self.agents[pair].analyze(data))
        
        results = await asyncio.gather(*tasks)
        return results

    async def _calculate_market_overview(self) -> Dict[str, Any]:
        """Calcula métricas generales del mercado"""
        market_data = await self.connector.get_market_data()
        
        # Analizar condiciones de mercado
        market_condition = await self.market_analyzer.analyze_market_conditions(market_data)
        
        # Calcular impacto de correlaciones
        correlation_impact = self.market_analyzer.calculate_correlation_impact(market_data)
        
        # Detectar movimientos extremos
        extremes = self.market_analyzer.detect_market_extremes(market_data)
        
        return {
            "market_condition": {
                "sentiment": market_condition.sentiment,
                "volatility": market_condition.volatility,
                "strength": market_condition.strength,
                "description": market_condition.description
            },
            "correlation_impact": correlation_impact,
            "extreme_movements": extremes
        }

    def _calculate_correlation_matrix(self, market_data: Dict[str, pd.DataFrame]) -> Dict[str, float]:
        """Calcula la matriz de correlación entre pares"""
        correlation_dict = {}
        pairs = list(market_data.keys())
        
        for i in range(len(pairs)):
            for j in range(i + 1, len(pairs)):
                pair1, pair2 = pairs[i], pairs[j]
                correlation = market_data[pair1]['close'].corr(market_data[pair2]['close'])
                correlation_dict[f"{pair1}_{pair2}_correlation"] = round(float(correlation), 2)
        
        return correlation_dict

    async def _assess_market_risk(self, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Evalúa el riesgo general del mercado"""
        bullish_count = sum(1 for analysis in analyses if analysis['trend'] == 'bullish')
        bearish_count = sum(1 for analysis in analyses if analysis['trend'] == 'bearish')
        
        total_pairs = len(analyses)
        market_direction = "bullish" if bullish_count > bearish_count else "bearish"
        confidence = abs(bullish_count - bearish_count) / total_pairs
        
        return {
            "potential_movement": market_direction,
            "confidence_level": round(confidence, 2)
        }

    async def _calculate_volatility_index(self) -> float:
        """Calcula un índice de volatilidad personalizado"""
        volatilities = []
        
        for pair in self.connector.trading_pairs:
            ticker = await self.connector.get_ticker_info(pair)
            price_range = (ticker['high_24h'] - ticker['low_24h']) / ticker['last_price']
            volatilities.append(price_range)
        
        return round(sum(volatilities) / len(volatilities), 2)

    def _classify_sentiment(self, sentiment: float) -> str:
        """Clasifica el sentimiento del mercado"""
        if sentiment > 0.03:
            return "bullish"
        elif sentiment < -0.03:
            return "bearish"
        return "neutral"

    def export_report(self, report: Dict[str, Any], format: str = "json") -> str:
        """Exporta el informe en el formato especificado"""
        if format.lower() == "json":
            return json.dumps(report, indent=2)
        else:
            raise ValueError(f"Formato de exportación no soportado: {format}") 