"""
Dashboard de Análisis de Sentimiento - Prensa Deportiva
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import select, func
from sqlalchemy.orm import Session, joinedload

# Añadir data_pipeline al path
sys.path.insert(0, str(Path(__file__).parent.parent / "data_pipeline"))
import db


# Configuración de la página
st.set_page_config(
    page_title="El Sesgo del Fútbol",
    page_icon="⚽",
    layout="wide",
)


# Mapeo de sentimiento a score numérico para ranking
SENTIMENT_SCORES = {
    "POS": 1,
    "NEU": 0,
    "NEG": -1,
}

SENTIMENT_COLORS = {
    "POS": "#00a651",     # Verde
    "NEU": "#d3d3d3",     # Gris
    "NEG": "#d32f2f",     # Rojo
}

# Logos de equipos vía ESPN CDN (tamaño uniforme 500px, se muestra a 30px)
TEAM_LOGOS: dict[str, str] = {
    "Real Madrid":        "https://a.espncdn.com/i/teamlogos/soccer/500/86.png",
    "FC Barcelona":       "https://a.espncdn.com/i/teamlogos/soccer/500/83.png",
    "Atlético de Madrid": "https://a.espncdn.com/i/teamlogos/soccer/500/1068.png",
    "Villarreal CF":      "https://a.espncdn.com/i/teamlogos/soccer/500/102.png",
    "Valencia CF":        "https://a.espncdn.com/i/teamlogos/soccer/500/94.png",
    "Sevilla FC":         "https://a.espncdn.com/i/teamlogos/soccer/500/243.png",
    "Athletic Club":      "https://a.espncdn.com/i/teamlogos/soccer/500/93.png",
    "Real Sociedad":      "https://a.espncdn.com/i/teamlogos/soccer/500/89.png",
    "Real Betis":         "https://a.espncdn.com/i/teamlogos/soccer/500/244.png",
    "Celta de Vigo":      "https://a.espncdn.com/i/teamlogos/soccer/500/85.png",
    "Rayo Vallecano":     "https://a.espncdn.com/i/teamlogos/soccer/500/101.png",
    "Girona FC":          "https://a.espncdn.com/i/teamlogos/soccer/500/9812.png",
    "CA Osasuna":         "https://a.espncdn.com/i/teamlogos/soccer/500/97.png",
    "Getafe CF":          "https://a.espncdn.com/i/teamlogos/soccer/500/2922.png",
    "Deportivo Alavés":   "https://a.espncdn.com/i/teamlogos/soccer/500/96.png",
    "RCD Mallorca":       "https://a.espncdn.com/i/teamlogos/soccer/500/84.png",
    "RCD Espanyol":       "https://a.espncdn.com/i/teamlogos/soccer/500/88.png",
    "Levante UD": "",
    "Elche": "",
    "Oviedo" : "",
}

# Logos de LaLiga y Marca para branding del dashboard
LALIGA_LOGO_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/LaLiga_logo.svg/160px-LaLiga_logo.svg.png"
MARCA_LOGO_URL  = "https://upload.wikimedia.org/wikipedia/commons/thumb/6/68/Logotipo_de_Marca.svg/160px-Logotipo_de_Marca.svg.png"


def load_articles(start_date=None, end_date=None):
    """Carga artículos de la DB con filtros opcionales de fecha."""
    try:
        with Session(db.engine) as session:
            stmt = (
                select(db.ArticleRow)
                .options(joinedload(db.ArticleRow.player_rel))
                .where(db.ArticleRow.sentiment_label.is_not(None))
            )

            if start_date:
                stmt = stmt.where(db.ArticleRow.published_at >= start_date)
            if end_date:
                stmt = stmt.where(db.ArticleRow.published_at <= end_date)

            articles = list(session.scalars(stmt).unique().all())

            data = [{
                'player': a.player,
                'team': a.club,
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
    label_order = ['POS', 'NEU', 'NEG']
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


def calculate_team_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula % de cada label por equipo. Ordenado de mayor a menor % positivo."""
    rows = []
    for team in sorted(df['team'].unique()):
        team_df = df[df['team'] == team]
        total = len(team_df)
        rows.append({
            'Equipo': team,
            '% Positivo': round((team_df['sentiment_label'] == 'POS').sum() / total * 100, 1),
            '% Negativo': round((team_df['sentiment_label'] == 'NEG').sum() / total * 100, 1),
            '% Neutro':   round((team_df['sentiment_label'] == 'NEU').sum() / total * 100, 1),
            'Total artículos': total,
        })
    return pd.DataFrame(rows).sort_values('% Positivo', ascending=False).reset_index(drop=True)


def calculate_team_rankings(df: pd.DataFrame) -> pd.DataFrame:
    """Ranking de equipos: volumen de cobertura e índice de positividad.

    Índice de positividad = (nº POS − nº NEG) / total × 100
    Score medio           = media de {POS→1, NEU→0, NEG→−1}
    """
    df2 = df.copy()
    df2['numeric_score'] = df2['sentiment_label'].map(SENTIMENT_SCORES)

    team_stats = (
        df2.groupby('team')
        .agg(
            total_articles=('title', 'count'),
            pos_count=('sentiment_label', lambda x: (x == 'POS').sum()),
            neg_count=('sentiment_label', lambda x: (x == 'NEG').sum()),
            neu_count=('sentiment_label', lambda x: (x == 'NEU').sum()),
            mean_score=('numeric_score', 'mean'),
        )
        .reset_index()
    )

    team_stats['positivity_index'] = (
        (team_stats['pos_count'] - team_stats['neg_count'])
        / team_stats['total_articles'] * 100
    ).round(1)
    team_stats['mean_score'] = team_stats['mean_score'].round(3)
    team_stats['logo'] = team_stats['team'].map(TEAM_LOGOS)

    return team_stats


