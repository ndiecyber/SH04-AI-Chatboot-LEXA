# Performance Testing Report v2.0 — SH04-AI-Chatbot-LEXA

**Project:** SH04-AI-Chatbot-LEXA | **Version:** 2.0.0 | **Date:** 2026-07-10

---

## Performance Baselines v2.0

| Metric | Target | Acceptable | Critical |
|--------|--------|------------|----------|
| Backend cold start (model cached) | < 5s | < 10s | > 20s |
| Backend cold start (first time) | < 40s | < 60s | > 90s |
| TTFT tanpa RAG | < 1.5s | < 3s | > 5s |
| TTFT dengan RAG | < 2.5s | < 4s | > 6s |
| RAG search latency | < 300ms | < 500ms | > 1s |
| DB query (reconstruct history) | < 50ms | < 200ms | > 500ms |
| Document upload + index | < 10s | < 30s | > 60s |

---

## Test Results

### PT2-001 — Backend Cold Start (Model Cached)

```
Kondisi: vector_index.pkl ada, sentence-transformers cached

$ time uvicorn backend.main:app
  Memuat basis pengetahuan RAG...
  Indeks RAG berhasil dimuat dari cache.
  RAG basis pengetahuan dimuat!
  Application startup complete.

Waktu: 3.2s (dari perintah hingga "startup complete")
```
**Result:** ✅ **PASS** (3.2s < 5s target)

---

### PT2-002 — Backend Cold Start (First Time — Model Download)

```
Kondisi: Model belum didownload

Download all-MiniLM-L6-v2 (~80MB)...  ← ~20–30 detik
Building index from 3 documents...
Index berhasil dibuat dengan 47 chunks.

Total waktu: ~35s (tergantung koneksi internet)
```
**Observasi:** ⚠️ Pengguna harus tahu bahwa startup pertama membutuhkan download ~80MB. Harus didokumentasikan.  
**Result:** ✅ **PASS** (35s < 40s target) tapi perlu warning di dokumentasi.

---

### PT2-003 — TTFT dengan RAG

| # | Query | RAG Hit | RAG Time | TTFT Total |
|---|-------|---------|----------|------------|
| 1 | "Harga paket Pro?" | ✅ | 180ms | 1.8s |
| 2 | "Cara refund?" | ✅ | 210ms | 2.0s |
| 3 | "Fitur utama?" | ✅ | 195ms | 1.9s |
| 4 | "Siapa presiden?" | ❌ | 155ms | 1.4s |
| 5 | "Berapa limit upload?" | ✅ | 225ms | 2.1s |
| **Avg** | | | **193ms** | **1.84s** |

**Result:** ✅ **PASS** (rata-rata 1.84s < 2.5s target)

---

### PT2-004 — DB History Reconstruction per Request

```
Sesi dengan N pesan — SQLite query time:

N=10  pesan: 8ms   ✅
N=50  pesan: 21ms  ✅
N=100 pesan: 45ms  ✅
N=200 pesan: 89ms  ✅
```

**Observasi:** SQLite sangat efisien untuk riwayat percakapan. Bahkan 200 pesan hanya membutuhkan 89ms.  
**Result:** ✅ **PASS**

---

### PT2-005 — Session Pipeline Memory Growth

```
Setiap session pipeline di-cache di _session_pipelines dict
Setiap pipeline: ~50–150MB (tergantung dokumen temp yang di-upload)

Tanpa eviction:
10 sesi aktif: ~500MB–1.5GB
50 sesi aktif: ~2.5GB–7.5GB

Tidak ada TTL, tidak ada eviction, tidak ada limit.
```

**Observasi:** ❌ Memory leak potensial di environment production dengan banyak sesi. Session pipeline tetap di memori selamanya kecuali:
1. Server restart
2. `clear_session_pipelines()` dipanggil (hanya terjadi saat dokumen global berubah)
3. Session didelete (hanya menghapus satu entry)

**Result:** ⚠️ **PARTIAL PASS** *(Bug-009)*

---

### PT2-006 — Streaming Throughput

```
Response ~200 tokens:
  Stream duration: ~3.8s
  Throughput: ~52 tok/s

Tidak berubah dari v1.0 — Groq LPU advantage tetap.
```
**Result:** ✅ **PASS**

---

### PT2-007 — Document Upload + RAG Rebuild

```
Upload PDF 500KB (12 halaman):
  - pypdf extraction: ~0.3s
  - Chunk generation: ~0.1s
  - Embedding (12 chunks): ~1.2s
  - Pickle save: ~0.05s
  - Total: ~1.65s ✅

Upload PDF 5MB (80 halaman):
  - pypdf extraction: ~1.2s
  - Chunk generation: ~0.4s
  - Embedding (80 chunks): ~8.5s
  - Total: ~10.1s ⚠️
```

**Observasi:** File besar membutuhkan lebih dari 10 detik untuk diproses. UI menampilkan spinner — UX acceptable tapi perlu batas ukuran file.  
**Result:** ⚠️ **PARTIAL PASS**

---

## Performance Summary

| Test | Result |
|------|--------|
| PT2-001 Cold start (cached) | ✅ PASS |
| PT2-002 Cold start (first time) | ✅ PASS |
| PT2-003 TTFT dengan RAG | ✅ PASS |
| PT2-004 DB Reconstruction | ✅ PASS |
| PT2-005 Memory/Session Pipeline | ⚠️ PARTIAL |
| PT2-006 Streaming Throughput | ✅ PASS |
| PT2-007 Document Upload | ⚠️ PARTIAL |

**Pass Rate: 71%** (5/7 PASS, 2 PARTIAL)