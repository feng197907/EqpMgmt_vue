import hashlib
import json
import os
import sqlite3
import time
from datetime import datetime, timezone
from flask import (
    Flask,
    flash,
    has_request_context,
    redirect,
    render_template,
    request,
    jsonify,
    send_from_directory,
    url_for,
)
from flask_login import (
    LoginManager,
    UserMixin,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from database import get_db, init_db

# 基础路径与上传配置。
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "xls", "xlsx", "jpg", "jpeg", "png"}

# 文档类型枚举与展示标签，用于UI分组。
DOC_TYPES = [
    ("equipment_history", "设备履历表"),
    ("urs", "URS"),
    ("dq", "DQ报告"),
    ("iq", "IQ报告"),
    ("oq", "OQ报告"),
    ("pq", "PQ报告"),
    ("calibration", "校准记录"),
    ("maintenance", "维护记录"),
    ("deviation", "偏差报告"),
    ("change", "变更记录"),
    ("drawing", "图纸"),
    ("manual", "手册"),
]
# 文档类型标签快速映射。
DOC_TYPE_LABELS = dict(DOC_TYPES)

# 文档状态枚举与展示标签。
DOC_STATUS_LABELS = {
    "draft": "起草",
    "pending": "审批中",
    "active": "生效",
    "changing": "变更中",
    "archived": "归档",
    "deprecated": "作废",
}

# 审批流程配置（可扩展为多级）。
APPROVAL_STEPS = [
    {"role": "admin", "label": "管理员审批"},
]

# Flask 应用核心配置。
app = Flask(__name__)
app.config["SECRET_KEY"] = "dev-secret-key"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 50000 * 1024

# Flask-Login 会话管理配置。
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)


# Flask-Login 使用的用户对象（登录后写入会话）。
class User(UserMixin):
    def __init__(self, user_id, username, role, password_hash):
        self.id = user_id
        self.username = username
        self.role = role
        self.password_hash = password_hash

    @property
    def is_admin(self):
        return self.role == "admin"


@login_manager.user_loader
def load_user(user_id):
    """按用户ID加载会话用户，用于会话恢复。"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    if row is None:
        return None
    return User(row["id"], row["username"], row["role"], row["password"])


def allowed_file(filename):
    """校验上传文件扩展名是否在白名单内。"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def log_action(
    user,
    action,
    target_type,
    target_id=None,
    details=None,
    before_value=None,
    after_value=None,
    reason=None,
    ip_address=None,
):
    """写入审计日志，作为不可篡改的合规记录。"""
    if ip_address is None and has_request_context():
        ip_address = request.headers.get("X-Forwarded-For", request.remote_addr)
    conn = get_db()
    cur = conn.cursor()
    log_action_with_cursor(
        cur,
        user,
        action,
        target_type,
        target_id=target_id,
        details=details,
        before_value=before_value,
        after_value=after_value,
        reason=reason,
        ip_address=ip_address,
    )
    commit_with_retry(conn)
    conn.close()


def _to_json(value):
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


def log_action_with_cursor(
    cur,
    user,
    action,
    target_type,
    target_id=None,
    details=None,
    before_value=None,
    after_value=None,
    reason=None,
    ip_address=None,
):
    """使用现有游标写入审计日志，避免嵌套写连接。"""
    execute_with_retry(
        cur,
        """
        INSERT INTO audit_logs
        (user, action, target_type, target_id, details, before_value, after_value, reason, ip_address)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user,
            action,
            target_type,
            target_id,
            details,
            _to_json(before_value),
            _to_json(after_value),
            reason,
            ip_address,
        ),
    )


def execute_with_retry(cur, sql, params=(), retries=5, base_delay=0.2):
    """遇到锁冲突时进行短暂重试，避免瞬时写入失败。"""
    for attempt in range(retries):
        try:
            cur.execute(sql, params)
            return
        except sqlite3.OperationalError as exc:
            if "locked" in str(exc).lower() and attempt < retries - 1:
                time.sleep(base_delay * (attempt + 1))
                continue
            raise


def commit_with_retry(conn, retries=5, base_delay=0.2):
    """提交时遇到锁冲突进行重试。"""
    for attempt in range(retries):
        try:
            conn.commit()
            return
        except sqlite3.OperationalError as exc:
            if "locked" in str(exc).lower() and attempt < retries - 1:
                time.sleep(base_delay * (attempt + 1))
                continue
            raise


def compute_doc_hash(file_path, signer, meaning, signed_at):
    """计算文档签名哈希：文档内容 + 签名信息。"""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as file_obj:
        for chunk in iter(lambda: file_obj.read(8192), b""):
            hasher.update(chunk)
    hasher.update(signer.encode("utf-8"))
    hasher.update(meaning.encode("utf-8"))
    hasher.update(signed_at.encode("utf-8"))
    return hasher.hexdigest()


def admin_required(view_func):
    """装饰器：限制仅管理员可访问的路由。"""
    def wrapper(*args, **kwargs):
        if not current_user.is_admin:
            flash("仅管理员可执行此操作。", "warning")
            return redirect(url_for("index"))
        return view_func(*args, **kwargs)

    wrapper.__name__ = view_func.__name__
    return login_required(wrapper)


def get_next_version(conn, device_id, doc_type):
    """计算同设备+同类型的下一个版本号。"""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT version FROM documents
        WHERE device_id = ? AND doc_type = ? AND is_deleted = 0
        ORDER BY id DESC
        LIMIT 1
        """,
        (device_id, doc_type),
    )
    row = cur.fetchone()
    if row is None:
        return "1.0"
    parts = row["version"].split(".")
    if len(parts) != 2 or not parts[1].isdigit() or not parts[0].isdigit():
        return "1.0"
    major = int(parts[0])
    minor = int(parts[1]) + 1
    return f"{major}.{minor}"


