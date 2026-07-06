import streamlit as st
import requests
import uuid

API_URL = "http://127.0.0.1:8000"

# Konfigurasi Halaman
st.set_page_config(
    page_title="Lexa Chatbot - CS Assistant", 
    page_icon="💬", 
    layout="centered"
)

st.markdown("""
    <style>
    .main {
        background-color: #f8fafc;
    }
    .stButton>button {
        border-radius: 8px;
        background-color: #ef4444;
        color: white;
        border: none;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #dc2626;
        color: white;
    }
    h1 {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        color: #0f172a;
    }
    </style>
""", unsafe_allow_html=True) 

# Cek Konektivitas Backend API
try:
    requests.get(API_URL, timeout=3)
except Exception:
    st.error("❌ Gagal terhubung ke API Server Backend LEXA (http://127.0.0.1:8000)")
    st.info(
        "Silakan jalankan server backend terlebih dahulu dengan perintah:\n\n"
        "```powershell\n"
        ".\\.venv\\Scripts\\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000\n"
        "```"
    )
    st.stop()

# Inisialisasi Sesi Chat
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    # Daftarkan sesi ke backend
    try:
        requests.post(
            f"{API_URL}/api/sessions/", 
            json={"id": st.session_state.session_id, "title": "Percakapan Baru"}
        )
    except Exception as e:
        st.error(f"Gagal membuat sesi di backend: {e}")

# Sidebar untuk opsi tambahan
with st.sidebar:
    st.image("https://img.icons8.com/fluent/96/000000/bot.png", width=80)
    st.title("Lexa CS Control Panel")
    
    st.subheader("Manajemen Sesi")
    # Tombol Reset Chat
    if st.button("Reset Percakapan", use_container_width=True):
        try:
            # Hapus sesi lama di backend
            requests.delete(f"{API_URL}/api/sessions/{st.session_state.session_id}")
            # Buat sesi baru
            st.session_state.session_id = str(uuid.uuid4())
            requests.post(
                f"{API_URL}/api/sessions/", 
                json={"id": st.session_state.session_id, "title": "Percakapan Baru"}
            )
            if "indexed_files" in st.session_state:
                st.session_state.indexed_files.clear()
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Gagal mereset sesi: {e}")

    st.write("---")
    st.subheader("Unggah Dokumen Dinamis")
    st.write("Unggah dokumen PDF atau TXT untuk sesi chat ini saja (in-memory).")
    uploaded_file = st.file_uploader(
        "Pilih file (PDF atau TXT)",
        type=["pdf", "txt"],
        help="Maksimal ukuran 10MB"
    )
    
    # Logika Pemrosesan Berkas Unggahan via API
    if uploaded_file is not None:
        file_name = uploaded_file.name
        if "indexed_files" not in st.session_state:
            st.session_state.indexed_files = set()
            
        if file_name not in st.session_state.indexed_files:
            try:
                with st.spinner(f"Mengunggah dan mengindeks {file_name} di backend..."):
                    # Kirim file ke backend temporary upload
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    response = requests.post(
                        f"{API_URL}/api/documents/upload-temp/{st.session_state.session_id}",
                        files=files
                    )
                    if response.status_code == 200:
                        st.session_state.indexed_files.add(file_name)
                        st.sidebar.success(f"Berhasil mengindeks '{file_name}'!")
                        st.rerun()
                    else:
                        st.sidebar.error(f"Gagal mengindeks: {response.json().get('detail')}")
            except Exception as e:
                st.sidebar.error(f"Gagal memproses berkas: {e}")
    else:
        # Jika file uploader kosong tapi ada file di session_state, bersihkan memori sesi
        if "indexed_files" in st.session_state and st.session_state.indexed_files:
            try:
                with st.spinner("Membersihkan memori..."):
                    # Reset sesi di backend agar memori temporer dibersihkan
                    requests.delete(f"{API_URL}/api/sessions/{st.session_state.session_id}")
                    # Buat sesi baru dengan ID lama agar history chat ter-reset bersih
                    requests.post(
                        f"{API_URL}/api/sessions/", 
                        json={"id": st.session_state.session_id, "title": "Percakapan Baru"}
                    )
                st.session_state.indexed_files.clear()
                st.sidebar.info("Dokumen sementara dibersihkan.")
                st.rerun()
            except Exception as e:
                st.sidebar.error(f"Gagal membersihkan dokumen sementara: {e}")

    # Tampilkan daftar dokumen dinamis aktif
    if "indexed_files" in st.session_state and st.session_state.indexed_files:
        st.write("**Dokumen Aktif di Sesi Ini:**")
        for fn in st.session_state.indexed_files:
            st.caption(f"📄 {fn}")

    st.write("---")
    st.subheader("Basis Pengetahuan RAG")
    st.write("Jika Anda menambah atau memperbarui dokumen di folder `knowledge_base/`, klik tombol di bawah untuk menyegarkan indeks.")
    
    # Tombol Rebuild RAG Index via API
    if st.button("Perbarui Indeks RAG Bawaan", use_container_width=True):
        try:
            with st.spinner("Membangun ulang indeks di backend..."):
                response = requests.post(f"{API_URL}/api/documents/rebuild-index")
                if response.status_code == 200:
                    st.success("Indeks RAG berhasil diperbarui!")
                    st.rerun()
                else:
                    st.error("Gagal memperbarui indeks di backend.")
        except Exception as e:
            st.error(f"Koneksi gagal ke backend: {e}")


