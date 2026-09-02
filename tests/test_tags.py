import httpx

from matia import MatiaBadRequestError


def test_create_and_assign_tag(mock_api, client):
    mock_api.post("/tags").mock(
        return_value=httpx.Response(200, json={"code": "OK", "data": {"id": "t1"}})
    )
    mock_api.post("/tags/t1/relation").mock(
        return_value=httpx.Response(200, json={"code": "OK", "message": "assigned"})
    )

    tag = client.tags.create("pii", "user-1", description="sensitive")
    assert tag.id == "t1"
    assert tag.name == "pii"

    tag.assign(resource_id="asset-1", resource_type="DataAsset", tagged_by="user-1")

    relation_request = mock_api.calls.last.request
    assert relation_request.url.path == "/v1/tags/t1/relation"


def test_delete_tag(mock_api, client):
    mock_api.delete("/tags/t1").mock(
        return_value=httpx.Response(200, json={"code": "OK", "message": "deleted"})
    )

    client.tags.delete("t1")

    assert mock_api.calls.last.request.method == "DELETE"


def test_bad_request_raises_typed_error(mock_api, client):
    mock_api.post("/tags").mock(
        return_value=httpx.Response(
            400, json={"code": "BAD_REQUEST", "message": "name is required"}
        )
    )

    try:
        client.tags.create("", "user-1")
        assert False, "expected MatiaBadRequestError"
    except MatiaBadRequestError as exc:
        assert exc.status_code == 400
        assert exc.code == "BAD_REQUEST"
        assert exc.message == "name is required"
