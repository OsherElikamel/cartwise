from sqlalchemy import delete

from app.models.store_item import StoreItem


def follow_demo_branches(client, headers, catalog):
    for key in ("shufersal", "rami_levy"):
        client.post("/api/me/stores", json={"store_id": str(catalog[key].id)}, headers=headers)


def compare(client, text, headers=None):
    return client.post("/api/baskets/compare", json={"text": text}, headers=headers or {}).json()


def line(body, chain, index=0):
    return next(s for s in body["stores"] if s["chain_slug"] == chain)["lines"][index]


def test_confident_picks_are_remembered_and_skip_the_ai_next_time(client, auth_headers, catalog, fake_llm):
    follow_demo_branches(client, auth_headers, catalog)
    first = compare(client, "2 חלב 3%", auth_headers)
    assert (first["ai_matches"], first["remembered_matches"]) == (2, 0)

    # Different quantity, same item: served from memory, no AI matching call.
    calls_before = fake_llm.match_calls
    second = compare(client, "3 חלב 3%", auth_headers)
    assert (second["ai_matches"], second["remembered_matches"]) == (0, 2)
    assert fake_llm.match_calls == calls_before
    assert line(second, "shufersal")["confidence"] == "remembered"


def test_unsure_picks_are_not_remembered(client, auth_headers, catalog, fake_llm):
    follow_demo_branches(client, auth_headers, catalog)
    fake_llm.confidence = "low"
    compare(client, "חלב 3%", auth_headers)
    assert client.get("/api/matches", headers=auth_headers).json() == []


def test_swapping_a_product_is_used_on_the_next_list(client, auth_headers, catalog, fake_llm):
    follow_demo_branches(client, auth_headers, catalog)
    body = compare(client, "חלב 3%", auth_headers)
    shufersal_line = line(body, "shufersal")
    swap = shufersal_line["alternatives"][0]
    assert swap["name"] == "חלב 3% תנובה 2 ליטר"

    res = client.put("/api/matches", headers=auth_headers, json={
        "match_key": shufersal_line["match_key"], "store_id": str(catalog["shufersal"].id), "item_code": swap["item_code"],
    })
    assert res.status_code == 200

    again = line(compare(client, "חלב 3%", auth_headers), "shufersal")
    assert (again["item_code"], again["confidence"]) == (swap["item_code"], "remembered")


def test_remembered_product_no_longer_sold_falls_back_to_the_ai(client, auth_headers, catalog, fake_llm, db):
    follow_demo_branches(client, auth_headers, catalog)
    compare(client, "במבה", auth_headers)
    db.execute(delete(StoreItem).where(StoreItem.item_code == "7290000066318"))
    db.commit()

    body = compare(client, "במבה", auth_headers)
    assert body["remembered_matches"] == 0


def test_choice_must_be_sold_at_the_branch(client, auth_headers, catalog, fake_llm):
    res = client.put("/api/matches", headers=auth_headers, json={
        "match_key": "במבה||", "store_id": str(catalog["shufersal"].id), "item_code": "7290000066318",
    })
    assert res.status_code == 404


def test_guests_never_get_memory(client, catalog, fake_llm):
    compare(client, "חלב 3%")
    body = compare(client, "חלב 3%")
    assert body["remembered_matches"] == 0


def test_forget_a_match(client, auth_headers, catalog, fake_llm):
    follow_demo_branches(client, auth_headers, catalog)
    compare(client, "חלב 3%", auth_headers)
    saved = client.get("/api/matches", headers=auth_headers).json()
    assert len(saved) == 2
    assert client.delete(f"/api/matches/{saved[0]['id']}", headers=auth_headers).status_code == 204
    assert len(client.get("/api/matches", headers=auth_headers).json()) == 1
