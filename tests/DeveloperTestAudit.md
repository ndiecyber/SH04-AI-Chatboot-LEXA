# Developer Test Scripts Audit — SH04-AI-Chatbot-LEXA

**Document Type:** QA Audit — Developer Test Coverage Review  
**Folder:** `llm_tests/`  
**Date:** 2026-07-18  
**Auditor:** QA Engineering Team  
**Status:** ⚠️ Perlu Formalisasi

---

## 1. Overview

Repo mengandung folder `llm_tests/` dengan 2 file test script yang ditulis developer secara manual. Folder ini **tidak pernah diaudit** di sesi QA sebelumnya. Dokumen ini menjadi laporan audit resmi atas keberadaan, kualitas, dan rekomendasi tindak lanjut.

---

## 2. File yang Ditemukan

| File | Tujuan | Tipe |
|------|--------|------|
| `llm_tests/scratch_rag_test.py` | Menguji RAG pipeline — build index + search | Manual developer script |
| `llm_tests/scratch_pdf_test.py` | Menguji RAG dengan dokumen dinamis (temporary) + verifikasi keamanan disk | Manual developer script |

---

## 3. Analisis `scratch_rag_test.py`

### Apa yang Diuji

```python
# 1. Build index dengan force_rebuild=True
pipeline.load_or_build(force_rebuild=True)

# 2. Cari 4 query berbeda:
queries = [
    "bagaimana cara menghubungkan dengan whatsapp?",
    "berapa harga paket pro bulannya?",
    "apakah data saya aman?",
    "bagaimana jika bot tidak bisa menjawab pertanyaan?"
]

# 3. Tampilkan hasil: skor, sumber, preview konten
```

### Evaluasi QA

| Kriteria | Nilai | Keterangan |
|----------|-------|------------|
| Coverage fungsional | ✅ Baik | Menguji core RAG: build + search |
| Assertion / assert | ❌ Tidak ada | Hanya print output — tidak ada pass/fail otomatis |
| Error handling | ⚠️ Minimal | Tidak ada try/except untuk edge cases |
| Portabilitas | ⚠️ Tergantung knowledge_base | Harus ada file di folder lokal |
| Threshold dipakai | `0.1` | Lebih rendah dari yang dipakai di production (`0.15`) |
| Format | Informal | Bukan pytest, bukan unittest |

### Temuan

- Script bekerja sebagai **smoke test manual** yang berguna selama development.
- Karena tidak ada `assert`, script tidak otomatis deteksi kegagalan — developer harus baca output manual.
- Threshold `0.1` lebih longgar dari production `0.15` (via `llm.py`) → hasil test mungkin lebih banyak dari yang user lihat di chat.

---

## 4. Analisis `scratch_pdf_test.py`

### Apa yang Diuji

```python
# 1. Load base index
pipeline.load_or_build()

# 2. Upload dokumen sementara (in-memory)
pipeline.add_temporary_document("panduan_kucing_anggora.txt", uploaded_doc_text)

# 3. Search di dokumen sementara
results = pipeline.search(query, top_k=1, threshold=0.1)
assert-like: if results → pass, else sys.exit(1)

# 4. Verifikasi keamanan: dokumen sementara TIDAK disimpan ke disk
clean_pipeline = RAGPipeline()
clean_pipeline.load_or_build()
if clean_chunk_count == initial_chunk_count:
    print("[Sukses] Tidak bocor ke disk!")
else:
    sys.exit(1)
```

### Evaluasi QA

| Kriteria | Nilai | Keterangan |
|----------|-------|------------|
| Coverage fungsional | ✅ Sangat Baik | Menguji add_temporary_document + isolasi memori |
| Assertion / pass-fail | ✅ Ada (via sys.exit(1)) | Lebih baik dari scratch_rag_test.py |
| Verifikasi keamanan | ✅ Excellent | Test ini secara eksplisit verifikasi data tidak bocor ke disk |
| Test data realistis | ✅ Baik | Menggunakan teks dokumen yang bermakna |
| Portabilitas | ✅ Self-contained | Teks dokumen ada di dalam script |

### Temuan

