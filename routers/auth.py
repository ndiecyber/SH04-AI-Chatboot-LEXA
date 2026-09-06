import bcrypt
from fastapi import APIRouter, HTTPException, Depends, Request

from core.schemas import LoginRequest
from core.auth import create_jwt_token, decode_token_allow_expired
from core.database import AdminUser, SessionLocal
from core.rate_limit import limiter

router = APIRouter()


@router.post("/api/auth/login")
@limiter.limit("5/minute")
async def login(request: Request, req: LoginRequest):
    db = SessionLocal()
    try:
        user = db.query(AdminUser).filter(AdminUser.email == req.email).first()
        if not user or not user.password_hash:
            raise HTTPException(status_code=401, detail="Email atau password salah")

        pwd_bytes = req.password.encode('utf-8')
        hash_bytes = user.password_hash.encode('utf-8')
        if not bcrypt.checkpw(pwd_bytes, hash_bytes):
            raise HTTPException(status_code=401, detail="Email atau password salah")

        token = create_jwt_token({"sub": user.email, "role": user.role, "name": user.name})
        return {"token": token, "user": {"name": user.name, "email": user.email, "role": user.role}}
    finally:
        db.close()


@router.post("/api/auth/refresh")
@limiter.limit("10/minute")
async def refresh_token(request: Request, token: str = ""):
    if not token:
        raise HTTPException(status_code=401, detail="Token required")

    payload = decode_token_allow_expired(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token expired or invalid. Please login again.")

    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    db = SessionLocal()
    try:
        user = db.query(AdminUser).filter(AdminUser.email == email).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        new_token = create_jwt_token({"sub": user.email, "role": user.role, "name": user.name})
        return {"token": new_token, "user": {"name": user.name, "email": user.email, "role": user.role}}
    finally:
        db.close()
