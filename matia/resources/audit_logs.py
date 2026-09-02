from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Iterator, Literal

from ..models.audit_logs import AuditLog, AuditLogPage

if TYPE_CHECKING:
    from ..client import MatiaClient


class AuditLogsResource:
    """Read access to audit logs, with offset-based pagination."""

    def __init__(self, client: "MatiaClient") -> None:
        self._client = client

    def list(
        self,
        *,
        limit: int = 20,
        offset: int = 0,
        sort_by: Literal["timestamp"] = "timestamp",
        sort_order: Literal["asc", "desc"] = "desc",
        start_at: str | datetime | None = None,
        end_at: str | datetime | None = None,
    ) -> AuditLogPage:
        """List a single page of audit logs matching the given filters."""
        params = {
            "limit": limit,
            "offset": offset,
            "sortBy": sort_by,
            "sortOrder": sort_order,
            "startAt": _isoformat(start_at),
            "endAt": _isoformat(end_at),
        }
        raw = self._client._http.request("GET", "/audit-logs", params=params)
        page = AuditLogPage.model_validate(raw.get("data", {}))
        for item in page.items:
            item._bind(self._client)
        return page

    def iter_all(
        self,
        *,
        limit: int = 20,
        sort_by: Literal["timestamp"] = "timestamp",
        sort_order: Literal["asc", "desc"] = "desc",
        start_at: str | datetime | None = None,
        end_at: str | datetime | None = None,
    ) -> Iterator[AuditLog]:
        """Auto-paginate through every audit log matching the given filters."""
        offset = 0
        while True:
            page = self.list(
                limit=limit,
                offset=offset,
                sort_by=sort_by,
                sort_order=sort_order,
                start_at=start_at,
                end_at=end_at,
            )
            if not page.items:
                return
            yield from page.items
            offset += len(page.items)
            if offset >= page.total_items:
                return


def _isoformat(value: str | datetime | None) -> str | None:
    if isinstance(value, datetime):
        return value.isoformat()
    return value
