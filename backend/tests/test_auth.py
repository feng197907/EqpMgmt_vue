"""Authentication module tests.

Covers login, token refresh, password change, and must-change-password flows.
"""

import pytest
from fastapi import status


# ── Login Tests ──────────────────────────────────────────────────────────────


class TestLogin:
    """Tests for POST /api/v1/auth/login."""

    def test_login_success(self, client, test_user):
        """Normal login returns access and refresh tokens."""
        resp = client.post(
            "/api/v1/auth/login",
            json={"username": "admin_test", "password": "Admin@1234"},
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["must_change_password"] is False

    def test_login_wrong_password(self, client, test_user):
        """Login with wrong password returns 400."""
        resp = client.post(
            "/api/v1/auth/login",
            json={"username": "admin_test", "password": "WrongPass@1"},
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "Incorrect username or password" in resp.json()["detail"]

    def test_login_nonexistent_user(self, client):
        """Login with a non-existent user returns 400."""
        resp = client.post(
            "/api/v1/auth/login",
            json={"username": "ghost_user", "password": "NoMatter@1"},
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


# ── Token Refresh Tests ─────────────────────────────────────────────────────


class TestRefreshToken:
    """Tests for POST /api/v1/auth/refresh."""

    def test_refresh_token(self, client, test_user):
        """A valid refresh token can be exchanged for a new token pair."""
        # First, login to get tokens
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"username": "admin_test", "password": "Admin@1234"},
        )
        refresh_token = login_resp.json()["refresh_token"]

        # Then, use the refresh token
        resp = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        # Verify the new tokens are valid (structure check)
        assert data["token_type"] == "bearer"


# ── Change Password Tests ───────────────────────────────────────────────────


class TestChangePassword:
    """Tests for PUT /api/v1/auth/change-password."""

    def test_change_password(self, client, test_user, auth_headers):
        """Changing password succeeds with correct old password."""
        resp = client.put(
            "/api/v1/auth/change-password",
            json={
                "old_password": "Admin@1234",
                "new_password": "NewAdmin@5678",
            },
            headers=auth_headers,
        )
        assert resp.status_code == status.HTTP_200_OK
        assert "密码已修改" in resp.json()["detail"]

        # Verify the new password works for login
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"username": "admin_test", "password": "NewAdmin@5678"},
        )
        assert login_resp.status_code == status.HTTP_200_OK

    def test_change_password_wrong_old(self, client, test_user, auth_headers):
        """Changing password with wrong old password returns 400."""
        resp = client.put(
            "/api/v1/auth/change-password",
            json={
                "old_password": "WrongOld@1",
                "new_password": "NewAdmin@5678",
            },
            headers=auth_headers,
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


# ── Must-Change-Password Tests ──────────────────────────────────────────────


class TestMustChangePassword:
    """Tests for the must_change_password login flow."""

    def test_must_change_password(self, client, test_must_change_user):
        """Login for a user with must_change_password=True returns the flag."""
        resp = client.post(
            "/api/v1/auth/login",
            json={"username": "mustchange_test", "password": "OldPass@1234"},
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["must_change_password"] is True
        # The tokens should still be valid
        assert "access_token" in data
        assert "refresh_token" in data
