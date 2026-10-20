from tests.conftest import register_and_login


def follow_demo_branches(client, headers, catalog):
    for key in ("shufersal", "rami_levy"):
        client.post("/api/me/stores", json={"store_id": str(catalog[key].id)}, headers=headers)


def create_list(client, headers, text="2 חלב 3%\nבמבה"):
    return client.post("/api/lists", json={"name": "Weekly", "text": text}, headers=headers).json()


def test_repeat_run_of_a_saved_list_needs_no_ai_calls(client, auth_headers, catalog, fake_llm):
    follow_demo_branches(client, auth_headers, catalog)
    weekly = create_list(client, auth_headers)
    assert weekly["is_parsed"] is False

    first = client.post(f"/api/lists/{weekly['id']}/compare", headers=auth_headers)
    assert first.status_code == 200
    calls = (fake_llm.parse_calls, fake_llm.match_calls)
    assert calls == (1, 1)

    second = client.post(f"/api/lists/{weekly['id']}/compare", headers=auth_headers).json()
    assert (fake_llm.parse_calls, fake_llm.match_calls) == calls  # zero new AI calls
    assert second["ai_matches"] == 0
    assert second["stores"][0]["chain_slug"] == "rami-levy"


def test_editing_the_text_reparses_the_list(client, auth_headers, catalog, fake_llm):
    weekly = create_list(client, auth_headers)
    client.post(f"/api/lists/{weekly['id']}/compare", headers=auth_headers)

    renamed = client.patch(f"/api/lists/{weekly['id']}", json={"name": "Friday"}, headers=auth_headers).json()
    assert renamed["is_parsed"] is True  # a rename keeps the cached reading

    edited = client.patch(f"/api/lists/{weekly['id']}", json={"text": "חלב 3%"}, headers=auth_headers).json()
    assert edited["is_parsed"] is False
    body = client.post(f"/api/lists/{weekly['id']}/compare", headers=auth_headers).json()
    assert [i["original"] for i in body["items"]] == ["חלב 3%"]
    assert fake_llm.parse_calls == 2


def test_lists_are_private(client, auth_headers, catalog, fake_llm):
    weekly = create_list(client, auth_headers)
    other = register_and_login(client, "other@example.com")
    assert client.post(f"/api/lists/{weekly['id']}/compare", headers=other).status_code == 404
    assert client.delete(f"/api/lists/{weekly['id']}", headers=other).status_code == 404
    assert client.get("/api/lists", headers=other).json() == []


def test_history_records_signed_in_comparisons_only(client, auth_headers, catalog, fake_llm):
    weekly = create_list(client, auth_headers)
    client.post(f"/api/lists/{weekly['id']}/compare", headers=auth_headers)
    client.post("/api/baskets/compare", json={"text": "במבה"}, headers=auth_headers)
    client.post("/api/baskets/compare", json={"text": "במבה"})  # guest: not recorded

    runs = client.get("/api/history", headers=auth_headers).json()
    assert [r["list_name"] for r in runs] == [None, "Weekly"]  # newest first
    assert runs[1]["cheapest_chain"] == "Rami Levy"

    detail = client.get(f"/api/history/{runs[1]['id']}", headers=auth_headers).json()
    assert len(detail["result"]["items"]) == 2


def test_history_is_private(client, auth_headers, catalog, fake_llm):
    client.post("/api/baskets/compare", json={"text": "במבה"}, headers=auth_headers)
    run_id = client.get("/api/history", headers=auth_headers).json()[0]["id"]
    other = register_and_login(client, "other@example.com")
    assert client.get(f"/api/history/{run_id}", headers=other).status_code == 404
