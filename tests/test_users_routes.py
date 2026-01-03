"""
Tests for new individual-first user routes.

Tests the new /users endpoints:
- POST /users/signup - Create user profile
- GET /users/me - Get my profile
- PATCH /users/me - Update profile
- POST /users/me/household/create - Create household
- POST /users/me/household/link - Link to household
- DELETE /users/me/household - Unlink from household
- GET /users/me/household - Get my household
"""

import pytest
from app.core.firebase import db


@pytest.fixture(autouse=True)
def cleanup():
    """Clean up test data before each test."""
    # Clear users collection
    users_coll = db.collection("users")
    if hasattr(users_coll, "_docs"):
        users_coll._docs.clear()
    
    # Clear households collection
    households_coll = db.collection("households")
    if hasattr(households_coll, "_docs"):
        households_coll._docs.clear()
    
    yield


# ==================== Signup Tests ====================

def test_signup_creates_user_profile(client, set_claims):
    """Test that POST /users/signup creates a new user profile."""
    set_claims(uid="new_user_001", email="newuser@example.com")
    
    response = client.post("/users/signup", json={
        "email": "newuser@example.com",
        "first_name": "Jane",
        "last_name": "Doe",
        "address": "123 Main St",
        "lat": 30.0,
        "lng": -97.0
    })
    
    assert response.status_code == 201
    data = response.json()
    assert data["uid"] == "new_user_001"
    assert data["email"] == "newuser@example.com"
    assert data["first_name"] == "Jane"
    assert data["last_name"] == "Doe"
    assert data["household_id"] is None  # No household yet!
    assert data["discovery_opt_in"] is True  # Default
    assert data["visibility"] == "neighbors"  # Default


def test_signup_without_household(client, set_claims):
    """Test that users can sign up without creating a household."""
    set_claims(uid="single_user_002", email="single@example.com")
    
    response = client.post("/users/signup", json={
        "email": "single@example.com",
        "first_name": "Single",
        "last_name": "User"
    })
    
    assert response.status_code == 201
    data = response.json()
    assert data["household_id"] is None  # Singles don't need households


def test_signup_duplicate_returns_409(client, set_claims):
    """Test that signing up twice returns 409 Conflict."""
    set_claims(uid="duplicate_user_003", email="dup@example.com")
    
    # First signup
    response1 = client.post("/users/signup", json={
        "email": "dup@example.com",
        "first_name": "Dup",
        "last_name": "User"
    })
    assert response1.status_code == 201
    
    # Second signup (should fail)
    response2 = client.post("/users/signup", json={
        "email": "dup@example.com",
        "first_name": "Dup",
        "last_name": "User"
    })
    assert response2.status_code == 409
    assert "already exists" in response2.json()["detail"].lower()


# ==================== Get Profile Tests ====================

def test_get_my_profile(client, set_claims):
    """Test that GET /users/me returns user profile."""
    # Create user first
    set_claims(uid="profile_user_004", email="profile@example.com")
    client.post("/users/signup", json={
        "email": "profile@example.com",
        "first_name": "Profile",
        "last_name": "User"
    })
    
    # Get profile
    response = client.get("/users/me")
    assert response.status_code == 200
    data = response.json()
    assert data["uid"] == "profile_user_004"
    assert data["first_name"] == "Profile"


def test_get_profile_not_found(client, set_claims):
    """Test that GET /users/me returns 404 for non-existent user."""
    set_claims(uid="nonexistent_user_005")
    
    response = client.get("/users/me")
    assert response.status_code == 404


# ==================== Update Profile Tests ====================

