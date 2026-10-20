from decimal import Decimal


def compare(client, text, headers=None, store_ids=None):
    body = {"text": text}
    if store_ids is not None:
        body["store_ids"] = [str(s) for s in store_ids]
    return client.post("/api/baskets/compare", json=body, headers=headers or {})


def by_chain(result):
    return {s["chain_slug"]: s for s in result["stores"]}


def test_guest_compares_on_demo_branches_ranked_by_shared_items(client, catalog, fake_llm):
    res = compare(client, "2 חלב 3%\nבמבה")
    assert res.status_code == 200
    body = res.json()

    # Bamba exists only at Rami Levy, so the ranking uses milk alone.
    assert body["shared_items"] == [0]
    stores = by_chain(body)
    assert stores["shufersal"]["missing"] == [1]
    assert Decimal(stores["rami-levy"]["shared_total"]) == Decimal("12.40")
    assert Decimal(stores["shufersal"]["shared_total"]) == Decimal("14.70")
    assert body["stores"][0]["chain_slug"] == "rami-levy"
    assert Decimal(body["savings_vs_most_expensive"]) == Decimal("2.30")


def test_missing_item_does_not_make_a_branch_look_cheaper(client, catalog, fake_llm):
    body = compare(client, "חלב 3%\nבמבה").json()
    stores = by_chain(body)
    # Shufersal's full total is lower only because it lacks Bamba.
    assert Decimal(stores["shufersal"]["full_total"]) < Decimal(stores["rami-levy"]["full_total"])
    assert body["stores"][0]["chain_slug"] == "rami-levy"


def test_multi_buy_deal_applies_to_full_groups(client, catalog, fake_llm):
    body = compare(client, "4 במבה").json()
    line = by_chain(body)["rami-levy"]["lines"][0]
    # 3 for 10 + one at the regular 4.50
    assert Decimal(line["line_total"]) == Decimal("14.50")
    assert line["deal"] == "במבה 3ב10"


def test_weighted_item_is_priced_per_kilo(client, catalog, fake_llm):
    body = compare(client, "0.5 עגבניה kg").json()
    assert Decimal(by_chain(body)["shufersal"]["lines"][0]["line_total"]) == Decimal("3.95")


def test_codes_the_llm_invents_are_discarded(client, catalog, fake_llm):
    fake_llm.bogus_codes_for = {"shufersal"}
    body = compare(client, "חלב 3%").json()
    assert by_chain(body)["shufersal"]["missing"] == [0]


def test_guest_cannot_compare_on_other_branches(client, catalog, fake_llm):
    res = compare(client, "חלב 3%", store_ids=[catalog["rami_levy_other"].id])
    assert res.status_code == 400


def test_signed_in_user_compares_on_followed_branches(client, auth_headers, catalog, fake_llm):
    client.post("/api/me/stores", json={"store_id": str(catalog["rami_levy"].id)}, headers=auth_headers)
    body = compare(client, "חלב 3%", headers=auth_headers).json()
    assert [s["chain_slug"] for s in body["stores"]] == ["rami-levy"]


def test_empty_list_is_rejected(client, catalog, fake_llm):
    assert compare(client, "  \n ").status_code == 400


def picks_from(body):
    return [
        {"store_id": s["store_id"], "index": line["index"], "item_code": line["item_code"],
         "confidence": line["confidence"], "reason": line["reason"]}
        for s in body["stores"] for line in s["lines"] if line["item_code"]
    ]


def test_reprice_applies_a_swap_without_any_ai_call(client, catalog, fake_llm):
    body = compare(client, "חלב 3%").json()
    calls = (fake_llm.parse_calls, fake_llm.match_calls)
    picks = picks_from(body)
    shufersal = next(s for s in body["stores"] if s["chain_slug"] == "shufersal")
    swap_to = shufersal["lines"][0]["alternatives"][0]
    for p in picks:
        if p["store_id"] == shufersal["store_id"]:
            p.update(item_code=swap_to["item_code"], confidence="high", reason="You chose this")

    res = client.post("/api/baskets/reprice", json={
        "items": body["items"], "store_ids": [s["store_id"] for s in body["stores"]], "picks": picks,
    })
    assert res.status_code == 200
    stores = by_chain(res.json())
    assert stores["shufersal"]["lines"][0]["item_code"] == swap_to["item_code"]
    assert Decimal(stores["shufersal"]["shared_total"]) == Decimal(swap_to["price"])
    assert (fake_llm.parse_calls, fake_llm.match_calls) == calls


def test_reprice_ignores_products_not_sold_at_the_branch(client, catalog, fake_llm):
    body = compare(client, "חלב 3%").json()
    picks = picks_from(body)
    for p in picks:
        p["item_code"] = "9999999999999"
    res = client.post("/api/baskets/reprice", json={
        "items": body["items"], "store_ids": [s["store_id"] for s in body["stores"]], "picks": picks,
    })
    assert all(s["missing"] == [0] for s in res.json()["stores"])


def test_guest_cannot_reprice_on_other_branches(client, catalog, fake_llm):
    body = compare(client, "חלב 3%").json()
    res = client.post("/api/baskets/reprice", json={
        "items": body["items"], "store_ids": [str(catalog["rami_levy_other"].id)], "picks": [],
    })
    assert res.status_code == 400


def reprice_one(client, catalog, item, store_key, item_code):
    store_id = str(catalog[store_key].id)
    res = client.post("/api/baskets/reprice", json={
        "items": [item], "store_ids": [store_id],
        "picks": [{"store_id": store_id, "index": 0, "item_code": item_code, "confidence": "high", "reason": "test"}],
    })
    assert res.status_code == 200
    return res.json()["stores"][0]["lines"][0]


def test_counted_item_sold_by_weight_is_priced_at_its_estimated_weight(client, catalog):
    # "a watermelon": 1 unit of about 8 kg, sold per kilo
    item = {"original": "אבטיח", "search_terms": ["אבטיח"], "quantity": 1, "unit": "unit", "unit_weight_kg": 8}
    line = reprice_one(client, catalog, item, "shufersal", "2000001")  # עגבניה, 7.90 per kg, weighted
    assert Decimal(line["line_total"]) == Decimal("63.20")
    assert Decimal(line["estimated_kg"]) == Decimal("8")


def test_several_counted_items_multiply_the_estimate(client, catalog):
    item = {"original": "6 תפוחים", "search_terms": ["תפוח"], "quantity": 6, "unit": "unit", "unit_weight_kg": 0.2}
    line = reprice_one(client, catalog, item, "shufersal", "2000001")
    assert Decimal(line["line_total"]) == Decimal("9.48")  # 1.2 kg x 7.90
    assert Decimal(line["estimated_kg"]) == Decimal("1.2")


def test_item_asked_by_weight_is_not_an_estimate(client, catalog):
    item = {"original": "חצי קילו עגבניות", "search_terms": ["עגבניה"], "quantity": 0.5, "unit": "kg"}
    line = reprice_one(client, catalog, item, "shufersal", "2000001")
    assert Decimal(line["line_total"]) == Decimal("3.95")
    assert line["estimated_kg"] is None


def test_counted_item_sold_per_unit_is_simply_counted(client, catalog):
    item = {"original": "2 חלב", "search_terms": ["חלב"], "quantity": 2, "unit": "unit", "unit_weight_kg": 1}
    line = reprice_one(client, catalog, item, "shufersal", "7290004131074")  # packaged, not weighted
    assert Decimal(line["line_total"]) == Decimal("14.70")
    assert line["estimated_kg"] is None
