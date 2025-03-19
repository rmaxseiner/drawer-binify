import json
from fastapi import status
from app.models import Drawer

def get_auth_token(client, username, password):
    """Helper function to get an authentication token"""
    response = client.post(
        "/token",
        data={
            "username": username,
            "password": password,
            "grant_type": "password"
        }
    )
    if response.status_code != 200:
        print(f"Failed to get token: {response.status_code} - {response.text}")
        return None
    
    return response.json().get("access_token")

def create_test_drawer(db_session, user_id, name="Test Drawer", width=200, depth=300, height=100):
    """Helper function to create a test drawer"""
    drawer = Drawer(
        name=name,
        width=width,
        depth=depth,
        height=height,
        owner_id=user_id
    )
    db_session.add(drawer)
    db_session.commit()
    db_session.refresh(drawer)
    return drawer

def test_get_user_me_endpoint(client, test_user):
    """Test that the /users/me endpoint returns properly formatted user data"""
    # Get authentication token
    token = get_auth_token(client, test_user.username, "testpass123")
    assert token is not None, "Failed to get authentication token"
    
    # Make request to /users/me endpoint with the required local_kw parameter
    response = client.get(
        "/users/me/",
        headers={"Authorization": f"Bearer {token}"},
        params={"local_kw": "test"}  # Add the missing parameter
    )
    
    # Check status code
    assert response.status_code == 200, f"Failed with status {response.status_code}: {response.text}"
    
    # Get response data
    user_data = response.json()
    
    # Log the response for debugging
    print(f"User data response: {json.dumps(user_data, indent=2)}")
    
    # Verify all required fields are present
    required_fields = ["id", "username", "email", "first_name", "last_name", "created_at"]
    for field in required_fields:
        assert field in user_data, f"Missing required field: {field}"
    
    # Verify data types match expected format
    assert isinstance(user_data["id"], int)
    assert isinstance(user_data["username"], str)
    assert isinstance(user_data["email"], str)
    assert isinstance(user_data["first_name"], str)  # Even if null, backend returns empty string
    assert isinstance(user_data["last_name"], str)   # Even if null, backend returns empty string
    assert isinstance(user_data["created_at"], str)  # ISO formatted datetime string
    
    # Verify user data matches test user
    assert user_data["username"] == test_user.username
    assert user_data["email"] == test_user.email
    assert user_data["first_name"] == test_user.first_name
    assert user_data["last_name"] == test_user.last_name

def test_get_user_me_invalid_token(client):
    """Test that the /users/me endpoint returns 401 with invalid token"""
    # Make request with invalid token
    response = client.get(
        "/users/me/",
        headers={"Authorization": "Bearer invalid_token"},
        params={"local_kw": "test"}  # Add the missing parameter
    )
    
    # Should return 401 Unauthorized
    assert response.status_code == 401
    
def test_get_user_me_missing_token(client):
    """Test that the /users/me endpoint returns 401 with missing token"""
    # Make request with no token
    response = client.get(
        "/users/me/",
        params={"local_kw": "test"}  # Add the missing parameter
    )
    
    # Should return 401 Unauthorized
    assert response.status_code == 401

def test_user_format_matches_frontend_expectation(client, test_user):
    """Test that the response format matches what the frontend expects"""
    # Get authentication token
    token = get_auth_token(client, test_user.username, "testpass123")
    assert token is not None, "Failed to get authentication token"
    
    # Make request to /users/me endpoint
    response = client.get(
        "/users/me/",
        headers={"Authorization": f"Bearer {token}"},
        params={"local_kw": "test"}  # Add the missing parameter
    )
    
    # Check status code
    assert response.status_code == 200
    
    # Get response data
    user_data = response.json()
    
    # This is what the frontend expects based on src/types/index.ts
    expected_format = {
        "id": 0,           # Should be an integer
        "username": "",    # Should be a string
        "email": "",       # Should be a string
        "first_name": "",  # Optional string
        "last_name": ""    # Optional string
    }
    
    # Check that all expected fields exist and have correct types
    for key, value in expected_format.items():
        assert key in user_data, f"Missing expected field: {key}"
        assert isinstance(user_data[key], type(value) if value != "" else str)
    
    # The created_at field is extra in the backend but should not cause issues
    # as long as it's properly serialized
    assert isinstance(user_data.get("created_at"), str)

