import os
import re
import hashlib
import logging
import urllib.error
import urllib.request
import chromadb
from chromadb.utils import embedding_functions
import PyPDF2

logger = logging.getLogger("lexa")

DEFAULT_KB_URL = "https://sh-01-company-profile.vercel.app/api/knowledge-base"

class ChromaVectorStore:
    """
    Penyimpanan Vektor menggunakan ChromaDB.
    """
    def __init__(self, persist_directory="knowledge_base/chroma_db", model_name="all-MiniLM-L6-v2"):
        self.persist_directory = persist_directory
        self.model_name = model_name
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=self.model_name)
        
        self.collection = self.client.get_or_create_collection(
            name="lexa_kb",
            embedding_function=self.embedding_fn
        )

    def add_chunks(self, chunks):
        """Menambahkan chunks dokumen baru ke ChromaDB."""
        if not chunks:
            return
            
        documents = []
        metadatas = []
        ids = []
        
        for i, chunk in enumerate(chunks):
            documents.append(chunk["content"])
            metadatas.append(chunk["metadata"])
            # Generate ID unik berdasarkan konten dan indeks
            content_hash = hashlib.md5(chunk['content'].encode()).hexdigest()
            ids.append(f"doc_{i}_{content_hash}")
            
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

    def search(self, query: str, top_k: int = 3, threshold: float = 0.2):
        """Mencari chunk dokumen teratas yang relevan."""
        if self.collection.count() == 0:
            return []
            
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            include=['documents', 'metadatas', 'distances']
        )
        
        formatted_results = []
        if results['documents'] and len(results['documents']) > 0:
            for i in range(len(results['documents'][0])):
                distance = results['distances'][0][i]
                # Konversi jarak L2 default ChromaDB ke pseudo-similarity score
                score = 1.0 / (1.0 + distance)
                
                if score >= threshold:
                    formatted_results.append({
                        "chunk": {
                            "content": results['documents'][0][i],
                            "metadata": results['metadatas'][0][i]
                        },
                        "score": score
                    })
        return formatted_results

    def save(self, filepath: str):
        """ChromaDB otomatis menyimpan ke disk, metode ini dipertahankan untuk kompatibilitas."""
        pass

    def load(self, filepath: str):
        """ChromaDB otomatis memuat dari disk, metode ini dipertahankan untuk kompatibilitas."""
        pass


class RAGPipeline:
    """
    RAG Pipeline untuk mengelola pembacaan folder dokumen, chunking,
    pengindeksan, dan pencarian basis pengetahuan.
    """
    def __init__(
        self,
        db_dir="knowledge_base",
        index_path="knowledge_base/vector_index.pkl",
        kb_url=None,
    ):
        self.db_dir = db_dir
        self.index_path = index_path
        self.chroma_dir = os.path.join(self.db_dir, "chroma_db")
        self.kb_url = kb_url or os.getenv("KNOWLEDGE_BASE_URL", DEFAULT_KB_URL)
        self.vector_store = ChromaVectorStore(persist_directory=self.chroma_dir)

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
            logger.info(f"Berhasil menambahkan {len(chunks)} chunks dari dokumen sementara '{file_name}' ke memori.")


    def fetch_remote_kb(self, url: str = None) -> str:
        """Mengambil basis pengetahuan markdown dari API company profile."""
        url = url or self.kb_url
        request = urllib.request.Request(url, headers={"User-Agent": "LexaChatbot/1.0"})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.read().decode("utf-8")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Gagal mengambil basis pengetahuan dari {url}: {e}") from e

    def _cache_kb_text(self, text: str) -> str:
        """Menyimpan salinan lokal basis pengetahuan untuk fallback offline."""
        os.makedirs(self.db_dir, exist_ok=True)
        cache_path = os.path.join(self.db_dir, "lexa_company_profile.md")
        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(text)
        return cache_path

    def _load_cached_kb_text(self):
        cache_path = os.path.join(self.db_dir, "lexa_company_profile.md")
        if not os.path.exists(cache_path):
            return None
        with open(cache_path, "r", encoding="utf-8") as f:
            return f.read()

    def build_index_from_url(self, url: str = None):
        """Fetch KB dari API, cache ke disk, lalu bangun indeks vektor."""
        filename = "lexa_company_profile.md"
        try:
            text = self.fetch_remote_kb(url)
            self._cache_kb_text(text)
            logger.info(f"Basis pengetahuan berhasil diambil dari API.")
        except RuntimeError as e:
            cached = self._load_cached_kb_text()
            if cached:
                text = cached
                logger.warning(f"Peringatan: {e}. Menggunakan cache lokal.")
            else:
                raise RuntimeError(
                    f"{e} Tidak ada cache lokal. Pastikan koneksi internet aktif."
                ) from e

        chunks = self.chunk_markdown(text, filename)
        if not chunks:
            raise RuntimeError("Basis pengetahuan kosong setelah chunking.")

        self.vector_store = ChromaVectorStore(persist_directory=self.chroma_dir)
        self.vector_store.add_chunks(chunks)
        self.vector_store.save(self.index_path)
        logger.info(f"Indeks RAG berhasil dibuat dengan {len(chunks)} chunks dari API.")

    def build_index(self):
        """Membaca file lokal atau fetch dari API jika folder kosong."""
        if not os.path.exists(self.db_dir):
            os.makedirs(self.db_dir)

        all_chunks = []
        for file in os.listdir(self.db_dir):
            if file.endswith((".md", ".txt", ".pdf")) and file != "lexa_company_profile.md":
                filepath = os.path.join(self.db_dir, file)
                try:
                    text = ""
                    if file.endswith(".pdf"):
                        with open(filepath, "rb") as f:
                            reader = PyPDF2.PdfReader(f)
                            for page in reader.pages:
                                text += page.extract_text() + "\n"
                        chunks = self.chunk_text(text, file)
                    else:
                        with open(filepath, "r", encoding="utf-8") as f:
                            text = f.read()
                        chunks = self.chunk_markdown(text, file)
                        
                    all_chunks.extend(chunks)
                except Exception as e:
                    logger.error(f"Gagal membaca file {file}: {e}")

        if all_chunks:
            self.vector_store = ChromaVectorStore(persist_directory=self.chroma_dir)
            self.vector_store.add_chunks(all_chunks)
            self.vector_store.save(self.index_path)
            logger.info(f"Indeks berhasil dibuat dengan {len(all_chunks)} chunks dokumen lokal.")
        else:
            logger.info("Tidak ada dokumen lokal. Mengambil basis pengetahuan dari API...")
            self.build_index_from_url()

    def load_or_build(self, force_rebuild=False):
        """Memuat indeks dari cache. Jika belum ada atau force_rebuild, bangun dari dokumen lokal/API."""
        if os.path.exists(self.chroma_dir) and not force_rebuild:
            try:
                # ChromaDB otomatis ter-load saat inisialisasi Client
                if self.vector_store.collection.count() > 0:
                    logger.info(f"Indeks RAG berhasil dimuat dari ChromaDB ({self.vector_store.collection.count()} chunks).")
                else:
                    logger.info("ChromaDB kosong, membangun ulang...")
                    self.build_index()
            except Exception as e:
                logger.error(f"Gagal memuat indeks dari cache, membangun ulang: {e}")
                self.build_index()
        else:
            self.build_index()

    def search(self, query: str, top_k: int = 5, threshold: float = 0.22):
        """Mencari dokumen yang relevan dengan query user."""
        return self.vector_store.search(query, top_k=top_k, threshold=threshold)