def plot_coverage_ranking(team_rankings: pd.DataFrame) -> go.Figure:
    """Gráfico de barras horizontales: ranking por volumen de cobertura."""
    sorted_df = team_rankings.sort_values('total_articles', ascending=True)

    fig = go.Figure(go.Bar(
        x=sorted_df['total_articles'],
        y=sorted_df['team'],
        orientation='h',
        marker_color='#2196f3',
        text=sorted_df['total_articles'],
        textposition='outside',
        hovertemplate='%{y}<br>Artículos: %{x}<extra></extra>',
    ))
    fig.update_layout(
        title='📰 Volumen de Cobertura',
        xaxis_title='Nº de artículos',
        yaxis_title='',
        height=max(320, len(sorted_df) * 30),
        margin=dict(l=10, r=70, t=55, b=20),
        showlegend=False,
    )
    return fig


def plot_positivity_ranking(team_rankings: pd.DataFrame) -> go.Figure:
    """Gráfico de barras horizontales: ranking por índice de positividad."""
    sorted_df = team_rankings.sort_values('positivity_index', ascending=True)
    colors = [
        SENTIMENT_COLORS['POS'] if v >= 0 else SENTIMENT_COLORS['NEG']
        for v in sorted_df['positivity_index']
    ]

    fig = go.Figure(go.Bar(
        x=sorted_df['positivity_index'],
        y=sorted_df['team'],
        orientation='h',
        marker_color=colors,
        text=sorted_df['positivity_index'].apply(lambda v: f'{v:+.1f}%'),
        textposition='outside',
        hovertemplate='%{y}<br>Índice: %{x:+.1f}%<extra></extra>',
    ))
    fig.add_vline(x=0, line_dash='dot', line_color='gray', opacity=0.5)
    fig.update_layout(
        title='💚 Índice de Positividad',
        xaxis_title='(% artículos POS − % artículos NEG)',
        yaxis_title='',
        height=max(320, len(sorted_df) * 30),
        margin=dict(l=10, r=70, t=55, b=20),
        showlegend=False,
    )
    return fig


def plot_team_pie(df: pd.DataFrame, team: str):
    """Pie chart de distribución de sentimiento para un equipo."""
    team_df = df[df['team'] == team]
    counts = team_df['sentiment_label'].value_counts().reset_index()
    counts.columns = ['label', 'count']

    fig = px.pie(
        counts,
        names='label',
        values='count',
        title=f'Distribución de sentimiento — {team}',
        color='label',
        color_discrete_map=SENTIMENT_COLORS,
    )
    fig.update_traces(textinfo='label+percent',
                      hovertemplate='%{label}: %{value} artículos<br>%{percent}<extra></extra>')
    fig.update_layout(height=400)
    return fig


def plot_sentiment_evolution(df: pd.DataFrame, player: str):
    """Evolución semanal del score de sentimiento para un jugador."""
    player_df = df[df['player'] == player].copy()
    player_df['numeric_score'] = player_df['sentiment_label'].map(SENTIMENT_SCORES)
    player_df['published_at'] = pd.to_datetime(player_df['published_at'])
    player_df = player_df.dropna(subset=['published_at'])

    # Agrupar por semana
    player_df['semana'] = player_df['published_at'].dt.to_period('W').dt.start_time
    weekly = (
        player_df.groupby('semana')
        .agg(score=('numeric_score', 'mean'), articulos=('numeric_score', 'count'))
        .reset_index()
    )

    fig = px.line(
        weekly, x='semana', y='score',
        title=f'Evolución del sentimiento semanal — {player}',
        markers=True,
        custom_data=['articulos'],
    )
    fig.update_traces(
        line=dict(width=2.5),
        marker=dict(size=8),
        hovertemplate='Semana: %{x|%d %b %Y}<br>Score: %{y:.2f}<br>Artículos: %{customdata[0]}<extra></extra>',
    )
    # Línea de neutralidad
    fig.add_hline(y=0, line_dash='dot', line_color='gray', opacity=0.4,
                  annotation_text='Neutral', annotation_position='right')
    fig.update_layout(
        yaxis=dict(range=[-1.2, 1.2], title='Score  (1 = positivo · -1 = negativo)',
                   tickvals=[-1, 0, 1], ticktext=['NEG', 'NEU', 'POS']),
        xaxis_title='',
        height=320,
        margin=dict(t=50, b=20),
    )
    # Colorear el área bajo la línea según positivo/negativo
    fig.add_hrect(y0=0, y1=1.2,  fillcolor='#00a651', opacity=0.04, line_width=0)
    fig.add_hrect(y0=-1.2, y1=0, fillcolor='#d32f2f', opacity=0.04, line_width=0)
    return fig


