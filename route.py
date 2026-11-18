"""Seluruh route aplikasi: halaman publik, login admin, dan CRUD admin."""
import time

import pymysql
from flask import (abort, flash, redirect, render_template, request, session,
                   url_for)
from werkzeug.security import check_password_hash

import db
from config import KATEGORI_PENGALAMAN, STATUS_PESAN
from utils import (delete_image, login_required, parse_date, save_image,
                   valid_email)

_FAILED = {}  # ip -> (jumlah_gagal, waktu_buka_kunci)  — pembatas percobaan login
MAX_TRY, LOCK_SECONDS = 5, 60


def safe_rows(sql, params=(), one=False):
    """Query untuk halaman publik: bila database mati, halaman tetap tampil."""
    try:
        return db.fetch_one(sql, params) if one else db.fetch_all(sql, params)
    except pymysql.MySQLError:
        from flask import current_app
        current_app.logger.exception("Query gagal")
        flash("Database belum terhubung. Data dinamis sementara tidak dapat ditampilkan.", "error")
        return None if one else []


def kumpulkan_foto_tambahan(sudah_ada=0):
    """Validasi & simpan semua foto tambahan dari form. Return (daftar_nama, errors)."""
    from flask import current_app
    files = [f for f in request.files.getlist("foto_tambahan") if f and f.filename]
    batas = current_app.config["MAX_FOTO_TAMBAHAN"]
    if sudah_ada + len(files) > batas:
        return [], [f"Foto tambahan maksimal {batas} per pengalaman (saat ini {sudah_ada} + {len(files)} baru)."]
    names, errors = [], []
    for f in files:
        nama, err = save_image(f, "pengalaman")
        if err:
            errors.append(f"{f.filename}: {err}")
        elif nama:
            names.append(nama)
    if errors:
        for n in names:
            delete_image("pengalaman", n)
        return [], errors
    return names, []


def foto_tambahan_pengalaman(id_pengalaman):
    return safe_rows("SELECT * FROM pengalaman_gambar WHERE id_pengalaman=%s ORDER BY id_gambar", (id_pengalaman,))


