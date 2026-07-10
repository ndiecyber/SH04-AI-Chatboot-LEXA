import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import engine, Base, SessionLocal
from backend.globals import base_pipeline
from backend.routers import sessions, chat, documents
from backend.config import KNOWLEDGE_BASE_DIR, INDEX_PATH
from backend.models import Document as DBDocument

app = FastAPI(
    title="LEXA Chatbot API Backend",
    description="Backend API untuk Chatbot Customer Service LEXA dengan RAG Pipeline",
    version="1.0.0"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(sessions.router)
app.include_router(chat.router)
app.include_router(documents.router)

@app.on_event("startup")
def startup_event():
    # 1. Buat tabel database jika belum ada
    Base.metadata.create_all(bind=engine)
    
    # 2. Muat atau bangun indeks RAG
    print("Memuat basis pengetahuan RAG...")
    base_pipeline.load_or_build()
    print("RAG basis pengetahuan dimuat!")
    
    # 3. Sinkronisasi database dengan folder local knowledge_base
    sync_database_documents()

def sync_database_documents():
    """Menyelaraskan data di folder knowledge_base dengan tabel documents SQLite"""
    if not os.path.exists(KNOWLEDGE_BASE_DIR):
        os.makedirs(KNOWLEDGE_BASE_DIR)
        return
        
    db = SessionLocal()
    try:
        # Dapatkan list file dari disk
        disk_files = [f for f in os.listdir(KNOWLEDGE_BASE_DIR) 
                      if f.endswith((".md", ".txt")) and f != os.path.basename(INDEX_PATH)]
        
        # Dapatkan list file dari DB
        db_docs = db.query(DBDocument).all()
        db_filenames = [doc.filename for doc in db_docs]
        
        # 1. Hapus dari DB file-file yang sudah tidak ada di disk
        for doc in db_docs:
            if doc.filename not in disk_files:
                db.delete(doc)
                print(f"Sinkronisasi: Hapus '{doc.filename}' dari DB karena tidak ada di disk.")
                
        # 2. Tambah ke DB file-file baru di disk yang belum tercatat
        for file in disk_files:
            if file not in db_filenames:
                file_path = os.path.join(KNOWLEDGE_BASE_DIR, file)
                file_type = "pdf" if file.endswith(".pdf") else "txt"
                
                # Baca konten untuk menghitung chunk count secara kasar
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    chunks = base_pipeline.chunk_text(content, file)
                    chunk_count = len(chunks)
                except Exception:
                    chunk_count = 0
                    
                new_doc = DBDocument(
                    filename=file,
                    file_type=file_type,
                    chunk_count=chunk_count
                )
                db.add(new_doc)
                print(f"Sinkronisasi: Daftarkan file lokal '{file}' ke database.")
                
        db.commit()
    except Exception as e:
        print(f"Gagal melakukan sinkronisasi database: {e}")
        db.rollback()
    finally:
        db.close()

@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "Selamat datang di LEXA Chatbot API Backend!",
        "docs_url": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
