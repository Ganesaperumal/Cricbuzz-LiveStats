"""
Database Connection Utility
============================
Centralised SQLite connection helper.
All pages import get_connection() from here so we never
hard-code the DB path in more than one place.

Usage:
    from utils.db_connection import get_connection, run_query

    conn = get_connection()          # raw sqlite3 connection
    df   = run_query("SELECT …")     # returns a pandas DataFrame
"""

import sqlite3
import os
import pandas as pd

# ── Path resolution ──────────────────────────────────────────────────────────
# Works whether you run from the project root  OR  from inside utils/
_THIS_DIR    = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_THIS_DIR)

# Primary search: utils/cricBuzz.db   (relative to this file)
_DB_CANDIDATES = [
    os.path.join(_THIS_DIR,    "cricBuzz.db"),
    os.path.join(_PROJECT_ROOT, "utils", "cricBuzz.db"),
    os.path.join(_PROJECT_ROOT, "cricBuzz.db"),
]

def _find_db() -> str:
    """Return the first existing DB path, else fall back to the canonical one."""
    for path in _DB_CANDIDATES:
        if os.path.exists(path):
            return path
    # If none found yet, return canonical path (will be created on first write)
    return _DB_CANDIDATES[0]

DB_PATH: str = _find_db()


# ── Public API ───────────────────────────────────────────────────────────────

def get_connection(check_same_thread: bool = False) -> sqlite3.Connection:
    """
    Return a live sqlite3 Connection object.

    Parameters
    ----------
    check_same_thread : bool
        Set to True when using inside Streamlit's threaded context if you
        need strict thread-safety (usually False is fine for read-only work).

    Returns
    -------
    sqlite3.Connection
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=check_same_thread)
    # Enable foreign-key enforcement
    conn.execute("PRAGMA foreign_keys = ON;")
    # Return dict-like rows (access columns by name)
    conn.row_factory = sqlite3.Row
    return conn


def run_query(sql: str, params: tuple = ()) -> pd.DataFrame:
    """
    Execute a SELECT query and return results as a pandas DataFrame.

    Parameters
    ----------
    sql    : str   — The SQL query string
    params : tuple — Optional bound parameters (use ? placeholders)

    Returns
    -------
    pd.DataFrame — Empty DataFrame on error; check console for details.

    Example
    -------
    df = run_query("SELECT * FROM players WHERE teamId = ?", (2,))
    """
    try:
        conn = sqlite3.connect(DB_PATH)          # plain connection for pandas
        df   = pd.read_sql_query(sql, conn, params=params)
        conn.close()
        return df
    except Exception as exc:
        print(f"[db_connection] Query error: {exc}\nSQL: {sql}")
        return pd.DataFrame()


def execute_write(sql: str, params: tuple = ()) -> bool:
    """
    Execute an INSERT / UPDATE / DELETE statement.

    Parameters
    ----------
    sql    : str   — The SQL statement
    params : tuple — Bound parameters

    Returns
    -------
    bool — True on success, False on failure.
    """
    try:
        conn   = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        conn.close()
        return True
    except Exception as exc:
        print(f"[db_connection] Write error: {exc}\nSQL: {sql}")
        return False


def get_table_names() -> list:
    """Return a list of all user-created tables in the database."""
    conn   = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
    )
    names = [row[0] for row in cursor.fetchall()]
    conn.close()
    return names


def get_row_counts() -> dict:
    """
    Return {table_name: row_count} for every table in the database.
    Useful for the Home page dashboard stats.
    """
    counts = {}
    conn   = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for table in get_table_names():
        try:
            cursor.execute(f"SELECT COUNT(*) FROM [{table}]")
            counts[table] = cursor.fetchone()[0]
        except Exception:
            counts[table] = -1
    conn.close()
    return counts
