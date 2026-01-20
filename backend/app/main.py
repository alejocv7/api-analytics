from typing import Union

from fastapi import FastAPI
from .routers.health import router as health_router

app = FastAPI(
    title="API Analytics",
    description="Track and analyze API performance metrics",
    version="1.0.0",
)

app.include_router(health_router)


@app.get("/")
async def root():
    return {"message": "API Analytics Service", "version": "1.0.0", "docs": "/docs"}
