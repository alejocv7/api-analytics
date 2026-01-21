from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import app.crud as crud
from app.core.db import get_db
from app.schemas import APIMetric

router = APIRouter()


@router.get("/", response_model=list[APIMetric])
async def read_metrics(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    Retrieve API metrics.
    """
    return crud.get_metrics(db, skip=skip, limit=limit)
