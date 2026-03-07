"""
Capa de persistencia. SQLite en local, Postgres en producción.
Cambiar DATABASE_URL es todo lo que hace falta para migrar.
"""

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy import (
    Column, DateTime, Float, String, Text, create_engine, select
)
from sqlalchemy.orm import DeclarativeBase, Session

_DB_PATH = Path(__file__).parent.parent / "data" / "articles.db"
# Configuración para mejor manejo de concurrencia en SQLite
DATABASE_URL = f"sqlite:///{_DB_PATH}?check_same_thread=False"


class Base(DeclarativeBase):
    pass


class ArticleRow(Base):
    __tablename__ = "articles"

    id              = Column(String, primary_key=True)  # hash(url)
    player          = Column(String, nullable=False, index=True)
    title           = Column(Text, nullable=False)
    summary         = Column(Text)
    url             = Column(Text, nullable=False)
    author          = Column(String)
    published_at    = Column(DateTime)
    fetched_at      = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # NLP — NULL hasta que pase por el modelo
    # Labels posibles: VERY_POSITIVE, POSITIVE, NEUTRAL, UNDEFINED, NEGATIVE, VERY_NEGATIVE
    sentiment_label = Column(String)     # La label del modelo
    sentiment_score = Column(Float)      # Confianza del modelo para esa label (0-1)


engine = create_engine(
    DATABASE_URL, 
    echo=False,
    connect_args={"timeout": 30, "check_same_thread": False},
    pool_pre_ping=True,
)


def init_db() -> None:
    Base.metadata.create_all(engine)


def _article_id(url: str) -> str:
    return hashlib.sha1(url.encode()).hexdigest()


def save_articles(articles: list) -> tuple[int, int]:
    """
    Guarda una lista de Article (de main.py) en la DB.
    Devuelve (insertados, ya_existían).
    """
    inserted = 0
    skipped = 0

    with Session(engine) as session:
        for article in articles:
            article_id = _article_id(article.url)

            exists = session.get(ArticleRow, article_id)
            if exists:
                skipped += 1
                continue

            row = ArticleRow(
                id=article_id,
                player=article.player,
                title=article.title,
                summary=article.summary,
                url=article.url,
                author=article.author,
                published_at=_parse_date(article.published),
            )
            session.add(row)
            inserted += 1

        session.commit()

    return inserted, skipped


def get_articles_without_sentiment() -> list[ArticleRow]:
    """Devuelve todos los artículos que todavía no tienen sentimiento."""
    with Session(engine) as session:
        stmt = select(ArticleRow).where(ArticleRow.sentiment_label.is_(None))
        return list(session.scalars(stmt).all())


def save_sentiment(article_id: str, label: str, score: float) -> None:
    """Guarda el resultado del análisis de sentimiento para un artículo."""
    with Session(engine) as session:
        row = session.get(ArticleRow, article_id)
        if row:
            row.sentiment_label = label
            row.sentiment_score = score
            session.commit()


def save_sentiments_batch(results: list[tuple[str, str, float]]) -> int:
    """
    Guarda múltiples sentimientos de golpe (más eficiente).
    results: lista de tuplas (article_id, label, score)
    Devuelve: número de artículos actualizados.
    """
    updated = 0
    with Session(engine) as session:
        for article_id, label, score in results:
            row = session.get(ArticleRow, article_id)
            if row:
                row.sentiment_label = label
                row.sentiment_score = score
                updated += 1
        session.commit()
    return updated


def _parse_date(date_str: str) -> Optional[datetime]:
    if not date_str:
        return None
    try:
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(date_str)
    except Exception:
        return None
