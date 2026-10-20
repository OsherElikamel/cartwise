"""Grocery list in, ranked baskets out.

1. The LLM parses the free-text list (one call).
2. A signed-in user's remembered matches are used directly.
3. For everything else, Postgres finds candidate products per branch, and the
   LLM picks one per item per branch (one batched call, skipped when nothing
   is left). Confident picks are remembered for next time.
4. Pricing is plain arithmetic on published prices; the LLM never sees a total.

Branches are ranked on the items every branch has, so a branch can't look
cheaper just because it is missing something.
"""

import logging
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.provider import LLMProvider
from app.ai.schemas import Candidate, MatchDecision, MatchRequestItem, ParsedItem
from app.core.errors import ValidationError
from app.models.chain import Chain, Store
from app.models.user import User
from app.schemas.basket import Alternative, BasketComparison, BasketLine, StoreBasket
from app.schemas.catalog import ProductResult
from app.services import match_service
from app.services.catalog_service import get_products, search_products
from app.services.pricing import price_line
from app.services.user_store_service import demo_store_ids, followed_store_ids

logger = logging.getLogger(__name__)

CANDIDATES_PER_STORE = 10
ALTERNATIVES_PER_LINE = 4


@dataclass(frozen=True)
class Pick:
    store_id: UUID
    index: int
    item_code: str
    confidence: str
    reason: str


@dataclass(frozen=True)
class Choice:
    product: ProductResult
    confidence: str
    reason: str


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
        if user:
            raise ValidationError("Compare only on your own branches", "own_branches_only")
        raise ValidationError("Sign in to compare on other branches", "sign_in_for_branches")
    return requested


def _resolve_stores(db: Session, store_ids: list[UUID] | None) -> list[tuple[Store, Chain]]:
    query = select(Store, Chain).join(Chain)
    query = query.where(Store.id.in_(store_ids)) if store_ids else query.where(Store.is_tracked.is_(True))
    rows = db.execute(query.order_by(Chain.name)).all()

    if store_ids and len(rows) != len(set(store_ids)):
        raise ValidationError("One or more branches were not found", "branch_not_found")
    if not rows:
        raise ValidationError("No branches selected", "no_branches")
    chains = [chain.slug for _, chain in rows]
    if len(chains) != len(set(chains)):
        raise ValidationError("Choose one branch per chain", "one_branch_per_chain")
    untracked = [store.name for store, _ in rows if not store.is_tracked]
    if untracked:
        raise ValidationError(f"No price data yet for: {', '.join(untracked)}", "prices_not_ready")
    return [(store, chain) for store, chain in rows]


def parse_list(llm: LLMProvider, text: str) -> list[ParsedItem]:
    items = llm.parse_list(text)
    if not items:
        raise ValidationError("No products found in the list", "empty_list")
    return items


def compare_basket(
    db: Session, llm: LLMProvider, text: str, store_ids: list[UUID] | None, user: User | None = None
) -> BasketComparison:
    return compare_items(db, llm, parse_list(llm, text), store_ids, user)


def compare_items(
    db: Session, llm: LLMProvider, items: list[ParsedItem], store_ids: list[UUID] | None, user: User | None = None
) -> BasketComparison:
    """Compare an already-parsed list (a saved list skips the parsing call)."""
    stores = _resolve_stores(db, store_ids)
    store_by_chain = {chain.slug: store for store, chain in stores}
    chain_by_slug = {chain.slug: chain for _, chain in stores}
    keys = [match_service.match_key(item) for item in items]

    chosen = _remembered_choices(db, user, keys, store_by_chain) if user else {}
    remembered_count = len(chosen)

    open_pairs = {(i, slug) for i in range(len(items)) for slug in store_by_chain if (i, slug) not in chosen}
    candidates = _find_candidates(db, items, open_pairs, store_by_chain)
    decisions = llm.choose_matches(_match_requests(items, open_pairs, candidates)) if candidates else []

    for decision, product in _accept_decisions(decisions, open_pairs, candidates):
        chosen[(decision.index, decision.chain)] = Choice(product, decision.confidence, decision.reason)
        if user and decision.confidence == "high":
            match_service.remember(db, user, keys[decision.index], chain_by_slug[decision.chain].id,
                                   product.item_code, product.name)
    if user:
        db.commit()

    # The provider records whether it had to fall back to rule-based matching.
    return _assemble(stores, items, keys, chosen, candidates, remembered_count, not getattr(llm, "degraded", False))


