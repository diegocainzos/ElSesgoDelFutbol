import tomllib
from dataclasses import dataclass
from pathlib import Path

import feedparser

import db

MARCA_RSS_BASE = "https://www.marca.com/rss/googlenews/personajes/{slug}.xml"
_PLAYERS_CONFIG = Path(__file__).parent.parent / "data" / "players.toml"


@dataclass
class Article:
    player: str
    club: str
    slug: str
    title: str
    url: str
    published: str
    summary: str = ""
    author: str = ""


def load_players_config() -> list[dict]:
    """Load teams and players from data/players.toml."""
    with open(_PLAYERS_CONFIG, "rb") as f:
        config = tomllib.load(f)
    return config["teams"]


def fetch_player_articles(player_name: str, slug: str, club: str) -> list[Article]:
    """Obtiene TODOS los artículos disponibles en el RSS del jugador (sin límite)."""
    feed_url = MARCA_RSS_BASE.format(slug=slug)
    feed = feedparser.parse(feed_url)

    if feed.bozo and not feed.entries:
        print(f"  [WARN] No se pudo parsear el feed de {player_name}: {feed.bozo_exception}")
        return []

    articles = []
    for entry in feed.entries:
        articles.append(Article(
            player=player_name,
            club=club,
            slug=slug,
            title=entry.get("title", ""),
            url=entry.get("link", ""),
            published=entry.get("published", ""),
            summary=entry.get("summary", ""),
            author=entry.get("author", ""),
        ))
    return articles


def fetch_all_players() -> list[Article]:
    """Obtiene todos los artículos de todos los equipos y jugadores."""
    teams = load_players_config()
    all_articles = []
    for team in teams:
        club = team["club"]
        for player in team["players"]:
            name = player["name"]
            slug = player["slug"]
            print(f"Fetching {name} ({club})...")
            articles = fetch_player_articles(name, slug, club)
            print(f"  → {len(articles)} artículos")
            all_articles.extend(articles)
    return all_articles


def main():
    db.init_db()

    articles = fetch_all_players()
    inserted, skipped = db.save_articles(articles)

    print(f"\n{'='*60}")
    print(f"Total fetched:  {len(articles)}")
    print(f"Insertados:     {inserted}")
    print(f"Ya existían:    {skipped}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
