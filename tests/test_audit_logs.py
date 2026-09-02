import httpx


def _log(i):
    return {
        "id": f"log-{i}",
        "timestamp": "2026-01-01T00:00:00Z",
        "event": f"event-{i}",
        "actor": {"type": "user", "email": "a@example.com"},
    }


def test_list_audit_logs(mock_api, client):
    mock_api.get("/audit-logs").mock(
        return_value=httpx.Response(
            200,
            json={
                "code": "OK",
                "data": {"totalItems": 1, "items": [_log(1)]},
            },
        )
    )

    page = client.audit_logs.list(limit=10)

    assert page.total_items == 1
    assert len(page.items) == 1
    assert page.items[0].event == "event-1"
    assert page.items[0].actor.type == "user"


def test_iter_all_paginates(mock_api, client):
    def responder(request):
        offset = int(request.url.params.get("offset", "0"))
        if offset == 0:
            items = [_log(1), _log(2)]
        elif offset == 2:
            items = [_log(3)]
        else:
            items = []
        return httpx.Response(
            200, json={"code": "OK", "data": {"totalItems": 3, "items": items}}
        )

    mock_api.get("/audit-logs").mock(side_effect=responder)

    logs = list(client.audit_logs.iter_all(limit=2))

    assert [log.event for log in logs] == ["event-1", "event-2", "event-3"]