def reprice(
    db: Session, items: list[ParsedItem], store_ids: list[UUID], picks: list[Pick]
) -> BasketComparison:
    """Recompute totals and ranking for explicit product picks. No AI involved.

    Used after the user confirms or swaps a product, so prices always come
    from the server, never from arithmetic in the browser.
    """
    stores = _resolve_stores(db, store_ids)
    store_by_chain = {chain.slug: store for store, chain in stores}
    chain_by_store = {store.id: chain for store, chain in stores}
    keys = [match_service.match_key(item) for item in items]

    valid = [p for p in picks if p.store_id in chain_by_store and 0 <= p.index < len(items)]
    products = get_products(db, [(p.store_id, p.item_code) for p in valid])
    chosen = {
        (p.index, chain_by_store[p.store_id].slug): Choice(products[(p.store_id, p.item_code)], p.confidence, p.reason)
        for p in valid
        if (p.store_id, p.item_code) in products
    }
    all_pairs = {(i, slug) for i in range(len(items)) for slug in store_by_chain}
    candidates = _find_candidates(db, items, all_pairs, store_by_chain)
    remembered = sum(1 for c in chosen.values() if c.confidence == "remembered")
    return _assemble(stores, items, keys, chosen, candidates, remembered)


def _assemble(stores, items, keys, chosen, candidates, remembered_count, ai_available: bool = True) -> BasketComparison:
    """Price every branch's basket and rank branches on the items all of them have."""
    baskets = [_build_basket(store, chain, items, keys, chosen, candidates) for store, chain in stores]
    shared = [i for i in range(len(items)) if all(i not in b.missing for b in baskets)]
    for basket in baskets:
        basket.shared_total = sum(
            (line.line_total for line in basket.lines if line.index in shared), Decimal("0.00")
        )
    baskets.sort(key=lambda b: (len(b.missing) == len(items), b.shared_total))

    totals = [b.shared_total for b in baskets]
    return BasketComparison(
        ai_available=ai_available,
        items=items,
        shared_items=shared,
        stores=baskets,
        savings_vs_most_expensive=(max(totals) - min(totals)) if totals else Decimal("0.00"),
        remembered_matches=remembered_count,
        ai_matches=len(chosen) - remembered_count,
    )


def _remembered_choices(db, user, keys, store_by_chain) -> dict[tuple[int, str], Choice]:
    """Remembered products that this branch still sells."""
    memory = match_service.load(db, user, set(keys))
    wanted = {
        (index, slug): (store.id, memory[(key, slug)])
        for index, key in enumerate(keys)
        for slug, store in store_by_chain.items()
        if (key, slug) in memory
    }
    products = get_products(db, list(wanted.values()))
    return {
        pair: Choice(products[product_key], "remembered", "Your saved choice")
        for pair, product_key in wanted.items()
        if product_key in products
    }


def _find_candidates(db, items, open_pairs, store_by_chain) -> dict[int, dict[str, list[ProductResult]]]:
    """Text-search candidates for every (item, chain) still without a choice."""
    candidates: dict[int, dict[str, list[ProductResult]]] = {}
    for index in sorted({i for i, _ in open_pairs}):
        item = items[index]
        open_chains = {slug for i, slug in open_pairs if i == index}
        store_ids = [store_by_chain[slug].id for slug in open_chains]
        by_chain: dict[str, list[ProductResult]] = defaultdict(list)
        for result in search_products(db, item.search_terms, store_ids, CANDIDATES_PER_STORE, prefer_weighted=item.unit == "kg"):
            by_chain[result.chain_slug].append(result)
        if by_chain:
            candidates[index] = dict(by_chain)
    return candidates


