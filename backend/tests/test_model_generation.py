def test_generate_bin(client, test_user):
    # Login first to get token
    login_response = client.post(
        "/token",
        data={
            "username": test_user.username,
            "password": "testpass123",
            "grant_type": "password"
        }
    )
    token = login_response.json()["access_token"]

    # Test bin generation
    response = client.post(
        "/generate/bin/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "width": 42.0,
            "depth": 42.0,
            "height": 30.0
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "file_path" in data


def test_generate_baseplate(client, test_user):
    # Login first
    login_response = client.post(
        "/token",
        data={
            "username": test_user.username,
            "password": "testpass123",
            "grant_type": "password"
        }
    )
    token = login_response.json()["access_token"]

    # Test baseplate generation
    response = client.post(
        "/generate/baseplate/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "width": 84.0,
            "depth": 84.0,
            "height": 0.0
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "file_path" in data