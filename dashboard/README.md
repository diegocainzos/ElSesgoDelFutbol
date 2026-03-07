# 📊 Dashboard de Sentimiento - Real Madrid

Dashboard interactivo para analizar el sentimiento de la prensa deportiva sobre jugadores del Real Madrid.

## 🚀 Lanzar el Dashboard

```bash
./run_dashboard.sh
```

O manualmente:
```bash
uv run streamlit run dashboard/app.py
```

El dashboard estará disponible en: **http://localhost:8501**

## 📋 Funcionalidades

### 1️⃣ Filtros por Fecha
- Todo el tiempo
- Últimos 7 días
- Últimos 30 días
- Custom (selecciona rango específico)

### 2️⃣ Comparativa General
- **Ranking**: Jugadores ordenados por score de sentimiento (-2 a +2)
- **Top 3 / Bottom 3**: Mejor y peor tratados por la prensa
- **Heatmap**: Distribución porcentual de cada tipo de sentimiento por jugador

### 3️⃣ Análisis Individual
- Selecciona un jugador del dropdown
- Ver score promedio y distribución de sentimiento (pie chart)
- Lista de artículos recientes con:
  - Título
  - Fecha de publicación
  - Label de sentimiento (color-coded)
  - Score de confianza
  - Link al artículo original

## 🎨 Labels de Sentimiento

| Label | Color | Score |
|---|---|---|
| 🟢 VERY POSITIVE | Verde oscuro | +2 |
| 🟢 POSITIVE | Verde claro | +1 |
| ⚪ NEUTRAL | Gris | 0 |
| 🟠 UNDEFINED | Naranja | 0 |
| 🔴 NEGATIVE | Rojo claro | -1 |
| 🔴 VERY NEGATIVE | Rojo oscuro | -2 |

## 🛑 Detener el Dashboard

```bash
# Si lo lanzaste con el script
pkill -f "streamlit run dashboard/app.py"

# O si guardaste el PID
kill $(cat /tmp/streamlit_dashboard.pid)
```

## 📊 Datos

El dashboard lee directamente de `data/articles.db` que contiene:
- 188 artículos de 21 jugadores del Real Madrid
- Análisis de sentimiento con modelo BETO (BERT español)
- Actualización mediante `data_pipeline/main.py` + `sentiment_analysis/label-data.py`

## 🔄 Actualizar Datos

1. Fetch nuevos artículos:
   ```bash
   cd data_pipeline && uv run main.py
   ```

2. Analizar sentimiento:
   ```bash
   cd sentiment_analysis && uv run label-data.py
   ```

3. El dashboard se actualizará automáticamente (refresca la página)
