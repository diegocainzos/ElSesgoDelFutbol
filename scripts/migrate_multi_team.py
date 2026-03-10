"""
Migration: introduces players table and player_id FK in articles.
Backfills all existing articles as Real Madrid players.

Safe to run multiple times (idempotent).
Usage: uv run scripts/migrate_multi_team.py
"""

import hashlib
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "data_pipeline"))

from sqlalchemy import text
import db


def _sha1(value: str) -> str:
    return hashlib.sha1(value.encode()).hexdigest()


def load_slugs_from_config() -> dict[str, str]:
    """Returns {player_name: slug} for all players in players.toml."""
    config_path = Path(__file__).parent.parent / "data" / "players.toml"
    with open(config_path, "rb") as f:
        config = tomllib.load(f)
    return {p["name"]: p["slug"] for team in config["teams"] for p in team["players"]}


def migrate() -> None:
    db.init_db()  # Creates the players table if it doesn't exist yet

    slugs = load_slugs_from_config()

    with db.engine.connect() as conn:
        cols = {row[1] for row in conn.execute(text("PRAGMA table_info(articles)")).fetchall()}

        if "player" not in cols and "player_id" in cols:
            print("✅ Migration already applied. Nothing to do.")
            return

        # Step 1: populate players table from distinct names in articles
        players = [row[0] for row in conn.execute(text("SELECT DISTINCT player FROM articles")).fetchall()]
        print(f"Found {len(players)} distinct players in articles")

        for name in players:
            pid = _sha1(name)
            slug = slugs.get(name, "")
            conn.execute(text("""
                INSERT OR IGNORE INTO players (id, name, club, slug)
                VALUES (:id, :name, :club, :slug)
            """), {"id": pid, "name": name, "club": "Real Madrid", "slug": slug})

        conn.commit()
        print(f"✅ Populated players table ({len(players)} players, club='Real Madrid')")

        # Step 2: add player_id column to articles if not present
        if "player_id" not in cols:
            conn.execute(text("ALTER TABLE articles ADD COLUMN player_id VARCHAR"))
            conn.commit()
            print("✅ Added player_id column to articles")

        # Step 3: populate player_id for every article
        rows = conn.execute(text("SELECT id, player FROM articles WHERE player_id IS NULL")).fetchall()
        for article_id, player_name in rows:
            pid = _sha1(player_name)
            conn.execute(
                text("UPDATE articles SET player_id = :pid WHERE id = :aid"),
                {"pid": pid, "aid": article_id},
            )
        conn.commit()
        print(f"✅ Populated player_id for {len(rows)} articles")

        # Step 4: drop the index on the old player column, then drop the column
        conn.execute(text("DROP INDEX IF EXISTS ix_articles_player"))
        conn.execute(text("ALTER TABLE articles DROP COLUMN player"))
        conn.commit()
        print("✅ Dropped player text column from articles")

    print("\n🎉 Migration complete.")


if __name__ == "__main__":
    migrate()
