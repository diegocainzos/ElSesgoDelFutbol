"""
Script de análisis de sentimiento usando HuggingFace transformers.
Procesa todos los artículos sin sentimiento y los guarda en la DB.
"""

import sys
from pathlib import Path

# Añadir data_pipeline al path para importar db
sys.path.insert(0, str(Path(__file__).parent.parent / "data_pipeline"))

import db
from transformers import pipeline


# Modelo de sentimiento español RoBERTuito con 3 categorías
MODEL_NAME = "pysentimiento/robertuito-sentiment-analysis"


def analyze_articles_batch(articles: list[db.ArticleRow], batch_size: int = 32) -> list[tuple[str, str, float]]:
    """
    Analiza una lista de artículos y devuelve los resultados.
    Returns: lista de (article_id, label, score)
    
    Labels posibles del modelo:
    - POS (Positivo)
    - NEU (Neutral)
    - NEG (Negativo)
    """
    print(f"🔮 Cargando modelo: {MODEL_NAME}")
    classifier = pipeline('sentiment-analysis', model=MODEL_NAME, device=-1)  # CPU
    
    # Preparar textos: título + summary
    texts = []
    article_ids = []
    
    for article in articles:
        text = article.title
        if article.summary:
            text += ". " + article.summary
        texts.append(text[:512])  # Truncar a 512 caracteres (límite BERT)
        article_ids.append(article.id)
    
    print(f"📊 Analizando {len(texts)} artículos...")
    
    # Procesar en batches
    results = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        batch_ids = article_ids[i:i + batch_size]
        
        predictions = classifier(batch, truncation=True, max_length=128)
        
        for article_id, pred in zip(batch_ids, predictions):
            label = pred['label']
            score = pred['score']
            
            results.append((article_id, label, score))
        
        print(f"  Procesados {min(i + batch_size, len(texts))}/{len(texts)}")
    
    return results


def main():
    """Procesa todos los artículos sin sentimiento."""
    db.init_db()
    
    articles = db.get_articles_without_sentiment()
    
    if not articles:
        print("✅ Todos los artículos ya tienen sentimiento analizado.")
        return
    
    print(f"📰 Encontrados {len(articles)} artículos sin sentimiento.")
    print()
    
    # Analizar
    results = analyze_articles_batch(articles)
    
    # Guardar en DB
    print("\n💾 Guardando resultados...")
    updated = db.save_sentiments_batch(results)
    
    print(f"✅ Actualizado sentimiento de {updated} artículos.")
    
    # Mostrar ejemplo de resultados
    print("\n📊 Ejemplo de resultados:")
    for article_id, label, score in results[:5]:
        article = next(a for a in articles if a.id == article_id)
        print(f"\n  [{article.player}] {article.title[:60]}...")
        print(f"  → {label} (score: {score:.2f})")


if __name__ == "__main__":
    main()
