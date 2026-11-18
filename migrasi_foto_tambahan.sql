-- Jalankan SEKALI jika database db_portofolio_fuad sudah terlanjur diimpor sebelumnya
-- (data lama tidak terhapus). phpMyAdmin: pilih db_portofolio_fuad -> tab Import / SQL.
USE db_portofolio_fuad;
CREATE TABLE IF NOT EXISTS pengalaman_gambar (
  id_gambar     INT UNSIGNED NOT NULL AUTO_INCREMENT,
  id_pengalaman INT UNSIGNED NOT NULL,
  gambar        VARCHAR(255) NOT NULL COMMENT 'nama file di static/uploads/pengalaman/',
  created_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id_gambar),
  KEY idx_pg_pengalaman (id_pengalaman),
  CONSTRAINT fk_pg_pengalaman FOREIGN KEY (id_pengalaman)
    REFERENCES pengalaman (id_pengalaman) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
