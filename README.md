<div align="center">
  <div style="display: flex; justify-content: center; align-items: center; gap: 40px; margin-bottom: 20px;">
    <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/0/0f/LaLiga_logo_2023.svg/960px-LaLiga_logo_2023.svg.png" height="80" alt="LaLiga" />
    <span style="font-size: 40px; color: #d32f2f;">✖</span>
    <img src="https://cdn.freebiesupply.com/logos/large/2x/marca-com-1-logo-png-transparent.png" height="80" alt="Marca" />
  </div>
  
  # 🏆⚽ EL SESGO DEL FÚTBOL 🔥🏟️
  
  *La prensa tiene opinión. Los datos la revelan.*
</div>

---

> *"El sentimiento no se negocia, se calcula."* 🧠⚽

## 📝 Crónica del Partido (Descripción)

Bienvenidos a la transmisión en vivo de **El Sesgo del Fútbol**, una herramienta analítica digna de la sala del VAR. Este proyecto es un *pipeline* de extracción y análisis de sentimiento automatizado que escanea la prensa deportiva española (Marca.com) para descubrir en tiempo real cómo se habla de los jugadores de LaLiga. 

Cada día saltamos al campo para hacer *scraping*, aplicar inteligencia artificial con un modelo BERT entrenado en español, y pintar los resultados en un dashboard interactivo que no deja lugar a dudas. ¿A quién acaricia la prensa? ¿Quién se lleva la tarjeta roja mediática? Aquí están los datos para demostrarlo.

---

## 📋 Alineación Inicial (Tech Stack)

Salimos a la cancha con un 4-3-3 ultra ofensivo, usando las mejores herramientas del mercado:

<div align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit" />
  <img src="https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/SQLAlchemy-D4380D?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLAlchemy" />
  <img src="https://img.shields.io/badge/HuggingFace-FF6F00?style=for-the-badge&logo=huggingface&logoColor=white" alt="HuggingFace" />
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker" />
  <img src="https://img.shields.io/badge/AWS-232F3E?style=for-the-badge&logo=amazon-aws&logoColor=white" alt="AWS" />
</div>

---

## 🌟 El Plantel (Equipos Analizados)

Una muestra de los clubes que están bajo la lupa táctica de nuestro sistema:

| Escudo | Equipo | Escudo | Equipo |
|:---:|:---|:---:|:---|
| <img src="https://a.espncdn.com/i/teamlogos/soccer/500/86.png" width="35"> | **Real Madrid** | <img src="https://a.espncdn.com/i/teamlogos/soccer/500/83.png" width="35"> | **FC Barcelona** |
| <img src="https://a.espncdn.com/i/teamlogos/soccer/500/1068.png" width="35"> | **Atlético de Madrid** | <img src="https://a.espncdn.com/i/teamlogos/soccer/500/102.png" width="35"> | **Villarreal CF** |
| <img src="https://a.espncdn.com/i/teamlogos/soccer/500/94.png" width="35"> | **Valencia CF** | <img src="https://a.espncdn.com/i/teamlogos/soccer/500/243.png" width="35"> | **Sevilla FC** |
| <img src="https://a.espncdn.com/i/teamlogos/soccer/500/93.png" width="35"> | **Athletic Club** | <img src="https://a.espncdn.com/i/teamlogos/soccer/500/89.png" width="35"> | **Real Sociedad** |

---

## 📊 Marcador en Tiempo Real (Features)

Nuestro estadio digital cuenta con las siguientes métricas de alto rendimiento:

*   🟢 **Semáforos de Positividad**: Escalas de colores térmicas en el dashboard para identificar rápidamente si las noticias y el trato son `POS` (Verde), `NEU` (Gris) o `NEG` (Rojo).
*   🏅 **Ranking Comparativo**: Tablas de posiciones de los equipos mejor y peor tratados por la prensa. La liga de los medios.
*   🆚 **Cara a Cara (1v1)**: Gráficos evolutivos para comparar el sentimiento de dos jugadores como si fuera un derbi personal.
*   🚨 **Alertas Editoriales**: Detección de picos anómalos de sentimiento. Si a alguien le están dando palos de más (o flores sospechosas), nuestro cálculo de Z-Score salta al instante.

---

## 🏆 MVP del Análisis

**El Ojo Clínico de la IA 🤖:** 
Nuestro sistema no solo lee, *entiende*. Impulsado por el modelo `pysentimiento/robertuito`, la IA funciona como el mejor scout del equipo, procesando el lenguaje natural, detectando el contexto deportivo y cuantificando el tono con el que se narra la actualidad. 

**Precisión del VAR 🔎:** 
Implementamos una mejora crítica en la última actualización del reglamento. Hemos calibrado los monitores ajustando el cálculo a **2 decimales exactos**. Ahora el *score* es milimétrico, asegurando que ninguna injusticia estadística pase desapercibida. ¡Líneas trazadas, gol validado! 🟥🟦

---

## 🛠️ El VAR del Código (Instalación)

¿Quieres sumarte al cuerpo técnico? Sigue las reglas del juego para levantar el proyecto en tu máquina local. Utilizamos `uv` como nuestro preparador físico principal (Package Manager).

```bash
# 1. Ficha a los jugadores (Instala dependencias con uv)
uv sync

# 2. Salta a calentar (Testea la conexión a la base de datos)
cd data_pipeline && uv run python -c "import db; db.init_db(); print('DB OK')"

# 3. Arranca el partido (Ejecuta el dashboard interactivo)
./scripts/run_dashboard.sh
# 🌐 El estadio virtual abrirá sus puertas en: http://localhost:8501
```

### 🧤 Jugadas de Pizarra (Comandos Útiles)

```bash
# 🔄 Actualización completa (Extraer noticias + Clasificar IA)
./scripts/update_data.sh

# 📰 Solo extraer noticias (El Scout en acción)
cd data_pipeline && uv run main.py

# ⚖️ Solo etiquetar artículos sin clasificar (El Árbitro revisando)
cd sentiment_analysis && uv run label-data.py
```

---

> *"Al final del día, los datos no mienten, aunque los titulares sí lo intenten."* 🏟️🔥

<div align="center">
  <p>Construido con código, sudor y mucha pasión futbolera por <strong>Diego Cainzos</strong>.</p>
  <a href="https://diegocainzos.cv">diegocainzos.cv</a>
</div>
