# Quickstart

## Install

```bash
poetry add matia-client
```

## Create a client

```python
from matia import MatiaClient

client = MatiaClient(api_key="...")
```

## Resource managers

```python
integrations = client.integrations.list()
tag = client.tags.create(name="pii", owner="user-123")
```

## Fluent model methods

Models returned from calls carry action methods back to the API, so you don't
always need to go back through `client.<resource>`:

```python
tag.assign(resource_id="asset-123", resource_type="DataAsset", tagged_by="user-123")

integration = client.integrations.get("integration-123")
integration.run()
```

## Chainable connector builder

Creating an integration involves a deeply nested, source-specific payload, so
`client.integrations.postgres()` and `client.integrations.google_analytics_4()`
return a chainable builder instead of one long argument list:

```python
integration = (
    client.integrations.postgres()
    .name("Prod Postgres")
    .destination(destination_id="dest-1", destination_schema="public")
    .replication_frequency("1h")
    .auth_method("password")
    .connection(username="user", password="pass", hostname="db.internal", port=5432, database="app")
    .connection_type("database")
    .owners(["user-123"])
    .source_settings(max_clients=10, incremental_mode="cursor")
    .create()
)
```

## Auto-pagination

```python
for log in client.audit_logs.iter_all():
    print(log.event)
```

See the [API Reference](reference/client.md) for the full method list on each resource.
