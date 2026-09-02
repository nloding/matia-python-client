from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, PrivateAttr


class MatiaModel(BaseModel):
    """Base model for API payloads.

    Accepts the API's camelCase field names on input (via aliases) while
    exposing idiomatic snake_case attributes in Python.
    """

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    _client: Any = PrivateAttr(default=None)

    def _bind(self, client: Any) -> "MatiaModel":
        self._client = client
        return self
