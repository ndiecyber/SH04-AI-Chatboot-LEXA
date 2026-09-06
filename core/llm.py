import os
from groq import AsyncGroq
from core.database import SessionLocal, ChatSession, UnansweredQuery
from core.settings import SettingsManager

class LexaChatbot:
    """
    Kelas utama untuk chatbot customer service Lexa menggunakan Groq API.
    """
    def __init__(
        self,
        session_id=None,
        system_instruction=None,
        model="openai/gpt-oss-120b",
        rag_pipeline=None,
        max_history_turns=10,
    ):
        # Mengambil API key dari environment variable (.env)
        # Mendukung baik 'GROQ_API_KEY' (standar) maupun 'GROQ API KEY' (sesuai format Anda)
        self.api_key = os.getenv("GROQ_API_KEY") or os.getenv("GROQ API KEY")
        
        if not self.api_key:
            raise ValueError(
                "API Key Groq tidak ditemukan! Pastikan variabel 'GROQ_API_KEY' atau "
                "'GROQ API KEY' sudah didefinisikan dengan benar di file .env Anda."
            )
            
        # Inisialisasi client Groq (async)
        self.client = AsyncGroq(api_key=self.api_key)
        self.model = model
        self.rag_pipeline = rag_pipeline
        self.max_history_turns = max_history_turns
        self.last_references = []
        self.session_id = session_id or "default"
        
        # Menggunakan system prompt dari SettingsManager
        self.default_system_instruction = SettingsManager.get_settings().get("system_prompt", "Anda adalah asisten AI.")
        
        self.system_instruction = system_instruction or self.default_system_instruction
        self.history = []
        self._load_history()

    def _load_history(self):
        """Memuat riwayat chat dari database PostgreSQL."""
        db = SessionLocal()
        try:
            session = db.query(ChatSession).filter(ChatSession.session_id == self.session_id).first()
            if session and session.history:
                self.history = session.history
            else:
                self.reset_chat(save=False)
        finally:
            db.close()

    def _save_history(self):
        """Menyimpan riwayat chat saat ini ke database PostgreSQL."""
        db = SessionLocal()
        try:
            session = db.query(ChatSession).filter(ChatSession.session_id == self.session_id).first()
            if not session:
                session = ChatSession(session_id=self.session_id, history=self.history)
                db.add(session)
            else:
                # Tetapkan list baru agar SQLAlchemy mendeteksi perubahan JSON
                session.history = list(self.history)
            db.commit()
        finally:
            db.close()

    def reset_chat(self, save=True):
        """Mengosongkan riwayat percakapan dan menetapkan ulang System Prompt."""
        self.history = [
            {"role": "system", "content": self.system_instruction}
        ]
        self.last_references = []
        if save:
            self._save_history()

    def _trim_history(self):
        """Batasi riwayat chat per sesi agar tidak menumpuk token."""
        max_messages = self.max_history_turns * 2
        if len(self.history) > 1 + max_messages:
            self.history = [self.history[0]] + self.history[-max_messages:]
            self._save_history()

    def _log_unanswered_query(self, message: str):
        """Mencatat pertanyaan yang tidak ditemukan di RAG ke database."""
        db = SessionLocal()
        try:
            query = UnansweredQuery(session_id=self.session_id, user_query=message)
            db.add(query)
            db.commit()
        finally:
            db.close()

    def _prepare_messages(self, message: str) -> list:
        """
        Melakukan pencarian RAG (jika diaktifkan) dan menyisipkan konteks dokumen
        ke dalam system prompt sementara untuk pemanggilan model.
        """
        self.last_references = []
        context_str = ""

        # Lakukan pencarian RAG jika pipeline tersedia
        if self.rag_pipeline:
            from core.config import Config
            results = self.rag_pipeline.search(message, top_k=Config.RAG_TOP_K, threshold=Config.RAG_THRESHOLD)
            self.last_references = results
            
            if results:
                context_str = (
                    "\n\n[DOKUMEN REFERENSI BASIS PENGETAHUAN]\n"
                    "Gunakan informasi di bawah ini untuk menjawab pertanyaan pelanggan. "
                    "Jawab secara jujur berdasarkan referensi ini saja. "
                    "Jika informasi tidak ada di referensi, jawablah jujur bahwa informasi "
                    "belum tersedia dan arahkan ke info@lexatech.id atau +62 853 2013 2014.\n\n"
                )
                for i, res in enumerate(results):
                    chunk = res["chunk"]
                    source = chunk["metadata"]["source"]
                    doc_title = chunk["metadata"]["document_title"]
                    context_str += f"Dokumen #{i+1} | Sumber: {source} ({doc_title}):\n{chunk['content']}\n---\n\n"
            else:
                self._log_unanswered_query(message)
                context_str = (
                    "\n\n[CATATAN SISTEM]\n"
                    "Tidak ditemukan informasi relevan di basis pengetahuan untuk pertanyaan ini. "
                    "Jawab jujur bahwa informasi spesifik tersebut belum tersedia di dokumentasi kami. "
                    "Arahkan pelanggan ke info@lexatech.id atau +62 853 2013 2014 untuk informasi lebih lanjut. "
                    "JANGAN mengarang jawaban.\n"
                )

        # Buat salinan riwayat chat untuk dikirim ke API
        messages_to_send = [msg.copy() for msg in self.history]
        
        # Sisipkan konteks dokumen ke pesan system (pesan pertama) jika ada
        if context_str and messages_to_send and messages_to_send[0]["role"] == "system":
            messages_to_send[0]["content"] = self.system_instruction + context_str
            
        return messages_to_send

    async def send_message(self, message: str) -> str:
        """
        Mengirim pesan ke Groq API dan menyimpan percakapan ke dalam riwayat.
        Mengembalikan jawaban model dalam bentuk string utuh.
        """
        self.history.append({"role": "user", "content": message})
        self._save_history()
        messages_to_send = self._prepare_messages(message)
        
        try:
            chat_completion = await self.client.chat.completions.create(
                messages=messages_to_send,
                model=self.model,
            )
            
            reply = chat_completion.choices[0].message.content
            self.history.append({"role": "assistant", "content": reply})
            self._save_history()
            self._trim_history()
            return reply
            
        except Exception as e:
            # Jika gagal, hapus pesan terakhir user agar history tetap sinkron
            if self.history and self.history[-1]["role"] == "user":
                self.history.pop()
                self._save_history()
            raise RuntimeError(f"Gagal memproses request ke Groq API: {e}")

    async def send_message_stream(self, message: str):
        """
        Mengirim pesan ke Groq API dan menghasilkan (yield) jawaban per kata/token
        secara streaming (real-time). Cocok untuk antarmuka chat yang interaktif.
        """
        self.history.append({"role": "user", "content": message})
        self._save_history()
        messages_to_send = self._prepare_messages(message)
        
        try:
            stream = await self.client.chat.completions.create(
                messages=messages_to_send,
                model=self.model,
                stream=True
            )
            
            full_reply = ""
            async for chunk in stream:
                content = chunk.choices[0].delta.content or ""
                full_reply += content
                yield content
                
            self.history.append({"role": "assistant", "content": full_reply})
            self._save_history()
            self._trim_history()
            
        except Exception as e:
            if self.history and self.history[-1]["role"] == "user":
                self.history.pop()
                self._save_history()
            raise RuntimeError(f"Gagal memproses stream request ke Groq API: {e}")
