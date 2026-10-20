import httpx
import pytest
from google.genai import errors as genai_errors

from app.ai.gemini import GeminiProvider
from app.core.errors import UpstreamError


class FakeResponse:
    text = '{"items": [{"original": "במבה", "search_terms": ["במבה"], "quantity": 1, "unit": "unit"}]}'


def quota_error():
    return genai_errors.APIError(429, {"error": {"code": 429, "message": "quota", "status": "RESOURCE_EXHAUSTED"}})


@pytest.fixture
def provider():
    return GeminiProvider(api_key="test", model="gemini-2.5-flash", fallback_model="gemini-3.5-flash-lite")


def stub(monkeypatch, provider, outcomes):
    """Each call pops the next outcome: an exception is raised, anything else returned."""
    calls = []

    def generate_content(*, model, contents, config):
        calls.append((model, config.thinking_config))
        outcome = outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setattr(provider.client.models, "generate_content", generate_content)
    return calls


def test_quota_error_falls_back_to_the_second_model(monkeypatch, provider):
    calls = stub(monkeypatch, provider, [quota_error(), FakeResponse()])
    items = provider.parse_list("במבה")
    assert [i.search_terms for i in items] == [["במבה"]]
    assert [model for model, _ in calls] == ["gemini-2.5-flash", "gemini-3.5-flash-lite"]


def test_each_model_generation_gets_its_own_thinking_setting(monkeypatch, provider):
    calls = stub(monkeypatch, provider, [quota_error(), FakeResponse()])
    provider.parse_list("במבה")
    (_, gemini2), (_, gemini3) = calls
    assert gemini2.thinking_budget == 0 and gemini2.thinking_level is None
    assert gemini3.thinking_level is not None and gemini3.thinking_budget is None


def test_quota_on_every_model_gives_a_friendly_error(monkeypatch, provider):
    stub(monkeypatch, provider, [quota_error(), quota_error()])
    with pytest.raises(UpstreamError, match="try again in a minute"):
        provider.parse_list("במבה")


def busy_error():
    return genai_errors.APIError(503, {"error": {"code": 503, "message": "busy", "status": "UNAVAILABLE"}})


def test_busy_is_retried_once_on_the_same_model(monkeypatch, provider):
    calls = stub(monkeypatch, provider, [busy_error(), FakeResponse()])
    provider.parse_list("במבה")
    assert [model for model, _ in calls] == ["gemini-2.5-flash", "gemini-2.5-flash"]


def test_timeout_is_never_retried(monkeypatch, provider):
    calls = stub(monkeypatch, provider, [httpx.ReadTimeout("slow"), FakeResponse()])
    with pytest.raises(UpstreamError) as exc:
        provider.parse_list("במבה")
    assert exc.value.code == "ai_timeout"
    assert len(calls) == 1


def test_each_attempt_gets_only_the_time_left(monkeypatch, provider):
    seen = []

    def generate_content(*, model, contents, config):
        seen.append(config.http_options.timeout)
        if len(seen) == 1:
            raise quota_error()
        return FakeResponse()

    monkeypatch.setattr(provider.client.models, "generate_content", generate_content)
    provider.parse_list("במבה")
    assert seen[0] <= provider.budget_seconds * 1000 and seen[1] <= seen[0]


def test_invalid_model_output_is_rejected(monkeypatch, provider):
    class Broken:
        text = '{"items": [{"original": "x", "search_terms": [], "quantity": -1, "unit": "box"}]}'

    stub(monkeypatch, provider, [Broken()])
    with pytest.raises(UpstreamError, match="unexpected answer"):
        provider.parse_list("x")
