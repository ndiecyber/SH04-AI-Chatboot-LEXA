import os
import logging
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger("lexa")

JWT_SECRET: str = os.getenv("JWT_SECRET", "")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24
# Grace period: token expired < 7 hari masih bisa di-refresh
REFRESH_GRACE_PERIOD_DAYS = 7

if not JWT_SECRET:
    logger.warning("JWT_SECRET not set! Using insecure dev default. Set JWT_SECRET in .env for production.")

security = HTTPBearer()


def create_jwt_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_jwt(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def decode_token_allow_expired(token: str):
    """Decode token meskipun expired, selama masih dalam grace period."""
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            options={"verify_exp": False},
        )
        exp = payload.get("exp")
        if exp:
            exp_dt = datetime.fromtimestamp(exp, tz=timezone.utc)
            if datetime.now(timezone.utc) - exp_dt > timedelta(days=REFRESH_GRACE_PERIOD_DAYS):
                return None
        return payload
    except jwt.InvalidTokenError:
        return None


def require_role(*allowed_roles):
    """Dependency factory untuk role-based access control."""
    def role_checker(payload: dict = Depends(verify_jwt)):
        user_role = payload.get("role")
        if user_role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Akses ditolak. Role tidak mencukupi.")
        return payload
    return role_checker
