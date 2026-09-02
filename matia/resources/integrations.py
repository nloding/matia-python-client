from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..models.integrations import (
    ColumnConfig,
    GoogleAnalytics4Connection,
    GoogleAnalytics4ConnectorPayload,
    GoogleAnalytics4SourceConfig,
    GoogleAnalytics4SourceSettings,
    Integration,
    IntegrationRun,
    IntegrationSchemaConfig,
    PostgresConnection,
    PostgresConnectorPayload,
    PostgresSourceConfig,
    PostgresSourceSettings,
)

if TYPE_CHECKING:
    from ..client import MatiaClient


class IntegrationsResource:
    """Manage integrations: sync runs, schema config, and connector creation."""

    def __init__(self, client: "MatiaClient") -> None:
        self._client = client

    def list(self) -> list[Integration]:
        """List all integrations."""
        raw = self._client._http.request("GET", "/integrations")
        items = raw.get("data", {}).get("items", [])
        return [Integration.model_validate(item)._bind(self._client) for item in items]

    def get(self, integration_id: str) -> Integration:
        """Get the details of a specific integration."""
        raw = self._client._http.request("GET", f"/integrations/{integration_id}")
        data = raw.get("data", {}).get("integration", {})
        return Integration.model_validate(data)._bind(self._client)

    def update(self, integration_id: str, *, paused: bool | None = None) -> Integration:
        """Update an integration (currently only its paused state)."""
        body = {} if paused is None else {"paused": paused}
        self._client._http.request(
            "PATCH", f"/integrations/{integration_id}", json=body
        )
        # The update response only echoes back `paused`, not the full
        # integration, so re-fetch to hand back a complete, fluent model.
        return self.get(integration_id)

    def delete(self, integration_id: str) -> None:
        """Delete an integration."""
        self._client._http.request("DELETE", f"/integrations/{integration_id}")

    def run(self, integration_id: str) -> Integration:
        """Trigger a sync run for an integration.

        The API's run response only acks which integration was triggered
        (no run id or status), so this re-fetches the integration afterward.
        Its `latest_run_id` can then be passed to `get_run` to poll status.
        """
        self._client._http.request("POST", f"/integrations/{integration_id}/run")
        return self.get(integration_id)

    def get_run(self, integration_id: str, run_id: str) -> IntegrationRun:
        """Get the status of a specific integration run."""
        raw = self._client._http.request(
            "GET", f"/integrations/{integration_id}/runs/{run_id}"
        )
        return IntegrationRun.model_validate(raw.get("data", {}))

    def get_schema_config(self, integration_id: str) -> IntegrationSchemaConfig:
        """Get the source schema config (schemas/tables/columns) for an integration."""
        raw = self._client._http.request(
            "GET", f"/integrations/{integration_id}/schemas"
        )
        return IntegrationSchemaConfig.from_api(raw.get("data", {}))

    def update_schema_config(
        self, integration_id: str, schemas: dict[str, Any]
    ) -> IntegrationSchemaConfig:
        """Update the source schema config for an integration."""
        raw = self._client._http.request(
            "PATCH",
            f"/integrations/{integration_id}/schemas",
            json={"schemas": schemas},
        )
        return IntegrationSchemaConfig.from_api(raw.get("data", {}))

    def get_table_columns(
        self, integration_id: str, schema: str, table: str
    ) -> list[ColumnConfig]:
        """Get the source columns for a specific schema/table of an integration."""
        raw = self._client._http.request(
            "GET",
            f"/integrations/{integration_id}/schemas/{schema}/tables/{table}/columns",
        )
        columns = raw.get("data", {}).get("columns", {}) or {}
        return [
            ColumnConfig.model_validate({**(val or {}), "source_name": name})
            for name, val in columns.items()
        ]

    def postgres(self) -> "PostgresConnectorBuilder":
        """Start a chainable builder for creating a Postgres integration."""
        return PostgresConnectorBuilder(self)

    def google_analytics_4(self) -> "GoogleAnalytics4ConnectorBuilder":
        """Start a chainable builder for creating a Google Analytics 4 integration."""
        return GoogleAnalytics4ConnectorBuilder(self)

    def _create(self, payload: Any) -> Integration:
        raw = self._client._http.request(
            "POST",
            "/integrations",
            json=payload.model_dump(by_alias=True, exclude_none=True),
        )
        created_id = raw.get("data", {}).get("id") or raw.get("id")
        return self.get(str(created_id))


