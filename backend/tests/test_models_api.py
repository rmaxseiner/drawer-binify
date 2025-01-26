def test_get_models(client, test_user):
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

    # Test models list endpoint
    response = client.get(
        "/models/",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_delete_model(client, test_user):
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

    # First generate a model
    gen_response = client.post(
        "/generate/bin/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "width": 42.0,
            "depth": 42.0,
            "height": 30.0
        }
    )

    # Get models list
    models_response = client.get(
        "/models/",
        headers={"Authorization": f"Bearer {token}"}
    )
    models = models_response.json()

    if models:
        model_id = models[0]["id"]
        # Test delete endpoint
        delete_response = client.delete(
            f"/models/{model_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert delete_response.status_code == 200
        data = delete_response.json()
        assert data["message"] == "Model deleted successfully"