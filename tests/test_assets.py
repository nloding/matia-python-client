import httpx


def test_create_asset(mock_api, client):
    route = mock_api.post("/assets").mock(
        return_value=httpx.Response(
            201,
            json={"code": "OK", "data": {"id": "a1", "name": "My Asset", "type": "table"}},
        )
    )

    asset = client.assets.create(
        "My Asset", "table", description="desc", connection_type="source"
    )

    assert route.called
    request = route.calls.last.request
    assert request.headers["x-api-key"] == "test-key"
    assert asset.id == "a1"
    assert asset.name == "My Asset"
    assert asset.type == "table"
    assert asset.description == "desc"
    assert asset.connection_type == "source"


def test_update_asset(mock_api, client):
    mock_api.patch("/assets/a1").mock(
        return_value=httpx.Response(200, json={"code": "OK", "data": {"id": "a1"}})
    )

    asset = client.assets.update("a1", name="Renamed")

    assert asset.id == "a1"
    assert asset.name == "Renamed"


def test_asset_model_update_is_fluent(mock_api, client):
    mock_api.post("/assets").mock(
        return_value=httpx.Response(
            201, json={"code": "OK", "data": {"id": "a1", "name": "A", "type": "table"}}
        )
    )
    mock_api.patch("/assets/a1").mock(
        return_value=httpx.Response(200, json={"code": "OK", "data": {"id": "a1"}})
    )

    asset = client.assets.create("A", "table")
    updated = asset.update(name="B")

    assert updated.id == "a1"
    assert updated.name == "B"
