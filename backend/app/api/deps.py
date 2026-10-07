from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import User
from app.core.security import decode_token

bearer = HTTPBearer(auto_error=False)
def get_current_user(db: Session = Depends(get_db), creds: HTTPAuthorizationCredentials | None = Depends(bearer)):
    if not creds: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try: payload = decode_token(creds.credentials); user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError): raise HTTPException(status_code=401, detail="Invalid token")
    user = db.get(User, user_id)
    if not user or not user.is_active: raise HTTPException(status_code=401, detail="Inactive account")
    return user

def require_roles(*roles):
    def dep(user=Depends(get_current_user)):
        if user.role not in roles: raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return dep
