"""What one basket line costs. Pure arithmetic, no database, fully unit-tested."""

from dataclasses import dataclass
from decimal import ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")


@dataclass(frozen=True)
class LinePrice:
    total: Decimal
    deal_applied: bool


def price_line(
    quantity: Decimal,
    is_weighted: bool,
    price: Decimal,
    deal_min_qty: Decimal | None = None,
    deal_unit_price: Decimal | None = None,
) -> LinePrice:
    """Cost of buying `quantity` of one product.

    Weighted products: price is per kilo and quantity is kilos.
    Packaged products: quantity is rounded up to whole packages.
    Deals: a single-item or per-kilo deal (min_qty <= 1) applies to everything;
    a multi-buy ("3 for 10") applies to each complete group of min_qty, and the
    remainder is charged at the regular price.
    """
    if not is_weighted:
        quantity = max(Decimal(1), quantity.to_integral_value(rounding=ROUND_CEILING))

    if deal_unit_price is None or deal_min_qty is None or deal_unit_price >= price:
        return LinePrice(_cents(quantity * price), deal_applied=False)

    if is_weighted or deal_min_qty <= 1:
        return LinePrice(_cents(quantity * deal_unit_price), deal_applied=True)

    groups = (quantity / deal_min_qty).to_integral_value(rounding=ROUND_FLOOR)
    if groups == 0:
        return LinePrice(_cents(quantity * price), deal_applied=False)
    in_deal = groups * deal_min_qty
    total = in_deal * deal_unit_price + (quantity - in_deal) * price
    return LinePrice(_cents(total), deal_applied=True)


def _cents(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)
