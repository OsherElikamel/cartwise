"""A no-AI provider: reads the list with plain rules and leaves every product
choice for the user to check.

Used when the AI is out of quota, slow, or failing. It is deliberately humble:
quantities and simple Hebrew forms are handled, nothing is guessed silently,
and every pick comes back with confidence "low" ("Check this").
"""

import re

from app.ai.schemas import MatchDecision, MatchRequestItem, ParsedItem

PACKAGING = {"פחית", "פחיות", "קופסה", "קופסת", "קופסאות", "שקית", "שקיות", "בקבוק", "בקבוקי", "חבילה", "חבילת"}
NUMBER_WORDS = {"אחד": 1, "אחת": 1, "שני": 2, "שתי": 2, "שניים": 2, "שתיים": 2, "שלוש": 3, "שלושה": 3,
                "ארבע": 4, "ארבעה": 4, "חמש": 5, "חמישה": 5, "שש": 6, "שישה": 6}
LEADING_NUMBER = re.compile(r"^(\d+(?:[.,]\d+)?)\s*(?:x|×)?\s*")
TRAILING_KG = re.compile(r"\s*(\d+(?:[.,]\d+)?)?\s*(?:kg|ק\"ג|ק״ג|קילו)\s*$", re.IGNORECASE)
TRAILING_GRAMS = re.compile(r"\s*(\d+)\s*(?:g|גרם|גר)\s*$", re.IGNORECASE)


# Hebrew letters take a final form at the end of a word.
FINAL_FORMS = str.maketrans({"כ": "ך", "מ": "ם", "נ": "ן", "פ": "ף", "צ": "ץ"})


def _final(word: str) -> str:
    return word[:-1] + word[-1].translate(FINAL_FORMS) if word else word


def _variants(term: str) -> list[str]:
    """The term plus a simple singular form: labels often use the singular for
    loose produce ("עגבניות" -> "עגבניה", "מלפפונים" -> "מלפפון", with the
    final ן restored)."""
    words = term.split()
    last = words[-1] if words else ""
    singular = None
    if last.endswith("ות") and len(last) > 4:
        singular = last[:-2] + "ה"
    elif last.endswith("ים") and len(last) > 4:
        singular = _final(last[:-2])
    variants = [term]
    if singular:
        variants.append(" ".join(words[:-1] + [singular]))
    return variants


def parse_line(line: str) -> ParsedItem | None:
    text = " ".join(line.split())
    if not text:
        return None
    quantity, unit = 1.0, "unit"

    if text.startswith("חצי קילו "):
        quantity, unit, text = 0.5, "kg", text[len("חצי קילו "):]
    elif text.startswith("קילו "):
        quantity, unit, text = 1.0, "kg", text[len("קילו "):]
    elif match := LEADING_NUMBER.match(text):
        quantity, text = float(match.group(1).replace(",", ".")), text[match.end():]
    elif (first := text.split()[0]) in NUMBER_WORDS:
        quantity, text = float(NUMBER_WORDS[first]), text[len(first):].strip()

    if match := TRAILING_KG.search(text):
        unit = "kg"
        if match.group(1):
            quantity = float(match.group(1).replace(",", "."))
        text = text[:match.start()]
    elif match := TRAILING_GRAMS.search(text):
        unit, quantity, text = "kg", int(match.group(1)) / 1000, text[:match.start()]

    words = [w for w in text.split() if w not in PACKAGING]
    term = " ".join(words).strip()
    if not term or quantity <= 0:
        return None
    return ParsedItem(original=line.strip(), search_terms=_variants(term)[:3], quantity=quantity, unit=unit)


class RuleBasedProvider:
    name = "rules"

    def parse_list(self, text: str) -> list[ParsedItem]:
        lines = re.split(r"[\n,]", text)
        return [item for item in (parse_line(line) for line in lines) if item]

    def choose_matches(self, items: list[MatchRequestItem]) -> list[MatchDecision]:
        """The best text-search candidate per item and chain, always to be checked."""
        return [
            MatchDecision(index=item.index, chain=chain, item_code=candidates[0].item_code,
                          confidence="low", reason="Picked by text search; the AI was unavailable")
            for item in items
            for chain, candidates in item.candidates_by_chain.items()
            if candidates
        ]
