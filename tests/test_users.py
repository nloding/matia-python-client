import httpx


def test_list_users(mock_api, client):
    mock_api.get("/users").mock(
        return_value=httpx.Response(
            200,
            json={
                "code": "OK",
                "data": {
                    "items": [
                        {
                            "id": "u1",
                            "email": "a@example.com",
                            "name": "Alice",
                            "createdAt": "2026-01-01T00:00:00Z",
                        }
                    ]
                },
            },
        )
    )

    users = client.users.list()

    assert len(users) == 1
    assert users[0].id == "u1"
    assert users[0].email == "a@example.com"
    assert users[0].name == "Alice"
