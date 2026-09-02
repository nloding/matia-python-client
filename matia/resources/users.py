from __future__ import annotations

from typing import TYPE_CHECKING

from ..models.users import User

if TYPE_CHECKING:
    from ..client import MatiaClient


class UsersResource:
    """Read access to Matia users."""

    def __init__(self, client: "MatiaClient") -> None:
        self._client = client

    def list(self) -> list[User]:
        """List all users."""
        raw = self._client._http.request("GET", "/users")
        items = raw.get("data", {}).get("items", [])
        return [User.model_validate(item)._bind(self._client) for item in items]
