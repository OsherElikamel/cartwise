from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.ingestion.pipeline import sync_store_prices_by_id
from app.models.user import User
from app.schemas.catalog import StoreResponse
from app.schemas.locality import HomeUpdate, LocalityResponse
from app.services import locality_service, user_store_service

router = APIRouter(prefix="/api/me", tags=["My branches"])


class FollowRequest(BaseModel):
    store_id: UUID


@router.patch("/home", response_model=LocalityResponse | None)
def set_home(data: HomeUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Remember the user's city, so branch suggestions start from it."""
    return locality_service.set_home(db, user, data.home_locality_code)


@router.get("/stores", response_model=list[StoreResponse])
def my_stores(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return user_store_service.list_followed(db, user)


@router.post("/stores", response_model=StoreResponse)
def follow_store(
    data: FollowRequest,
    response: Response,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Follow a branch (replacing your branch of the same chain).

    202 when its prices are still loading; poll GET /api/me/stores until is_ready.
    """
    store, needs_loading = user_store_service.follow(db, user, data.store_id)
    if needs_loading:
        background.add_task(sync_store_prices_by_id, store.id)
        response.status_code = status.HTTP_202_ACCEPTED
    return store


@router.delete("/stores/{store_id}", status_code=status.HTTP_204_NO_CONTENT)
def unfollow_store(store_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    user_store_service.unfollow(db, user, store_id)
