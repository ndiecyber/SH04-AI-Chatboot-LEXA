import os
import shutil
import datetime
import logging

import bcrypt
from fastapi import APIRouter, Request, HTTPException, Depends, UploadFile, File, BackgroundTasks
from fastapi.responses import StreamingResponse

from core.schemas import UserCreateRequest, AdminReplyReq
from core.auth import verify_jwt, require_role

logger = logging.getLogger("lexa")
from core.state import rag_pipeline, manager
from core.config import Config
from core.settings import SettingsManager
from core.database import (
    get_analytics_chart_data,
    get_analytics_metrics,
    get_recent_unanswered_queries,
    get_all_sessions,
    get_all_users,
    get_session_history,
    AdminUser,
    SessionLocal,
    ChatSession,
    set_human_handoff,
)
from core.rate_limit import limiter

router = APIRouter()


@router.post("/api/admin/reindex")
@limiter.limit("5/minute")
async def reindex(request: Request, payload: dict = Depends(require_role("Super Admin"))):
    if rag_pipeline:
        rag_pipeline.load_or_build()
        return {"status": "success", "message": "Knowledge base reindexed successfully."}
    raise HTTPException(status_code=500, detail="RAG pipeline not initialized.")


@router.get("/api/admin/settings")
async def get_admin_settings(payload: dict = Depends(verify_jwt)):
    return SettingsManager.get_settings()


@router.post("/api/admin/settings")
@limiter.limit("10/minute")
async def update_admin_settings(request: Request, payload: dict = Depends(require_role("Super Admin"))):
    data = await request.json()
    return SettingsManager.save_settings(data)


@router.get("/api/admin/stats")
async def get_dashboard_statistics(payload: dict = Depends(verify_jwt)):
    metrics = get_analytics_metrics()
    chart_data = get_analytics_chart_data()
    return {
        "kpi": {
            "total_conversations": metrics["total_conversations"],
            "active_users": metrics["active_users_30min"],
            "unanswered_queries": metrics["unanswered_queries"],
        },
        "chart": chart_data,
        "metrics": metrics,
    }


@router.get("/api/admin/unanswered")
async def admin_unanswered_queries(payload: dict = Depends(verify_jwt)):
    return get_recent_unanswered_queries(limit=10)


@router.get("/api/admin/sessions")
async def admin_get_sessions(payload: dict = Depends(verify_jwt), limit: int = 50, offset: int = 0):
    return get_all_sessions(limit=limit, offset=offset)


@router.get("/api/admin/sessions/{session_id}")
async def admin_get_session_history(session_id: str, payload: dict = Depends(verify_jwt)):
    db = SessionLocal()
    try:
        s = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if not s:
            raise HTTPException(status_code=404, detail="Session not found")

        history = [msg for msg in s.history if msg.get("role") != "system"]
        return {"history": history, "is_human_handoff": s.is_human_handoff}
    finally:
        db.close()


@router.get("/api/admin/kb/files")
async def get_kb_files(payload: dict = Depends(verify_jwt)):
    kb_dir = "knowledge_base"
    if not os.path.exists(kb_dir):
        return []

    files = []
    for f in os.listdir(kb_dir):
        if f.endswith((".md", ".txt", ".pdf")) and f != "lexa_company_profile.md":
            path = os.path.join(kb_dir, f)
            files.append({
                "filename": f,
                "size": os.path.getsize(path)
            })
    return files


@router.post("/api/admin/kb/export")
async def export_kb(payload: dict = Depends(require_role("Super Admin"))):
    """Export semua dokumen KB sebagai zip/download."""
    import zipfile
    import io
    
    kb_dir = "knowledge_base"
    if not os.path.exists(kb_dir):
        raise HTTPException(status_code=404, detail="Knowledge base directory not found")
    
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for f in os.listdir(kb_dir):
            if f.endswith((".md", ".txt", ".pdf")) and f != "lexa_company_profile.md":
                filepath = os.path.join(kb_dir, f)
                zf.write(filepath, arcname=f)
    
    memory_file.seek(0)
    return StreamingResponse(
        io.BytesIO(memory_file.read()),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=lexa_kb_export.zip"}
    )