def plot_player_vs_team(df: pd.DataFrame, player: str):
    """Barra horizontal: score del jugador vs. media del equipo."""
    player_df = df[df['player'] == player]
    if player_df.empty:
        return go.Figure()

    player_score = player_df['sentiment_label'].map(SENTIMENT_SCORES).mean()
    team = player_df['team'].iloc[0]
    team_score = df[df['team'] == team]['sentiment_label'].map(SENTIMENT_SCORES).mean()

    fig = go.Figure(go.Bar(
        x=[team_score, player_score],
        y=[f'Media {team}', player],
        orientation='h',
        marker_color=['rgba(128,128,128,0.45)',
                      SENTIMENT_COLORS['POS'] if player_score >= 0 else SENTIMENT_COLORS['NEG']],
        text=[f'{team_score:.2f}', f'{player_score:.2f}'],
        textposition='outside',
    ))
    fig.update_layout(
        title=f'{player} vs. media del equipo',
        xaxis=dict(range=[-1.2, 1.2], showticklabels=False, zeroline=True,
                   zerolinecolor='gray', zerolinewidth=1),
        height=170,
        margin=dict(t=45, b=10, l=10, r=50),
        showlegend=False,
    )
    return fig


def plot_player_comparison(df: pd.DataFrame, player1: str, player2: str) -> go.Figure:
    """Evolución semanal del score de dos jugadores en el mismo gráfico."""
    fig = go.Figure()
    palette = ['#2196f3', '#FF6F00']

    for i, player in enumerate([player1, player2]):
        pdf = df[df['player'] == player].copy()
        pdf['numeric_score'] = pdf['sentiment_label'].map(SENTIMENT_SCORES)
        pdf['published_at'] = pd.to_datetime(pdf['published_at'])
        pdf = pdf.dropna(subset=['published_at'])
        pdf['semana'] = pdf['published_at'].dt.to_period('W').dt.start_time

        weekly = (
            pdf.groupby('semana')
            .agg(score=('numeric_score', 'mean'), articulos=('numeric_score', 'count'))
            .reset_index()
        )
        fig.add_trace(go.Scatter(
            x=weekly['semana'], y=weekly['score'],
            name=player,
            mode='lines+markers',
            line=dict(width=2.5, color=palette[i]),
            marker=dict(size=7),
            customdata=weekly['articulos'],
            hovertemplate=(
                f'<b>{player}</b><br>'
                'Semana: %{x|%d %b %Y}<br>'
                'Score: %{y:.2f}<br>'
                'Artículos: %{customdata}<extra></extra>'
            ),
        ))

    fig.add_hline(y=0, line_dash='dot', line_color='gray', opacity=0.4,
                  annotation_text='Neutral', annotation_position='right')
    fig.add_hrect(y0=0,    y1=1.2,  fillcolor='#00a651', opacity=0.04, line_width=0)
    fig.add_hrect(y0=-1.2, y1=0,    fillcolor='#d32f2f', opacity=0.04, line_width=0)
    fig.update_layout(
        title=f'{player1} vs {player2} — Evolución del sentimiento',
        yaxis=dict(range=[-1.2, 1.2], title='Score',
                   tickvals=[-1, 0, 1], ticktext=['NEG', 'NEU', 'POS']),
        xaxis_title='',
        height=380,
        margin=dict(t=60, b=20),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
    )
    return fig


def _weekly_scores(df: pd.DataFrame, player: str) -> pd.DataFrame:
    """Calcula score semanal con rolling mean/std para un jugador."""
    pdf = df[df['player'] == player].copy()
    pdf['numeric_score'] = pdf['sentiment_label'].map(SENTIMENT_SCORES)
    pdf['published_at'] = pd.to_datetime(pdf['published_at'])
    pdf = pdf.dropna(subset=['published_at'])
    pdf['semana'] = pdf['published_at'].dt.to_period('W').dt.start_time
    weekly = (
        pdf.groupby('semana')
        .agg(score=('numeric_score', 'mean'), articulos=('numeric_score', 'count'))
        .reset_index()
        .sort_values('semana')
    )
    return weekly


def detect_anomalies(df: pd.DataFrame, player: str,
                     window: int = 6, threshold: float = 1.5) -> pd.DataFrame:
    """Semanas con score inusual (|z-score rolling| >= threshold).

    Usa una ventana deslizante hacia el pasado para evitar look-ahead bias.
    """
    weekly = _weekly_scores(df, player)
    if len(weekly) < window + 1:
        return pd.DataFrame()

    # shift(1): la media/std se calcula con datos ANTERIORES a la semana evaluada
    weekly['rolling_mean'] = weekly['score'].rolling(window, min_periods=3).mean().shift(1)
    weekly['rolling_std']  = weekly['score'].rolling(window, min_periods=3).std().shift(1)
    weekly['z_score'] = (
        (weekly['score'] - weekly['rolling_mean'])
        / weekly['rolling_std'].replace(0, float('nan'))
    )

    anomalies = weekly[weekly['z_score'].abs() >= threshold].copy()
    anomalies['direction'] = anomalies['z_score'].apply(
        lambda z: 'positiva' if z > 0 else 'negativa'
    )
    return anomalies[['semana', 'score', 'articulos', 'z_score', 'direction']].dropna()


