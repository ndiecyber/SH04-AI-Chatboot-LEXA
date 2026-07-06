from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List

from backend.database import get_db
from backend.schemas import ChatRequest, ChatResponse, MessageResponse, ReferenceItem
from backend.services.chat_service import ChatService
from backend.globals import base_pipeline
from backend.models import Message as DBMessage, Session as DBSession
from core.llm import LexaChatbot
from backend.services.chat_service import get_session_pipeline
import datetime

router = APIRouter(
    prefix="/api/chat",
    tags=["Chat"]
)

# Cache in-memory untuk referensi terakhir per sesi
_last_references = {}

# Helper to get ChatService
def get_chat_service(db: Session = Depends(get_db)):
    return ChatService(db, base_pipeline)

@router.post("/{session_id}", response_model=ChatResponse)
def send_chat_message(
    session_id: str,
    chat_req: ChatRequest,
    service: ChatService = Depends(get_chat_service)
):
    try:
        result = service.send_chat_message(session_id, chat_req.message)
        # Simpan referensi ke cache
        _last_references[session_id] = result["references"]
        return ChatResponse(
            response=result["response"],
            references=result["references"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{session_id}/history", response_model=List[MessageResponse])
def get_chat_history(
    session_id: str,
    service: ChatService = Depends(get_chat_service)
):
    return service.get_session_history(session_id)

@router.get("/{session_id}/last-references", response_model=List[ReferenceItem])
def get_last_references(session_id: str):
    """Ambil referensi dokumen RAG terakhir dari percakapan di sesi ini"""
    return _last_references.get(session_id, [])

@router.post("/{session_id}/stream")
def send_chat_message_stream(
    session_id: str,
    chat_req: ChatRequest,
    db: Session = Depends(get_db),
    service: ChatService = Depends(get_chat_service)
):
    """
    Kirim pesan chat dan dapatkan respon secara streaming token-by-token.
    Riwayat pesan akan otomatis disimpan ke database setelah streaming selesai.
    """
    # 1. Pastikan sesi ada
    session = service.get_or_create_session(session_id)
    
    # Update judul sesi jika masih default
    db_messages = db.query(DBMessage).filter(DBMessage.session_id == session_id).all()
    if session.title == "Percakapan Baru" and len(chat_req.message) > 0:
        session.title = chat_req.message[:50] + ("..." if len(chat_req.message) > 50 else "")

    # 2. Simpan pesan user
    db_user_msg = DBMessage(
        session_id=session_id,
        role="user",
        content=chat_req.message
    )
    db.add(db_user_msg)
    session.updated_at = datetime.datetime.utcnow()
    db.commit()

    # 3. Setup pipeline dan chatbot
    pipeline = get_session_pipeline(session_id, base_pipeline)
    chatbot = LexaChatbot(rag_pipeline=pipeline)
    chatbot.reset_chat()
    for msg in db_messages:
        chatbot.history.append({"role": msg.role, "content": msg.content})

    def event_generator():
        full_response = ""
        try:
            # Panggil stream generator dari core.llm
            for chunk in chatbot.send_message_stream(chat_req.message):
                # Simpan referensi ke cache global sesaat setelah generator mulai ( references terisi )
                if chatbot.last_references:
                    _last_references[session_id] = chatbot.last_references
                full_response += chunk
                yield chunk
                
            # Simpan jawaban bot ke DB setelah stream selesai
            db_assistant_msg = DBMessage(
                session_id=session_id,
                role="assistant",
                content=full_response
            )
            # Dapatkan DB session baru agar tidak bentrok thread/context
            from backend.database import SessionLocal
            with SessionLocal() as db_session:
                db_session.add(db_assistant_msg)
                # update updated_at di session
                db_sess = db_session.query(DBSession).filter(DBSession.id == session_id).first()
                if db_sess:
                    db_sess.updated_at = datetime.datetime.utcnow()
                db_session.commit()
                
        except Exception as e:
            # Kirim error message ke stream
            yield f"\n[ERROR: {str(e)}]"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
