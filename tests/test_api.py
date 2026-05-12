import json
import os
import tempfile

import pytest

from database import init_db, get_db


@pytest.fixture()
def client(monkeypatch):
    # 使用临时数据库文件，避免影响工作区数据库
    fd, tmp = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    import database as dbmod

    monkeypatch.setattr(dbmod, "DB_PATH", tmp)
    # 重新初始化数据库结构
    init_db()

    # 导入 app 放在这里以确保 database.DB_PATH 已被替换
    from app import create_app

    app = create_app()
    app.config["TESTING"] = True
    app.config["LOGIN_DISABLED"] = True

    with app.test_client() as c:
        yield c

    try:
        os.remove(tmp)
    except OSError:
        pass


def insert_device(device_code="DEV-001", device_name="TestDevice"):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO devices (device_code, device_name, model, location, status) VALUES (?, ?, ?, ?, ?)",
        (device_code, device_name, "M1", "Lab", "active"),
    )
    conn.commit()
    cur.execute("SELECT id FROM devices WHERE device_code = ?", (device_code,))
    row = cur.fetchone()
    conn.close()
    return row["id"]


def test_get_devices(client):
    dev_id = insert_device()
    rv = client.get("/api/devices")
    assert rv.status_code == 200
    data = rv.get_json()
    assert isinstance(data, list)
    assert any(d.get("device_code") == "DEV-001" for d in data)


def test_change_status_noncritical(client):
    dev_id = insert_device(device_code="DEV-002")
    payload = {"new_status": "maintenance", "reason": "periodic check"}
    rv = client.post(
        f"/api/devices/{dev_id}/status", data=json.dumps(payload), content_type="application/json"
    )
    assert rv.status_code == 200
    data = rv.get_json()
    assert data.get("status") == "updated"

    # 验证 DB 中状态已更新
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT status FROM devices WHERE id = ?", (dev_id,))
    row = cur.fetchone()
    conn.close()
    assert row["status"] == "maintenance"


def test_change_status_critical_creates_request(client):
    dev_id = insert_device(device_code="DEV-003")
    payload = {"new_status": "retired", "reason": "end of life"}
    rv = client.post(
        f"/api/devices/{dev_id}/status", data=json.dumps(payload), content_type="application/json"
    )
    assert rv.status_code == 202
    data = rv.get_json()
    assert data.get("status") == "pending"

    # 验证请求表中存在记录
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM device_status_requests WHERE device_id = ?", (dev_id,))
    row = cur.fetchone()
    conn.close()
    assert row is not None
    assert row["new_status"] == "retired"
