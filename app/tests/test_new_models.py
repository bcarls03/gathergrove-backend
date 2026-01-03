"""
Tests for new individual-first data models.

Tests the UserProfile, Household, and updated Event models to ensure:
- Individual-first architecture works (users separate from households)
- Households are optional (users can exist without them)
- Events use host_user_id (not household-based)
- 8 event categories work
- Visibility and shareable_link fields work
"""

import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from app.models.user import UserProfile, UserProfileUpdate, UserSignupRequest
from app.models.household import Household, Kid, HouseholdCreate
from app.models.events import Category


# ==================== UserProfile Tests ====================

def test_user_profile_without_household():
    """Test that users can exist without households (singles/couples)."""
    user = UserProfile(
        uid="user_123",
        email="jane@email.com",
        first_name="Jane",
        last_name="Doe",
        address="123 Main St",
        lat=30.0,
        lng=-97.0,
        household_id=None  # No household - this is valid!
    )
    
    assert user.uid == "user_123"
    assert user.email == "jane@email.com"
    assert user.first_name == "Jane"
    assert user.last_name == "Doe"
    assert user.household_id is None  # Singles don't need households!
    assert user.discovery_opt_in is True  # Default
    assert user.visibility == "neighbors"  # Default


def test_user_profile_with_household():
    """Test that users can optionally link to households."""
    user = UserProfile(
        uid="user_456",
        email="sarah@email.com",
        first_name="Sarah",
        last_name="Smith",
        household_id="household_abc"  # Optional linking
    )
    
    assert user.household_id == "household_abc"
    assert user.uid == "user_456"


def test_user_profile_defaults():
    """Test that UserProfile has correct default values."""
    user = UserProfile(
        uid="user_789",
        email="test@email.com",
        first_name="Test",
        last_name="User"
    )
    
    # Check defaults
    assert user.discovery_opt_in is True
    assert user.visibility == "neighbors"
    assert user.household_id is None
    assert user.profile_photo_url is None
    assert user.bio is None
    assert isinstance(user.created_at, datetime)
    assert isinstance(user.updated_at, datetime)


def test_user_profile_visibility_options():
    """Test all three visibility options work."""
    user_private = UserProfile(
        uid="u1", email="u1@test.com", first_name="U", last_name="One",
        visibility="private"
    )
    user_neighbors = UserProfile(
        uid="u2", email="u2@test.com", first_name="U", last_name="Two",
        visibility="neighbors"
    )
    user_public = UserProfile(
        uid="u3", email="u3@test.com", first_name="U", last_name="Three",
        visibility="public"
    )
    
    assert user_private.visibility == "private"
    assert user_neighbors.visibility == "neighbors"
    assert user_public.visibility == "public"


def test_user_profile_invalid_visibility():
    """Test that invalid visibility values are rejected."""
    with pytest.raises(ValidationError):
        UserProfile(
            uid="u1", email="u1@test.com", first_name="U", last_name="One",
            visibility="invalid"  # Should fail
        )


def test_user_profile_with_interests():
    """Test that users can have interests list."""
    user = UserProfile(
        uid="user_123",
        email="test@email.com",
        first_name="Test",
        last_name="User",
        interests=["hiking", "cooking", "board_games"]
    )
    
    assert user.interests == ["hiking", "cooking", "board_games"]
    assert len(user.interests) == 3


def test_user_signup_request():
    """Test UserSignupRequest validation."""
    signup = UserSignupRequest(
        email="newuser@email.com",
        first_name="New",
        last_name="User",
        address="456 Elm St",
        lat=30.2672,
        lng=-97.7431
    )
    
    assert signup.email == "newuser@email.com"
    assert signup.first_name == "New"
    assert signup.last_name == "User"


def test_user_profile_update():
    """Test that UserProfileUpdate allows partial updates."""
    update = UserProfileUpdate(
        first_name="Updated",
        bio="New bio",
        discovery_opt_in=False
    )
    
    assert update.first_name == "Updated"
    assert update.bio == "New bio"
    assert update.discovery_opt_in is False
    # Other fields should be None (not provided)
    assert update.last_name is None
    assert update.address is None


# ==================== Household Tests ====================

def test_household_multiple_members():
    """Test that households can have multiple adult members."""
    household = Household(
        id="household_xyz",
        name="The Smith Family",
        member_uids=["user_sarah_123", "user_mike_456"],  # Two adults
        household_type="family_with_kids",
        kids=[
            Kid(age_range="6-8", gender="female"),
            Kid(age_range="3-5", gender="male")
        ]
    )
    
    assert len(household.member_uids) == 2
    assert "user_sarah_123" in household.member_uids
    assert "user_mike_456" in household.member_uids
    assert household.name == "The Smith Family"
    assert len(household.kids) == 2


def test_household_single_member():
    """Test that households can have just one member (single parent)."""
    household = Household(
        id="household_abc",
        name="The Doe Household",
        member_uids=["user_jane_789"],  # Single parent
        household_type="family_with_kids",
        kids=[Kid(age_range="6-8")]
    )
    
    assert len(household.member_uids) == 1
    assert household.member_uids[0] == "user_jane_789"


def test_household_no_kids():
    """Test that households can exist without kids (empty nesters)."""
    household = Household(
        id="household_empty",
        name="The Johnson Family",
        member_uids=["user_john_111", "user_mary_222"],
        household_type="empty_nesters",
        kids=None  # No kids
    )
    
    assert household.kids is None
    assert household.household_type == "empty_nesters"


