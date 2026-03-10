import sys
import sqlite3
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from sqlalchemy.orm import Session
from data_pipeline.db import engine, PlayerRow, ArticleRow

def migrate():
    sqlite_db_path = Path("data/articles.db")
    if not sqlite_db_path.exists():
        print("No encontré la base de datos local SQLite. ¿Capaz ya la borraste, papá?")
        return

    print(f"Me conecto al potrero local: {sqlite_db_path}")
    conn = sqlite3.connect(sqlite_db_path)
    cursor = conn.cursor()

    with Session(engine) as session:
        # 1. Migrar Jugadores
        print("Traemos a los jugadores...")
        cursor.execute("SELECT id, name, club, slug FROM players")
        players = cursor.fetchall()
        
        for p in players:
            # Check if exists
            if not session.get(PlayerRow, p[0]):
                player_row = PlayerRow(id=p[0], name=p[1], club=p[2], slug=p[3])
                session.add(player_row)
        
        session.commit()
        print(f"¡{len(players)} jugadores en la nueva concentración!")

        # 2. Migrar Artículos
        print("Traemos los artículos y las noticias...")
        cursor.execute("""
            SELECT id, player_id, title, summary, url, author, published_at, fetched_at, sentiment_label, sentiment_score
            FROM articles
        """)
        articles = cursor.fetchall()
        
        from datetime import datetime
        def parse_date(date_str):
            if not date_str:
                return None
            try:
                # SQLite usually stores dates as strings in ISO format
                return datetime.fromisoformat(date_str)
            except ValueError:
                return None

        for a in articles:
            if not session.get(ArticleRow, a[0]):
                article_row = ArticleRow(
                    id=a[0],
                    player_id=a[1],
                    title=a[2],
                    summary=a[3],
                    url=a[4],
                    author=a[5],
                    published_at=parse_date(a[6]),
                    fetched_at=parse_date(a[7]),
                    sentiment_label=a[8],
                    sentiment_score=a[9]
                )
                session.add(article_row)
        
        session.commit()
        print(f"¡{len(articles)} artículos pasados a primera división!")

    conn.close()
    print("¡Migración terminada, pibe! Ya estamos listos para el mundial.")

if __name__ == "__main__":
    migrate()
