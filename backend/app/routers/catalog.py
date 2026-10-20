from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.catalog import ChainResponse, ProductResult, StoreResponse
from app.services import catalog_service

router = APIRouter(prefix="/api", tags=["Catalog"])


@router.get("/chains", response_model=list[ChainResponse])
def list_chains(db: Session = Depends(get_db)):
    return catalog_service.list_chains(db)


@router.get("/stores", response_model=list[StoreResponse])
def search_stores(
    search: str | None = Query(None, max_length=100, description="Words to find in branch name, address or chain"),
    chain: str | None = Query(None, max_length=30, description="Chain slug, e.g. rami-levy"),
    tracked_only: bool = False,
    demo_only: bool = Query(False, description="Only the branches guests compare on"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return catalog_service.search_stores(db, search, chain, tracked_only, limit, demo_only)


@router.get("/products/search", response_model=list[ProductResult])
def search_products(
    q: str = Query(..., min_length=2, max_length=100, description="Free text, e.g. חלב 3%"),
    store_id: list[UUID] | None = Query(None, description="Limit to these branches (default: all tracked)"),
    per_store: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    return catalog_service.search_products(db, [q], store_id, per_store)
