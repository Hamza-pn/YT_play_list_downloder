from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T | None = None
    message: str | None = None


class ErrorDetail(BaseModel):
    code: str
    message: str


class APIError(BaseModel):
    success: bool = False
    error: ErrorDetail
