# 设备档案文档管理系统 (DMS)

一个基于 Flask + SQLite 的设备档案与文档管理系统，支持设备台账、文档上传下载、借阅管理、审批流、审计日志、菜单权限和基础权限控制。

## 主要功能

- **设备档案管理**：新增、编辑、停用、报废、查询设备
- **设备看板**：按状态展示设备统计与列表
- **设备校准**：设备校准记录管理
- **设备维护**：维护计划与维护记录
- **文档管理**：支持上传、下载、版本控制和文档状态流转
- **借阅管理**：记录文档借阅与归还
- **审批流程**：支持基础审批与电子签名确认
- **菜单权限**：管理类角色可为用户分配菜单访问权限
- **密码重置**：用户可申请重置密码，管理类角色可审批处理
- **权限控制**：支持 7 种角色，每种角色有独立的功能权限
- **审计日志**：记录关键操作，便于追踪变更
- **系统设置**：可配置审批开关、文档自动生效等选项
- **提醒中心**：集中展示待办事项和提醒通知

## 环境要求

- Python 3.10+
- Windows 下推荐使用项目自带虚拟环境 `.venv`

## 快速开始

1. 安装依赖：

```bash
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

2. 启动服务：

```bash
.venv\Scripts\python.exe app.py
```

3. 打开浏览器访问：

```text
http://127.0.0.1:5000
```

## 默认账号

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | 管理员 |
| user | user123 | 设备工程师 |

> ⚠️ **安全提示**：首次登录后请务必修改默认密码！

首次启动时会自动初始化 SQLite 数据库，并写入上述默认账号。

## 本地验证建议

1. 使用 `admin` 登录后新增设备
2. 进入设备详情页，上传文档并确认版本号自动递增
3. 在设备详情页下载文档，观察下载次数递增
4. 进入"借阅记录"查看借阅与归还
5. 管理员可在设备列表中停用/启用设备
6. 进入"用户管理"为用户分配菜单权限
7. 在"审计日志"中查看操作记录

## 项目结构

```
DMS/
├── app.py                 # Flask 应用入口（工厂函数）
├── config.py              # 全局配置（角色、权限、菜单、文档类型等）
├── extensions.py          # Flask 扩展（LoginManager 单例）
├── database.py            # SQLite 初始化与迁移
├── requirements.txt       # Python 依赖
├── models/
│   └── user.py            # User 模型
├── blueprints/            # Flask Blueprint 模块化路由
│   ├── auth.py            # 认证（登录/登出）
│   ├── devices.py         # 设备管理
│   ├── documents.py       # 文档管理
│   ├── borrowing.py       # 借阅管理
│   ├── approvals.py       # 审批流程
│   ├── device_changes.py  # 设备变更
│   ├── users.py           # 用户管理
│   ├── dashboard.py       # 看板
│   ├── password.py        # 密码重置
│   ├── search.py          # 全局搜索
│   ├── settings.py        # 系统设置
│   └── maintenance.py     # 维护计划
├── utils/                 # 工具函数
│   ├── decorators.py      # 权限装饰器（@admin_required, @role_required）
│   ├── audit.py           # 审计日志
│   ├── file_utils.py      # 文件处理
│   ├── db_utils.py        # 数据库操作
│   └── helpers.py         # 辅助函数
├── templates/             # Jinja2 页面模板
├── static/                # 前端样式资源
├── tests/                 # 自动化测试
├── docs/                  # 文档目录
│   └── 使用手册.md         # 系统使用手册
└── uploads/               # 上传文件存储
```

## 数据库表结构

| 表名 | 说明 |
|------|------|
| users | 用户表（用户名、密码、角色、状态、权限） |
| devices | 设备表（编号、名称、型号、位置、状态） |
| documents | 文档表（关联设备、类型、名称、版本、路径） |
| borrow_records | 借阅记录表 |
| approval_requests | 审批请求表 |
| approval_steps | 审批步骤表 |
| signatures | 电子签名表 |
| audit_logs | 审计日志表 |
| system_settings | 系统设置表 |
| password_reset_requests | 密码重置请求表 |
| maintenance_plan | 维护计划表 |
| maintenance_record | 维护记录表 |

## 角色权限说明

| 角色 | 角色键值 | 主要功能 |
|------|----------|----------|
| 管理员 | admin | 所有功能 |
| QA经理 | qa_manager | 质量审批、报告查看 |
| 设备工程师 | equipment_engineer | 设备操作、校准维护 |
| 验证工程师 | validation_engineer | IQ/OQ/PQ管理 |
| 档案管理员 | archivist | 文档上传归档 |
| 生产主管 | production_supervisor | 生产审批 |
| 计量工程师 | metrology_engineer | 计量器具管理 |

### 菜单权限

| 菜单 | 说明 |
|------|------|
| dashboard | 数据看板 |
| device_management | 设备管理 |
| document_center | 文档中心 |
| user_management | 用户管理 |
| system_settings | 系统设置 |
| reminder_center | 提醒中心 |

管理员可为用户分配不同的菜单访问权限。

## 测试

项目提供了基于 `pytest` 的自动化测试。安装开发依赖后可执行：

```bash
.venv\Scripts\python.exe -m pytest
```

测试会使用临时数据库文件，不会影响本地的 `dms.db`。

## 云服务器部署

### 环境要求

- CentOS 7 / Ubuntu 20.04+
- Python 3.10+（腾讯云 CentOS 7 默认 Python 3.6，需升级或使用兼容密码）

### 部署步骤

1. 上传项目到服务器：

```bash
# 本地打包（排除 .venv, .git, docs 等）
zip -r dms.zip . -x "*.git*" -x "*.venv*" -x "__pycache__/*" -x "*.pyc" -x ".pytest_cache/*" -x "docs/*"

