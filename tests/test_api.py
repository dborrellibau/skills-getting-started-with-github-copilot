"""
Tests for the Mergington High School API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to initial state before each test"""
    activities.clear()
    activities.update({
        "Soccer Team": {
            "description": "Join the school soccer team and compete in inter-school matches",
            "schedule": "Tuesdays and Thursdays, 4:00 PM - 6:00 PM",
            "max_participants": 22,
            "participants": ["alex@mergington.edu", "sarah@mergington.edu"]
        },
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": []
        }
    })


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_success(self, client):
        """Test successfully retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert "Soccer Team" in data
        assert "Chess Club" in data
        assert data["Soccer Team"]["max_participants"] == 22

    def test_get_activities_contains_correct_fields(self, client):
        """Test that activities contain all required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_details in data.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self, client):
        """Test successfully signing up for an activity"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up newstudent@mergington.edu for Chess Club" in data["message"]
        
        # Verify the participant was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "newstudent@mergington.edu" in activities_data["Chess Club"]["participants"]

    def test_signup_activity_not_found(self, client):
        """Test signing up for a non-existent activity"""
        response = client.post(
            "/activities/NonExistent%20Activity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"

    def test_signup_duplicate_participant(self, client):
        """Test signing up when already registered"""
        email = "alex@mergington.edu"
        response = client.post(
            f"/activities/Soccer%20Team/signup?email={email}"
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"].lower()

    def test_signup_multiple_different_students(self, client):
        """Test that multiple students can sign up for the same activity"""
        emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        
        for email in emails:
            response = client.post(
                f"/activities/Chess%20Club/signup?email={email}"
            )
            assert response.status_code == 200
        
        # Verify all were added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        for email in emails:
            assert email in activities_data["Chess Club"]["participants"]


class TestRemoveParticipant:
    """Tests for DELETE /activities/{activity_name}/participants/{email} endpoint"""

    def test_remove_participant_success(self, client):
        """Test successfully removing a participant"""
        email = "alex@mergington.edu"
        response = client.delete(
            f"/activities/Soccer%20Team/participants/{email}"
        )
        assert response.status_code == 200
        data = response.json()
        assert f"Removed {email} from Soccer Team" in data["message"]
        
        # Verify the participant was removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email not in activities_data["Soccer Team"]["participants"]

    def test_remove_participant_activity_not_found(self, client):
        """Test removing participant from non-existent activity"""
        response = client.delete(
            "/activities/NonExistent%20Activity/participants/student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"

    def test_remove_participant_not_in_activity(self, client):
        """Test removing a participant not registered for the activity"""
        response = client.delete(
            "/activities/Chess%20Club/participants/notregistered@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_remove_and_resign_up(self, client):
        """Test removing a participant and signing them up again"""
        email = "sarah@mergington.edu"
        
        # Remove participant
        remove_response = client.delete(
            f"/activities/Soccer%20Team/participants/{email}"
        )
        assert remove_response.status_code == 200
        
        # Sign up again
        signup_response = client.post(
            f"/activities/Soccer%20Team/signup?email={email}"
        )
        assert signup_response.status_code == 200
        
        # Verify they're back in the list
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data["Soccer Team"]["participants"]


class TestRootRedirect:
    """Tests for GET / endpoint"""

    def test_root_redirects_to_static(self, client):
        """Test that root path redirects to static index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"
