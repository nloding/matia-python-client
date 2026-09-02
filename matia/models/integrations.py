from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import Field

from .common import MatiaModel

# --- Read models -----------------------------------------------------------


class IntegrationEndpoint(MatiaModel):
    """A source or destination asset referenced by an integration."""

    id: str | None = None
    name: str | None = None
    type: str | None = None


class Integration(MatiaModel):
    """A configured sync between a source and a destination."""

    id: str
    name: str | None = None
    created_at: datetime | None = Field(default=None, alias="createdAt")
    paused: bool | None = None
    source: IntegrationEndpoint | None = None
    destination: IntegrationEndpoint | None = None
    latest_run_id: str | None = Field(
        default=None,
        alias="latestRunId",
        description="ID of the most recent run; pass to get_run to check its status.",
    )

    def update(self, *, paused: bool | None = None) -> "Integration":
        """Update this integration via the API and return the refreshed model."""
        return self._client.integrations.update(self.id, paused=paused)

    def delete(self) -> None:
        """Delete this integration."""
        self._client.integrations.delete(self.id)

    def run(self) -> "Integration":
        """Trigger a sync for this integration and return the refreshed integration."""
        return self._client.integrations.run(self.id)

    def get_run(self, run_id: str) -> "IntegrationRun":
        """Get the status of a specific run of this integration."""
        return self._client.integrations.get_run(self.id, run_id)

    def get_latest_run(self) -> "IntegrationRun | None":
        """Get the status of this integration's most recent run, if any."""
        if not self.latest_run_id:
            return None
        return self.get_run(self.latest_run_id)

    def get_schema_config(self) -> "IntegrationSchemaConfig":
        """Get this integration's source schema config."""
        return self._client.integrations.get_schema_config(self.id)

    def update_schema_config(self, schemas: dict[str, Any]) -> "IntegrationSchemaConfig":
        """Update this integration's source schema config."""
        return self._client.integrations.update_schema_config(self.id, schemas)

    def get_table_columns(self, schema: str, table: str) -> list["ColumnConfig"]:
        """Get the source columns for a schema/table of this integration."""
        return self._client.integrations.get_table_columns(self.id, schema, table)


class IntegrationRun(MatiaModel):
    """The status and stats of a single integration sync run."""

    id: str
    integration_id: str | None = Field(default=None, alias="integrationId")
    status: str | None = None
    start_time: datetime | None = Field(default=None, alias="startTime")
    end_time: datetime | None = Field(default=None, alias="endTime")
    committed_records: int | None = Field(default=None, alias="committedRecords")
    emitted_records: int | None = Field(default=None, alias="emittedRecords")
    size: int | None = None


class ColumnConfig(MatiaModel):
    """Sync config for a single source column."""

    source_name: str | None = Field(
        default=None, description="The column's name in the source (not returned by the API)."
    )
    name_in_destination: str | None = Field(default=None, alias="nameInDestination")
    enabled: bool | None = None
    hashed: bool | None = Field(
        default=None, description="Whether the column's values are hashed before syncing."
    )
    is_primary_key: bool | None = Field(default=None, alias="isPrimaryKey")


class TableConfig(MatiaModel):
    """Sync config for a single source table, including its column configs."""

    source_name: str | None = Field(
        default=None, description="The table's name in the source (not returned by the API)."
    )
    name_in_destination: str | None = Field(default=None, alias="nameInDestination")
    enabled: bool | None = None
    sync_mode: str | None = Field(default=None, alias="syncMode")
    cursor_field: str | None = Field(
        default=None, alias="cursorField", description="Column used for incremental sync."
    )
    columns: dict[str, ColumnConfig] = {}


class SchemaConfigEntry(MatiaModel):
    """Sync config for a single source schema, including its table configs."""

    source_name: str | None = Field(
        default=None, description="The schema's name in the source (not returned by the API)."
    )
    name_in_destination: str | None = Field(default=None, alias="nameInDestination")
    enabled: bool | None = None
    tables: dict[str, TableConfig] = {}