- Ini adalah test yang **sangat bernilai** — secara eksplisit memverifikasi bahwa dokumen sementara tidak bocor ke `vector_index.pkl`. Ini menguji satu aspek keamanan yang belum tercakup di test QA formal.
- `sys.exit(1)` pada failure adalah mekanisme pass/fail sederhana tapi efektif.
- **Tidak ada dalam test suite QA formal** — harus diintegrasikan.

---

## 5. Gap antara Developer Tests vs QA Tests

| Aspek | Developer Tests | QA Tests | Gap |
|-------|----------------|----------|-----|
| RAG build index | ✅ `scratch_rag_test.py` | ✅ TC-R-001 | Tidak ada |
| RAG search relevan | ✅ `scratch_rag_test.py` | ✅ TC-R-003 | Tidak ada |
| Temporary doc add | ✅ `scratch_pdf_test.py` | ✅ TC-R-005 | Tidak ada |
| **Isolasi disk temp doc** | ✅ `scratch_pdf_test.py` | ❌ **Tidak ada** | **GAP** |
| **Auto pass/fail RAG** | ⚠️ Partial (sys.exit) | ❌ Tidak ada | **GAP** |
| PDF extraction | ✅ `scratch_pdf_test.py` | ✅ TC-R-002 | Tidak ada |
| threshold akurasi | ✅ Dipakai (0.1) | ✅ Documented | Minor diff |

---

## 6. Rekomendasi QA

### 6.1 Tambah Test Case Baru — TC-R-009 (Isolasi Disk Dokumen Sementara)

Test case ini secara eksplisit memvalidasi bahwa dokumen yang di-upload sementara tidak tersimpan ke `vector_index.pkl`. Ini temuan dari `scratch_pdf_test.py` yang belum ada di test suite formal.

**TC-R-009:**
```
Feature: Dokumen Sementara Tidak Bocor ke Disk
Steps:
  1. Catat jumlah chunks sebelum: len(pipeline.vector_store.chunks) = N
  2. Tambah dokumen temp: pipeline.add_temporary_document("test.txt", "...")
  3. Catat setelah: len = N + M (bertambah di memori)
  4. Load pipeline baru dari disk: clean_pipeline.load_or_build()
  5. Verifikasi: len(clean_pipeline.vector_store.chunks) == N (tidak berubah)
Expected: Chunks di disk = N (tidak berubah)
```

### 6.2 Formalisasi ke Pytest

Rekomendasikan developer mengkonversi `llm_tests/` ke format pytest:

```python
# llm_tests/test_rag_pipeline.py (contoh konversi)
import pytest
from core.rag import RAGPipeline

def test_rag_search_returns_results(base_pipeline):
    results = base_pipeline.search("harga paket pro", threshold=0.1)
    assert len(results) > 0, "RAG harus mengembalikan hasil untuk query relevan"
    assert results[0]["score"] >= 0.1

def test_temporary_doc_isolation(base_pipeline, tmp_path):
    initial_count = len(base_pipeline.vector_store.chunks)
    base_pipeline.add_temporary_document("temp.txt", "konten tes sementara " * 50)
    assert len(base_pipeline.vector_store.chunks) > initial_count
    
    # Load baru dari disk — harus sama dengan sebelum
    clean = RAGPipeline()
    clean.load_or_build()
    assert len(clean.vector_store.chunks) == initial_count, \
        "Dokumen sementara tidak boleh tersimpan ke disk"
```

### 6.3 Tambah ke CI/CD Pipeline (Future)

Ketika CI/CD diimplementasikan, `llm_tests/` harus dijalankan otomatis sebagai bagian dari pre-commit atau pre-deploy checks.

---

## 7. Summary

| Item | Status |
|------|--------|
| Developer tests ditemukan | ✅ `llm_tests/scratch_pdf_test.py`, `scratch_rag_test.py` |
| Coverage developer tests | ✅ Baik untuk core RAG |
| Format | ⚠️ Informal (bukan pytest) |
| Auto pass/fail | ⚠️ Partial |
| Gap yang ditemukan | ❌ Isolasi disk temp doc belum di test suite QA formal |
| Rekomendasi | Konversi ke pytest, tambah TC-R-009 |
