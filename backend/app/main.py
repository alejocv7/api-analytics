from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import settings
from app.middleware import APIMetricMiddleware

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
)

app.include_router(api_router, prefix=settings.API_V1_STR)
app.add_middleware(APIMetricMiddleware)


@app.get("/")
async def root():
    return {
        "message": settings.PROJECT_NAME,
        "description": settings.PROJECT_DESCRIPTION,
        "docs": "/docs",
    }
