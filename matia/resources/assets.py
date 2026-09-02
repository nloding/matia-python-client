from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..models.assets import Asset

if TYPE_CHECKING:
    from ..client import MatiaClient


class AssetsResource:
    """Create and update data assets."""

    def __init__(self, client: "MatiaClient") -> None:
        self._client = client

    def create(
        self,
        name: str,
        type: str,
        *,
        description: str | None = None,
        connection: dict[str, Any] | None = None,
        connection_type: str | None = None,
    ) -> Asset:
        """Create a new asset."""
        body = {
            "name": name,
            "type": type,
            "description": description,
            "connection": connection,
            "connectionType": connection_type,
        }
        raw = self._client._http.request(
            "POST", "/assets", json=_drop_none(body)
        )
        data = raw.get("data", {})
        # The API only echoes id/name/type back; merge in the rest of the
        # request so the returned model reflects what was actually created.
        merged = {**body, **data}
        return Asset.model_validate(merged)._bind(self._client)

    def update(
        self,
        asset_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        connection: dict[str, Any] | None = None,
    ) -> Asset:
        """Edit an existing asset."""
        body = {"name": name, "description": description, "connection": connection}
        raw = self._client._http.request(
            "PATCH", f"/assets/{asset_id}", json=_drop_none(body)
        )
        data = raw.get("data", {})
        merged = {**body, "id": asset_id, **data}
        return Asset.model_validate(_drop_none(merged))._bind(self._client)


def _drop_none(d: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None}