# Header Utama
st.title("💬 Lexa Customer Service")
st.caption("Asisten Customer Service Interaktif dengan basis pengetahuan RAG (FastAPI + Groq API)")
st.write("---")

# Mengambil riwayat chat dari database backend
history = []
try:
    history_resp = requests.get(f"{API_URL}/api/chat/{st.session_state.session_id}/history")
    if history_resp.status_code == 200:
        history = history_resp.json()
except Exception as e:
    st.error(f"Gagal memuat riwayat chat: {e}")

# Menampilkan riwayat chat
for message in history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Form Input untuk User
if prompt := st.chat_input("Ada yang bisa saya bantu hari ini?"):
    # Tampilkan input user secara instan ke UI
    with st.chat_message("user"):
        st.markdown(prompt)

    # Tampilkan respon bot secara streaming (real-time) dari REST API
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            # Request streaming ke FastAPI backend
            resp = requests.post(
                f"{API_URL}/api/chat/{st.session_state.session_id}/stream",
                json={"message": prompt},
                stream=True
            )
            
            if resp.status_code == 200:
                for chunk in resp.iter_content(chunk_size=None, decode_unicode=True):
                    if chunk:
                        full_response += chunk
                        response_placeholder.markdown(full_response + "▌")
                # Tampilkan respon akhir tanpa kursor ketik
                response_placeholder.markdown(full_response)
            else:
                st.error("Gagal mendapatkan jawaban dari backend.")
            
            # Tampilkan referensi dokumen pendukung (jika ada hasil RAG)
            ref_resp = requests.get(f"{API_URL}/api/chat/{st.session_state.session_id}/last-references")
            if ref_resp.status_code == 200:
                refs = ref_resp.json()
                if refs:
                    with st.expander("📚 Referensi Basis Pengetahuan"):
                        for i, res in enumerate(refs):
                            chunk = res["chunk"]
                            score = res["score"]
                            source = chunk["metadata"]["source"]
                            doc_title = chunk["metadata"]["document_title"]
                            st.markdown(f"**{i+1}. {doc_title}** (File: `{source}`, Skor Kemiripan: `{score:.2f}`)")
                            st.caption(chunk["content"])
                            if i < len(refs) - 1:
                                st.write("---")
                            
        except Exception as e:
            st.error(f"Terjadi kesalahan saat memproses jawaban: {e}")
