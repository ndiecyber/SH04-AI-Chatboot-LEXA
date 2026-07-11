# Technical Documentation v2.0 — SH04-AI-Chatbot-LEXA

**Project:** SH04-AI-Chatbot-LEXA  
**Version:** 2.0.0  
**Last Updated:** 2026-07-10  
**Audience:** Developer, Technical Reviewer, QA Engineer

---

## 1. Repository Structure

```
SH04-AI-Chatboot-LEXA/
├── backend/
│   ├── main.py              ← FastAPI app, CORS, middleware, startup events
│   ├── config.py            ← Env vars, Settings class (pydantic)
│   ├── database.py          ← SQLAlchemy engine, SessionLocal, Base
│   ├── models.py            ← ORM models: Session, Message, Document
│   ├── schemas.py           ← Pydantic schemas: request/response DTOs
│   ├── globals.py           ← Global RAG pipeline instance
│   └── routers/
│   │   ├── chat.py          ← /api/chat endpoints
│   │   ├── sessions.py      ← /api/sessions endpoints
│   │   └── documents.py     ← /api/documents endpoints
│   └── services/
│       ├── chat_service.py      ← Business logic: chat, history, RAG
│       └── document_service.py  ← Business logic: upload, index, sync
├── core/
│   ├── llm.py               ← LexaChatbot class (Groq API wrapper)
│   └── rag.py               ← RAGPipeline, SimpleVectorStore
├── knowledge_base/          ← Dokumen basis pengetahuan (.md, .txt, .pdf)
├── app.py                   ← Streamlit frontend
├── main.py                  ← CLI frontend
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## 2. Module Documentation

### 2.1 `core/llm.py` — LexaChatbot

Wrapper di atas Groq SDK. Tidak berubah signifikan dari v1.0, tapi system prompt diperbarui.

**System Prompt v2.0 — Perubahan Kunci:**
```python
# Ditambahkan di v2.0:
"Anda ditenagai oleh model open-source GPT-OSS (bukan GPT-4 atau buatan OpenAI). "
"Ingatlah identitas Anda ini dan jangan pernah mengaku sebagai model buatan OpenAI."
```

**Method Utama:**

| Method | Signature | Deskripsi |
|--------|-----------|-----------|
| `__init__` | `(system_instruction=None, model="openai/gpt-oss-120b")` | Init Groq client, load API key |
| `reset_chat` | `() → None` | Reset history ke system prompt saja |
| `send_message` | `(message: str) → str` | Sync chat, return full response |
| `send_message_stream` | `(message: str) → Generator[str]` | Streaming chat, yield token chunks |

**Known Issue:** Tidak ada `_validate_message()` — Bug-002 dari v1.0 masih open.

---

### 2.2 `core/rag.py` — RAG Pipeline

Komponen baru di v2.0. Mengimplementasikan Retrieval-Augmented Generation menggunakan sentence-transformers dan vector similarity search sederhana.

#### Class: `SimpleVectorStore`

```python
class SimpleVectorStore:
    chunks: list[dict]          # {"content": str, "metadata": dict}
    embeddings: np.ndarray      # shape: (n_chunks, embedding_dim)
    model: SentenceTransformer  # all-MiniLM-L6-v2
```

**Methods:**

| Method | Deskripsi |
|--------|-----------|
| `add_texts(chunks, metadatas)` | Encode dan simpan chunks ke vector store |
| `search(query, k=3, threshold=0.15)` | Cosine similarity search, return top-k di atas threshold |
| `save(filepath)` | Serialize ke Pickle file |
| `load(filepath)` | Deserialize dari Pickle file |

**⚠️ Security Note:** `pickle.load()` digunakan — risiko jika file tidak terpercaya (lihat ST2-004).

#### Class: `RAGPipeline`

```python
class RAGPipeline:
    knowledge_base_dir: str          # default: "knowledge_base"
    index_file: str                  # "knowledge_base/vector_index.pkl"
    vector_store: SimpleVectorStore
```

**Methods:**

| Method | Deskripsi |
|--------|-----------|
| `load_or_build()` | Load cache jika ada, build dari scratch jika tidak |
| `build_index()` | Proses semua file .md/.txt/.pdf → chunk → embed → simpan |
| `search(query, k=3)` | Proxy ke `vector_store.search()` |
| `add_documents(texts, metadatas)` | Tambah dokumen ke index yang sudah ada (untuk temp upload) |

**Chunking Strategy:**
- `.md` files: Split by header (`##`)
- `.txt` files: Split by double newline (paragraf)
- `.pdf` files: Extract text per halaman via `pypdf`, split jika > 500 chars