def ensure_upload_dir(device_id):
    """确保设备专属上传目录存在。"""
    device_dir = os.path.join(UPLOAD_FOLDER, f"device_{device_id}")
    os.makedirs(device_dir, exist_ok=True)
    return device_dir


def get_document_rows(device_id):
    """查询文档并附加最新借阅状态，供详情页展示。"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT d.*, br.id AS borrow_id, br.status AS borrow_status,
               br.borrower AS borrow_user, br.borrow_date AS borrow_date
        FROM documents d
        LEFT JOIN (
            SELECT b1.*
            FROM borrow_records b1
            JOIN (
                SELECT doc_id, MAX(id) AS max_id
                FROM borrow_records
                GROUP BY doc_id
            ) latest ON latest.max_id = b1.id
        ) br ON br.doc_id = d.id
        WHERE d.device_id = ? AND d.is_deleted = 0
        ORDER BY d.doc_type, d.upload_time DESC
        """,
        (device_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


@app.route("/login", methods=["GET", "POST"])
def login():
    """验证登录，拦截停用账号并创建会话。"""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cur.fetchone()
        conn.close()

        if row and row["status"] != "active":
            flash("账户已停用，请联系管理员。", "warning")
        elif row and check_password_hash(row["password"], password):
            user = User(row["id"], row["username"], row["role"], row["password"])
            login_user(user)
            log_action(user.username, "login", "user", user.id, "用户登录")
            return redirect(url_for("index"))

        flash("用户名或密码错误。", "danger")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    """退出登录并记录审计日志。"""
    log_action(current_user.username, "logout", "user", current_user.id, "用户登出")
    logout_user()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    """设备列表：支持搜索与管理员查看停用设备。"""
    query = request.args.get("q", "").strip()
    show_inactive = request.args.get("show_inactive", "").lower() in {"1", "true", "on", "yes"}
    conn = get_db()
    cur = conn.cursor()
    status_filter = "" if (show_inactive and current_user.is_admin) else "AND status = 'active'"
    if query:
        cur.execute(
            f"""
            SELECT * FROM devices
            WHERE (device_code LIKE ? OR device_name LIKE ? OR model LIKE ?)
            {status_filter}
            ORDER BY created_at DESC
            """,
            (f"%{query}%", f"%{query}%", f"%{query}%"),
        )
    else:
        cur.execute(
            f"SELECT * FROM devices WHERE 1=1 {status_filter} ORDER BY created_at DESC"
        )
    devices = cur.fetchall()
    conn.close()
    return render_template(
        "index.html",
        devices=devices,
        query=query,
        show_inactive=show_inactive,
    )


@app.route("/add_device", methods=["GET", "POST"])
@login_required
def add_device():
    """新增设备记录（设备编码和名称必填）。"""
    if request.method == "POST":
        device_code = request.form.get("device_code", "").strip()
        device_name = request.form.get("device_name", "").strip()
        model = request.form.get("model", "").strip()
        location = request.form.get("location", "").strip()

        if not device_code or not device_name:
            flash("设备编码和名称为必填项。", "warning")
            return redirect(url_for("add_device"))

        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                INSERT INTO devices (device_code, device_name, model, location)
                VALUES (?, ?, ?, ?)
                """,
                (device_code, device_name, model, location),
            )
            conn.commit()
            device_id = cur.lastrowid
            log_action(
                current_user.username,
                "create_device",
                "device",
                device_id,
                f"新增设备 {device_code}",
            )
            flash("设备已创建。", "success")
            return redirect(url_for("index"))
        except Exception:
            conn.rollback()
            flash("设备编码已存在或保存失败。", "danger")
        finally:
            conn.close()

    return render_template("add_device.html")


@app.route("/users")
@admin_required
def user_list():
    """管理员查看用户列表及状态。"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, username, role, status FROM users ORDER BY id ASC")
    users = cur.fetchall()
    conn.close()
    return render_template("users.html", users=users)


