from decimal import Decimal

from app.db.database import engine
from app.models.store_item import StoreItem
from app.services.catalog_service import search_products


def test_database_pool_tests_connections_before_use():
    # The hosted database drops connections when it scales to zero.
    assert engine.pool._pre_ping is True


def test_weighted_preference_never_beats_a_strong_match(db, catalog):
    store = catalog["rami_levy"]
    db.add_all([
        StoreItem(store_id=store.id, item_code="501", name="פרגיות עוף קפוא 1 קג", price=Decimal("49.90"), is_weighted=False),
        StoreItem(store_id=store.id, item_code="502", name="פרגיות", price=Decimal("1.00"), is_weighted=False),
        StoreItem(store_id=store.id, item_code="503", name="עוף שלם טרי", price=Decimal("19.90"), is_weighted=True),
    ])
    db.commit()
    # "3 קילו פרגיות": bought by the kilo, but only "פרגיות" products really match.
    results = search_products(db, ["פרגיות"], [store.id], 5, prefer_weighted=True)
    assert results[0].name.startswith("פרגיות")


def test_browser_crashes_are_accepted_for_logging(client):
    res = client.post("/api/client-errors", json={"message": "TypeError: x is undefined", "stack": "at Foo", "url": "/branches"})
    assert res.status_code == 204
