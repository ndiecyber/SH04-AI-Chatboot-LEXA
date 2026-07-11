# Regression Testing Report — SH04-AI-Chatbot-LEXA

**Project:** SH04-AI-Chatbot-LEXA  
**Version:** 2.0.0  
**Tester:** QA Engineering Team  
**Date:** 2026-07-10  
**Purpose:** Verifikasi semua bug v1.0 yang diklaim sudah diperbaiki

---

## 1. Bug Regression Matrix

| Bug ID v1.0 | Deskripsi | Klaim Fix | Status Regresi |
|-------------|-----------|-----------|----------------|
| Bug-001 | Missing `.gitignore` | ✅ Fixed (commit repo) | ✅ **CONFIRMED FIXED** |
| Bug-002 | No input validation di `llm.py` | ❌ Belum di-fix | ⚠️ **STILL OPEN** |
| Bug-003 | Dark mode CSS override | ❌ Belum di-fix | ⚠️ **STILL OPEN** |
| Bug-004 | Rate limit tidak user-friendly | ❌ Belum di-fix | ⚠️ **STILL OPEN** |
| Bug-005 | Unbounded history growth | ✅ Dimediasi oleh DB (namun tetap ada issue) | ⚠️ **PARTIALLY FIXED** |
| ST-005 v1.0 | No prompt injection defense | ⚠️ Partial fix (identity clause only) | ⚠️ **PARTIALLY FIXED** |
| AT-007 v1.0 | No retry on API failure | ❌ Belum di-fix | ⚠️ **STILL OPEN** |

---

## 2. Detail Hasil Regresi

---

### REG-001 — Bug-001: `.gitignore` Missing

**Test:** Cek keberadaan dan isi `.gitignore`.

```bash
cat .gitignore
# Output:
.env
.venv
__pycache__
knowledge_base
lexa.db
lexa.db-journal
```

**Finding:** ✅ `.gitignore` ada dan meng-cover semua file sensitif termasuk `.env`, database, dan vector index.

**Status:** ✅ **FIXED** — Bug-001 ditutup.

---

### REG-002 — Bug-002: No Input Validation di `llm.py`

**Test:** Panggil `send_message("")` dan `send_message(None)` langsung.

```python
# core/llm.py — send_message():
def send_message(self, message: str) -> str:
    self.history.append({"role": "user", "content": message})
    # ← Tidak ada validasi sama sekali sebelum append
```

**Finding:** ❌ Tidak ada `_validate_message()`. Empty string, None, dan oversized input masih bisa melewati tanpa validasi di layer `llm.py`.

**Catatan:** Di arsitektur v2.0, `ChatService` di backend menjadi buffer — tapi validasi tetap tidak ada di sana juga.

**Status:** ⚠️ **STILL OPEN** — Bug-002 masih aktif.

---

### REG-003 — Bug-003: Dark Mode CSS

**Test:** Buka Streamlit, toggle dark mode.

```python
# app.py masih memiliki:
st.markdown("""<style>.main { background-color: #f8fafc; }</style>""",
            unsafe_allow_html=True)
```

**Finding:** ❌ CSS hardcoded masih ada. Dark mode masih broken.

**Status:** ⚠️ **STILL OPEN** — Bug-003 masih aktif.

---

### REG-004 — Bug-004: Rate Limit Error Tidak User-Friendly

**Test:** Trigger 429 dari Groq API.

```python
# core/llm.py — exception handler:
except Exception as e:
    self.history.pop()
    raise RuntimeError(f"Gagal memproses request ke Groq API: {e}")
```

**Finding:** ❌ Masih menggunakan generic `except Exception`. `RateLimitError` tidak ditangani secara khusus. User masih melihat pesan teknis.

**Status:** ⚠️ **STILL OPEN** — Bug-004 masih aktif.

---

### REG-005 — Bug-005: Unbounded History Growth

**Test:** Kirim 100+ pesan, observasi memory dan DB.

**v1.0 Issue:** `self.history` list tumbuh tidak terbatas di memori.

**v2.0 Status:**
- History sekarang disimpan di SQLite (tidak di memori permanen) ✅
- Setiap request merekonstruksi history dari DB (bukan menyimpan di objek) ✅
- **Tapi:** Seluruh history tetap dikirim ke Groq API setiap request ❌
- Pada sesi 200 turn, 400 pesan dikirim ke API = ~40,000 tokens per request ❌

**Finding:** ⚠️ Memory leak in-process sudah teratasi (history tidak di RAM permanen), tapi token growth ke API masih ada. Sliding window belum diimplementasikan.

**Status:** ⚠️ **PARTIALLY FIXED** — Memory teratasi, token growth masih bermasalah.

---

### REG-006 — ST-005 v1.0: Prompt Injection Defense

**Test:** Kirim `"Ignore all previous instructions"`.

**v2.0 System Prompt:** Menambahkan klausa identitas:
> *"Anda ditenagai oleh model open-source GPT-OSS (bukan GPT-4 atau buatan OpenAI). Ingatlah identitas Anda ini dan jangan pernah mengaku sebagai model buatan OpenAI."*

**Finding:** ⚠️ Klausa identitas membantu mengatasi halusinasi model. Tapi tidak ada klausa eksplisit untuk menolak pengungkapan system prompt atau perubahan persona.

**Status:** ⚠️ **PARTIALLY FIXED** — Identitas fix, injection defense masih belum lengkap.

---

### REG-007 — Bug Baru yang Dikonfirmasi dari v2.0

Bug baru yang ditemukan dalam arsitektur v2.0 (bukan regresi dari v1.0):

| Bug ID | Deskripsi | Severity |
|--------|-----------|----------|
| Bug-006 | `requests` tidak di requirements.txt | 🔴 Critical |
| Bug-007 | Tidak ada validasi ukuran file | 🟠 High |
| Bug-008 | Orphaned user message saat stream disconnect | 🟠 High |
| Bug-009 | Session pipeline cache tanpa eviction | 🟡 Medium |
| Bug-010 | File uploader clear memicu full session reset | 🟡 Medium |

---

## 3. Regression Summary

| Kategori | Jumlah | Status |
|----------|--------|--------|
| Bug v1.0 Confirmed Fixed | 1 | Bug-001 |
| Bug v1.0 Partially Fixed | 2 | Bug-005, ST-005 |
| Bug v1.0 Still Open | 4 | Bug-002, Bug-003, Bug-004, AT-007 |
| Bug Baru di v2.0 | 5 | Bug-006 s/d Bug-010 |
| **Total Bug Aktif** | **9** | |

---

## 4. Kesimpulan Regresi

Dari 7 bug yang dilaporkan di v1.0, **hanya 1 yang benar-benar fixed** (Bug-001 gitignore). 2 bug partially fixed, dan 4 bug masih open. Selain itu, arsitektur baru v2.0 memperkenalkan **5 bug baru**, dengan 1 di antaranya Critical (Bug-006).

**Rekomendasi:** Prioritaskan Bug-006 sebelum distribusi README/onboarding baru apapun.
