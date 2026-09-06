import json
import uuid
import datetime
import logging

from fastapi import APIRouter, Request, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

from core.config import Config
from core.schemas import ChatRequest, ChatResponse

logger = logging.getLogger("lexa")
from core.state import chat_sessions, rag_pipeline, manager, touch_session, cleanup_old_sessions, MAX_SESSIONS
from core.llm import LexaChatbot
from core.database import get_session_history, SessionLocal, ChatSession
from core.rate_limit import limiter

router = APIRouter()


def _save_handoff_message(session_id: str, content: str, role: str = "user"):
    """Simpan pesan handoff ke database."""
    db = SessionLocal()
    try:
        s = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if s:
            new_hist = list(s.history)
            new_hist.append({
                "role": role,
                "content": content,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000,
            })
            s.history = new_hist
            db.commit()
    except Exception as e:
        logger.error(f"Error saving handoff message: {e}")
    finally:
        db.close()


def get_or_create_session(session_id: str) -> LexaChatbot:
    # Cleanup old sessions periodically
    if len(chat_sessions) > MAX_SESSIONS:
        cleanup_old_sessions()
    
    if session_id not in chat_sessions:
        chat_sessions[session_id] = LexaChatbot(
            session_id=session_id,
            rag_pipeline=rag_pipeline,
            model=Config.MODEL_NAME,
            max_history_turns=Config.MAX_HISTORY_TURNS,
        )
    touch_session(session_id)
    return chat_sessions[session_id]


@router.post("/chat", response_model=ChatResponse)
@limiter.limit("20/minute")
async def chat(request: Request, req: ChatRequest):
    if len(req.message) > Config.MAX_INPUT_LENGTH:
        raise HTTPException(
            status_code=413,
            detail=f"Pesan terlalu panjang. Maksimal {Config.MAX_INPUT_LENGTH} karakter.",
        )
    session_id = req.session_id or str(uuid.uuid4())
    bot = get_or_create_session(session_id)

    try:
        reply = await bot.send_message(req.message)
        return ChatResponse(
            reply=reply,
            session_id=session_id,
            references=[
                {
                    "title": r["chunk"]["metadata"]["document_title"],
                    "source": r["chunk"]["metadata"]["source"],
                    "score": round(r["score"], 2),
                    "content": r["chunk"]["content"][:200],
                }
                for r in bot.last_references
            ],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
@limiter.limit("20/minute")
async def chat_stream(request: Request, req: ChatRequest):
    if len(req.message) > Config.MAX_INPUT_LENGTH:
        raise HTTPException(
            status_code=413,
            detail=f"Pesan terlalu panjang. Maksimal {Config.MAX_INPUT_LENGTH} karakter.",
        )
    session_id = req.session_id or str(uuid.uuid4())
    bot = get_or_create_session(session_id)

    async def event_generator():
        yield f"data: {json.dumps({'type': 'session', 'session_id': session_id})}\n\n"

        try:
            history_data = get_session_history(session_id)
            is_handoff = history_data.get("is_human_handoff", False) if history_data else False

            full_response = ""

            if is_handoff:
                _save_handoff_message(session_id, req.message)

                yield f"data: {json.dumps({'type': 'done', 'references': []})}\n\n"
                return

            async for chunk in bot.send_message_stream(req.message):
                full_response += chunk
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"

            refs = [
                {
                    "title": r["chunk"]["metadata"]["document_title"],
                    "source": r["chunk"]["metadata"]["source"],
                    "score": round(r["score"], 2),
                }
                for r in bot.last_references
            ]
            yield f"data: {json.dumps({'type': 'done', 'references': refs})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.websocket("/ws/chat/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect(websocket, session_id)
    bot = get_or_create_session(session_id)
    try:
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type", "message")

            if message_type == "message":
                user_msg = data.get("content", "")
                if len(user_msg) > Config.MAX_INPUT_LENGTH:
                    await manager.broadcast_to_session(
                        {"type": "error", "message": f"Pesan terlalu panjang. Maksimal {Config.MAX_INPUT_LENGTH} karakter."},
                        session_id,
                    )
                    continue

                history_data = get_session_history(session_id)
                is_handoff = history_data.get("is_human_handoff", False) if history_data else False

                if is_handoff:
                    _save_handoff_message(session_id, user_msg)
                    await manager.broadcast_to_session({"type": "handoff_user_msg", "content": user_msg}, session_id)
                    await manager.broadcast_to_admins({
                        "type": "new_message",
                        "session_id": session_id,
                        "content": user_msg,
                        "timestamp": datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000,
                    })
                else:
                    await manager.broadcast_to_session({"type": "typing"}, session_id)

                    full_response = ""
                    async for chunk in bot.send_message_stream(user_msg):
                        full_response += chunk
                        await manager.broadcast_to_session({"type": "chunk", "content": chunk}, session_id)

                    refs = [
                        {
                            "title": r["chunk"]["metadata"]["document_title"],
                            "source": r["chunk"]["metadata"]["source"],
                            "score": round(r["score"], 2),
                        }
                        for r in bot.last_references
                    ]
                    await manager.broadcast_to_session({"type": "done", "references": refs}, session_id)

            elif message_type == "handoff_request":
                user_name = data.get("user_name", "Anonymous")
                db = SessionLocal()
                try:
                    s = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
                    if s:
                        s.is_human_handoff = True
                        new_hist = list(s.history)
                        new_hist.append({"role": "system", "content": f"[HANDOFF REQUESTED by {user_name}]", "timestamp": datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000})
                        s.history = new_hist
                        db.commit()
                except Exception as e:
                    logger.error(f"Error saving handoff request: {e}")
                finally:
                    db.close()

                await manager.broadcast_to_admins({
                    "type": "handoff_request",
                    "session_id": session_id,
                    "user_name": user_name,
                    "timestamp": datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000,
                })
                await manager.broadcast_to_session({"type": "handoff_requested"}, session_id)

            elif message_type == "admin_reply":
                pass

            elif message_type == "typing":
                # Broadcast typing event ke semua koneksi di session (termasuk widget)
                await manager.broadcast_to_session({"type": "typing", "role": data.get("role", "admin")}, session_id)

    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
    except Exception as e:
        manager.disconnect(websocket, session_id)


@router.post("/chat/reset")
@limiter.limit("10/minute")
async def reset_chat(request: Request, session_id: str = ""):
    if session_id and session_id in chat_sessions:
        chat_sessions[session_id].reset_chat()
        return {"status": "reset", "session_id": session_id}
    elif session_id:
        raise HTTPException(status_code=404, detail="Sesi tidak ditemukan")
    else:
        raise HTTPException(status_code=400, detail="session_id wajib diisi")


@router.get("/api/chat/poll")
@limiter.limit("30/minute")
async def poll_chat(request: Request, session_id: str):
    history = get_session_history(session_id)
    if not history:
        return {"history": [], "is_human_handoff": False}
    filtered_history = [m for m in history.get("history", []) if m.get("role") != "system"]
    return {"history": filtered_history, "is_human_handoff": history.get("is_human_handoff", False)}
