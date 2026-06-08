import requests
import time
import os

BASE = "http://127.0.0.1:8000"


def main():
    print("Starting smoke tests for documents API...")
    # login
    r = requests.post(BASE + "/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    print("login status:", r.status_code)
    try:
        token = r.json().get("access_token")
    except Exception:
        print("login response not json:", r.text)
        return
    headers = {"Authorization": f"Bearer {token}"}

    # ensure device exists by listing devices
    r = requests.get(BASE + "/api/v1/devices/", headers=headers)
    print("devices list status:", r.status_code)
    devices = r.json() if r.status_code == 200 else []
    device_id = devices[0]['id'] if devices else 1

    # create temp file to upload
    tmp_path = os.path.join(os.getcwd(), "backend", "tests", "tmp_test_doc.txt")
    os.makedirs(os.path.dirname(tmp_path), exist_ok=True)
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write("smoke test file")

    files = {"file": open(tmp_path, "rb")}
    data = {"device_id": str(device_id), "doc_type": "manual", "version": "1.0", "remarks": "smoke"}
    r = requests.post(BASE + "/api/v1/documents/upload", headers=headers, data=data, files=files)
    print("upload status:", r.status_code)
    try:
        print(r.json())
    except Exception:
        print(r.text[:400])
    if r.status_code != 200:
        print("Upload failed, aborting remaining checks.")
        return
    doc = r.json()
    doc_id = doc.get("id")

    # list
    r = requests.get(BASE + "/api/v1/documents/", headers=headers)
    print("documents list status:", r.status_code, "count:", len(r.json()) if r.status_code==200 else "n/a")

    # download
    r = requests.get(BASE + f"/api/v1/documents/{doc_id}/download", headers=headers)
    print("download status:", r.status_code, "content-length:", len(r.content) if r.status_code==200 else "n/a")

    # submit
    r = requests.post(BASE + f"/api/v1/documents/{doc_id}/submit", headers=headers)
    print("submit status:", r.status_code, r.text[:200])

    # delete (requires admin)
    r = requests.delete(BASE + f"/api/v1/documents/{doc_id}", headers=headers)
    print("delete status:", r.status_code, r.text[:200])

    print("Smoke tests finished.")


if __name__ == '__main__':
    main()
