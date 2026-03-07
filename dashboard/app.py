"""
Dashboard de Análisis de Sentimiento - Prensa Deportiva Real Madrid
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import func, select
from sqlalchemy.orm import Session

# Añadir data_pipeline al path
sys.path.insert(0, str(Path(__file__).parent.parent / "data_pipeline"))
import db


# Configuración de la página
st.set_page_config(
    page_title="Sentimiento Prensa - Real Madrid",
    page_icon="⚽",
    layout="wide",
)


# Mapeo de sentimiento a score numérico para ranking
SENTIMENT_SCORES = {
    "VERY POSITIVE": 2,
    "POSITIVE": 1,
    "NEUTRAL": 0,
    "UNDEFINED": 0,
    "NEGATIVE": -1,
    "VERY NEGATIVE": -2,
}

SENTIMENT_COLORS = {
    "VERY POSITIVE": "#00a651",
    "POSITIVE": "#90ee90",
    "NEUTRAL": "#d3d3d3",
    "UNDEFINED": "#ffa500",
    "NEGATIVE": "#ff6b6b",
    "VERY NEGATIVE": "#d32f2f",
}


def load_articles(start_date=None, end_date=None):
    """Carga artículos de la DB con filtros opcionales de fecha."""
    try:
        with Session(db.engine) as session:
            stmt = select(db.ArticleRow).where(db.ArticleRow.sentiment_label.is_not(None))
            
            if start_date:
                stmt = stmt.where(db.ArticleRow.published_at >= start_date)
            if end_date:
                stmt = stmt.where(db.ArticleRow.published_at <= end_date)
            
            articles = list(session.scalars(stmt).all())
            
            # Convertir a DataFrame
            data = [{
                'player': a.player,
                'title': a.title,
                'url': a.url,
                'published_at': a.published_at,
                'sentiment_label': a.sentiment_label,
                'sentiment_score': a.sentiment_score,
            } for a in articles]
            
            return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error al cargar artículos de la base de datos: {e}")
        st.info("Intenta recargar la página. Si el problema persiste, verifica que no haya otros procesos usando la DB.")
        return pd.DataFrame()


def calculate_player_scores(df):
    """Calcula el score agregado por jugador."""
    df['numeric_score'] = df['sentiment_label'].map(SENTIMENT_SCORES)
    
    player_stats = df.groupby('player').agg({
        'numeric_score': 'mean',
        'player': 'count'
    }).rename(columns={'player': 'total_articles'})
    
    player_stats = player_stats.reset_index()
    player_stats = player_stats.sort_values('numeric_score', ascending=False)
    
    return player_stats


def plot_ranking(player_stats):
    """Gráfico de ranking de jugadores."""
    fig = px.bar(
        player_stats,
        y='player',
        x='numeric_score',
        orientation='h',
        title='Ranking de Jugadores por Sentimiento',
        labels={'numeric_score': 'Score de Sentimiento', 'player': 'Jugador'},
        color='numeric_score',
        color_continuous_scale=['#d32f2f', '#ffa500', '#00a651'],
        text='numeric_score'
    )
    
    fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    fig.update_layout(height=600, showlegend=False)
    
    return fig


def plot_sentiment_distribution(df):
    """Heatmap de distribución de sentimientos por jugador."""
    # Calcular porcentajes
    sentiment_counts = df.groupby(['player', 'sentiment_label']).size().reset_index(name='count')
    total_per_player = df.groupby('player').size().reset_index(name='total')
    
    sentiment_counts = sentiment_counts.merge(total_per_player, on='player')
    sentiment_counts['percentage'] = (sentiment_counts['count'] / sentiment_counts['total'] * 100).round(1)
    
    # Pivot para heatmap
    pivot = sentiment_counts.pivot(index='player', columns='sentiment_label', values='percentage').fillna(0)
    
    # Ordenar columnas por orden lógico
    label_order = ['VERY POSITIVE', 'POSITIVE', 'NEUTRAL', 'UNDEFINED', 'NEGATIVE', 'VERY NEGATIVE']
    pivot = pivot[[col for col in label_order if col in pivot.columns]]
    
    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns,
        y=pivot.index,
        colorscale='RdYlGn',
        text=pivot.values,
        texttemplate='%{text:.0f}%',
        textfont={"size": 10},
        hovertemplate='Jugador: %{y}<br>Label: %{x}<br>Porcentaje: %{z:.1f}%<extra></extra>'
    ))
    
    fig.update_layout(
        title='Distribución de Sentimiento por Jugador (%)',
        xaxis_title='Sentimiento',
        yaxis_title='Jugador',
        height=600
    )
    
    return fig


def plot_player_pie(df, player):
    """Pie chart del sentimiento para un jugador específico."""
    player_df = df[df['player'] == player]
    
    sentiment_counts = player_df['sentiment_label'].value_counts()
    
    fig = go.Figure(data=[go.Pie(
        labels=sentiment_counts.index,
        values=sentiment_counts.values,
        marker=dict(colors=[SENTIMENT_COLORS.get(label, '#cccccc') for label in sentiment_counts.index]),
        textinfo='label+percent',
        hovertemplate='%{label}: %{value} artículos<br>%{percent}<extra></extra>'
    )])
    
    fig.update_layout(
        title=f'Distribución de Sentimiento - {player}',
        height=400
    )
    
    return fig


def main():
    st.title("⚽ Análisis de Sentimiento - Prensa Real Madrid")
    st.markdown("Análisis automático del tono de la prensa deportiva sobre jugadores del Real Madrid")
    
    st.markdown("---")
    
    # ============================================================
    # SECCIÓN 1: FILTROS
    # ============================================================
    st.header("📅 Filtros")
    
    col1, col2 = st.columns(2)
    
    with col1:
        date_filter = st.selectbox(
            "Periodo de análisis",
            ["Todo el tiempo", "Últimos 7 días", "Últimos 30 días", "Custom"],
            index=0
        )
    
    start_date = None
    end_date = None
    
    if date_filter == "Últimos 7 días":
        start_date = datetime.now() - timedelta(days=7)
    elif date_filter == "Últimos 30 días":
        start_date = datetime.now() - timedelta(days=30)
    elif date_filter == "Custom":
        with col2:
            start_date = st.date_input("Desde", value=datetime.now() - timedelta(days=30))
            end_date = st.date_input("Hasta", value=datetime.now())
    
    # Cargar datos
    df = load_articles(start_date, end_date)
    
    if df.empty:
        st.error("No hay artículos en el periodo seleccionado.")
        return
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Artículos", len(df))
    
    with col2:
        positive_pct = (df['sentiment_label'].isin(['VERY POSITIVE', 'POSITIVE']).sum() / len(df) * 100)
        st.metric("% Positivo", f"{positive_pct:.1f}%")
    
    with col3:
        negative_pct = (df['sentiment_label'].isin(['VERY NEGATIVE', 'NEGATIVE']).sum() / len(df) * 100)
        st.metric("% Negativo", f"{negative_pct:.1f}%")
    
    with col4:
        neutral_pct = (df['sentiment_label'].isin(['NEUTRAL', 'UNDEFINED']).sum() / len(df) * 100)
        st.metric("% Neutral", f"{neutral_pct:.1f}%")
    
    st.markdown("---")
    
    # ============================================================
    # SECCIÓN 2: COMPARATIVA GENERAL
    # ============================================================
    st.header("📊 Comparativa General")
    
    player_stats = calculate_player_scores(df)
    
    # Top 3 / Bottom 3
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏆 Mejor Tratados")
        top3 = player_stats.head(3)
        for idx, row in top3.iterrows():
            st.success(f"**{row['player']}**: {row['numeric_score']:.2f} ({int(row['total_articles'])} artículos)")
    
    with col2:
        st.subheader("📉 Peor Tratados")
        bottom3 = player_stats.tail(3).iloc[::-1]
        for idx, row in bottom3.iterrows():
            st.error(f"**{row['player']}**: {row['numeric_score']:.2f} ({int(row['total_articles'])} artículos)")
    
    # Gráfico de ranking
    st.plotly_chart(plot_ranking(player_stats), use_container_width=True)
    
    # Heatmap de distribución
    st.plotly_chart(plot_sentiment_distribution(df), use_container_width=True)
    
    st.markdown("---")
    
    # ============================================================
    # SECCIÓN 3: ANÁLISIS INDIVIDUAL
    # ============================================================
    st.header("🔍 Análisis Individual")
    
    selected_player = st.selectbox(
        "Selecciona un jugador",
        sorted(df['player'].unique())
    )
    
    player_df = df[df['player'] == selected_player]
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        avg_score = player_df['sentiment_label'].map(SENTIMENT_SCORES).mean()
        st.metric("Score Promedio", f"{avg_score:.2f}")
        st.metric("Total Artículos", len(player_df))
        
        st.plotly_chart(plot_player_pie(df, selected_player), use_container_width=True)
    
    with col2:
        st.subheader(f"📰 Artículos Recientes - {selected_player}")
        
        # Tabla de artículos
        recent_articles = player_df.sort_values('published_at', ascending=False).head(10)
        
        for _, article in recent_articles.iterrows():
            sentiment_color = SENTIMENT_COLORS.get(article['sentiment_label'], '#cccccc')
            
            with st.container():
                col_label, col_content = st.columns([1, 4])
                
                with col_label:
                    st.markdown(
                        f"<div style='background-color: {sentiment_color}; padding: 5px; "
                        f"border-radius: 5px; text-align: center; color: white; font-weight: bold;'>"
                        f"{article['sentiment_label']}</div>",
                        unsafe_allow_html=True
                    )
                
                with col_content:
                    st.markdown(f"**{article['title']}**")
                    st.caption(f"📅 {article['published_at'].strftime('%d/%m/%Y %H:%M')} | "
                             f"Score: {article['sentiment_score']:.2f}")
                    st.markdown(f"[🔗 Ver artículo]({article['url']})")
                
                st.markdown("---")


if __name__ == "__main__":
    main()
