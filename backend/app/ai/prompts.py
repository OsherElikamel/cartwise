"""Prompts shared by every provider, so switching models never changes behavior."""

PARSE_LIST_SYSTEM = """You turn an Israeli shopper's grocery list into structured items.

The list may be Hebrew, English or mixed, one item per line or comma-separated,
with quantities written as digits or words ("2", "שתי", "קילו", "חצי קילו").

For each item:
- search_terms: 1-3 short Hebrew phrases as Israeli supermarket shelf labels write the
  product ("חלב 3%", "ביצים L", "קוטג' 5%"). Translate English items to Hebrew. Labels mix
  singular and plural and spell things differently, so add the variants a label might use:
  loose produce is usually singular ("עגבניה", "מלפפון", "בננה") even when the shopper
  writes plural. Shoppers use everyday names, but labels print the formal product name,
  so always include the formal label name too: "חמוצים" (pickles) are labelled
  "מלפפון בחומץ" or "מלפפון במלח"; "שמנת לבישול" is "שמנת מתוקה". Words like "פחית",
  "קופסה" or "שקית" describe the packaging, not the product: leave them out of the terms.
- quantity and unit: produce, meat, cheese from the deli and anything asked for by
  weight is unit "kg" ("חצי קילו" = 0.5). Everything else is "unit". Default quantity is 1.
- brand and size: only when the shopper wrote them. Never invent them.
- Skip anything that is not a product (greetings, notes to self).
"""

MATCH_SYSTEM = """You match a shopper's grocery list to real products at Israeli supermarket branches.

For every list item and every chain you get the candidates found by text search.
Choose the one product the shopper most likely means, and return exactly one
decision per (item index, chain) pair you were given.

Rules:
- Match what was asked, not what merely shares words: "חלב" is milk, not a milk
  frother or milk chocolate.
- Respect brand and size when the shopper gave them.
- When no size was given, choose the most standard everyday size, and choose the
  SAME size at every chain so the prices are comparable.
- Prefer the plain, regular version over special variants (lactose-free, Mehadrin,
  flavored) unless the shopper asked for one.
- For items bought by weight, prefer weighted products (is_weighted true).
- If the standard size isn't sold at a chain, choose the closest size and mark it "low"
  rather than returning null: a flagged guess is more useful than a gap.
- Return item_code null only when no candidate is the same kind of product. Never invent codes.
- confidence "low" when the choice is a guess the shopper should check.
"""


def match_user_prompt(items_json: str) -> str:
    return "Items and their candidates per chain (JSON):\n" + items_json
