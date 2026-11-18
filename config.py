"""Konfigurasi terpusat aplikasi portofolio Fuad Atoil.

Semua nilai dapat di-override lewat environment variable, sehingga file ini
tidak perlu diubah saat dipindah ke komputer / server lain.
Default di bawah cocok untuk MySQL bawaan XAMPP (user root, tanpa password).
"""
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # --- Keamanan -----------------------------------------------------------
    # GANTI SECRET_KEY sebelum aplikasi dipublikasikan.
    SECRET_KEY = os.environ.get("SECRET_KEY", "ganti-dengan-kunci-rahasia-yang-panjang-dan-acak")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 8  # sesi admin 8 jam

    # --- Database MySQL (XAMPP) --------------------------------------------
    DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
    DB_PORT = int(os.environ.get("DB_PORT", "3306"))
    DB_USER = os.environ.get("DB_USER", "root")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
    DB_NAME = os.environ.get("DB_NAME", "db_portofolio_fuad")

    # --- Upload gambar -------------------------------------------------------
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
    MAX_IMAGE_BYTES = 2 * 1024 * 1024          # batas per gambar: 2 MB
    MAX_CONTENT_LENGTH = 20 * 1024 * 1024      # batas total request: 20 MB
    MAX_FOTO_TAMBAHAN = 8                      # maksimal foto tambahan per pengalaman


# Data profil & kontak yang tampil di website.
# Isi / ubah di sini. Nilai kosong ("") akan tampil sebagai "Belum diisi".
PROFILE = {
    "nama": "Fuad Atoil",
    "status": "Mahasiswa Informatika",
    "kampus": "Universitas Nahdlatul Ulama Yogyakarta",
    "foto": "images/fotopp.jpeg",
    "email": "fuadatoilwork@gmail.com",                                   # contoh: "fuad@email.com"
    "whatsapp": "628888254662",                                # format internasional tanpa +, contoh: "6281234567890"
    "domisili": "DI Yogyakarta",                                # contoh: "Yogyakarta"
    "instagram": "fuaddddddd_",                     # username tanpa @
    "linkedin": "",                                # URL profil LinkedIn lengkap
    "github": "https://github.com/liotadawork",    # URL profil GitHub
}

KATEGORI_PENGALAMAN = ["Pekerjaan", "Magang", "Organisasi", "Kegiatan", "Akademik"]
STATUS_PESAN = ("Belum Dibaca", "Sudah Dibaca")