def _match_requests(items: list[ParsedItem], open_pairs, candidates) -> list[MatchRequestItem]:
    return [
        MatchRequestItem(
            index=index,
            item=items[index],
            candidates_by_chain={
                slug: [
                    Candidate(item_code=r.item_code, name=r.name, manufacturer=r.manufacturer,
                              is_weighted=r.is_weighted, price=float(r.price))
                    for r in results
                ]
                for slug, results in by_chain.items()
                if (index, slug) in open_pairs
            },
        )
        for index, by_chain in candidates.items()
    ]


def _accept_decisions(decisions: list[MatchDecision], open_pairs, candidates):
    """Keep only decisions for open pairs that point at a candidate we offered."""
    for d in decisions:
        if d.item_code is None or (d.index, d.chain) not in open_pairs:
            continue
        offered = {r.item_code: r for r in candidates.get(d.index, {}).get(d.chain, [])}
        if d.item_code not in offered:
            logger.warning("LLM chose unknown item %s for item %d at %s; ignored", d.item_code, d.index, d.chain)
            continue
        yield d, offered[d.item_code]


def _quantity_for(item: ParsedItem, product: ProductResult) -> tuple[Decimal, Decimal | None]:
    """How much of `product` to price, and the estimated kilos when we had to guess.

    A counted item ("אבטיח", "6 תפוחים") sold by weight is priced at its typical
    weight per unit, and flagged as an estimate. The same item sold per unit
    (some chains price a pineapple per piece) is simply counted.
    """
    quantity = Decimal(str(item.quantity))
    if product.is_weighted and item.unit == "unit":
        kilos = quantity * Decimal(str(item.unit_weight_kg or 1))
        return kilos, kilos.normalize()
    return quantity, None


def _build_basket(store, chain, items, keys, chosen, candidates) -> StoreBasket:
    lines, missing = [], []
    for index, item in enumerate(items):
        choice = chosen.get((index, chain.slug))
        offered = candidates.get(index, {}).get(chain.slug, [])
        alternatives = [
            Alternative(item_code=r.item_code, name=r.name, price=r.price)
            for r in offered
            if choice is None or r.item_code != choice.product.item_code
        ][:ALTERNATIVES_PER_LINE]

        if choice is None:
            missing.append(index)
            lines.append(BasketLine(
                index=index, match_key=keys[index], item_code=None, name=None, is_weighted=None,
                regular_price=None, line_total=None, deal=None, confidence=None,
                reason="Not found at this branch", alternatives=alternatives,
            ))
            continue

        product = choice.product
        quantity, estimated_kg = _quantity_for(item, product)
        priced = price_line(
            quantity, product.is_weighted, product.price,
            product.deal.min_qty if product.deal else None,
            product.deal.unit_price if product.deal else None,
        )
        lines.append(BasketLine(
            index=index, match_key=keys[index], item_code=product.item_code, name=product.name,
            is_weighted=product.is_weighted, regular_price=product.price, line_total=priced.total,
            estimated_kg=estimated_kg,
            deal=product.deal.description if priced.deal_applied and product.deal else None,
            confidence=choice.confidence, reason=choice.reason, alternatives=alternatives,
        ))
    return StoreBasket(
        store_id=store.id, chain_slug=chain.slug, chain_name=chain.name, store_name=store.name,
        prices_updated_at=store.prices_synced_at, shared_total=Decimal("0.00"),
        full_total=sum((line.line_total for line in lines if line.line_total is not None), Decimal("0.00")),
        missing=missing, lines=lines,
    )
