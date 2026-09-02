from __future__ import annotations

from datetime import datetime

from pydantic import Field

from .common import MatiaModel


class Tag(MatiaModel):
    """A tag that can be attached to resources (Integrations, DataAssets, Monitors)."""

    id: str
    name: str | None = None
    description: str | None = None
    owner: str | None = Field(default=None, description="User ID of the tag's owner.")
    origin: str | None = None
    created_at: datetime | None = Field(default=None, alias="createdAt")
    last_updated_at: datetime | None = Field(default=None, alias="lastUpdatedAt")

    def update(
        self,
        *,
        name: str | None = None,
        description: str | None = None,
        owner: str | None = None,
    ) -> "Tag":
        """Update this tag via the API and return the refreshed model."""
        return self._client.tags.update(
            self.id, name=name, description=description, owner=owner
        )

    def delete(self) -> None:
        self._client.tags.delete(self.id)

    def assign(self, *, resource_id: str, resource_type: str, tagged_by: str) -> None:
        """Create a relation between this tag and a resource (Integration, DataAsset, Monitor)."""
        self._client.tags.assign(
            self.id,
            resource_id=resource_id,
            resource_type=resource_type,
            tagged_by=tagged_by,
        )

    def unassign(self, *, resource_id: str, resource_type: str) -> None:
        self._client.tags.unassign(
            self.id, resource_id=resource_id, resource_type=resource_type
        )
