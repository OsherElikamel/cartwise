"""Load chain files into Postgres.

Each PriceFull / PromoFull file is a complete snapshot of one branch, so a
sync replaces that branch's rows inside one transaction: readers see the
old snapshot or the new one, never half of each.
"""

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import NotFoundError, UpstreamError
from app.db.database import SessionLocal
from app.ingestion.chains import CHAINS, CHAINS_BY_SLUG, ChainConfig
from app.ingestion.parsers import parse_prices, parse_promotions, parse_stores
from app.ingestion.sources import RemoteFile, Source, latest
from app.models.chain import Chain, Store
from app.models.promotion import Promotion
from app.models.store_item import StoreItem
from app.models.user_store import UserStore

logger = logging.getLogger(__name__)

BATCH_SIZE = 2000


def _fetch(source: Source, remote: RemoteFile, chain_slug: str) -> bytes:
    """Download a file once; later runs read it from the local cache."""
    cache = Path(settings.DATA_DIR) / chain_slug / remote.name
    if cache.exists():
        return cache.read_bytes()
    raw = source.download(remote)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_bytes(raw)
    return raw


def prune_cache(older_than_days: int) -> int:
    """Delete downloaded files older than the given age; they only serve the current run."""
    root = Path(settings.DATA_DIR)
    if not root.exists():
        return 0
    cutoff = datetime.now(timezone.utc).timestamp() - older_than_days * 86400
    removed = 0
    for path in root.glob("*/*"):
        if path.is_file() and path.stat().st_mtime < cutoff:
            path.unlink()
            removed += 1
    return removed


def sync_chains(db: Session) -> None:
    for config in CHAINS:
        stmt = pg_insert(Chain).values(
            slug=config.slug, chain_code=config.chain_code, name=config.name, name_he=config.name_he
        )
        db.execute(stmt.on_conflict_do_update(
            index_elements=[Chain.slug],
            set_={"chain_code": config.chain_code, "name": config.name, "name_he": config.name_he},
        ))
    db.commit()


def sync_stores(db: Session, config: ChainConfig, source: Source) -> int:
    chain = db.scalar(select(Chain).where(Chain.slug == config.slug))
    if chain is None:
        raise NotFoundError(f"Chain {config.slug} not synced yet")

    remote = latest(source.list_files("Stores"), "Stores")
    if remote is None:
        raise UpstreamError(f"No Stores file published for {config.slug}")

    records = parse_stores(_fetch(source, remote, config.slug))
    for r in records:
        stmt = pg_insert(Store).values(
            chain_id=chain.id, store_code=r.store_code, sub_chain_code=r.sub_chain_code,
            name=r.name, address=r.address, city_code=r.city_code,
        )
        db.execute(stmt.on_conflict_do_update(
            constraint="uq_stores_chain_store_code",
            set_={"sub_chain_code": r.sub_chain_code, "name": r.name, "address": r.address, "city_code": r.city_code},
        ))
    db.commit()
    logger.info("%s: %d stores from %s", config.slug, len(records), remote.name)
    return len(records)


def _insert_batches(db: Session, model, rows: list[dict]) -> None:
    for start in range(0, len(rows), BATCH_SIZE):
        db.execute(insert(model), rows[start:start + BATCH_SIZE])


def sync_store_prices(db: Session, config: ChainConfig, source: Source, store: Store) -> tuple[int, int]:
    """Replace one branch's items and promotions with its latest files.

    A per-branch advisory lock serializes concurrent syncs (two users adding
    the same new branch, or a user add racing the nightly job): the second
    waits for the first instead of colliding on the same rows.
    """
    db.execute(select(func.pg_advisory_xact_lock(func.hashtext(str(store.id)))))
    price_file = latest(source.list_files("PriceFull", store.store_code), "PriceFull", store.store_code)
    if price_file is None:
        raise UpstreamError(f"No PriceFull file for {config.slug} store {store.store_code}")
    promo_file = latest(source.list_files("PromoFull", store.store_code), "PromoFull", store.store_code)

    items = parse_prices(_fetch(source, price_file, config.slug))
    promos = parse_promotions(_fetch(source, promo_file, config.slug)) if promo_file else []

    item_rows = [{"store_id": store.id, **vars(i)} for i in items]
    # A promotion on an item this branch doesn't list can never apply.
    item_codes = {i.item_code for i in items}
    promo_rows = [{"store_id": store.id, **vars(p)} for p in promos if p.item_code in item_codes]

    db.execute(delete(StoreItem).where(StoreItem.store_id == store.id))
    db.execute(delete(Promotion).where(Promotion.store_id == store.id))
    _insert_batches(db, StoreItem, item_rows)
    _insert_batches(db, Promotion, promo_rows)
    store.prices_synced_at = datetime.now(timezone.utc)
    db.commit()

    logger.info(
        "%s store %s (%s): %d items, %d promotion rows from %s",
        config.slug, store.store_code, store.name, len(item_rows), len(promo_rows), price_file.name,
    )
    return len(item_rows), len(promo_rows)


def sync_store_prices_by_id(store_id) -> None:
    """Background entry point: its own session, never raises into the caller."""
    with SessionLocal() as db:
        row = db.execute(select(Store, Chain).join(Chain).where(Store.id == store_id)).first()
        if row is None:
            return
        store, chain = row
        config = CHAINS_BY_SLUG[chain.slug]
        try:
            sync_store_prices(db, config, config.make_source(), store)
        except Exception:
            db.rollback()
            logger.exception("Background price load failed for %s store %s", chain.slug, store.store_code)


def prune_abandoned_stores(db: Session, older_than_days: int) -> int:
    """Stop tracking branches no user has followed for a while (demo branches stay)."""
    now = datetime.now(timezone.utc)
    followed = select(UserStore.store_id).distinct()
    db.execute(update(Store).where(Store.id.in_(followed)).values(last_followed_at=now))

    cutoff = now - timedelta(days=older_than_days)
    abandoned = list(db.scalars(
        select(Store).where(
            Store.is_tracked.is_(True), Store.is_demo.is_(False), Store.id.not_in(followed),
            (Store.last_followed_at.is_(None)) | (Store.last_followed_at < cutoff),
        )
    ))
    for store in abandoned:
        db.execute(delete(StoreItem).where(StoreItem.store_id == store.id))
        db.execute(delete(Promotion).where(Promotion.store_id == store.id))
        store.is_tracked = False
        store.prices_synced_at = None
        logger.info("Pruned abandoned branch %s (%s)", store.store_code, store.name)
    db.commit()
    return len(abandoned)