**Threshold:** Score cosine similarity ≥ 0.15 untuk dikembalikan sebagai referensi.

---

### 2.3 `backend/main.py` — FastAPI Application

```python
app = FastAPI(title="LEXA Chatbot API", ...)

# CORS — Restricted (fixed dari v1.0 wildcard)
app.add_middleware(CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Optional API Key Guard Middleware
# Aktif hanya jika LEXA_API_KEY diset di .env

# Startup Event
@app.on_event("startup")
async def startup_event():
    create_db_tables()       # SQLAlchemy create_all()
    load_rag_pipeline()      # Load/build vector index
    sync_database_documents() # Sinkronisasi file lokal ke DB
```

**Routers:**
```python
app.include_router(sessions_router, prefix="/api/sessions", tags=["sessions"])
app.include_router(chat_router, prefix="/api/chat", tags=["chat"])
app.include_router(documents_router, prefix="/api/documents", tags=["documents"])
```

---

### 2.4 `backend/models.py` — Database Models

```python
class DBSession(Base):
    __tablename__ = "sessions"
    id: str (PK)          # UUID string, digenerate client
    title: str
    created_at: datetime
    updated_at: datetime
    messages: relationship → DBMessage (cascade delete)
    documents: relationship → DBDocument

class DBMessage(Base):
    __tablename__ = "messages"
    id: int (PK, autoincrement)
    session_id: str (FK → sessions.id, CASCADE)
    role: str             # "user" atau "assistant"
    content: str
    created_at: datetime

class DBDocument(Base):
    __tablename__ = "documents"
    id: int (PK, autoincrement)
    filename: str
    file_path: str
    file_type: str        # "pdf", "txt", "md"
    chunk_count: int
    uploaded_at: datetime
    session_id: str (nullable) # null = global document
```

---

### 2.5 `backend/services/chat_service.py` — Chat Service

Inti logika percakapan. Bertanggung jawab atas rekonstruksi history, RAG search, dan penyimpanan pesan.

**Flow `send_chat_message()`:**
```
1. get_or_create_session(session_id, db)
2. Ambil semua pesan dari DB: db.query(DBMessage).filter_by(session_id)
3. Rekonstruksi: history = [system_prompt] + [{role, content} for msg in db_messages]
4. Tentukan RAG pipeline: session pipeline (jika ada) atau global pipeline
5. RAG search: references = pipeline.search(message, k=3)
6. Jika references ada: tambahkan konteks ke pesan terakhir
7. Simpan user message ke DB
8. chatbot.send_message(message) → reply
9. Simpan assistant message ke DB
10. Update session.updated_at
11. Return reply + references
```

**In-Memory State:**
```python
_session_pipelines: dict[str, RAGPipeline] = {}  # Per-session pipeline cache
_last_references: dict[str, list] = {}            # Last RAG references per session
```

---

### 2.6 `backend/routers/chat.py` — Streaming Endpoint

```python
@router.post("/{session_id}/stream")
async def send_chat_message_stream(session_id: str, chat_req: ChatRequest, ...):
    
    def event_generator():
        full_reply = ""
        # Simpan user message SEBELUM streaming
        db.add(DBMessage(role="user", content=chat_req.message, ...))
        db.commit()
        
        try:
            for chunk in chatbot.send_message_stream(chat_req.message):
                full_reply += chunk
                yield chunk     # Raw token, bukan SSE format
            
            # Simpan assistant message SETELAH streaming selesai
            db.add(DBMessage(role="assistant", content=full_reply, ...))
            db.commit()
        except Exception as e:
            yield f"\n[ERROR: {str(e)}]"  # ⚠️ Raw error ke client
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

**⚠️ Known Issue (Bug-008):** Jika error terjadi mid-stream, user message sudah tersimpan tapi assistant message tidak. Menghasilkan orphaned user message di DB.

---

### 2.7 `app.py` — Streamlit Frontend

**Session State Keys:**

| Key | Type | Deskripsi |
|-----|------|-----------|
| `session_id` | `str` | UUID sesi aktif |
| `indexed_files` | `set[str]` | Nama file yang sudah diindex di sesi ini |

**Koneksi ke Backend:**
```python
API_URL = "http://127.0.0.1:8000"

