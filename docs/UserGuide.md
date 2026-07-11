# User Guide v2.0 — Lexa Customer Service Chatbot

**Project:** SH04-AI-Chatbot-LEXA  
**Version:** 2.0.0  
**Last Updated:** 2026-07-10  
**Changelog:** Panduan diperbarui untuk arsitektur baru (FastAPI backend + RAG + upload dokumen)

---

## Selamat Datang di Lexa v2.0 💬

Lexa adalah asisten customer service berbasis AI yang kini hadir dengan kemampuan yang jauh lebih canggih:

| Fitur | v1.0 | v2.0 |
|-------|------|------|
| Chat AI (Groq) | ✅ | ✅ |
| Riwayat Chat Permanen | ❌ | ✅ SQLite |
| Basis Pengetahuan (RAG) | ❌ | ✅ |
| Upload Dokumen PDF | ❌ | ✅ |
| Referensi Sumber Jawaban | ❌ | ✅ |
| Multi-sesi | ❌ | ✅ |
| REST API Backend | ❌ | ✅ FastAPI |

---

## Cara Menjalankan Aplikasi

### ⚠️ Penting: Backend Harus Jalan Lebih Dulu

Lexa v2.0 terdiri dari dua komponen yang harus dijalankan secara terpisah:

**Terminal 1 — Jalankan Backend:**
```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Tunggu hingga muncul:
```
RAG basis pengetahuan dimuat!
INFO: Uvicorn running on http://127.0.0.1:8000
```

**Terminal 2 — Jalankan Frontend:**
```bash
streamlit run app.py
```

Browser otomatis terbuka di `http://localhost:8501`.

**Opsional — Terminal 3 (CLI):**
```bash
python main.py
```

---

## Mode 1: Browser Interface (Streamlit)

### Tampilan Antarmuka

```
┌─────────────────┬─────────────────────────────────────────┐
│ SIDEBAR         │  💬 Lexa Customer Service                │
│─────────────────│  ─────────────────────────────────────  │
│ 🤖 Lexa         │                                          │
│ CS Control Panel│  [User] Halo Lexa                       │
│                 │  [Lexa] Halo! Ada yang bisa saya bantu? │
│ Upload Dokumen  │                                          │
│ [📄 pilih file] │  [User] Berapa harga paket Pro?         │
│                 │  [Lexa] Harga Paket Pro adalah Rp...    │
│ Dokumen Aktif:  │  ▼ 📚 Referensi Basis Pengetahuan       │
│ • warranty.pdf  │    1. pricing.md | Score: 0.74          │
│                 │                                          │
│ [Rebuild Index] │  ┌─ Ada yang bisa saya bantu hari ini? ─┐│
│ [Reset Chat]    │  └────────────────────────────────────┘ │
└─────────────────┴─────────────────────────────────────────┘
```

---

### Cara Chat

1. Ketik pesan di kotak input bawah → tekan **Enter**.
2. Lexa menjawab secara **streaming** (teks muncul bertahap).
3. Jika ada dokumen relevan, **referensi sumber** muncul di bawah jawaban.
4. Riwayat percakapan **tersimpan permanen** — tidak hilang saat refresh.

---

### Fitur Upload Dokumen (Basis Pengetahuan Sementara)

Upload dokumen pribadi agar Lexa dapat menjawab berdasarkan isinya:

1. Klik **"Pilih file"** di sidebar.
2. Pilih file **PDF atau TXT** (maks. 10MB).
3. Tunggu proses indexing — muncul pesan sukses hijau.
4. Dokumen langsung bisa digunakan — tanyakan konten dokumen tersebut ke Lexa.

**Catatan:**
- Dokumen hanya aktif untuk sesi ini (bukan permanen).
- Dokumen dari sesi lain tidak terlihat di sesi Anda.
- Jika file uploader dikosongkan, dokumen sementara akan dihapus.

**Format yang didukung:** `.pdf`, `.txt`, `.md`

---

### Tombol Sidebar

| Tombol | Fungsi |
|--------|--------|
| 🔄 **Rebuild Basis Pengetahuan** | Update RAG index setelah admin menambahkan dokumen baru ke server |
| 🗑️ **Reset Percakapan** | Hapus semua riwayat chat dan mulai sesi baru |

> ⚠️ **Reset tidak dapat dibatalkan.** Seluruh riwayat percakapan akan dihapus permanen.

---

### Referensi Sumber Jawaban

Ketika Lexa menjawab berdasarkan dokumen basis pengetahuan, akan muncul expander:

```
▼ 📚 Referensi Basis Pengetahuan

1. pricing.md (Paket Harga) | Relevansi: 0.74
   "## Paket Pro\nHarga: Rp 299.000/bulan, mencakup 10 pengguna..."

2. features.md (Fitur Utama) | Relevansi: 0.61
   "Fitur premium meliputi: laporan analitik, integrasi API..."
```

