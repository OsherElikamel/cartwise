"""The branches a user shops at, one per chain.

Following a branch nobody tracks yet starts tracking it; its prices are
then loaded in the background, so the request returns at once with the
branch marked as loading.
"""

import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import ConflictError, NotFoundError
from app.models.chain import Chain, Store
from app.models.user import User
from app.models.user_store import UserStore
from app.schemas.catalog import StoreResponse

logger = logging.getLogger(__name__)


def to_store_response(store: Store, chain: Chain) -> StoreResponse:
    return StoreResponse(
        id=store.id, chain_slug=chain.slug, chain_name=chain.name, store_code=store.store_code,
        name=store.name, address=store.address, is_tracked=store.is_tracked,
        is_demo=store.is_demo, is_ready=store.prices_synced_at is not None,
    )


def list_followed(db: Session, user: User) -> list[StoreResponse]:
    rows = db.execute(
        select(Store, Chain).join(Chain).join(UserStore, UserStore.store_id == Store.id)
        .where(UserStore.user_id == user.id).order_by(Chain.name)
    ).all()
    return [to_store_response(store, chain) for store, chain in rows]


def follow(db: Session, user: User, store_id: UUID) -> tuple[StoreResponse, bool]:
    """Follow a branch, replacing the user's branch of the same chain.

    Returns the branch and whether its prices still need loading.
    """
    row = db.execute(select(Store, Chain).join(Chain).where(Store.id == store_id)).first()
    if row is None:
        raise NotFoundError("Branch not found")
    store, chain = row

    if not store.is_tracked:
        tracked = db.scalar(select(func.count()).select_from(Store).where(Store.is_tracked.is_(True)))
        if tracked >= settings.MAX_TRACKED_STORES:
            raise ConflictError("CartWise is at its branch limit right now; pick a branch that's already available")
        store.is_tracked = True
        logger.info("Branch %s (%s) is now tracked", store.id, store.name)

    same_chain = select(Store.id).where(Store.chain_id == chain.id)
    db.execute(delete(UserStore).where(UserStore.user_id == user.id, UserStore.store_id.in_(same_chain)))
    db.add(UserStore(user_id=user.id, store_id=store.id))
    store.last_followed_at = datetime.now(timezone.utc)
    db.commit()
    return to_store_response(store, chain), store.prices_synced_at is None


def unfollow(db: Session, user: User, store_id: UUID) -> None:
    result = db.execute(delete(UserStore).where(UserStore.user_id == user.id, UserStore.store_id == store_id))
    if result.rowcount == 0:
        raise NotFoundError("You don't follow this branch")
    db.commit()


def followed_store_ids(db: Session, user: User) -> list[UUID]:
    return list(db.scalars(select(UserStore.store_id).where(UserStore.user_id == user.id)))


def demo_store_ids(db: Session) -> list[UUID]:
    return list(db.scalars(select(Store.id).where(Store.is_demo.is_(True), Store.is_tracked.is_(True))))