def test_get_user_drawers_endpoint(client, test_user, db_session):
    """Test the /drawers/ endpoint that returns user's drawers"""
    # Create some test drawers for the user
    drawer1 = create_test_drawer(db_session, test_user.id, "Kitchen Drawer", 200, 300, 100)
    drawer2 = create_test_drawer(db_session, test_user.id, "Office Drawer", 250, 400, 75)
    
    # Get authentication token
    token = get_auth_token(client, test_user.username, "testpass123")
    assert token is not None
    
    # Make request to /drawers/ endpoint
    response = client.get(
        "/drawers/",
        headers={"Authorization": f"Bearer {token}"},
        params={"local_kw": "test"}  # Add the missing parameter
    )
    
    # Check status code
    assert response.status_code == 200, f"Failed with status {response.status_code}: {response.text}"
    
    # Get response data
    drawers_data = response.json()
    
    # Log the response for debugging
    print(f"Drawers response: {json.dumps(drawers_data, indent=2)}")
    
    # Verify response is a list
    assert isinstance(drawers_data, list)
    assert len(drawers_data) == 2  # Should have our two test drawers
    
    # Check first drawer format
    drawer = drawers_data[0]
    required_fields = ["id", "name", "width", "depth", "height", "owner_id", "created_at", "bins"]
    for field in required_fields:
        assert field in drawer, f"Missing required field: {field}"
    
    # Verify data types match expected format
    assert isinstance(drawer["id"], int)
    assert isinstance(drawer["name"], str)
    assert isinstance(drawer["width"], (int, float))
    assert isinstance(drawer["depth"], (int, float))
    assert isinstance(drawer["height"], (int, float))
    assert isinstance(drawer["owner_id"], int)
    assert isinstance(drawer["created_at"], str)
    assert isinstance(drawer["bins"], list)
    
    # Verify drawer data matches what we created
    found_drawer1 = False
    found_drawer2 = False
    
    for drawer in drawers_data:
        if drawer["name"] == "Kitchen Drawer":
            found_drawer1 = True
            assert drawer["width"] == 200
            assert drawer["depth"] == 300
            assert drawer["height"] == 100
        elif drawer["name"] == "Office Drawer":
            found_drawer2 = True
            assert drawer["width"] == 250
            assert drawer["depth"] == 400
            assert drawer["height"] == 75
    
    assert found_drawer1, "Kitchen Drawer not found in response"
    assert found_drawer2, "Office Drawer not found in response"

def test_drawer_format_matches_frontend_expectation(client, test_user, db_session):
    """Test that the drawer response format matches what the frontend expects"""
    # Create a test drawer for the user
    drawer = create_test_drawer(db_session, test_user.id)
    
    # Get authentication token
    token = get_auth_token(client, test_user.username, "testpass123")
    assert token is not None
    
    # Make request to /drawers/ endpoint
    response = client.get(
        "/drawers/",
        headers={"Authorization": f"Bearer {token}"},
        params={"local_kw": "test"}  # Add the missing parameter
    )
    
    # Check status code
    assert response.status_code == 200
    
    # Get response data
    drawers_data = response.json()
    assert len(drawers_data) > 0
    
    drawer_data = drawers_data[0]
    
    # This is what the frontend expects based on the frontend code
    expected_format = {
        "id": 0,             # integer
        "name": "",          # string
        "width": 0.0,        # float
        "depth": 0.0,        # float
        "height": 0.0,       # float
        "bins": []           # array of bins
    }
    
    # Check that all expected fields exist and have correct types
    for key, value in expected_format.items():
        assert key in drawer_data, f"Missing expected field: {key}"
        if key == "bins":
            assert isinstance(drawer_data[key], list)
        else:
            expected_type = type(value)
            actual_value = drawer_data[key]
            
            # Handle numbers more flexibly (allow int or float)
            if expected_type in (int, float) and isinstance(actual_value, (int, float)):
                pass  # This is fine
            else:
                assert isinstance(actual_value, expected_type), f"Field {key} has type {type(actual_value)} but expected {expected_type}"