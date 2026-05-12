import os
import tempfile

import pytest

from database import init_db


@pytest.fixture()
def client(monkeypatch):
    fd, tmp = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    import database as dbmod

    monkeypatch.setattr(dbmod, "DB_PATH", tmp)
    init_db()

    from app import create_app

    app = create_app()
    app.config["TESTING"] = True

    with app.test_client() as c:
        yield c

    try:
        os.remove(tmp)
    except OSError:
        pass


def login(client, username, password):
    return client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=True,
    )


def test_anonymous_user_redirects_to_login(client):
    rv = client.get("/", follow_redirects=False)
    assert rv.status_code in {301, 302}
    assert "/login" in rv.headers["Location"]


def test_default_admin_can_login_and_open_user_page(client):
    rv = login(client, "admin", "admin123")
    assert rv.status_code == 200
    assert "设备管理" in rv.get_data(as_text=True)

    rv = client.get("/users")
    assert rv.status_code == 200
    assert "用户管理" in rv.get_data(as_text=True)


def test_default_user_cannot_open_admin_page(client):
    rv = login(client, "user", "user123")
    assert rv.status_code == 200

    rv = client.get("/users", follow_redirects=True)
    body = rv.get_data(as_text=True)
    assert rv.status_code == 200
    assert "仅管理员可执行此操作" in body


def test_invalid_password_rejected(client):
    rv = login(client, "admin", "wrong-password")
    body = rv.get_data(as_text=True)
    assert rv.status_code == 200
    assert "用户名或密码错误" in body