class IntegrationSchemaConfig(MatiaModel):
    """The full source schema config (schemas -> tables -> columns) for an integration."""

    schemas: dict[str, SchemaConfigEntry] = {}

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "IntegrationSchemaConfig":
        """Build a schema config from the API's map-of-maps shape, tagging each
        entry with the map key it came from (source_name) since the schema/
        table/column name only exists as a dict key in the API response."""
        schemas: dict[str, SchemaConfigEntry] = {}
        for schema_name, schema_val in (data.get("schemas") or {}).items():
            schema_val = schema_val or {}
            tables: dict[str, TableConfig] = {}
            for table_name, table_val in (schema_val.get("tables") or {}).items():
                table_val = table_val or {}
                columns = {
                    col_name: ColumnConfig.model_validate(
                        {**(col_val or {}), "source_name": col_name}
                    )
                    for col_name, col_val in (table_val.get("columns") or {}).items()
                }
                tables[table_name] = TableConfig.model_validate(
                    {**table_val, "source_name": table_name, "columns": columns}
                )
            schemas[schema_name] = SchemaConfigEntry.model_validate(
                {**schema_val, "source_name": schema_name, "tables": tables}
            )
        return cls(schemas=schemas)


# --- Write models (connector creation payloads) -----------------------------


class PostgresConnection(MatiaModel):
    """Postgres database connection details for a source config."""

    username: str | None = None
    password: str | None = None
    hostname: str | None = None
    port: int | None = None
    database: str | None = None
    slot: str | None = Field(default=None, description="Logical replication slot name.")
    publication: str | None = Field(default=None, description="Logical replication publication name.")


class PostgresSourceSettings(MatiaModel):
    """Postgres-specific source settings."""

    max_clients: int | None = None
    incremental_mode: str | None = None


class PostgresSourceConfig(MatiaModel):
    """The `sourceConfig` payload for a Postgres integration."""

    type: Literal["postgres"] = "postgres"
    name: str
    auth_method: str = Field(alias="authMethod")
    connection: PostgresConnection = PostgresConnection()
    connection_type: str = Field(alias="connectionType")
    owners: list[str] = Field(default=[], description="User IDs who own this source.")


class PostgresConnectorPayload(MatiaModel):
    """Request payload for creating a Postgres integration."""

    destination_id: str = Field(alias="destinationId")
    destination_schema: str = Field(alias="destinationSchema")
    replication_frequency: str = Field(alias="replicationFrequency")
    on_schema_update: str | None = Field(default=None, alias="onSchemaUpdate")
    enabled: bool = True
    source_config: PostgresSourceConfig = Field(alias="sourceConfig")
    source_settings: PostgresSourceSettings = Field(alias="sourceSettings")


class GoogleAnalytics4Connection(MatiaModel):
    """Google Analytics 4 OAuth connection details for a source config."""

    refresh_token: str | None = None
    client_id: str | None = None
    client_secret: str | None = None
    rollback: int | None = Field(
        default=None, description="Number of days of historical data to re-sync."
    )


class GoogleAnalytics4SourceSettings(MatiaModel):
    """Google Analytics 4-specific source settings."""

    account: str | None = None
    properties: list[str] = []
    custom_reports: list[str] = Field(default_factory=list, alias="customReports")


class GoogleAnalytics4SourceConfig(MatiaModel):
    """The `sourceConfig` payload for a Google Analytics 4 integration."""

    type: Literal["google_analytics_4"] = "google_analytics_4"
    name: str
    connection: GoogleAnalytics4Connection = GoogleAnalytics4Connection()
    connection_type: str = Field(alias="connectionType")
    owners: list[str] = Field(default=[], description="User IDs who own this source.")


class GoogleAnalytics4ConnectorPayload(MatiaModel):
    """Request payload for creating a Google Analytics 4 integration."""

    destination_id: str = Field(alias="destinationId")
    destination_schema: str = Field(alias="destinationSchema")
    replication_frequency: str = Field(alias="replicationFrequency")
    on_schema_update: str | None = Field(default=None, alias="onSchemaUpdate")
    enabled: bool = True
    source_config: GoogleAnalytics4SourceConfig = Field(alias="sourceConfig")
    source_settings: GoogleAnalytics4SourceSettings = Field(alias="sourceSettings")
