from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request, Response
from sqlalchemy.orm import Session

from app.config.settings import Settings, get_settings
from app.db.session import get_db
from app.models.user import User
from app.services.session_service import get_or_create_user

DbSession = Annotated[Session, Depends(get_db)]
AppSettings = Annotated[Settings, Depends(get_settings)]


def get_current_user(request: Request, response: Response, db: DbSession) -> User:
    return get_or_create_user(db, request, response)


CurrentUser = Annotated[User, Depends(get_current_user)]
