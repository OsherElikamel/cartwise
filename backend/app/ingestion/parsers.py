"""Parse the price-transparency files every chain publishes by law.

The files share one schema on paper, but each chain bends it: gzip or
plain XML, UTF-8 / UTF-8 with BOM / UTF-16, inconsistent tag casing, and
padded or unpadded store codes. Everything here is a pure function from
bytes to records, so it can be tested without a network or a database.
"""

import gzip
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo

ISRAEL_TZ = ZoneInfo("Asia/Jerusalem")
GZIP_MAGIC = b"\x1f\x8b"

# Deals marked "for everyone" (ClubID 0) that still carry a condition in their
# text: the chain's credit card, a coupon, club membership, or a minimum spend.
CONDITIONAL_DEAL_WORDS = ("אשראי", "קופון", "מועדון", "חברי", "מעל ")


@dataclass(frozen=True)
class StoreRecord:
    store_code: str
    sub_chain_code: str | None
    name: str
    address: str | None
    city_code: str | None


@dataclass(frozen=True)
class ItemRecord:
    item_code: str
    item_type: int
    name: str
    manufacturer: str | None
    quantity: Decimal | None
    unit: str | None
    is_weighted: bool
    price: Decimal
    unit_price: Decimal | None
    price_updated_at: datetime | None


@dataclass(frozen=True)
class PromotionRecord:
    promotion_id: str
    item_code: str
    description: str
    min_qty: Decimal
    discounted_price: Decimal
    effective_unit_price: Decimal
    starts_at: datetime | None
    ends_at: datetime | None


# --- decoding ---------------------------------------------------------------

def decode_payload(raw: bytes) -> str:
    """Return the XML text of a downloaded file, whatever its packaging."""
    if raw.startswith(GZIP_MAGIC):
        raw = gzip.decompress(raw)
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16")
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return raw.decode("cp1255")


def parse_xml(raw: bytes) -> ET.Element:
    text = decode_payload(raw)
    # The declaration may claim an encoding we already decoded away (UTF-16).
    text = re.sub(r"^\s*<\?xml[^>]*\?>", "", text)
    return ET.fromstring(text)


# --- small helpers ----------------------------------------------------------

def _iter_tag(root: ET.Element, tag: str):
    tag = tag.lower()
    return (el for el in root.iter() if el.tag.lower() == tag)


def _text(el: ET.Element, *names: str) -> str | None:
    """Text of the first child matching any of names, case-insensitively."""
    wanted = {n.lower() for n in names}
    for child in el:
        if child.tag.lower() in wanted:
            value = (child.text or "").strip()
            return value or None
    return None


def _decimal(value: str | None) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(value.replace(",", ""))
    except InvalidOperation:
        return None


def _datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    value = value.strip().replace("T", " ")
    value = re.sub(r"\.\d+$", "", value)
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=ISRAEL_TZ)
        except ValueError:
            continue
    return None


def normalize_store_code(code: str) -> str:
    """'001' in one file and '1' in another are the same branch."""
    code = code.strip()
    return str(int(code)) if code.isdigit() else code


def _is_conditional(*texts: str | None) -> bool:
    return any(word in (text or "") for text in texts for word in CONDITIONAL_DEAL_WORDS)


def _leading_int(value: str | None, default: int = 0) -> int:
    match = re.match(r"\s*(\d+)", value or "")
    return int(match.group(1)) if match else default


# --- stores -----------------------------------------------------------------

