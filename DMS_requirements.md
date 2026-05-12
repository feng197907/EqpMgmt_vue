# 设备档案文档管理系统（DMS）开发需求文档

## 1. 项目背景

在制药行业，设备档案管理需要遵循GMP规范，要求对设备的履历、URS、确认文件（DQ/IQ/OQ/PQ）、校准记录、维护记录、偏差报告、变更记录、图纸、手册等文档进行版本控制、审计追踪和借阅管理。本系统旨在替代传统纸质或共享文件夹方式，实现数字化、合规化的文档管理。

## 2. 用户角色

- **管理员（admin）**：所有功能权限，包括用户管理、审计日志查看、文档强制删除。
- **普通用户（user）**：可浏览设备、上传/下载文档、借阅/归还文档，但不能删除文档或查看审计日志。

## 3. 功能需求

### 3.1 用户认证
- 登录/登出
- 密码加密存储
- 基于Flask-Login的会话管理

### 3.2 设备管理
- 添加设备（设备编码唯一，名称、型号、位置）
- 设备列表展示（支持搜索）
- 设备停用/启用（软删除）

### 3.3 文档管理
- 文档类型：设备履历表、URS、DQ报告、IQ报告、OQ报告、PQ报告、校准记录、维护记录、偏差报告、变更记录、图纸、手册
- 上传文档：选择设备→选择文档类型→上传文件（PDF/Word/Excel/图片）→自动生成版本号（主版本.次版本，基于同一设备+文档类型自动递增）
- 文档列表：按设备查看，按文档类型分组，显示版本、上传人、上传时间、下载次数（可选）
- 下载文档
- 版本控制：同一文档类型可保存多个版本，下载时默认最新版本，但可历史版本列表查看/下载
- 删除文档（仅管理员，软删除或物理删除，需记录审计）

### 3.4 借阅管理
- 用户借阅文档：若文档未被借出，可借阅，状态变为“已借出”
- 归还：用户归还文档，状态变为“在库”
- 借阅记录：展示所有借阅历史（文档名称、借阅人、借阅日期、归还日期）

### 3.5 审计追踪
- 自动记录以下操作：登录/登出、创建设备、上传文档、下载文档、借阅文档、归还文档、删除文档
- 审计日志字段：操作人、操作时间、操作类型、目标对象（设备/文档/借阅）、详情
- 管理员可查看全部日志，普通用户不可见

### 3.6 文档借阅登记（支持线下实物借阅场景）
- 若文档为电子版，借阅本质是授予下载权限（本系统简化：借阅期允许下载，归还后禁止下载）
- 实现方式：借阅时生成一条记录，归还后关闭访问。系统实际可简单处理为：下载不受借阅限制（仅记录），或严格限制：只有借阅期内可下载。建议采用简单模式：借阅不阻断下载，只用于追溯。

## 4. 技术栈建议（与VSCode AI友好）

- **后端**：Python 3.9+，Flask（轻量，易调试）
- **数据库**：SQLite（开发简单，生产可换PostgreSQL）
- **前端**：HTML5 + Bootstrap 5（快速布局），Jinja2模板
- **文件存储**：本地文件夹 `uploads/`，按设备ID分目录存储（可选）
- **身份验证**：Flask-Login，密码使用 `werkzeug.security.generate_password_hash`
- **部署**：支持直接运行 `python app.py`，或使用 `gunicorn`

## 5. 数据库设计（SQLite）

### 表结构

#### 5.1 users
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | |
| username | TEXT UNIQUE | |
| password | TEXT | 哈希存储 |
| role | TEXT | admin / user |

#### 5.2 devices
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | |
| device_code | TEXT UNIQUE | 设备编码 |
| device_name | TEXT | |
| model | TEXT | |
| location | TEXT | |
| status | TEXT | active / inactive |
| created_at | TIMESTAMP | 默认CURRENT_TIMESTAMP |

#### 5.3 documents
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | |
| device_id | INTEGER FK | |
| doc_type | TEXT | 文档类型枚举值 |
| doc_name | TEXT | 原始文件名 |
| version | TEXT | 如 "1.0", "1.1", "2.0" |
| file_path | TEXT | 存储路径 |
| uploaded_by | TEXT | 用户名 |
| upload_time | TIMESTAMP | |
| remarks | TEXT | |
| is_deleted | INTEGER | 0/1 软删除 |

