from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.services.fruit_service import FruitService

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/fruit")
def list_fruit(
    color: str | None = None,
    in_season: bool | None = None,
    name: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    service = FruitService(db)
    return service.get_fruits(color, in_season, name, page, page_size)
