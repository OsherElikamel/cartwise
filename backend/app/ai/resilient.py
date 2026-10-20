"""Try the AI, fall back to rules: CartWise keeps working when the AI doesn't.

A small circuit breaker sits in front of the AI. After a failure (quota used
up, timeout, outage) the AI is skipped for a cool-down period, so only the
first unlucky request waits; everyone after gets the rule-based answer at once.
"""

import logging
import threading
import time

from app.ai.provider import LLMProvider
from app.ai.rules import RuleBasedProvider
from app.ai.schemas import MatchDecision, MatchRequestItem, ParsedItem
from app.core.errors import UpstreamError

logger = logging.getLogger(__name__)

COOL_DOWN_SECONDS = 300


class CircuitBreaker:
    def __init__(self, cool_down: float = COOL_DOWN_SECONDS) -> None:
        self.cool_down = cool_down
        self._open_until = 0.0
        self._lock = threading.Lock()

    @property
    def is_open(self) -> bool:
        return time.monotonic() < self._open_until

    def trip(self) -> None:
        with self._lock:
            self._open_until = time.monotonic() + self.cool_down

    def reset(self) -> None:
        with self._lock:
            self._open_until = 0.0


breaker = CircuitBreaker()


class ResilientProvider:
    """One per request, so `degraded` describes this request only."""

    name = "resilient"

    def __init__(self, ai: LLMProvider, rules: RuleBasedProvider | None = None, circuit: CircuitBreaker = breaker) -> None:
        self.ai = ai
        self.rules = rules or RuleBasedProvider()
        self.circuit = circuit
        self.degraded = False

    def _call(self, ai_call, rules_call):
        if not self.circuit.is_open:
            try:
                return ai_call()
            except UpstreamError as exc:
                logger.warning("AI unavailable (%s); using rules for %ds", exc.code, self.circuit.cool_down)
                self.circuit.trip()
        self.degraded = True
        return rules_call()

    def parse_list(self, text: str) -> list[ParsedItem]:
        return self._call(lambda: self.ai.parse_list(text), lambda: self.rules.parse_list(text))

    def choose_matches(self, items: list[MatchRequestItem]) -> list[MatchDecision]:
        return self._call(lambda: self.ai.choose_matches(items), lambda: self.rules.choose_matches(items))
