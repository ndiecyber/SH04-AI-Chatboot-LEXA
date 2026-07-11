# Test Plan v2.0 — SH04-AI-Chatbot-LEXA

---

## Document Information

| Field | Details |
|-------|---------|
| **Project Name** | SH04-AI-Chatbot-LEXA |
| **Document Title** | Test Plan |
| **Version** | 2.0.0 |
| **Prepared By** | QA Engineering Team |
| **Date** | 2026-07-10 |
| **Status** | Active |
| **Changelog** | Arsitektur berubah total: Streamlit monolith → Decoupled FastAPI + RAG + SQLite |
| **Referensi Sebelumnya** | TestPlan v1.0.0 (2025-07-01) |

---

## 1. Objectives

- Memvalidasi integrasi antara **Frontend (Streamlit/CLI)** dan **Backend (FastAPI)** via REST API.
- Memverifikasi fungsionalitas **RAG Pipeline** (indexing, chunking, similarity search, PDF support).
- Menguji semua endpoint FastAPI: `/api/sessions`, `/api/chat`, `/api/documents`.
- Memvalidasi **persistensi chat history** menggunakan SQLite + SQLAlchemy.
- Memastikan **keamanan** API (CORS fix, optional API key guard, prompt injection).
- Menguji fitur baru: dynamic document upload per-sesi, rebuild RAG index, streaming SSE.
- Meregresi semua bug lama dari v1.0 yang diklaim sudah diperbaiki.
- Mendokumentasikan bug baru yang muncul akibat arsitektur v2.0.

---

## 2. Scope

### 2.1 In Scope

| Area | Komponen |
|------|----------|
| Backend API | `backend/main.py`, routers (chat, sessions, documents), services, models, schemas |
| Core LLM | `core/llm.py` — LexaChatbot, RAG-augmented chat, identity fix |
| Core RAG | `core/rag.py` — RAGPipeline, SimpleVectorStore, PDF + MD + TXT support |
| Frontend Streamlit | `app.py` — REST client, streaming render, document upload UI |
| CLI Interface | `main.py` — REST client, streaming output, session management |
| Database | SQLite (`lexa.db`) — sessions, messages, documents tables |
| Configuration | `backend/config.py`, `.env`, `backend/database.py` |
| Security | CORS config, LEXA_API_KEY guard, prompt injection |
| Performance | RAG latency, embedding cold start, streaming throughput, memory |
| Regression | Bug-001 s/d Bug-005 + ST-005 dari laporan v1.0 |

### 2.2 Out of Scope

- Infrastruktur deployment (Docker, cloud hosting, nginx).
- JWT/OAuth2 authentication (backlog).
- ChromaDB / Qdrant integration (belum diimplementasi).
- `.docx` / `.xlsx` document parser (belum diimplementasi).
- Multi-worker production deployment.

---

## 3. Arsitektur Sistem v2.0

```
┌──────────────────────────────────────────────────────────┐
│  Client Layer                                            │
│  ┌─────────────┐         ┌────────────────────────────┐ │
│  │  main.py    │         │        app.py              │ │
│  │  (CLI REST) │         │  (Streamlit REST Client)   │ │
│  └──────┬──────┘         └────────────┬───────────────┘ │
└─────────┼───────────────────────────┼──────────────────┘
          │ HTTP/REST                  │ HTTP/REST + SSE
          ▼                            ▼
┌──────────────────────────────────────────────────────────┐
│  FastAPI Backend (:8000)                                 │
│  ┌────────────┬───────────┬──────────────────────────┐  │
│  │ /sessions  │  /chat    │  /documents              │  │
│  │ router     │  router   │  router                  │  │
│  └─────┬──────┴─────┬─────┴──────────┬───────────────┘  │
│        │             │                │                   │
│  ┌─────▼─────────────▼────────────────▼─────────────┐   │
│  │           Services Layer                          │   │
│  │    ChatService      DocumentService               │   │
│  └─────┬──────────────────────┬────────────────────┘   │
│        │                      │                          │
│  ┌─────▼──────┐    ┌──────────▼───────────────────┐    │
│  │ SQLite DB  │    │  Core Layer                  │    │
│  │ lexa.db    │    │  LexaChatbot + RAGPipeline   │    │
│  │ sessions   │    │  SimpleVectorStore           │    │
│  │ messages   │    │  sentence-transformers       │    │
│  │ documents  │    └──────────┬───────────────────┘    │
│  └────────────┘               │ HTTPS                   │
└───────────────────────────────┼─────────────────────────┘
                                 ▼
                        Groq Cloud API
                     (openai/gpt-oss-120b)
```

---

## 4. Test Environment

