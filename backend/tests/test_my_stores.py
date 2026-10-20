import pytest

from app.core.config import settings
from app.routers import me as me_router


@pytest.fixture
def loads(monkeypatch):
    """Record background price loads instead of downloading real files."""
    calls = []
    monkeypatch.setattr(me_router, "sync_store_prices_by_id", lambda store_id: calls.append(store_id))
    return calls


def test_following_an_untracked_branch_starts_loading_it(client, auth_headers, catalog, loads, db):
    other = catalog["rami_levy_other"]
    res = client.post("/api/me/stores", json={"store_id": str(other.id)}, headers=auth_headers)

    assert res.status_code == 202
    assert res.json()["is_ready"] is False
    assert loads == [other.id]
    db.refresh(other)
    assert other.is_tracked is True


def test_following_a_loaded_branch_returns_200_without_loading(client, auth_headers, catalog, loads):
    store = catalog["rami_levy"]
    res = client.post("/api/me/stores", json={"store_id": str(store.id)}, headers=auth_headers)
    assert res.status_code == 200
    assert loads == []


def test_one_branch_per_chain(client, auth_headers, catalog, loads):
    client.post("/api/me/stores", json={"store_id": str(catalog["rami_levy"].id)}, headers=auth_headers)
    client.post("/api/me/stores", json={"store_id": str(catalog["rami_levy_other"].id)}, headers=auth_headers)

    mine = client.get("/api/me/stores", headers=auth_headers).json()
    assert [s["store_code"] for s in mine] == ["1"]


def test_branch_cap_blocks_new_branches(client, auth_headers, catalog, loads, monkeypatch):
    monkeypatch.setattr(settings, "MAX_TRACKED_STORES", 2)
    res = client.post("/api/me/stores", json={"store_id": str(catalog["rami_levy_other"].id)}, headers=auth_headers)
    assert res.status_code == 409
    assert loads == []


def test_unfollow(client, auth_headers, catalog, loads):
    store_id = str(catalog["shufersal"].id)
    client.post("/api/me/stores", json={"store_id": store_id}, headers=auth_headers)
    assert client.delete(f"/api/me/stores/{store_id}", headers=auth_headers).status_code == 204
    assert client.delete(f"/api/me/stores/{store_id}", headers=auth_headers).status_code == 404


def test_my_stores_requires_sign_in(client):
    assert client.get("/api/me/stores").status_code == 401
