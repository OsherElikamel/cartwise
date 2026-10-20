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