#### 5.4 borrow_records
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | |
| doc_id | INTEGER FK | |
| borrower | TEXT | 借阅人用户名 |
| borrow_date | TIMESTAMP | |
| return_date | TIMESTAMP | NULL表示未归还 |
| status | TEXT | borrowed / returned |

#### 5.5 audit_logs
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | |
| user | TEXT | |
| action | TEXT | 动作描述 |
| target_type | TEXT | device / document / borrow |
| target_id | INTEGER | 对应ID |
| details | TEXT | |
| log_time | TIMESTAMP | |

## 6. 页面及路由规划

| 路由 | 方法 | 说明 | 模板 |
|------|------|------|------|
| /login | GET/POST | 登录 | login.html |
| /logout | GET | 登出 | - |
| / | GET | 设备列表 | index.html |
| /add_device | GET/POST | 添加设备 | add_device.html |
| /device/<id> | GET | 设备详情（文档列表） | device_detail.html |
| /upload_doc/<device_id> | GET/POST | 上传文档 | upload_doc.html |
| /download/<doc_id> | GET | 下载文档 | - |
| /borrow/<doc_id> | POST | 借阅文档 | - |
| /return/<borrow_id> | POST | 归还文档 | - |
| /borrow_list | GET | 借阅记录列表 | borrow_list.html |
| /audit_log | GET | 审计日志（管理员） | audit_log.html |
| /delete_doc/<doc_id> | POST | 删除文档（管理员） | - |

## 7. 界面要求（简要）

- 使用Bootstrap 5，响应式布局
- 导航栏包含：设备管理、借阅记录、审计日志（仅admin）、用户名+登出
- 设备列表卡片或表格形式
- 设备详情页：上方显示设备基本信息，下方按文档类型折叠面板（accordion）展示文档，每个文档有版本、上传时间、操作按钮（下载、借阅、归还）
- 上传文档：下拉选择文档类型，文件选择，备注字段可选
- 借阅记录页：表格展示所有借阅记录，并显示归还按钮（当状态为borrowed时）

## 8. 非功能需求

- **安全性**：
  - 所有页面需登录访问（Flask-Login `@login_required`）
  - 文件上传类型限制（.pdf, .docx, .xlsx, .jpg, .png），大小≤20MB
  - 防止路径遍历攻击（使用 `secure_filename`）
- **合规性**：
  - 审计日志不可篡改（仅写入，无删除修改功能）
  - 文档版本号自动递增规则：同一设备+同一文档类型，新版本号为末位+1
- **易用性**：
  - 提供搜索设备功能
  - 支持按文档类型筛选显示

## 9. 开发环境配置（供VSCode AI参考）

- 创建虚拟环境：`python -m venv venv`
- 激活：`venv\Scripts\activate` (Windows) 或 `source venv/bin/activate` (Mac/Linux)
- 安装依赖：`pip install flask flask-login werkzeug`
- 运行：`python app.py`，默认端口5000
- 访问：`http://127.0.0.1:5000`

## 10. 开发任务拆解（建议按顺序）

1. 初始化项目文件夹结构，创建 `app.py`, `database.py`, `templates/`, `static/`, `uploads/`
2. 编写 `database.py` 创建所有表，插入初始用户（admin/admin123，user/user123）
3. 实现 `app.py` 基础Flask应用，配置 `UPLOAD_FOLDER`, `SECRET_KEY`
4. 实现登录/登出功能 (`login.html`, `logout`)
5. 实现设备列表及添加设备 (`index.html`, `add_device.html`)
6. 实现设备详情页，展示文档列表（从数据库读取）
7. 实现文档上传功能（自动版本控制、文件保存）
8. 实现文档下载功能
9. 实现借阅/归还功能及借阅记录页面
10. 实现审计日志自动记录与查看页面
11. 实现管理员删除文档（软删除）
12. 添加搜索、筛选等增强功能
13. 前端美化（Bootstrap）

## 11. 示例代码片段（提示AI生成风格）

建议向AI提问示例：

> “基于Flask实现一个文档管理系统，有设备管理、文档上传下载、版本控制、借阅记录、审计日志。请参考以下需求文档逐文件生成代码：...”