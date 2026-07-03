import os
from dotenv import load_dotenv
from groq import Groq

# Memuat variabel lingkungan dari file .env
load_dotenv()

class LexaChatbot:
    """
    Kelas utama untuk chatbot customer service Lexa menggunakan Groq API.
    """
    def __init__(self, system_instruction=None, model="openai/gpt-oss-120b", rag_pipeline=None):
        # Mengambil API key dari environment variable (.env)
        # Mendukung baik 'GROQ_API_KEY' (standar) maupun 'GROQ API KEY' (sesuai format Anda)
        self.api_key = os.getenv("GROQ_API_KEY") or os.getenv("GROQ API KEY")
        
        if not self.api_key:
            raise ValueError(
                "API Key Groq tidak ditemukan! Pastikan variabel 'GROQ_API_KEY' atau "
                "'GROQ API KEY' sudah didefinisikan dengan benar di file .env Anda."
            )
            
        # Inisialisasi client Groq
        self.client = Groq(api_key=self.api_key)
        self.model = model
        self.rag_pipeline = rag_pipeline
        self.last_references = []
        
        # System prompt default untuk Customer Service
        self.default_system_instruction = (
            "Anda adalah Lexa, asisten customer service yang ramah, sopan, profesional, "
            "dan siap membantu pelanggan dengan solusi terbaik. Jawablah menggunakan Bahasa Indonesia "
            "yang santun, jelas, dan mudah dipahami."
        )
        
        self.system_instruction = system_instruction or self.default_system_instruction
        self.history = []
        self.reset_chat()

    def reset_chat(self):
        """Mengosongkan riwayat percakapan dan menetapkan ulang System Prompt."""
        self.history = [
            {"role": "system", "content": self.system_instruction}
        ]
        self.last_references = []

    def _prepare_messages(self, message: str) -> list:
        """
        Melakukan pencarian RAG (jika diaktifkan) dan menyisipkan konteks dokumen
        ke dalam system prompt sementara untuk pemanggilan model.
        """
        self.last_references = []
        context_str = ""

        # Lakukan pencarian RAG jika pipeline tersedia
        if self.rag_pipeline:
            results = self.rag_pipeline.search(message, top_k=3, threshold=0.15)
            self.last_references = results
            
            if results:
                context_str = (
                    "\n\n[DOKUMEN REFERENSI BASIS PENGETAHUAN]\n"
                    "Gunakan informasi di bawah ini untuk menjawab pertanyaan pelanggan. "
                    "Jawab secara jujur berdasarkan referensi ini. Jika informasi tidak ada di referensi, "
                    "jawablah secara umum dan sopan tetapi beri tahu bahwa informasi spesifik tersebut "
                    "belum tersedia di dokumentasi kami.\n\n"
                )
                for i, res in enumerate(results):
                    chunk = res["chunk"]
                    source = chunk["metadata"]["source"]
                    doc_title = chunk["metadata"]["document_title"]
                    context_str += f"Dokumen #{i+1} | Sumber: {source} ({doc_title}):\n{chunk['content']}\n---\n\n"

        # Buat salinan riwayat chat untuk dikirim ke API
        messages_to_send = [msg.copy() for msg in self.history]
        
        # Sisipkan konteks dokumen ke pesan system (pesan pertama) jika ada
        if context_str and messages_to_send and messages_to_send[0]["role"] == "system":
            messages_to_send[0]["content"] = self.system_instruction + context_str
            
        return messages_to_send

    def send_message(self, message: str) -> str:
        """
        Mengirim pesan ke Groq API dan menyimpan percakapan ke dalam riwayat.
        Mengembalikan jawaban model dalam bentuk string utuh.
        """
        self.history.append({"role": "user", "content": message})
        messages_to_send = self._prepare_messages(message)
        
        try:
            chat_completion = self.client.chat.completions.create(
                messages=messages_to_send,
                model=self.model,
            )
            
            reply = chat_completion.choices[0].message.content
            self.history.append({"role": "assistant", "content": reply})
            return reply
            
        except Exception as e:
            # Jika gagal, hapus pesan terakhir user agar history tetap sinkron
            self.history.pop()
            raise RuntimeError(f"Gagal memproses request ke Groq API: {e}")

    def send_message_stream(self, message: str):
        """
        Mengirim pesan ke Groq API dan menghasilkan (yield) jawaban per kata/token
        secara streaming (real-time). Cocok untuk antarmuka chat yang interaktif.
        """
        self.history.append({"role": "user", "content": message})
        messages_to_send = self._prepare_messages(message)
        
        try:
            stream = self.client.chat.completions.create(
                messages=messages_to_send,
                model=self.model,
                stream=True
            )
            
            full_reply = ""
            for chunk in stream:
                content = chunk.choices[0].delta.content or ""
                full_reply += content
                yield content
                
            self.history.append({"role": "assistant", "content": full_reply})
            
        except Exception as e:
            self.history.pop()
            raise RuntimeError(f"Gagal memproses stream request ke Groq API: {e}")
