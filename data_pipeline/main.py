import feedparser
from dataclasses import dataclass

import db

MARCA_RSS_BASE = "https://www.marca.com/rss/googlenews/personajes/{slug}.xml"

# Slug = la parte de la URL: marca.com/personajes/{slug}.html
# Para añadir un jugador: busca en Google "marca <nombre>" y copia el slug de la URL
PLAYERS: dict[str, str] = {
    "Courtois":        "courtois",
    "Lunin":           "andriy-lunin",
    "Carvajal":        "dani-carvajal",
    "Militao":         "eder-militao",
    "Alaba":           "david-alaba",
    "Rudiger":         "antonio-rudiger",
    "Vallejo":         "jesus-vallejo",
    "Fran Garcia":     "fran-garcia",
    "Mendy":           "ferland-mendy",
    "Tchouameni":      "aurelien-tchouameni",
    "Camavinga":       "camavinga",
    "Valverde":        "fede-valverde",
    "Bellingham":      "jude-bellingham",
    "Güler":           "arda-guler",
    "Vinicius":        "vinicius-junior",
    "Rodrygo":         "rodrygo-goes",
    "Brahim":          "brahim-diaz",
    "Mbappé":          "mbappe",
    "Endrick":         "endrick-felipe",
}


@dataclass
class Article:
    player: str
    title: str
    url: str
    published: str
    summary: str = ""
    author: str = ""


def fetch_player_articles(player_name: str, slug: str) -> list[Article]:
    """Obtiene TODOS los artículos disponibles en el RSS del jugador (sin límite)."""
    feed_url = MARCA_RSS_BASE.format(slug=slug)
    feed = feedparser.parse(feed_url)

    if feed.bozo and not feed.entries:
        print(f"  [WARN] No se pudo parsear el feed de {player_name}: {feed.bozo_exception}")
        return []

    articles = []
    # Sin límite: procesa todos los entries del feed
    for entry in feed.entries:
        articles.append(Article(
            player=player_name,
            title=entry.get("title", ""),
            url=entry.get("link", ""),
            published=entry.get("published", ""),
            summary=entry.get("summary", ""),
            author=entry.get("author", ""),
        ))
    return articles


def fetch_all_players() -> list[Article]:
    """Obtiene todos los artículos de todos los jugadores (sin límite)."""
    all_articles = []
    for player_name, slug in PLAYERS.items():
        print(f"Fetching {player_name}...")
        articles = fetch_player_articles(player_name, slug)
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
