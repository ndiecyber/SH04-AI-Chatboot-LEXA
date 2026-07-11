# API Testing Report v2.0 — SH04-AI-Chatbot-LEXA

**Project:** SH04-AI-Chatbot-LEXA | **Version:** 2.0.0 | **Date:** 2026-07-10

---

## 1. Overview

Pengujian API mencakup semua endpoint FastAPI: `/api/sessions`, `/api/chat`, `/api/documents`. Termasuk verifikasi CORS fix, API key guard, streaming endpoint, dan integrasi Groq API.

---

## 2. Endpoint Inventory

| Method | Endpoint | Tag | Fungsi |
|--------|----------|-----|--------|
| GET | `/` | Root | Health check |
| GET | `/docs` | Docs | Swagger UI |
| POST | `/api/sessions/` | Sessions | Buat sesi |
| GET | `/api/sessions/` | Sessions | List sesi |
| DELETE | `/api/sessions/{id}` | Sessions | Hapus sesi |
| POST | `/api/chat/{id}` | Chat | Kirim pesan (sync) |
| GET | `/api/chat/{id}/history` | Chat | Ambil riwayat |
| POST | `/api/chat/{id}/stream` | Chat | Kirim pesan (streaming) |
| GET | `/api/chat/{id}/last-references` | Chat | Ambil referensi RAG terakhir |
| GET | `/api/documents/` | Documents | List dokumen global |
| POST | `/api/documents/upload` | Documents | Upload dokumen global |
| DELETE | `/api/documents/{id}` | Documents | Hapus dokumen |
| POST | `/api/documents/rebuild-index` | Documents | Rebuild RAG index |
| POST | `/api/documents/upload-temp/{sid}` | Documents | Upload dokumen sementara |

---

## 3. Test Results

### AT2-001 — Sessions CRUD Lengkap

| Step | Request | Expected | Actual | Status |
|------|---------|----------|--------|--------|
| Create | POST /api/sessions/ `{"id":"s1","title":"Test"}` | 201 + SessionResponse | ✅ 201 | PASS |
| List | GET /api/sessions/ | 200 + list | ✅ 200 dengan s1 | PASS |
| Delete | DELETE /api/sessions/s1 | 204 | ✅ 204 | PASS |
| Delete nonexistent | DELETE /api/sessions/s1 | 404 | ✅ 404 | PASS |

---

### AT2-002 — Chat Endpoint (Sync)

```
Request: POST /api/chat/s1
Body: {"message": "Apa layanan yang tersedia?"}

Response: 200 OK
{
  "response": "Halo! Kami menyediakan layanan customer support...",
  "references": []
}

DB check: messages table → 2 rows (user + assistant) untuk session s1
```

**Result:** ✅ **PASS**

---

### AT2-003 — Chat Endpoint (Streaming)

```
Request: POST /api/chat/s1/stream
Body: {"message": "Ceritakan layanan premium"}
Headers: Accept: text/event-stream

Response: 200 OK, Content-Type: text/event-stream
Chunks received: "Layanan " → "premium " → "kami " → "mencakup " → ...
[Stream ends]

DB check: assistant message tersimpan setelah stream selesai
```

**Catatan Teknis:** Endpoint menggunakan format token mentah, bukan SSE standar (`data:`/`[DONE]`). Client Streamlit menangani ini dengan baik, tapi client non-Streamlit perlu adaptasi.

**Result:** ✅ **PASS** *(non-standard SSE format — noted)*

---

### AT2-004 — CORS Fix Verification

```
Sebelumnya (v1.0): allow_origins=["*"] + allow_credentials=True → browser reject
Sekarang (v2.0):   allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"]

Test dari http://localhost:8501: → Preflight CORS OK ✅
Test dari http://evil.com:      → CORS blocked by browser ✅
```

**Result:** ✅ **PASS** *(Regression fix confirmed)*

---

### AT2-005 — LEXA_API_KEY Guard

```
Scenario A — LEXA_API_KEY tidak diset:
  Semua request → diterima ✅ (non-breaking, dev mode)

Scenario B — LEXA_API_KEY=mysecret123 diset:
  GET /             → 200 ✅ (public endpoint)
  GET /docs         → 200 ✅ (public endpoint)
  POST /api/chat/s1 (tanpa header) → 401 ✅
  POST /api/chat/s1 (Bearer mysecret123) → 200 ✅
  POST /api/chat/s1 (Bearer wrongkey) → 401 ✅
```

**Result:** ✅ **PASS**

---

### AT2-006 — Document Upload Flow

```
1. POST /api/documents/upload (PDF valid, 50KB)
   → 201 Created
   → File saved: knowledge_base/doc.pdf
   → DB: documents table row inserted (file_type: "pdf", chunk_count: 12)
   → RAG rebuild triggered
   → Session pipelines cleared

2. GET /api/documents/
   → 200, list includes doc.pdf ✅

3. DELETE /api/documents/1
   → 204
   → File removed from disk ✅
   → DB row deleted ✅
   → RAG rebuild triggered ✅
```

**Result:** ✅ **PASS**

---

### AT2-007 — Upload Temp Document + Query

```
1. POST /api/documents/upload-temp/s1 (file: warranty.pdf)
   → 200: {"status":"success","message":"Berhasil mengindeks 'warranty.pdf'"}

2. POST /api/chat/s1/stream {"message": "Berapa lama garansi produk?"}
   → References: [{chunk: {content:"Garansi 2 tahun..."}, score: 0.78}] ✅

3. POST /api/chat/s2/stream {"message": "Berapa lama garansi produk?"} (sesi lain)
   → References: [] (isolasi sesi terkonfirmasi) ✅
```

**Result:** ✅ **PASS**

---

### AT2-008 — Groq API Error Propagation

```
Scenario: GROQ_API_KEY tidak valid

POST /api/chat/s1 → ChatService → LexaChatbot.send_message()
→ groq.AuthenticationError
→ RuntimeError("Gagal memproses request ke Groq API: ...")
→ HTTPException(500, detail=str(e))

Response: 500 Internal Server Error
{"detail": "Gagal memproses request ke Groq API: 401 Invalid API Key"}
```

**Catatan:** Error message mengekspos detail API error ke client. Pertimbangkan sanitasi.  
**Result:** ✅ **PASS** *(sanitasi pesan direkomendasikan)*

---

## 4. API Testing Summary

| Test | Status |
|------|--------|
| Sessions CRUD | ✅ PASS |
| Chat Sync | ✅ PASS |
| Chat Streaming | ✅ PASS |
| CORS Fix | ✅ PASS |
| API Key Guard | ✅ PASS |
| Document Upload | ✅ PASS |
| Temp Document | ✅ PASS |
| Error Propagation | ✅ PASS |

**Pass Rate: 100%** (8/8)