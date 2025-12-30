from datetime import datetime, timedelta
from typing import Optional, Union, Any
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
from app.core.config import get_settings
from app.core.database import get_session
from app.models import User

settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/admin/login")

def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = int(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exception
    
    user = session.get(User, user_id)
    if not user:
        raise credentials_exception
    return user

def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="The user doesn't have enough privileges"
        )
    return current_user

class AltchaService:
    def __init__(self, secret: str, complexity: int = 100000):
        self.secret = secret
        self.complexity = complexity

    def create_challenge(self):
        # Implementation of Altcha Challenge Generation
        # For now, return a simple mock structure as we are fixing the import error first.
        # In a real scenario, this would generate a cryptographic challenge.
        import random
        import string
        salt = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        return {
            "algorithm": "SHA-256",
            "challenge": salt,
            "salt": salt,
            "signature": "" # Mock signature
        }

    def verify_solution(self, payload: str) -> bool:
        # Mock verification - in production implement actual verification
        return True
