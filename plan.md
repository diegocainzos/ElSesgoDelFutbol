# Football Sentiment Intelligence
### Análisis de Sentimiento de Prensa Deportiva con NLP

---

## Descripción

Pipeline automatizado que extrae noticias de fútbol de medios españoles,
analiza el sentimiento por jugador y equipo usando NLP, y lo visualiza
en un dashboard interactivo. El objetivo es responder preguntas como:
¿Cómo habla Marca de Vinicius esta temporada? ¿Ha cambiado el tono
tras el último partido?

---

## Problema que resuelve

Los clubes, agencias de comunicación y periodistas no tienen forma
rápida de monitorizar cómo la prensa trata a sus jugadores a lo largo
del tiempo. Este proyecto lo automatiza y lo hace visual.

---

## Stack Tecnológico

| Capa | Tecnología | Justificación |
|---|---|---|
| Scraping | `feedparser` + `BeautifulSoup` | RSS de Marca, sin coste |
| NLP Sentimiento | `pysentimiento` (HuggingFace) | Modelo entrenado en español |
| NER Jugadores | `spaCy` es_core_news_lg | Extracción automática de nombres |
| Base de datos | `PostgreSQL` | Historial persistente de artículos |
| Dashboard | `Streamlit` | Rápido, pythónico, visual |
| Despliegue | `Docker` + `HuggingFace Spaces` | Gratuito, público, en producción |
| Scheduler | `APScheduler` | Actualización automática cada 6h |

---

## Arquitectura

```
RSS Marca
    ↓
feedparser → artículos crudos
    ↓
spaCy NER → extrae jugadores mencionados
    ↓
pysentimiento → puntuación POS/NEG/NEU por párrafo
    ↓
PostgreSQL → almacena artículo + jugadores + scores
    ↓
Streamlit Dashboard → visualización interactiva
```

---

## Fases de Desarrollo

### Fase 1 — MVP Funcional
- [ ] Scraping RSS de Marca con `feedparser`
- [ ] Limpieza y parseo de artículos
- [ ] NER con spaCy — extracción automática de jugadores
- [ ] Análisis de sentimiento con `pysentimiento`
- [ ] Almacenamiento en PostgreSQL
- [ ] Script de ingestión manual funcional

**Criterio de éxito:** Pipeline corre de principio a fin con datos reales.

### Fase 2 — Dashboard
- [ ] Selector de equipo y jugador
- [ ] Gráfico de evolución de sentimiento en el tiempo
- [ ] Listado de artículos recientes con score
- [ ] Métricas agregadas: sentimiento medio, artículos positivos vs negativos
- [ ] Vista de resumen por equipo

**Criterio de éxito:** Demo navegable en local con datos de 2 semanas.

### Fase 3 — Producción y Portfolio
- [ ] Dockerizar todo el stack
- [ ] Desplegar en HuggingFace Spaces
- [ ] README profesional con capturas y GIF demo
- [ ] Scheduler automático cada 6 horas
- [ ] Documentación de limitaciones honestas (ironía, sarcasmo)

**Criterio de éxito:** URL pública funcional. Añadido al CV y LinkedIn.

---

## Mejoras Futuras (v2)

- Comparativa entre Marca y AS sobre el mismo jugador
- Evolución del sentimiento durante una temporada completa
- Alertas automáticas cuando el sentimiento cambia bruscamente
- Análisis de sesgo editorial por medio
- Versión multiidioma: inglés (BBC Sport), francés (L'Équipe)
- API REST para que terceros consuman los datos

---

## Limitaciones Conocidas (documentar honestamente)

- El sarcasmo y la ironía en prensa deportiva genera falsos positivos
- El scraping puede ser bloqueado — respetar `robots.txt` y añadir delays
- `pysentimiento` no está entrenado específicamente en lenguaje deportivo

---

## Valor Empresarial

| Cliente potencial | Uso |
|---|---|
| Clubes de fútbol | Monitorizar imagen de jugadores en prensa |
| Agencias de comunicación deportiva | Informes automatizados para clientes |
| Medios deportivos | Análisis de su propio tono editorial |
| Plataformas de fantasy football | Señales de sentimiento como feature |

---

## Nombre del repositorio

`football-sentiment-intelligence`

---

## Orden de ejecución

1. Terminar procesos de selección activos (Inditex, BIP)
2. Montar entorno y scraping básico — Fase 1
3. Dashboard mínimo navegable — Fase 2
4. Despliegue y portfolio — Fase 3

