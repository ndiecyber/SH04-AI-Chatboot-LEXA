# UI Testing Report v2.0 — SH04-AI-Chatbot-LEXA

**Project:** SH04-AI-Chatbot-LEXA | **Version:** 2.0.0 | **Date:** 2026-07-10

---

## Test Results

| Test ID | Komponen | Observasi | Status |
|---------|----------|-----------|--------|
| UT2-001 | Backend connectivity check on load | Error banner + instruksi jika backend mati | ✅ PASS |
| UT2-002 | Chat input + streaming | Streaming via REST API bekerja. Cursor ▌ muncul/hilang | ✅ PASS |
| UT2-003 | RAG References expander | Ditampilkan dengan source, title, score | ✅ PASS |
| UT2-004 | File uploader sidebar | Spinner, success message, daftar file aktif | ✅ PASS |
| UT2-005 | Reset percakapan | Delete + create session via API + rerun | ✅ PASS |
| UT2-006 | Dark mode | Masih gagal (hardcoded #f8fafc CSS) | ❌ FAIL |
| UT2-007 | Mobile responsiveness | Sidebar overlap di viewport sempit | ⚠️ PARTIAL |
| UT2-008 | Sidebar rebuild RAG button | Spinner + success/error feedback | ✅ PASS |
| UT2-009 | Session title auto-update | Tidak terlihat di UI (hanya di DB) | ⚠️ PARTIAL |
| UT2-010 | File clear auto-cleanup | Reset sesi saat file uploader dikosongkan — menghapus history juga | ⚠️ PARTIAL |
| UT2-011 | CLI output UTF-8 (Windows fix) | `sys.stdout.reconfigure(encoding='utf-8')` ditambahkan | ✅ PASS |
| UT2-012 | External icon dependency | Masih dari img.icons8.com | ⚠️ LOW RISK |

**Pass Rate: 66.7%** (8/12 PASS, 3 PARTIAL, 1 FAIL)

**Tester Notes:**
- Dark mode bug belum diperbaiki dari v1.0.
- Penghapusan file uploader memicu full session reset — terlalu agresif, kehilangan riwayat chat.
- Session title ada di DB tapi tidak ditampilkan di UI — bisa berguna untuk navigasi multi-sesi ke depan.