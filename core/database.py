import os
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON, Boolean, text
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

logger = logging.getLogger("lexa")

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Default ke SQLite jika DATABASE_URL tidak diset (untuk development/local)
if not DATABASE_URL:
    DATABASE_URL = os.getenv(
        "DATABASE_URL", "sqlite:///./lexa.db"
    ).replace("postgres://", "postgresql://", 1)

# Fix untuk Heroku/Supabase format lama
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    session_id = Column(String, primary_key=True, index=True)
    history = Column(JSON, default=list) # Menyimpan list of dicts [{"role": "...", "content": "..."}]
    is_human_handoff = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class AdminUser(Base):
    __tablename__ = "admin_users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String) # Kolom baru untuk autentikasi
    role = Column(String) # Super Admin, CS Agent, Editor (Knowledge Base)
    status = Column(String, default="Online")
    last_active = Column(String, default="Sekarang")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class UnansweredQuery(Base):
    __tablename__ = "unanswered_queries"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    user_query = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

def get_analytics_metrics():
    """Ambil metrics real dari database untuk dashboard."""
    db = SessionLocal()
    try:
        total_conversations = db.query(ChatSession).count()
        unanswered_queries = db.query(UnansweredQuery).count()
        
        # Calculate average response time dari history yang sudah ada
        sessions_with_timestamps = db.query(ChatSession).filter(
            ChatSession.updated_at.isnot(None)
        ).all()
        
        avg_response_time = "N/A"
        if sessions_with_timestamps:
            total_time_diffs = 0
            count = 0
            for s in sessions_with_timestamps:
                if s.history and len(s.history) > 1:
                    # Waktu dari pertama ke terakhir di session
                    first = s.history[0].get("timestamp", 0)
                    last = s.history[-1].get("timestamp", 0)
                    if first and last:
                        diff = (last - first) / 1000  # convert ms to detik
                        total_time_diffs += diff
                        count += 1
            
            if count > 0:
                avg_seconds = total_time_diffs / count
                if avg_seconds < 60:
                    avg_response_time = f"{avg_seconds:.1f}s"
                elif avg_seconds < 3600:
                    avg_response_time = f"{avg_seconds/60:.1f} menit"
                else:
                    avg_response_time = f"{avg_seconds/3600:.1f} jam"
        
        # Count active users (sessions aktif dalam waktu 30 menit terakhir)
        thirty_min_ago = datetime.now(timezone.utc) - timedelta(minutes=30)
        active_users = db.query(ChatSession).filter(
            ChatSession.updated_at >= thirty_min_ago
        ).count()
        
        # Active users bulanan
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        monthly_active = db.query(ChatSession).filter(
            ChatSession.created_at >= thirty_days_ago
        ).count()
        
        return {
            "total_conversations": total_conversations,
            "unanswered_queries": unanswered_queries,
            "avg_response_time": avg_response_time,
            "active_users_30min": active_users,
            "monthly_active": monthly_active,
        }
    finally:
        db.close()

def get_analytics_chart_data():
    db = SessionLocal()
    try:
        today = datetime.now(timezone.utc).date()
        seven_days_ago = today - timedelta(days=6)
        cutoff = datetime.combine(seven_days_ago, datetime.min.time(), tzinfo=timezone.utc)

        days_data = {}
        for i in range(6, -1, -1):
            d = today - timedelta(days=i)
            label = d.strftime("%d/%m")
            days_data[label] = {"name": label, "chats": 0, "percakapan": 0, "unresolved": 0}

        # Filter 7 hari terakhir lewat SQL, group by Python
        sessions = db.query(ChatSession).filter(ChatSession.created_at >= cutoff).all()
        for s in sessions:
            label = s.created_at.strftime("%d/%m")
            if label in days_data:
                days_data[label]["chats"] += 1
                days_data[label]["percakapan"] += 1

        queries = db.query(UnansweredQuery).filter(UnansweredQuery.created_at >= cutoff).all()
        for q in queries:
            label = q.created_at.strftime("%d/%m")
            if label in days_data:
                days_data[label]["unresolved"] += 1

        return list(days_data.values())
    finally:
        db.close()