def parse_stores(raw: bytes) -> list[StoreRecord]:
    root = parse_xml(raw)
    records: dict[str, StoreRecord] = {}

    def add(store_el: ET.Element, sub_chain_code: str | None) -> None:
        code = _text(store_el, "StoreID", "StoreId")
        name = _text(store_el, "StoreName")
        if not code or not name:
            return
        store_code = normalize_store_code(code)
        records[store_code] = StoreRecord(
            store_code=store_code,
            sub_chain_code=sub_chain_code,
            name=name,
            address=_text(store_el, "Address"),
            city_code=_text(store_el, "City"),
        )

    sub_chains = list(_iter_tag(root, "SubChain"))
    if sub_chains:
        for sub in sub_chains:
            sub_code = _text(sub, "SubChainID", "SubChainId")
            for store_el in _iter_tag(sub, "Store"):
                add(store_el, sub_code)
    else:
        for store_el in _iter_tag(root, "Store"):
            add(store_el, _text(store_el, "SubChainID", "SubChainId"))
    return list(records.values())


# --- prices -----------------------------------------------------------------

def parse_prices(raw: bytes) -> list[ItemRecord]:
    root = parse_xml(raw)
    items: dict[str, ItemRecord] = {}
    for el in _iter_tag(root, "Item"):
        code = _text(el, "ItemCode")
        name = _text(el, "ItemName", "ItemNm")
        price = _decimal(_text(el, "ItemPrice"))
        if not code or not name or price is None or price <= 0:
            continue
        items[code] = ItemRecord(
            item_code=code,
            item_type=_leading_int(_text(el, "ItemType"), default=1),
            name=name,
            manufacturer=_text(el, "ManufacturerName", "ManufactureName"),
            quantity=_decimal(_text(el, "Quantity")),
            unit=_text(el, "UnitQty", "UnitOfMeasure"),
            is_weighted=_text(el, "bIsWeighted", "BisWeighted") == "1",
            price=price,
            unit_price=_decimal(_text(el, "UnitOfMeasurePrice")),
            price_updated_at=_datetime(_text(el, "PriceUpdateDate", "PriceUpdateTime")),
        )
    return list(items.values())


# --- promotions -------------------------------------------------------------

def parse_promotions(raw: bytes) -> list[PromotionRecord]:
    """Promotions open to every shopper, flattened to one record per item.

    Skipped on purpose: club-only deals (ClubID != 0), coupons and deals whose
    text names a condition (credit card, club, minimum spend), deals with no
    price (gifts, "spend 99 get a cooler bag"), and spend-threshold deals.
    """
    root = parse_xml(raw)
    records: dict[tuple[str, str], PromotionRecord] = {}
    for promo in _iter_tag(root, "Promotion"):
        if _leading_int(_text(promo, "ClubID", "ClubId")) != 0:
            continue
        promotion_id = _text(promo, "PromotionID", "PromotionId")
        if not promotion_id:
            continue
        description = _text(promo, "PromotionDescription") or ""
        if _text(promo, "AdditionalIsCoupon") == "1" or _is_conditional(description, _text(promo, "Remarks")):
            continue
        starts_at = _datetime(_text(promo, "PromotionStartDateTime", "PromotionStartDate"))
        ends_at = _datetime(_text(promo, "PromotionEndDateTime", "PromotionEndDate"))

        groups = _iter_tag(promo, "Group")
        if any((_decimal(_text(g, "MinPurchaseAmount")) or 0) > 0 for g in groups):
            continue

        for item in _iter_tag(promo, "PromotionItem"):
            code = _text(item, "ItemCode")
            discounted = _decimal(_text(item, "DiscountedPrice"))
            min_qty = _decimal(_text(item, "MinQty")) or Decimal(1)
            if not code or discounted is None or discounted <= 0:
                continue
            # Weighted items carry a per-kilo price with a token MinQty (0.010).
            per_unit = discounted / min_qty if min_qty >= 1 else discounted
            records[(promotion_id, code)] = PromotionRecord(
                promotion_id=promotion_id,
                item_code=code,
                description=description[:300],
                min_qty=min_qty,
                discounted_price=discounted,
                effective_unit_price=per_unit.quantize(Decimal("0.001")),
                starts_at=starts_at,
                ends_at=ends_at,
            )
    return list(records.values())
