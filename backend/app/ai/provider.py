"""The LLM behind an interface: one adapter per provider, chosen by LLM_PROVIDER."""

from functools import lru_cache
from typing import Protocol

from app.ai.schemas import MatchDecision, MatchRequestItem, ParsedItem
from app.core.config import settings


class LLMProvider(Protocol):
    name: str

    def parse_list(self, text: str) -> list[ParsedItem]: ...

    def choose_matches(self, items: list[MatchRequestItem]) -> list[MatchDecision]: ...


@lru_cache
def get_llm() -> LLMProvider:
    if settings.LLM_PROVIDER == "gemini":
        from app.ai.gemini import GeminiProvider

        return GeminiProvider(api_key=settings.GEMINI_API_KEY, model=settings.GEMINI_MODEL)
    raise ValueError(f"Unsupported LLM_PROVIDER: {settings.LLM_PROVIDER}")
