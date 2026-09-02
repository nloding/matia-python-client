from __future__ import annotations

from datetime import datetime

from pydantic import Field

from .common import MatiaModel


class User(MatiaModel):
    """A Matia user."""

    id: str
    email: str
    name: str | None = None
    created_at: datetime | None = Field(default=None, alias="createdAt")
