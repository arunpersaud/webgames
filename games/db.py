"""SQLite storage for game state.

All state is short-lived: games nobody touched for MAX_AGE are deleted
whenever a new game is created.
"""

import sqlite3
import time
from contextlib import closing
from pathlib import Path

from flask import Flask, current_app, g

MAX_AGE = 7 * 24 * 60 * 60  # seconds

SCHEMA = """
CREATE TABLE IF NOT EXISTS boggle (
    seed    TEXT NOT NULL,
    size    TEXT NOT NULL,           -- '4x4' or '5x5'
    letters TEXT NOT NULL,           -- comma separated, row by row
    started INTEGER NOT NULL,        -- unix time in ms
    PRIMARY KEY (seed, size)
);
CREATE TABLE IF NOT EXISTS hand_seen (
    game    TEXT NOT NULL,           -- 'doko' or 'skat'
    seed    TEXT NOT NULL,
    nr      INTEGER NOT NULL,
    player  TEXT NOT NULL,
    seen    REAL NOT NULL,
    PRIMARY KEY (game, seed, nr, player)
);
CREATE TABLE IF NOT EXISTS krazy_round (
    seed    TEXT NOT NULL,
    nr      INTEGER NOT NULL,
    data    TEXT NOT NULL,           -- JSON: words, player-info, language
    created REAL NOT NULL,
    PRIMARY KEY (seed, nr)
);
CREATE TABLE IF NOT EXISTS krazy_play (
    seed    TEXT NOT NULL,
    nr      INTEGER NOT NULL,
    player  INTEGER NOT NULL,
    word    TEXT,                    -- the word the player built
    guess   TEXT,                    -- JSON list: word number per player
    updated REAL NOT NULL,
    PRIMARY KEY (seed, nr, player)
);
"""

# table -> column with the time of the last change
_TIMESTAMPS = {
    "boggle": "started / 1000.0",
    "hand_seen": "seen",
    "krazy_round": "created",
    "krazy_play": "updated",
}


def connect(path: str | Path) -> sqlite3.Connection:
    db = sqlite3.connect(path, autocommit=True, timeout=10)
    db.row_factory = sqlite3.Row
    return db


def get_db() -> sqlite3.Connection:
    """The connection for the current request."""
    if "db" not in g:
        g.db = connect(current_app.config["DATABASE"])
    return g.db


def close_db(exc: BaseException | None = None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def cleanup(max_age: float = MAX_AGE) -> None:
    """Delete game state older than max_age seconds."""
    cutoff = time.time() - max_age
    db = get_db()
    for table, column in _TIMESTAMPS.items():
        db.execute(f"DELETE FROM {table} WHERE {column} < ?", (cutoff,))


def init_app(app: Flask) -> None:
    path = Path(app.config["DATABASE"])
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(connect(path)) as db:
        db.execute("PRAGMA journal_mode = WAL")
        db.executescript(SCHEMA)
    app.teardown_appcontext(close_db)
