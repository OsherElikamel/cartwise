import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AuthenticationError, ConflictError
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse

logger = logging.getLogger(__name__)


def register_user(db: Session, data: RegisterRequest) -> User:
    email = data.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise ConflictError("Email already registered")

    user = User(name=data.name, email=email, password_hash=hash_password(data.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("User registered: %s", user.id)
    return user


def login_user(db: Session, data: LoginRequest) -> TokenResponse:
    email = data.email.lower()
    user = db.scalar(select(User).where(User.email == email, User.deleted_at.is_(None)))
    if not user or not verify_password(data.password, user.password_hash):
        logger.warning("Failed login for %s", email)
        raise AuthenticationError("Invalid credentials")
    return TokenResponse(access_token=create_access_token({"sub": str(user.id)}))
