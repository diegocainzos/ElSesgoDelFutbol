"""
Tutorial de SQLAlchemy 2.0 — basado en los modelos de este proyecto.
Ejecutar: uv run test/tutorial.py
"""

import sys
from pathlib import Path
from datetime import datetime, timezone
import sqlalchemy
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

# Reutilizamos los modelos y el engine ya definidos en test/db.py
sys.path.insert(0, str(Path(__file__).parent))
from db import engine, PlayerRow, ArticleRow


# ─────────────────────────────────────────────────────────────
# HELPERS DE VISUALIZACIÓN
# ─────────────────────────────────────────────────────────────

def header(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def show(rows: list, limit: int = 5):
    """Imprime una lista de ORM objects de forma legible."""
    for row in rows[:limit]:
        print(vars(row))   # muestra todos los atributos como dict
    if len(rows) > limit:
        print(f"  ... ({len(rows) - limit} más)")


# ─────────────────────────────────────────────────────────────
# 1. SELECCIONAR — traer todas las filas
# ─────────────────────────────────────────────────────────────
header("1. SELECT todos los jugadores")

with Session(engine) as session:
    stmt = select(PlayerRow)
    players = list(session.scalars(stmt).all())
    # .scalars()  → devuelve los objetos ORM directamente (no tuplas)
    # .execute()  → devuelve tuplas de filas (ver sección 5)

print(f"Total jugadores: {len(players)}")
for p in players[:3]:
    print(f"  {p.id[:8]}… | {p.name:20} | {p.club}")


# ─────────────────────────────────────────────────────────────
# 2. WHERE — filtrar filas
# ─────────────────────────────────────────────────────────────
header("2. WHERE — filtros")

with Session(engine) as session:

    # Igualdad
    stmt = select(PlayerRow).where(PlayerRow.name == "Alaba")
    alaba = session.scalars(statement=stmt).first()   # .first() → un objeto o None
    print(f"Igualdad:   {alaba.name if alaba else 'no encontrado'}")

    # IN — varios valores
    stmt = select(PlayerRow).where(PlayerRow.name.in_(["Vinicius", "Mbappé", "Bellingham"]))
    galacticos = list(session.scalars(stmt).all())
    print(f"IN:         {[p.name for p in galacticos]}")

    # LIKE — búsqueda parcial (% es comodín)
    stmt = select(PlayerRow).where(PlayerRow.name.ilike("%williams%"))
    williams = list(session.scalars(stmt).all())
    print(f"ILIKE:      {[p.name for p in williams]}")

    # Filtro por club
    stmt = select(PlayerRow).where(PlayerRow.club == "FC Barcelona")
    barca = list(session.scalars(stmt).all())
    print(f"Barcelona:  {len(barca)} jugadores")

    # Múltiples condiciones con AND (simplemente encadena .where())
    stmt = (
        select(PlayerRow)
        .where(PlayerRow.club == "Real Madrid")
        .where(PlayerRow.slug.like("%-junior"))  # slug termina en -junior
    )
    result = list(session.scalars(stmt).all())
    print(f"AND:        {[p.name for p in result]}")

    # IS NULL / IS NOT NULL
    stmt = select(ArticleRow).where(ArticleRow.sentiment_label.is_(None))
    sin_sentimiento = session.scalar(select(func.count()).select_from(
        select(ArticleRow).where(ArticleRow.sentiment_label.is_(None)).subquery()
    ))
    print(f"IS NULL:    {sin_sentimiento} artículos sin sentimiento")


# ─────────────────────────────────────────────────────────────
# 3. ORDER BY y LIMIT
# ─────────────────────────────────────────────────────────────
header("3. ORDER BY y LIMIT")

with Session(engine) as session:
    stmt = (
        select(ArticleRow)
        .options(joinedload(ArticleRow.player_rel))  # carga el jugador en el mismo query
        .where(ArticleRow.sentiment_label.is_not(None))
        .order_by(ArticleRow.published_at.desc())    # .asc() para ascendente
        .limit(5)
    )
    recent = list(session.scalars(stmt).unique().all())

for a in recent:
    print(f"  [{a.player:12}] {a.sentiment_label} | {a.title[:50]}")


# ─────────────────────────────────────────────────────────────
# 4. AGGREGATE — COUNT, GROUP BY
# ─────────────────────────────────────────────────────────────
header("4. COUNT y GROUP BY")

with Session(engine) as session:

    # COUNT total
    total = session.scalar(select(func.count()).select_from(ArticleRow))
    print(f"Total artículos: {total}")

    # COUNT con filtro
    positivos = session.scalar(
        select(func.count())
        .select_from(ArticleRow)
        .where(ArticleRow.sentiment_label == "POS")
    )
    print(f"Artículos POS:   {positivos}")

    # GROUP BY — artículos por club (join necesario)
    stmt = (
        select(PlayerRow.club, func.count(ArticleRow.id).label("total"))
        .join(ArticleRow, ArticleRow.player_id == PlayerRow.id)
        .group_by(PlayerRow.club)
        .order_by(func.count(ArticleRow.id).desc())
    )
    # Aquí usamos .execute() porque seleccionamos columnas sueltas, no objetos ORM
    for club, total in session.execute(stmt).all():
        print(f"  {club:25} → {total} artículos")


# ─────────────────────────────────────────────────────────────
# 5. .scalars() vs .execute() — cuándo usar cada uno
# ─────────────────────────────────────────────────────────────
header("5. scalars() vs execute()")

with Session(engine) as session:

    # .scalars() → cuando el SELECT es sobre un modelo completo
    # Devuelve objetos ORM con sus atributos (p.name, p.club, etc.)
    stmt = select(PlayerRow).limit(2)
    for p in session.scalars(stmt).all():
        print(f"  scalars → objeto ORM: {p.name}, {p.club}")

    # .execute() → cuando el SELECT es sobre columnas sueltas
    # Devuelve named tuples: row.name, row.club
    stmt = select(PlayerRow.name, PlayerRow.club).limit(2)
    for row in session.execute(stmt).all():
        print(f"  execute → tupla:      {row.name}, {row.club}")
        # También accesible por índice: row[0], row[1]


# ─────────────────────────────────────────────────────────────
# 6. GET por clave primaria
# ─────────────────────────────────────────────────────────────
header("6. GET por primary key")

with Session(engine) as session:
    # Obtener el id de un jugador primero
    alaba = session.scalars(select(PlayerRow).where(PlayerRow.name == "Alaba")).first()
    if alaba:
        player_id = alaba.id
        # session.get() → busca por PK, devuelve None si no existe
        found = session.get(PlayerRow, player_id)
        print(f"GET by PK: {found.name} ({found.club})")


# ─────────────────────────────────────────────────────────────
# 7. INSERT
# ─────────────────────────────────────────────────────────────
# header("7. INSERT")

# import hashlib
# test_id = hashlib.sha1(b"__test_player__").hexdigest()

# with Session(engine) as session:
#     # Crear el objeto ORM y añadirlo a la sesión
#     nuevo = PlayerRow(
#         id=test_id,
#         name="Test Player",
#         club="Test FC",
#         slug="test-player",
#     )
#     session.add(nuevo)
#     session.commit()   # ← escribe en la DB
#     print(f"Insertado: {nuevo.name} (id={nuevo.id[:8]}…)")


# ─────────────────────────────────────────────────────────────
# 8. UPDATE
# ─────────────────────────────────────────────────────────────
# header("8. UPDATE")

# with Session(engine) as session:
#     jugador = session.get(PlayerRow, test_id)
#     if jugador:
#         jugador.club = "Test FC Updated"   # modificar el atributo directamente
#         session.commit()                    # SQLAlchemy detecta el cambio automáticamente
#         print(f"Actualizado: {jugador.name} → {jugador.club}")


# # ─────────────────────────────────────────────────────────────
# # 9. DELETE
# # ─────────────────────────────────────────────────────────────
# header("9. DELETE")

# with Session(engine) as session:
#     jugador = session.get(PlayerRow, test_id)
#     if jugador:
#         session.delete(jugador)
#         session.commit()
#         print(f"Eliminado: {jugador.name}")


# ─────────────────────────────────────────────────────────────
# 10. SESIÓN — buenas prácticas
# ─────────────────────────────────────────────────────────────
header("10. Sesión — buenas prácticas")
print(f"Version SQL ALchemhy ------ {sqlalchemy.__version__}")
print("""
  ✅  Usa siempre 'with Session(engine) as session:'
      El bloque garantiza que la sesión se cierra aunque haya errores.

  ✅  session.commit()   → confirma cambios (INSERT/UPDATE/DELETE)
  ✅  session.rollback() → deshace cambios si algo falla
  ✅  session.flush()    → envía cambios a la DB sin hacer commit
                           (útil para obtener IDs antes de cerrar la transacción)

  ✅  Usa joinedload() cuando necesites acceder a relaciones
      fuera de la sesión (evita DetachedInstanceError):
        select(ArticleRow).options(joinedload(ArticleRow.player_rel))

  ❌  Session(bind=engine)  → sintaxis de SQLAlchemy 1.x, NO usar
  ❌  col.is_('valor')      → solo válido con None/True/False
  ❌  col == None           → usar col.is_(None)
""")

print("Tutorial completado ✅")
