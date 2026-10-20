import pytest

from app.models.chain import Chain, Store
from app.models.locality import Locality
from app.services.locality_service import _name_index, match_locality, normalize_place, resolve_store_localities

# Real city codes and approximate centers.
YEHUD = Locality(code="9400", name_he="יהוד-מונוסון", name_en="Yehud-Monoson", lat=32.0331, lon=34.8907)
OR_YEHUDA = Locality(code="2400", name_he="אור יהודה", name_en="Or Yehuda", lat=32.0270, lon=34.8629)
KIRYAT_ONO = Locality(code="2620", name_he="קרית אונו", name_en="Kiryat Ono", lat=32.0581, lon=34.8580)
ASHDOD = Locality(code="70", name_he="אשדוד", name_en="Ashdod", lat=31.8014, lon=34.6435)


def test_normalize_handles_hyphens_and_kiryat_spelling():
    assert normalize_place("קריית אונו") == normalize_place("קרית-אונו") == "קרית אונו"


def test_match_uses_longest_whole_word_name_and_first_part_alias():
    index = _name_index([YEHUD, OR_YEHUDA, KIRYAT_ONO])
    assert match_locality("אור יהודה גדול", index) == "2400"    # not "יהוד"
    assert match_locality("שלי יהוד - סביונים", index) == "9400"  # "יהוד" alias of יהוד-מונוסון
    assert match_locality("אקספרס קריית אונו", index) == "2620"   # קריית vs קרית
    assert match_locality("מפוח", index) is None


def test_addresses_are_never_used_to_place_a_branch(db):
    # "רחוב" (street) and "אזור" (zone) are also real locality names.
    db.add_all([Locality(code="1", name_he="רחוב", name_en="Rehov"), Locality(code="2", name_he="אזור", name_en="Azor")])
    chain = Chain(slug="yohananof", chain_code="7290803800003", name="Yohananof", name_he="יוחננוף")
    db.add(chain)
    db.flush()
    db.add_all([
        Store(chain_id=chain.id, store_code="8", name="אחד העם", address="רחוב אחד העם 19", city_code="0"),
        Store(chain_id=chain.id, store_code="1", name="יוחננוף מפוח", address="רחוב המפוח 11, אזור התעשיה", city_code="0"),
    ])
    db.commit()
    assert resolve_store_localities(db) == 2


def test_match_handles_abbreviations_merged_councils_and_parentheses():
    index = _name_index([
        Locality(code="5000", name_he="תל אביב - יפו", name_en="Tel Aviv - Yafo"),
        Locality(code="8300", name_he="ראשון לציון", name_en="Rishon Leziyyon"),
        Locality(code="9800", name_he="בנימינה-גבעת עדה", name_en="Binyamina-Giv'at Ada"),
        Locality(code="199", name_he="אשדות יעקב (איחוד)", name_en="Ashdot Ya'aqov (Ihud)"),
        Locality(code="9999", name_he="יפו", name_en="Yafo"),
    ])
    assert match_locality('ת"א - אחד העם', index) == "5000"
    assert match_locality("ראשלצ רמת אליהו", index) == "8300"
    assert match_locality("אקספרס גבעת עדה", index) == "9800"
    assert match_locality("אשדות יעקב", index) == "199"
    # A real locality's own name beats another locality's alias.
    assert match_locality("סניף יפו", index) == "9999"


@pytest.fixture
def area(db):
    db.add_all([Locality(**{c: getattr(loc, c) for c in ("code", "name_he", "name_en", "lat", "lon")})
                for loc in (YEHUD, OR_YEHUDA, KIRYAT_ONO, ASHDOD)])
    shufersal = Chain(slug="shufersal", chain_code="7290027600007", name="Shufersal", name_he="שופרסל")
    osher = Chain(slug="osher-ad", chain_code="7290103152017", name="Osher Ad", name_he="אושר עד")
    yohananof = Chain(slug="yohananof", chain_code="7290803800003", name="Yohananof", name_he="יוחננוף")
    db.add_all([shufersal, osher, yohananof])
    db.flush()
    db.add_all([
        Store(chain_id=shufersal.id, store_code="1", sub_chain_code="1", name="שלי יהוד", city_code="9400"),
        Store(chain_id=shufersal.id, store_code="2", sub_chain_code="5", name="BE סביונים", city_code="9400"),  # drugstore
        Store(chain_id=osher.id, store_code="3", name="קרית אונו", city_code="2620"),
        Store(chain_id=osher.id, store_code="4", name="אשדוד", city_code="70"),
        Store(chain_id=yohananof.id, store_code="5", name="אור יהודה גדול", city_code="0"),  # no city code
    ])
    db.commit()
    assert resolve_store_localities(db) == 0


def test_city_search_finds_hebrew_and_english(client, area):
    assert [l["code"] for l in client.get("/api/localities", params={"search": "יהוד"}).json()][:1] == ["9400"]
    assert client.get("/api/localities", params={"search": "kiryat"}).json()[0]["code"] == "2620"


def test_branches_in_my_city_and_nearest_elsewhere(client, area):
    chains = {c["chain_slug"]: c for c in client.get("/api/localities/9400/branches").json()}

    # Shufersal is in Yehud; the BE drugstore is not offered.
    assert [s["name"] for s in chains["shufersal"]["in_city"]] == ["שלי יהוד"]

    # No Osher Ad in Yehud: Kiryat Ono (~3.7 km) comes before Ashdod (~33 km).
    osher = chains["osher-ad"]
    assert osher["in_city"] == []
    assert [g["locality"]["code"] for g in osher["nearby"]] == ["2620", "70"]
    assert 3 < osher["nearby"][0]["distance_km"] < 5

    # Yohananof publishes no city code; its branch was matched by name.
    assert chains["yohananof"]["nearby"][0]["locality"]["code"] == "2400"


def test_branches_for_one_chain_only(client, area):
    body = client.get("/api/localities/9400/branches", params={"chain": "osher-ad"}).json()
    assert [c["chain_slug"] for c in body] == ["osher-ad"]


def test_home_city_is_saved_and_validated(client, auth_headers, area):
    res = client.patch("/api/me/home", json={"home_locality_code": "9400"}, headers=auth_headers)
    assert res.json()["name_he"] == "יהוד-מונוסון"
    assert client.get("/api/auth/me", headers=auth_headers).json()["home_locality_code"] == "9400"
    bad = client.patch("/api/me/home", json={"home_locality_code": "99999"}, headers=auth_headers)
    assert (bad.status_code, bad.json()["code"]) == (404, "locality_not_found")