def get_recent_unanswered_queries(limit: int = 5):
    db = SessionLocal()
    try:
        queries = db.query(UnansweredQuery).order_by(UnansweredQuery.created_at.desc()).limit(limit).all()
        return [{"id": q.id, "query": q.user_query, "created_at": q.created_at.isoformat()} for q in queries]
    finally:
        db.close()

def get_all_sessions(limit: int = 50, offset: int = 0):
    db = SessionLocal()
    try:
        total = db.query(ChatSession).count()
        sessions = db.query(ChatSession).order_by(ChatSession.updated_at.desc()).offset(offset).limit(limit).all()
        
        results = []
        for s in sessions:
            history = s.history or []
            last_msg = ""
            if history:
                last_msg = history[-1].get("content", "")
                if len(last_msg) > 50:
                    last_msg = last_msg[:50] + "..."
            
            results.append({
                "session_id": s.session_id,
                "last_message": last_msg,
                "created_at": s.created_at.isoformat() if s.created_at else "",
                "updated_at": s.updated_at.isoformat() if s.updated_at else ""
            })
        return {"items": results, "total": total, "limit": limit, "offset": offset}
    finally:
        db.close()

def get_session_history(session_id: str):
    db = SessionLocal()
    try:
        s = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if not s:
            return None
        return {
            "session_id": s.session_id,
            "history": s.history,
            "is_human_handoff": s.is_human_handoff,
            "created_at": s.created_at.isoformat(),
            "updated_at": s.updated_at.isoformat()
        }
    finally:
        db.close()

def set_human_handoff(session_id: str, is_handoff: bool):
    db = SessionLocal()
    try:
        s = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if s:
            s.is_human_handoff = is_handoff
            db.commit()
            return True
        return False
    finally:
        db.close()

def get_all_users(limit: int = 50, offset: int = 0):
    db = SessionLocal()
    try:
        total = db.query(AdminUser).count()
        users = db.query(AdminUser).offset(offset).limit(limit).all()
        return {
            "items": [{"id": u.id, "name": u.name, "email": u.email, "role": u.role, "status": u.status, "last_active": u.last_active} for u in users],
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    finally:
        db.close()

def delete_user(user_id: int):
    db = SessionLocal()
    try:
        user = db.query(AdminUser).filter(AdminUser.id == user_id).first()
        if user:
            db.delete(user)
            db.commit()
            return True
        return False
    finally:
        db.close()

# Inisialisasi tabel (dan migrasi manual sederhana)
import logging as _logging
_db_logger = _logging.getLogger("lexa")

try:
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE chat_sessions ADD COLUMN is_human_handoff BOOLEAN DEFAULT 0"))
        conn.commit()
except Exception as e:
    msg = str(e).lower()
    if "duplicate column" not in msg and "already exists" not in msg:
        _db_logger.warning(f"ALTER TABLE chat_sessions failed: {e}")

try:
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE admin_users ADD COLUMN password_hash VARCHAR"))
        conn.commit()
except Exception as e:
    msg = str(e).lower()
    if "duplicate column" not in msg and "already exists" not in msg:
        _db_logger.warning(f"ALTER TABLE admin_users failed: {e}")

Base.metadata.create_all(bind=engine)

def seed_default_admin():
    db = SessionLocal()
    try:
        if db.query(AdminUser).count() == 0:
            import bcrypt
            admin_email = os.getenv("ADMIN_EMAIL", "admin@lexatech.id")
            admin_password = os.getenv("ADMIN_PASSWORD", None)
            # Generate secure password if not set
            if not admin_password:
                import secrets
                admin_password = secrets.token_urlsafe(16)
                logger.info(f"Default admin password generated. Email: {admin_email}")
                logger.info(f"Save this password securely: {admin_password}")
            pwd = admin_password.encode('utf-8')
            salt = bcrypt.gensalt()
            default_pwd = bcrypt.hashpw(pwd, salt).decode('utf-8')
            admin = AdminUser(
                name="Super Admin",
                email=admin_email,
                password_hash=default_pwd,
                role="Super Admin"
            )
            db.add(admin)
            db.commit()
            logger.info(f"Default admin created: {admin_email}")
    finally:
        db.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
