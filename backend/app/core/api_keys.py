from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy import select

from app import models
from app.core.security import hash_api_key
from app.dependencies import SessionDep

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_project_id_from_api_key(
    session: SessionDep,
    api_key: str = Security(api_key_header),
) -> int:
    """Validates API key and returns the Project id."""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="API key required"
        )

    api_key_obj = session.execute(
        select(models.ApiKey).where(
            models.ApiKey.key_hash == hash_api_key(api_key),
            models.ApiKey.is_active.is_(True),
        )
    ).scalar_one_or_none()

    if not api_key_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key"
        )

    return api_key_obj.project_id
