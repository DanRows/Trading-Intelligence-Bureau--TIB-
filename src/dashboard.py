import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
import asyncio
from typing import Dict, Any

class Dashboard:
    def __init__(self, market_data: Dict[str, Any], analyses: Dict[str, Any]):
        self.market_data = market_data
        self.analyses = analyses
        
    def render(self):
        """Renderiza el dashboard"""
        st.set_page_config(page_title="Trading Intelligence Bureau", layout="wide")
        st.title("Trading Intelligence Bureau")
        
        # Mostrar análisis por par
        for pair, analysis in self.analyses.items():
            self._render_pair_analysis(pair, analysis)
    
    def _render_pair_analysis(self, pair: str, analysis: Dict[str, Any]):
        """Renderiza el análisis de un par"""
        st.subheader(f"Análisis de {pair}")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Gráfico de velas
            fig = go.Figure(data=[
                go.Candlestick(
                    x=self.market_data[pair]['timestamp'],
                    open=self.market_data[pair]['open'],
                    high=self.market_data[pair]['high'],
                    low=self.market_data[pair]['low'],
                    close=self.market_data[pair]['close']
                )
            ])
            
            fig.update_layout(
                title=f"{pair} - Precio",
                yaxis_title="Precio",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Mostrar alertas si existen
            if 'alerts' in analysis and analysis['alerts']:
                st.subheader("⚠️ Alertas Activas")
                for alert in analysis['alerts']:
                    with st.expander(f"{alert.severity.upper()}: {alert.message}"):
                        st.write(f"Tipo: {alert.type}")
                        st.write(f"Timestamp: {alert.timestamp}")
                        st.json(alert.data)
        
        with col2:
            # Métricas
            st.metric("Tendencia", analysis['trend'])
            st.metric("RSI", f"{analysis['rsi']:.2f}")
            st.metric(
                "Volumen", 
                f"{analysis['volume_analysis']['current_volume']:,.0f}",
                f"{(analysis['volume_analysis']['volume_ratio'] - 1) * 100:.1f}%"
            )
            
            # Nuevos indicadores
            with st.expander("Indicadores Técnicos"):
                # MACD
                macd = analysis['indicators']['macd']
                st.write("MACD")
                st.write(f"- Valor: {macd['value']:.4f}")
                st.write(f"- Señal: {macd['signal']:.4f}")
                st.write(f"- Histograma: {macd['histogram']:.4f}")
                
                # Bandas de Bollinger
                bb = analysis['indicators']['bollinger_bands']
                st.write("Bandas de Bollinger")
                st.write(f"- Superior: {bb['upper']:.2f}")
                st.write(f"- Media: {bb['middle']:.2f}")
                st.write(f"- Inferior: {bb['lower']:.2f}")
                
                # Estocástico
                stoch = analysis['indicators']['stochastic']
                st.write("Estocástico")
                st.write(f"- %K: {stoch['k']:.2f}")
                st.write(f"- %D: {stoch['d']:.2f}")