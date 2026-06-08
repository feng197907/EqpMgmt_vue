import os
import requests

BASE = "http://127.0.0.1:8000"


def login():
    res = requests.post(BASE + "/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    res.raise_for_status()
    return res.json()["access_token"]


def main():
    token = login()
    headers = {"Authorization": f"Bearer {token}"}

    devices = requests.get(BASE + "/api/v1/devices/", headers=headers)
    devices.raise_for_status()
    device_list = devices.json()
    if not device_list:
        create_payload = {
            "device_code": "TEST-MAINT-001",
            "device_name": "Maintenance Smoke Device",
            "model": "SM-1",
            "location": "Lab",
        }
        created = requests.post(BASE + "/api/v1/devices/", json=create_payload, headers=headers)
        created.raise_for_status()
        device_id = created.json()["id"]
    else:
        device_id = device_list[0]["id"]

    plan_payload = {
        "device_id": device_id,
        "maintenance_type": "preventive",
        "interval_days": 30,
        "next_due_date": "2026-12-31",
    }
    res = requests.post(f"{BASE}/api/v1/devices/{device_id}/maintenance/plans", json=plan_payload, headers=headers)
    res.raise_for_status()
    plan = res.json()
    plan_id = plan["id"]
    print("created plan", plan_id)

    res = requests.get(f"{BASE}/api/v1/devices/{device_id}/maintenance/plans", headers=headers)
    res.raise_for_status()
    print("plans count", len(res.json()))

    rec_payload = {"content": "Routine inspection", "result": "qualified", "parts_used": ""}
    res = requests.post(f"{BASE}/api/v1/devices/{device_id}/maintenance/plans/{plan_id}/records", json=rec_payload, headers=headers)
    res.raise_for_status()
    record = res.json()
    print("created record", record["id"])

    res = requests.get(f"{BASE}/api/v1/devices/{device_id}/maintenance/plans/{plan_id}/records", headers=headers)
    res.raise_for_status()
    print("records count", len(res.json()))

    rep_payload = {"content": "Panel fixed", "result": "fixed", "parts_used": ""}
    res = requests.post(f"{BASE}/api/v1/devices/{device_id}/maintenance/repair-records", json=rep_payload, headers=headers)
    res.raise_for_status()
    repair = res.json()
    print("created repair record", repair["id"])

    res = requests.get(f"{BASE}/api/v1/devices/{device_id}/maintenance/repair-records", headers=headers)
    res.raise_for_status()
    print("repair records count", len(res.json()))

    res = requests.delete(f"{BASE}/api/v1/devices/{device_id}/maintenance/plans/{plan_id}", headers=headers)
    res.raise_for_status()
    print("deleted plan", plan_id)


if __name__ == "__main__":
    main()
