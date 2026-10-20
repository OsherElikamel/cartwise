import os
import time

from app.core.config import settings
from app.ingestion.pipeline import prune_cache


def test_prune_cache_removes_only_old_files(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "DATA_DIR", str(tmp_path))
    chain_dir = tmp_path / "rami-levy"
    chain_dir.mkdir()
    old, fresh = chain_dir / "PriceFull-old.gz", chain_dir / "PriceFull-new.gz"
    old.write_bytes(b"x")
    fresh.write_bytes(b"x")
    four_days_ago = time.time() - 4 * 86400
    os.utime(old, (four_days_ago, four_days_ago))

    assert prune_cache(3) == 1
    assert not old.exists() and fresh.exists()


def test_prune_cache_without_a_cache_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "DATA_DIR", str(tmp_path / "missing"))
    assert prune_cache(3) == 0


def test_baskets_say_when_prices_were_loaded(client, catalog, fake_llm):
    body = client.post("/api/baskets/compare", json={"text": "חלב 3%"}).json()
    assert all(s["prices_updated_at"] for s in body["stores"])
