# Regression & Bug Status Report — SH04-AI-Chatbot-LEXA

**Project:** SH04-AI-Chatbot-LEXA  
**Version:** 2.0.0 (Update: 2026-07-18)  
**Tester:** QA Engineering Team  
**Date:** 2026-07-18  
**Purpose:** Status lengkap semua bug dari v1.0 s/d v2.0 + temuan baru

---

## 1. Konsep Status Bug

Dalam proyek ini, dokumentasi bug mengikuti standar berikut:

| Status | Ikon | Arti |
|--------|------|------|
| Open | 🔴 | Bug ditemukan, belum ada perbaikan |
| Fixed | 🔧 | Developer mengklaim sudah diperbaiki |
| Closed | ✅ | QA melakukan re-test dan konfirmasi fixed |
| Partial | ⚠️ | Sebagian diperbaiki, sebagian masih open |
| Acknowledged | 📝 | Developer mengakui tapi belum fix |
| Won't Fix | 🚫 | Keputusan tidak akan diperbaiki (dengan alasan) |
| Reopened | 🔁 | Sebelumnya closed, muncul lagi |

**Prinsip penting:** Bug yang sudah Closed **tidak dihapus** dari dokumentasi. Tetap ada sebagai historical record dan untuk mencegah regresi di versi berikutnya.

---

## 2. Master Bug Tracker — Semua Bug

| Bug ID | Judul | Severity | Pertama Ditemukan | Status Saat Ini | Versi Fix |
|--------|-------|----------|-------------------|-----------------|-----------|
| Bug-001 | Missing `.gitignore` | 🔴 Critical | v1.0 (2025-07-01) | ✅ **CLOSED** | v2.0 |
| Bug-002 | No input validation di `llm.py` | 🟠 High | v1.0 (2025-07-01) | 🔴 **OPEN** | — |
| Bug-003 | Dark mode CSS override | 🟡 Medium | v1.0 (2025-07-01) | 🔴 **OPEN** | — |
| Bug-004 | Rate limit error tidak user-friendly | 🟠 High | v1.0 (2025-07-01) | 🔴 **OPEN** | — |
| Bug-005 | Unbounded history ke Groq API | 🟠 High | v1.0 (2025-07-01) | ⚠️ **PARTIAL** | v2.0 partial |
| Bug-006 | `requests` tidak di requirements.txt | 🔴 Critical | v2.0 (2026-07-10) | 📝 **ACKNOWLEDGED** | — |
| Bug-007 | Tidak ada validasi ukuran file | 🟠 High | v2.0 (2026-07-10) | 🔴 **OPEN** | — |
| Bug-008 | Orphaned user message stream disconnect | 🟠 High | v2.0 (2026-07-10) | 🔴 **OPEN** | — |
| Bug-009 | Session pipeline cache tanpa eviction | 🟡 Medium | v2.0 (2026-07-10) | 🔴 **OPEN** | — |
| Bug-010 | File uploader clear → session reset | 🟡 Medium | v2.0 (2026-07-10) | 🔴 **OPEN** | — |
| Bug-011 | `SessionLocal()` dibuat manual di generator | 🟠 High | v2.0 (2026-07-18) | 🔴 **OPEN** *(baru)* | — |
| Bug-012 | Inkonsistensi threshold RAG di dokumentasi | 🟢 Low | v2.0 (2026-07-18) | 🔴 **OPEN** *(baru, doc fix)* | — |

---

## 3. Bug yang CLOSED (Fixed & Verified)

### ✅ Bug-001 — Missing `.gitignore`

**Fix:** `.gitignore` ditambahkan di commit arsitektur v2.0.  
**Re-test:** File `.gitignore` ditemukan dan meng-cover `.env`, `lexa.db`, `knowledge_base`, `.venv`.  
**Verified by QA:** 2026-07-10  
**Historical note:** Ini adalah bug Critical pertama yang ditemukan. Perbaikannya menjadi fondasi keamanan proyek.

---

## 4. Bug yang CLOSED dari developer-side (Fixed tapi bukan bug formal QA)

Berikut adalah fix yang tercatat di `progress_log.md` developer tapi tidak dalam format bug report formal QA:

| Fix | Keterangan | Status |
|-----|------------|--------|
| CORS Wildcard (`allow_origins=["*"]`) | Fixed → restricted ke localhost:8501 | ✅ QA Verified |
| PDF tidak diindeks di `build_index()` | Fixed → `.pdf` kini diproses | ✅ QA Verified |
| PDF tidak tercatat di DB (`sync_database_documents`) | Fixed → `.pdf` disertakan | ✅ QA Verified |
| Identity hallucination (bot mengaku GPT-4) | Fixed → system prompt diperbarui | ✅ QA Verified |
| API tanpa autentikasi | Fixed → optional LEXA_API_KEY guard | ✅ QA Verified |

---

## 5. Bug yang PARTIAL Fix

### ⚠️ Bug-005 — Unbounded History