def plot_anomaly_timeline(df: pd.DataFrame, player: str,
                          window: int = 6, threshold: float = 1.5) -> go.Figure:
    """Línea de sentimiento semanal con triángulos en las semanas anómalas."""
    weekly = _weekly_scores(df, player)
    weekly['rolling_mean'] = weekly['score'].rolling(window, min_periods=3).mean().shift(1)
    weekly['rolling_std']  = weekly['score'].rolling(window, min_periods=3).std().shift(1)
    weekly['z_score'] = (
        (weekly['score'] - weekly['rolling_mean'])
        / weekly['rolling_std'].replace(0, float('nan'))
    )
    anomalies = weekly[weekly['z_score'].abs() >= threshold].dropna(subset=['z_score'])

    fig = go.Figure()

    # Línea principal
    fig.add_trace(go.Scatter(
        x=weekly['semana'], y=weekly['score'],
        mode='lines+markers', name='Score semanal',
        line=dict(width=2.5, color='#2196f3'),
        marker=dict(size=6),
        customdata=weekly['articulos'],
        hovertemplate='Semana: %{x|%d %b %Y}<br>Score: %{y:.2f}<br>Artículos: %{customdata}<extra></extra>',
    ))

    # Marcadores de anomalías
    if not anomalies.empty:
        for z_sign, color, symbol, label in [
            (1,  SENTIMENT_COLORS['POS'], 'triangle-up',   '🟢 Pico positivo'),
            (-1, SENTIMENT_COLORS['NEG'], 'triangle-down',  '🔴 Pico negativo'),
        ]:
            subset = anomalies[anomalies['z_score'] * z_sign > 0]
            if not subset.empty:
                fig.add_trace(go.Scatter(
                    x=subset['semana'], y=subset['score'],
                    mode='markers', name=label,
                    marker=dict(size=15, color=color, symbol=symbol,
                                line=dict(width=2, color='white')),
                    customdata=subset[['z_score', 'articulos']].values,
                    hovertemplate=(
                        '⚠️ <b>Anomalía</b><br>'
                        'Semana: %{x|%d %b %Y}<br>'
                        'Score: %{y:.2f}<br>'
                        'Z-score: %{customdata[0]:.2f}<br>'
                        'Artículos: %{customdata[1]}<extra></extra>'
                    ),
                ))

    fig.add_hline(y=0, line_dash='dot', line_color='gray', opacity=0.4,
                  annotation_text='Neutral', annotation_position='right')
    fig.add_hrect(y0=0,    y1=1.2,  fillcolor='#00a651', opacity=0.04, line_width=0)
    fig.add_hrect(y0=-1.2, y1=0,    fillcolor='#d32f2f', opacity=0.04, line_width=0)
    fig.update_layout(
        title=f'Evolución del sentimiento — {player}',
        yaxis=dict(range=[-1.2, 1.2], title='Score',
                   tickvals=[-1, 0, 1], ticktext=['NEG', 'NEU', 'POS']),
        xaxis_title='',
        height=340,
        margin=dict(t=55, b=20),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
    )
    return fig


def get_top_anomalies(df: pd.DataFrame, n: int = 8,
                      window: int = 6, threshold: float = 1.5) -> pd.DataFrame:
    """Devuelve las N semanas más anómalas del conjunto de jugadores activos."""
    parts = []
    for player in df['player'].unique():
        anom = detect_anomalies(df, player, window, threshold)
        if not anom.empty:
            anom = anom.copy()
            anom['player'] = player
            anom['team']   = df.loc[df['player'] == player, 'team'].iloc[0]
            parts.append(anom)

    if not parts:
        return pd.DataFrame()

    combined = pd.concat(parts, ignore_index=True)
    combined = combined.iloc[combined['z_score'].abs().argsort()[::-1]]
    return combined.head(n).reset_index(drop=True)


def load_hero_stats() -> dict:
    """Carga las métricas globales para el hero del dashboard."""
    try:
        from sqlalchemy import distinct
        with Session(db.engine) as session:
            return {
                "articulos": session.scalar(select(func.count()).select_from(db.ArticleRow)) or 0,
                "equipos":   session.scalar(select(func.count(distinct(db.PlayerRow.club))).select_from(db.PlayerRow)) or 0,
                "jugadores": session.scalar(select(func.count()).select_from(db.PlayerRow)) or 0,
                "clasificados": session.scalar(
                    select(func.count()).select_from(db.ArticleRow)
                    .where(db.ArticleRow.sentiment_label.is_not(None))
                ) or 0,
            }
    except Exception:
        return {"articulos": 0, "equipos": 0, "jugadores": 0, "clasificados": 0}