@app.route("/users/create", methods=["POST"])
@admin_required
def create_user():
    """管理员创建用户并保存密码哈希。"""
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()
    role = request.form.get("role", "user").strip()

    if not username or not password:
        flash("用户名和密码不能为空。", "warning")
        return redirect(url_for("user_list"))

    if role not in {"admin", "user"}:
        flash("角色不合法。", "warning")
        return redirect(url_for("user_list"))

    conn = get_db()
    cur = conn.cursor()
    try:
        hashed = generate_password_hash(password)
        cur.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, hashed, role),
        )
        conn.commit()
        user_id = cur.lastrowid
        log_action(
            current_user.username,
            "create_user",
            "user",
            user_id,
            f"创建用户 {username} ({role})",
        )
        flash("用户已创建。", "success")
    except Exception:
        conn.rollback()
        flash("创建失败，用户名可能已存在。", "danger")
    finally:
        conn.close()

    return redirect(url_for("user_list"))


@app.route("/users/<int:user_id>/toggle", methods=["POST"])
@admin_required
def toggle_user(user_id):
    """管理员启用/停用用户账号。"""
    if current_user.id == user_id:
        flash("不能停用当前登录用户。", "warning")
        return redirect(url_for("user_list"))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, username, status FROM users WHERE id = ?", (user_id,))
    user_row = cur.fetchone()
    if user_row is None:
        conn.close()
        flash("用户不存在。", "warning")
        return redirect(url_for("user_list"))

    new_status = "inactive" if user_row["status"] == "active" else "active"
    cur.execute("UPDATE users SET status = ? WHERE id = ?", (new_status, user_id))
    conn.commit()
    log_action(
        current_user.username,
        "toggle_user",
        "user",
        user_id,
        f"用户 {user_row['username']} 状态改为 {new_status}",
    )
    conn.close()
    flash("用户状态已更新。", "success")
    return redirect(url_for("user_list"))


@app.route("/device/<int:device_id>")
@login_required
def device_detail(device_id):
    """设备详情页：按文档类型分组展示。"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM devices WHERE id = ?", (device_id,))
    device = cur.fetchone()
    conn.close()
    if device is None:
        flash("设备不存在。", "warning")
        return redirect(url_for("index"))

    rows = get_document_rows(device_id)
    grouped = {key: [] for key, _ in DOC_TYPES}
    for row in rows:
        grouped.setdefault(row["doc_type"], []).append(row)

    return render_template(
        "device_detail.html",
        device=device,
        grouped=grouped,
        doc_types=DOC_TYPES,
        doc_type_labels=DOC_TYPE_LABELS,
        doc_status_labels=DOC_STATUS_LABELS,
    )


@app.route("/device/<int:device_id>/toggle", methods=["POST"])
@admin_required
def toggle_device(device_id):
    """管理员切换设备启用/停用状态。"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM devices WHERE id = ?", (device_id,))
    device = cur.fetchone()
    if device is None:
        conn.close()
        flash("设备不存在。", "warning")
        return redirect(url_for("index"))

    new_status = "inactive" if device["status"] == "active" else "active"
    cur.execute("UPDATE devices SET status = ? WHERE id = ?", (new_status, device_id))
    conn.commit()
    log_action(
        current_user.username,
        "toggle_device",
        "device",
        device_id,
        f"设备状态改为 {new_status}",
    )
    conn.close()
    flash("设备状态已更新。", "success")
    if new_status == "inactive":
        return redirect(url_for("index", show_inactive=1))
    return redirect(url_for("index"))


@app.route("/device/<int:device_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_device(device_id):
    """编辑设备信息。"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM devices WHERE id = ?", (device_id,))
    device = cur.fetchone()
    if device is None:
        conn.close()
        flash("设备不存在。", "warning")
        return redirect(url_for("index"))

    if request.method == "POST":
        device_code = request.form.get("device_code", "").strip()
        device_name = request.form.get("device_name", "").strip()
        model = request.form.get("model", "").strip()
        location = request.form.get("location", "").strip()

        if not device_code or not device_name:
            flash("设备编码和名称为必填项。", "warning")
            return redirect(url_for("edit_device", device_id=device_id))

        try:
            cur.execute(
                "UPDATE devices SET device_code = ?, device_name = ?, model = ?, location = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (device_code, device_name, model, location, device_id),
            )
            conn.commit()
            log_action(
                current_user.username,
                "update_device",
                "device",
                device_id,
                f"更新设备 {device_code}",
                before_value={
                    "device_code": device["device_code"],
                    "device_name": device["device_name"],
                    "model": device["model"],
                    "location": device["location"],
                },
                after_value={
                    "device_code": device_code,
                    "device_name": device_name,
                    "model": model,
                    "location": location,
                },
            )
            flash("设备信息已更新。", "success")
        except Exception:
            conn.rollback()
            flash("更新失败，可能设备编码已存在。", "danger")
        finally:
            conn.close()
        return redirect(url_for("device_detail", device_id=device_id))

    conn.close()
    return render_template("add_device.html", device=device)


@app.route("/device/<int:device_id>/delete", methods=["POST"])
@admin_required
def delete_device(device_id):
    """软删除设备（标记停用）并记录审计。"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM devices WHERE id = ?", (device_id,))
    device = cur.fetchone()
    if device is None:
        conn.close()
        flash("设备不存在。", "warning")
        return redirect(url_for("index"))

    try:
        cur.execute("UPDATE devices SET status = 'inactive', is_deleted = 1 WHERE id = ?", (device_id,))
        conn.commit()
        log_action(
            current_user.username,
            "delete_device",
            "device",
            device_id,
            f"删除设备 {device['device_code']}",
            before_value={"status": device.get("status")},
            after_value={"status": "inactive"},
        )
        flash("设备已删除（停用）。", "success")
    except Exception:
        conn.rollback()
        flash("删除失败。", "danger")
    finally:
        conn.close()

    return redirect(url_for("index"))


