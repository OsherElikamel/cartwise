from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.ai.provider import LLMProvider, get_llm
from app.core.dependencies import get_optional_user
from app.core.rate_limit import limiter
from app.db.database import get_db
from app.models.user import User
from app.schemas.basket import BasketComparison, BasketRequest
from app.services import basket_service

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
    return basket_service.compare_basket(db, llm, data.text, store_ids)
