"""
Capa de persistencia. SQLite en local, Postgres en producción.
Cambiar DATABASE_URL es todo lo que hace falta para migrar.
"""

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy import (
    Column, DateTime, Float, ForeignKey, String, Text, create_engine, select
)
from sqlalchemy.orm import DeclarativeBase, Session, joinedload, relationship

_DB_PATH = Path(__file__).parent.parent / "data" / "articles.db"
DATABASE_URL = "postgresql://neondb_owner:npg_BLtVOTG8MSa3@ep-flat-smoke-ab11u7zs-pooler.eu-west-2.aws.neon.tech/neondb?sslmode=require"


class Base(DeclarativeBase):
    pass


class PlayerRow(Base):
    __tablename__ = "players"

    id    = Column(String, primary_key=True)  # SHA1(name)
    name  = Column(String, nullable=False)
    club  = Column(String, nullable=False)
    slug  = Column(String, nullable=False, default="")

    articles = relationship("ArticleRow", back_populates="player_rel")


class ArticleRow(Base):
    __tablename__ = "articles"

    id           = Column(String, primary_key=True)  # SHA1(url)
    player_id    = Column(String, ForeignKey("players.id"), nullable=False, index=True)
    title        = Column(Text, nullable=False)
    summary      = Column(Text)
    url          = Column(Text, nullable=False)
    author       = Column(String)
    published_at = Column(DateTime)
    fetched_at   = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # NLP — NULL hasta que pase por el modelo
    # Labels posibles: POS (Positivo), NEU (Neutral), NEG (Negativo)
    sentiment_label = Column(String)  # La label del modelo
    sentiment_score = Column(Float)   # Confianza del modelo para esa label (0-1)

    # Eager-load player on every ArticleRow query to avoid DetachedInstanceError
    player_rel = relationship("PlayerRow", back_populates="articles", lazy="joined")

    @property
    def player(self) -> str:
        """Player name — backward-compatible convenience accessor."""
        return self.player_rel.name if self.player_rel else ""

    @property
    def club(self) -> str:
        """Club name — convenience accessor."""
        return self.player_rel.club if self.player_rel else ""


engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)


def init_db() -> None:
    Base.metadata.create_all(engine)


def _article_id(url: str) -> str:
    return hashlib.sha1(url.encode()).hexdigest()


def _player_id(name: str) -> str:
    return hashlib.sha1(name.encode()).hexdigest()


def _get_or_create_player(session: Session, name: str, club: str, slug: str) -> PlayerRow:
    """Get existing player or insert a new one within the given session."""
    pid = _player_id(name)
    existing = session.get(PlayerRow, pid)
    if existing:
        return existing
    player = PlayerRow(id=pid, name=name, club=club, slug=slug)
    session.add(player)
    session.flush()
    return player


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

            if session.get(ArticleRow, article_id):
                skipped += 1
                continue

            player_row = _get_or_create_player(session, article.player, article.club, article.slug)
            row = ArticleRow(
                id=article_id,
                player_id=player_row.id,
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
    """
    Devuelve todos los artículos que todavía no tienen sentimiento.
    Los objetos son expulsados de la sesión con sus relaciones ya cargadas,
    por lo que son seguros de usar fuera de la sesión.
    """
    with Session(engine) as session:
        stmt = (
            select(ArticleRow)
            .options(joinedload(ArticleRow.player_rel))
            .where(ArticleRow.sentiment_label.is_(None))
        )
        rows = list(session.scalars(stmt).unique().all())
        session.expunge_all()
        return rows


def save_sentiment(article_id: str, label: str, score: float) -> None:
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
