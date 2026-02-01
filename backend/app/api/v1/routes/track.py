from fastapi import APIRouter, Request

from app import schemas
from app.core.rate_limiter import limiter
from app.dependencies import ProjectIdDep, SessionDep
from app.services import metric_service

router = APIRouter()


@router.post(
    "/",
    response_model=schemas.MetricResponse,
    summary="Track an API metric",
    description="""
    Records a new API metric for the project associated with the provided API key.
    
    This endpoint is used by client libraries (SDKs) or direct API calls to log details
    about an incoming request in the application being monitored.
    
    The API key must be sent in the `X-API-Key` header.
    """,
)
@limiter.limit("100/minute")
async def track_metric(
    request: Request,
    metric: schemas.MetricCreate,
    session: SessionDep,
    project_id: ProjectIdDep,
):
    """
    Track an API metric.
    """
    return await metric_service.add_metric(session, project_id, metric)
