import pytest
from fastapi.testclient import TestClient


def helper_create_rule(client: TestClient, auth_token: str):
    response = client.post(
        "/api/rules",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "name": "Test Rule",
            "dataset_type": "sales",
            "field_name": "amount",
            "rule_type": "NOT_NULL",
            "severity": "HIGH",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Rule"
    assert "id" in data
    assert data["created_by"] is not None
    return data["id"]


def test_create_rule(client: TestClient, auth_token: str):
    helper_create_rule(client, auth_token)


def test_update_rule_as_owner(client: TestClient, auth_token: str):
    # First create
    rule_id = helper_create_rule(client, auth_token)

    # Then update
    response = client.patch(
        f"/api/rules/{rule_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"name": "Updated Rule Name"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Rule Name"


def test_update_rule_as_admin(client: TestClient, auth_token: str, admin_token: str):
    rule_id = helper_create_rule(client, auth_token)

    response = client.patch(
        f"/api/rules/{rule_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"severity": "LOW"},
    )
    assert response.status_code == 200
    assert response.json()["severity"] == "LOW"


def test_update_rule_as_non_owner(client: TestClient, auth_token: str):
    # Rule created by auth_token owner
    rule_id = helper_create_rule(client, auth_token)

    # Create another user and get token
    res = client.post(
        "/api/auth/register",
        json={"email": "other@req.com", "password": "pass", "full_name": "Other"},
    )
    other_token = res.json()["access_token"]

    response = client.patch(
        f"/api/rules/{rule_id}",
        headers={"Authorization": f"Bearer {other_token}"},
        json={"severity": "LOW"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized to update this rule"


def test_delete_rule_as_owner(client: TestClient, auth_token: str):
    rule_id = helper_create_rule(client, auth_token)

    response = client.delete(
        f"/api/rules/{rule_id}", headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 204


def test_delete_rule_as_non_owner(client: TestClient, auth_token: str):
    rule_id = helper_create_rule(client, auth_token)

    res = client.post(
        "/api/auth/register",
        json={"email": "another@req.com", "password": "pass", "full_name": "Other2"},
    )
    other_token = res.json()["access_token"]

    response = client.delete(
        f"/api/rules/{rule_id}", headers={"Authorization": f"Bearer {other_token}"}
    )
    assert response.status_code == 403


def test_rule_not_found(client: TestClient, auth_token: str):
    response = client.patch(
        "/api/rules/9999",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"name": "Ghosts"},
    )
    assert response.status_code == 404
