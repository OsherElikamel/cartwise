import json
import logging
import time

import httpx
from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from pydantic import ValidationError

from app.ai.prompts import MATCH_SYSTEM, PARSE_LIST_SYSTEM, match_user_prompt
from app.ai.schemas import MatchDecision, MatchDecisions, MatchRequestItem, ParsedItem, ParsedList
from app.core.errors import UpstreamError

logger = logging.getLogger(__name__)

RETRYABLE_STATUS = {500, 503, 504}


class GeminiProvider:
    name = "gemini"

    # Measured on a 7-item list x 4 branches: default thinking took 67s for the
    # match call, a 1024-token budget 13s, none 7s, with the same picks.
    # Parsing is mechanical (no thinking); matching keeps a small budget for judgment.
    PARSE_THINKING_BUDGET = 0
    MATCH_THINKING_BUDGET = 1024

    def __init__(self, api_key: str, model: str, fallback_model: str | None = None, timeout_seconds: float = 20) -> None:
        # SDK retries are off: they also retry timeouts, which multiplied a 20s
        # limit into an 88s wait. The policy lives in _generate instead, against
        # one time budget per call: a 503 ("busy") gets one quick retry; a 429
        # (quota) moves to the fallback model, which has its own quota; a
        # timeout gives up at once, because asking a slow model again only
        # doubles the wait.
        self.client = genai.Client(api_key=api_key, http_options=types.HttpOptions(retry_options=types.HttpRetryOptions(attempts=1)))
        self.models = [model] + ([fallback_model] if fallback_model and fallback_model != model else [])
        self.budget_seconds = timeout_seconds

    @staticmethod
    def _thinking(model: str, budget: int) -> types.ThinkingConfig:
        """Gemini 2.x takes a token budget; Gemini 3.x takes a level instead."""
        if model.startswith("gemini-2."):
            return types.ThinkingConfig(thinking_budget=budget)
        return types.ThinkingConfig(thinking_level=types.ThinkingLevel.MINIMAL if budget == 0 else types.ThinkingLevel.LOW)

    def _generate(self, system: str, prompt: str, schema: type, thinking_budget: int):
        deadline = time.monotonic() + self.budget_seconds
        index, retried_busy = 0, False
        while True:
            model = self.models[index]
            remaining = deadline - time.monotonic()
            if remaining < 1:
                raise UpstreamError("The AI took too long to answer.", "ai_timeout")
            try:
                response = self.client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system,
                        response_mime_type="application/json",
                        response_json_schema=schema.model_json_schema(),
                        temperature=0,
                        thinking_config=self._thinking(model, thinking_budget),
                        http_options=types.HttpOptions(timeout=int(remaining * 1000)),
                    ),
                )
                break
            except genai_errors.APIError as exc:
                if exc.code in RETRYABLE_STATUS and not retried_busy:
                    retried_busy = True
                    logger.warning("Gemini busy (%s) on %s; retrying once", exc.code, model)
                    time.sleep(1)
                    continue
                if exc.code == 429 and index + 1 < len(self.models):
                    logger.warning("Gemini quota hit on %s; falling back to %s", model, self.models[index + 1])
                    index += 1
                    continue
                logger.error("Gemini call failed on %s: %s", model, exc)
                if exc.code == 429:
                    raise UpstreamError("CartWise's free AI quota is busy. Please try again in a minute.", "ai_busy") from exc
                raise UpstreamError("The AI service is unavailable right now. Please try again.", "ai_unavailable") from exc
            except httpx.TimeoutException as exc:
                logger.error("Gemini call timed out on %s", model)
                raise UpstreamError("The AI took too long to answer.", "ai_timeout") from exc

        # Validate with our own models: the schema guides the model, our code enforces it.
        try:
            return schema.model_validate_json(response.text or "")
        except ValidationError as exc:
            logger.error("Gemini output failed validation: %s | %.500s", exc, response.text)
            raise UpstreamError("The AI returned an unexpected answer. Please try again.", "ai_bad_answer") from exc

    def parse_list(self, text: str) -> list[ParsedItem]:
        return self._generate(PARSE_LIST_SYSTEM, text, ParsedList, self.PARSE_THINKING_BUDGET).items

    def choose_matches(self, items: list[MatchRequestItem]) -> list[MatchDecision]:
        payload = json.dumps([i.model_dump() for i in items], ensure_ascii=False)
        return self._generate(
            MATCH_SYSTEM, match_user_prompt(payload), MatchDecisions, self.MATCH_THINKING_BUDGET
        ).decisions
