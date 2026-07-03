# Chatbot Customer Service - Lexa 💬📚

Lexa adalah chatbot asisten customer service interaktif berbasis AI yang dilengkapi dengan teknologi **RAG (Retrieval-Augmented Generation)**. Chatbot ini dapat menjawab pertanyaan pelanggan secara cerdas dan akurat berdasarkan basis pengetahuan dokumen perusahaan Anda, baik dari dokumen bawaan (*static*) maupun dokumen yang diunggah langsung saat percakapan berlangsung (*dynamic upload*).

Proyek ini ditenagai oleh **Groq Cloud API** dengan antarmuka berbasis **Streamlit** (Web UI) dan **Terminal (CLI)**.

---

## 🚀 Fitur Utama
1. **Retrieval-Augmented Generation (RAG) Lokal**: Pencarian dokumen menggunakan representasi vektor dari model `all-MiniLM-L6-v2` (`sentence-transformers`) dan kecocokan kecerdasan kosinus (*Cosine Similarity*).
2. **Dynamic PDF & TXT Upload**: Mengekstraksi teks dari berkas PDF (`pypdf`) dan TXT yang diunggah langsung oleh pengguna di halaman web.
3. **Penyimpanan Vektor Aman di Memori**: Dokumen unggahan pengguna hanya disimpan di dalam memori sesi aktif dan akan otomatis terhapus saat sesi di-reset atau ditutup (tidak tersimpan ke disk).
4. **Indikator Dokumen Aktif & Referensi Transparan**: Menampilkan sumber dokumen pendukung beserta skor kecocokan dalam panel *expander* di bawah jawaban bot.

---

## 🛠️ Persiapan Awal

### 1. Dapatkan API Key Groq
Silakan daftar secara gratis dan ambil API Key Anda di: **[Groq Console](https://console.groq.com/)**.

### 2. Konfigurasi Environment File (`.env`)
Buat file bernama `.env` di root folder proyek Anda, lalu masukkan API Key Anda:
```env
GROQ_API_KEY=gsk_IsiDenganApiKeyGroqAndaDiSini
```

---

## 🚀 Instalasi & Setup

Sangat disarankan untuk menggunakan **Virtual Environment (venv)** agar pustaka terisolasi secara aman.

### 1. Buat dan Aktifkan Virtual Environment
Jalankan perintah berikut di terminal Anda (PowerShell/CMD):

* **Windows (PowerShell)**:
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  ```
* **Windows (CMD)**:
  ```cmd
  python -m venv .venv
  .\.venv\Scripts\activate.bat
  ```

### 2. Instal Library (Requirements)
Jalankan perintah berikut untuk menginstal semua pustaka yang diperlukan (`groq`, `streamlit`, `sentence-transformers`, `numpy`, `pypdf`):
```bash
pip install -r requirements.txt
```

---

## 🎮 Cara Menjalankan

### A. Tampilan Browser (Streamlit Web UI)
Jalankan perintah berikut untuk membuka antarmuka chatbot interaktif:
```powershell
.\.venv\Scripts\streamlit.exe run app.py
```
Aplikasi web akan otomatis terbuka di browser Anda pada alamat `http://localhost:8501`.

### B. Uji Coba Pencarian RAG (CLI)
Untuk memverifikasi kecocokan pencarian dokumen dinamis secara terpisah di terminal:
```powershell
.\.venv\Scripts\python.exe tests/scratch_pdf_test.py
```

---

## 📁 Struktur Direktori Proyek
```text
CHATBOT LEXA/
├── .venv/                      # Python virtual environment
├── core/                       # Logika Utama (Package)
│   ├── __init__.py             # Inisialisasi package
│   ├── llm.py                  # Logika utama LLM & orkestrasi
│   └── rag.py                  # Mesin pencari RAG & chunking
├── knowledge_base/             # Folder dokumen basis pengetahuan
│   ├── features.md             # Data fitur-fitur utama SaaS
│   ├── pricing.md              # Data daftar paket harga SaaS
│   └── vector_index.pkl        # Berkas cache indeks vektor (permanen)
├── tests/                      # Script Pengujian
│   ├── scratch_pdf_test.py     # Pengujian PDF / Dynamic RAG
│   └── scratch_rag_test.py     # Pengujian static RAG
├── app.py                      # Aplikasi utama (Streamlit Web UI)
├── main.py                     # Aplikasi CLI terminal
├── requirements.txt            # Daftar dependensi pustaka Python
└── README.md                   # Panduan proyek ini
```

---

## 🤝 Pembagian Kerja Tim (Batas Kolaborasi)
* **LLM Engineer (Anda)**: Mengelola sistem prompt, pembuatan embeddings, vector database, logika chunking (`rag.py`), serta integrasi LLM (`llm.py`).
* **Backend Engineer**: Menyediakan server API (misalnya memakai FastAPI/Node.js) untuk menghubungkan modul `LexaChatbot` dengan basis data utama (riwayat chat) dan autentikasi user.
* **Frontend Engineer**: Membuat antarmuka UI chat widget interaktif di web SaaS utama dan mengalirkan respons teks secara *real-time*.
