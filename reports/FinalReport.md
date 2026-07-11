# Final QA Report v2.0 — SH04-AI-Chatbot-LEXA

**Project:** SH04-AI-Chatbot-LEXA  
**Version:** 2.0.0  
**QA Team:** QA Engineering Team  
**Report Date:** 2026-07-10  
**Previous Version:** v1.0.0 (2025-07-01)

---

## 1. Project Overview v2.0

| Field | Details |
|-------|---------|
| **Versi** | 2.0.0 |
| **Perubahan Utama** | Monolith → Decoupled FastAPI + RAG + SQLite |
| **Fitur Baru** | RAG pipeline, PDF support, persistent DB, REST API, document management |
| **Bug Fix dari v1.0** | CORS wildcard, .gitignore, PDF indexing, identity hallucination |
| **Stack** | Python + FastAPI + SQLite + Streamlit + Groq + SentenceTransformers |

---

## 2. Test Coverage Summary

| Kategori | Cases | PASS | PARTIAL | FAIL | Rate |
|----------|-------|------|---------|------|------|
| Functional | 12 | 12 | 0 | 0 | 100% |
| RAG Pipeline | 8 | 8 | 0 | 0 | 100% |
| UI | 12 | 8 | 3 | 1 | 66.7% |
| API | 8 | 8 | 0 | 0 | 100% |
| Negative | 10 | 6 | 2 | 2 | 60% |
| Security | 6 | 3 | 3 | 0 | 50% |
| Performance | 7 | 5 | 2 | 0 | 71.4% |
| **TOTAL** | **63** | **50** | **10** | **3** | **79.4%** |

---

## 3. Bug Statistics

### Semua Bug Aktif (v1.0 carry-over + v2.0 baru)

| Bug ID | Judul | Severity | Sumber | Status |
|--------|-------|----------|--------|--------|
| Bug-002 | No input validation di llm.py | 🟠 High | v1.0 | Open |
| Bug-003 | Dark mode CSS override | 🟡 Medium | v1.0 | Open |
| Bug-004 | Rate limit tidak user-friendly | 🟠 High | v1.0 | Open |
| Bug-005 | History token growth ke API | 🟠 High | v1.0 partial | Open |
| Bug-006 | `requests` tidak di requirements.txt | 🔴 Critical | v2.0 | Open |
| Bug-007 | Tidak ada validasi ukuran file | 🟠 High | v2.0 | Open |
| Bug-008 | Orphaned message saat stream disconnect | 🟠 High | v2.0 | Open |
| Bug-009 | Session pipeline cache tanpa eviction | 🟡 Medium | v2.0 | Open |
| Bug-010 | File uploader clear memicu session reset | 🟡 Medium | v2.0 | Open |

**Total Bug Aktif: 9** | Critical: 1 | High: 5 | Medium: 3

### Bug yang Ditutup (Fixed di v2.0)

| Bug ID | Judul | Status |
|--------|-------|--------|
| Bug-001 | Missing .gitignore | ✅ FIXED |
| CORS Wildcard | allow_origins=["*"] | ✅ FIXED |
| PDF RAG Indexing | PDF tidak diindeks | ✅ FIXED |
| PDF DB Sync | PDF tidak tercatat di DB | ✅ FIXED |
| Identity Hallucination | Bot mengaku GPT-4 | ✅ FIXED |

---

## 4. Arsitektur Assessment

### ✅ Yang Berhasil Baik di v2.0

```
✅ Decoupled architecture — clean separation of concerns
✅ FastAPI REST API — well-structured dengan router/service/schema layer
✅ SQLAlchemy ORM — proper DB abstraction dengan models
✅ Persistent chat history — SQLite menyelesaikan masalah v1.0
✅ RAG pipeline — fungsional, akurat, dan efisien
✅ PDF support — end-to-end dari upload ke search
✅ Per-session document isolation — clean implementation
✅ CORS restricted — security fix
✅ Optional API key guard — non-breaking, deployable
✅ Swagger UI — auto-generated, memudahkan testing
✅ Session title auto-update — nice UX detail
✅ CLI UTF-8 fix untuk Windows
```

### ❌ Yang Perlu Diperbaiki

```
❌ `requests` missing dari requirements.txt (CRITICAL)
❌ No file size validation (HIGH)
❌ Orphaned message on stream disconnect (HIGH)
❌ Session pipeline cache tanpa eviction (MEDIUM)
❌ File clear trigger full session reset (MEDIUM)
❌ Dark mode CSS masih broken dari v1.0 (MEDIUM)
❌ Input validation di llm.py masih absen (HIGH)
❌ Non-standard SSE format di streaming endpoint (LOW)
❌ Prompt injection defense belum lengkap (MEDIUM)
❌ Pickle deserialization risk untuk vector index (MEDIUM)
```

