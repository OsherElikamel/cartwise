from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.match import MatchChoice, MatchResponse
from app.services import match_service

router = APIRouter(prefix="/api/matches", tags=["Remembered matches"])


@router.get("", response_model=list[MatchResponse])
def list_matches(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return match_service.list_matches(db, user)


@router.put("", response_model=MatchResponse)
def save_choice(data: MatchChoice, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Confirm or swap the product for a list item; used for every later list."""
    return match_service.save_choice(db, user, data.match_key, data.store_id, data.item_code)


@router.delete("/{match_id}", status_code=status.HTTP_204_NO_CONTENT)
def forget(match_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    match_service.forget(db, user, match_id)
