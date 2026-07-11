# QA Report v2.0 — SH04-AI-Chatbot-LEXA

**Project:** SH04-AI-Chatbot-LEXA  
**Version:** 2.0.0  
**QA Lead:** QA Engineering Team  
**Date:** 2026-07-10

---

## 1. Executive Summary

SH04-AI-Chatbot-LEXA v2.0 menghadirkan perubahan arsitektur yang signifikan dan matang: dari monolith Streamlit menjadi sistem decoupled FastAPI backend + RAG pipeline + SQLite persistence. Peningkatan kualitas dibandingkan v1.0 sangat nyata — terutama dari sisi persistensi data, kemampuan RAG, dan pemisahan concerns yang bersih.

**Namun**, 1 bug Critical baru ditemukan (Bug-006: `requests` tidak di `requirements.txt`) yang menyebabkan **fresh install gagal total** sebelum aplikasi sempat dijalankan. Ini harus diperbaiki segera sebelum distribusi apapun.

**Verdict: CONDITIONAL PASS** — matang secara arsitektur, perlu 1 critical fix dan beberapa high fixes.

---

## 2. Coverage Summary

| Kategori | Cases | PASS | PARTIAL | FAIL | Rate |
|----------|-------|------|---------|------|------|
| Functional | 12 | 12 | 0 | 0 | **100%** |
| RAG Pipeline | 8 | 8 | 0 | 0 | **100%** |
| API/Integration | 8 | 8 | 0 | 0 | **100%** |
| UI | 12 | 8 | 3 | 1 | **66.7%** |
| Negative | 10 | 6 | 2 | 2 | **60%** |
| Security | 6 | 3 | 3 | 0 | **50%** |
| Performance | 7 | 5 | 2 | 0 | **71.4%** |
| **TOTAL** | **63** | **50** | **10** | **3** | **79.4%** |

---

## 3. Bug Statistics

| Severity | Jumlah | Bug IDs |
|----------|--------|---------|
| 🔴 Critical | 1 | Bug-006 |
| 🟠 High | 5 | Bug-002, Bug-004, Bug-005, Bug-007, Bug-008 |
| 🟡 Medium | 3 | Bug-003, Bug-009, Bug-010 |
| **Total Aktif** | **9** | |

| Status | Jumlah |
|--------|--------|
| Confirmed Fixed | 5 *(dari v1.0)* |
| Still Open (carry-over) | 4 *(dari v1.0)* |
| New Bugs in v2.0 | 5 |

---

## 4. Regression Result

| Bug v1.0 | Status |
|----------|--------|
| Bug-001 (gitignore) | ✅ FIXED |
| Bug-002 (input validation) | ⚠️ STILL OPEN |
| Bug-003 (dark mode) | ⚠️ STILL OPEN |
| Bug-004 (rate limit) | ⚠️ STILL OPEN |
| Bug-005 (history growth) | ⚠️ PARTIALLY FIXED |
| CORS wildcard | ✅ FIXED |
| PDF indexing | ✅ FIXED |
| PDF DB sync | ✅ FIXED |
| Identity hallucination | ✅ FIXED |

---

## 5. Strength vs Weakness

**✅ Strengths:**
- Arsitektur decoupled yang bersih dan scalable
- FastAPI dengan layering router/service/schema yang proper
- SQLite persistence — riwayat chat tidak hilang lagi
- RAG pipeline fungsional dengan referensi sumber yang transparan
- PDF support end-to-end
- CORS fix — security posture meningkat
- Optional API key guard
- Per-session document isolation
- Swagger UI auto-generated

**❌ Weaknesses:**
- `requests` tidak di requirements.txt (fresh install crash)
- Tidak ada file size validation
- Orphaned message saat stream disconnect
- Session pipeline memory leak
- Dark mode CSS masih broken
- Prompt injection defense belum complete
- Pickle deserialization risk
- Non-standard SSE format
- Error leakage dalam stream response

---

## 6. Recommendations

| Priority | Action |
|----------|--------|
| 🔴 P1 | Tambah `requests` ke `requirements.txt` |
| 🟠 P2 | Tambah file size validation (max 10MB) di backend |
| 🟠 P2 | Perbaiki orphaned message dengan atomic DB save |
| 🟠 P2 | Tambah `_validate_message()` di `core/llm.py` |
| 🟠 P2 | Handle `RateLimitError` secara spesifik |
| 🟠 P2 | Implementasikan sliding window untuk history ke API |
| 🟡 P3 | Tambah TTL/eviction untuk `_session_pipelines` |
| 🟡 P3 | Pisahkan file-clear dari session-reset |
| 🟡 P3 | Fix dark mode CSS |
| 🟡 P3 | Harden system prompt anti-injection |
| 🟡 P3 | Migrasi Pickle ke format aman |
| 🟡 P3 | Sanitasi error message dalam stream |

---

## 7. QA Sign-off

**Status:** CONDITIONAL PASS  
**QA Lead:** QA Engineering Team — 2026-07-10  
**Re-test Required:** Ya, setelah Bug-006, Bug-007, Bug-008 diperbaiki.