def main():
    # ============================================================
    # CSS — fuente de marca + estilos globales
    # ============================================================
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Oswald:wght@700&display=swap');
.sesgo-title {
    font-family: 'Oswald', sans-serif;
    font-size: 3.8rem;
    font-weight: 700;
    letter-spacing: -1px;
    line-height: 1;
    text-transform: uppercase;
}
.sesgo-accent { color: #d32f2f; }
.sesgo-sidebar-brand {
    font-family: 'Oswald', sans-serif;
    font-size: 1.55rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    line-height: 1.15;
}
</style>
""", unsafe_allow_html=True)

    # ============================================================
    # SIDEBAR — branding + filtros
    # ============================================================
    with st.sidebar:
        st.markdown("""
<div style="text-align:center; padding:1.2rem 0 1rem 0;">
  <div style="font-size:3rem; line-height:1;">⚽</div>
  <div class="sesgo-sidebar-brand" style="margin-top:0.5rem;">
    El Sesgo<br><span class="sesgo-accent">del Fútbol</span>
  </div>
  <div style="font-size:0.68rem; opacity:0.45; margin-top:0.5rem;
              letter-spacing:0.12em; text-transform:uppercase;">
    Análisis de sentimiento
  </div>
</div>
""", unsafe_allow_html=True)

        # Logos de LaLiga y Marca
        brand_col1, brand_col2 = st.columns(2)
        with brand_col1:
            st.markdown(
                f'<div style="text-align:center; padding:4px 0;">'
                f'<img src="{LALIGA_LOGO_URL}" style="height:36px; object-fit:contain;" '
                f'title="LaLiga" onerror="this.style.display=\'none\'">'
                f'<div style="font-size:0.6rem; opacity:0.4; margin-top:2px;">DATOS</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with brand_col2:
            st.markdown(
                f'<div style="text-align:center; padding:4px 0;">'
                f'<img src="{MARCA_LOGO_URL}" style="height:36px; object-fit:contain;" '
                f'title="Marca" onerror="this.style.display=\'none\'">'
                f'<div style="font-size:0.6rem; opacity:0.4; margin-top:2px;">FUENTE</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        st.divider()

        date_filter = st.selectbox(
            "📅 Periodo de análisis",
            ["Todo el tiempo", "Últimos 7 días", "Últimos 30 días", "Custom"],
            index=0,
        )
        start_date = None
        end_date = None
        if date_filter == "Últimos 7 días":
            start_date = datetime.now() - timedelta(days=7)
        elif date_filter == "Últimos 30 días":
            start_date = datetime.now() - timedelta(days=30)
        elif date_filter == "Custom":
            start_date = st.date_input("Desde", value=datetime.now() - timedelta(days=30))
            end_date   = st.date_input("Hasta", value=datetime.now())

    # ============================================================
    # HERO
    # ============================================================
    stats = load_hero_stats()

    st.markdown("""
<div style="text-align:center; padding:2.5rem 1rem 1rem 1rem;">
  <h1 class="sesgo-title">
    El Sesgo <span class="sesgo-accent">del Fútbol</span>
  </h1>
  <p style="font-size:1.15rem; opacity:0.65; max-width:620px; margin:0.8rem auto 1.5rem auto;
            letter-spacing:0.01em;">
    La prensa tiene opinión. <strong>Los datos la revelan.</strong><br>
    Scraping diario de Marca.com · IA de análisis de sentimiento · La Liga completa
  </p>
</div>
""", unsafe_allow_html=True)

    # Pipeline visual
    st.markdown("""
<div style="display:flex; justify-content:center; align-items:center;
            gap:0.6rem; padding:1.5rem 1rem; background:rgba(128,128,128,0.08);
            border-radius:14px; margin:0 0 1.5rem 0; flex-wrap:wrap;">

  <div style="text-align:center; padding:1rem 1.4rem; background:rgba(128,128,128,0.1);
              border-radius:10px; min-width:110px;">
    <div style="font-size:2rem;">📰</div>
    <div style="font-weight:700; font-size:0.95rem; margin-top:0.4rem;">Scraping</div>
    <div style="opacity:0.55; font-size:0.78rem;">Marca.com RSS</div>
  </div>

  <div style="font-size:1.6rem; opacity:0.35; font-weight:300;">→</div>

  <div style="text-align:center; padding:1rem 1.4rem; background:rgba(128,128,128,0.1);
              border-radius:10px; min-width:110px;">
    <div style="font-size:2rem;">🤖</div>
    <div style="font-weight:700; font-size:0.95rem; margin-top:0.4rem;">IA Sentiment</div>
    <div style="opacity:0.55; font-size:0.78rem;">RoBERTuito NLP</div>
  </div>

  <div style="font-size:1.6rem; opacity:0.35; font-weight:300;">→</div>

  <div style="text-align:center; padding:1rem 1.4rem; background:rgba(128,128,128,0.1);
              border-radius:10px; min-width:110px;">
    <div style="font-size:2rem;">🗄️</div>
    <div style="font-weight:700; font-size:0.95rem; margin-top:0.4rem;">Base de datos</div>
    <div style="opacity:0.55; font-size:0.78rem;">PostgreSQL</div>
  </div>

  <div style="font-size:1.6rem; opacity:0.35; font-weight:300;">→</div>

  <div style="text-align:center; padding:1rem 1.4rem; background:rgba(128,128,128,0.1);
              border-radius:10px; min-width:110px;">
    <div style="font-size:2rem;">📊</div>
    <div style="font-weight:700; font-size:0.95rem; margin-top:0.4rem;">Dashboard</div>
    <div style="opacity:0.55; font-size:0.78rem;">Streamlit</div>
  </div>

</div>
""", unsafe_allow_html=True)

    # Métricas globales
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📰 Artículos analizados", f"{stats['articulos']:,}".replace(",", "."))
    c2.metric("🏟️ Equipos de La Liga",   stats['equipos'])
    c3.metric("👤 Jugadores monitorizados", stats['jugadores'])
    c4.metric("🤖 Articulos clasificados con IA",  f"{stats['clasificados']:,}".replace(",", "."))

    # Badges de stack y despliegue
    st.markdown("""
<div style="display:flex; gap:0.5rem; flex-wrap:wrap; margin:1rem 0 0.5rem 0; justify-content:center;">
  <span style="background:#FF4B4B; color:white; padding:4px 12px; border-radius:20px; font-size:0.8rem; font-weight:600;">Streamlit</span>
  <span style="background:#3776AB; color:white; padding:4px 12px; border-radius:20px; font-size:0.8rem; font-weight:600;">Python</span>
  <span style="background:#336791; color:white; padding:4px 12px; border-radius:20px; font-size:0.8rem; font-weight:600;">PostgreSQL</span>
  <span style="background:#D4380D; color:white; padding:4px 12px; border-radius:20px; font-size:0.8rem; font-weight:600;">SQLAlchemy</span>
  <span style="background:#FF6F00; color:white; padding:4px 12px; border-radius:20px; font-size:0.8rem; font-weight:600;">HuggingFace 🤗</span>
  <span style="background:#2496ED; color:white; padding:4px 12px; border-radius:20px; font-size:0.8rem; font-weight:600;">🐳 Docker</span>
  <span style="background:#232F3E; color:white; padding:4px 12px; border-radius:20px; font-size:0.8rem; font-weight:600;">☁️ AWS</span>
</div>
""", unsafe_allow_html=True)

    st.markdown("---")

    # Cargar datos con el filtro de fecha de la sidebar
    df = load_articles(start_date, end_date)

    if df.empty:
        st.error("No hay artículos en el periodo seleccionado.")
        return

    # Filtro de equipos en la sidebar (necesita df ya cargado)
    with st.sidebar:
        st.divider()
        available_teams = sorted(df['team'].unique())
        if len(available_teams) > 1:
            selected_teams = st.multiselect(
                "🏟️ Equipos",
                available_teams,
                default=["Real Madrid", "FC Barcelona", "Atlético de Madrid"],
            )
            if selected_teams:
                df = df[df['team'].isin(selected_teams)]

        st.divider()
        st.markdown("""
<div style="font-size:0.72rem; opacity:0.4; text-align:center; padding:0.5rem 0;">
  Hecho por <strong>Diego Cainzos</strong><br>
  <a href="https://diegocainzos.cv" target="_blank"
     style="color:inherit;">diegocainzos.cv</a>
</div>
""", unsafe_allow_html=True)

    if df.empty:
        st.warning("No hay artículos para los equipos seleccionados.")
        return
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Artículos", len(df))
    
    with col2:
        positive_pct = (df['sentiment_label'] == 'POS').sum() / len(df) * 100
        st.metric("% Positivo", f"{positive_pct:.1f}%")
    
    with col3:
        negative_pct = (df['sentiment_label'] == 'NEG').sum() / len(df) * 100
        st.metric("% Negativo", f"{negative_pct:.1f}%")
    
    with col4:
        neutral_pct = (df['sentiment_label'] == 'NEU').sum() / len(df) * 100
        st.metric("% Neutral", f"{neutral_pct:.1f}%")
    
    st.markdown("---")

    # ============================================================
    # SECCIÓN 2: RANKING COMPARATIVO DE EQUIPOS
    # ============================================================
    teams_in_data = sorted(df['team'].unique())
    if len(teams_in_data) > 1:
        st.header("🏅 Ranking Comparativo de Equipos")

        team_rankings = calculate_team_rankings(df)

        # ── Dos gráficos en paralelo ──────────────────────────────
        rank_col1, rank_col2 = st.columns(2)
        with rank_col1:
            st.plotly_chart(plot_coverage_ranking(team_rankings), use_container_width=True)
        with rank_col2:
            st.plotly_chart(plot_positivity_ranking(team_rankings), use_container_width=True)

        # ── Filtro de fecha en el contexto del ranking ─────────────
        st.caption(
            "💡 Ajusta el **Periodo de análisis** en la barra lateral para que el ranking sea dinámico."
        )

        # ── Tabla detallada con logos ──────────────────────────────
        st.subheader("📋 Tabla Detallada")

        display_df = (
            team_rankings[['logo', 'team', 'total_articles', 'positivity_index', 'mean_score',
                            'pos_count', 'neu_count', 'neg_count']]
            .rename(columns={
                'logo':             'Escudo',
                'team':             'Equipo',
                'total_articles':   'Artículos',
                'positivity_index': 'Positividad (%)',
                'mean_score':       'Score Medio',
                'pos_count':        'POS',
                'neu_count':        'NEU',
                'neg_count':        'NEG',
            })
            .sort_values('Positividad (%)', ascending=False)
            .reset_index(drop=True)
        )

        st.dataframe(
            display_df,
            column_config={
                "Escudo": st.column_config.ImageColumn(
                    "", width="small",
                    help="Logo del club (ESPN CDN)",
                ),
                "Equipo":          st.column_config.TextColumn("Equipo"),
                "Artículos":       st.column_config.NumberColumn("Artículos", format="%d"),
                "Positividad (%)": st.column_config.NumberColumn("Positividad (%)", format="%.1f"),
                "Score Medio":     st.column_config.NumberColumn("Score", format="%.3f",
                                   help="Media de POS→1, NEU→0, NEG→−1"),
                "POS": st.column_config.NumberColumn("✅ POS", format="%d"),
                "NEU": st.column_config.NumberColumn("⬜ NEU", format="%d"),
                "NEG": st.column_config.NumberColumn("❌ NEG", format="%d"),
            },
            hide_index=True,
            use_container_width=True,
        )
        st.markdown("---")

    # ============================================================
    # SECCIÓN 3: COMPARATIVA GENERAL
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
    st.plotly_chart(plot_ranking(player_stats), width="stretch")
    
    # Heatmap de distribución
    st.plotly_chart(plot_sentiment_distribution(df), width="stretch")
    
    st.markdown("---")

    # ============================================================
    # SECCIÓN 3b: COMPARATIVA JUGADOR VS JUGADOR
    # ============================================================
    st.header("🆚 Comparativa de Jugadores")

    all_players = sorted(df['player'].unique())
    cmp_col1, cmp_col2 = st.columns(2)
    with cmp_col1:
        cmp_player1 = st.selectbox(
            "Jugador A", all_players,
            index=0, key="cmp_p1",
        )
    with cmp_col2:
        default_p2 = all_players[1] if len(all_players) > 1 else all_players[0]
        cmp_player2 = st.selectbox(
            "Jugador B", all_players,
            index=all_players.index(default_p2), key="cmp_p2",
        )

    if cmp_player1 == cmp_player2:
        st.info("Selecciona dos jugadores distintos para comparar.")
    else:
        # Gráfico de evolución compartido
        st.plotly_chart(
            plot_player_comparison(df, cmp_player1, cmp_player2),
            use_container_width=True,
        )

        # Métricas cara a cara
        m_col1, m_col2 = st.columns(2)
        for col, player in [(m_col1, cmp_player1), (m_col2, cmp_player2)]:
            pdf = df[df['player'] == player]
            score = pdf['sentiment_label'].map(SENTIMENT_SCORES).mean()
            pos_pct = (pdf['sentiment_label'] == 'POS').mean() * 100
            neg_pct = (pdf['sentiment_label'] == 'NEG').mean() * 100
            team    = pdf['team'].iloc[0]
            logo_url = TEAM_LOGOS.get(team, '')
            with col:
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">'
                    f'<img src="{logo_url}" style="height:28px;object-fit:contain;" '
                    f'onerror="this.style.display=\'none\'">'
                    f'<strong style="font-size:1.05rem;">{player}</strong>'
                    f'<span style="opacity:0.5;font-size:0.85rem;">({team})</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                mc1, mc2, mc3 = st.columns(3)
                mc1.metric("Score",    f"{score:.2f}")
                mc2.metric("% POS",    f"{pos_pct:.0f}%")
                mc3.metric("% NEG",    f"{neg_pct:.0f}%")

    st.markdown("---")

    # ============================================================
    # SECCIÓN 3c: ALERTAS EDITORIALES (anomalías globales)
    # ============================================================
    st.header("🚨 Alertas Editoriales")
    st.caption(
        "Semanas con cambios de tono estadísticamente inusuales para cada jugador "
        "(z-score rolling ≥ 1.5 sobre ventana de 6 semanas)."
    )

    top_anom = get_top_anomalies(df, n=10)

    if top_anom.empty:
        st.info("No hay anomalías detectadas con los datos y filtros actuales.")
    else:
        anom_display = top_anom.copy()
        anom_display['logo'] = anom_display['team'].map(TEAM_LOGOS)
        anom_display['semana_str'] = anom_display['semana'].dt.strftime('Sem. %d %b %Y')
        anom_display['tipo'] = anom_display['direction'].map(
            {'positiva': '🟢 Pico positivo', 'negativa': '🔴 Pico negativo'}
        )
        anom_display['z_abs'] = anom_display['z_score'].abs().round(2)

        st.dataframe(
            anom_display[['logo', 'player', 'team', 'semana_str', 'tipo', 'score', 'z_abs', 'articulos']],
            column_config={
                "logo":       st.column_config.ImageColumn("", width="small"),
                "player":     st.column_config.TextColumn("Jugador"),
                "team":       st.column_config.TextColumn("Equipo"),
                "semana_str": st.column_config.TextColumn("Semana"),
                "tipo":       st.column_config.TextColumn("Tipo"),
                "score":      st.column_config.NumberColumn("Score", format="%.2f"),
                "z_abs":      st.column_config.NumberColumn("Intensidad (z)", format="%.2f",
                              help="Cuántas desviaciones estándar sobre la media reciente"),
                "articulos":  st.column_config.NumberColumn("Arts.", format="%d"),
            },
            hide_index=True,
            use_container_width=True,
        )

    st.markdown("---")

    # ============================================================
    # SECCIÓN 4: ANÁLISIS INDIVIDUAL
    # ============================================================
    st.header("🔍 Análisis Individual")

    # Player selector is scoped to the teams currently selected above
    selected_player = st.selectbox(
        "Selecciona un jugador",
        sorted(df['player'].unique())
    )

    player_df = df[df['player'] == selected_player]
    avg_score  = player_df['sentiment_label'].map(SENTIMENT_SCORES).mean()
    player_team = player_df['team'].iloc[0] if not player_df.empty else ""
    team_avg   = df[df['team'] == player_team]['sentiment_label'].map(SENTIMENT_SCORES).mean()
    delta      = avg_score - team_avg

    # Fila de métricas
    m1, m2, m3 = st.columns(3)
    m1.metric("Score del jugador",    f"{avg_score:.2f}")
    m2.metric("Total artículos",       len(player_df))
    m3.metric("vs. media del equipo",  f"{team_avg:.2f}", delta=f"{delta:+.2f}",
              delta_color="normal")

    # Evolución temporal con anomalías marcadas — ancho completo
    st.plotly_chart(plot_anomaly_timeline(df, selected_player), use_container_width=True)

    # Anomalías específicas del jugador seleccionado
    player_anomalies = detect_anomalies(df, selected_player)
    if not player_anomalies.empty:
        with st.expander(f"⚠️ {len(player_anomalies)} semanas anómalas detectadas para {selected_player}", expanded=False):
            anom_fmt = player_anomalies.copy()
            anom_fmt['semana'] = anom_fmt['semana'].dt.strftime('%d %b %Y')
            anom_fmt['tipo']   = anom_fmt['direction'].map(
                {'positiva': '🟢 Pico positivo', 'negativa': '🔴 Pico negativo'}
            )
            st.dataframe(
                anom_fmt[['semana', 'tipo', 'score', 'z_score', 'articulos']]
                .rename(columns={'semana': 'Semana', 'tipo': 'Tipo',
                                 'score': 'Score', 'z_score': 'Z-score', 'articulos': 'Arts.'}),
                hide_index=True, use_container_width=True,
            )

    # Comparativa equipo + artículos recientes
    col1, col2 = st.columns([1, 2])

    with col1:
        st.plotly_chart(plot_player_vs_team(df, selected_player), width="stretch")

    with col2:
        st.subheader(f"📰 Artículos Recientes - {selected_player}")

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

    # ============================================================
    # SECCIÓN FINAL: PIE CHARTS POR EQUIPO
    # ============================================================
    st.markdown("---")
    st.header("🥧 Distribución de Sentimiento por Equipo")

    pie_cols = st.columns(min(len(teams_in_data), 3))
    for i, team in enumerate(teams_in_data):
        with pie_cols[i % len(pie_cols)]:
            st.plotly_chart(plot_team_pie(df, team), width="stretch")

    # ============================================================
    # SOBRE ESTE PROYECTO
    # ============================================================
    st.markdown("---")
    with st.expander("📖 Sobre este proyecto", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
### ¿Qué hace esta herramienta?

Monitoriza en tiempo real el tono con el que la prensa deportiva española
cubre a los jugadores de la Liga española.

Cada vez que se actualiza, el sistema:
1. **Extrae** los artículos más recientes de las RSS de Marca.com para cada jugador
2. **Clasifica** automáticamente cada artículo como Positivo, Negativo o Neutral
   usando un modelo de inteligencia artificial entrenado en español
3. **Almacena** los resultados en una base de datos para su análisis histórico
4. **Visualiza** las tendencias en este dashboard interactivo

El resultado es un termómetro del sentimiento mediático: ¿a quién trata bien
la prensa? ¿Quién está en el punto de mira?

---

### 🛠️ Stack técnico

| Capa | Tecnología |
|---|---|
| Extracción de datos | `feedparser` (RSS) |
| Análisis de sentimiento | `pysentimiento/robertuito` (BERT en español) |
| Base de datos | SQLite / PostgreSQL |
| ORM | SQLAlchemy 2.0 |
| Dashboard | Streamlit + Plotly |
| Gestión de entornos | `uv` |
""")

        with col2:
            st.markdown("""
### 💡 Lo que aprendí construyendo esto

**Datos y pipelines**
- Cómo construir un pipeline ETL completo desde cero: extracción, transformación y carga
- Deduplicación de datos con SHA1 para evitar artículos repetidos
- Procesamiento en batches para no saturar el modelo de NLP

**Bases de datos**
- Diseño de esquema relacional con claves foráneas
- ORM con SQLAlchemy: modelos, relaciones, migraciones
- La diferencia entre SQLite (local) y PostgreSQL (producción)
- SQL puro vs ORM: cuándo usar cada uno

**Machine Learning aplicado**
- Uso de modelos preentrenados de HuggingFace sin necesidad de entrenar desde cero
- Las limitaciones reales de los modelos: el sarcasmo, el contexto deportivo,
  los titulares ambiguos

**Ingeniería de software**
- Separación de responsabilidades en capas independientes
- Configuración externalizada (TOML) para escalar sin tocar código
- Escritura de migraciones de base de datos idempotentes

---

### 👨‍💻 Autor

Proyecto personal de **Diego Cainzos** — construido como ejercicio práctico
de ingeniería de datos y desarrollo de producto.

[diegocainzos.cv](https://diegocainzos.cv)
""")


if __name__ == "__main__":
    main()
