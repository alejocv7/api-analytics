from fastapi import APIRouter

import app.crud as crud
from app.dependencies import SessionDep
from app.schemas import APIMetric

router = APIRouter()


@router.get("/", response_model=list[APIMetric])
async def read_metrics(
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
):
    """
    Retrieve API metrics.
    """
    return crud.get_metrics(session, skip=skip, limit=limit)
