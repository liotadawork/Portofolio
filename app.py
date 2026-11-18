"""Titik masuk aplikasi portofolio Fuad Atoil (Flask + MySQL).

Jalankan dengan:  python app.py
"""
from datetime import timedelta

from flask import Flask, session

import db
from config import Config, KATEGORI_PENGALAMAN, PROFILE
from route import register_routes
from utils import csrf_token, check_csrf, periode, tgl, tgl_lengkap, tgl_waktu


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)
    app.permanent_session_lifetime = timedelta(seconds=app.config["PERMANENT_SESSION_LIFETIME"])

    db.init_app(app)
    app.before_request(check_csrf)

    app.jinja_env.filters.update(tgl=tgl, tgl_lengkap=tgl_lengkap, tgl_waktu=tgl_waktu, periode=periode)
    app.jinja_env.globals.update(csrf_token=csrf_token, profile=PROFILE, kategori_list=KATEGORI_PENGALAMAN)

    @app.context_processor
    def inject_unread():
        """Jumlah pesan belum dibaca untuk badge di sidebar admin."""
        if session.get("admin_id"):
            try:
                row = db.fetch_one("SELECT COUNT(*) AS n FROM pesan WHERE status='Belum Dibaca'")
                return {"belum_dibaca": row["n"] if row else 0}
            except Exception:
                return {"belum_dibaca": 0}
        return {}

    register_routes(app)
    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