def ensure_device_change_table(cur):
    """确保用于记录设备状态变更请求的表存在。"""
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS device_status_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id INTEGER NOT NULL,
            requested_by TEXT NOT NULL,
            new_status TEXT NOT NULL,
            reason TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            decided_by TEXT,
            decided_at TIMESTAMP,
            comment TEXT
        )
        """
    )


@app.route("/device/<int:device_id>/change_status", methods=["POST"])
@login_required
def change_device_status(device_id):
    """提交设备状态变更：关键状态生成审批请求，其他直接修改并记录审计。"""
    new_status = request.form.get("new_status", "").strip()
    reason = request.form.get("reason", "").strip()

    if not new_status or not reason:
        flash("请选择目标状态并填写变更原因。", "warning")
        return redirect(url_for("device_detail", device_id=device_id))

    critical = {"inactive", "retired"}

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM devices WHERE id = ?", (device_id,))
    device = cur.fetchone()
    if device is None:
        conn.close()
        flash("设备不存在。", "warning")
        return redirect(url_for("index"))

    if new_status in critical:
        # create device change request
        ensure_device_change_table(cur)
        execute_with_retry(
            cur,
            "INSERT INTO device_status_requests (device_id, requested_by, new_status, reason) VALUES (?, ?, ?, ?)",
            (device_id, current_user.username, new_status, reason),
        )
        conn.commit()
        log_action(
            current_user.username,
            "request_device_status_change",
            "device",
            device_id,
            f"申请将设备 {device['device_code']} 状态更改为 {new_status}",
            before_value={"status": device.get("status")},
            after_value={"requested_status": new_status},
            reason=reason,
        )
        conn.close()
        flash("变更已提交，需审批通过后生效。", "info")
        return redirect(url_for("device_detail", device_id=device_id))

    # non-critical: apply immediately
    try:
        execute_with_retry(
            cur,
            "UPDATE devices SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (new_status, device_id),
        )
        conn.commit()
        log_action(
            current_user.username,
            "change_device_status",
            "device",
            device_id,
            f"将设备 {device['device_code']} 状态更新为 {new_status}",
            before_value={"status": device.get("status")},
            after_value={"status": new_status},
            reason=reason,
        )
        flash("设备状态已更新。", "success")
    except Exception:
        conn.rollback()
        flash("更新设备状态失败。", "danger")
    finally:
        conn.close()

    return redirect(url_for("device_detail", device_id=device_id))


@app.route("/device_changes")
@admin_required
def device_changes():
    """管理员查看待处理的设备状态变更请求。"""
    conn = get_db()
    cur = conn.cursor()
    ensure_device_change_table(cur)
    cur.execute(
        "SELECT r.*, d.device_code, d.device_name FROM device_status_requests r JOIN devices d ON d.id = r.device_id WHERE r.status = 'pending' ORDER BY r.created_at ASC"
    )
    rows = cur.fetchall()
    conn.close()
    return render_template("device_changes.html", rows=rows)


@app.route("/device_changes/<int:req_id>/decide", methods=["POST"])
@admin_required
def decide_device_change(req_id):
    """管理员批准或拒绝设备变更请求（需密码确认）。"""
    decision = request.form.get("decision")
    password = request.form.get("password", "")
    comment = request.form.get("comment", "").strip()

    if decision not in {"approve", "reject"}:
        flash("无效的决策。", "warning")
        return redirect(url_for("device_changes"))

    if not check_password_hash(current_user.password_hash, password):
        flash("密码校验失败，无法签名。", "danger")
        return redirect(url_for("device_changes"))

    conn = get_db()
    cur = conn.cursor()
    ensure_device_change_table(cur)
    cur.execute("SELECT * FROM device_status_requests WHERE id = ?", (req_id,))
    req = cur.fetchone()
    if req is None or req["status"] != "pending":
        conn.close()
        flash("请求不存在或已处理。", "warning")
        return redirect(url_for("device_changes"))

    if decision == "approve":
        try:
            execute_with_retry(cur, "UPDATE devices SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (req["new_status"], req["device_id"]))
            execute_with_retry(cur, "UPDATE device_status_requests SET status = 'approved', decided_by = ?, decided_at = CURRENT_TIMESTAMP, comment = ? WHERE id = ?", (current_user.username, comment, req_id))
            conn.commit()
            log_action(
                current_user.username,
                "approve_device_status_change",
                "device",
                req["device_id"],
                f"批准设备状态变更为 {req['new_status']}",
                before_value=None,
                after_value={"status": req["new_status"]},
                reason=comment or None,
            )
            flash("已批准并生效。", "success")
        except Exception:
            conn.rollback()
            flash("批准失败。", "danger")
    else:
        execute_with_retry(cur, "UPDATE device_status_requests SET status = 'rejected', decided_by = ?, decided_at = CURRENT_TIMESTAMP, comment = ? WHERE id = ?", (current_user.username, comment, req_id))
        conn.commit()
        log_action(
            current_user.username,
            "reject_device_status_change",
            "device",
            req["device_id"],
            f"拒绝设备状态变更到 {req['new_status']}",
            reason=comment or None,
        )
        flash("已拒绝。", "warning")

    conn.close()
    return redirect(url_for("device_changes"))


@app.route("/upload_doc/<int:device_id>", methods=["GET", "POST"])
@login_required
def upload_doc(device_id):
    """上传文档：自动版本、保存元数据与文件。"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM devices WHERE id = ?", (device_id,))
    device = cur.fetchone()
    if device is None:
        conn.close()
        flash("设备不存在。", "warning")
        return redirect(url_for("index"))

    if request.method == "POST":
        doc_type = request.form.get("doc_type")
        remarks = request.form.get("remarks", "").strip()
        file = request.files.get("file")

        if doc_type not in DOC_TYPE_LABELS:
            flash("请选择正确的文档类型。", "warning")
            return redirect(url_for("upload_doc", device_id=device_id))

        if not file or file.filename == "":
            flash("请选择要上传的文件。", "warning")
            return redirect(url_for("upload_doc", device_id=device_id))

        if not allowed_file(file.filename):
            flash("文件类型不允许。", "danger")
            return redirect(url_for("upload_doc", device_id=device_id))

        version = get_next_version(conn, device_id, doc_type)
        original_name = secure_filename(file.filename)
        device_dir = ensure_upload_dir(device_id)
        stored_name = f"{doc_type}_{version}_{original_name}"
        file_path = os.path.join(device_dir, stored_name)
        file.save(file_path)

        cur.execute(
            """
            INSERT INTO documents
            (device_id, doc_type, doc_name, version, file_path, uploaded_by, remarks, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                device_id,
                doc_type,
                original_name,
                version,
                file_path,
                current_user.username,
                remarks,
                "draft",
            ),
        )
        conn.commit()
        doc_id = cur.lastrowid
        log_action(
            current_user.username,
            "upload_document",
            "document",
            doc_id,
            f"上传 {DOC_TYPE_LABELS.get(doc_type)} v{version}",
        )
        conn.close()
        flash("文档已上传。", "success")
        return redirect(url_for("device_detail", device_id=device_id))

    conn.close()
    return render_template(
        "upload_doc.html", device=device, doc_types=DOC_TYPES
    )


@app.route("/download/<int:doc_id>")
@login_required
def download_doc(doc_id):
    """下载文档并累计下载次数，同时记录审计。"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM documents WHERE id = ? AND is_deleted = 0", (doc_id,)
    )
    doc = cur.fetchone()
    if doc is not None and doc["status"] not in {"active", "archived"}:
        conn.close()
        flash("该文档当前状态不允许下载。", "warning")
        return redirect(url_for("device_detail", device_id=doc["device_id"]))
    if doc is not None:
        cur.execute(
            "UPDATE documents SET download_count = download_count + 1 WHERE id = ?",
            (doc_id,),
        )
        conn.commit()
    conn.close()
    if doc is None:
        flash("文档不存在或已删除。", "warning")
        return redirect(url_for("index"))

    log_action(
        current_user.username,
        "download_document",
        "document",
        doc_id,
        f"下载 {doc['doc_name']} v{doc['version']}",
    )

    directory = os.path.dirname(doc["file_path"])
    filename = os.path.basename(doc["file_path"])
    return send_from_directory(
        directory,
        filename,
        as_attachment=True,
        download_name=doc["doc_name"],
    )


