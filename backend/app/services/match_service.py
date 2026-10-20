"""Remembered matches: a user's earlier answers to "which product is this".

Confident AI picks are remembered automatically; unsure ones only once the
user confirms or swaps them. Remembered items skip the AI on later lists.
"""

import re
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.ai.schemas import ParsedItem
from app.core.errors import NotFoundError
from app.models.chain import Chain, Store
from app.models.item_match import ItemMatch
from app.models.store_item import StoreItem
from app.models.user import User
from app.schemas.match import MatchResponse

_QUOTES = re.compile(r"[\"'׳״`]")
_SPACES = re.compile(r"\s+")


def match_key(item: ParsedItem) -> str:
    """Identity of a list item for memory: what, which brand, which size.

    Quantity is deliberately left out, so "2 חלב 3%" this week and "חלב 3%"
    next week share one memory.
    """
    parts = [item.search_terms[0], item.brand or "", item.size or ""]
    normalized = [_SPACES.sub(" ", _QUOTES.sub("", p)).strip().lower() for p in parts]
    return "|".join(normalized)[:200]


def load(db: Session, user: User, keys: set[str]) -> dict[tuple[str, str], str]:
    """(match_key, chain_slug) -> item_code for the given keys."""
    if not keys:
        return {}
    rows = db.execute(
        select(ItemMatch.match_key, Chain.slug, ItemMatch.item_code)
        .join(Chain, Chain.id == ItemMatch.chain_id)
        .where(ItemMatch.user_id == user.id, ItemMatch.match_key.in_(keys))
    ).all()
    return {(key, slug): code for key, slug, code in rows}


def remember(db: Session, user: User, key: str, chain_id: UUID, item_code: str, item_name: str) -> None:
    stmt = pg_insert(ItemMatch).values(
        user_id=user.id, chain_id=chain_id, match_key=key, item_code=item_code, item_name=item_name
    )
    db.execute(stmt.on_conflict_do_update(
        constraint="uq_item_matches_user_chain_key",
        set_={"item_code": item_code, "item_name": item_name},
    ))


def save_choice(db: Session, user: User, key: str, store_id: UUID, item_code: str) -> MatchResponse:
    """The user confirmed or swapped a product at one of their branches."""
    row = db.execute(
        select(StoreItem, Store, Chain)
        .join(Store, Store.id == StoreItem.store_id)
        .join(Chain, Chain.id == Store.chain_id)
        .where(StoreItem.store_id == store_id, StoreItem.item_code == item_code)
    ).first()
    if row is None:
        raise NotFoundError("That product isn't sold at this branch")
    item, _store, chain = row
    remember(db, user, key, chain.id, item.item_code, item.name)
    db.commit()
    saved = db.scalar(select(ItemMatch).where(
        ItemMatch.user_id == user.id, ItemMatch.chain_id == chain.id, ItemMatch.match_key == key
    ))
    return _to_response(saved, chain)


def list_matches(db: Session, user: User) -> list[MatchResponse]:
    rows = db.execute(
        select(ItemMatch, Chain).join(Chain, Chain.id == ItemMatch.chain_id)
        .where(ItemMatch.user_id == user.id).order_by(ItemMatch.match_key, Chain.name)
    ).all()
    return [_to_response(match, chain) for match, chain in rows]


def forget(db: Session, user: User, match_id: UUID) -> None:
    result = db.execute(delete(ItemMatch).where(ItemMatch.id == match_id, ItemMatch.user_id == user.id))
    if result.rowcount == 0:
        raise NotFoundError("Remembered match not found")
    db.commit()


def _to_response(match: ItemMatch, chain: Chain) -> MatchResponse:
    return MatchResponse(
        id=match.id, match_key=match.match_key, chain_slug=chain.slug, chain_name=chain.name,
        item_code=match.item_code, item_name=match.item_name, updated_at=match.updated_at,
    )
