import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any
import asyncio
from datetime import datetime, timedelta
from ..data.bybit_connector import BybitConnector
from .report_generator import ReportGenerator

class TradingDashboard:
    def __init__(self, api_key: str, api_secret: str):
        self.connector = BybitConnector(api_key, api_secret)
        self.report_generator = ReportGenerator(self.connector)
        
    def run(self):
        """Inicializa y ejecuta el dashboard"""
        st.set_page_config(page_title="Crypto Trading Analysis", layout="wide")
        st.title("Análisis de Trading de Criptomonedas")
        
        # Sidebar para configuración
        self._render_sidebar()
        
        # Layout principal
        col1, col2 = st.columns([2, 1])
        
        with col1:
            self._render_market_overview()
            self._render_price_charts()
            
        with col2:
            self._render_correlation_matrix()
            self._render_risk_assessment()

    def _render_sidebar(self):
        """Renderiza la barra lateral con controles"""
        st.sidebar.header("Configuración")
        
        # Intervalo de actualización
        update_interval = st.sidebar.slider(
            "Intervalo de actualización (segundos)",
            min_value=5,
            max_value=300,
            value=60
        )
        
        # Selección de pares
        selected_pairs = st.sidebar.multiselect(
            "Pares de Trading",
            self.connector.trading_pairs,
            default=self.connector.trading_pairs[:3]
        )
        
        # Botón de actualización manual
        if st.sidebar.button("Actualizar Ahora"):
            st.experimental_rerun()

    async def _render_market_overview(self):
        """Renderiza la visión general del mercado"""
        st.subheader("Visión General del Mercado")
        
        try:
            report = await self.report_generator.generate_market_report()
            overview = report["market_overview"]
            
            # Métricas principales
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Volumen Total (24h)",
                    f"${overview['total_volume']:,.2f}"
                )
                
            with col2:
                st.metric(
                    "Sentimiento del Mercado",
                    overview['market_sentiment']
                )
                
            with col3:
                st.metric(
                    "Índice de Volatilidad",
                    f"{overview['volatility_index']:.2%}"
                )
                
        except Exception as e:
            st.error(f"Error al cargar la visión general: {str(e)}")

    async def _render_price_charts(self):
        """Renderiza gráficos de precios"""
        st.subheader("Análisis de Precios")
        
        try:
            market_data = await self.connector.get_market_data()
            
            for pair, data in market_data.items():
                fig = go.Figure(data=[
                    go.Candlestick(
                        x=data['timestamp'],
                        open=data['open'],
                        high=data['high'],
                        low=data['low'],
                        close=data['close'],
                        name=pair
                    )
                ])
                
                fig.update_layout(
                    title=f"{pair} - Gráfico de Velas",
                    xaxis_title="Fecha",
                    yaxis_title="Precio",
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
        except Exception as e:
            st.error(f"Error al renderizar gráficos: {str(e)}")

    def _render_correlation_matrix(self):
        """Renderiza la matriz de correlación"""
        st.subheader("Matriz de Correlación")
        
        try:
            report = asyncio.run(self.report_generator.generate_market_report())
            correlations = report["correlation_matrix"]
            
            # Convertir el diccionario de correlaciones a DataFrame
            pairs = list(self.connector.trading_pairs)
            corr_matrix = pd.DataFrame(index=pairs, columns=pairs)
            
            for pair1 in pairs:
                for pair2 in pairs:
                    if pair1 == pair2:
                        corr_matrix.loc[pair1, pair2] = 1.0
                    else:
                        key = f"{pair1}_{pair2}_correlation"
                        rev_key = f"{pair2}_{pair1}_correlation"
                        value = correlations.get(key) or correlations.get(rev_key) or 0
                        corr_matrix.loc[pair1, pair2] = value
            
            fig = px.imshow(
                corr_matrix,
                labels=dict(color="Correlación"),
                color_continuous_scale="RdBu"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error al renderizar matriz de correlación: {str(e)}")

    async def _render_risk_assessment(self):
        """Renderiza la evaluación de riesgo"""
        st.subheader("Evaluación de Riesgo")
        
        try:
            report = await self.report_generator.generate_market_report()
            risk = report["risk_assessment"]
            
            # Gauge chart para nivel de confianza
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = risk["confidence_level"] * 100,
                title = {'text': f"Nivel de Confianza - {risk['potential_movement'].title()}"},
                gauge = {
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 33], 'color': "lightgray"},
                        {'range': [33, 66], 'color': "gray"},
                        {'range': [66, 100], 'color': "darkgray"}
                    ]
                }
            ))
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error al renderizar evaluación de riesgo: {str(e)}")

def main():
    """Función principal para ejecutar el dashboard"""
    api_key = st.secrets["BYBIT_API_KEY"]
    api_secret = st.secrets["BYBIT_API_SECRET"]
    
    dashboard = TradingDashboard(api_key, api_secret)
    dashboard.run()

if __name__ == "__main__":
    main() 