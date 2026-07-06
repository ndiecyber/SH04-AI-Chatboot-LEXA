# 📈 Progress Log & Changelog - LEXA Chatbot

Dokumen ini digunakan untuk mencatat seluruh riwayat pengerjaan, pembaruan fitur (changelog), dan rencana pengembangan project **LEXA Chatbot** ke depannya.

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

- [ ] **Opsi 1: User Authentication & Security (JWT)**
    - Membuat fitur Registrasi & Login user.
    - Mengamankan API endpoint dengan JWT Token agar user hanya dapat mengakses riwayat chat miliknya sendiri.
- [ ] **Opsi 2: Integrasi Vector Database Profesional (ChromaDB / Qdrant / FAISS)**
    - Mengganti penyimpanan index berbasis file Pickle (`vector_index.pkl`) ke Vector Database asli untuk pencarian dokumen skala besar yang lebih cepat dan aman.
- [ ] **Opsi 3: URL Web Scraper & Multi-Format Doc Parser**
    - Menambahkan fitur scraper untuk membaca konten dari link website artikel.
    - Menambahkan parser dokumen `.docx` (Microsoft Word) dan `.csv`/`.xlsx` (Excel) ke sistem RAG.
- [ ] **Opsi 4: Advanced RAG (Re-ranking)**
    - Mengintegrasikan Cohere Rerank API atau model reranker lokal untuk menyaring ulang hasil pencarian dokumen agar jawaban bot jauh lebih akurat.
