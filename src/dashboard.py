import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
import asyncio
from typing import Dict, Any, List
import pandas as pd
from data.realtime_data import RealtimeDataService

class Dashboard:
    def __init__(self, market_data: Dict[str, Any], analyses: Dict[str, Any]):
        self.market_data = market_data
        self.analyses = analyses
        
    def render(self):
        """Renderiza el dashboard"""
        st.set_page_config(
            page_title="🚀 Crypto Analyzer Pro",
            layout="wide",
            page_icon="📊"
        )
        
        # Estilo personalizado
        st.markdown("""
            <style>
            .main {
                background-color: #0e1117;
            }
            .stAlert {
                background-color: #1c1c1c;
                color: #ffffff;
            }
            </style>
            """, unsafe_allow_html=True)
            
        st.title("🚀 Crypto Analyzer Pro")
        
        # Mostrar análisis por par
        for pair, data in self.market_data.items():
            self._render_pair_analysis(pair, data)
            
    def _render_pair_analysis(self, pair: str, data: pd.DataFrame):
        """Renderiza el análisis de un par"""
        st.subheader(f"Análisis de {pair}")
        
        # Datos en tiempo real
        realtime_service = RealtimeDataService()
        realtime_data = asyncio.run(realtime_service.update_realtime_data())
        
        if pair in realtime_data:
            rt_data = realtime_data[pair]
            
            # Métricas en tiempo real
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Precio (Tiempo Real)",
                    f"${rt_data['price']:,.2f}",
                    f"{rt_data['change_24h']:.2f}%"
                )
                
            with col2:
                st.metric(
                    "Volumen 24h",
                    f"${rt_data['volume_24h']:,.0f}",
                    f"High: ${rt_data['high_24h']:,.2f}"
                )
                
            with col3:
                market_cap = rt_data.get('market_cap', 0)
                st.metric(
                    "Market Cap",
                    f"${market_cap:,.0f}"
                )
                
            with col4:
                st.metric(
                    "Última Actualización",
                    rt_data['last_update'].strftime('%H:%M:%S')
                )
                
            # Agregar botón de actualización manual
            if st.button(" Actualizar Datos"):
                st.experimental_rerun()
                
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        
        current_price = data['Close'].iloc[-1]
        prev_price = data['Close'].iloc[-2]
        price_change = ((current_price - prev_price) / prev_price) * 100
        rsi = data['RSI'].iloc[-1]
        
        with col1:
            st.metric(
                "Precio Actual",
                f"${current_price:,.2f}",
                f"{price_change:.2f}%"
            )
            
        with col2:
            st.metric(
                "RSI",
                f"{rsi:.2f}",
                "Neutral" if 45 < rsi < 55 else "Sobrecompra" if rsi > 70 else "Sobreventa" if rsi < 30 else ""
            )
            
        with col3:
            trend = self._analyze_trend(data)
            st.metric("Tendencia", trend)
            
        with col4:
            volume_change = ((data['Volume'].iloc[-1] - data['Volume'].iloc[-2]) / data['Volume'].iloc[-2]) * 100
            st.metric("Cambio Volumen 24h", f"{volume_change:.2f}%")
        
        # Gráficos
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.plotly_chart(self._render_price_chart(pair, data), use_container_width=True)
            st.plotly_chart(self._render_indicators(data), use_container_width=True)
            
        with col2:
            # Análisis técnico
            with st.expander("📊 Análisis Técnico", expanded=True):
                analysis = self._generate_analysis(data)
                for point in analysis:
                    st.write(point)
                    
            # Datos técnicos
            with st.expander("🔍 Datos Técnicos"):
                latest = data.iloc[-1]
                st.write(f"SMA 20: ${latest['SMA_20']:.2f}")
                st.write(f"SMA 50: ${latest['SMA_50']:.2f}")
                st.write(f"SMA 200: ${latest['SMA_200']:.2f}")
                st.write(f"RSI: {latest['RSI']:.2f}")
                st.write(f"Volumen: {latest['Volume']:,.0f}")
                
        # Disclaimer
        st.warning("""
        ⚠️ DISCLAIMER: Este es un análisis automático con fines educativos.
        No constituye consejo financiero. El mercado crypto es altamente volátil y riesgoso.
        Siempre realiza tu propia investigación antes de tomar decisiones de inversión.
        """)
        
    def _analyze_trend(self, df: pd.DataFrame) -> str:
        """Analiza la tendencia usando SMAs"""
        current_price = df['Close'].iloc[-1]
        sma_20 = df['SMA_20'].iloc[-1]
        sma_50 = df['SMA_50'].iloc[-1]
        sma_200 = df['SMA_200'].iloc[-1]
        
        if current_price > sma_20 > sma_50 > sma_200:
            return "Alcista Fuerte"
        elif current_price < sma_20 < sma_50 < sma_200:
            return "Bajista Fuerte"
        elif current_price > sma_20 and current_price > sma_50:
            return "Alcista Moderada"
        else:
            return "Bajista Moderada"
            
    def _generate_analysis(self, df: pd.DataFrame) -> List[str]:
        """Genera análisis técnico detallado"""
        analysis = []
        
        # Análisis de tendencia
        trend = self._analyze_trend(df)
        analysis.append(f"🎯 Tendencia: {trend}")
        
        # Análisis RSI
        rsi = df['RSI'].iloc[-1]
        if rsi > 70:
            analysis.append("⚠️ RSI indica sobrecompra")
        elif rsi < 30:
            analysis.append("⚠️ RSI indica sobreventa")
        else:
            analysis.append("✅ RSI en rango neutral")
            
        # Análisis MACD
        macd = df['MACD'].iloc[-1]
        macd_signal = df['MACD_signal'].iloc[-1]
        if macd > macd_signal:
            analysis.append("📈 MACD muestra momentum alcista")
        else:
            analysis.append("📉 MACD muestra momentum bajista")
            
        # Análisis Bollinger Bands
        price = df['Close'].iloc[-1]
        bb_high = df['BB_high'].iloc[-1]
        bb_low = df['BB_low'].iloc[-1]
        
        if price > bb_high:
            analysis.append("⚠️ Precio por encima de Banda Superior de Bollinger")
        elif price < bb_low:
            analysis.append("⚠️ Precio por debajo de Banda Inferior de Bollinger")
            
        return analysis
        
    def _render_price_chart(self, pair: str, data: pd.DataFrame):
        """Renderiza el gráfico de precios con indicadores"""
        fig = go.Figure()
        
        # Velas japonesas
        fig.add_trace(go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name=pair
        ))
        
        # Medias móviles
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['SMA_20'],
            name='SMA 20',
            line=dict(color='yellow', width=1)
        ))
        
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['SMA_50'],
            name='SMA 50',
            line=dict(color='blue', width=1)
        ))
        
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['SMA_200'],
            name='SMA 200',
            line=dict(color='red', width=1)
        ))
        
        # Bandas de Bollinger
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['BB_high'],
            name='BB Superior',
            line=dict(color='gray', dash='dash'),
            opacity=0.5
        ))
        
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['BB_low'],
            name='BB Inferior',
            line=dict(color='gray', dash='dash'),
            fill='tonexty',
            opacity=0.5
        ))
        
        fig.update_layout(
            title=f'{pair} - Análisis Técnico',
            yaxis_title='Precio USD',
            template='plotly_dark',
            height=600
        )
        
        return fig
        
    def _render_indicators(self, data: pd.DataFrame):
        """Renderiza los indicadores técnicos"""
        fig = go.Figure()
        
        # RSI
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['RSI'],
            name='RSI',
            line=dict(color='purple')
        ))
        
        # Líneas de referencia RSI
        fig.add_hline(y=70, line_color='red', line_dash='dash')
        fig.add_hline(y=30, line_color='green', line_dash='dash')
        
        # MACD
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['MACD'],
            name='MACD',
            line=dict(color='blue')
        ))
        
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['MACD_signal'],
            name='Señal MACD',
            line=dict(color='orange')
        ))
        
        fig.update_layout(
            title='Indicadores Técnicos',
            template='plotly_dark',
            height=400,
            showlegend=True
        )
        
        return fig