---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: 271e30e7ab75d869e436a4d3f3508f69_7731b87d631f11f18c3c5254007bceed
    ReservedCode1: QAsjDuo19VLyObP/NftI6PR9HApieHP27MQgdPmOSYokcg+8QELOwInTIi2ZI9+MkprXJc6zf7wwoV4R41V6pLrrNb3n/qNT09BNzk2zJDQ06RyjwhIpNeGIVxcn7KW/C28Gnh4snt/5IYoU37p8kl/ey3Xoj1XIMMUYohjZ/ofLGVAuPQSZ0XBzJIA=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: 271e30e7ab75d869e436a4d3f3508f69_7731b87d631f11f18c3c5254007bceed
    ReservedCode2: QAsjDuo19VLyObP/NftI6PR9HApieHP27MQgdPmOSYokcg+8QELOwInTIi2ZI9+MkprXJc6zf7wwoV4R41V6pLrrNb3n/qNT09BNzk2zJDQ06RyjwhIpNeGIVxcn7KW/C28Gnh4snt/5IYoU37p8kl/ey3Xoj1XIMMUYohjZ/ofLGVAuPQSZ0XBzJIA=
---

# 设备档案文档管理系统 (DMS)

<div align="center">

![Python](https://img.shields.io/badge/Python-3.12-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-teal.svg)
![Vue](https://img.shields.io/badge/Vue-3.5-green.svg)
![Element Plus](https://img.shields.io/badge/Element_Plus-2.9-blueviolet.svg)
![MySQL](https://img.shields.io/badge/MySQL-8.0-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

**面向制药企业的 GMP 合规设备档案与文档管理系统**

FastAPI + Vue 3 前后端分离 · JWT 认证 · RBAC 权限 · 电子签名 · 审计追踪

[快速开始](#快速开始) · [功能概览](#功能概览) · [项目结构](#项目结构) · [API 文档](#api-文档)

</div>

---

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| **后端框架** | FastAPI 0.115 | 异步 Python Web 框架，自动生成 OpenAPI 文档 |
| **ORM** | SQLAlchemy 2.0 | 声明式模型，连接池管理 |
| **数据库** | MySQL 8.0 | 生产级关系型数据库 |
| **认证** | JWT (python-jose) | Access Token + Refresh Token 双令牌机制 |
| **密码** | passlib bcrypt + werkzeug | 兼容旧版 scrypt 哈希，新密码使用 bcrypt |
| **前端框架** | Vue 3.5 + Vite | Composition API，极速开发体验 |
| **UI 组件** | Element Plus 2.9 | 企业级 Vue 3 组件库 |
| **迁移工具** | Alembic | 数据库版本管理与增量迁移 |

---

## 功能概览

### 核心模块

| 模块 | 功能 | 说明 |
|------|------|------|
| **设备管理** | 新增/编辑/停用/报废 | 完整的设备生命周期管理 |
| **设备看板** | 状态统计与列表 | 可视化设备分布情况 |
| **设备变更** | 状态变更审批流 | 设备状态变更需审批+电子签名 |
| **设备维护** | 维护计划与执行 | 预防性维护管理，支持备件消耗 |
| **备件管理** | 库存/入库/消耗/预警 | 加权平均价计算，库存自动预警 |
| **文档中心** | 上传/下载/版本控制 | 支持多版本文档管理 |
| **借阅管理** | 借出/归还/审批 | 文档资产追踪 |
| **审批流程** | 多级审批+电子签名 | 数字化审批体验 |
| **仪表盘** | 统计概览 | 设备/维护/备件数据汇总 |

### 角色权限

| 角色 | 核心权限 |
|------|----------|
| **管理员** (admin) | 全部功能 |
| **QA经理** (qa_manager) | 文档审批、质量审批、报告查看 |
| **设备工程师** (equipment_engineer) | 设备操作、校准、维护 |
| **验证工程师** (validation_engineer) | IQ/OQ/PQ、文档审批 |
| **计量工程师** (metrology_engineer) | 设备校准、计量管理 |
| **生产主管** (production_supervisor) | 生产审批、文档审批、报告查看 |
| **文档管理员** (archivist) | 文档上传、归档管理 |

### 审计追踪

所有关键操作均记录审计日志，包含操作人、时间、IP、操作前后数据对比。

---

## 快速开始

### 环境要求

- Python 3.12+
- Node.js 16+
- MySQL 8.0+

### 安装步骤

```bash
# 1. 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # Linux/Mac

# 2. 安装后端依赖
pip install -r requirements.txt

# 3. 配置环境变量（复制示例文件并修改）
cp .env.example .env
# 编辑 .env，配置 DATABASE_URL、SECRET_KEY 等

# 4. 初始化数据库（创建库、导入表结构）
# 确保 MySQL 已运行，然后启动后端会自动建表
```

### 启动项目

**Windows（推荐）**：

```bash
start.bat
```

**手动启动**：

```bash
# 终端 1：启动后端
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

# 终端 2：启动前端
cd frontend
npm install
npm run dev
```

### 访问系统

| 服务 | 地址 |
|------|------|
| 前端界面 | http://localhost:5173 |
| 后端 API | http://localhost:8000 |
| API 文档 (Swagger) | http://localhost:8000/docs |
| API 文档 (ReDoc) | http://localhost:8000/redoc |

### 默认账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | admin123 |
| 设备工程师 | user | user123 |

> 首次登录后请立即修改默认密码。

---

## 项目结构

```
EquipmentManagement-Django/
├── backend/                     # FastAPI 后端
│   └── app/
│       ├── main.py              # 应用入口（路由注册、中间件、lifespan）
│       ├── api/                 # API 路由层
│       │   ├── auth.py          # 登录/刷新令牌/个人资料
│       │   ├── users.py         # 用户管理
│       │   ├── devices.py       # 设备管理
│       │   ├── documents.py     # 文档管理
│       │   ├── approvals.py     # 审批流程
│       │   ├── maintenance.py   # 设备维护
│       │   ├── spare_parts.py   # 备件管理
│       │   ├── borrowing.py     # 借阅管理
│       │   ├── esign.py         # 电子签名
│       │   ├── device_changes.py # 设备状态变更
│       │   ├── dashboard.py     # 仪表盘
│       │   ├── audit.py         # 审计日志
│       │   ├── password.py      # 密码管理
│       │   └── deps.py          # 依赖注入（get_db, get_current_user）
│       ├── services/            # 业务逻辑层
│       │   ├── auth_service.py  # 认证服务
│       │   ├── user_service.py  # 用户服务
│       │   ├── device_change_service.py
│       │   ├── maintenance_service.py
│       │   └── ...
│       ├── schemas/             # Pydantic 数据模型（请求/响应）
│       ├── models/              # SQLAlchemy ORM 模型
│       │   ├── user.py          # 用户表
│       │   ├── device.py        # 设备表
│       │   ├── document.py      # 文档表
│       │   ├── approval.py      # 审批表
│       │   ├── maintenance.py   # 维护计划/记录/维修记录
│       │   ├── spare_part.py    # 备件/入库/消耗/预警
│       │   ├── borrowing.py     # 借阅记录
│       │   ├── esign.py         # 电子签名
│       │   ├── device_change.py # 设备状态变更请求
│       │   ├── audit.py         # 审计日志/系统设置
│       │   └── password_reset.py
│       ├── middleware/          # 中间件
│       │   ├── rbac.py          # 基于角色的访问控制
│       │   └── audit.py         # 审计日志自动记录
│       ├── core/                # 核心配置
│       │   ├── config.py        # 应用配置（从 .env 加载）
│       │   └── security.py      # 密码哈希、JWT 令牌
│       └── db/
│           └── session.py       # 数据库引擎与会话工厂
│
├── frontend/                    # Vue 3 前端
│   ├── src/
│   │   ├── api/                 # Axios API 调用封装
│   │   ├── pages/               # 页面组件
│   │   ├── router/              # Vue Router 路由配置
│   │   └── assets/              # 静态资源
│   ├── package.json             # 前端依赖
│   └── vite.config.js           # Vite 构建配置
│
├── alembic/                     # 数据库迁移
├── docs/                        # 文档
│   ├── 使用手册.md
│   ├── ARCHITECTURE.md
│   ├── DEVELOPMENT.md
│   └── DEPLOYMENT.md
│
├── .env                         # 环境变量（不提交到版本控制）
├── .env.example                 # 环境变量示例
├── start.bat                    # Windows 一键启动脚本
├── start.ps1                    # PowerShell 启动脚本
└── test_startup.py              # 启动诊断脚本
```

---

## API 文档

启动后端后访问 Swagger UI 可查看完整 API：

```
http://localhost:8000/docs
```

### 主要 API 端点

| 模块 | 前缀 | 说明 |
|------|------|------|
| 认证 | `/api/v1/auth` | 登录、刷新令牌、个人资料、修改密码 |
| 用户 | `/api/v1/users` | 用户 CRUD |
| 设备 | `/api/v1/devices` | 设备管理、状态变更 |
| 文档 | `/api/v1/documents` | 文档上传/下载/审批 |
| 审批 | `/api/v1/approvals` | 审批流程处理 |
| 维护 | `/api/v1/maintenance` | 维护计划/记录/维修 |
| 备件 | `/api/v1/spare-parts` | 备件库存/入库/消耗/预警 |
| 借阅 | `/api/v1/borrowing` | 文档借阅管理 |
| 签名 | `/api/v1/esign` | 电子签名 |
| 审计 | `/api/v1/audit` | 审计日志查询 |
| 仪表盘 | `/api/v1/dashboard` | 统计数据 |
| 密码 | `/api/v1/password` | 密码重置 |

---

## 数据库

### 环境变量配置

`.env` 文件示例：

```env
DATABASE_URL=mysql+pymysql://root:Mysql%402025Root@127.0.0.1:3306/dms_db
SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_MINUTES=10080
```

### 数据库表

| 表名 | 说明 |
|------|------|
| `users` | 用户表（含角色、权限、电子邮箱等） |
| `devices` | 设备表 |
| `documents` | 文档表 |
| `approvals` / `approval_steps` | 审批流程 |
| `maintenance_plan` / `maintenance_record` / `repair_record` | 维护 |
| `spare_parts` / `spare_part_inbounds` / `spare_part_consumptions` / `spare_part_alerts` | 备件 |
| `borrow_records` | 借阅记录 |
| `electronic_signatures` | 电子签名 |
| `device_status_requests` | 设备状态变更 |
| `audit_logs` / `system_settings` | 审计与设置 |
| `esign_lockouts` | 签名锁定 |
| `password_resets` | 密码重置 |

---

## 常见问题

| 问题 | 解决方案 |
|------|----------|
| 启动报 MySQL 连接错误 | 确保 MySQL 服务已启动，`.env` 中 `DATABASE_URL` 配置正确 |
| `Unknown column` 错误 | 数据库表缺少字段，需要执行 `ALTER TABLE` 或使用 Alembic 迁移 |
| 登录报密码错误 | 检查 `SECRET_KEY` 是否与旧版一致；scrypt 哈希已兼容 |
| 前端页面空白 | 确认 `frontend` 已 `npm install`，且 Vite 端口未被占用 |
| CORS 错误 | 后端已配置 `localhost:5173` 和 `localhost:3000` 为允许源 |

---

## 参考文档

- [使用手册](docs/使用手册.md)
- [架构文档](docs/ARCHITECTURE.md)
- [开发指南](docs/DEVELOPMENT.md)
- [部署指南](docs/DEPLOYMENT.md)

---

## 开源协议

MIT License
*（内容由AI生成，仅供参考）*