@app.route("/borrow/<int:doc_id>", methods=["POST"])
@login_required
def borrow_doc(doc_id):
    """文档借阅：未被借出时创建借阅记录。"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT d.*, br.status AS borrow_status
        FROM documents d
        LEFT JOIN borrow_records br
            ON br.id = (
                SELECT id FROM borrow_records
                WHERE doc_id = d.id
                ORDER BY id DESC LIMIT 1
            )
        WHERE d.id = ? AND d.is_deleted = 0
        """,
        (doc_id,),
    )
    doc = cur.fetchone()
    if doc is None:
        conn.close()
        flash("文档不存在。", "warning")
        return redirect(url_for("index"))

    if doc["status"] != "active":
        conn.close()
        flash("只有生效文档可以借阅。", "warning")
        return redirect(url_for("device_detail", device_id=doc["device_id"]))

    if doc["borrow_status"] == "borrowed":
        conn.close()
        flash("文档已借出。", "warning")
        return redirect(url_for("device_detail", device_id=doc["device_id"]))

    cur.execute(
        """
        INSERT INTO borrow_records (doc_id, borrower)
        VALUES (?, ?)
        """,
        (doc_id, current_user.username),
    )
    conn.commit()
    borrow_id = cur.lastrowid
    log_action(
        current_user.username,
        "borrow_document",
        "borrow",
        borrow_id,
        f"借阅 {doc['doc_name']} v{doc['version']}",
    )
    conn.close()
    flash("借阅成功。", "success")
    return redirect(url_for("device_detail", device_id=doc["device_id"]))