| Komponen | Versi / Spesifikasi |
|----------|---------------------|
| Python | 3.9+ (recommended 3.11) |
| FastAPI | Latest stable |
| Uvicorn | Latest stable (with standard) |
| SQLAlchemy | Latest stable |
| Streamlit | Latest stable |
| groq SDK | Latest stable |
| sentence-transformers | Latest stable (model: all-MiniLM-L6-v2 ~80MB) |
| numpy | Latest stable |
| pypdf | Latest stable |
| python-multipart | Latest stable |
| requests | Latest stable *(tidak ada di requirements.txt — Bug-006)* |
| OS | Windows 10/11, Ubuntu 22.04+, macOS 13+ |
| DB | SQLite (`lexa.db`) |
| Port Backend | 8000 |
| Port Frontend | 8501 |

**Startup Order yang Benar:**
```
1. uvicorn backend.main:app --host 127.0.0.1 --port 8000
2. streamlit run app.py         (tunggu backend ready dulu)
# CLI: python main.py           (opsional, paralel dengan streamlit)
```

---

## 5. Test Types

| Tipe | Ruang Lingkup |
|------|---------------|
| Functional | Lifecycle chat end-to-end, RAG pipeline, session management |
| API/Integration | Semua endpoint FastAPI, request/response validation |
| UI | Streamlit layout, konektivitas API, upload UI, referensi display |
| CLI | CLI streaming, error handling, session management |
| Negative | Input invalid, file rusak, API mati, format tidak didukung |
| Security | CORS, API key guard, prompt injection, pickle risk, error leakage |
| Performance | RAG latency, cold start, streaming, memory growth |
| Regression | Verifikasi semua bug v1.0 — fixed atau masih open |

---

## 6. Entry Criteria

- [ ] `uvicorn backend.main:app` berjalan tanpa error.
- [ ] `GROQ_API_KEY` valid ada di `.env`.
- [ ] Semua dependencies terinstall (termasuk `requests` manual — Bug-006).
- [ ] `http://127.0.0.1:8000/docs` dapat diakses (Swagger UI).
- [ ] SQLite DB terbuat otomatis (`lexa.db`).
- [ ] RAG index berhasil dimuat atau dibangun.
- [ ] Minimal 1 dokumen ada di `knowledge_base/`.

---

## 7. Exit Criteria

- [ ] ≥ 45 test cases dieksekusi.
- [ ] Overall pass rate ≥ 80%.
- [ ] Semua bug Critical diselesaikan.
- [ ] Regression report lengkap.
- [ ] Semua deliverables QA v2.0 selesai.

---

## 8. Risks v2.0

| Risk ID | Deskripsi | Likelihood | Impact | Mitigasi |
|---------|-----------|------------|--------|----------|
| R-001 | `requests` tidak di requirements.txt | High | Critical | Tambah segera |
| R-002 | Backend harus jalan sebelum frontend | High | High | Dokumentasikan urutan startup |
| R-003 | Model download 80MB saat pertama kali | Medium | Medium | Tambah ke install guide |
| R-004 | Pickle vector index tidak aman | Medium | High | Migrasikan ke ChromaDB |
| R-005 | Session pipeline memory leak | Medium | High | Implementasikan eviction |
| R-006 | Orphaned user message saat stream gagal | Medium | Medium | Atomic save setelah stream |
| R-007 | SQLite concurrent write di multi-worker | Low | High | Gunakan PostgreSQL untuk prod |
| R-008 | Stream error leakage ke client | Medium | Medium | Sanitasi error message |

---

## 9. Deliverables v2.0

| Deliverable | File | Status |
|-------------|------|--------|
| Test Plan v2.0 | `docs/TestPlan.md` | ✅ |
| Test Cases v2.0 | `tests/TestCases.md` | ✅ |
| Functional Testing v2.0 | `tests/FunctionalTesting.md` | ✅ |
| UI Testing v2.0 | `tests/UITesting.md` | ✅ |
| API Testing v2.0 | `tests/APITesting.md` | ✅ |
| Negative Testing v2.0 | `tests/NegativeTesting.md` | ✅ |
| Security Testing v2.0 | `tests/SecurityTesting.md` | ✅ |
| Performance Testing v2.0 | `tests/PerformanceTesting.md` | ✅ |
| Bug Reports (006–010) | `bug_reports/Bug00X.md` | ✅ |
| Regression Report | `reports/RegressionReport.md` | ✅ |
| QA Report | `reports/QA_Report.md` | ✅ |
| Test Summary | `reports/TestSummary.md` | ✅ |
| Final Report v2.0 | `reports/FinalReport.md` | ✅ |
| User Guide v2.0 | `docs/UserGuide.md` | ✅ |
| Installation Guide v2.0 | `docs/InstallationGuide.md` | ✅ |
| Technical Documentation v2.0 | `docs/TechnicalDocumentation.md` | ✅ |

---

## 10. Approval

| Role | Name | Signature | Date |
|------|------|-----------|------|
| QA Lead | QA Engineering Team | _(signed)_ | 2026-07-10 |
| Backend Dev | — | _(pending)_ | — |
| Project Owner | — | _(pending)_ | — |

---
*IEEE 829 Standard — SH04-AI-Chatbot-LEXA Test Plan v2.0 — 2026-07-10*
