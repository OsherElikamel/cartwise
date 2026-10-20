"""Read side of the price data: chains, branches and product search."""

from uuid import UUID

from sqlalchemy import Float, func, literal, or_, select, true, tuple_
from sqlalchemy.orm import Session

from app.models.chain import Chain, Store
from app.models.promotion import Promotion
from app.models.store_item import StoreItem
from app.schemas.catalog import ChainResponse, Deal, ProductResult, StoreResponse

MIN_WORD_SIMILARITY = 0.3


def list_chains(db: Session) -> list[ChainResponse]:
    rows = db.execute(
        select(
            Chain,
            func.count(Store.id),
            func.count(Store.id).filter(Store.is_tracked.is_(True)),
        )
        .outerjoin(Store)
        .group_by(Chain.id)
        .order_by(Chain.name)
    ).all()
    return [
        ChainResponse(
            id=chain.id, slug=chain.slug, name=chain.name, name_he=chain.name_he,
            store_count=total, tracked_store_count=tracked,
        )
        for chain, total, tracked in rows
    ]


def search_stores(
    db: Session, search: str | None, chain_slug: str | None, tracked_only: bool, limit: int, demo_only: bool = False
) -> list[StoreResponse]:
    query = select(Store, Chain).join(Chain)
    if chain_slug:
        query = query.where(Chain.slug == chain_slug)
    if tracked_only:
        query = query.where(Store.is_tracked.is_(True))
    if demo_only:
        query = query.where(Store.is_demo.is_(True))
    # Every word must appear in the branch name, address or chain name: a city
    # filter can't work because some chains publish no city codes at all.
    for word in (search or "").split():
        pattern = f"%{word}%"
        query = query.where(or_(
            Store.name.ilike(pattern), Store.address.ilike(pattern),
            Chain.name.ilike(pattern), Chain.name_he.ilike(pattern),
        ))
    rows = db.execute(query.order_by(Chain.name, Store.name).limit(limit)).all()
    return [
        StoreResponse(
            id=store.id, chain_slug=chain.slug, chain_name=chain.name, store_code=store.store_code,
            name=store.name, address=store.address, is_tracked=store.is_tracked,
            is_demo=store.is_demo, is_ready=store.prices_synced_at is not None,
        )
        for store, chain in rows
    ]


def _best_deal(store_id, item_code, regular_price):
    """The cheapest live promotion for one candidate row, as a lateral join."""
    now = func.now()
    return (
        select(Promotion.description, Promotion.min_qty, Promotion.effective_unit_price)
        .where(
            Promotion.store_id == store_id,
            Promotion.item_code == item_code,
            or_(Promotion.starts_at.is_(None), Promotion.starts_at <= now),
            or_(Promotion.ends_at.is_(None), Promotion.ends_at > now),
            Promotion.effective_unit_price < regular_price,
        )
        .order_by(Promotion.effective_unit_price)
        .limit(1)
        .lateral("deal")
    )


def search_products(
    db: Session, terms: list[str], store_ids: list[UUID] | None, per_store: int, prefer_weighted: bool = False
) -> list[ProductResult]:
    """Top candidates at each tracked branch for one or more search terms.

    word_similarity scores how well a term fits inside a longer product name,
    which suits short queries like "חלב 3%" far better than comparing the two
    strings whole. A product scores by its best-matching term, because labels
    mix forms: loose tomatoes are "עגבניה" while the shopper writes "עגבניות".
    """
    scores = [func.word_similarity(term, StoreItem.name) for term in terms]
    score = (func.greatest(*scores) if len(scores) > 1 else scores[0]).cast(Float)
    # Many names contain the whole term (score 1.0); the closer overall match breaks the tie.
    tiebreak = func.similarity(terms[0], StoreItem.name)
    # Bought by weight: loose produce before canned or packaged products that share the word.
    ordering = [StoreItem.is_weighted.desc()] if prefer_weighted else []
    # Among equal scores, a name that starts with one of the terms is almost
    # always the one meant ("במבה 80 גרם", not "פופקו פופקורן במבה"), and the
    # plain product usually has the shortest label ("עגבניה", not "עגבניות שרי").
    starts_with = or_(*[StoreItem.name.ilike(f"{term}%") for term in terms])
    ordering += [score.desc(), starts_with.desc(), func.length(StoreItem.name), tiebreak.desc()]
    scope = Store.is_tracked.is_(True) if not store_ids else Store.id.in_(store_ids)
    ranked = (
        select(
            StoreItem.store_id, StoreItem.item_code, StoreItem.name, StoreItem.manufacturer,
            StoreItem.is_weighted, StoreItem.price, StoreItem.unit_price,
            score.label("score"),
            func.row_number().over(partition_by=StoreItem.store_id, order_by=ordering).label("rank"),
        )
        .join(Store, Store.id == StoreItem.store_id)
        .where(scope, score >= MIN_WORD_SIMILARITY)
        .subquery("ranked")
    )
    rows = db.execute(
        _with_chain_and_deal(ranked).where(ranked.c.rank <= per_store).order_by(Chain.name, ranked.c.rank)
    ).all()
    return [_to_product(r) for r in rows]


def get_products(db: Session, keys: list[tuple[UUID, str]]) -> dict[tuple[UUID, str], ProductResult]:
    """Specific (store_id, item_code) products with their best live deal."""
    if not keys:
        return {}
    picked = (
        select(
            StoreItem.store_id, StoreItem.item_code, StoreItem.name, StoreItem.manufacturer,
            StoreItem.is_weighted, StoreItem.price, StoreItem.unit_price,
            literal(1.0, Float).label("score"),
        )
        .where(tuple_(StoreItem.store_id, StoreItem.item_code).in_(keys))
        .subquery("picked")
    )
    rows = db.execute(_with_chain_and_deal(picked)).all()
    return {(r.store_id, r.item_code): _to_product(r) for r in rows}


def _with_chain_and_deal(products):
    """Add chain names and the best live deal to a subquery of store items."""
    deal = _best_deal(products.c.store_id, products.c.item_code, products.c.price)
    return (
        select(
            products,
            Chain.slug.label("chain_slug"),
            Chain.name.label("chain_name"),
            deal.c.description.label("deal_description"),
            deal.c.min_qty.label("deal_min_qty"),
            deal.c.effective_unit_price.label("deal_unit_price"),
        )
        .join(Store, Store.id == products.c.store_id)
        .join(Chain, Chain.id == Store.chain_id)
        .outerjoin(deal, true())
    )


def _to_product(row) -> ProductResult:
    deal = None
    if row.deal_description is not None:
        deal = Deal(description=row.deal_description, min_qty=row.deal_min_qty, unit_price=row.deal_unit_price)
    return ProductResult(
        store_id=row.store_id, chain_slug=row.chain_slug, chain_name=row.chain_name,
        item_code=row.item_code, name=row.name, manufacturer=row.manufacturer,
        is_weighted=row.is_weighted, price=row.price, unit_price=row.unit_price,
        deal=deal, score=round(row.score, 3),
    )