---

## 5. Security Posture v2.0

```
Score: 5/8 checks passing (v1.0: 4/9)
+1 perbaikan: .gitignore
+1 perbaikan: CORS restricted
+1 perbaikan: API key guard
−1 risiko baru: SQLite berisi PII
−1 risiko baru: Pickle deserialization
```

---

## 6. Regression Assessment

| Category | Count |
|----------|-------|
| v1.0 bugs confirmed fixed | 1/7 |
| v1.0 bugs partially fixed | 2/7 |
| v1.0 bugs still open | 4/7 |
| New bugs introduced in v2.0 | 5 |

---

## 7. Prioritized Recommendations

### 🔴 P1 — Sebelum Distribusi Apapun
1. **Tambah `requests` ke requirements.txt** (Bug-006) — 5 menit fix, impact critical.

### 🟠 P2 — Sprint Berikutnya
2. Tambah validasi ukuran file di backend (Bug-007).
3. Perbaiki orphaned message dengan atomic save (Bug-008).
4. Tambah `_validate_message()` di `core/llm.py` (Bug-002 carry-over).
5. Handle `RateLimitError` secara spesifik (Bug-004 carry-over).
6. Implementasi sliding window untuk history ke Groq API (Bug-005).

### 🟡 P3 — Sebelum Production
7. Implementasi session pipeline eviction/TTL (Bug-009).
8. Pisahkan logika pembersihan dokumen temp dari reset sesi (Bug-010).
9. Fix dark mode CSS (Bug-003 carry-over).
10. Tambah klausa anti-injection ke system prompt.
11. Pertimbangkan migrasi dari Pickle ke format aman.
12. Sanitasi error messages sebelum dikirim ke client.
13. Dokumentasikan model download 80MB di Installation Guide.

---

## 8. QA Verdict v2.0

```
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║   QA VERDICT v2.0: ⚠️  CONDITIONAL PASS                ║
║                                                          ║
║   79.4% overall pass rate                               ║
║   9 bug aktif (1 Critical, 5 High)                      ║
║                                                          ║
║   ✅ APPROVED untuk: Development, Demo, Internal use     ║
║   ❌ NOT APPROVED untuk: Production, Public release      ║
║                                                          ║
║   Syarat minimum sebelum release:                        ║
║   → Fix Bug-006 (requests di requirements.txt)           ║
║   → Fix Bug-007 (file size validation)                   ║
║   → Fix Bug-008 (orphaned message)                       ║
║                                                          ║
║   Catatan positif:                                       ║
║   Arsitektur v2.0 jauh lebih mature dari v1.0.           ║
║   RAG, persistence, dan API layer sangat solid.          ║
║   Dengan 3 fix P1/P2, aplikasi layak untuk beta.         ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
```

---

## 9. Deliverables Checklist v2.0

| Deliverable | File | Status |
|-------------|------|--------|
| Test Plan v2.0 | `docs/TestPlan.md` | ✅ |
| Test Cases v2.0 (45 cases) | `tests/TestCases.md` | ✅ |
| Functional Testing | `tests/FunctionalTesting.md` | ✅ |
| UI Testing | `tests/UITesting.md` | ✅ |
| API Testing | `tests/APITesting.md` | ✅ |
| Negative Testing | `tests/NegativeTesting.md` | ✅ |
| Security Testing | `tests/SecurityTesting.md` | ✅ |
| Performance Testing | `tests/PerformanceTesting.md` | ✅ |
| Bug-006 | `bug_reports/Bug006.md` | ✅ |
| Bug-007 | `bug_reports/Bug007.md` | ✅ |
| Bug-008 | `bug_reports/Bug008.md` | ✅ |
| Bug-009 | `bug_reports/Bug009.md` | ✅ |
| Bug-010 | `bug_reports/Bug010.md` | ✅ |
| Regression Report | `reports/RegressionReport.md` | ✅ |
| Final Report v2.0 | `reports/FinalReport.md` | ✅ |

**Total: 15 deliverables — semua selesai ✅**

---

## 10. Sign-off

| Role | Name | Signature | Date |
|------|------|-----------|------|
| QA Lead | QA Engineering Team | _(signed)_ | 2026-07-10 |
| Backend Dev | — | _(pending)_ | — |
| Project Owner | — | _(pending)_ | — |

---
*IEEE 829 Standard — SH04-AI-Chatbot-LEXA QA Final Report v2.0 — 2026-07-10*
