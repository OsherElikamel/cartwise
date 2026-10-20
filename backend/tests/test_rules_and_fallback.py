import pytest

from app.ai.provider import get_llm
from app.ai.resilient import CircuitBreaker, ResilientProvider
from app.ai.rules import RuleBasedProvider, parse_line
from app.core.errors import UpstreamError
from app.main import app


@pytest.mark.parametrize("line, quantity, unit, first_term", [
    ("2 חלב 3%", 2, "unit", "חלב 3%"),
    ("חצי קילו עגבניות", 0.5, "kg", "עגבניות"),
    ("קילו בננות", 1, "kg", "בננות"),
    ("עגבניות 1.5 kg", 1.5, "kg", "עגבניות"),
    ("גבינה צהובה 200 גרם", 0.2, "kg", "גבינה צהובה"),
    ("שתי פחיות טונה", 2, "unit", "טונה"),
    ("במבה", 1, "unit", "במבה"),
])
def test_rule_parser_reads_quantities_and_units(line, quantity, unit, first_term):
    item = parse_line(line)
    assert (item.quantity, item.unit, item.search_terms[0]) == (quantity, unit, first_term)


def test_rule_parser_adds_simple_singular_forms():
    assert parse_line("עגבניות").search_terms == ["עגבניות", "עגבניה"]
    assert parse_line("מלפפונים").search_terms == ["מלפפונים", "מלפפון"]  # final ן restored
    assert parse_line("תפוחים").search_terms == ["תפוחים", "תפוח"]


def test_rule_provider_splits_lines_and_commas_and_skips_blanks():
    items = RuleBasedProvider().parse_list("חלב, ביצים\n\n במבה ")
    assert [i.search_terms[0] for i in items] == ["חלב", "ביצים", "במבה"]


class FailingAI:
    name = "failing"

    def __init__(self):
        self.calls = 0

    def parse_list(self, text):
        self.calls += 1
        raise UpstreamError("quota", "ai_busy")

    def choose_matches(self, items):
        self.calls += 1
        raise UpstreamError("quota", "ai_busy")


def test_resilient_provider_falls_back_and_trips_the_breaker():
    ai, circuit = FailingAI(), CircuitBreaker(cool_down=60)
    first = ResilientProvider(ai, circuit=circuit)
    assert [i.search_terms[0] for i in first.parse_list("במבה")] == ["במבה"]
    assert first.degraded and circuit.is_open

    # While the breaker is open, the AI isn't even tried: no waiting.
    second = ResilientProvider(ai, circuit=circuit)
    second.parse_list("חלב")
    assert ai.calls == 1 and second.degraded


def test_working_ai_is_not_degraded(fake_llm):
    provider = ResilientProvider(fake_llm, circuit=CircuitBreaker())
    provider.parse_list("במבה")
    assert not provider.degraded


@pytest.fixture
def ai_down():
    app.dependency_overrides[get_llm] = lambda: ResilientProvider(FailingAI(), circuit=CircuitBreaker(cool_down=60))
    yield
    app.dependency_overrides.pop(get_llm, None)


def test_compare_still_works_without_the_ai_and_says_so(client, catalog, ai_down):
    res = client.post("/api/baskets/compare", json={"text": "2 חלב 3%\nבמבה"})
    assert res.status_code == 200
    body = res.json()
    assert body["ai_available"] is False
    lines = [line for store in body["stores"] for line in store["lines"] if line["item_code"]]
    assert lines and all(line["confidence"] == "low" for line in lines)


def test_rule_based_reading_of_a_saved_list_is_not_cached(client, auth_headers, catalog, ai_down):
    weekly = client.post("/api/lists", json={"name": "Weekly", "text": "חלב 3%"}, headers=auth_headers).json()
    client.post(f"/api/lists/{weekly['id']}/compare", headers=auth_headers)
    assert client.get("/api/lists", headers=auth_headers).json()[0]["is_parsed"] is False
