"""Device module tests.

Covers device CRUD operations and the status-change request workflow.
"""

import pytest
from fastapi import status


# ── Helper ───────────────────────────────────────────────────────────────────

_DEVICE_PAYLOAD = {
    "device_code": "DEV-001",
    "device_name": "测试设备",
    "model": "MODEL-A",
    "location": "车间1号",
}


# ── Create Device ────────────────────────────────────────────────────────────


class TestCreateDevice:
    """Tests for POST /api/v1/devices/."""

    def test_create_device(self, client, auth_headers):
        """Admin can create a new device."""
        resp = client.post(
            "/api/v1/devices/",
            json=_DEVICE_PAYLOAD,
            headers=auth_headers,
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["device_code"] == "DEV-001"
        assert data["device_name"] == "测试设备"
        assert data["model"] == "MODEL-A"
        assert data["location"] == "车间1号"
        assert data["status"] == "active"
        assert data["is_deleted"] is False

    def test_create_device_duplicate_code(self, client, auth_headers):
        """Creating a device with a duplicate code returns 400."""
        # First device
        client.post("/api/v1/devices/", json=_DEVICE_PAYLOAD, headers=auth_headers)
        # Duplicate
        resp = client.post(
            "/api/v1/devices/",
            json=_DEVICE_PAYLOAD,
            headers=auth_headers,
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


# ── List Devices ─────────────────────────────────────────────────────────────


class TestListDevices:
    """Tests for GET /api/v1/devices/."""

    def test_list_devices(self, client, auth_headers):
        """Listing devices returns the created device."""
        # Create a device first
        client.post("/api/v1/devices/", json=_DEVICE_PAYLOAD, headers=auth_headers)

        resp = client.get("/api/v1/devices/", headers=auth_headers)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(d["device_code"] == "DEV-001" for d in data)

    def test_list_devices_empty(self, client, auth_headers):
        """Listing devices when none exist returns an empty list."""
        resp = client.get("/api/v1/devices/", headers=auth_headers)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json() == []


# ── Update Device ────────────────────────────────────────────────────────────


class TestUpdateDevice:
    """Tests for PUT /api/v1/devices/{device_id}."""

    def test_update_device(self, client, auth_headers):
        """Admin can update device fields."""
        # Create
        create_resp = client.post(
            "/api/v1/devices/", json=_DEVICE_PAYLOAD, headers=auth_headers
        )
        device_id = create_resp.json()["id"]

        # Update
        resp = client.put(
            f"/api/v1/devices/{device_id}",
            json={"device_name": "更新后设备", "location": "车间2号"},
            headers=auth_headers,
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["device_name"] == "更新后设备"
        assert data["location"] == "车间2号"
        # Unchanged fields remain
        assert data["device_code"] == "DEV-001"

    def test_update_device_not_found(self, client, auth_headers):
        """Updating a non-existent device returns 404."""
        resp = client.put(
            "/api/v1/devices/99999",
            json={"device_name": "不存在"},
            headers=auth_headers,
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND


# ── Delete Device ────────────────────────────────────────────────────────────


class TestDeleteDevice:
    """Tests for DELETE /api/v1/devices/{device_id}."""

    def test_delete_device(self, client, auth_headers):
        """Admin can soft-delete a device."""
        # Create
        create_resp = client.post(
            "/api/v1/devices/", json=_DEVICE_PAYLOAD, headers=auth_headers
        )
        device_id = create_resp.json()["id"]

        # Delete
        resp = client.delete(
            f"/api/v1/devices/{device_id}",
            headers=auth_headers,
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["status"] == "deleted"

        # Verify it no longer appears in the default list
        list_resp = client.get("/api/v1/devices/", headers=auth_headers)
        devices = list_resp.json()
        assert not any(d["id"] == device_id for d in devices)

    def test_delete_device_not_found(self, client, auth_headers):
        """Deleting a non-existent device returns 404."""
        resp = client.delete(
            "/api/v1/devices/99999",
            headers=auth_headers,
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND


# ── Device Status Change Request ─────────────────────────────────────────────


class TestDeviceStatusChange:
    """Tests for the device status-change request workflow.

    When a device's status is changed via the update API, a
    DeviceStatusRequest record is automatically created.
    """

    def test_device_status_change_request(self, client, auth_headers, db):
        """Changing device status via update triggers a change request."""
        from backend.app.models.device_change import DeviceStatusRequest

        # Create a device
        create_resp = client.post(
            "/api/v1/devices/", json=_DEVICE_PAYLOAD, headers=auth_headers
        )
        device_id = create_resp.json()["id"]

        # Update the device status (active → inactive)
        resp = client.put(
            f"/api/v1/devices/{device_id}",
            json={"status": "inactive"},
            headers=auth_headers,
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["status"] == "inactive"

        # Verify that a DeviceStatusRequest was created
        change_requests = db.query(DeviceStatusRequest).filter(
            DeviceStatusRequest.device_id == device_id
        ).all()
        assert len(change_requests) >= 1
        cr = change_requests[0]
        assert cr.current_status == "active"
        assert cr.new_status == "inactive"
        assert cr.status == "pending"