class _ConnectorBuilderBase:
    """Shared chainable setters for the Postgres/GA4 connector builders."""

    def __init__(self, resource: IntegrationsResource) -> None:
        self._resource = resource
        self._name: str | None = None
        self._destination_id: str | None = None
        self._destination_schema: str | None = None
        self._replication_frequency: str | None = None
        self._on_schema_update: str | None = None
        self._enabled: bool = True
        self._connection_type: str | None = None
        self._owners: list[str] = []

    def name(self, name: str) -> "_ConnectorBuilderBase":
        """Set the source connector's display name."""
        self._name = name
        return self

    def destination(self, destination_id: str, destination_schema: str) -> "_ConnectorBuilderBase":
        """Set the destination asset id and destination schema to sync into."""
        self._destination_id = destination_id
        self._destination_schema = destination_schema
        return self

    def replication_frequency(self, frequency: str) -> "_ConnectorBuilderBase":
        """Set how often the integration replicates data."""
        self._replication_frequency = frequency
        return self

    def on_schema_update(self, value: str) -> "_ConnectorBuilderBase":
        """Set the behavior to apply when the source schema changes."""
        self._on_schema_update = value
        return self

    def enabled(self, enabled: bool = True) -> "_ConnectorBuilderBase":
        """Set whether the integration is enabled (defaults to True)."""
        self._enabled = enabled
        return self

    def connection_type(self, connection_type: str) -> "_ConnectorBuilderBase":
        """Set the source connection type."""
        self._connection_type = connection_type
        return self

    def owners(self, owners: list[str]) -> "_ConnectorBuilderBase":
        """Set the user IDs who own this source."""
        self._owners = owners
        return self


class PostgresConnectorBuilder(_ConnectorBuilderBase):
    """Chainable builder for creating a Postgres-sourced integration."""

    def __init__(self, resource: IntegrationsResource) -> None:
        super().__init__(resource)
        self._auth_method: str | None = None
        self._connection: dict[str, Any] = {}
        self._source_settings: dict[str, Any] = {}

    def auth_method(self, auth_method: str) -> "PostgresConnectorBuilder":
        """Set the Postgres authentication method."""
        self._auth_method = auth_method
        return self

    def connection(
        self,
        *,
        username: str | None = None,
        password: str | None = None,
        hostname: str | None = None,
        port: int | None = None,
        database: str | None = None,
        slot: str | None = None,
        publication: str | None = None,
    ) -> "PostgresConnectorBuilder":
        """Set Postgres connection details; only the given fields are updated."""
        self._connection.update(
            {
                k: v
                for k, v in {
                    "username": username,
                    "password": password,
                    "hostname": hostname,
                    "port": port,
                    "database": database,
                    "slot": slot,
                    "publication": publication,
                }.items()
                if v is not None
            }
        )
        return self

    def source_settings(
        self, *, max_clients: int | None = None, incremental_mode: str | None = None
    ) -> "PostgresConnectorBuilder":
        """Set Postgres-specific source settings; only the given fields are updated."""
        self._source_settings.update(
            {
                k: v
                for k, v in {
                    "max_clients": max_clients,
                    "incremental_mode": incremental_mode,
                }.items()
                if v is not None
            }
        )
        return self

    def create(self) -> Integration:
        """Create the Postgres integration and return the resulting Integration."""
        payload = PostgresConnectorPayload(
            destinationId=self._destination_id,
            destinationSchema=self._destination_schema,
            replicationFrequency=self._replication_frequency,
            onSchemaUpdate=self._on_schema_update,
            enabled=self._enabled,
            sourceConfig=PostgresSourceConfig(
                name=self._name,
                authMethod=self._auth_method,
                connection=PostgresConnection(**self._connection),
                connectionType=self._connection_type,
                owners=self._owners,
            ),
            sourceSettings=PostgresSourceSettings(**self._source_settings),
        )
        return self._resource._create(payload)


class GoogleAnalytics4ConnectorBuilder(_ConnectorBuilderBase):
    """Chainable builder for creating a Google Analytics 4-sourced integration."""

    def __init__(self, resource: IntegrationsResource) -> None:
        super().__init__(resource)
        self._connection: dict[str, Any] = {}
        self._source_settings: dict[str, Any] = {}

    def connection(
        self,
        *,
        refresh_token: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        rollback: int | None = None,
    ) -> "GoogleAnalytics4ConnectorBuilder":
        """Set GA4 OAuth connection details; only the given fields are updated."""
        self._connection.update(
            {
                k: v
                for k, v in {
                    "refresh_token": refresh_token,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "rollback": rollback,
                }.items()
                if v is not None
            }
        )
        return self

    def source_settings(
        self,
        *,
        account: str | None = None,
        properties: list[str] | None = None,
        custom_reports: list[str] | None = None,
    ) -> "GoogleAnalytics4ConnectorBuilder":
        """Set GA4-specific source settings; only the given fields are updated."""
        if account is not None:
            self._source_settings["account"] = account
        if properties is not None:
            self._source_settings["properties"] = properties
        if custom_reports is not None:
            self._source_settings["custom_reports"] = custom_reports
        return self

    def create(self) -> Integration:
        """Create the GA4 integration and return the resulting Integration."""
        payload = GoogleAnalytics4ConnectorPayload(
            destinationId=self._destination_id,
            destinationSchema=self._destination_schema,
            replicationFrequency=self._replication_frequency,
            onSchemaUpdate=self._on_schema_update,
            enabled=self._enabled,
            sourceConfig=GoogleAnalytics4SourceConfig(
                name=self._name,
                connection=GoogleAnalytics4Connection(**self._connection),
                connectionType=self._connection_type,
                owners=self._owners,
            ),
            sourceSettings=GoogleAnalytics4SourceSettings(**self._source_settings),
        )
        return self._resource._create(payload)
