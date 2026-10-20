import os
from datetime import datetime, timezone
from decimal import Decimal

# Settings are read at import time: configure the test environment first.
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
os.environ.setdefault("LLM_PROVIDER", "gemini")
os.environ.setdefault("GEMINI_API_KEY", "test-key-never-used")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-that-is-at-least-32-bytes")
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://cartwise_user:cartwise_password@localhost:5433/cartwise_test")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.ai.provider import get_llm  # noqa: E402
from app.ai.schemas import MatchDecision, MatchRequestItem, ParsedItem  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.database import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.chain import Chain, Store  # noqa: E402
from app.routers import me as me_router  # noqa: E402
from app.models.promotion import Promotion  # noqa: E402
from app.models.store_item import StoreItem  # noqa: E402

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://cartwise_user:cartwise_password@localhost:5433/cartwise_test",
)

engine = create_engine(TEST_DATABASE_URL)
TestingSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class FakeLLM:
    """Deterministic stand-in for the real provider: no network, no cost.

    parse_list: one item per line; "2 x" means quantity 2, a trailing "kg" means by weight.
    choose_matches: the first candidate per chain, unless a chain is listed in
    `bogus_codes_for`, in which case it returns a code that was never offered.
    """

    name = "fake"

    def __init__(self) -> None:
        self.bogus_codes_for: set[str] = set()
        self.confidence = "high"
        self.parse_calls = 0
        self.match_calls = 0

    def parse_list(self, text_: str) -> list[ParsedItem]:
        self.parse_calls += 1
        items = []
        for line in filter(None, (raw.strip() for raw in text_.splitlines())):
            words = line.split()
            quantity = float(words.pop(0)) if words[0].replace(".", "").isdigit() else 1.0
            unit = "kg" if words[-1] == "kg" else "unit"
            if unit == "kg":
                words.pop()
            items.append(ParsedItem(original=line, search_terms=[" ".join(words)], quantity=quantity, unit=unit))
        return items

    def choose_matches(self, items: list[MatchRequestItem]) -> list[MatchDecision]:
        self.match_calls += 1
        decisions = []
        for item in items:
            for chain, candidates in item.candidates_by_chain.items():
                code = "0000000000000" if chain in self.bogus_codes_for else candidates[0].item_code
                decisions.append(MatchDecision(index=item.index, chain=chain, item_code=code, confidence=self.confidence, reason="test"))
        return decisions


def _override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture(scope="session", autouse=True)
def _create_tables():
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def _clean_tables():
    yield
    with engine.connect() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(text(f'TRUNCATE TABLE "{table.name}" CASCADE'))
        conn.commit()


@pytest.fixture(autouse=True)
def _no_network_price_loads(monkeypatch):
    """No test may download real chain files: background loads become no-ops.

    Tests that care about loads (test_my_stores) replace this with a recorder.
    """
    monkeypatch.setattr(me_router, "sync_store_prices_by_id", lambda store_id: None)


@pytest.fixture
def fake_llm():
    llm = FakeLLM()
    app.dependency_overrides[get_llm] = lambda: llm
    yield llm
    app.dependency_overrides.pop(get_llm, None)


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db():
    session = TestingSession()
    yield session
    session.close()


def register_and_login(client, email="shopper@example.com") -> dict:
    client.post("/api/auth/register", json={"name": "Shopper", "email": email, "password": "cartwise123"})
    res = client.post("/api/auth/login", json={"email": email, "password": "cartwise123"})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


@pytest.fixture
def auth_headers(client):
    return register_and_login(client)


@pytest.fixture
def catalog(db):
    """Two chains with one demo branch each and a third, untracked branch.

    Milk is at both demo branches; Bamba only at Rami Levy (which also has a
    "3 for 10" deal on it); loose tomatoes are weighted at both.
    """
    shufersal = Chain(slug="shufersal", chain_code="7290027600007", name="Shufersal", name_he="שופרסל")
    rami = Chain(slug="rami-levy", chain_code="7290058140886", name="Rami Levy", name_he="רמי לוי")
    db.add_all([shufersal, rami])
    db.flush()

    loaded = datetime.now(timezone.utc)
    sh_demo = Store(chain_id=shufersal.id, store_code="92", name="דיל אשדוד", is_tracked=True, is_demo=True, prices_synced_at=loaded)
    rl_demo = Store(chain_id=rami.id, store_code="709", name="שבט לוי אשדוד", is_tracked=True, is_demo=True, prices_synced_at=loaded)
    rl_other = Store(chain_id=rami.id, store_code="1", name="תלפיות")
    db.add_all([sh_demo, rl_demo, rl_other])
    db.flush()

    def item(store, code, name, price, weighted=False):
        return StoreItem(store_id=store.id, item_code=code, name=name, price=Decimal(price), is_weighted=weighted)

    db.add_all([
        item(sh_demo, "7290004131074", "חלב 3% תנובה 1 ליטר", "7.35"),
        item(sh_demo, "7290004131081", "חלב 3% תנובה 2 ליטר", "13.90"),
        item(rl_demo, "7290004131074", "חלב 3% תנובה 1 ליטר", "6.20"),
        item(rl_demo, "7290000066318", "במבה 80 גרם", "4.50"),
        item(sh_demo, "2000001", "עגבניה", "7.90", weighted=True),
        item(rl_demo, "2000002", "עגבניה", "8.90", weighted=True),
    ])
    db.add(Promotion(
        store_id=rl_demo.id, promotion_id="P1", item_code="7290000066318", description="במבה 3ב10",
        min_qty=Decimal(3), discounted_price=Decimal("10.00"), effective_unit_price=Decimal("3.333"),
    ))
    db.commit()
    return {"shufersal": sh_demo, "rami_levy": rl_demo, "rami_levy_other": rl_other}
