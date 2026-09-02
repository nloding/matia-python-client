import httpx


def _integration(id="i1", **overrides):
    data = {
        "id": id,
        "name": "My Integration",
        "createdAt": "2026-01-01T00:00:00Z",
        "paused": False,
        "source": {"id": "s1", "name": "Source", "type": "postgres"},
        "destination": {"id": "d1", "name": "Dest", "type": "snowflake"},
        "latestRunId": None,
    }
    data.update(overrides)
    return data


def test_list_integrations(mock_api, client):
    mock_api.get("/integrations").mock(
        return_value=httpx.Response(
            200, json={"code": "OK", "data": {"items": [_integration()]}}
        )
    )

    integrations = client.integrations.list()

    assert len(integrations) == 1
    assert integrations[0].id == "i1"
    assert integrations[0].source.type == "postgres"


def test_get_integration(mock_api, client):
    mock_api.get("/integrations/i1").mock(
        return_value=httpx.Response(
            200, json={"code": "OK", "data": {"integration": _integration()}}
        )
    )

    integration = client.integrations.get("i1")

    assert integration.id == "i1"
    assert integration.name == "My Integration"


def test_run_refetches_integration(mock_api, client):
    mock_api.post("/integrations/i1/run").mock(
        return_value=httpx.Response(
            200, json={"code": "OK", "message": "started", "data": {"id": "i1"}}
        )
    )
    mock_api.get("/integrations/i1").mock(
        return_value=httpx.Response(
            200,
            json={
                "code": "OK",
                "data": {"integration": _integration(latestRunId="run-1")},
            },
        )
    )

    integration = client.integrations.run("i1")

    assert integration.id == "i1"
    assert integration.latest_run_id == "run-1"


def test_get_run(mock_api, client):
    mock_api.get("/integrations/i1/runs/run-1").mock(
        return_value=httpx.Response(
            200,
            json={
                "code": "OK",
                "data": {
                    "id": "run-1",
                    "integrationId": "i1",
                    "status": "completed",
                    "committedRecords": 100,
                    "emittedRecords": 100,
                    "size": 2048,
                },
            },
        )
    )

    run = client.integrations.get_run("i1", "run-1")

    assert run.id == "run-1"
    assert run.status == "completed"
    assert run.committed_records == 100


def test_schema_config_round_trip(mock_api, client):
    mock_api.get("/integrations/i1/schemas").mock(
        return_value=httpx.Response(
            200,
            json={
                "code": "OK",
                "data": {
                    "schemas": {
                        "public": {
                            "enabled": True,
                            "tables": {
                                "users": {
                                    "enabled": True,
                                    "syncMode": "incremental",
                                    "columns": {
                                        "id": {"enabled": True, "isPrimaryKey": True}
                                    },
                                }
                            },
                        }
                    }
                },
            },
        )
    )

    config = client.integrations.get_schema_config("i1")

    schema = config.schemas["public"]
    assert schema.source_name == "public"
    assert schema.enabled is True
    table = schema.tables["users"]
    assert table.source_name == "users"
    assert table.sync_mode == "incremental"
    column = table.columns["id"]
    assert column.source_name == "id"
    assert column.is_primary_key is True


def test_get_table_columns(mock_api, client):
    mock_api.get("/integrations/i1/schemas/public/tables/users/columns").mock(
        return_value=httpx.Response(
            200,
            json={
                "code": "OK",
                "data": {
                    "columns": {
                        "id": {"enabled": True, "isPrimaryKey": True},
                        "email": {"enabled": True, "hashed": True},
                    }
                },
            },
        )
    )

    columns = client.integrations.get_table_columns("i1", "public", "users")

    assert {c.source_name for c in columns} == {"id", "email"}
    hashed = next(c for c in columns if c.source_name == "email")
    assert hashed.hashed is True


def test_postgres_builder_creates_integration(mock_api, client):
    create_route = mock_api.post("/integrations").mock(
        return_value=httpx.Response(
            201, json={"code": "OK", "message": "created", "data": {"id": "i2"}}
        )
    )
    mock_api.get("/integrations/i2").mock(
        return_value=httpx.Response(
            200, json={"code": "OK", "data": {"integration": _integration(id="i2")}}
        )
    )

    integration = (
        client.integrations.postgres()
        .name("Prod PG")
        .destination(destination_id="dest-1", destination_schema="public")
        .replication_frequency("1h")
        .auth_method("password")
        .connection(username="u", password="p", hostname="h", port=5432, database="db")
        .connection_type("database")
        .owners(["user-1"])
        .source_settings(max_clients=10, incremental_mode="cursor")
        .create()
    )

    assert integration.id == "i2"
    sent_body = create_route.calls.last.request.content
    import json

    body = json.loads(sent_body)
    assert body["sourceConfig"]["type"] == "postgres"
    assert body["sourceConfig"]["connection"]["hostname"] == "h"
    assert body["destinationId"] == "dest-1"


def test_google_analytics_4_builder_creates_integration(mock_api, client):
    create_route = mock_api.post("/integrations").mock(
        return_value=httpx.Response(
            201, json={"code": "OK", "message": "created", "data": {"id": "i3"}}
        )
    )
    mock_api.get("/integrations/i3").mock(
        return_value=httpx.Response(
            200, json={"code": "OK", "data": {"integration": _integration(id="i3")}}
        )
    )

    integration = (
        client.integrations.google_analytics_4()
        .name("GA4 Prod")
        .destination(destination_id="dest-1", destination_schema="public")
        .replication_frequency("1d")
        .connection(refresh_token="rt", client_id="cid", client_secret="secret")
        .connection_type("oauth")
        .owners(["user-1"])
        .source_settings(account="123", properties=["p1"], custom_reports=["r1"])
        .create()
    )

    assert integration.id == "i3"
    import json

    body = json.loads(create_route.calls.last.request.content)
    assert body["sourceConfig"]["type"] == "google_analytics_4"
    assert body["sourceSettings"]["customReports"] == ["r1"]
