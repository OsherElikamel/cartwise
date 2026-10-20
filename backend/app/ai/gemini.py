import json
import logging

from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from pydantic import ValidationError

from app.ai.prompts import MATCH_SYSTEM, PARSE_LIST_SYSTEM, match_user_prompt
from app.ai.schemas import MatchDecision, MatchDecisions, MatchRequestItem, ParsedItem, ParsedList
from app.core.errors import UpstreamError

logger = logging.getLogger(__name__)


class GeminiProvider:
    name = "gemini"

    # Measured on a 7-item list x 4 branches: default thinking took 67s for the
    # match call, a 1024-token budget 13s, none 7s, with the same picks.
    # Parsing is mechanical (no thinking); matching keeps a small budget for judgment.
    PARSE_THINKING_BUDGET = 0
    MATCH_THINKING_BUDGET = 1024

    def __init__(self, api_key: str, model: str, fallback_model: str | None = None) -> None:
        # 503 ("high demand") is temporary: back off and retry. 429 is not retried
        # here: the free tier's quota is per minute, so retrying the same model
        # only spends more of it. A 429 moves on to the fallback model instead,
        # which has its own quota.
        retry = types.HttpRetryOptions(
            attempts=4, initial_delay=1.0, max_delay=8.0, exp_base=2.0, jitter=0.5,
            http_status_codes=[500, 503, 504],
        )
        self.client = genai.Client(api_key=api_key, http_options=types.HttpOptions(retry_options=retry))
        self.models = [model] + ([fallback_model] if fallback_model and fallback_model != model else [])

    @staticmethod
    def _thinking(model: str, budget: int) -> types.ThinkingConfig:
        """Gemini 2.x takes a token budget; Gemini 3.x takes a level instead."""
        if model.startswith("gemini-2."):
            return types.ThinkingConfig(thinking_budget=budget)
        return types.ThinkingConfig(thinking_level=types.ThinkingLevel.MINIMAL if budget == 0 else types.ThinkingLevel.LOW)

    def _generate(self, system: str, prompt: str, schema: type, thinking_budget: int):
        for attempt, model in enumerate(self.models, start=1):
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
                    ),
                )
                break
            except genai_errors.APIError as exc:
                if exc.code == 429 and attempt < len(self.models):
                    logger.warning("Gemini quota hit on %s; falling back to %s", model, self.models[attempt])
                    continue
                logger.error("Gemini call failed on %s: %s", model, exc)
                if exc.code == 429:
                    raise UpstreamError("CartWise's free AI quota is busy. Please try again in a minute.") from exc
                raise UpstreamError("The AI service is unavailable right now. Please try again.") from exc

        # Validate with our own models: the schema guides the model, our code enforces it.
        try:
            return schema.model_validate_json(response.text or "")
        except ValidationError as exc:
            logger.error("Gemini output failed validation: %s | %.500s", exc, response.text)
            raise UpstreamError("The AI returned an unexpected answer. Please try again.") from exc

    def parse_list(self, text: str) -> list[ParsedItem]:
        return self._generate(PARSE_LIST_SYSTEM, text, ParsedList, self.PARSE_THINKING_BUDGET).items

    def choose_matches(self, items: list[MatchRequestItem]) -> list[MatchDecision]:
        payload = json.dumps([i.model_dump() for i in items], ensure_ascii=False)
        return self._generate(
            MATCH_SYSTEM, match_user_prompt(payload), MatchDecisions, self.MATCH_THINKING_BUDGET
        ).decisions
