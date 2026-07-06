import sys
import requests
import uuid

API_URL = "http://127.0.0.1:8000"

def main():
    # Set stdout encoding to UTF-8 to support emojis on Windows terminal
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass

    print("=== Memulai Chatbot Customer Service Lexa (CLI) ===")
    
    # 1. Cek koneksi ke backend API
    try:
        requests.get(API_URL, timeout=3)
    except Exception:
        print("\n❌ Gagal terhubung ke API Server Backend LEXA di http://127.0.0.1:8000.")
        print("Pastikan server backend sudah berjalan dengan menjalankan perintah:")
        print("python -m uvicorn backend.main:app\n")
        sys.exit(1)

    # 2. Buat sesi chat unik untuk CLI ini
    session_id = f"cli-{uuid.uuid4().hex[:8]}"
    try:
        requests.post(
            f"{API_URL}/api/sessions/",
            json={"id": session_id, "title": f"Sesi CLI ({session_id})"}
        )
        print(f"Sesi chat aktif (ID: {session_id})")
        print("Lexa aktif! Ketik 'keluar' atau 'exit' untuk menyudahi obrolan.\n")
    except Exception as e:
        print(f"Gagal menginisialisasi sesi di backend: {e}")
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
            
            # 3. Kirim dan stream jawaban dari API backend
            resp = requests.post(
                f"{API_URL}/api/chat/{session_id}/stream",
                json={"message": user_input},
                stream=True
            )
            
            if resp.status_code == 200:
                for chunk in resp.iter_content(chunk_size=None, decode_unicode=True):
                    if chunk:
                        print(chunk, end="", flush=True)
                print("\n")
            else:
                print(f"\n[ERROR: Server backend mengembalikan status {resp.status_code}]\n")
            
        except KeyboardInterrupt:
            print("\nLexa: Obrolan dihentikan secara paksa. Sampai jumpa!")
            break
        except Exception as e:
            print(f"\nTerjadi kesalahan koneksi: {e}\n")

if __name__ == "__main__":
    main()