@router.post("/api/admin/kb/upload")
@limiter.limit("10/minute")
async def upload_kb_file(request: Request, file: UploadFile = File(...), payload: dict = Depends(require_role("Super Admin"))):
    if not file.filename.endswith((".md", ".txt", ".pdf")):
        raise HTTPException(status_code=400, detail="Hanya file .txt, .md, atau .pdf yang didukung")

    # Sanitize filename to prevent path traversal
    import re
    safe_filename = re.sub(r'[^\w\-.]', '_', os.path.basename(file.filename))
    if not safe_filename or safe_filename.startswith('.'):
        raise HTTPException(status_code=400, detail="Invalid filename")

    # Check file size (max 10MB)
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File terlalu besar. Maksimal 10MB.")

    kb_dir = "knowledge_base"
    os.makedirs(kb_dir, exist_ok=True)

    file_path = os.path.join(kb_dir, safe_filename)
    with open(file_path, "wb") as buffer:
        buffer.write(contents)

    return {"status": "success", "filename": safe_filename}


@router.delete("/api/admin/kb/files/{filename}")
async def delete_kb_file(filename: str, payload: dict = Depends(require_role("Super Admin"))):
    kb_dir = "knowledge_base"
    file_path = os.path.join(kb_dir, filename)

    if ".." in filename or not os.path.abspath(file_path).startswith(os.path.abspath(kb_dir)):
        raise HTTPException(status_code=403, detail="Invalid filename")

    if os.path.exists(file_path) and filename != "lexa_company_profile.md":
        os.remove(file_path)
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="File not found")


def run_rebuild():
    try:
        rag_pipeline.load_or_build(force_rebuild=True)
    except Exception as e:
        logger.error(f"Error rebuilding RAG: {e}")


@router.post("/api/admin/kb/reindex")
async def reindex_kb(background_tasks: BackgroundTasks, payload: dict = Depends(require_role("Super Admin"))):
    chroma_dir = "knowledge_base/chroma_db"
    if os.path.exists(chroma_dir):
        shutil.rmtree(chroma_dir, ignore_errors=True)

    background_tasks.add_task(run_rebuild)
    return {"status": "success", "message": "Knowledge Base re-indexing started in background."}


@router.get("/api/admin/users")
async def admin_get_users(payload: dict = Depends(verify_jwt), limit: int = 50, offset: int = 0):
    return get_all_users(limit=limit, offset=offset)


@router.post("/api/admin/users")
@limiter.limit("10/minute")
async def admin_create_user(request: Request, req: UserCreateRequest, payload: dict = Depends(require_role("Super Admin"))):
    db = SessionLocal()
    try:
        existing = db.query(AdminUser).filter(AdminUser.email == req.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email sudah terdaftar")

        pwd_bytes = req.password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_pwd = bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')

        new_user = AdminUser(
            name=req.name,
            email=req.email,
            password_hash=hashed_pwd,
            role=req.role
        )
        db.add(new_user)
        db.commit()
        return {"status": "success", "message": "User berhasil dibuat"}
    finally:
        db.close()


@router.delete("/api/admin/users/{user_id}")
async def admin_delete_user(user_id: int, payload: dict = Depends(require_role("Super Admin"))):
    db = SessionLocal()
    try:
        user = db.query(AdminUser).filter(AdminUser.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User tidak ditemukan")
        if user.email == os.getenv("ADMIN_EMAIL", "admin@lexatech.id"):
            raise HTTPException(status_code=403, detail="Super Admin default tidak bisa dihapus")

        db.delete(user)
        db.commit()
        return {"status": "success", "message": "User berhasil dihapus"}
    finally:
        db.close()


@router.post("/api/admin/handoff")
async def admin_set_handoff(session_id: str, is_handoff: bool, payload: dict = Depends(verify_jwt)):
    if set_human_handoff(session_id, is_handoff):
        return {"status": "success", "is_human_handoff": is_handoff}
    raise HTTPException(status_code=404, detail="Sesi tidak ditemukan")


@router.post("/api/admin/reply")
async def admin_reply(req: AdminReplyReq, payload: dict = Depends(verify_jwt)):
    db = SessionLocal()
    try:
        s = db.query(ChatSession).filter(ChatSession.session_id == req.session_id).first()
        if not s:
            raise HTTPException(status_code=404, detail="Session tidak ditemukan")
        new_hist = list(s.history)
        new_hist.append({"role": "admin", "content": req.content, "timestamp": datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000})
        s.history = new_hist
        db.commit()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving admin reply: {e}")
        raise HTTPException(status_code=500, detail="Gagal menyimpan balasan")
    finally:
        db.close()

    await manager.broadcast_to_session({"type": "admin_reply", "content": req.content}, req.session_id)
    return {"status": "success"}
