# UkurGardu

Aplikasi web untuk mencatat hasil pengukuran beban gardu distribusi (trafo PLN),
menggantikan pencatatan manual via Google Sheets. Dibangun dengan Streamlit
supaya bisa diakses langsung lewat browser (tanpa install apa pun di sisi
pengguna) dan datanya bisa diunduh kapan saja sebagai CSV.

## Menjalankan secara lokal

```
pip install -r requirements.txt
streamlit run app.py
```

## Deploy agar mudah diakses tim lapangan

Push repo ini ke GitHub lalu deploy gratis di [Streamlit Community Cloud](https://streamlit.io/cloud)
— cukup arahkan ke `app.py`, dan tim lapangan tinggal buka link dari HP tanpa
instalasi apa pun.

## Cara kerja & penyimpanan data

- Setiap pengisian form pada tab **Input Pengukuran** ditambahkan sebagai satu
  baris ke `data/pengukuran_gardu.csv` di server (append-only, tidak menimpa data lama).
- Tab **Data & Unduh** menampilkan seluruh riwayat, bisa difilter berdasarkan
  Nomor Gardu/Penyulang/Unit, dan punya tombol unduh CSV — kapan saja, tanpa syarat.
- File CSV tidak ikut di-commit ke git (lihat `.gitignore`). Untuk hosting dengan
  disk permanen (VM/VPS sendiri), data akan terus terkumpul selama servernya jalan.
  Untuk hosting *ephemeral* (misalnya Streamlit Community Cloud versi gratis, yang
  bisa reset disk saat redeploy), disarankan rutin mengunduh CSV sebagai backup,
  atau ke depan mengganti storage ke Google Sheets API / database (lihat bagian
  "Pengembangan lanjutan").

## Struktur kolom

Kolom-kolom di bawah mengikuti struktur data Google Sheet yang sudah dipakai tim,
ditambah beberapa kolom yang saya lengkapi (ditandai *tambahan*) karena diperlukan
tapi belum ada di sheet asli.

| Kolom | Keterangan |
|---|---|
| `TIMESTAMP` | Waktu submit form, otomatis diisi server (format `DD/MM/YYYY HH.MM.SS`) |
| `TANGGAL` | Tanggal pengukuran sebenarnya di lapangan (diisi manual, bisa beda dari tanggal submit) |
| `ID` | ID unik, dibentuk otomatis: `KODE_UNIT.NOMOR_GARDU-yyyymmdd-hhmmss` dari waktu submit |
| `KODE UNIT` *(tambahan)* | Kode singkat unit/rayon (contoh `PGK`), dipakai untuk membentuk `ID` — di sheet asli kode ini tersirat di dalam `ID` tapi tidak ada kolom terpisah, jadi ditambahkan agar bisa diisi ulang & konsisten |
| `UNIT` | Nama unit/sub-unit (contoh `KUPRIK`) |
| `PENYULANG` | Nama penyulang |
| `NOMOR GARDU` | Nomor gardu distribusi |
| `LWBP/WBP` | Periode waktu pengukuran: Luar Waktu Beban Puncak / Waktu Beban Puncak |
| `KAPASITAS TRAFO KVA` | Kapasitas trafo (pilihan ukuran standar PLN: 25–630 kVA) |
| `JUMLAH JURUSAN` | Jumlah jurusan yang diukur (1–4), menentukan berapa blok Jurusan yang tampil di form |
| `R/S/T/N INDUK` | Arus (A) di sisi induk untuk fasa R, S, T, dan Netral |
| `R/S/T/N JURUSAN 1..4` | Arus (A) per jurusan untuk fasa R, S, T, dan Netral. Jurusan yang tidak diisi (melebihi `JUMLAH JURUSAN`) dikosongkan, sama seperti di sheet asli |
| `COS Q` | Faktor daya, diisi manual (default 0,9) — tidak bisa dihitung otomatis dari data arus saja karena butuh data sudut fasa/daya aktual |
| `% TIDAK SEIMBANG` | **Dihitung otomatis** — lihat rumus di bawah |
| `% BEBAN TRAFO` | **Dihitung otomatis** — lihat rumus di bawah |
| `KAPASITAS DERATING` | **Dihitung otomatis** — lihat rumus di bawah |
| `PETUGAS` *(tambahan)* | Nama petugas yang melakukan pengukuran, untuk akuntabilitas data |
| `KETERANGAN` *(tambahan)* | Catatan bebas/opsional (kondisi gardu, kendala pengukuran, dll) |

## Rumus kolom otomatis

Tiga kolom terakhir sebelumnya diisi manual di Google Sheet. Rumusnya ditelusuri
ulang dari data contoh yang diberikan dan cocok persis untuk ketiga baris contoh,
lalu diterapkan sebagai kalkulasi otomatis di aplikasi ini:

- **Arus rata-rata induk** `I_rata = (R + S + T) / 3` (dari arus fasa induk, N tidak diikutkan)
- **Arus nominal trafo** `I_nominal = (kVA × 1000) / (√3 × 380V)` — mengasumsikan tegangan
  sisi sekunder trafo 380V fasa-fasa (standar jaringan tegangan rendah PLN)
- **% TIDAK SEIMBANG** = `(max(R,S,T) − I_rata) / I_rata × 100`
- **% BEBAN TRAFO** = `I_rata / I_nominal × 100`
- **KAPASITAS DERATING** = `KAPASITAS TRAFO KVA × (I_rata / max(R,S,T))`

Semua dibulatkan ke bilangan bulat terdekat mengikuti format pada data contoh.

## Validasi

Kode Unit, Penyulang, dan Nomor Gardu wajib diisi sebelum data bisa disimpan.
Field lain boleh kosong jika memang belum ada nilainya di lapangan.

## Pengembangan lanjutan (saran, belum diimplementasikan)

- Integrasi ke Google Sheets API atau database (PostgreSQL/SQLite) agar data
  tidak bergantung pada disk lokal server.
- Upload foto gardu sebagai bukti pengukuran (seperti pola di aplikasi
  `tree_slice_inspection.py` pada repo RABAS).
- Autentikasi petugas (login) jika perlu membatasi siapa yang bisa input data.