def test_household_types():
    """Test all three household types."""
    family = Household(
        id="h1", name="Family", member_uids=["u1"],
        household_type="family_with_kids"
    )
    empty = Household(
        id="h2", name="Empty", member_uids=["u2"],
        household_type="empty_nesters"
    )
    singles = Household(
        id="h3", name="Singles", member_uids=["u3"],
        household_type="singles_couples"
    )
    
    assert family.household_type == "family_with_kids"
    assert empty.household_type == "empty_nesters"
    assert singles.household_type == "singles_couples"


def test_kid_model():
    """Test Kid model with all fields."""
    kid = Kid(
        age_range="6-8",
        gender="female",
        interests=["soccer", "art"],
        available_for_babysitting=False
    )
    
    assert kid.age_range == "6-8"
    assert kid.gender == "female"
    assert kid.interests == ["soccer", "art"]
    assert kid.available_for_babysitting is False


def test_kid_babysitting_opt_in():
    """Test that kids can opt-in to babysitting (for teens)."""
    kid_babysitter = Kid(
        age_range="13-17",
        gender="female",
        interests=["reading", "crafts"],
        available_for_babysitting=True  # Teen babysitter
    )
    
    kid_not_babysitter = Kid(
        age_range="6-8",
        gender="male",
        available_for_babysitting=False  # Default for younger kids
    )
    
    assert kid_babysitter.available_for_babysitting is True
    assert kid_not_babysitter.available_for_babysitting is False


def test_kid_age_ranges():
    """Test all valid kid age ranges."""
    age_ranges = ["0-2", "3-5", "6-8", "9-12", "13-17", "18+"]
    
    for age_range in age_ranges:
        kid = Kid(age_range=age_range)
        assert kid.age_range == age_range


def test_household_create():
    """Test HouseholdCreate request model."""
    create_req = HouseholdCreate(
        name="The New Family",
        household_type="family_with_kids",
        kids=[Kid(age_range="6-8", gender="female")]
    )
    
    assert create_req.name == "The New Family"
    assert create_req.household_type == "family_with_kids"
    assert len(create_req.kids) == 1


# ==================== Event Model Tests ====================

def test_event_eight_categories():
    """Test that all 8 categories are valid."""
    # Import the Category type to verify all options
    categories = [
        "neighborhood", "playdate", "help", "pet",
        "food", "celebrations", "sports", "other"
    ]
    
    # This test verifies the Category Literal has all 8 options
    # by checking the type annotation
    import typing
    category_args = typing.get_args(Category)
    
    assert len(category_args) == 8
    for cat in categories:
        assert cat in category_args


def test_new_event_categories():
    """Test that new categories (food, celebrations, sports) work."""
    from app.models.events import EventCreate
    
    # Test food category
    event_food = EventCreate(
        title="Potluck Dinner",
        category="food",
        start=datetime.now(timezone.utc),
        end=datetime.now(timezone.utc),
        neighborhood="Bayhill"
    )
    assert event_food.category == "food"
    
    # Test celebrations category
    event_celebration = EventCreate(
        title="Birthday Party",
        category="celebrations",
        start=datetime.now(timezone.utc),
        end=datetime.now(timezone.utc),
        neighborhood="Bayhill"
    )
    assert event_celebration.category == "celebrations"
    
    # Test sports category
    event_sports = EventCreate(
        title="Pickup Basketball",
        category="sports",
        start=datetime.now(timezone.utc),
        end=datetime.now(timezone.utc),
        neighborhood="Bayhill"
    )
    assert event_sports.category == "sports"


def test_event_visibility_options():
    """Test that event visibility field has correct options."""
    from app.models.events import EventCreate
    
    now = datetime.now(timezone.utc)
    
    event_private = EventCreate(
        title="Private Event",
        category="other",
        start=now,
        end=now,
        neighborhood="Test",
        visibility="private"
    )
    
    event_link_only = EventCreate(
        title="Link-Only Event",
        category="other",
        start=now,
        end=now,
        neighborhood="Test",
        visibility="link_only"
    )
    
    event_public = EventCreate(
        title="Public Event",
        category="other",
        start=now,
        end=now,
        neighborhood="Test",
        visibility="public"
    )
    
    assert event_private.visibility == "private"
    assert event_link_only.visibility == "link_only"
    assert event_public.visibility == "public"


def test_event_default_visibility():
    """Test that events default to private visibility."""
    from app.models.events import EventCreate
    
    event = EventCreate(
        title="Test Event",
        category="other",
        start=datetime.now(timezone.utc),
        end=datetime.now(timezone.utc),
        neighborhood="Test"
        # visibility not specified - should default to "private"
    )
    
    assert event.visibility == "private"


# ==================== Integration Tests ====================

def test_user_household_relationship():
    """Test that users can link to households and households track members."""
    # Create a household
    household = Household(
        id="household_integration_test",
        name="The Test Family",
        member_uids=["user_a", "user_b"],
        household_type="family_with_kids"
    )
    
    # Create users that link to this household
    user_a = UserProfile(
        uid="user_a",
        email="usera@test.com",
        first_name="User",
        last_name="A",
        household_id="household_integration_test"
    )
    
    user_b = UserProfile(
        uid="user_b",
        email="userb@test.com",
        first_name="User",
        last_name="B",
        household_id="household_integration_test"
    )
    
    # Verify relationship
    assert user_a.household_id == household.id
    assert user_b.household_id == household.id
    assert user_a.uid in household.member_uids
    assert user_b.uid in household.member_uids


def test_single_user_no_household():
    """Test that single users work without any household."""
    user = UserProfile(
        uid="single_user_123",
        email="single@test.com",
        first_name="Single",
        last_name="User",
        household_id=None,  # No household
        discovery_opt_in=True,
        visibility="neighbors"
    )
    
    # Single user should work perfectly fine
    assert user.household_id is None
    assert user.discovery_opt_in is True
    assert user.visibility == "neighbors"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
