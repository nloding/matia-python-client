from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from .common import MatiaModel


class Actor(MatiaModel):
    """Who or what triggered an audit log event."""

    type: Literal["user", "system"]
    email: str | None = None


class Context(MatiaModel):
    """Request context captured alongside an audit log event."""

    ip_address: str | None = Field(default=None, alias="ipAddress")
    user_agent: str | None = Field(default=None, alias="userAgent")


class AuditLog(MatiaModel):
    """A single audit log entry."""

    id: str
    timestamp: datetime = Field(description="UTC timestamp of the audit log.")
    event: str
    actor: Actor
    context: Context | None = None


class AuditLogPage(MatiaModel):
    """A page of audit logs returned by `AuditLogsResource.list`."""

    total_items: int = Field(
        default=0, alias="totalItems", description="Total number of matching audit logs."
    )
    items: list[AuditLog] = []
