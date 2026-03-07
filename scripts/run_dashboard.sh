#!/bin/bash
# Script para lanzar el dashboard de Streamlit

cd "$(dirname "$0")"

echo "🚀 Lanzando dashboard de sentimiento..."
echo "📍 URL: http://localhost:8501"
echo ""

uv run streamlit run dashboard/app.py