def register_routes(app):

    # ============================================================ PUBLIK ====
    @app.route("/")
    def home():
        pengalaman = safe_rows("SELECT * FROM pengalaman ORDER BY tanggal_mulai DESC, id_pengalaman DESC LIMIT 3")
        sertifikat = safe_rows("SELECT * FROM sertifikat ORDER BY tanggal DESC, id_sertifikat DESC LIMIT 3")
        return render_template("index.html", pengalaman=pengalaman, sertifikat=sertifikat)

    @app.route("/about")
    def about():
        return render_template("about.html")

    @app.route("/skills")
    def skills():
        return render_template("skills.html")

    # "Projects" diubah menjadi "Pengalaman" (nama endpoint 'projects' dipertahankan)
    @app.route("/pengalaman")
    def projects():
        kategori = request.args.get("kategori", "")
        if kategori in KATEGORI_PENGALAMAN:
            rows = safe_rows("SELECT * FROM pengalaman WHERE kategori=%s ORDER BY tanggal_mulai DESC, id_pengalaman DESC", (kategori,))
        else:
            kategori = ""
            rows = safe_rows("SELECT * FROM pengalaman ORDER BY tanggal_mulai DESC, id_pengalaman DESC")
        return render_template("projects.html", pengalaman=rows, kategori=kategori)

    @app.route("/projects")
    def projects_lama():
        return redirect(url_for("projects"), 301)

    @app.route("/pengalaman/<int:id_pengalaman>")
    def detail_pengalaman_publik(id_pengalaman):
        row = safe_rows("SELECT * FROM pengalaman WHERE id_pengalaman=%s", (id_pengalaman,), one=True)
        if not row:
            abort(404)
        return render_template("detail_pengalaman.html", p=row, galeri=foto_tambahan_pengalaman(id_pengalaman))

    # "Blog" diubah menjadi "Sertifikat & Pencapaian" (endpoint 'blog' dipertahankan)
    @app.route("/sertifikat")
    def blog():
        rows = safe_rows("SELECT * FROM sertifikat ORDER BY tanggal DESC, id_sertifikat DESC")
        return render_template("blog.html", sertifikat=rows)

    @app.route("/blog")
    def blog_lama():
        return redirect(url_for("blog"), 301)

    @app.route("/contact", methods=["GET", "POST"])
    def contact():
        if request.method == "POST":
            data = {k: request.form.get(k, "").strip() for k in ("nama", "email", "subjek", "pesan")}
            errors = []
            if request.form.get("website"):  # honeypot anti-bot
                return redirect(url_for("contact"))
            if not all(data.values()):
                errors.append("Semua kolom wajib diisi.")
            else:
                if not 2 <= len(data["nama"]) <= 100:
                    errors.append("Nama harus 2–100 karakter.")
                if not valid_email(data["email"]):
                    errors.append("Format email tidak valid.")
                if not 3 <= len(data["subjek"]) <= 150:
                    errors.append("Subjek harus 3–150 karakter.")
                if not 10 <= len(data["pesan"]) <= 3000:
                    errors.append("Pesan harus 10–3000 karakter.")
            if errors:
                for e in errors:
                    flash(e, "error")
                session["form_kontak"] = data
                return redirect(url_for("contact") + "#kirim-pesan")
            try:
                db.execute(
                    "INSERT INTO pesan (nama, email, subjek, isi_pesan, status) VALUES (%s,%s,%s,%s,%s)",
                    (data["nama"], data["email"], data["subjek"], data["pesan"], "Belum Dibaca"),
                )
            except pymysql.MySQLError:
                app.logger.exception("Gagal menyimpan pesan")
                flash("Pesan gagal dikirim karena masalah database. Silakan coba lagi nanti.", "error")
                session["form_kontak"] = data
                return redirect(url_for("contact") + "#kirim-pesan")
            flash("Terima kasih! Pesan Anda berhasil dikirim.", "success")
            return redirect(url_for("contact") + "#kirim-pesan")
        form = session.pop("form_kontak", {})
        return render_template("contact.html", form=form)

    # ======================================================== AUTH ADMIN ====
    @app.route("/admin/login", methods=["GET", "POST"])
    def admin_login():
        if session.get("admin_id"):
            return redirect(url_for("admin_dashboard"))
        if request.method == "POST":
            ip = request.remote_addr or "?"
            count, until = _FAILED.get(ip, (0, 0))
            if until > time.time():
                flash(f"Terlalu banyak percobaan. Coba lagi dalam {int(until - time.time()) + 1} detik.", "error")
                return redirect(url_for("admin_login"))
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            if not username or not password:
                flash("Username dan password wajib diisi.", "error")
                return redirect(url_for("admin_login"))
            try:
                admin = db.fetch_one("SELECT * FROM admin WHERE username=%s", (username,))
            except pymysql.MySQLError:
                app.logger.exception("Login: database error")
                flash("Tidak dapat terhubung ke database.", "error")
                return redirect(url_for("admin_login"))
            if admin and check_password_hash(admin["password"], password):
                _FAILED.pop(ip, None)
                session.clear()
                session.permanent = True
                session["admin_id"] = admin["id_admin"]
                session["admin_username"] = admin["username"]
                flash(f"Selamat datang, {admin['username']}!", "success")
                return redirect(url_for("admin_dashboard"))
            count += 1
            _FAILED[ip] = (count, time.time() + LOCK_SECONDS if count >= MAX_TRY else 0)
            if count >= MAX_TRY:
                _FAILED[ip] = (0, time.time() + LOCK_SECONDS)
            flash("Username atau password salah.", "error")
            return redirect(url_for("admin_login"))
        return render_template("admin/login.html")

    @app.route("/admin/logout", methods=["POST"])
    def admin_logout():
        session.clear()
        flash("Anda telah logout.", "success")
        return redirect(url_for("admin_login"))

    # ===================================================== DASHBOARD ========
    @app.route("/admin")
    @app.route("/admin/dashboard")
    @login_required
    def admin_dashboard():
        stat = db.fetch_one(
            "SELECT (SELECT COUNT(*) FROM pengalaman) AS pengalaman,"
            " (SELECT COUNT(*) FROM sertifikat) AS sertifikat,"
            " (SELECT COUNT(*) FROM pesan) AS pesan,"
            " (SELECT COUNT(*) FROM pesan WHERE status='Belum Dibaca') AS belum"
        )
        pesan = db.fetch_all("SELECT * FROM pesan ORDER BY created_at DESC, id_pesan DESC LIMIT 5")
        pengalaman = db.fetch_all("SELECT * FROM pengalaman ORDER BY created_at DESC, id_pengalaman DESC LIMIT 4")
        return render_template("admin/dashboard.html", stat=stat, pesan=pesan, pengalaman=pengalaman)

    # ================================================ CRUD PENGALAMAN =======
    def _form_pengalaman():
        f = {k: request.form.get(k, "").strip() for k in
             ("judul", "posisi", "instansi", "kategori", "tanggal_mulai", "tanggal_selesai", "deskripsi")}
        errors = []
        if not 3 <= len(f["judul"]) <= 150:
            errors.append("Judul wajib diisi (3–150 karakter).")
        if not 2 <= len(f["posisi"]) <= 100:
            errors.append("Posisi / jabatan wajib diisi (2–100 karakter).")
        if not 2 <= len(f["instansi"]) <= 150:
            errors.append("Instansi / organisasi wajib diisi (2–150 karakter).")
        if f["kategori"] not in KATEGORI_PENGALAMAN:
            errors.append("Kategori tidak valid.")
        mulai = parse_date(f["tanggal_mulai"])
        selesai = parse_date(f["tanggal_selesai"]) if f["tanggal_selesai"] else None
        if not mulai:
            errors.append("Tanggal mulai wajib diisi dengan benar.")
        if f["tanggal_selesai"] and not selesai:
            errors.append("Tanggal selesai tidak valid.")
        if mulai and selesai and selesai < mulai:
            errors.append("Tanggal selesai tidak boleh sebelum tanggal mulai.")
        if len(f["deskripsi"]) < 10:
            errors.append("Deskripsi minimal 10 karakter.")
        return f, mulai, selesai, errors

    @app.route("/admin/pengalaman")
    @login_required
    def admin_pengalaman():
        rows = db.fetch_all("SELECT * FROM pengalaman ORDER BY tanggal_mulai DESC, id_pengalaman DESC")
        return render_template("admin/pengalaman.html", rows=rows)

    @app.route("/admin/pengalaman/tambah", methods=["GET", "POST"])
    @login_required
    def admin_tambah_pengalaman():
        if request.method == "POST":
            f, mulai, selesai, errors = _form_pengalaman()
            nama, err = save_image(request.files.get("gambar"), "pengalaman")
            if err:
                errors.append(err)
            extras, err_extra = kumpulkan_foto_tambahan(0)
            errors += err_extra
            if errors:
                delete_image("pengalaman", nama)
                for n in extras:
                    delete_image("pengalaman", n)
                return render_template("admin/tambah_pengalaman.html", f=f, errors=errors, extras=[]), 422
            new_id = db.execute(
                "INSERT INTO pengalaman (judul,posisi,instansi,kategori,tanggal_mulai,tanggal_selesai,deskripsi,gambar)"
                " VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                (f["judul"], f["posisi"], f["instansi"], f["kategori"], mulai, selesai, f["deskripsi"], nama),
            )
            for n in extras:
                db.execute("INSERT INTO pengalaman_gambar (id_pengalaman, gambar) VALUES (%s,%s)", (new_id, n))
            flash("Pengalaman berhasil ditambahkan.", "success")
            return redirect(url_for("admin_pengalaman"))
        return render_template("admin/tambah_pengalaman.html", f={}, errors=[], extras=[])

    @app.route("/admin/pengalaman/<int:id_>/edit", methods=["GET", "POST"])
    @login_required
    def admin_edit_pengalaman(id_):
        row = db.fetch_one("SELECT * FROM pengalaman WHERE id_pengalaman=%s", (id_,))
        if not row:
            abort(404)
        extras_lama = db.fetch_all("SELECT * FROM pengalaman_gambar WHERE id_pengalaman=%s ORDER BY id_gambar", (id_,))
        if request.method == "POST":
            f, mulai, selesai, errors = _form_pengalaman()
            nama, err = save_image(request.files.get("gambar"), "pengalaman")
            if err:
                errors.append(err)
            hapus_ids = {int(x) for x in request.form.getlist("hapus_foto") if x.isdigit()}
            hapus_rows = [e for e in extras_lama if e["id_gambar"] in hapus_ids]
            extras_baru, err_extra = kumpulkan_foto_tambahan(len(extras_lama) - len(hapus_rows))
            errors += err_extra
            if errors:
                delete_image("pengalaman", nama)
                for n in extras_baru:
                    delete_image("pengalaman", n)
                merged = dict(row, **f)
                return render_template("admin/edit_pengalaman.html", p=row, f=merged, errors=errors, extras=extras_lama), 422
            gambar = row["gambar"]
            if nama:                                   # ganti gambar utama
                delete_image("pengalaman", gambar)
                gambar = nama
            elif request.form.get("hapus_gambar"):     # hapus gambar utama saja
                delete_image("pengalaman", gambar)
                gambar = None
            db.execute(
                "UPDATE pengalaman SET judul=%s,posisi=%s,instansi=%s,kategori=%s,tanggal_mulai=%s,"
                "tanggal_selesai=%s,deskripsi=%s,gambar=%s WHERE id_pengalaman=%s",
                (f["judul"], f["posisi"], f["instansi"], f["kategori"], mulai, selesai, f["deskripsi"], gambar, id_),
            )
            for e in hapus_rows:                       # hapus foto tambahan terpilih
                db.execute("DELETE FROM pengalaman_gambar WHERE id_gambar=%s AND id_pengalaman=%s", (e["id_gambar"], id_))
                delete_image("pengalaman", e["gambar"])
            for n in extras_baru:
                db.execute("INSERT INTO pengalaman_gambar (id_pengalaman, gambar) VALUES (%s,%s)", (id_, n))
            flash("Pengalaman berhasil diperbarui.", "success")
            return redirect(url_for("admin_pengalaman"))
        return render_template("admin/edit_pengalaman.html", p=row, f=row, errors=[], extras=extras_lama)

    @app.route("/admin/pengalaman/<int:id_>/hapus", methods=["POST"])
    @login_required
    def admin_hapus_pengalaman(id_):
        row = db.fetch_one("SELECT gambar FROM pengalaman WHERE id_pengalaman=%s", (id_,))
        if not row:
            abort(404)
        extras = db.fetch_all("SELECT gambar FROM pengalaman_gambar WHERE id_pengalaman=%s", (id_,))
        db.execute("DELETE FROM pengalaman_gambar WHERE id_pengalaman=%s", (id_,))
        db.execute("DELETE FROM pengalaman WHERE id_pengalaman=%s", (id_,))
        delete_image("pengalaman", row["gambar"])
        for e in extras:
            delete_image("pengalaman", e["gambar"])
        flash("Pengalaman dan gambar terkait berhasil dihapus.", "success")
        return redirect(url_for("admin_pengalaman"))

    # ================================================= CRUD SERTIFIKAT ======
    def _form_sertifikat():
        f = {k: request.form.get(k, "").strip() for k in ("nama_sertifikat", "penyelenggara", "tanggal", "deskripsi")}
        errors = []
        if not 3 <= len(f["nama_sertifikat"]) <= 150:
            errors.append("Nama sertifikat wajib diisi (3–150 karakter).")
        if not 2 <= len(f["penyelenggara"]) <= 150:
            errors.append("Penyelenggara wajib diisi (2–150 karakter).")
        tanggal = parse_date(f["tanggal"])
        if not tanggal:
            errors.append("Tanggal diperoleh wajib diisi dengan benar.")
        if len(f["deskripsi"]) < 5:
            errors.append("Deskripsi singkat minimal 5 karakter.")
        return f, tanggal, errors

    @app.route("/admin/sertifikat")
    @login_required
    def admin_sertifikat():
        rows = db.fetch_all("SELECT * FROM sertifikat ORDER BY tanggal DESC, id_sertifikat DESC")
        return render_template("admin/sertifikat.html", rows=rows)

    @app.route("/admin/sertifikat/<int:id_>")
    @login_required
    def admin_detail_sertifikat(id_):
        row = db.fetch_one("SELECT * FROM sertifikat WHERE id_sertifikat=%s", (id_,))
        if not row:
            abort(404)
        return render_template("admin/detail_sertifikat.html", s=row)

    @app.route("/admin/sertifikat/tambah", methods=["GET", "POST"])
    @login_required
    def admin_tambah_sertifikat():
        if request.method == "POST":
            f, tanggal, errors = _form_sertifikat()
            nama, err = save_image(request.files.get("gambar"), "sertifikat")
            if err:
                errors.append(err)
            if errors:
                delete_image("sertifikat", nama)
                return render_template("admin/tambah_sertifikat.html", f=f, errors=errors), 422
            db.execute(
                "INSERT INTO sertifikat (nama_sertifikat,penyelenggara,tanggal,deskripsi,gambar) VALUES (%s,%s,%s,%s,%s)",
                (f["nama_sertifikat"], f["penyelenggara"], tanggal, f["deskripsi"], nama),
            )
            flash("Sertifikat berhasil ditambahkan.", "success")
            return redirect(url_for("admin_sertifikat"))
        return render_template("admin/tambah_sertifikat.html", f={}, errors=[])

    @app.route("/admin/sertifikat/<int:id_>/edit", methods=["GET", "POST"])
    @login_required
    def admin_edit_sertifikat(id_):
        row = db.fetch_one("SELECT * FROM sertifikat WHERE id_sertifikat=%s", (id_,))
        if not row:
            abort(404)
        if request.method == "POST":
            f, tanggal, errors = _form_sertifikat()
            nama, err = save_image(request.files.get("gambar"), "sertifikat")
            if err:
                errors.append(err)
            if errors:
                delete_image("sertifikat", nama)
                return render_template("admin/edit_sertifikat.html", s=row, f=dict(row, **f), errors=errors), 422
            gambar = row["gambar"]
            if nama:
                delete_image("sertifikat", gambar)
                gambar = nama
            elif request.form.get("hapus_gambar"):
                delete_image("sertifikat", gambar)
                gambar = None
            db.execute(
                "UPDATE sertifikat SET nama_sertifikat=%s,penyelenggara=%s,tanggal=%s,deskripsi=%s,gambar=%s"
                " WHERE id_sertifikat=%s",
                (f["nama_sertifikat"], f["penyelenggara"], tanggal, f["deskripsi"], gambar, id_),
            )
            flash("Sertifikat berhasil diperbarui.", "success")
            return redirect(url_for("admin_sertifikat"))
        return render_template("admin/edit_sertifikat.html", s=row, f=row, errors=[])

    @app.route("/admin/sertifikat/<int:id_>/hapus", methods=["POST"])
    @login_required
    def admin_hapus_sertifikat(id_):
        row = db.fetch_one("SELECT gambar FROM sertifikat WHERE id_sertifikat=%s", (id_,))
        if not row:
            abort(404)
        db.execute("DELETE FROM sertifikat WHERE id_sertifikat=%s", (id_,))
        delete_image("sertifikat", row["gambar"])
        flash("Sertifikat dan gambar terkait berhasil dihapus.", "success")
        return redirect(url_for("admin_sertifikat"))

    # ===================================================== PESAN MASUK ======
    @app.route("/admin/pesan")
    @login_required
    def admin_pesan():
        filt = request.args.get("status", "")
        if filt in STATUS_PESAN:
            rows = db.fetch_all("SELECT * FROM pesan WHERE status=%s ORDER BY created_at DESC, id_pesan DESC", (filt,))
        else:
            filt = ""
            rows = db.fetch_all("SELECT * FROM pesan ORDER BY created_at DESC, id_pesan DESC")
        return render_template("admin/pesan.html", rows=rows, filt=filt)

    @app.route("/admin/pesan/<int:id_>")
    @login_required
    def admin_detail_pesan(id_):
        row = db.fetch_one("SELECT * FROM pesan WHERE id_pesan=%s", (id_,))
        if not row:
            abort(404)
        if row["status"] == "Belum Dibaca":  # otomatis ditandai dibaca saat dibuka
            db.execute("UPDATE pesan SET status='Sudah Dibaca' WHERE id_pesan=%s", (id_,))
            row["status"] = "Sudah Dibaca"
        return render_template("admin/detail_pesan.html", m=row)

    @app.route("/admin/pesan/<int:id_>/status", methods=["POST"])
    @login_required
    def admin_status_pesan(id_):
        status = request.form.get("status", "")
        if status not in STATUS_PESAN:
            abort(400)
        if not db.fetch_one("SELECT id_pesan FROM pesan WHERE id_pesan=%s", (id_,)):
            abort(404)
        db.execute("UPDATE pesan SET status=%s WHERE id_pesan=%s", (status, id_))
        flash(f"Status pesan diubah menjadi “{status}”.", "success")
        back = request.form.get("kembali")
        return redirect(url_for("admin_detail_pesan", id_=id_) if back == "detail" else url_for("admin_pesan"))

    @app.route("/admin/pesan/<int:id_>/hapus", methods=["POST"])
    @login_required
    def admin_hapus_pesan(id_):
        if not db.fetch_one("SELECT id_pesan FROM pesan WHERE id_pesan=%s", (id_,)):
            abort(404)
        db.execute("DELETE FROM pesan WHERE id_pesan=%s", (id_,))
        flash("Pesan berhasil dihapus.", "success")
        return redirect(url_for("admin_pesan"))

    # ============================================================ ERROR =====
    @app.errorhandler(404)
    def not_found(_e):
        return render_template("error.html", kode=404, judul="Halaman tidak ditemukan",
                               pesan="Alamat yang Anda tuju tidak tersedia atau sudah dipindahkan."), 404

    @app.errorhandler(400)
    def bad_request(e):
        return render_template("error.html", kode=400, judul="Permintaan tidak valid",
                               pesan=getattr(e, "description", "Permintaan tidak dapat diproses.")), 400

    @app.errorhandler(413)
    def too_large(_e):
        flash("Ukuran file terlalu besar (maksimal total 20 MB, per gambar 2 MB).", "error")
        return redirect(request.referrer or url_for("home"))

    @app.errorhandler(pymysql.MySQLError)
    def db_error(e):
        app.logger.exception("Database error")
        return render_template("error.html", kode=500, judul="Database bermasalah",
                               pesan="Tidak dapat terhubung ke MySQL. Pastikan MySQL di XAMPP aktif "
                                     "dan database db_portofolio_fuad sudah diimpor."), 500
