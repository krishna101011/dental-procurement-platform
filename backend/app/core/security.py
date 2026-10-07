from datetime import datetime, timedelta, timezone
from jose import jwt
from pwdlib import PasswordHash
from app.core.config import settings

password_hash = PasswordHash.recommended()
ALGORITHM = "HS256"

def hash_password(password: str) -> str: return password_hash.hash(password)
def verify_password(password: str, hashed: str) -> bool: return password_hash.verify(password, hashed)
def create_token(user_id: int, role: str):
    exp = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_minutes)
    return jwt.encode({"sub": str(user_id), "role": role, "exp": exp}, settings.secret_key, algorithm=ALGORITHM)

def decode_token(token: str): return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