@app.route("/document/<int:doc_id>/submit", methods=["POST"])
@login_required
def submit_document(doc_id):
    """提交文档审批：起草 -> 审批中，并创建审批请求。"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM documents WHERE id = ? AND is_deleted = 0", (doc_id,))
    doc = cur.fetchone()
    if doc is None:
        conn.close()
        flash("文档不存在。", "warning")
        return redirect(url_for("index"))

    if doc["status"] != "draft":
        conn.close()
        flash("当前状态不允许提交审批。", "warning")
        return redirect(url_for("device_detail", device_id=doc["device_id"]))

    execute_with_retry(
        cur,
        """
        INSERT INTO approval_requests (doc_id, status, created_by, current_step)
        VALUES (?, 'pending', ?, 1)
        """,
        (doc_id, current_user.username),
    )
    request_id = cur.lastrowid
    for idx, step in enumerate(APPROVAL_STEPS, start=1):
        execute_with_retry(
            cur,
            """
            INSERT INTO approval_steps (request_id, step_order, approver_role)
            VALUES (?, ?, ?)
            """,
            (request_id, idx, step["role"]),
        )

    execute_with_retry(
        cur,
        "UPDATE documents SET status = 'pending' WHERE id = ?",
        (doc_id,),
    )
    commit_with_retry(conn)
    log_action(
        current_user.username,
        "submit_document",
        "document",
        doc_id,
        "提交文档审批",
        before_value={"status": "draft"},
        after_value={"status": "pending"},
    )
    conn.close()
    flash("已提交审批。", "success")
    return redirect(url_for("device_detail", device_id=doc["device_id"]))


@app.route("/approvals")
@admin_required
def approvals():
    """管理员审批待办列表。"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT ar.*, d.doc_name, d.doc_type, d.version, d.device_id
        FROM approval_requests ar
        JOIN documents d ON d.id = ar.doc_id
        WHERE ar.status = 'pending'
        ORDER BY ar.created_at ASC
        """
    )
    rows = cur.fetchall()
    conn.close()
    return render_template("approvals.html", rows=rows, doc_type_labels=DOC_TYPE_LABELS)


@app.route("/approvals/<int:request_id>/decide", methods=["POST"])
@admin_required
def decide_approval(request_id):
    """审批动作：管理员通过或拒绝，并记录电子签名。"""
    decision = request.form.get("decision")
    password = request.form.get("password", "")
    comment = request.form.get("comment", "").strip()

    if decision not in {"approve", "reject"}:
        flash("审批操作无效。", "warning")
        return redirect(url_for("approvals"))

    if not check_password_hash(current_user.password_hash, password):
        flash("密码校验失败，无法签名。", "danger")
        return redirect(url_for("approvals"))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM approval_requests WHERE id = ?", (request_id,))
    req = cur.fetchone()
    if req is None or req["status"] != "pending":
        conn.close()
        flash("审批请求不存在或已处理。", "warning")
        return redirect(url_for("approvals"))

    cur.execute("SELECT * FROM documents WHERE id = ?", (req["doc_id"],))
    doc = cur.fetchone()
    if doc is None:
        conn.close()
        flash("关联文档不存在。", "warning")
        return redirect(url_for("approvals"))

    cur.execute(
        """
        SELECT * FROM approval_steps
        WHERE request_id = ? AND status = 'pending'
        ORDER BY step_order ASC LIMIT 1
        """,
        (request_id,),
    )
    step = cur.fetchone()
    if step is None:
        conn.close()
        flash("审批步骤异常。", "warning")
        return redirect(url_for("approvals"))

    signed_at = datetime.now(timezone.utc).isoformat()
    meaning = "Approved" if decision == "approve" else "Rejected"
    doc_hash = compute_doc_hash(doc["file_path"], current_user.username, meaning, signed_at)
    execute_with_retry(
        cur,
        """
        INSERT INTO signatures (user, meaning, doc_id, doc_version, doc_hash, ip_address, user_agent)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            current_user.username,
            meaning,
            doc["id"],
            doc["version"],
            doc_hash,
            request.headers.get("X-Forwarded-For", request.remote_addr),
            request.headers.get("User-Agent"),
        ),
    )
    signature_id = cur.lastrowid

    new_status = "approved" if decision == "approve" else "rejected"
    execute_with_retry(
        cur,
        """
        UPDATE approval_steps
        SET status = ?, decided_by = ?, decided_at = CURRENT_TIMESTAMP, comment = ?, signature_id = ?
        WHERE id = ?
        """,
        (new_status, current_user.username, comment, signature_id, step["id"]),
    )

    if decision == "approve":
        execute_with_retry(
            cur,
            "UPDATE approval_requests SET status = 'approved' WHERE id = ?",
            (request_id,),
        )
        execute_with_retry(
            cur,
            """
            UPDATE documents
            SET status = 'archived'
            WHERE device_id = ? AND doc_type = ? AND status = 'active' AND id != ?
            """,
            (doc["device_id"], doc["doc_type"], doc["id"]),
        )
        execute_with_retry(
            cur,
            "UPDATE documents SET status = 'active' WHERE id = ?",
            (doc["id"],),
        )
        log_action_with_cursor(
            cur,
            current_user.username,
            "approve_document",
            "document",
            doc["id"],
            "审批通过",
            before_value={"status": "pending"},
            after_value={"status": "active"},
            reason=comment or None,
            ip_address=request.headers.get("X-Forwarded-For", request.remote_addr),
        )
        flash("审批通过。", "success")
    else:
        execute_with_retry(
            cur,
            "UPDATE approval_requests SET status = 'rejected' WHERE id = ?",
            (request_id,),
        )
        execute_with_retry(
            cur,
            "UPDATE documents SET status = 'draft' WHERE id = ?",
            (doc["id"],),
        )
        log_action_with_cursor(
            cur,
            current_user.username,
            "reject_document",
            "document",
            doc["id"],
            "审批拒绝",
            before_value={"status": "pending"},
            after_value={"status": "draft"},
            reason=comment or None,
            ip_address=request.headers.get("X-Forwarded-For", request.remote_addr),
        )
        flash("已拒绝。", "warning")

    commit_with_retry(conn)
    conn.close()
    return redirect(url_for("approvals"))


