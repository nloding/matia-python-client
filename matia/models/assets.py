from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from .common import MatiaModel


class Asset(MatiaModel):
    """A data asset registered with Matia."""

    id: str
    name: str | None = None
    type: str | None = Field(default=None, description="Type of the asset.")
    description: str | None = None
    connection: dict[str, Any] | None = Field(
        default=None, description="Connection details for the asset."
    )
    connection_type: Literal["source", "destination"] | None = Field(
        default=None, alias="connectionType"
    )

    def update(
        self,
        *,
        name: str | None = None,
        description: str | None = None,
        connection: dict[str, Any] | None = None,
    ) -> "Asset":
        """Update this asset in place via the API and return the refreshed model."""
        return self._client.assets.update(
            self.id, name=name, description=description, connection=connection
        )
