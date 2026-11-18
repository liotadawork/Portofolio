# Portofolio Pribadi Fuad Atoil — Flask + MySQL
![image alt](1_beranda_hero.jpg?raw=true)
## Akun admin awal


## 1. Menyalakan MySQL di XAMPP
1. Buka **XAMPP Control Panel** → klik **Start** pada **MySQL** (Apache boleh ikut dinyalakan untuk phpMyAdmin).
2. Port bawaan MySQL adalah 3306. Bila berbeda, set variabel `DB_PORT`.

## 2. Impor database lewat phpMyAdmin
1. Buka http://localhost/phpmyadmin
2. Klik tab **Import** → **Choose File** → pilih `database_portofolio.sql` → **Import/Kirim**.
3. Database `db_portofolio_fuad` beserta 4 tabel (admin, pengalaman, sertifikat, pesan) langsung dibuat. Tidak perlu membuat tabel manual.

## 3. Menjalankan aplikasi Flask
```bash
cd 066_FUADATOIL_P03/route
python -m venv .venv
.venv\Scripts\activate          # Windows   (Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
python app.py
```
Buka http://127.0.0.1:5000

Pengaturan database ada di `config.py`. Default: host 127.0.0.1, user `root`, password kosong (bawaan XAMPP).
Bila root XAMPP Anda memakai password, jalankan dengan `set DB_PASSWORD=passwordAnda` (Windows) sebelum `python app.py`.

## 4. Mengisi kontak
Edit dictionary `PROFILE` di `config.py` (email, whatsapp, domisili, linkedin). Nilai kosong tampil "Belum diisi".

## Struktur folder
```
route/
├── app.py              # pembuat app Flask, filter Jinja, CSRF
├── route.py            # semua route: publik, login, CRUD admin
├── config.py           # konfigurasi DB, upload, data profil/kontak
├── db.py               # koneksi MySQL terpusat (PyMySQL)
├── utils.py            # login_required, CSRF, validasi, upload gambar
├── database_portofolio.sql
├── requirements.txt
├── templates/
│   ├── base.html, _icons.html, _kartu.html, error.html
│   ├── index.html (Beranda)  about.html  skills.html
│   ├── projects.html (Pengalaman)  detail_pengalaman.html
│   ├── blog.html (Sertifikat & Pencapaian)  contact.html
│   └── admin/ login, dashboard, pengalaman, tambah/edit_pengalaman,
│              sertifikat, tambah/edit/detail_sertifikat, pesan, detail_pesan
└── static/
    ├── css/style.css  css/admin.css
    ├── js/main.js  js/admin.js
    ├── images/ (fotopp.jpeg, unu.png)
    └── uploads/pengalaman/  uploads/sertifikat/
```
Peta halaman lama → baru: Projects → **Pengalaman** (`/pengalaman`), Blog → **Sertifikat & Pencapaian** (`/sertifikat`). URL lama `/projects` dan `/blog` otomatis dialihkan.

## Foto pengalaman (lebih dari satu)
Tiap pengalaman punya 1 gambar utama (sampul) + maksimal 8 foto tambahan yang tampil sebagai galeri di halaman detail.
Jika database sudah diimpor sebelum fitur ini ada, jalankan `migrasi_foto_tambahan.sql` sekali di phpMyAdmin (tanpa menghapus data lama).
