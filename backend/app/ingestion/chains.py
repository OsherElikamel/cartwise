from collections.abc import Callable
from dataclasses import dataclass

from app.ingestion.sources import PublishedPricesSource, ShufersalSource, Source


@dataclass(frozen=True)
class ChainConfig:
    slug: str
    chain_code: str
    name: str
    name_he: str
    make_source: Callable[[], Source]
    # Sub-chains that are not grocery stores (Shufersal's 5 is BE, a drugstore chain).
    non_grocery_sub_chains: frozenset[str] = frozenset()


CHAINS: list[ChainConfig] = [
    ChainConfig("shufersal", "7290027600007", "Shufersal", "שופרסל", ShufersalSource, frozenset({"5"})),
    ChainConfig("rami-levy", "7290058140886", "Rami Levy", "רמי לוי", lambda: PublishedPricesSource("RamiLevi")),
    ChainConfig("yohananof", "7290803800003", "Yohananof", "יוחננוף", lambda: PublishedPricesSource("yohananof")),
    ChainConfig("osher-ad", "7290103152017", "Osher Ad", "אושר עד", lambda: PublishedPricesSource("osherad")),
]

CHAINS_BY_SLUG = {c.slug: c for c in CHAINS}
