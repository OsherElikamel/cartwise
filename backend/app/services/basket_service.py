"""Grocery list in, ranked baskets out.

1. The LLM parses the free-text list (one call).
2. Postgres finds candidate products per item per branch (no AI).
3. The LLM picks one candidate per item per branch (one batched call).
4. Pricing is plain arithmetic on published prices; the LLM never sees a total.

Branches are ranked on the items every branch has, so a branch can't look
cheaper just because it is missing something.
"""

import logging
from collections import defaultdict
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.provider import LLMProvider
from app.ai.schemas import Candidate, MatchDecision, MatchRequestItem
from app.core.errors import ValidationError
from app.models.chain import Chain, Store
from app.models.user import User
from app.schemas.basket import BasketComparison, BasketLine, StoreBasket
from app.schemas.catalog import ProductResult
from app.services.catalog_service import search_products
from app.services.pricing import price_line
from app.services.user_store_service import demo_store_ids, followed_store_ids

logger = logging.getLogger(__name__)

CANDIDATES_PER_STORE = 10


def allowed_store_ids(db: Session, user: User | None, requested: list[UUID] | None) -> list[UUID]:
    """Which branches this caller may compare on.

    Guests get the demo branches. Signed-in users get the branches they follow
    (or the demo set until they follow some). A request may narrow that set,
    never widen it.
    """
    allowed = followed_store_ids(db, user) if user else []
    if not allowed:
        allowed = demo_store_ids(db)
    if requested is None:
        return allowed
    outside = set(requested) - set(allowed)
    if outside:
        raise ValidationError("Compare only on your own branches" if user else "Sign in to compare on other branches")
    return requested


def _resolve_stores(db: Session, store_ids: list[UUID] | None) -> list[tuple[Store, Chain]]:
    query = select(Store, Chain).join(Chain)
    query = query.where(Store.id.in_(store_ids)) if store_ids else query.where(Store.is_tracked.is_(True))
    rows = db.execute(query.order_by(Chain.name)).all()

    if store_ids and len(rows) != len(set(store_ids)):
        raise ValidationError("One or more branches were not found")
    if not rows:
        raise ValidationError("No branches selected")
    chains = [chain.slug for _, chain in rows]
    if len(chains) != len(set(chains)):
        raise ValidationError("Choose one branch per chain")
    untracked = [store.name for store, _ in rows if not store.is_tracked]
    if untracked:
        raise ValidationError(f"No price data yet for: {', '.join(untracked)}")
    return [(store, chain) for store, chain in rows]


def compare_basket(db: Session, llm: LLMProvider, text: str, store_ids: list[UUID] | None) -> BasketComparison:
    stores = _resolve_stores(db, store_ids)
    ids = [store.id for store, _ in stores]

    items = llm.parse_list(text)
    if not items:
        raise ValidationError("No products found in the list")

    # candidates[index][chain_slug] -> ProductResult rows from the text search
    candidates: dict[int, dict[str, list[ProductResult]]] = {}
    for index, item in enumerate(items):
        by_chain: dict[str, list[ProductResult]] = defaultdict(list)
        for result in search_products(db, item.search_terms, ids, CANDIDATES_PER_STORE, prefer_weighted=item.unit == "kg"):
            by_chain[result.chain_slug].append(result)
        candidates[index] = by_chain

    requests = [
        MatchRequestItem(
            index=index,
            item=item,
            candidates_by_chain={
                slug: [
                    Candidate(item_code=r.item_code, name=r.name, manufacturer=r.manufacturer,
                              is_weighted=r.is_weighted, price=float(r.price))
                    for r in results
                ]
                for slug, results in candidates[index].items()
            },
        )
        for index, item in enumerate(items)
        if candidates[index]
    ]
    decisions = llm.choose_matches(requests) if requests else []
    chosen = _accept_decisions(decisions, candidates)

    baskets = [_build_basket(store, chain, items, chosen) for store, chain in stores]
    shared = [i for i in range(len(items)) if all(i not in b.missing for b in baskets)]
    for basket in baskets:
        basket.shared_total = sum(
            (line.line_total for line in basket.lines if line.index in shared), Decimal("0.00")
        )
    baskets.sort(key=lambda b: (len(b.missing) == len(items), b.shared_total))

    totals = [b.shared_total for b in baskets]
    return BasketComparison(
        items=items,
        shared_items=shared,
        stores=baskets,
        savings_vs_most_expensive=(max(totals) - min(totals)) if totals else Decimal("0.00"),
    )


def _accept_decisions(
    decisions: list[MatchDecision], candidates: dict[int, dict[str, list[ProductResult]]]
) -> dict[tuple[int, str], tuple[ProductResult, MatchDecision]]:
    """Keep only decisions that point at a candidate we actually offered."""
    chosen = {}
    for d in decisions:
        offered = {r.item_code: r for r in candidates.get(d.index, {}).get(d.chain, [])}
        if d.item_code is None:
            continue
        if d.item_code not in offered:
            logger.warning("LLM chose unknown item %s for item %d at %s; ignored", d.item_code, d.index, d.chain)
            continue
        chosen[(d.index, d.chain)] = (offered[d.item_code], d)
    return chosen


def _build_basket(store, chain, items, chosen) -> StoreBasket:
    lines, missing = [], []
    for index, item in enumerate(items):
        match = chosen.get((index, chain.slug))
        if match is None:
            missing.append(index)
            lines.append(BasketLine(
                index=index, item_code=None, name=None, is_weighted=None, regular_price=None,
                line_total=None, deal=None, confidence=None, reason="Not found at this branch",
            ))
            continue
        product, decision = match
        quantity = Decimal(str(item.quantity))
        priced = price_line(
            quantity, product.is_weighted, product.price,
            product.deal.min_qty if product.deal else None,
            product.deal.unit_price if product.deal else None,
        )
        lines.append(BasketLine(
            index=index, item_code=product.item_code, name=product.name, is_weighted=product.is_weighted,
            regular_price=product.price, line_total=priced.total,
            deal=product.deal.description if priced.deal_applied and product.deal else None,
            confidence=decision.confidence, reason=decision.reason,
        ))
    return StoreBasket(
        store_id=store.id, chain_slug=chain.slug, chain_name=chain.name, store_name=store.name,
        shared_total=Decimal("0.00"),
        full_total=sum((line.line_total for line in lines if line.line_total is not None), Decimal("0.00")),
        missing=missing, lines=lines,
    )
