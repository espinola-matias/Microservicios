import os
import jwt
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
TOKEN_EXP_HOURS = int(os.getenv("TOKEN_EXP_HOURS", 12))

def crear_token(usuario_id: str, scopes: Optional[list[str]] = None, is_service: bool = False):
    now = datetime.now(timezone.utc)
    payload = {
        "usuario_id": usuario_id,
        "scopes": scopes or [],
        "is_service": is_service,
        "iat": now,
        "exp": now + timedelta(hours=TOKEN_EXP_HOURS)}
    
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verificar_token(token: str):
    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if data.get("usuario_id") != "admin":
            return {"error": "No autorizado"}
        return data
    except jwt.ExpiredSignatureError:
        return {"error": "Token expirado"}
    except jwt.InvalidTokenError:
        return {"error": "Token invalido"}
