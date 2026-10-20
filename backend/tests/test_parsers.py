import gzip
from decimal import Decimal

from app.ingestion.parsers import (
    decode_payload,
    normalize_store_code,
    parse_prices,
    parse_promotions,
    parse_stores,
)

STORES_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Root><ChainID>7290058140886</ChainID><SubChains><SubChain>
  <SubChainID>001</SubChainID>
  <Stores>
    <Store><StoreID>001</StoreID><StoreName>תלפיות</StoreName><Address>האומן 15</Address><City>3000</City></Store>
    <Store><StoreID>002</StoreID><StoreName>מבשרת</StoreName><Address></Address><City>3000</City></Store>
    <Store><StoreID>003</StoreID><StoreName>חולון</StoreName><Address>unknown</Address><City>0</City></Store>
  </Stores>
</SubChain></SubChains></Root>"""

PRICES_XML = """<Root><ChainID>7290027600007</ChainID><StoreID>001</StoreID><Items>
  <Item>
    <PriceUpdateTime>2026-09-30T08:54:00</PriceUpdateTime>
    <ItemCode>7290004131074</ItemCode><ItemType>1</ItemType>
    <ItemName>חלב 3% קרטון 1 ליטר</ItemName><ManufactureName>תנובה</ManufactureName>
    <Quantity>1.00</Quantity><UnitQty>ליטר</UnitQty><bIsWeighted>0</bIsWeighted>
    <ItemPrice>7.12</ItemPrice><UnitOfMeasurePrice>7.12</UnitOfMeasurePrice>
  </Item>
  <item>
    <itemcode>2000123</itemcode><itemtype>0</itemtype><itemname>עגבניות</itemname>
    <bisweighted>1</bisweighted><itemprice>6.90</itemprice>
  </item>
  <Item><ItemCode>999</ItemCode><ItemName>broken price</ItemName><ItemPrice>0.00</ItemPrice></Item>
</Items></Root>"""


def promo(promotion_id, club, items_xml, min_purchase="0.00", description=None, coupon="0"):
    return f"""<Promotion>
      <PromotionID>{promotion_id}</PromotionID>
      <PromotionDescription>{description or f"deal {promotion_id}"}</PromotionDescription>
      <AdditionalIsCoupon>{coupon}</AdditionalIsCoupon>
      <PromotionStartDateTime>2026-10-01T00:00:00.000</PromotionStartDateTime>
      <PromotionEndDateTime>2026-10-31T23:59:00.000</PromotionEndDateTime>
      <ClubID>{club}</ClubID>
      <Groups><Group><MinPurchaseAmount>{min_purchase}</MinPurchaseAmount>
        <PromotionItems>{items_xml}</PromotionItems>
      </Group></Groups>
    </Promotion>"""


def promo_item(code, min_qty, price):
    return f"<PromotionItem><ItemCode>{code}</ItemCode><MinQty>{min_qty}</MinQty><DiscountedPrice>{price}</DiscountedPrice></PromotionItem>"


def test_decode_handles_gzip_utf8_bom_and_utf16():
    text = "<Root>שלום</Root>"
    assert decode_payload(gzip.compress(text.encode("utf-8"))) == text
    assert decode_payload(("﻿" + text).encode("utf-8")) == text
    assert decode_payload(text.encode("utf-16")) == text


def test_store_codes_are_normalized():
    assert normalize_store_code("001") == normalize_store_code("1") == "1"


def test_parse_stores_reads_utf16_file_with_declaration():
    stores = parse_stores(STORES_XML.encode("utf-16"))
    assert [s.store_code for s in stores] == ["1", "2", "3"]
    assert stores[0].name == "תלפיות"
    assert stores[0].sub_chain_code == "001"
    assert stores[1].address is None
    assert stores[2].address is None  # the literal "unknown" some chains publish


def test_parse_prices_handles_tag_casing_and_skips_invalid_prices():
    items = {i.item_code: i for i in parse_prices(gzip.compress(PRICES_XML.encode()))}
    assert set(items) == {"7290004131074", "2000123"}

    milk = items["7290004131074"]
    assert milk.price == Decimal("7.12")
    assert milk.manufacturer == "תנובה"
    assert milk.price_updated_at.utcoffset() is not None

    tomatoes = items["2000123"]
    assert tomatoes.is_weighted is True
    assert tomatoes.item_type == 0


def test_parse_promotions_computes_per_unit_price():
    xml = "<Root><Promotions>" + promo("1", "0", promo_item("111", "3", "10.00")) + "</Promotions></Root>"
    [record] = parse_promotions(xml.encode())
    assert record.min_qty == Decimal("3")
    assert record.effective_unit_price == Decimal("3.333")


def test_parse_promotions_weighted_price_is_per_kilo():
    xml = "<Root>" + promo("2", "0", promo_item("222", "0.010", "5.90")) + "</Root>"
    [record] = parse_promotions(xml.encode())
    assert record.effective_unit_price == Decimal("5.900")


def test_parse_promotions_skips_club_gift_and_threshold_deals():
    xml = "<Root>" + "".join([
        promo("3", "1 - מועדון", promo_item("333", "1", "5.00")),
        promo("4", "0 - כלל הלקוחות", promo_item("444", "1", "0.00")),
        promo("5", "0", promo_item("555", "1", "5.00"), min_purchase="99.00"),
        promo("6", "0 - כלל הלקוחות", promo_item("666", "2", "9.00")),
    ]) + "</Root>"
    assert [r.item_code for r in parse_promotions(xml.encode())] == ["666"]


def test_parse_promotions_skips_coupons_and_conditions_hidden_in_text():
    # All marked ClubID 0, yet none is a price every shopper gets.
    xml = "<Root>" + "".join([
        promo("7", "0", promo_item("777", "1", "2.90"), description="שמן קנולה 1לי ב2.90-אשראי"),
        promo("8", "0", promo_item("888", "1", "5.00"), coupon="1"),
        promo("9", "0", promo_item("999", "2", "9.00"), description="פסטה ב-50% מעל 100 מו2"),
        promo("10", "0", promo_item("1010", "1", "4.00"), description="קוטג' ב4 בקופון"),
        promo("11", "0", promo_item("1111", "3", "10.00"), description="במבה 3ב10"),
    ]) + "</Root>"
    assert [r.item_code for r in parse_promotions(xml.encode())] == ["1111"]
