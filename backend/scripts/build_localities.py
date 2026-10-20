"""Build app/data/localities.json: every Israeli locality with coordinates.

Names and codes come from the official locality list on data.gov.il (the same
codes the chains publish in their Stores files). Coordinates come from
OpenStreetMap's Nominatim geocoder, at its required pace of one request per
second. This runs once, offline; the app only reads the resulting file.

    python scripts/build_localities.py                     # resumes if interrupted
    python scripts/build_localities.py --priority codes.txt  # these codes first (one per line)
    python scripts/build_localities.py --priority codes.txt --only  # just those codes

Coordinates (c) OpenStreetMap contributors, ODbL.
"""

import json
import sys
import time
from pathlib import Path

import httpx

RESOURCE = "8f714b6f-c35c-4b40-a0e7-547b675eee0e"  # רשימת ישובים בישראל, English headers
OUT = Path(__file__).resolve().parent.parent / "app" / "data" / "localities.json"
USER_AGENT = "CartWise/0.1 (portfolio project; github.com/OsherElikamel/cartwise)"


def fetch_localities(client: httpx.Client) -> list[dict]:
    res = client.get(
        "https://data.gov.il/api/3/action/datastore_search",
        params={"resource_id": RESOURCE, "limit": 5000},
    )
    res.raise_for_status()
    rows = res.json()["result"]["records"]
    localities = []
    for row in rows:
        code = str(row["city_code"]).strip()
        name_he = " ".join(str(row["city_name_he"]).split())
        name_en = " ".join(str(row["city_name_en"]).split()).title()
        if code and code != "0" and name_he:
            localities.append({"code": code, "name_he": name_he, "name_en": name_en})
    return localities


def geocode(client: httpx.Client, name_he: str, name_en: str) -> tuple[float, float] | None:
    for query in (name_he, name_en):
        if not query:
            continue
        res = client.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": query, "countrycodes": "il,ps", "format": "json", "limit": 1},
        )
        time.sleep(1.1)  # Nominatim usage policy: at most one request per second
        if res.status_code == 200 and res.json():
            hit = res.json()[0]
            return round(float(hit["lat"]), 5), round(float(hit["lon"]), 5)
    return None


def save(done: dict) -> None:
    OUT.write_text(json.dumps(sorted(done.values(), key=lambda l: l["code"]), ensure_ascii=False, indent=0))


def main() -> int:
    priority: list[str] = []
    if len(sys.argv) >= 3 and sys.argv[1] == "--priority":
        priority = [line.strip() for line in Path(sys.argv[2]).read_text().splitlines() if line.strip()]
    only = "--only" in sys.argv
    done = {loc["code"]: loc for loc in json.loads(OUT.read_text())} if OUT.exists() else {}
    with httpx.Client(timeout=30, headers={"User-Agent": USER_AGENT}) as client:
        localities = fetch_localities(client)
        # Cities that have branches matter most for suggestions: do them first.
        rank = {code: i for i, code in enumerate(priority)}
        localities.sort(key=lambda loc: rank.get(loc["code"], len(rank)))
        print(f"{len(localities)} localities, {len(done)} already geocoded", flush=True)
        for i, loc in enumerate(localities, 1):
            if only and loc["code"] not in rank:
                break
            if loc["code"] in done:
                continue
            coords = geocode(client, loc["name_he"], loc["name_en"])
            done[loc["code"]] = {**loc, "lat": coords[0] if coords else None, "lon": coords[1] if coords else None}
            if i % 25 == 0:
                save(done)
                print(f"{i}/{len(localities)}", flush=True)
    save(done)
    missing = sum(1 for loc in done.values() if loc["lat"] is None)
    print(f"done: {len(done)} localities, {missing} without coordinates", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
