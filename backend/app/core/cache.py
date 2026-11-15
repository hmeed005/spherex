"""Petit cache clé -> JSON dans SQLite (résultats de requêtes IRSA)."""
import json
import sqlite3
import time
from contextlib import closing

from app.core.config import DB_PATH


def _conn():
    con = sqlite3.connect(DB_PATH)
    con.execute("CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, created REAL, value TEXT)")
    return con


def cache_get(key: str):
    with closing(_conn()) as con:
        row = con.execute("SELECT value, created FROM kv WHERE key = ?", (key,)).fetchone()
    if row is None:
        return None
    return json.loads(row[0]), row[1]


def cache_set(key: str, value) -> None:
    with closing(_conn()) as con, con:
        con.execute("INSERT OR REPLACE INTO kv VALUES (?, ?, ?)",
                    (key, time.time(), json.dumps(value)))
