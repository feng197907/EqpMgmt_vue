# 设备档案文档管理系统 (DMS)

一个基于 Flask + SQLite 的设备档案与文档管理系统，支持设备台账、文档上传下载、借阅管理、审批流、审计日志和基础权限控制。

## 主要功能

- 设备档案管理：新增、编辑、停用、查询设备。
- 设备看板：按状态展示设备统计与列表。
- 文档管理：支持上传、下载、版本控制和文档状态流转。
- 借阅管理：记录文档借阅与归还。
- 审批流程：支持基础审批与电子签名确认。
- 权限控制：支持 7 种角色（管理员、QA经理、设备工程师、验证工程师、档案管理员、生产主管、计量工程师），每种角色有独立的功能权限。
- 审计日志：记录关键操作，便于追踪变更。

## 环境要求

- Python 3.10+。
- Windows 下推荐使用项目自带虚拟环境 `.venv`。

## 快速开始

1. 安装依赖：

```bash
.venv\\Scripts\\python.exe -m pip install -r requirements-dev.txt
```

2. 启动服务：

```bash
.venv\\Scripts\\python.exe app.py
```

3. 打开浏览器访问：

```text
http://127.0.0.1:5000
```

## 测试

项目提供了基于 `pytest` 的自动化测试。安装开发依赖后可执行：

```bash
.venv\\Scripts\\python.exe -m pytest
```

测试会使用临时数据库文件，不会影响本地的 `dms.db`。

## 默认账号

- admin / admin123
- user / user123

首次启动时会自动初始化 SQLite 数据库，并写入上述默认账号。

## 本地验证建议

1. 使用 `admin` 登录后新增设备。
2. 进入设备详情页，上传文档并确认版本号自动递增。
3. 在设备详情页下载文档，观察下载次数递增。
4. 进入“借阅记录”查看借阅与归还。
5. 管理员可在设备列表中停用/启用设备，并在“审计日志”中查看操作记录。

## 项目结构

```
DMS/
├── app.py                 # Flask 应用入口（工厂函数）
├── config.py              # 全局配置（角色、权限、文档类型等）
├── extensions.py          # Flask 扩展（LoginManager 单例）
├── database.py            # SQLite 初始化与迁移
├── models/
│   └── user.py            # User 模型
├── blueprints/            # Flask Blueprint 模块化路由
│   ├── auth.py            # 认证（登录/登出）
│   ├── devices.py         # 设备管理
│   ├── documents.py       # 文档管理
│   ├── borrowing.py       # 借阅管理
│   ├── approvals.py      # 审批流程
│   ├── device_changes.py # 设备变更
│   ├── users.py           # 用户管理
│   └── dashboard.py      # 看板
├── utils/                 # 工具函数
│   ├── decorators.py      # 权限装饰器（@admin_required, @role_required）
│   ├── audit.py           # 审计日志
│   ├── file_utils.py      # 文件处理
│   ├── db_utils.py        # 数据库操作
│   └── helpers.py         # 辅助函数
├── templates/             # Jinja2 页面模板
├── static/                # 前端样式资源
├── tests/                 # 自动化测试
└── uploads/              # 上传文件存储
```

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

## 说明

- 上传文件保存在 `uploads/` 目录。
- 数据库存储文件为 `dms.db`。
- 如果是首次部署，直接启动应用即可自动建表。

## 常见问题

### 1. 登录后看不到内容

请确认已使用默认账号登录，或者检查当前账号是否被管理员停用。

### 2. 启动时报数据库字段缺失

首次启动时系统会自动执行轻量迁移；如果是旧数据库，请直接重启一次应用，让迁移逻辑完成。

### 3. 上传文件失败

请确认文件格式在允许范围内，当前支持 `pdf`、`doc`、`docx`、`xls`、`xlsx`、`jpg`、`jpeg`、`png`。

## 计划中的能力

当前仓库已覆盖核心 MVP 功能，并在持续完善中，包括：

- 更完整的 REST API。
- 更细粒度的审批流。
- 更完善的文档生命周期管理。
- 更全面的单元测试覆盖。
