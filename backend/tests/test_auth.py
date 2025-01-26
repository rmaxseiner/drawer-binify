def test_login(client, test_user):
    response = client.post(
        "/token",
        data={
            "username": test_user.username,
            "password": "testpass123",
            "grant_type": "password"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials(client):
    response = client.post(
        "/token",
        data={
            "username": "wronguser",
            "password": "wrongpass",
            "grant_type": "password"
        }
    )
    assert response.status_code == 401