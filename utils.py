"""Fungsi bantu: autentikasi, CSRF, validasi, upload gambar, format tanggal."""
import hmac
import os
import re
import secrets
import uuid
from datetime import date, datetime
from functools import wraps

from flask import abort, current_app, flash, redirect, request, session, url_for
from werkzeug.utils import secure_filename

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
BULAN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]


# ---------------------------------------------------------------- Auth ----
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_id"):
            flash("Silakan login terlebih dahulu.", "error")
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)
    return wrapped


# ---------------------------------------------------------------- CSRF ----
def csrf_token():
    token = session.get("_csrf")
    if not token:
        token = secrets.token_hex(24)
        session["_csrf"] = token
    return token


def check_csrf():
    """Dipanggil sebelum setiap request POST."""
    if request.method == "POST":
        sent = request.form.get("csrf_token", "")
        expected = session.get("_csrf", "")
        if not expected or not hmac.compare_digest(sent, expected):
            abort(400, "Token CSRF tidak valid atau sesi kedaluwarsa. Muat ulang halaman lalu coba lagi.")


# ----------------------------------------------------------- Validasi ----
def valid_email(value):
    return bool(value) and len(value) <= 150 and bool(EMAIL_RE.match(value))


def parse_date(value):
    """'YYYY-MM-DD' -> date, atau None bila kosong/tidak valid."""
    try:
        return datetime.strptime((value or "").strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


# ------------------------------------------------------ Format tanggal ----
def _to_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value:
        try:
            return datetime.strptime(value[:10], "%Y-%m-%d").date()
        except ValueError:
            return None
    return None


def tgl(value, full=False):
    d = _to_date(value)
    if not d:
        return "-"
    if full:
        return f"{d.day} {BULAN[d.month - 1]} {d.year}"
    return f"{BULAN[d.month - 1]} {d.year}"


def tgl_lengkap(value):
    return tgl(value, full=True)


def tgl_waktu(value):
    if isinstance(value, str):
        try:
            value = datetime.strptime(value[:19], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return value
    if isinstance(value, datetime):
        return f"{value.day} {BULAN[value.month - 1]} {value.year}, {value:%H:%M}"
    return "-"


def periode(mulai, selesai):
    return f"{tgl(mulai)} — {tgl(selesai) if selesai else 'Sekarang'}"


# --------------------------------------------------------------- Upload ----
_MAGIC = {
    "jpg": lambda h: h[:3] == b"\xff\xd8\xff",
    "jpeg": lambda h: h[:3] == b"\xff\xd8\xff",
    "png": lambda h: h[:8] == b"\x89PNG\r\n\x1a\n",
    "webp": lambda h: h[:4] == b"RIFF" and h[8:12] == b"WEBP",
}


def _folder(sub):
    path = os.path.join(current_app.config["UPLOAD_FOLDER"], sub)
    os.makedirs(path, exist_ok=True)
    return path


def save_image(file_storage, sub):
    """Validasi & simpan gambar. Return (nama_file, error)."""
    if file_storage is None or not file_storage.filename:
        return None, None
    ext = secure_filename(file_storage.filename).rsplit(".", 1)[-1].lower() if "." in file_storage.filename else ""
    if ext not in current_app.config["ALLOWED_EXTENSIONS"]:
        return None, "Format gambar harus JPG, JPEG, PNG, atau WEBP."
    data = file_storage.read(current_app.config["MAX_IMAGE_BYTES"] + 1)
    if len(data) > current_app.config["MAX_IMAGE_BYTES"]:
        mb = current_app.config["MAX_IMAGE_BYTES"] // (1024 * 1024)
        return None, f"Ukuran gambar maksimal {mb} MB."
    if not data or not _MAGIC[ext](data[:12]):
        return None, "Isi file bukan gambar yang valid."
    name = f"{uuid.uuid4().hex}.{ext}"
    with open(os.path.join(_folder(sub), name), "wb") as fh:
        fh.write(data)
    return name, None


def delete_image(sub, name):
    """Hapus file gambar dengan aman (mencegah path traversal)."""
    if not name:
        return
    base = os.path.realpath(_folder(sub))
    target = os.path.realpath(os.path.join(base, os.path.basename(name)))
    if target.startswith(base + os.sep) and os.path.isfile(target):
        try:
            os.remove(target)
        except OSError:
            current_app.logger.warning("Gagal menghapus file %s", target)
