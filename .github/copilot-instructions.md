# Copilot Instructions

## Project Overview

Automated sentiment analysis pipeline for Spanish sports press coverage of Real Madrid players. Scrapes Marca.com RSS feeds, classifies sentiment with a Spanish BERT model, stores results in SQLite, and renders an interactive Streamlit dashboard.

## Package Manager

This project uses **`uv`** (not pip/poetry). Always use `uv` commands:

```bash
uv sync                          # Install dependencies
uv run <script.py>               # Run a script in the project environment
uv add <package>                 # Add a dependency
```

## Key Commands

```bash
# Launch dashboard
./scripts/run_dashboard.sh
# or: uv run streamlit run dashboard/app.py  →  http://localhost:8501

# Full pipeline update (fetch RSS + classify sentiment)
./scripts/update_data.sh

# Fetch new articles only
cd data_pipeline && uv run main.py

# Classify unlabeled articles only
cd sentiment_analysis && uv run label-data.py

# View DB stats
cd data_pipeline && uv run view_db.py
# or: ./scripts/query_db.sh
```

## Architecture

Three independent layers share a single SQLAlchemy ORM (`data_pipeline/db.py`):

```
Marca.com RSS feeds (21 players)
    ↓  feedparser
data_pipeline/main.py  →  deduplication via SHA1(url)  →  data/articles.db
                                                              (sentiment_label=NULL)
    ↓
sentiment_analysis/label-data.py  →  pysentimiento/robertuito-sentiment-analysis
                                  →  UPDATE articles SET sentiment_label, sentiment_score
    ↓
dashboard/app.py  →  Streamlit + Plotly  →  localhost:8501
```

**Data flow**: `Article` dataclass (feedparser) → `ArticleRow` SQLAlchemy ORM → Pandas DataFrame → Plotly charts.

## Testing

There is **no pytest framework**. The only test script is a manual model smoke test:

```bash
cd sentiment_analysis && uv run test.py   # runs 15 hardcoded Spanish phrases through the model
```

To manually test individual components:

```bash
# Test DB connection
cd data_pipeline && uv run python -c "import db; db.init_db(); print('DB OK')"

# Test RSS fetch for one player
cd data_pipeline && uv run python -c "import main; arts = main.fetch_player_articles('Vinicius', 'vinicius-junior'); print(len(arts))"
```

## Key Conventions

- **Deduplication**: Articles are identified by `SHA1(url)`. `save_articles()` silently skips duplicates and returns `(inserted, skipped)` counts.
- **Sentiment labels**: Always uppercase 3-letter codes: `POS`, `NEU`, `NEG`. There is a DB CHECK constraint enforcing this.
- **Sentiment scores**: Numeric mapping used for rankings: `{"POS": 1, "NEU": 0, "NEG": -1}`.
- **Text truncation**: Input to the NLP model is `(title + " " + summary)[:512]` — BERT token limit.
- **Batch size**: Sentiment analysis processes 32 articles per batch (`batch_size=32`).
- **DB path**: Relative to `db.py` location — `../data/articles.db`. Always run pipeline scripts from their own directories (`cd data_pipeline && uv run ...`).
- **Concurrency**: SQLite is configured with `check_same_thread=False` and a 30s timeout so the dashboard and update pipeline can run simultaneously.
- **No environment variables**: All config (DB path, RSS URL template, model name) is hardcoded in source files; player/team config is in `data/players.toml`.
- **ORM relationship**: `ArticleRow.player_rel` uses `lazy="joined"` (always eager). Use `session.expunge_all()` when returning ORM objects outside a session — `get_articles_without_sentiment()` does this already.

## Database Schema

```sql
players (
    id    VARCHAR PRIMARY KEY,   -- SHA1(player name)
    name  VARCHAR NOT NULL,
    club  VARCHAR NOT NULL,
    slug  VARCHAR NOT NULL       -- Marca.com URL slug
)

articles (
    id              VARCHAR PRIMARY KEY,  -- SHA1(url)
    player_id       VARCHAR NOT NULL,     -- FK → players.id  (indexed)
    title           TEXT NOT NULL,
    summary         TEXT,
    url             TEXT NOT NULL,
    author          VARCHAR,
    published_at    DATETIME,
    fetched_at      DATETIME,
    sentiment_label VARCHAR,              -- POS | NEU | NEG (NULL until labeled)
    sentiment_score FLOAT,               -- 0.0–1.0 confidence
    CHECK (sentiment_label IN ('POS', 'NEU', 'NEG'))
)
```

`ArticleRow` exposes `.player` and `.club` as convenience properties (via `player_rel`), so all code that accesses `article.player` continues to work without changes.

## Adding a New Player or Team

Edit **`data/players.toml`** (committed to the repo):

```toml
[[teams]]
club = "FC Barcelona"
players = [
  { name = "Yamal", slug = "lamine-yamal" },
]
```

The slug comes from the Marca.com URL: `marca.com/personajes/{slug}.html`. After editing, run `./scripts/update_data.sh` to fetch and classify articles. New players are auto-inserted into the `players` table on first fetch.

## Migration (existing databases)

```bash
uv run scripts/migrate_multi_team.py   # idempotent — safe to run multiple times
```

## Dashboard Color/Score Constants (`dashboard/app.py`)

```python
SENTIMENT_COLORS = {"POS": "#00a651", "NEU": "#d3d3d3", "NEG": "#d32f2f"}
SENTIMENT_SCORES = {"POS": 1, "NEU": 0, "NEG": -1}
```
