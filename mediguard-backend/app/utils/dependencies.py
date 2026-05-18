from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import User
from app.db.session import get_db
from app.utils.auth import decode_access_token


def _token_from_header(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token


def optional_user(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> User | None:
    token = _token_from_header(authorization)
    if not token:
        return None
    subject = decode_access_token(token)
    if not subject:
        return None
    return db.query(User).filter(User.email == subject).first()


def get_current_user(user: User | None = Depends(optional_user)) -> User:
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return user

