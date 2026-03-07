# ⚽ Football Sentiment Intelligence

Análisis automático del sentimiento de la prensa deportiva española sobre jugadores del Real Madrid.

---

## 🚀 Inicio Rápido

```bash
# Ver el dashboard
./run_dashboard.sh
# Abre: http://localhost:8501

# Actualizar datos (añadir nuevos artículos)
./update_data.sh

# Ver estadísticas en consola
cd data_pipeline && uv run view_db.py
```

---

## 📊 Estado Actual

```
✅ 512 artículos analizados
✅ 21 jugadores del Real Madrid
✅ 100% con análisis de sentimiento
✅ Dashboard interactivo funcionando
```

---

## 🔄 Pipeline de Datos

```
RSS Marca → Extracción (main.py) → SQLite (articles.db)
                ↓
         Deduplicación automática
                ↓
    BETO NLP (label-data.py) → Sentimiento (6 categorías)
                ↓
         Dashboard (Streamlit) → Visualización
```

---

## 📂 Estructura del Proyecto

```
elsesgodelfutbol/
├── data_pipeline/          # Extracción de artículos RSS
│   ├── main.py            # Script principal de extracción
│   ├── db.py              # Capa de base de datos (SQLAlchemy)
│   └── view_db.py         # Visualizador de estadísticas
│
├── sentiment_analysis/     # Análisis NLP
│   └── label-data.py      # Clasificación con BETO (BERT español)
│
├── dashboard/              # Visualización Streamlit
│   ├── app.py             # Dashboard interactivo
│   └── README.md          # Documentación del dashboard
│
├── data/                   # Base de datos SQLite
│   └── articles.db        # 512 artículos con sentimiento
│
├── update_data.sh          # ⭐ Script de actualización
├── run_dashboard.sh        # ⭐ Lanzador del dashboard
└── ACTUALIZACION.md        # Guía de actualización
```

---

## 📊 Tecnologías

| Capa | Tecnología |
|---|---|
| **Scraping** | `feedparser` (RSS) |
| **NLP** | BETO `ignacio-ave/beto-sentiment-analysis-spanish` |
| **Database** | SQLite + SQLAlchemy |
| **Dashboard** | Streamlit + Plotly |
| **Deployment** | Python 3.13 + uv |

---

## 🎯 Características del Dashboard

- ✅ Filtros por fecha (7d, 30d, custom)
- ✅ Ranking de jugadores por sentimiento
- ✅ Heatmap de distribución
- ✅ Análisis individual con pie charts
- ✅ Lista de artículos con links a Marca

---

## 🛠️ Comandos Útiles

```bash
# Dashboard
./run_dashboard.sh                    # Lanzar
kill $(ps aux | grep streamlit | grep -v grep | awk '{print $2}')  # Detener

# Actualización de datos
./update_data.sh                      # Pipeline completo automático

# Consultas SQL directas
sqlite3 data/articles.db \
  "SELECT player, COUNT(*) FROM articles GROUP BY player;"

# Ver estadísticas
cd data_pipeline && uv run view_db.py
```

---

## 📝 Limitaciones Conocidas

1. **RSS limitado**: Marca publica solo ~30 artículos recientes por jugador
2. **Sarcasmo/ironía**: El modelo NLP no los detecta perfectamente
3. **Concurrencia**: Cerrar dashboard antes de ejecutar `update_data.sh`

---

## 📚 Documentación

- [dashboard/README.md](dashboard/README.md) - Guía del dashboard
- [ACTUALIZACION.md](ACTUALIZACION.md) - Cómo actualizar datos manualmente
- [plan.md](plan.md) - Plan original del proyecto

---

**Desarrollado por:** Diego  
**Tecnología:** Python + NLP + Streamlit  
**Datos:** Marca.com (RSS público)
