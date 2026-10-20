# CartWise

> Work in progress. The price ingestion pipeline is done; the API, AI matching and web app are being built now.

Type your weekly grocery list in plain Hebrew and CartWise finds the cheapest basket across Israel's big supermarket chains, using the price files every chain is required by law to publish (the 2014 Food Act, חוק קידום התחרות בענף המזון).

## How it works

1. **Ingest** — every day, download the official price, promotion and branch files for the branches users follow, and load them into PostgreSQL.
2. **Understand the list** — Claude turns free text ("2 חלב 3%, ביצים L, קילו עגבניות") into structured items.
3. **Match** — trigram search finds candidate products at each branch; Claude picks the right one or asks the user. Confirmed matches are remembered, so next week's list costs no AI calls.
4. **Compare** — the basket total per chain, using regular prices plus promotions open to every shopper (club-only deals are excluded; weighted items are compared per kilo).

The AI only interprets the list and picks matches. Prices always come from the published files, never from the model.

## Chains

| Chain | Source |
|-------|--------|
| Shufersal | prices.shufersal.co.il |
| Rami Levy | url.publishedprices.co.il |
| Yohananof | url.publishedprices.co.il |
| Osher Ad | url.publishedprices.co.il |

## Tech Stack

| Layer | Choice |
|-------|--------|
| Backend | FastAPI, SQLAlchemy 2.0, Alembic |
| Database | PostgreSQL 16 with `pg_trgm` |
| AI | Claude (Anthropic API) |
| Frontend | React + TypeScript (coming) |
| Dev environment | Docker Compose |

## Running the ingestion locally

```bash
docker compose up -d db
cd backend
cp .env.example .env
python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/alembic upgrade head

.venv/bin/python -m app.ingestion.run stores               # branch lists for all chains
.venv/bin/python -m app.ingestion.run track rami-levy 709  # follow a branch
.venv/bin/python -m app.ingestion.run prices               # load prices + promotions
```

Tests: `.venv/bin/pytest`

## Data sources

- Prices, promotions and branches: the files each chain publishes under the 2014 Food Act.
- Localities: the official list on [data.gov.il](https://data.gov.il/dataset/citiesandsettelments).
- City coordinates: © [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors, ODbL, via Nominatim (built once by `backend/scripts/build_localities.py`).

## License

MIT
