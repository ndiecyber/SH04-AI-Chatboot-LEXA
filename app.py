import streamlit as st
from core.llm import LexaChatbot
from core.rag import RAGPipeline

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

# Inisialisasi RAG Pipeline dalam Session State
if "rag" not in st.session_state:
    try:
        # Inisialisasi RAG dengan folder default
        rag = RAGPipeline()
        rag.load_or_build()
        st.session_state.rag = rag
    except Exception as e:
        st.error(f"Gagal memuat RAG Pipeline: {e}")
        st.session_state.rag = None

# Inisialisasi Chatbot dalam Session State agar history chat terjaga saat refresh
if "chatbot" not in st.session_state:
    try:
        # Chatbot akan membaca API key dari .env Anda secara otomatis
        # Menyertakan RAG pipeline ke chatbot
        st.session_state.chatbot = LexaChatbot(rag_pipeline=st.session_state.get("rag"))
    except Exception as e:
        st.error(f"Gagal menginisialisasi Chatbot: {e}")
        st.info("Silakan periksa apakah 'GROQ API KEY' sudah didefinisikan dengan benar di file `.env` Anda.")
        st.stop()

# Sidebar untuk opsi tambahan
with st.sidebar:
    st.image("https://img.icons8.com/fluent/96/000000/bot.png", width=80)
    st.title("Lexa CS Control Panel")
    
    st.subheader("Manajemen Sesi")
    # Tombol Reset Chat
    if st.button("Reset Percakapan", use_container_width=True):
        st.session_state.chatbot.reset_chat()
        # Bersihkan memori dan muat kembali indeks dasar dari disk
        if st.session_state.rag:
            st.session_state.rag.load_or_build(force_rebuild=False)
        if "indexed_files" in st.session_state:
            st.session_state.indexed_files.clear()
        st.rerun()

    st.write("---")
    st.subheader("Unggah Dokumen Dinamis")
    st.write("Unggah dokumen PDF atau TXT untuk sesi chat ini saja (in-memory).")
    uploaded_file = st.file_uploader(
        "Pilih file (PDF atau TXT)",
        type=["pdf", "txt"],
        help="Maksimal ukuran 10MB"
    )
    
    # Logika Pemrosesan Berkas Unggahan
    if uploaded_file is not None:
        file_name = uploaded_file.name
        if "indexed_files" not in st.session_state:
            st.session_state.indexed_files = set()
            
        if file_name not in st.session_state.indexed_files:
            try:
                with st.spinner(f"Mengekstrak teks dari {file_name}..."):
                    extracted_text = ""
                    if file_name.endswith(".pdf"):
                        import pypdf
                        reader = pypdf.PdfReader(uploaded_file)
                        for page in reader.pages:
                            page_text = page.extract_text()
                            if page_text:
                                extracted_text += page_text + "\n"
                    elif file_name.endswith(".txt"):
                        extracted_text = uploaded_file.read().decode("utf-8")
                        
                    if extracted_text.strip():
                        if st.session_state.rag:
                            st.session_state.rag.add_temporary_document(file_name, extracted_text)
                            st.session_state.indexed_files.add(file_name)
                            st.sidebar.success(f"Berhasil mengindeks '{file_name}'!")
                            st.rerun()
                    else:
                        st.sidebar.error("Gagal mengekstrak teks. Berkas mungkin kosong.")
            except Exception as e:
                st.sidebar.error(f"Gagal memproses berkas: {e}")
    else:
        # Jika file uploader kosong tapi ada file di session_state, berarti file baru saja dihapus
        if "indexed_files" in st.session_state and st.session_state.indexed_files:
            if st.session_state.rag:
                with st.spinner("Membersihkan memori..."):
                    st.session_state.rag.load_or_build(force_rebuild=False)
            st.session_state.indexed_files.clear()
            st.sidebar.info("Dokumen sementara dibersihkan.")
            st.rerun()

    # Tampilkan daftar dokumen dinamis aktif
    if "indexed_files" in st.session_state and st.session_state.indexed_files:
        st.write("**Dokumen Aktif di Sesi Ini:**")
        for fn in st.session_state.indexed_files:
            st.caption(f"📄 {fn}")

    st.write("---")
    st.subheader("Basis Pengetahuan RAG")
    st.write("Jika Anda menambah atau memperbarui dokumen di folder `knowledge_base/`, klik tombol di bawah untuk menyegarkan indeks.")
    
    # Tombol Rebuild RAG Index
    if st.button("Perbarui Indeks RAG Bawaan", use_container_width=True):
        if st.session_state.rag:
            with st.spinner("Membangun ulang indeks..."):
                st.session_state.rag.build_index()
            st.success("Indeks RAG berhasil diperbarui!")
            st.rerun()
        else:
            st.warning("RAG Pipeline tidak aktif.")


# Header Utama
st.title("💬 Lexa Customer Service")
st.caption("Asisten Customer Service Interaktif dengan basis pengetahuan RAG (Groq API)")
st.write("---")

# Menampilkan riwayat chat yang tersimpan (melewati system prompt indeks ke-0)
for message in st.session_state.chatbot.history:
    if message["role"] == "system":
        continue
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Form Input untuk User
if prompt := st.chat_input("Ada yang bisa saya bantu hari ini?"):
    # Tampilkan input user secara instan ke UI
    with st.chat_message("user"):
        st.markdown(prompt)

    # Tampilkan respon bot secara streaming (real-time)
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            # Memanggil generator stream dari llm.py
            for chunk in st.session_state.chatbot.send_message_stream(prompt):
                full_response += chunk
                response_placeholder.markdown(full_response + "▌")
            # Tampilkan respon akhir tanpa kursor ketik
            response_placeholder.markdown(full_response)
            
            # Tampilkan referensi dokumen pendukung (jika ada hasil RAG)
            refs = st.session_state.chatbot.last_references
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

