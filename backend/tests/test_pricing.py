from decimal import Decimal as D

from app.services.pricing import price_line


def test_packaged_item_without_deal():
    assert price_line(D(2), False, D("7.20")).total == D("14.40")


def test_packaged_quantity_rounds_up_to_whole_packages():
    # "half a kilo" of a 1 kg bag still means buying one bag
    assert price_line(D("0.5"), False, D("9.90")).total == D("9.90")


def test_weighted_item_is_priced_per_kilo():
    assert price_line(D("0.5"), True, D("6.90")).total == D("3.45")


def test_single_item_deal_applies_to_every_unit():
    line = price_line(D(2), False, D("12.90"), deal_min_qty=D(1), deal_unit_price=D("9.90"))
    assert (line.total, line.deal_applied) == (D("19.80"), True)


def test_multi_buy_applies_to_full_groups_only():
    # 3 for 10, buying 4: one group at 10.00 + one at the regular 4.50
    line = price_line(D(4), False, D("4.50"), deal_min_qty=D(3), deal_unit_price=D("3.333"))
    assert (line.total, line.deal_applied) == (D("14.50"), True)


def test_multi_buy_not_reached_charges_regular_price():
    line = price_line(D(2), False, D("4.50"), deal_min_qty=D(3), deal_unit_price=D("3.333"))
    assert (line.total, line.deal_applied) == (D("9.00"), False)


def test_weighted_deal_is_per_kilo():
    line = price_line(D("1.5"), True, D("7.90"), deal_min_qty=D("0.010"), deal_unit_price=D("4.90"))
    assert line.total == D("7.35")


def test_deal_that_is_not_cheaper_is_ignored():
    line = price_line(D(1), False, D("5.00"), deal_min_qty=D(1), deal_unit_price=D("5.50"))
    assert (line.total, line.deal_applied) == (D("5.00"), False)
