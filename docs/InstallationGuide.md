# Installation Guide v2.0 — SH04-AI-Chatbot-LEXA

**Project:** SH04-AI-Chatbot-LEXA  
**Version:** 2.0.0  
**Last Updated:** 2026-07-10

---

## System Requirements

| Komponen | Minimum | Recommended |
|----------|---------|-------------|
| Python | 3.9 | 3.11+ |
| RAM | 4 GB | 8 GB *(untuk embedding model)* |
| Storage | 500 MB | 1 GB *(model ~80MB + DB + docs)* |
| OS | Windows 10 / Ubuntu 20.04 / macOS 12 | Latest stable |
| Network | Required (Groq API + model download) | Stable broadband |

> ⚠️ **Perhatian:** Pada startup pertama, model `all-MiniLM-L6-v2` (~80MB) akan diunduh otomatis oleh `sentence-transformers`. Pastikan koneksi internet stabil.

---

## Step 1 — Dapatkan Groq API Key

1. Buka [https://console.groq.com](https://console.groq.com)
2. Daftar atau login.
3. Navigasi ke **API Keys** → **Create API Key**.
4. Copy key (awalan `gsk_...`) dan simpan dengan aman.

---

## Step 2 — Clone atau Download Project

```bash
# Clone via Git
git clone https://github.com/ndiecyber/SH04-AI-Chatboot-LEXA.git
cd SH04-AI-Chatboot-LEXA

# Atau download ZIP dan extract
```

**Pastikan struktur folder ada:**
```
SH04-AI-Chatboot-LEXA/
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── globals.py
│   ├── routers/
│   │   ├── chat.py
│   │   ├── sessions.py
│   │   └── documents.py
│   └── services/
│       ├── chat_service.py
│       └── document_service.py
├── core/
│   ├── llm.py
│   └── rag.py
├── knowledge_base/     ← Folder dokumen basis pengetahuan
├── app.py
├── main.py
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## Step 3 — Buat Virtual Environment

```bash
# Buat venv
python -m venv .venv

# Aktifkan (macOS/Linux)
source .venv/bin/activate

# Aktifkan (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Aktifkan (Windows CMD)
.\.venv\Scripts\activate.bat
```

Prompt akan berubah menjadi `(.venv) ...`

---

## Step 4 — Install Dependencies

```bash
pip install -r requirements.txt
```

> ⚠️ **Bug-006 Workaround:** Library `requests` tidak ada di `requirements.txt`. Install manual:
```bash
pip install requests
```

**Daftar lengkap yang dibutuhkan:**
```
groq
python-dotenv
streamlit
sentence-transformers
numpy
pypdf
fastapi
uvicorn[standard]
sqlalchemy
python-multipart
requests           ← Install manual (Bug-006)
```

**Verifikasi instalasi:**
```bash
python -c "import groq, streamlit, fastapi, sentence_transformers, requests; print('OK')"
```

---

## Step 5 — Setup Environment Variables

Salin file contoh:
```bash
# macOS/Linux
cp .env.example .env

# Windows
copy .env.example .env
```

Edit `.env`:
```env
# WAJIB — Groq API Key
GROQ_API_KEY=gsk_YourActualGroqApiKeyHere

# OPSIONAL — Kunci perlindungan API backend (kosongkan untuk nonaktif)
# LEXA_API_KEY=your_secret_backend_key

# OPSIONAL — Model (default: openai/gpt-oss-120b)
# LEXA_MODEL=llama-3.1-8b-instant
```

> ✅ File `.env` sudah tercatat di `.gitignore` — aman dari VCS.

---

## Step 6 — Siapkan Basis Pengetahuan (Opsional)

Tambahkan dokumen ke folder `knowledge_base/` agar Lexa bisa menjawab berdasarkan informasi spesifik bisnis Anda:

```bash
# Contoh struktur knowledge_base/
knowledge_base/
├── faq.md          ← FAQ layanan
├── pricing.md      ← Informasi harga
├── features.md     ← Fitur produk
└── policy.pdf      ← Kebijakan refund, dll
```

Format yang didukung: `.md`, `.txt`, `.pdf`

Folder ini akan diindeks otomatis saat backend pertama kali dijalankan.

---

## Step 7 — Jalankan Aplikasi

### Backend (wajib dijalankan lebih dulu)

```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Tunggu output berikut sebelum melanjutkan:
```
Memuat basis pengetahuan RAG...
Indeks RAG berhasil dimuat dari cache.    ← atau "dibangun baru"
RAG basis pengetahuan dimuat!
INFO: Application startup complete.
INFO: Uvicorn running on http://127.0.0.1:8000
```

> ⏳ **Startup pertama** membutuhkan waktu lebih lama (~30–40 detik) karena download model `all-MiniLM-L6-v2` (~80MB). Startup berikutnya ~3–5 detik dari cache.

### Frontend Streamlit (Terminal baru)

```bash
streamlit run app.py
```

Browser otomatis terbuka di `http://localhost:8501`.

### CLI (Opsional, Terminal baru)

```bash
python main.py
```

---

## Step 8 — Verifikasi Instalasi

1. Buka `http://127.0.0.1:8000/docs` → Swagger UI harus tampil.
2. Buka `http://localhost:8501` → Chat interface harus tampil tanpa error banner.
3. Kirim pesan "Halo" → Lexa harus merespons dalam Bahasa Indonesia.

---

## Troubleshooting Instalasi

### `ModuleNotFoundError: No module named 'requests'`
```bash
pip install requests
```

### `ModuleNotFoundError: No module named 'backend'`
Pastikan menjalankan perintah dari root folder proyek:
```bash
cd SH04-AI-Chatboot-LEXA
uvicorn backend.main:app ...
```

### Backend startup sangat lambat (>60 detik)
Model sedang diunduh. Periksa koneksi internet. Cukup tunggu — proses ini hanya terjadi sekali.

### `Address already in use` pada port 8000
```bash
# Cari proses yang menggunakan port
lsof -i :8000          # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Gunakan port lain
uvicorn backend.main:app --port 8001
# Update API_URL di app.py: API_URL = "http://127.0.0.1:8001"
```

### Streamlit "Backend tidak tersedia"
Backend belum berjalan. Jalankan `uvicorn` terlebih dahulu di terminal terpisah.

### PowerShell ExecutionPolicy Error (Windows)
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Error `ValueError: GROQ_API_KEY tidak ditemukan`
Periksa file `.env`:
```bash
cat .env
# Harus ada: GROQ_API_KEY=gsk_...
```

---

## Uninstall

```bash
deactivate
cd ..
rm -rf SH04-AI-Chatboot-LEXA/
```

Tidak ada perubahan sistem yang dilakukan selain folder project dan virtual environment.
