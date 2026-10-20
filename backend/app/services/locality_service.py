"""Cities and "which branches are near me".

Every branch is tied to a locality from the official list: by the city code
the chain publishes, or, when a chain publishes none (Yohananof sends 0), by
finding the locality's name inside the branch name. Never inside the street
address: streets are named after places and people, and words like "רחוב"
(street) and "אזור" (zone) are also locality names. A branch with no city is
better than one placed in the wrong city. Distances are between
city centers, which is honest at the scale people choose a supermarket.
"""

import json
import math
import re
from pathlib import Path

from sqlalchemy import func, or_, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.ingestion.chains import CHAINS_BY_SLUG
from app.models.chain import Chain, Store
from app.models.locality import Locality
from app.models.user import User
from app.schemas.locality import ChainBranches, LocalityResponse, NearbyGroup
from app.services.user_store_service import to_store_response

LOCALITIES_FILE = Path(__file__).resolve().parent.parent / "data" / "localities.json"
NEARBY_LOCALITIES = 3
STORES_PER_LOCALITY = 4


# --- loading and matching ---------------------------------------------------

def seed_localities(db: Session, path: Path = LOCALITIES_FILE) -> int:
    rows = json.loads(path.read_text(encoding="utf-8"))
    for row in rows:
        stmt = pg_insert(Locality).values(**row)
        db.execute(stmt.on_conflict_do_update(index_elements=[Locality.code], set_=row))
    db.commit()
    return len(rows)


# Abbreviations branch names use for big cities.
ABBREVIATIONS = {'ת"א': "תל אביב", "ת״א": "תל אביב", 'ראשל"צ': "ראשון לציון", "ראשלצ": "ראשון לציון",
                 'פ"ת': "פתח תקווה", 'ב"ש': "באר שבע"}


def normalize_place(text: str) -> str:
    """Spellings differ between the official list and branch names:
    abbreviations, hyphens, quote marks, and קריית vs קרית."""
    for short, full in ABBREVIATIONS.items():
        text = text.replace(short, full)
    text = re.sub(r"[-־–\"'׳״().,]", " ", text)
    text = re.sub(r"\bקריית\b", "קרית", text)
    return " ".join(text.split())


def _name_index(localities: list[Locality]) -> list[tuple[str, str]]:
    """(normalized name, code), longest first.

    Official names are often compound, and branches use one part: "יהוד-מונוסון"
    is "יהוד", merged councils like "בנימינה-גבעת עדה" keep both old names, and
    "אשדות יעקב (איחוד)" is just "אשדות יעקב". Every part becomes an alias, but
    full official names are indexed first, so an alias never takes over a real
    locality's own name.
    """
    index: dict[str, str] = {}
    for loc in localities:
        index.setdefault(normalize_place(loc.name_he), loc.code)
    for loc in localities:
        for part in re.split(r"\s*[-־–(]\s*", loc.name_he):
            part = part.strip(" )")
            if len(part) >= 3 and part != loc.name_he:
                index.setdefault(normalize_place(part), loc.code)
    return sorted(index.items(), key=lambda item: -len(item[0]))


def match_locality(text: str, index: list[tuple[str, str]]) -> str | None:
    """The longest locality name that appears as whole words in the text."""
    padded = f" {normalize_place(text)} "
    for name, code in index:
        if len(name) >= 3 and f" {name} " in padded:
            return code
    return None


def resolve_store_localities(db: Session) -> int:
    """Tie each branch to a locality; returns how many branches stay unresolved."""
    localities = list(db.scalars(select(Locality)))
    known = {loc.code for loc in localities}
    index = _name_index(localities)
    unresolved = 0
    for store in db.scalars(select(Store)):
        code = store.city_code if store.city_code in known else None
        if code is None:
            code = match_locality(store.name, index)
        store.locality_code = code
        unresolved += code is None
    db.commit()
    return unresolved


# --- queries ------------------------------------------------------------------

def _grocery_stores():
    """Branches people shop for groceries at (drugstore sub-chains left out)."""
    query = select(Store, Chain).join(Chain)
    for slug, config in CHAINS_BY_SLUG.items():
        if config.non_grocery_sub_chains:
            query = query.where(~((Chain.slug == slug) & Store.sub_chain_code.in_(config.non_grocery_sub_chains)))
    return query


def search_localities(db: Session, q: str, limit: int) -> list[LocalityResponse]:
    """Localities matching the text in Hebrew or English, the ones that have
    branches first, then prefix matches."""
    pattern, prefix = f"%{q.strip()}%", f"{q.strip()}%"
    has_branches = select(Store.locality_code).where(Store.locality_code.is_not(None)).distinct()
    rows = db.scalars(
        select(Locality)
        .where(or_(Locality.name_he.ilike(pattern), Locality.name_en.ilike(pattern)))
        .order_by(
            Locality.code.in_(has_branches).desc(),
            or_(Locality.name_he.ilike(prefix), Locality.name_en.ilike(prefix)).desc(),
            func.length(Locality.name_he),
        )
        .limit(limit)
    )
    return [LocalityResponse.model_validate(loc) for loc in rows]


def get_locality(db: Session, code: str) -> Locality:
    locality = db.get(Locality, code)
    if locality is None:
        raise NotFoundError("City not found", "locality_not_found")
    return locality


def distance_km(a: Locality, b: Locality) -> float:
    """Great-circle distance between two city centers."""
    lat1, lon1, lat2, lon2 = map(math.radians, (a.lat, a.lon, b.lat, b.lon))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 6371.0 * 2 * math.asin(math.sqrt(h))


def branches_near(db: Session, code: str, chain_slug: str | None = None) -> list[ChainBranches]:
    """Per chain: its branches in this city, and otherwise the nearest cities that have one."""
    home = get_locality(db, code)
    query = _grocery_stores().where(Store.locality_code.is_not(None))
    if chain_slug:
        query = query.where(Chain.slug == chain_slug)
    rows = db.execute(query.order_by(Store.name)).all()

    localities = {loc.code: loc for loc in db.scalars(select(Locality).where(Locality.code.in_({s.locality_code for s, _ in rows})))}
    by_chain: dict[str, tuple[Chain, dict[str, list[Store]]]] = {}
    for store, chain in rows:
        by_chain.setdefault(chain.slug, (chain, {}))[1].setdefault(store.locality_code, []).append(store)

    result = []
    for slug, (chain, stores_by_locality) in sorted(by_chain.items()):
        in_city = stores_by_locality.get(home.code, [])
        nearby: list[NearbyGroup] = []
        if home.lat is not None:
            candidates = [
                (distance_km(home, localities[loc_code]), localities[loc_code], stores)
                for loc_code, stores in stores_by_locality.items()
                if loc_code != home.code and localities[loc_code].lat is not None
            ]
            for distance, locality, stores in sorted(candidates, key=lambda c: c[0])[:NEARBY_LOCALITIES]:
                nearby.append(NearbyGroup(
                    locality=LocalityResponse.model_validate(locality),
                    distance_km=round(distance, 1),
                    stores=[to_store_response(s, chain) for s in stores[:STORES_PER_LOCALITY]],
                ))
        result.append(ChainBranches(
            chain_slug=slug, chain_name=chain.name,
            in_city=[to_store_response(s, chain) for s in in_city], nearby=nearby,
        ))
    return result


def set_home(db: Session, user: User, code: str | None) -> LocalityResponse | None:
    if code is not None:
        get_locality(db, code)
    db.execute(update(User).where(User.id == user.id).values(home_locality_code=code))
    db.commit()
    return LocalityResponse.model_validate(db.get(Locality, code)) if code else None