# Health check on startup
requests.get(API_URL, timeout=3)

# Streaming chat
response = requests.post(f"{API_URL}/api/chat/{session_id}/stream",
                         json={"message": prompt}, stream=True)
for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
    full_response += chunk
    placeholder.markdown(full_response + "▌")
```

---

## 3. Database Schema

```sql
CREATE TABLE sessions (
    id VARCHAR PRIMARY KEY,
    title VARCHAR DEFAULT 'Percakapan Baru',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id VARCHAR REFERENCES sessions(id) ON DELETE CASCADE,
    role VARCHAR NOT NULL,        -- 'user' | 'assistant'
    content TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename VARCHAR NOT NULL,
    file_path VARCHAR NOT NULL,
    file_type VARCHAR NOT NULL,   -- 'pdf' | 'txt' | 'md'
    chunk_count INTEGER DEFAULT 0,
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    session_id VARCHAR            -- NULL = global
);
```

---

## 4. API Reference Summary

| Method | Endpoint | Auth | Request | Response |
|--------|----------|------|---------|----------|
| GET | `/` | No | — | `{status, message, docs_url}` |
| POST | `/api/sessions/` | Optional | `SessionCreate` | `SessionResponse` 201 |
| GET | `/api/sessions/` | Optional | — | `list[SessionResponse]` |
| DELETE | `/api/sessions/{id}` | Optional | — | 204 |
| POST | `/api/chat/{id}` | Optional | `ChatRequest` | `ChatResponse` |
| GET | `/api/chat/{id}/history` | Optional | — | `list[MessageResponse]` |
| POST | `/api/chat/{id}/stream` | Optional | `ChatRequest` | `StreamingResponse` |
| GET | `/api/chat/{id}/last-references` | Optional | — | `list[Reference]` |
| GET | `/api/documents/` | Optional | — | `list[DocumentResponse]` |
| POST | `/api/documents/upload` | Optional | `multipart/form-data` | `DocumentResponse` 201 |
| DELETE | `/api/documents/{id}` | Optional | — | 204 |
| POST | `/api/documents/rebuild-index` | Optional | — | `{status, message}` |
| POST | `/api/documents/upload-temp/{sid}` | Optional | `multipart/form-data` | `{status, message}` |

---

## 5. Dependency Map

```
app.py ──────────────────────────────────────────► requests
  │                                                  │
  └──────────────► backend/main.py (FastAPI)          │
                        │                             │
                   backend/services/                  │
                   chat_service.py ──────► core/llm.py → groq
                        │         └──────► core/rag.py → sentence-transformers
                        │                               → numpy
                        │                               → pypdf
                   document_service.py ──► core/rag.py
                        │
                   backend/models.py ──────────────── SQLAlchemy
                   backend/database.py ─────────────── SQLite (lexa.db)
```

---

## 6. Known Limitations v2.0

| Limitasi | Dampak | Rekomendasi |
|----------|--------|-------------|
| `requests` tidak di requirements.txt | Fresh install gagal | Tambah ke requirements.txt |
| Pickle untuk vector index | Security risk | Migrasikan ke ChromaDB |
| SQLite single-writer | Multi-worker crash | Gunakan PostgreSQL untuk prod |
| Tidak ada file size validation | OOM risk | Tambah guard 10MB |
| Session pipeline tanpa eviction | Memory leak | Tambah TTL/LRU eviction |
| Non-standard SSE format | Kompatibilitas terbatas | Gunakan `data: chunk\n\n` format |
| History penuh dikirim ke Groq | Latency meningkat | Sliding window 20 turns |
| Tidak ada JWT authentication | Semua user share key | Implementasi auth layer |

---

## 7. Extending v2.0

### Ganti Model LLM
```python
# Di .env:
LEXA_MODEL=llama-3.3-70b-versatile

# Atau saat init:
bot = LexaChatbot(model="llama-3.1-8b-instant")
```

### Tambah Dokumen Permanen ke Basis Pengetahuan
```bash
cp your_document.pdf knowledge_base/
# Kemudian rebuild via API:
curl -X POST http://127.0.0.1:8000/api/documents/rebuild-index
```

### Aktifkan API Key Protection
```env
# Di .env:
LEXA_API_KEY=mysecretkey123
```
Semua request ke `/api/*` harus menyertakan header:
```
Authorization: Bearer mysecretkey123
```

### Custom System Prompt
```python
# Di core/llm.py, modifikasi self.default_system_instruction
```
