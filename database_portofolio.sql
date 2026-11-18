-- ============================================================================
--  database_portofolio.sql  —  Portofolio Fuad Atoil (Flask + MySQL)
--  Import lewat phpMyAdmin: tab "Import" -> pilih file ini -> "Go/Kirim".
--  File ini membuat database, semua tabel, akun admin, dan data awal.
-- ============================================================================

CREATE DATABASE IF NOT EXISTS db_portofolio_fuad
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE db_portofolio_fuad;

SET NAMES utf8mb4;

DROP TABLE IF EXISTS pengalaman_gambar;
DROP TABLE IF EXISTS pesan;
DROP TABLE IF EXISTS sertifikat;
DROP TABLE IF EXISTS pengalaman;
DROP TABLE IF EXISTS admin;

-- ---------------------------------------------------------------- admin ----
CREATE TABLE admin (
  id_admin   INT UNSIGNED NOT NULL AUTO_INCREMENT,
  username   VARCHAR(50)  NOT NULL,
  password   VARCHAR(255) NOT NULL COMMENT 'hash Werkzeug (pbkdf2:sha256), bukan teks biasa',
  created_at TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id_admin),
  UNIQUE KEY uq_admin_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------ pengalaman ----
CREATE TABLE pengalaman (
  id_pengalaman   INT UNSIGNED NOT NULL AUTO_INCREMENT,
  judul           VARCHAR(150) NOT NULL,
  posisi          VARCHAR(100) NOT NULL,
  instansi        VARCHAR(150) NOT NULL,
  kategori        ENUM('Pekerjaan','Magang','Organisasi','Kegiatan','Akademik') NOT NULL DEFAULT 'Kegiatan',
  tanggal_mulai   DATE         NOT NULL,
  tanggal_selesai DATE         NULL DEFAULT NULL COMMENT 'NULL = masih berjalan',
  deskripsi       TEXT         NOT NULL,
  gambar          VARCHAR(255) NULL DEFAULT NULL COMMENT 'nama file di static/uploads/pengalaman/',
  created_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id_pengalaman),
  KEY idx_pengalaman_kategori (kategori),
  KEY idx_pengalaman_mulai (tanggal_mulai)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------- foto tambahan pengalaman ----
CREATE TABLE pengalaman_gambar (
  id_gambar     INT UNSIGNED NOT NULL AUTO_INCREMENT,
  id_pengalaman INT UNSIGNED NOT NULL,
  gambar        VARCHAR(255) NOT NULL COMMENT 'nama file di static/uploads/pengalaman/',
  created_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id_gambar),
  KEY idx_pg_pengalaman (id_pengalaman),
  CONSTRAINT fk_pg_pengalaman FOREIGN KEY (id_pengalaman)
    REFERENCES pengalaman (id_pengalaman) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------ sertifikat ----
CREATE TABLE sertifikat (
  id_sertifikat   INT UNSIGNED NOT NULL AUTO_INCREMENT,
  nama_sertifikat VARCHAR(150) NOT NULL,
  penyelenggara   VARCHAR(150) NOT NULL,
  tanggal         DATE         NOT NULL,
  deskripsi       TEXT         NOT NULL,
  gambar          VARCHAR(255) NULL DEFAULT NULL COMMENT 'nama file di static/uploads/sertifikat/',
  created_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id_sertifikat),
  KEY idx_sertifikat_tanggal (tanggal)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------- pesan ----
CREATE TABLE pesan (
  id_pesan   INT UNSIGNED NOT NULL AUTO_INCREMENT,
  nama       VARCHAR(100) NOT NULL,
  email      VARCHAR(150) NOT NULL,
  subjek     VARCHAR(150) NOT NULL,
  isi_pesan  TEXT         NOT NULL,
  status     ENUM('Belum Dibaca','Sudah Dibaca') NOT NULL DEFAULT 'Belum Dibaca',
  created_at TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id_pesan),
  KEY idx_pesan_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------ data awal ----
-- Akun admin awal  ->  username: admin   |   password: Fuad@2026!
-- (password tersimpan dalam bentuk hash; segera ganti setelah dipakai)
INSERT INTO admin (username, password) VALUES
('admin', 'pbkdf2:sha256:600000$ERMq03quuVZ2AzFJ$c9a86cd080778454e8a48be91f5a3dda2735b3b36df4e4d7d361cf32de132d25');

-- Data contoh pengalaman (hanya fakta dari laporan praktikum; ubah/tambah lewat dashboard admin)
INSERT INTO pengalaman (judul, posisi, instansi, kategori, tanggal_mulai, tanggal_selesai, deskripsi, gambar) VALUES
('Mahasiswa Informatika', 'Mahasiswa', 'Universitas Nahdlatul Ulama Yogyakarta', 'Akademik', '2025-09-01', NULL,
 'Menempuh pendidikan di Program Studi Informatika, Fakultas Teknologi Informasi, Universitas Nahdlatul Ulama Yogyakarta. Fokus mempelajari pemrograman web, basis data, dan perancangan antarmuka.', NULL),
('Praktikum Pemrograman Web: Portofolio Pribadi', 'Praktikan', 'Praktikum Pemrograman Web, Informatika UNU Yogyakarta', 'Akademik', '2026-10-01', NULL,
 'Membangun website portofolio pribadi menggunakan Python Flask, HTML, dan CSS pada praktikum Pemrograman Web Semester Ganjil 2026/2027, lalu mengembangkannya menjadi website dinamis dengan database MySQL dan dashboard admin.', NULL);
