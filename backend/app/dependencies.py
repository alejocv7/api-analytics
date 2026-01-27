from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app import models
from app.core import api_keys, config, db
from app.crud import users

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{config.settings.API_PREFIX}/login/access-token"
)


def get_db() -> Generator[Session, None, None]:
    with db.Session() as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]
ProjectIdDep = Annotated[int, Depends(api_keys.get_project_id)]
CurrentUserDep = Annotated[models.User, Depends(users.get_current_user)]
TokenDep = Annotated[str, Depends(reusable_oauth2)]
