# data/database.py
import json
import os
import sqlite3

# По умолчанию — bot.db рядом с этим файлом; переопределение через переменную окружения DB_PATH
_DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("DB_PATH", os.path.join(_DB_DIR, "bot.db"))


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS user_state (
        user_id INTEGER PRIMARY KEY,
        data TEXT NOT NULL
    )"""
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS user_favorites (
        user_id INTEGER PRIMARY KEY,
        data TEXT NOT NULL
    )"""
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS user_progress (
        user_id INTEGER NOT NULL,
        child_name TEXT NOT NULL,
        data TEXT NOT NULL,
        PRIMARY KEY (user_id, child_name)
    )"""
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS user_history (
        user_id INTEGER PRIMARY KEY,
        data TEXT NOT NULL
    )"""
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS user_games_journal (
        user_id INTEGER PRIMARY KEY,
        data TEXT NOT NULL
    )"""
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS children (
        user_id INTEGER PRIMARY KEY,
        data TEXT NOT NULL
    )"""
    )
    conn.commit()
    conn.close()


# --- user_state ---
def get_user_state(user_id):
    conn = get_conn()
    row = conn.execute("SELECT data FROM user_state WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return json.loads(row["data"]) if row else {}


def set_user_state(user_id, data):
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO user_state (user_id, data) VALUES (?,?)",
        (user_id, json.dumps(data, ensure_ascii=False)),
    )
    conn.commit()
    conn.close()


# --- user_favorites ---
def get_user_favorites(user_id):
    conn = get_conn()
    row = conn.execute("SELECT data FROM user_favorites WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return set(json.loads(row["data"])) if row else set()


def set_user_favorites(user_id, data: set):
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO user_favorites (user_id, data) VALUES (?,?)",
        (user_id, json.dumps(list(data), ensure_ascii=False)),
    )
    conn.commit()
    conn.close()


# --- user_progress ---
def get_user_progress(user_id, child_name):
    conn = get_conn()
    row = conn.execute(
        "SELECT data FROM user_progress WHERE user_id=? AND child_name=?",
        (user_id, child_name),
    ).fetchone()
    conn.close()
    return json.loads(row["data"]) if row else None


def set_user_progress(user_id, child_name, data):
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO user_progress (user_id, child_name, data) VALUES (?,?,?)",
        (user_id, child_name, json.dumps(data, ensure_ascii=False)),
    )
    conn.commit()
    conn.close()


# --- user_history ---
def get_user_history(user_id):
    conn = get_conn()
    row = conn.execute("SELECT data FROM user_history WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return json.loads(row["data"]) if row else []


def set_user_history(user_id, data: list):
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO user_history (user_id, data) VALUES (?,?)",
        (user_id, json.dumps(data, ensure_ascii=False)),
    )
    conn.commit()
    conn.close()


# --- user_games_journal ---
def get_user_games_journal(user_id):
    conn = get_conn()
    row = conn.execute(
        "SELECT data FROM user_games_journal WHERE user_id=?", (user_id,)
    ).fetchone()
    conn.close()
    return json.loads(row["data"]) if row else []


def set_user_games_journal(user_id, data: list):
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO user_games_journal (user_id, data) VALUES (?,?)",
        (user_id, json.dumps(data, ensure_ascii=False)),
    )
    conn.commit()
    conn.close()


# --- children ---
def get_children(user_id):
    conn = get_conn()
    row = conn.execute("SELECT data FROM children WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return json.loads(row["data"]) if row else []


def set_children(user_id, data: list):
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO children (user_id, data) VALUES (?,?)",
        (user_id, json.dumps(data, ensure_ascii=False)),
    )
    conn.commit()
    conn.close()


# --- наличие строк (для `in` / `not in` в обработчиках) ---
def user_state_row_exists(user_id):
    conn = get_conn()
    row = conn.execute(
        "SELECT 1 FROM user_state WHERE user_id=? LIMIT 1", (user_id,)
    ).fetchone()
    conn.close()
    return row is not None


def user_favorites_row_exists(user_id):
    conn = get_conn()
    row = conn.execute(
        "SELECT 1 FROM user_favorites WHERE user_id=? LIMIT 1", (user_id,)
    ).fetchone()
    conn.close()
    return row is not None


def user_progress_row_exists(user_id, child_name):
    conn = get_conn()
    row = conn.execute(
        "SELECT 1 FROM user_progress WHERE user_id=? AND child_name=? LIMIT 1",
        (user_id, child_name),
    ).fetchone()
    conn.close()
    return row is not None
