from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.database import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def _user_from_token(token: str | None, db: Session) -> User | None:
    payload = decode_access_token(token) if token else None
    if payload is None:
        return None
    try:
        user_id = UUID(str(payload.get("sub")))
    except ValueError:
        return None
    return db.scalar(select(User).where(User.id == user_id, User.deleted_at.is_(None)))


def get_current_user(token: str | None = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    user = _user_from_token(token, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_optional_user(token: str | None = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User | None:
    """The signed-in user, or None for guests. A bad token is treated as a guest."""
    return _user_from_token(token, db)
