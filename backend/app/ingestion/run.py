"""Command-line entry point for ingestion.

    python -m app.ingestion.run stores            # all chains' branch lists
    python -m app.ingestion.run track rami-levy 1 # start tracking a branch
    python -m app.ingestion.run prices            # refresh every tracked branch
    python -m app.ingestion.run prune             # untrack branches nobody follows
"""

import argparse
import logging
import sys

from sqlalchemy import select

from app.core.config import settings
from app.core.errors import DomainError
from app.db.database import SessionLocal
from app.ingestion.chains import CHAINS, CHAINS_BY_SLUG
from app.ingestion.parsers import normalize_store_code
from app.ingestion.pipeline import prune_abandoned_stores, sync_chains, sync_store_prices, sync_stores
from app.models.chain import Chain, Store

logger = logging.getLogger("cartwise.ingestion")


def cmd_stores(args) -> int:
    failures = 0
    with SessionLocal() as db:
        sync_chains(db)
        for config in _chains(args.chain):
            try:
                sync_stores(db, config, config.make_source())
            except DomainError as exc:
                db.rollback()
                failures += 1
                logger.error("%s stores failed: %s", config.slug, exc.detail)
    return 1 if failures else 0


def cmd_track(args) -> int:
    with SessionLocal() as db:
        store = db.scalar(
            select(Store).join(Chain)
            .where(Chain.slug == args.chain, Store.store_code == normalize_store_code(args.store_code))
        )
        if store is None:
            logger.error("No store %s for %s (run `stores` first)", args.store_code, args.chain)
            return 1
        store.is_tracked = True
        store.is_demo = store.is_demo or args.demo
        db.commit()
        logger.info("Tracking %s store %s (%s)%s", args.chain, store.store_code, store.name, " as demo" if args.demo else "")
    return 0


def cmd_prune(args) -> int:
    with SessionLocal() as db:
        pruned = prune_abandoned_stores(db, args.days)
    logger.info("Pruned %d abandoned branches", pruned)
    return 0


def cmd_prices(args) -> int:
    failures = 0
    with SessionLocal() as db:
        for config in _chains(args.chain):
            stores = db.scalars(
                select(Store).join(Chain).where(Chain.slug == config.slug, Store.is_tracked.is_(True))
            ).all()
            if not stores:
                continue
            source = config.make_source()
            for store in stores:
                try:
                    sync_store_prices(db, config, source, store)
                except DomainError as exc:
                    db.rollback()
                    failures += 1
                    logger.error("%s store %s failed: %s", config.slug, store.store_code, exc.detail)
    return 1 if failures else 0


def _chains(slug: str | None):
    return [CHAINS_BY_SLUG[slug]] if slug else CHAINS


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    parser = argparse.ArgumentParser(prog="python -m app.ingestion.run")
    sub = parser.add_subparsers(dest="command", required=True)
    choices = list(CHAINS_BY_SLUG)

    p = sub.add_parser("stores", help="sync branch lists")
    p.add_argument("--chain", choices=choices)
    p.set_defaults(func=cmd_stores)

    p = sub.add_parser("track", help="start ingesting prices for a branch")
    p.add_argument("chain", choices=choices)
    p.add_argument("store_code")
    p.add_argument("--demo", action="store_true", help="also make it a guest demo branch")
    p.set_defaults(func=cmd_track)

    p = sub.add_parser("prune", help="stop tracking branches nobody follows")
    p.add_argument("--days", type=int, default=settings.PRUNE_AFTER_DAYS)
    p.set_defaults(func=cmd_prune)

    p = sub.add_parser("prices", help="refresh prices for tracked branches")
    p.add_argument("--chain", choices=choices)
    p.set_defaults(func=cmd_prices)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
