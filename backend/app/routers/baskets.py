from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.ai.provider import LLMProvider, get_llm
from app.core.rate_limit import limiter
from app.db.database import get_db
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
):
    return basket_service.compare_basket(db, llm, data.text, data.store_ids)
