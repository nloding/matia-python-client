from __future__ import annotations

from typing import Any

import httpx

from .exceptions import MatiaAPIError, MatiaBadRequestError, MatiaNotFoundError

_ERROR_CLASSES: dict[int, type[MatiaAPIError]] = {
    400: MatiaBadRequestError,
    404: MatiaNotFoundError,
}


class HttpTransport:
    """Thin wrapper around httpx.Client that applies auth, base_url, and error handling."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        timeout: float,
        client: httpx.Client | None = None,
    ) -> None:
        self._client = client or httpx.Client(
            base_url=base_url,
            timeout=timeout,
            headers={"x-api-key": api_key},
        )

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        response = self._client.request(method, path, params=_clean(params), json=json)
        if response.status_code >= 400:
            raise _build_error(response)
        if not response.content:
            return {}
        return response.json()

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "HttpTransport":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()


def _clean(params: dict[str, Any] | None) -> dict[str, Any] | None:
    if params is None:
        return None
    return {key: value for key, value in params.items() if value is not None}


def _build_error(response: httpx.Response) -> MatiaAPIError:
    message = f"Request failed with status {response.status_code}"
    code = None
    body: object = None
    try:
        body = response.json()
        if isinstance(body, dict):
            message = body.get("message", message)
            code = body.get("code")
    except ValueError:
        body = response.text

    error_class = _ERROR_CLASSES.get(response.status_code, MatiaAPIError)
    return error_class(
        message,
        status_code=response.status_code,
        code=code,
        response_body=body,
    )