def test_update_profile(client, set_claims):
    """Test that PATCH /users/me updates user profile."""
    # Create user first
    set_claims(uid="update_user_006", email="update@example.com")
    client.post("/users/signup", json={
        "email": "update@example.com",
        "first_name": "Update",
        "last_name": "User"
    })
    
    # Update profile
    response = client.patch("/users/me", json={
        "bio": "I love coding!",
        "discovery_opt_in": False
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["bio"] == "I love coding!"
    assert data["discovery_opt_in"] is False
    assert data["first_name"] == "Update"  # Unchanged


def test_update_profile_partial(client, set_claims):
    """Test that partial updates work (only provided fields updated)."""
    # Create user first
    set_claims(uid="partial_user_007", email="partial@example.com")
    client.post("/users/signup", json={
        "email": "partial@example.com",
        "first_name": "Original",
        "last_name": "Name"
    })
    
    # Update only first name
    response = client.patch("/users/me", json={
        "first_name": "Updated"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "Updated"
    assert data["last_name"] == "Name"  # Unchanged


def test_update_profile_empty_fails(client, set_claims):
    """Test that updating with no fields returns 400."""
    # Create user first
    set_claims(uid="empty_user_008", email="empty@example.com")
    client.post("/users/signup", json={
        "email": "empty@example.com",
        "first_name": "Empty",
        "last_name": "User"
    })
    
    # Try to update with no fields
    response = client.patch("/users/me", json={})
    assert response.status_code == 400


# ==================== Household Creation Tests ====================

def test_create_household(client, set_claims):
    """Test that POST /users/me/household/create creates a household."""
    # Create user first
    set_claims(uid="household_user_009", email="household@example.com")
    client.post("/users/signup", json={
        "email": "household@example.com",
        "first_name": "House",
        "last_name": "User"
    })
    
    # Create household
    response = client.post("/users/me/household/create", json={
        "name": "The Smith Family",
        "household_type": "family_with_kids",
        "kids": [
            {"age_range": "6-8", "gender": "female"},
            {"age_range": "3-5", "gender": "male"}
        ]
    })
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "The Smith Family"
    assert data["household_type"] == "family_with_kids"
    assert len(data["member_uids"]) == 1
    assert "household_user_009" in data["member_uids"]
    assert len(data["kids"]) == 2


def test_create_household_links_user(client, set_claims):
    """Test that creating a household links the user to it."""
    # Create user first
    set_claims(uid="link_user_010", email="link@example.com")
    client.post("/users/signup", json={
        "email": "link@example.com",
        "first_name": "Link",
        "last_name": "User"
    })
    
    # Create household
    household_response = client.post("/users/me/household/create", json={
        "name": "The Doe Family",
        "household_type": "family_with_kids"
    })
    household_id = household_response.json()["id"]
    
    # Check user profile is linked
    profile_response = client.get("/users/me")
    profile_data = profile_response.json()
    assert profile_data["household_id"] == household_id


def test_create_household_twice_fails(client, set_claims):
    """Test that creating a second household returns 409."""
    # Create user first
    set_claims(uid="double_household_011", email="double@example.com")
    client.post("/users/signup", json={
        "email": "double@example.com",
        "first_name": "Double",
        "last_name": "User"
    })
    
    # Create first household
    response1 = client.post("/users/me/household/create", json={
        "name": "First Household",
        "household_type": "family_with_kids"
    })
    assert response1.status_code == 201
    
    # Try to create second household (should fail)
    response2 = client.post("/users/me/household/create", json={
        "name": "Second Household",
        "household_type": "empty_nesters"
    })
    assert response2.status_code == 409


# ==================== Household Linking Tests ====================

def test_link_to_household(client, set_claims):
    """Test that POST /users/me/household/link links user to existing household."""
    # Create first user and household
    set_claims(uid="link_test_user1_012", email="user1@example.com")
    client.post("/users/signup", json={
        "email": "user1@example.com",
        "first_name": "User",
        "last_name": "One"
    })
    household_response = client.post("/users/me/household/create", json={
        "name": "Shared Household",
        "household_type": "family_with_kids"
    })
    household_id = household_response.json()["id"]
    
    # Create second user
    set_claims(uid="link_test_user2_013", email="user2@example.com")
    client.post("/users/signup", json={
        "email": "user2@example.com",
        "first_name": "User",
        "last_name": "Two"
    })
    
    # Link second user to first user's household
    response = client.post("/users/me/household/link", json={
        "household_id": household_id
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["household_id"] == household_id


def test_link_to_household_adds_member(client, set_claims):
    """Test that linking to household adds user to member_uids."""
    # Create first user and household
    set_claims(uid="member_test_user1_014", email="member1@example.com")
    client.post("/users/signup", json={
        "email": "member1@example.com",
        "first_name": "Member",
        "last_name": "One"
    })
    household_response = client.post("/users/me/household/create", json={
        "name": "Member Test Household",
        "household_type": "family_with_kids"
    })
    household_id = household_response.json()["id"]
    
    # Create second user and link
    set_claims(uid="member_test_user2_015", email="member2@example.com")
    client.post("/users/signup", json={
        "email": "member2@example.com",
        "first_name": "Member",
        "last_name": "Two"
    })
    client.post("/users/me/household/link", json={
        "household_id": household_id
    })
    
    # Check household has both members
    household_response = client.get("/users/me/household")
    household_data = household_response.json()
    assert len(household_data["member_uids"]) == 2
    assert "member_test_user1_014" in household_data["member_uids"]
    assert "member_test_user2_015" in household_data["member_uids"]


# ==================== Household Unlinking Tests ====================

def test_unlink_from_household(client, set_claims):
    """Test that DELETE /users/me/household unlinks user."""
    # Create user and household
    set_claims(uid="unlink_user_016", email="unlink@example.com")
    client.post("/users/signup", json={
        "email": "unlink@example.com",
        "first_name": "Unlink",
        "last_name": "User"
    })
    client.post("/users/me/household/create", json={
        "name": "Unlink Test Household",
        "household_type": "family_with_kids"
    })
    
    # Unlink from household
    response = client.delete("/users/me/household")
    assert response.status_code == 204
    
    # Check user profile is unlinked
    profile_response = client.get("/users/me")
    profile_data = profile_response.json()
    assert profile_data["household_id"] is None


def test_get_my_household(client, set_claims):
    """Test that GET /users/me/household returns user's household."""
    # Create user and household
    set_claims(uid="get_household_user_017", email="gethousehold@example.com")
    client.post("/users/signup", json={
        "email": "gethousehold@example.com",
        "first_name": "Get",
        "last_name": "Household"
    })
    household_response = client.post("/users/me/household/create", json={
        "name": "Get Test Household",
        "household_type": "empty_nesters"
    })
    household_id = household_response.json()["id"]
    
    # Get household
    response = client.get("/users/me/household")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == household_id
    assert data["name"] == "Get Test Household"


def test_get_household_without_link_returns_404(client, set_claims):
    """Test that GET /users/me/household returns 404 if no household."""
    # Create user without household
    set_claims(uid="no_household_user_018", email="nohousehold@example.com")
    client.post("/users/signup", json={
        "email": "nohousehold@example.com",
        "first_name": "No",
        "last_name": "Household"
    })
    
    # Try to get household (should return 404)
    response = client.get("/users/me/household")
    assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
