#!/bin/bash
# Script para actualizar la base de datos con nuevos artículos
# Ejecuta el pipeline completo: fetch RSS + análisis NLP

set -e  # Salir si hay algún error

#cd "$(dirname "$0")"

echo "════════════════════════════════════════════════════════════"
echo "🔄 ACTUALIZANDO BASE DE DATOS"
echo "════════════════════════════════════════════════════════════"
echo ""

# Paso 1: Extraer nuevos artículos
echo "📥 PASO 1/2: Extrayendo artículos de RSS..."
echo ""
cd data_pipeline
uv run main.py

echo ""
echo "─────────────────────────────────────────────────────────────"
echo ""

# Paso 2: Analizar sentimiento de artículos nuevos
echo "🔮 PASO 2/2: Analizando sentimiento..."
echo ""
cd ../sentiment_analysis
uv run label-data.py

echo ""
echo "════════════════════════════════════════════════════════════"
echo "✅ ACTUALIZACIÓN COMPLETADA"
echo "════════════════════════════════════════════════════════════"
echo ""

# Mostrar estadísticas finales
cd ../data_pipeline
uv run python3 << 'PYSTATS'
import db
from sqlalchemy import func, select
from sqlalchemy.orm import Session

with Session(db.engine) as s:
    total = s.scalar(select(func.count()).select_from(db.ArticleRow))
    with_sentiment = s.scalar(
        select(func.count())
        .select_from(db.ArticleRow)
        .where(db.ArticleRow.sentiment_label.is_not(None))
    )
    without_sentiment = total - with_sentiment
    
    print(f"📊 Total artículos en DB:     {total}")
    print(f"   ✅ Con sentimiento:         {with_sentiment}")
    if without_sentiment > 0:
        print(f"   ⚠️  Sin sentimiento:        {without_sentiment}")
    print()
    
    # Distribución de sentimiento
    results = s.execute(
        select(db.ArticleRow.sentiment_label, func.count())
        .where(db.ArticleRow.sentiment_label.is_not(None))
        .group_by(db.ArticleRow.sentiment_label)
    ).all()
    
    print("📈 Distribución:")
    label_order = ['VERY POSITIVE', 'POSITIVE', 'NEUTRAL', 'UNDEFINED', 'NEGATIVE', 'VERY NEGATIVE']
    results_dict = {label: count for label, count in results}
    
    for label in label_order:
        if label in results_dict:
            count = results_dict[label]
            pct = (count / with_sentiment * 100) if with_sentiment > 0 else 0
            emoji = "🟢" if "POSITIVE" in label else "🔴" if "NEGATIVE" in label else "⚪"
            print(f"   {emoji} {label:15} {count:3} ({pct:.1f}%)")
PYSTATS

echo ""
echo "💡 Si el dashboard está corriendo, refresca la página para ver los cambios."
echo ""
