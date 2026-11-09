import json
import sqlite3
import time
from . import config

_conn = sqlite3.connect(config.DB_PATH, check_same_thread=False)
_conn.row_factory = sqlite3.Row
_conn.executescript("""
CREATE TABLE IF NOT EXISTS todos(id INTEGER PRIMARY KEY, text TEXT, due TEXT, done INT DEFAULT 0);
CREATE TABLE IF NOT EXISTS reminders(id INTEGER PRIMARY KEY, text TEXT, fire_at REAL, sent INT DEFAULT 0);
CREATE TABLE IF NOT EXISTS memory(key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS pending(id INTEGER PRIMARY KEY, kind TEXT, payload TEXT, status TEXT DEFAULT 'pending');
CREATE TABLE IF NOT EXISTS issues(id INTEGER PRIMARY KEY, title TEXT, symptoms TEXT, solution TEXT, tags TEXT, ts REAL);
CREATE TABLE IF NOT EXISTS guests(user_id INTEGER PRIMARY KEY, ts REAL);
CREATE TABLE IF NOT EXISTS interactions(id INTEGER PRIMARY KEY, ts REAL, user_msg TEXT, transcript TEXT, reply TEXT, rating INT);
""")


def q(sql, args=()):
    return [dict(r) for r in _conn.execute(sql, args).fetchall()]


def x(sql, args=()):
    cur = _conn.execute(sql, args)
    _conn.commit()
    return cur.lastrowid


def log_interaction(user_msg, transcript, reply):
    return x("INSERT INTO interactions(ts,user_msg,transcript,reply) VALUES(?,?,?,?)",
             (time.time(), user_msg, json.dumps(transcript, default=str), reply))