Skor relevansi berkisar 0–1. Semakin tinggi skor, semakin relevan chunk tersebut dengan pertanyaan Anda.

---

## Mode 2: Terminal/CLI Interface

```bash
python main.py
```

```
=== Memulai Chatbot Customer Service Lexa (CLI) ===
Sesi chat aktif (ID: cli-a1b2c3d4)
Lexa aktif! Ketik 'keluar' atau 'exit' untuk menyudahi obrolan.

Pelanggan: Halo Lexa
Lexa: Halo! Selamat datang di layanan kami. Ada yang bisa saya bantu?

Pelanggan: keluar
Lexa: Terima kasih telah menghubungi kami. Semoga hari Anda menyenangkan!
```

| Perintah | Fungsi |
|----------|--------|
| Ketik pesan → Enter | Kirim ke Lexa |
| `keluar` atau `exit` | Akhiri percakapan |
| `Ctrl+C` | Paksa berhenti |

---

## Mode 3: API Langsung (Untuk Developer)

Backend FastAPI menyediakan Swagger UI di:
```
http://127.0.0.1:8000/docs
```

Endpoint utama:
```
POST /api/sessions/                        → Buat sesi baru
GET  /api/chat/{session_id}/history        → Lihat riwayat
POST /api/chat/{session_id}/stream         → Chat (streaming)
POST /api/documents/upload-temp/{sid}      → Upload dokumen sementara
```

---

## Pertanyaan yang Bisa Ditanyakan ke Lexa

**✅ Optimal:**
- Pertanyaan tentang konten dokumen yang diupload
- Pertanyaan tentang layanan customer service
- Pertanyaan tentang kebijakan, fitur, harga (jika ada di knowledge_base)
- Pertanyaan prosedural: cara refund, cara komplain, dll.

**⚠️ Kurang Optimal:**
- Pertanyaan data real-time (harga saham, berita hari ini)
- Pertanyaan di luar konteks layanan pelanggan
- Pertanyaan teknis pemrograman

---

## FAQ v2.0

**Q: Apakah riwayat chat saya disimpan?**  
A: Ya, di v2.0 riwayat disimpan permanen di database SQLite. Riwayat tetap ada setelah refresh atau restart browser — kecuali Anda klik Reset.

**Q: Apakah dokumen yang saya upload disimpan permanen?**  
A: Tidak. Dokumen yang diupload via sidebar hanya aktif untuk sesi saat ini (in-memory). Jika sesi di-reset atau server restart, dokumen tersebut hilang. Dokumen permanen harus ditambahkan oleh admin ke folder `knowledge_base/`.

**Q: Kenapa ada dua terminal yang harus dibuka?**  
A: v2.0 menggunakan arsitektur terpisah — backend FastAPI dan frontend Streamlit adalah dua proses berbeda. Backend menangani logika, database, dan AI. Frontend menampilkan UI.

**Q: Kenapa jawaban Lexa menyebut sumber dokumen?**  
A: Fitur RAG (Retrieval-Augmented Generation) memungkinkan Lexa mencari informasi relevan dari basis pengetahuan sebelum menjawab, sehingga jawaban lebih akurat dan dapat diverifikasi.

**Q: Apakah percakapan saya dikirim ke server luar?**  
A: Ya. Pesan dikirim ke Groq Cloud API untuk diproses oleh model AI. Jangan bagikan informasi sensitif seperti kata sandi atau nomor kartu kredit.

**Q: Apa yang terjadi jika Lexa menjawab berdasarkan informasi yang salah?**  
A: Periksa referensi sumber yang ditampilkan. Jika referensi tidak relevan atau tidak ada, jawaban Lexa berdasarkan pengetahuan umum model — verifikasi ke sumber resmi untuk informasi penting.

---

## Troubleshooting

| Masalah | Penyebab | Solusi |
|---------|----------|--------|
| "Backend tidak tersedia" di Streamlit | Backend belum jalan | Jalankan `uvicorn backend.main:app` dulu |
| `ModuleNotFoundError: requests` | Dependency kurang | `pip install requests` |
| Halaman load sangat lama pertama kali | Download model AI ~80MB | Tunggu hingga selesai (1x saja) |
| Upload gagal "File terlalu besar" | File > 10MB | Kompres atau split file |
| Riwayat hilang setelah clear file | Bug aktif (Bug-010) | Jangan clear uploader jika ingin simpan riwayat |
| Error "API Key tidak ditemukan" | `.env` tidak ada/salah | Cek file `.env` |

Untuk panduan instalasi lengkap, lihat [Installation Guide](InstallationGuide.md).
