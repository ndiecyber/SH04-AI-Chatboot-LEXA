# 📈 Progress Log & Changelog - LEXA Chatbot

Dokumen ini digunakan untuk mencatat seluruh riwayat pengerjaan, pembaruan fitur (changelog), dan rencana pengembangan project **LEXA Chatbot** ke depannya.

---

## 📅 [10 Juli 2026] - Perbaikan Bug Backend (RAG PDF & Security Hardening)

Dilakukan audit kode backend dan perbaikan bug yang ditemukan pada arsitektur FastAPI + RAG. Semua perubahan di-commit langsung ke branch `main` repo utama.

### 🐞 Bug yang Diperbaiki
*   **PDF Global Tidak Terindeks (RAG Search)**: `core/rag.py` → `build_index()` sebelumnya hanya memproses file `.md`/`.txt`. File PDF yang di-upload ke `knowledge_base/` tersimpan di disk tetapi **tidak pernah di-embed**, sehingga RAG statis buta terhadap isi PDF.
    *   **Perbaikan**: `build_index()` sekarang membaca `.pdf` (ekstraksi teks via `pypdf`) dan memprosesnya dengan `chunk_text()`. (Commit: `b4ccf31`)
*   **CORS Wildcard (Insecure + Bentrok)**: `backend/main.py` menggunakan `allow_origins=["*"]` bersama `allow_credentials=True`. Kombinasi ini ditolak browser (Starlette) dan tidak aman untuk deployment.
    *   **Perbaikan**: CORS di-restrict ke origin Streamlit (`http://localhost:8501`, `http://127.0.0.1:8501`). (Commit: `9710d55`)
*   **PDF Tidak Terdaftar di Tabel Database**: `backend/main.py` → `sync_database_documents()` hanya memindai `.md`/`.txt`, sehingga PDF yang sudah masuk vector store **tidak tercatat di tabel `documents`** (DB). Akibatnya `GET /api/documents/` tidak menampilkan PDF dan `DELETE /api/documents/{id}` gagal untuk PDF.
    *   **Perbaikan**: Pemindaian ikut menyertakan `.pdf`, dengan ekstraksi teks `pypdf` (bukan `open()` text-mode yang crash pada binary). `file_type` kini benar: `"pdf"` / `"md"` / `"txt"`. (Commit: `6768c19`)
*   **API Tanpa Autentikasi (Risiko Saat Deploy Publik)**: Seluruh endpoint terbuka. Aman untuk localhost, berisiko jika di-expose ke jaringan.
    *   **Perbaikan (Opt-in, Non-Breaking)**: Ditambahkan guard API key. Aktif **hanya jika** env `LEXA_API_KEY` diset. Jika aktif, semua endpoint mewajibkan header `Authorization: Bearer <LEXA_API_KEY>` kecuali `/`, `/docs`, `/openapi.json`, `/redoc`. Jika tidak diset, perilaku tetap seperti sebelumnya (aman untuk dev lokal). (Commit: `6768c19`)

### 📝 Catatan / Scope
*   Bug di luar ranah backend **tidak diubah** pada sesi ini:
    *   `requests` belum ada di `requirements.txt` (penyebab: `app.py`/frontend `import requests`) — perlu ditambahkan agar Streamlit UI bisa berjalan setelah `pip install -r requirements.txt`.
    *   Endpoint `/api/chat/{id}/stream` tidak menggunakan format SSE standar (`data:`/`[DONE]`) — sengaja dibiarkan karena client Streamlit mengandalkan format token mentah saat ini.
*   Laporan `bug_reports/Bug001.md` (`.gitignore` hilang) sudah **usang** — `.gitignore` saat ini sudah ada dan meng-cover `.env`.

---

## 📅 [07 Juli 2026] - Implementasi REST API & Decoupling Architecture

### 🛠️ Fitur & Perubahan Baru
*   **Arsitektur Terpisah (Decoupled)**: Memisahkan bagian Frontend (Streamlit) dengan Backend (FastAPI).
*   **FastAPI REST API**:
    *   Membuat server backend di folder `/backend` dengan framework FastAPI dan ASGI Uvicorn.
    *   Endpoint CRUD untuk manajemen sesi chat (`/api/sessions`).
    *   Endpoint Chat (Standard & Streaming token-by-token) terintegrasi dengan Groq API (`/api/chat`).
    *   Endpoint manajemen dokumen RAG (`/api/documents`) baik untuk database global maupun temporer per-sesi.
    *   Dokumentasi API otomatis via Swagger UI (`http://127.0.0.1:8000/docs`).
*   **Database Persistence (SQLite + SQLAlchemy)**:
    *   Setup database `lexa.db` untuk menyimpan riwayat chat agar tidak hilang saat aplikasi di-refresh.
    *   Auto-sync: Menyelaraskan otomatis isi folder fisik `knowledge_base` dengan record data di database saat backend dinyalakan.
*   **Refactor Client & Frontend**:
    *   Mengubah `app.py` (Streamlit Web UI) agar berkomunikasi penuh menggunakan HTTP request ke backend server (port 8000).
    *   Mengubah `main.py` (CLI Terminal) agar terhubung ke REST API backend.
*   **Perbaikan Halusinasi Identitas**:
    *   Memperbarui *default system prompt* di `core/llm.py` untuk menghentikan halusinasi model open-source yang sebelumnya mengaku sebagai GPT-4 buatan OpenAI.
*   **Dokumentasi & Git**:
    *   Menambahkan `lexa.db` ke `.gitignore` agar database lokal tidak ter-commit.
    *   Menambahkan `.env.example` sebagai template konfigurasi API key.
    *   Memperbarui file `README.md` tentang panduan arsitektur baru dan cara menjalankannya.

---

## 📋 Rencana Pengembangan Selanjutnya (Future Backlog)

Berikut adalah beberapa ide fitur backend berikutnya yang dapat dikembangkan untuk membuat aplikasi ini lebih aman dan berskala besar:

- [x] **Opsi 1a: API Key Guard (Opt-in)** — *DONE (10 Jul 2026)*: Guard Bearer token non-breaking via env `LEXA_API_KEY`. JWT penuh (registrasi/login user) masih terbuka sebagai pengembangan lanjutan.
- [ ] **Opsi 1b: User Authentication & Security (JWT)**
    - Membuat fitur Registrasi & Login user.
    - Mengamankan API endpoint dengan JWT Token agar user hanya dapat mengakses riwayat chat miliknya sendiri.
- [x] **Opsi 3a: PDF Global End-to-End** — *DONE (10 Jul 2026)*: PDF kini ter-indeks RAG DAN terdaftar di DB (`build_index` + `sync_database_documents`).
- [ ] **Opsi 2: Integrasi Vector Database Profesional (ChromaDB / Qdrant / FAISS)**
    - Mengganti penyimpanan index berbasis file Pickle (`vector_index.pkl`) ke Vector Database asli untuk pencarian dokumen skala besar yang lebih cepat dan aman.
- [ ] **Opsi 3b: URL Web Scraper & Multi-Format Doc Parser**
    - Menambahkan fitur scraper untuk membaca konten dari link website artikel.
    - Menambahkan parser dokumen `.docx` (Microsoft Word) dan `.csv`/`.xlsx` (Excel) ke sistem RAG.
- [ ] **Opsi 4: Advanced RAG (Re-ranking)**
    - Mengintegrasikan Cohere Rerank API atau model reranker lokal untuk menyaring ulang hasil pencarian dokumen agar jawaban bot jauh lebih akurat.
