from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.ai.provider import LLMProvider, get_llm
from app.core.dependencies import get_optional_user
from app.core.rate_limit import limiter
from app.db.database import get_db
from app.models.user import User
from app.schemas.basket import BasketComparison, BasketRequest, RepriceRequest
from app.services import basket_service, list_service

router = APIRouter(prefix="/api/baskets", tags=["Baskets"])


@router.post("/compare", response_model=BasketComparison)
@limiter.limit("10/minute")
def compare(
    request: Request,
    data: BasketRequest,
    db: Session = Depends(get_db),
    llm: LLMProvider = Depends(get_llm),
    user: User | None = Depends(get_optional_user),
):
    """Guests compare on the demo branches; signed-in users on the branches they follow."""
    store_ids = basket_service.allowed_store_ids(db, user, data.store_ids)
    result = basket_service.compare_basket(db, llm, data.text, store_ids, user)
    if user:
        list_service.record_run(db, user, result)
    return result


@router.post("/reprice", response_model=BasketComparison)
@limiter.limit("30/minute")
def reprice(
    request: Request,
    data: RepriceRequest,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    """Recalculate totals for explicit product picks (after a confirm or swap). No AI calls."""
    store_ids = basket_service.allowed_store_ids(db, user, data.store_ids)
    picks = [basket_service.Pick(**p.model_dump()) for p in data.picks]
    return basket_service.reprice(db, data.items, store_ids, picks)
