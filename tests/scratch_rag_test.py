import os
import sys

# Tambahkan path root proyek agar dapat mengimport modul di dalam core/
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.rag import RAGPipeline

def main():
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass

    print("=== Menjalankan Uji Coba RAG Pipeline ===")
    
    # 1. Inisialisasi Pipeline
    # Kita arahkan database ke folder root/knowledge_base
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_dir = os.path.join(project_root, "knowledge_base")
    index_path = os.path.join(db_dir, "vector_index.pkl")
    
    pipeline = RAGPipeline(db_dir=db_dir, index_path=index_path)
    
    # 2. Bangun Indeks (force rebuild untuk memastikan data terbaru terindeks)
    print("\n--- Membangun Indeks Vektor ---")
    pipeline.load_or_build(force_rebuild=True)
    
    # 3. Uji Coba Pencarian
    queries = [
        "bagaimana cara menghubungkan dengan whatsapp?",
        "berapa harga paket pro bulannya?",
        "apakah data saya aman?",
        "bagaimana jika bot tidak bisa menjawab pertanyaan?"
    ]
    
    print("\n--- Menguji Pencarian Relevansi ---")
    for q in queries:
        print(f"\nQuery: '{q}'")
        results = pipeline.search(q, top_k=2, threshold=0.1)
        
        if not results:
            print("  Hasil: Tidak ada dokumen relevan yang ditemukan.")
            continue
            
        for i, res in enumerate(results):
            chunk = res["chunk"]
            score = res["score"]
            source = chunk["metadata"]["source"]
            doc_title = chunk["metadata"]["document_title"]
            
            print(f"  [Hasil {i+1}] (Skor: {score:.4f}) | Sumber: {source} ({doc_title})")
            # Cetak 3 baris pertama dari konten chunk
            lines = chunk["content"].split("\n")
            preview = "\n  | ".join(lines[:4])
            print(f"  | {preview}\n  | ...")

if __name__ == "__main__":
    main()
