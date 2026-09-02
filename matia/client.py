from __future__ import annotations

import httpx

from ._http import HttpTransport
from .resources.assets import AssetsResource
from .resources.audit_logs import AuditLogsResource
from .resources.integrations import IntegrationsResource
from .resources.tags import TagsResource
from .resources.users import UsersResource

DEFAULT_BASE_URL = "https://api.matia.io/v1"
DEFAULT_TIMEOUT = 30.0


class MatiaClient:
    """Entry point for the Matia API.

    Example:
        client = MatiaClient(api_key="...")
        integrations = client.integrations.list()
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._http = HttpTransport(
            api_key=api_key, base_url=base_url, timeout=timeout, client=http_client
        )
        self.assets = AssetsResource(self)
        self.integrations = IntegrationsResource(self)
        self.tags = TagsResource(self)
        self.users = UsersResource(self)
        self.audit_logs = AuditLogsResource(self)

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "MatiaClient":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()
