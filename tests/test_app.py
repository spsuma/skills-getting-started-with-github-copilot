import copy
import urllib.parse

import pytest
from httpx import Client

from src.app import app, activities

original_activities = copy.deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities():
    activities.clear()
    activities.update(copy.deepcopy(original_activities))
    yield
    activities.clear()
    activities.update(copy.deepcopy(original_activities))


@pytest.fixture
def client():
    with Client(app=app, base_url="http://testserver") as client:
        yield client


def test_get_activities(client):
    response = client.get("/activities")

    assert response.status_code == 200
    data = response.json()
    assert "Chess Club" in data
    assert data["Chess Club"]["schedule"] == "Fridays, 3:30 PM - 5:00 PM"
    assert isinstance(data["Chess Club"]["participants"], list)


def test_signup_for_activity_adds_participant(client):
    activity_name = "Chess Club"
    participant_email = "newstudent@mergington.edu"
    encoded_activity = urllib.parse.quote(activity_name, safe="")

    response = client.post(f"/activities/{encoded_activity}/signup", params={"email": participant_email})

    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {participant_email} for {activity_name}"
    assert participant_email in activities[activity_name]["participants"]


def test_signup_duplicate_returns_400(client):
    activity_name = "Chess Club"
    participant_email = "michael@mergington.edu"
    encoded_activity = urllib.parse.quote(activity_name, safe="")

    response = client.post(f"/activities/{encoded_activity}/signup", params={"email": participant_email})

    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"


def test_remove_participant(client):
    activity_name = "Chess Club"
    participant_email = "michael@mergington.edu"
    encoded_activity = urllib.parse.quote(activity_name, safe="")

    response = client.delete(f"/activities/{encoded_activity}/participants", params={"email": participant_email})

    assert response.status_code == 200
    assert response.json()["message"] == f"Removed {participant_email} from {activity_name}"
    assert participant_email not in activities[activity_name]["participants"]


def test_remove_nonexistent_participant_returns_404(client):
    activity_name = "Chess Club"
    participant_email = "ghost@mergington.edu"
    encoded_activity = urllib.parse.quote(activity_name, safe="")

    response = client.delete(f"/activities/{encoded_activity}/participants", params={"email": participant_email})

    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"
