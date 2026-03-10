from sqlalchemy import (
    Column, DateTime, Float, ForeignKey, String, Text, create_engine, select, text
)
from sqlalchemy.orm import DeclarativeBase, Session, joinedload, relationship
import hashlib

DATABASE_URL = "postgresql://neondb_owner:npg_BLtVOTG8MSa3@ep-flat-smoke-ab11u7zs-pooler.eu-west-2.aws.neon.tech/neondb?sslmode=require"

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)


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

def check_test_player():
    test_id = hashlib.sha1(b"__test_player__").hexdigest()

    with Session(engine) as session:
        stmt = (select(PlayerRow).
                where(PlayerRow.id == test_id)
                )
        players = list(session.scalars(stmt).all())
        for player in players:
            print(f"{player.name} , {player.club}")
        session.expunge_all()

def create_test_player():
    test_id = hashlib.sha1(b"__test_player__").hexdigest()

    with Session(engine) as session:
        # Crear el objeto ORM y añadirlo a la sesión
        nuevo = PlayerRow(
            id=test_id,
            name="Test Player",
            club="Test FC",
            slug="test-player",
        )
        session.add(nuevo)
        session.commit()   # ← escribe en la DB
        print(f"Insertado: {nuevo.name} (id={nuevo.id[:8]}…)")


with Session(engine) as session:
    t = text("select COUNT(*), club from players group by club;")
    rows = session.execute(t)
    for row in rows:
        print(row)