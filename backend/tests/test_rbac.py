"""RBAC permission tests.

Covers admin access, unauthenticated access, insufficient-role denial,
and the ``require_role`` dependency factory.
"""

import pytest
from fastapi import status


class TestAdminAccess:
    """Tests that admin users can access all protected endpoints."""

    def test_admin_access(self, client, auth_headers):
        """Admin can access admin-only endpoints (e.g. user list)."""
        resp = client.get("/api/v1/users/", headers=auth_headers)
        assert resp.status_code == status.HTTP_200_OK

    def test_admin_can_create_device(self, client, auth_headers):
        """Admin can create devices (admin-only endpoint)."""
        resp = client.post(
            "/api/v1/devices/",
            json={"device_code": "RBAC-001", "device_name": "RBAC测试设备"},
            headers=auth_headers,
        )
        assert resp.status_code == status.HTTP_200_OK


class TestUnauthorizedAccess:
    """Tests that unauthenticated requests are rejected with 401."""

    def test_unauthorized_access(self, client):
        """Unauthenticated request to a protected API returns 401."""
        resp = client.get("/api/v1/devices/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_unauthorized_users_endpoint(self, client):
        """Unauthenticated request to /api/v1/users/ returns 401."""
        resp = client.get("/api/v1/users/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED


class TestForbiddenRole:
    """Tests that authenticated users with insufficient roles get 403."""

    def test_forbidden_role(self, client, normal_auth_headers):
        """A normal user cannot access admin-only /api/v1/users/."""
        resp = client.get("/api/v1/users/", headers=normal_auth_headers)
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_normal_user_cannot_create_device(self, client, normal_auth_headers):
        """A normal user cannot create devices (admin-only endpoint)."""
        resp = client.post(
            "/api/v1/devices/",
            json={"device_code": "FORBIDDEN-001", "device_name": "禁止测试"},
            headers=normal_auth_headers,
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN


class TestRequireRoleDependency:
    """Tests that the ``require_role`` dependency factory works correctly.

    The ``require_role`` dependency is used by several endpoints (e.g.
    esign, approvals).  We verify that it correctly allows or denies
    access based on the user's role.
    """

    def test_require_role_dependency_allows_admin(self, client, auth_headers):
        """Admin can access an endpoint protected by require_role."""
        # The esign list endpoint requires admin, qa_manager, or validation_engineer
        resp = client.get("/api/v1/esign/", headers=auth_headers)
        assert resp.status_code == status.HTTP_200_OK

    def test_require_role_dependency_denies_unauthorized(self, client, normal_auth_headers):
        """A role not in the allowed list is denied access."""
        # equipment_engineer is not in the esign allowed roles
        resp = client.get("/api/v1/esign/", headers=normal_auth_headers)
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_require_role_dependency_no_token(self, client):
        """No token at all returns 401 (caught by RBAC middleware)."""
        resp = client.get("/api/v1/esign/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