**Yang sudah fixed:** In-process memory leak (history tidak lagi di RAM permanen — dipindah ke SQLite). ✅  
**Yang masih open:** Seluruh history dari SQLite tetap direkonstruksi dan dikirim ke Groq API di setiap request. ❌  
**Impact:** Di sesi 100+ turn, ~20.000 token dikirim per request → latency meningkat + biaya API bertambah.  
**Next action:** Implementasi sliding window (max 20 turns) di `chat_service.py`.

---

## 6. Bug BARU yang Ditemukan di Audit Terbaru (2026-07-18)

### 🔴 Bug-011 — `SessionLocal()` Manual di Generator

**Ditemukan dari:** Pembacaan kode lengkap `backend/routers/chat.py`  
**Root cause:** `event_generator()` membuat koneksi DB sendiri tanpa lifecycle management FastAPI.  
**Risk:** Connection leak jika client disconnect sebelum stream selesai.  
**Severity:** High — potensi resource exhaustion di production.

### 🟢 Bug-012 — Inkonsistensi Threshold RAG

**Ditemukan dari:** Perbandingan `core/rag.py` vs `core/llm.py` vs dokumentasi QA sebelumnya.  
**Fact:** Default `RAGPipeline.search()` = 0.2, tapi `llm.py` memanggil dengan override 0.15, dan developer test scripts pakai 0.1.  
**Impact:** Dokumentasi QA menyebut "0.15 threshold" tanpa menjelaskan ini adalah override, bukan default.  
**Severity:** Low — hanya dokumentasi, tidak ada bug fungsional.

---

## 7. Temuan Baru: Developer Test Scripts (`llm_tests/`)

**File yang ditemukan:**
- `llm_tests/scratch_rag_test.py` — smoke test RAG pipeline
- `llm_tests/scratch_pdf_test.py` — test temp doc + verifikasi isolasi disk

**Gap yang ditemukan:** Test isolasi disk dokumen sementara ada di developer scripts tapi **tidak ada di test suite QA formal**.

**Tindakan:** Tambah TC-R-009 ke `TestCases.md` (lihat `tests/DeveloperTestAudit.md`).

---

## 8. Statistik Bug Terkini

```
Total bug terdokumentasi:  12
┌─────────────────────────────────────────────┐
│  ✅ CLOSED         : 1  (Bug-001)           │
│  📝 ACKNOWLEDGED   : 1  (Bug-006)           │
│  ⚠️  PARTIAL       : 1  (Bug-005)           │
│  🔴 OPEN           : 9  (002,003,004,        │
│                          007,008,009,010,    │
│                          011,012)            │
└─────────────────────────────────────────────┘

Berdasarkan severity (hanya yang OPEN):
  Critical : 0
  High     : 5  (002, 004, 007, 008, 011)
  Medium   : 2  (009, 010)
  Low      : 1  (012)
  Partial  : 1  (005 — High severity)
```

---

## 9. Prioritas Fix Berikutnya

| Priority | Bug ID | Action |
|----------|--------|--------|
| 🔴 P1 | Bug-006 | Tambah `requests` ke `requirements.txt` — 1 baris, 5 menit |
| 🟠 P2 | Bug-011 | Perbaiki `SessionLocal()` manual di generator — connection leak |
| 🟠 P2 | Bug-008 | Atomic save untuk streaming — orphaned message |
| 🟠 P2 | Bug-007 | Tambah validasi ukuran file 10MB |
| 🟠 P2 | Bug-002 | Tambah `_validate_message()` di `core/llm.py` |
| 🟠 P2 | Bug-004 | Handle `RateLimitError` secara spesifik |
| 🟠 P2 | Bug-005 | Sliding window history (max 20 turns) |
| 🟡 P3 | Bug-009 | Session pipeline TTL/eviction |
| 🟡 P3 | Bug-010 | Pisahkan file-clear dari session-reset |
| 🟡 P3 | Bug-003 | Fix dark mode CSS |
| 🟢 P4 | Bug-012 | Koreksi threshold di dokumentasi QA |

---

## 10. Template: Cara Update Bug Report Saat Bug Di-Fix

Ketika developer melaporkan bahwa suatu bug sudah di-fix, QA melakukan langkah berikut:

**1. Update `BugXXX.md`:**
```markdown
## Status History
| Date | Status | Actor | Notes |
|------|--------|-------|-------|
| YYYY-MM-DD | 🔴 Open | QA Team | Bug ditemukan |
| YYYY-MM-DD | 🔧 Fixed | Developer | [Deskripsi fix + commit hash jika ada] |
| YYYY-MM-DD | ✅ Closed | QA Team | Re-test PASS |

## Current Status: ✅ CLOSED

## Re-test Result
[Langkah re-test + output + konfirmasi]
```

**2. Update `RegressionReport.md`:** Pindahkan dari tabel Open ke tabel Closed.

**3. Update `TestSummary.md`:** Revisi statistik bug (Open: N-1, Closed: M+1).

**4. Update `FinalReport.md`:** Jika semua P1/P2 sudah closed, update verdict.
