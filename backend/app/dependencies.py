from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core import db
from app.core.api_keys import get_project_id_from_api_key


def get_db() -> Generator[Session, None, None]:
    with db.Session() as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]
ProjectIdDep = Annotated[int, Depends(get_project_id_from_api_key)]
