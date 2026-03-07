"""
Script para visualizar el contenido de la DB de forma bonita.
Uso: uv run view_db.py
"""

import db
from sqlalchemy import func, select
from sqlalchemy.orm import Session


def main():
    with Session(db.engine) as session:
        # Estadísticas generales
        total = session.scalar(select(func.count()).select_from(db.ArticleRow))
        with_sentiment = session.scalar(
            select(func.count())
            .select_from(db.ArticleRow)
            .where(db.ArticleRow.sentiment_label.is_not(None))
        )
        
        print("=" * 60)
        print(f"📊 ESTADÍSTICAS DE LA BASE DE DATOS")
        print("=" * 60)
        print(f"Total artículos:       {total}")
        print(f"Con sentimiento:       {with_sentiment}")
        print(f"Sin sentimiento:       {total - with_sentiment}")
        print()

        # Artículos por jugador
        print("=" * 60)
        print("👤 ARTÍCULOS POR JUGADOR (Top 10)")
        print("=" * 60)
        
        results = session.execute(
            select(db.ArticleRow.player, func.count().label('total'))
            .group_by(db.ArticleRow.player)
            .order_by(func.count().desc())
            .limit(10)
        ).all()
        
        for player, count in results:
            print(f"{player:20} {count:3} artículos")
        
        print()

        # Últimos artículos
        print("=" * 60)
        print("📰 ÚLTIMOS 5 ARTÍCULOS")
        print("=" * 60)
        
        latest = session.execute(
            select(db.ArticleRow)
            .order_by(db.ArticleRow.published_at.desc())
            .limit(5)
        ).scalars().all()
        
        for article in latest:
            print(f"\n[{article.player}] {article.title[:60]}...")
            print(f"   📅 {article.published_at}")
            print(f"   🔗 {article.url}")
            if article.sentiment_label:
                print(f"   💭 Sentimiento: {article.sentiment_label} ({article.sentiment_score:.2f})")


if __name__ == "__main__":
    main()