# 上传到服务器
scp dms.zip root@你的服务器IP:/data/EquipmentManagement/
```

2. 服务器上解压并安装依赖：

```bash
cd /data/EquipmentManagement
unzip dms.zip

# 安装 Python 依赖
pip3 install flask flask-login werkzeug gunicorn
```

3. 启动服务：

```bash
cd /data/EquipmentManagement
nohup gunicorn --bind 0.0.0.0:5000 --workers 2 app:app > gunicorn.log 2>&1 &
```

4. 开放端口（腾讯云控制台 → 安全组 → 添加入站规则）：

- 协议：TCP
- 端口：5000

### 服务管理命令

```bash
# 查看进程
ps aux | grep gunicorn

# 查看日志
tail -f /data/EquipmentManagement/gunicorn.log

# 停止
pkill -f gunicorn

# 重启
cd /data/EquipmentManagement
nohup gunicorn --bind 0.0.0.0:5000 --workers 2 app:app > gunicorn.log 2>&1 &

# 云服务器更新代码，重新部署
cd /data/EquipmentManagement
git pull origin main
pip3 install -r requirements.txt
pkill -f gunicorn
nohup gunicorn --bind 0.0.0.0:5000 --workers 2 app:app > gunicorn.log 2>&1 &
```

### 配置开机自启

```bash
cat > /etc/systemd/system/dms.service << 'EOF'
[Unit]
Description=DMS Equipment Management System
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/data/EquipmentManagement
ExecStart=/usr/bin/gunicorn --bind 0.0.0.0:5000 --workers 2 app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable dms
systemctl start dms
```

### GitHub Webhook 自动部署

#### 1. 服务器上初始化 Git 仓库

```bash
cd /data/EquipmentManagement
git init
git remote add origin https://github.com/你的用户名/你的仓库名.git
git config credential.helper store
git pull origin main
```

#### 2. 创建部署脚本

```bash
cat > /data/EquipmentManagement/deploy-webhook.sh << 'EOF'
#!/bin/bash
cd /data/EquipmentManagement
pkill -f gunicorn || true
git pull origin main
nohup gunicorn --bind 0.0.0.0:5000 --workers 2 app:app > gunicorn.log 2>&1 &
echo "部署完成: $(date)" >> deploy.log
EOF

chmod +x /data/EquipmentManagement/deploy-webhook.sh
```

#### 3. GitHub 配置 Webhook

- 仓库 → Settings → Webhooks → Add webhook
- Payload URL: `http://你的服务器IP:5001/webhook`
- Content type: `application/json`
- Events: Just push events
- Add webhook

## 数据库切换 (SQLite → MySQL)

项目默认使用 SQLite 数据库。如需切换到 MySQL，请按以下步骤操作：

### 1. 安装 MySQL 客户端库

```bash
pip install PyMySQL cryptography
```

### 2. 创建 MySQL 数据库

```sql
CREATE DATABASE dms_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'dms_user'@'%' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON dms_db.* TO 'dms_user'@'%';
FLUSH PRIVILEGES;
```

### 3. 修改数据库连接

编辑 `database.py`，将 `get_db()` 函数中的连接方式从 SQLite 改为 MySQL。

---

## 说明

- 上传文件保存在 `uploads/` 目录
- 数据库存储文件为 `dms.db`
- 如果是首次部署，直接启动应用即可自动建表
- 详细使用说明请参考 [使用手册](docs/使用手册.md)

## 常见问题

### 1. 登录后看不到内容

请确认已使用默认账号登录，或者检查当前账号是否被管理员停用。

### 2. 启动时报数据库字段缺失

首次启动时系统会自动执行轻量迁移；如果是旧数据库，请直接重启一次应用，让迁移逻辑完成。

### 3. 上传文件失败

请确认文件格式在允许范围内，当前支持 `pdf`、`doc`、`docx`、`xls`、`xlsx`、`jpg`、`jpeg`、`png`。

### 4. 忘记密码怎么办？

请联系系统管理员（admin），由管理员手动重置密码。

## 计划中的能力

当前仓库已覆盖核心 MVP 功能，并在持续完善中，包括：

- 更完整的 REST API
- 更细粒度的审批流
- 更完善的文档生命周期管理
- 更全面的单元测试覆盖
