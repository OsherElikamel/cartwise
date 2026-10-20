from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.locality import ChainBranches, LocalityResponse
from app.services import locality_service

router = APIRouter(prefix="/api/localities", tags=["Cities"])


@router.get("", response_model=list[LocalityResponse])
def search_localities(
    search: str = Query(..., min_length=1, max_length=60, description="City name in Hebrew or English"),
    limit: int = Query(10, ge=1, le=30),
    db: Session = Depends(get_db),
):
    return locality_service.search_localities(db, search, limit)


@router.get("/{code}", response_model=LocalityResponse)
def get_locality(code: str, db: Session = Depends(get_db)):
    return locality_service.get_locality(db, code)


@router.get("/{code}/branches", response_model=list[ChainBranches])
def branches_near(code: str, chain: str | None = Query(None, max_length=30), db: Session = Depends(get_db)):
    """Per chain: branches in this city, or the nearest cities that have one (distance between city centers)."""
    return locality_service.branches_near(db, code, chain)
