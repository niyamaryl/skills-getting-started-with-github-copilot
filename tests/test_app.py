import copy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture(autouse=True)
def reset_activities():
    # Arrange: snapshot and restore in-memory activities to prevent test leakage
    original = copy.deepcopy(app_module.activities)
    app_module.activities = copy.deepcopy(original)
    yield
    app_module.activities = copy.deepcopy(original)


@pytest.fixture()
def client():
    # Arrange: provide a test client for each test
    with TestClient(app_module.app) as c:
        yield c


def test_list_activities_returns_catalog(client):
    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, dict)
    assert "Chess Club" in payload


def test_signup_for_activity_adds_participant(client):
    # Arrange
    email = "newstudent@mergington.edu"

    # Act
    response = client.post(f"/activities/{quote('Chess Club')}/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Chess Club"}

    activities = client.get("/activities").json()
    assert email in activities["Chess Club"]["participants"]


def test_duplicate_signup_is_rejected(client):
    # Arrange
    email = "duplicate@mergington.edu"

    # Act
    first = client.post(f"/activities/{quote('Chess Club')}/signup", params={"email": email})
    second = client.post(f"/activities/{quote('Chess Club')}/signup", params={"email": email})

    # Assert
    assert first.status_code == 200
    assert second.status_code == 400
    assert second.json() == {"detail": "Student is already signed up for this activity"}


def test_unregister_participant_removes_email_from_activity(client):
    # Arrange
    email = "teststudent@mergington.edu"
    signup = client.post(f"/activities/{quote('Chess Club')}/signup", params={"email": email})
    assert signup.status_code == 200

    # Act
    resp = client.delete(f"/activities/{quote('Chess Club')}/participants/{quote(email)}")

    # Assert
    assert resp.status_code == 200
    assert resp.json() == {"message": f"Unregistered {email} from Chess Club"}

    activities = client.get("/activities").json()
    assert email not in activities["Chess Club"]["participants"]
