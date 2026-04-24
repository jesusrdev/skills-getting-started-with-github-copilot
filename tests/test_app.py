import pytest
import copy
from fastapi.testclient import TestClient
import src.app as app_module


@pytest.fixture
def client():
    # Arrange: Create a deep copy of the original activities for reset
    original_activities = copy.deepcopy(app_module.activities)
    client = TestClient(app_module.app, follow_redirects=True)
    yield client
    # Teardown: Reset activities to original state
    app_module.activities = original_activities


def test_root_redirect(client):
    # Arrange: No special setup needed

    # Act: Make GET request to root
    response = client.get("/")

    # Assert: Should follow redirect to /static/index.html and return 200 with html content
    assert response.status_code == 200
    assert "html" in response.text.lower()


def test_get_activities(client):
    # Arrange: No special setup needed

    # Act: Make GET request to /activities
    response = client.get("/activities")

    # Assert: Should return 200 and the activities dict
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "Basketball" in data
    assert data["Basketball"]["description"] == "Team sport focusing on basketball skills and competitive play"


def test_signup_success(client):
    # Arrange: Choose an activity with space
    activity_name = "Tennis Club"
    email = "newstudent@mergington.edu"

    # Act: Make POST request to signup
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert: Should return 200 and success message
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert f"Signed up {email} for {activity_name}" in data["message"]
    # Verify the email was added
    assert email in app_module.activities[activity_name]["participants"]


def test_signup_activity_not_found(client):
    # Arrange: Use a non-existent activity
    activity_name = "NonExistentActivity"
    email = "student@mergington.edu"

    # Act: Make POST request to signup
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert: Should return 404 with error message
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "Activity not found" in data["detail"]


def test_signup_already_registered(client):
    # Arrange: Use an activity where the email is already registered
    activity_name = "Basketball"
    email = "alex@mergington.edu"  # Already in participants

    # Act: Make POST request to signup
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert: Should return 400 with error message
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Already registered" in data["detail"]


def test_signup_activity_full(client):
    # Arrange: Find an activity and fill it up
    activity_name = "Tennis Club"
    max_participants = app_module.activities[activity_name]["max_participants"]
    # Add participants until full
    for i in range(max_participants - len(app_module.activities[activity_name]["participants"])):
        email = f"extra{i}@mergington.edu"
        app_module.activities[activity_name]["participants"].append(email)
    # Now try to add one more
    email = "overflow@mergington.edu"

    # Act: Make POST request to signup
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert: Should return 400 with error message
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Activity full" in data["detail"]


def test_unregister_success(client):
    # Arrange: Choose an activity and an email that's registered
    activity_name = "Art Studio"
    email = "grace@mergington.edu"  # Already registered

    # Act: Make DELETE request to unregister
    response = client.delete(f"/activities/{activity_name}/unregister", params={"email": email})

    # Assert: Should return 200 and success message
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert f"Unregistered {email} from {activity_name}" in data["message"]
    # Verify the email was removed
    assert email not in app_module.activities[activity_name]["participants"]


def test_unregister_activity_not_found(client):
    # Arrange: Use a non-existent activity
    activity_name = "NonExistentActivity"
    email = "student@mergington.edu"

    # Act: Make DELETE request to unregister
    response = client.delete(f"/activities/{activity_name}/unregister", params={"email": email})

    # Assert: Should return 404 with error message
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "Activity not found" in data["detail"]


def test_unregister_not_registered(client):
    # Arrange: Use an activity and an email not registered
    activity_name = "Music Ensemble"
    email = "notregistered@mergington.edu"

    # Act: Make DELETE request to unregister
    response = client.delete(f"/activities/{activity_name}/unregister", params={"email": email})

    # Assert: Should return 400 with error message
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Participant not found" in data["detail"]