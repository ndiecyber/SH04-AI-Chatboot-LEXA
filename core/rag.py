import os
import re
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer

class SimpleVectorStore:
    """
    Penyimpanan Vektor sederhana berbasis NumPy dan Pickle.
    Menggunakan SentenceTransformers untuk pembuatan embeddings lokal.
    """
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None  # Lazy loading model
        self.chunks = []
        self.embeddings = None

    @property
    def model(self):
        # Memuat model secara malas (lazy loading) agar tidak membebani memori jika hanya membaca cache
        if self._model is None:
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def add_chunks(self, chunks):
        """Menambahkan chunks dokumen baru dan menghitung embedding-nya."""
        if not chunks:
            return
            
        texts = [c["content"] for c in chunks]
        new_embeddings = self.model.encode(texts, show_progress_bar=False)
        
        self.chunks.extend(chunks)
        
        if self.embeddings is None:
            self.embeddings = new_embeddings
        else:
            self.embeddings = np.vstack([self.embeddings, new_embeddings])

    def search(self, query: str, top_k: int = 3, threshold: float = 0.2):
        """Mencari chunk dokumen teratas yang paling mirip dengan query menggunakan Cosine Similarity."""
        if not self.chunks or self.embeddings is None:
            return []

        # Generate embedding untuk query
        query_embedding = self.model.encode(query, show_progress_bar=False)

        # Hitung cosine similarity
        query_norm = np.linalg.norm(query_embedding)
        if query_norm == 0:
            return []

        matrix_norms = np.linalg.norm(self.embeddings, axis=1)
        matrix_norms = np.where(matrix_norms == 0, 1e-10, matrix_norms)  # Hindari pembagian dengan nol

        similarities = np.dot(self.embeddings, query_embedding) / (matrix_norms * query_norm)

        # Urutkan berdasarkan kemiripan tertinggi
        sorted_indices = np.argsort(similarities)[::-1]

        results = []
        for idx in sorted_indices:
            score = float(similarities[idx])
            if score >= threshold:
                results.append({
                    "chunk": self.chunks[idx],
                    "score": score
                })
            if len(results) >= top_k:
                break
                
        return results

    def save(self, filepath: str):
        """Menyimpan data indeks dan embeddings ke file pickle."""
        data = {
            "model_name": self.model_name,
            "chunks": self.chunks,
            "embeddings": self.embeddings
        }
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "wb") as f:
            pickle.dump(data, f)

    def load(self, filepath: str):
        """Memuat data indeks dan embeddings dari file pickle."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File indeks {filepath} tidak ditemukan.")
            
        with open(filepath, "rb") as f:
            data = pickle.load(f)
            
        self.model_name = data.get("model_name", self.model_name)
        self.chunks = data.get("chunks", [])
        self.embeddings = data.get("embeddings", None)


class RAGPipeline:
    """
    RAG Pipeline untuk mengelola pembacaan folder dokumen, chunking,
    pengindeksan, dan pencarian basis pengetahuan.
    """
    def __init__(self, db_dir="knowledge_base", index_path="knowledge_base/vector_index.pkl"):
        self.db_dir = db_dir
        self.index_path = index_path
        self.vector_store = SimpleVectorStore()

    def chunk_markdown(self, text: str, filename: str) -> list:
        """
        Memotong dokumen markdown berdasarkan header (## atau ###).
        Ini menjaga konteks per fitur atau per topik tetap menyatu.
        """
        # Split teks berdasarkan header utama (## atau ###), pertahankan posisinya
        sections = re.split(r'(?=(?:^|\n)(?:##+\s+))', text)
        chunks = []
        
        # Ekstrak judul utama H1 dari dokumen jika ada
        main_title_match = re.search(r'^#\s+(.+)', text, re.MULTILINE)
        main_title = main_title_match.group(1).strip() if main_title_match else filename
        
        for section in sections:
            section = section.strip()
            if not section:
                continue
            
            chunks.append({
                "content": section,
                "metadata": {
                    "source": filename,
                    "document_title": main_title
                }
            })
        return chunks

    def chunk_text(self, text: str, filename: str, chunk_size: int = 600) -> list:
        """
        Memotong teks biasa atau hasil PDF ke dalam chunks berbasis kalimat
        jika tidak ditemukan header Markdown di dalamnya.
        """
        # Jika teks mengandung tanda-tanda dokumen markdown terstruktur, gunakan chunk_markdown
        if re.search(r'(?:^|\n)(##+\s+)', text):
            return self.chunk_markdown(text, filename)

        # Pisahkan teks berdasarkan paragraf
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = []
        current_size = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # Jika satu paragraf sangat panjang, potong menjadi kalimat
            if len(para) > chunk_size:
                if current_chunk:
                    chunks.append("\n".join(current_chunk))
                    current_chunk = []
                    current_size = 0
                
                # Split per kalimat secara sederhana
                sentences = re.split(r'(?<=[.!?])\s+', para)
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                    if current_size + len(sentence) > chunk_size:
                        if current_chunk:
                            chunks.append(" ".join(current_chunk))
                        current_chunk = [sentence]
                        current_size = len(sentence)
                    else:
                        current_chunk.append(sentence)
                        current_size += len(sentence)
            else:
                if current_size + len(para) > chunk_size:
                    if current_chunk:
                        chunks.append("\n".join(current_chunk))
                    current_chunk = [para]
                    current_size = len(para)
                else:
                    current_chunk.append(para)
                    current_size += len(para)

        if current_chunk:
            chunks.append("\n".join(current_chunk))

        # Bungkus ke format chunk standar dengan metadata
        result_chunks = []
        for i, content in enumerate(chunks):
            result_chunks.append({
                "content": content,
                "metadata": {
                    "source": filename,
                    "document_title": f"{filename} (Bagian {i+1})"
                }
            })
        return result_chunks

    def add_temporary_document(self, file_name: str, text: str):
        """
        Menambahkan teks dokumen sementara (seperti unggahan user)
        ke dalam vector store aktif di memori saja (tanpa menyimpannya ke disk).
        """
        chunks = self.chunk_text(text, file_name)
        if chunks:
            self.vector_store.add_chunks(chunks)
            print(f"Berhasil menambahkan {len(chunks)} chunks dari dokumen sementara '{file_name}' ke memori.")


    def build_index(self):
        """Membaca semua file dokumen, memecahnya ke dalam chunks, dan mengindeksnya."""
        if not os.path.exists(self.db_dir):
            os.makedirs(self.db_dir)
            
        all_chunks = []
        for file in os.listdir(self.db_dir):
            if file.endswith((".md", ".txt")) and file != os.path.basename(self.index_path):
                filepath = os.path.join(self.db_dir, file)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        text = f.read()
                    
                    chunks = self.chunk_markdown(text, file)
                    all_chunks.extend(chunks)
                except Exception as e:
                    print(f"Gagal membaca file {file}: {e}")
                    
        if all_chunks:
            # Buat vector store baru
            self.vector_store = SimpleVectorStore()
            self.vector_store.add_chunks(all_chunks)
            self.vector_store.save(self.index_path)
            print(f"Indeks berhasil dibuat dengan {len(all_chunks)} chunks dokumen.")
        else:
            print("Tidak ada dokumen (.md atau .txt) yang ditemukan untuk diindeks.")

    def load_or_build(self, force_rebuild=False):
        """Memuat indeks dari cache lokal. Jika belum ada, buat indeks baru."""
        if os.path.exists(self.index_path) and not force_rebuild:
            try:
                self.vector_store.load(self.index_path)
                print("Indeks RAG berhasil dimuat dari cache.")
            except Exception as e:
                print(f"Gagal memuat indeks dari cache, membuat ulang: {e}")
                self.build_index()
        else:
            self.build_index()

    def search(self, query: str, top_k: int = 3, threshold: float = 0.2):
        """Mencari dokumen yang relevan dengan query user."""
        return self.vector_store.search(query, top_k=top_k, threshold=threshold)