@app.route("/return/<int:borrow_id>", methods=["POST"])
@login_required
def return_doc(borrow_id):
    """归还文档并更新借阅记录。"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM borrow_records WHERE id = ?", (borrow_id,))
    record = cur.fetchone()
    if record is None:
        conn.close()
        flash("借阅记录不存在。", "warning")
        return redirect(url_for("borrow_list"))

    if record["borrower"] != current_user.username:
        conn.close()
        flash("仅借阅人本人可归还文档。", "warning")
        return redirect(url_for("borrow_list"))

    if record["status"] == "returned":
        conn.close()
        flash("该记录已归还。", "info")
        return redirect(url_for("borrow_list"))

    cur.execute(
        """
        UPDATE borrow_records
        SET status = 'returned', return_date = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (borrow_id,),
    )
    conn.commit()
    log_action(
        current_user.username,
        "return_document",
        "borrow",
        borrow_id,
        "归还文档",
    )
    conn.close()
    flash("归还成功。", "success")
    return redirect(url_for("borrow_list"))


@app.route("/borrow_list")
@login_required
def borrow_list():
    """借阅历史列表，用于追溯。"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT b.*, d.doc_name, d.version, d.device_id, d.doc_type
        FROM borrow_records b
        JOIN documents d ON d.id = b.doc_id
        ORDER BY b.borrow_date DESC
        """
    )
    rows = cur.fetchall()
    conn.close()
    return render_template("borrow_list.html", rows=rows, doc_type_labels=DOC_TYPE_LABELS)


