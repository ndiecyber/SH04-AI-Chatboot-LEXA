import sys
from core.llm import LexaChatbot
from core.rag import RAGPipeline

def main():
    # Set stdout encoding to UTF-8 to support emojis on Windows terminal
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass

    print("=== Memulai Chatbot Customer Service Lexa (CLI) ===")
    try:
        # Inisialisasi RAG Pipeline bawaan
        print("Memuat basis pengetahuan RAG...")
        rag = RAGPipeline()
        rag.load_or_build()
        
        # Inisialisasi chatbot dengan pipeline RAG
        bot = LexaChatbot(rag_pipeline=rag)
        print("Lexa aktif! Ketik 'keluar' atau 'exit' untuk menyudahi obrolan.\n")
    except Exception as e:
        print(f"Error saat inisialisasi: {e}")
        sys.exit(1)

    while True:
        try:
            user_input = input("Pelanggan: ")
            if user_input.strip().lower() in ['keluar', 'exit']:
                print("Lexa: Terima kasih telah menghubungi kami. Semoga hari Anda menyenangkan!")
                break
                
            if not user_input.strip():
                continue

            print("Lexa: ", end="", flush=True)
            # Menggunakan mode stream agar respon terasa lebih hidup dan instan
            for chunk in bot.send_message_stream(user_input):
                print(chunk, end="", flush=True)
            print("\n")
            
        except KeyboardInterrupt:
            print("\nLexa: Obrolan dihentikan secara paksa. Sampai jumpa!")
            break
        except Exception as e:
            print(f"\nTerjadi kesalahan: {e}\n")

if __name__ == "__main__":
    main()

