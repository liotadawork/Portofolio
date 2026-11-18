"""Koneksi MySQL terpusat (PyMySQL).

Satu koneksi dibuat per request (disimpan di flask.g) lalu ditutup otomatis
di akhir request. Semua query memakai prepared statement (parameter %s).
"""
import pymysql
from flask import current_app, g


def get_db():
    if "db" not in g:
        cfg = current_app.config
        g.db = pymysql.connect(
            host=cfg["DB_HOST"],
            port=cfg["DB_PORT"],
            user=cfg["DB_USER"],
            password=cfg["DB_PASSWORD"],
            database=cfg["DB_NAME"],
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False,
            connect_timeout=5,
        )
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        try:
            db.close()
        except Exception:
            pass


def fetch_all(sql, params=()):
    with get_db().cursor() as cur:
        cur.execute(sql, params)
        return list(cur.fetchall())


def fetch_one(sql, params=()):
    with get_db().cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone()


def execute(sql, params=()):
    """Jalankan INSERT/UPDATE/DELETE, commit, kembalikan lastrowid."""
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(sql, params)
            last_id = cur.lastrowid
        db.commit()
        return last_id
    except Exception:
        db.rollback()
        raise


def init_app(app):
    app.teardown_appcontext(close_db)