@app.route("/documents")
@login_required
def document_search():
    """文档检索：按名称、设备、类型、状态与日期范围过滤。"""
    query = request.args.get("q", "").strip()
    device_query = request.args.get("device", "").strip()
    uploader = request.args.get("uploader", "").strip()
    doc_type = request.args.get("doc_type", "").strip()
    status = request.args.get("status", "").strip()
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()

    sql = (
        "SELECT d.*, dev.device_code, dev.device_name "
        "FROM documents d "
        "JOIN devices dev ON dev.id = d.device_id "
        "WHERE d.is_deleted = 0"
    )
    params = []

    if query:
        sql += " AND d.doc_name LIKE ?"
        params.append(f"%{query}%")
    if device_query:
        sql += " AND (dev.device_code LIKE ? OR dev.device_name LIKE ?)"
        params.extend([f"%{device_query}%", f"%{device_query}%"])
    if uploader:
        sql += " AND d.uploaded_by LIKE ?"
        params.append(f"%{uploader}%")
    if doc_type:
        sql += " AND d.doc_type = ?"
        params.append(doc_type)
    if status:
        sql += " AND d.status = ?"
        params.append(status)
    if start_date:
        sql += " AND date(d.upload_time) >= date(?)"
        params.append(start_date)
    if end_date:
        sql += " AND date(d.upload_time) <= date(?)"
        params.append(end_date)

    sql += " ORDER BY d.upload_time DESC"

    conn = get_db()
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()

    return render_template(
        "documents.html",
        rows=rows,
        query=query,
        device_query=device_query,
        uploader=uploader,
        doc_type=doc_type,
        status=status,
        start_date=start_date,
        end_date=end_date,
        doc_types=DOC_TYPES,
        doc_status_labels=DOC_STATUS_LABELS,
        doc_type_labels=DOC_TYPE_LABELS,
    )


@app.route("/audit_log")
@admin_required
def audit_log():
    """管理员查看审计日志（只读）。"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM audit_logs ORDER BY log_time DESC LIMIT 500"
    )
    rows = cur.fetchall()
    conn.close()
    return render_template("audit_log.html", rows=rows)


@app.route("/delete_doc/<int:doc_id>", methods=["POST"])
@admin_required
def delete_doc(doc_id):
    """管理员软删除文档，保留合规记录。"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
    doc = cur.fetchone()
    if doc is None:
        conn.close()
        flash("文档不存在。", "warning")
        return redirect(url_for("index"))

    cur.execute("UPDATE documents SET is_deleted = 1 WHERE id = ?", (doc_id,))
    conn.commit()
    log_action(
        current_user.username,
        "delete_document",
        "document",
        doc_id,
        f"删除 {doc['doc_name']} v{doc['version']}",
    )
    conn.close()
    flash("文档已删除。", "success")
    return redirect(url_for("device_detail", device_id=doc["device_id"]))


@app.route("/dashboard")
@login_required
def dashboard():
    """设备看板：支持按状态筛选、搜索与分页，返回状态汇总与设备列表。"""
    # 参数：status（可选）、q（关键词）、page、per_page
    status_filter = request.args.get("status", "").strip()
    q = request.args.get("q", "").strip()
    try:
        page = max(1, int(request.args.get("page", 1)))
    except Exception:
        page = 1
    try:
        per_page = max(5, int(request.args.get("per_page", 20)))
    except Exception:
        per_page = 20

    conn = get_db()
    cur = conn.cursor()
    # 按状态统计（全部设备，不受筛选影响）
    cur.execute(
        "SELECT status, COUNT(*) as cnt FROM devices WHERE is_deleted IS NULL OR is_deleted = 0 GROUP BY status"
    )
    counts_rows = cur.fetchall()
    status_counts = {r["status"]: r["cnt"] for r in counts_rows}

    # 构造分页查询
    params = []
    where = "WHERE is_deleted IS NULL OR is_deleted = 0"
    if status_filter:
        where += " AND status = ?"
        params.append(status_filter)
    if q:
        where += " AND (device_code LIKE ? OR device_name LIKE ? OR model LIKE ? OR location LIKE ?)"
        like = f"%{q}%"
        params.extend([like, like, like, like])

    # 总计用于分页
    count_sql = f"SELECT COUNT(*) as total FROM devices {where}"
    cur.execute(count_sql, params)
    cur.fetchone()

    # 修正：正确获取 total
    cur.execute(count_sql, params)
    total = cur.fetchone()["total"]

    offset = (page - 1) * per_page
    list_sql = f"SELECT id, device_code, device_name, model, location, status FROM devices {where} ORDER BY status, device_code LIMIT ? OFFSET ?"
    list_params = params + [per_page, offset]
    cur.execute(list_sql, list_params)
    devices = [dict(r) for r in cur.fetchall()]

    # 状态标签（中文）
    status_labels = {
        "active": "运行",
        "maintenance": "维护",
        "inactive": "停用",
        "retired": "报废",
        "debug": "调试",
        "standby": "待机",
        "repair": "维修",
    }

    conn.close()

    pagination = {
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": (total + per_page - 1) // per_page,
    }

    return render_template(
        "device_board.html",
        status_counts=status_counts,
        devices=devices,
        status_labels=status_labels,
        selected_status=status_filter,
        q=q,
        pagination=pagination,
    )


if __name__ == "__main__":
    # 初始化数据库结构与默认账号，然后启动开发服务器。
    init_db()
    app.run(debug=True, use_reloader=False)
