from __future__ import annotations

from typing import TYPE_CHECKING

from ..models.tags import Tag

if TYPE_CHECKING:
    from ..client import MatiaClient


class TagsResource:
    """Create, edit, and assign tags to resources."""

    def __init__(self, client: "MatiaClient") -> None:
        self._client = client

    def list(self) -> list[Tag]:
        """List all tags."""
        raw = self._client._http.request("GET", "/tags")
        items = raw.get("data", {}).get("items", [])
        return [Tag.model_validate(item)._bind(self._client) for item in items]

    def create(self, name: str, owner: str, *, description: str | None = None) -> Tag:
        """Create a new tag."""
        body = _drop_none({"name": name, "owner": owner, "description": description})
        raw = self._client._http.request("POST", "/tags", json=body)
        data = raw.get("data", {})
        merged = {**body, **data}
        return Tag.model_validate(merged)._bind(self._client)

    def get(self, tag_id: str) -> Tag:
        """Get the details of a specific tag."""
        raw = self._client._http.request("GET", f"/tags/{tag_id}")
        data = raw.get("data", {})
        return Tag.model_validate(data)._bind(self._client)

    def update(
        self,
        tag_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        owner: str | None = None,
    ) -> Tag:
        """Edit a tag by ID."""
        body = _drop_none({"name": name, "description": description, "owner": owner})
        raw = self._client._http.request("PUT", f"/tags/{tag_id}", json=body)
        data = raw.get("data", {})
        merged = {"id": tag_id, **body, **data}
        return Tag.model_validate(merged)._bind(self._client)

    def delete(self, tag_id: str) -> None:
        """Delete a tag by ID."""
        self._client._http.request("DELETE", f"/tags/{tag_id}")

    def assign(
        self, tag_id: str, *, resource_id: str, resource_type: str, tagged_by: str
    ) -> None:
        """Create a relation between a tag and a resource (Integration, DataAsset, Monitor)."""
        body = {
            "resourceId": resource_id,
            "resourceType": resource_type,
            "taggedBy": tagged_by,
        }
        self._client._http.request("POST", f"/tags/{tag_id}/relation", json=body)

    def unassign(self, tag_id: str, *, resource_id: str, resource_type: str) -> None:
        """Remove a relation between a tag and a resource."""
        body = {"resourceId": resource_id, "resourceType": resource_type}
        self._client._http.request("DELETE", f"/tags/{tag_id}/relation", json=body)


def _drop_none(d: dict) -> dict:
    return {k: v for k, v in d.items() if v is not None}
