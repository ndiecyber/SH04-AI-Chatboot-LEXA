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

    print("=== Menjalankan Uji Coba RAG Dokumen Dinamis ===")
    
    # 1. Inisialisasi Pipeline dan muat indeks dasar
    # Kita arahkan database ke folder root/knowledge_base
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_dir = os.path.join(project_root, "knowledge_base")
    index_path = os.path.join(db_dir, "vector_index.pkl")
    
    pipeline = RAGPipeline(db_dir=db_dir, index_path=index_path)
    pipeline.load_or_build()
    
    initial_chunk_count = len(pipeline.vector_store.chunks)
    print(f"Indeks dasar berhasil dimuat: {initial_chunk_count} chunks.")
    
    # 2. Simulasikan dokumen sementara yang baru diunggah (misal teks panjang dari PDF)
    uploaded_doc_name = "panduan_kucing_anggora.txt"
    uploaded_doc_text = (
        "Panduan Pemeliharaan Kucing Anggora Super\n\n"
        "Kucing Anggora adalah salah satu ras kucing tertua yang berasal dari Ankara, Turki. "
        "Kucing ini memiliki bulu panjang yang halus dan tubuh yang ramping berotot.\n\n"
        "Pola Makan & Nutrisi Kucing Anggora:\n"
        "Untuk menjaga bulunya tetap berkilau dan sehat, Kucing Anggora sebaiknya diberi makan "
        "ikan asin berkualitas tinggi sebanyak 3 kali sehari. Hindari makanan yang mengandung "
        "banyak pengawet kimia karena bisa memicu kerontokan bulu.\n\n"
        "Perawatan Bulu (Grooming):\n"
        "Sisir bulu kucing Anggora minimal sekali sehari menggunakan sisir bergigi jarang untuk "
        "mencegah bulunya menggumpal (tangled)."
    )
    
    print(f"\n--- Mengunggah Dokumen Dinamis: '{uploaded_doc_name}' ---")
    pipeline.add_temporary_document(uploaded_doc_name, uploaded_doc_text)
    
    post_chunk_count = len(pipeline.vector_store.chunks)
    print(f"Jumlah chunks setelah unggah sementara: {post_chunk_count} chunks (Bertambah {post_chunk_count - initial_chunk_count} chunks).")
    
    # 3. Uji Coba Pencarian pada Dokumen Sementara
    query = "berapa kali kucing anggora makan dalam sehari dan apa makanannya?"
    print(f"\nQuery Pencarian: '{query}'")
    results = pipeline.search(query, top_k=1, threshold=0.1)
    
    if results:
        res = results[0]
        chunk = res["chunk"]
        score = res["score"]
        source = chunk["metadata"]["source"]
        doc_title = chunk["metadata"]["document_title"]
        print(f"  [Hasil Ditemukan] (Skor: {score:.4f})")
        print(f"  Sumber: {source} | Judul: {doc_title}")
        print(f"  Konten:\n  | {chunk['content'].replace(chr(10), chr(10) + '  | ')}")
    else:
        print("  [Gagal] Hasil pencarian tidak menemukan dokumen dinamis yang relevan.")
        sys.exit(1)
        
    # 4. Verifikasi Keamanan (Pastikan data sementara tidak masuk ke file indeks permanen)
    print("\n--- Memverifikasi Keamanan Indeks Permanen ---")
    # Inisialisasi pipeline baru dari disk untuk cek apakah data kucing anggora tersimpan
    clean_pipeline = RAGPipeline(db_dir=db_dir, index_path=index_path)
    clean_pipeline.load_or_build()
    
    clean_chunk_count = len(clean_pipeline.vector_store.chunks)
    print(f"Jumlah chunks di pipeline bersih (dari disk): {clean_chunk_count}")
    
    if clean_chunk_count == initial_chunk_count:
        print("[Sukses] Verifikasi Sukses: Dokumen dinamis hanya disimpan di memori dan TIDAK bocor ke disk!")
    else:
        print("[Error] Kegagalan Keamanan: Dokumen dinamis tidak sengaja tersimpan ke disk!")
        sys.exit(1)

if __name__ == "__main__":
    main()
