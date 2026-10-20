"""Saved lists and comparison history for signed-in users."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.provider import LLMProvider
from app.ai.schemas import ParsedItem
from app.core.errors import NotFoundError
from app.models.shopping_list import BasketRun, ShoppingList
from app.models.user import User
from app.schemas.basket import BasketComparison
from app.schemas.shopping_list import ListCreate, ListResponse, ListUpdate, RunDetail, RunSummary
from app.services import basket_service

HISTORY_LIMIT = 50


def _to_response(lst: ShoppingList) -> ListResponse:
    return ListResponse(id=lst.id, name=lst.name, text=lst.text, is_parsed=lst.parsed_items is not None, updated_at=lst.updated_at)


def _get_owned(db: Session, user: User, list_id: UUID) -> ShoppingList:
    lst = db.scalar(select(ShoppingList).where(ShoppingList.id == list_id, ShoppingList.user_id == user.id))
    if lst is None:
        raise NotFoundError("List not found")
    return lst


def list_lists(db: Session, user: User) -> list[ListResponse]:
    rows = db.scalars(select(ShoppingList).where(ShoppingList.user_id == user.id).order_by(ShoppingList.updated_at.desc()))
    return [_to_response(lst) for lst in rows]


def create_list(db: Session, user: User, data: ListCreate) -> ListResponse:
    lst = ShoppingList(user_id=user.id, name=data.name, text=data.text)
    db.add(lst)
    db.commit()
    db.refresh(lst)
    return _to_response(lst)


def update_list(db: Session, user: User, list_id: UUID, data: ListUpdate) -> ListResponse:
    lst = _get_owned(db, user, list_id)
    if data.name is not None:
        lst.name = data.name
    if data.text is not None and data.text != lst.text:
        lst.text = data.text
        lst.parsed_items = None  # the cached reading no longer matches the text
    db.commit()
    db.refresh(lst)
    return _to_response(lst)


def delete_list(db: Session, user: User, list_id: UUID) -> None:
    db.delete(_get_owned(db, user, list_id))
    db.commit()


def compare_list(
    db: Session, llm: LLMProvider, user: User, list_id: UUID, store_ids: list[UUID] | None
) -> BasketComparison:
    """Compare a saved list, parsing it only the first time (or after an edit)."""
    lst = _get_owned(db, user, list_id)
    if lst.parsed_items is None:
        items = basket_service.parse_list(llm, lst.text)
        lst.parsed_items = [item.model_dump() for item in items]
        db.commit()
    else:
        items = [ParsedItem.model_validate(raw) for raw in lst.parsed_items]

    allowed = basket_service.allowed_store_ids(db, user, store_ids)
    result = basket_service.compare_items(db, llm, items, allowed, user)
    record_run(db, user, result, lst)
    return result


def record_run(db: Session, user: User, result: BasketComparison, lst: ShoppingList | None = None) -> None:
    cheapest = result.stores[0]
    db.add(BasketRun(
        user_id=user.id, list_id=lst.id if lst else None, item_count=len(result.items),
        cheapest_chain=cheapest.chain_name, cheapest_total=cheapest.shared_total,
        savings=result.savings_vs_most_expensive, result=result.model_dump(mode="json"),
    ))
    db.commit()


def history(db: Session, user: User) -> list[RunSummary]:
    rows = db.execute(
        select(BasketRun, ShoppingList.name)
        .outerjoin(ShoppingList, ShoppingList.id == BasketRun.list_id)
        .where(BasketRun.user_id == user.id)
        .order_by(BasketRun.created_at.desc())
        .limit(HISTORY_LIMIT)
    ).all()
    return [_summary(run, name) for run, name in rows]


def get_run(db: Session, user: User, run_id: UUID) -> RunDetail:
    row = db.execute(
        select(BasketRun, ShoppingList.name)
        .outerjoin(ShoppingList, ShoppingList.id == BasketRun.list_id)
        .where(BasketRun.id == run_id, BasketRun.user_id == user.id)
    ).first()
    if row is None:
        raise NotFoundError("Comparison not found")
    run, name = row
    return RunDetail(**_summary(run, name).model_dump(), result=BasketComparison.model_validate(run.result))


def _summary(run: BasketRun, list_name: str | None) -> RunSummary:
    return RunSummary(
        id=run.id, list_id=run.list_id, list_name=list_name, item_count=run.item_count,
        cheapest_chain=run.cheapest_chain, cheapest_total=run.cheapest_total,
        savings=run.savings, created_at=run.created_at,
    )
