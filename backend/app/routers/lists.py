from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.ai.provider import LLMProvider, get_llm
from app.core.dependencies import get_current_user
from app.core.rate_limit import limiter
from app.db.database import get_db
from app.models.user import User
from app.schemas.basket import BasketComparison
from app.schemas.shopping_list import ListCompareRequest, ListCreate, ListResponse, ListUpdate, RunDetail, RunSummary
from app.services import list_service

router = APIRouter(prefix="/api", tags=["Lists & history"])


@router.get("/lists", response_model=list[ListResponse])
def list_lists(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return list_service.list_lists(db, user)


@router.post("/lists", response_model=ListResponse, status_code=status.HTTP_201_CREATED)
def create_list(data: ListCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return list_service.create_list(db, user, data)


@router.patch("/lists/{list_id}", response_model=ListResponse)
def update_list(list_id: UUID, data: ListUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return list_service.update_list(db, user, list_id, data)


@router.delete("/lists/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_list(list_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    list_service.delete_list(db, user, list_id)


@router.post("/lists/{list_id}/compare", response_model=BasketComparison)
@limiter.limit("10/minute")
def compare_list(
    request: Request,
    list_id: UUID,
    data: ListCompareRequest | None = None,
    db: Session = Depends(get_db),
    llm: LLMProvider = Depends(get_llm),
    user: User = Depends(get_current_user),
):
    return list_service.compare_list(db, llm, user, list_id, data.store_ids if data else None)


@router.get("/history", response_model=list[RunSummary])
def history(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return list_service.history(db, user)


@router.get("/history/{run_id}", response_model=RunDetail)
def get_run(run_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return list_service.get_run(db, user, run_id)
