# Test Summary Report — SH04-AI-Chatbot-LEXA

**Project:** SH04-AI-Chatbot-LEXA | **Version:** 2.0.0  
**Date:** 2026-07-18 *(Update dari 2026-07-10)*  
**Changelog:** Tambah Bug-011, Bug-012, audit llm_tests/, koreksi threshold RAG

---

## Execution Summary

| Metrik | Nilai |
|--------|-------|
| Total Test Cases | 46 *(+1 TC-R-009 baru)* |
| PASS | 50 |
| PARTIAL PASS | 10 |
| FAIL | 3 |
| Overall Pass Rate | **79.4%** |

---

## Bug Status Terkini

```
Total bug terdokumentasi : 12
✅ CLOSED              : 1   (Bug-001)
📝 ACKNOWLEDGED        : 1   (Bug-006)
⚠️  PARTIAL            : 1   (Bug-005)
🔴 OPEN                : 9   (002,003,004,007,008,009,010,011,012)
```

### Yang Baru Sejak Update Terakhir

| Bug | Status | Keterangan |
|-----|--------|------------|
| Bug-011 | 🔴 Open (baru) | `SessionLocal()` manual di generator — connection leak |
| Bug-012 | 🟢 Open (baru) | Inkonsistensi threshold RAG di dokumentasi |
| TC-R-009 | ✅ Ditambahkan | Test isolasi disk dokumen sementara (dari dev scripts) |
| `llm_tests/` | ✅ Diaudit | Developer test scripts diaudit, gap diidentifikasi |
| Bug-006 | 📝 Acknowledged | Developer konfirmasi di `progress_log.md` — belum di-fix |

---

## Bug Priority Board

| 🔴 P1 | 🟠 P2 | 🟡 P3 | 🟢 P4 |
|-------|-------|-------|-------|
| Bug-006 | Bug-011 | Bug-009 | Bug-012 |
| | Bug-008 | Bug-010 | |
| | Bug-007 | Bug-003 | |
| | Bug-002 | | |
| | Bug-004 | | |
| | Bug-005 | | |

---

## File Coverage Audit

| File | Coverage QA |
|------|-------------|
| `core/llm.py` | ✅ Lengkap |
| `core/rag.py` | ✅ Lengkap + koreksi threshold |
| `backend/main.py` | ✅ Lengkap |
| `backend/config.py` | ✅ Lengkap |
| `backend/database.py` | ✅ Lengkap |
| `backend/models.py` | ✅ Lengkap |
| `backend/schemas.py` | ✅ Lengkap |
| `backend/globals.py` | ✅ Lengkap |
| `backend/routers/chat.py` | ✅ Lengkap + Bug-011 baru |
| `backend/routers/sessions.py` | ✅ Lengkap |
| `backend/routers/documents.py` | ✅ Lengkap |
| `backend/services/chat_service.py` | ✅ Lengkap |
| `backend/services/document_service.py` | ✅ Lengkap |
| `app.py` | ✅ Lengkap |
| `main.py` | ✅ Lengkap |
| `requirements.txt` | ✅ Bug-006 |
| `.gitignore` | ✅ Bug-001 closed |
| `.env.example` | ✅ Terdokumentasi |
| `progress_log.md` | ✅ Dibaca — info Bug-006 acknowledged |
| `llm_tests/scratch_rag_test.py` | ✅ **Baru diaudit** |
| `llm_tests/scratch_pdf_test.py` | ✅ **Baru diaudit** |
| `backend/__init__.py` | ⬜ Trivial (kosong) |
| `backend/routers/__init__.py` | ⬜ Trivial (kosong) |
| `backend/services/__init__.py` | ⬜ Trivial (kosong) |
| `core/__init__.py` | ⬜ Trivial (kosong) |

**Coverage: 21/21 file non-trivial = 100% ✅**

---

*QA Engineering Team — 2026-07-18*