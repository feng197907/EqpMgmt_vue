# DMS 设备管理系统 — 渐进式重构 PRD

> **版本**：v1.0 | **日期**：2026-06-08 | **作者**：产品经理（Alice）
> **项目地址**：`D:\EquipmentManagement-Django`

---

## 1. 项目信息

| 字段 | 值 |
|------|------|
| 项目名称 | `dms-refactor` |
| 编程语言 | Python 3.10+ / FastAPI + SQLAlchemy ORM（后端）；Vue 3 + Element Plus + Vite（前端） |
| 原始需求 | 将现有 Flask + Jinja2 + 手写 SQL 的设备管理系统，渐进式重构为 FastAPI + Vue 3 SPA + SQLAlchemy ORM 架构 |

### 原始需求复述

现有 DMS 系统基于 Flask + Jinja2 + 手写 SQL 构建，存在安全风险（SQL 注入、硬编码密码）、架构混乱（双前端、双数据库、双签名系统）、性能问题（无连接池、SQLite 锁定）等 11 项已知问题。项目已在 `backend/` 目录建立 FastAPI 骨架和部分模型/路由，在 `frontend/` 目录建立 Vue 3 SPA 基础页面。本次重构的目标是在已有代码基础上补齐缺失模块、统一架构、消除技术债，实现从 Flask 到 FastAPI 的完整迁移。

---

## 2. 产品定义

### 2.1 产品目标

| # | 目标 | 成功标准 |
|---|------|----------|
| G1 | **消除安全风险** | 无手写 SQL、无硬编码密码、全 API 鉴权覆盖、SQL 注入风险为 0 |
| G2 | **统一技术架构** | 单一 FastAPI 后端 + 单一 Vue 3 前端 + 单一 SQLAlchemy ORM + 单一数据库（MySQL），Flask 代码完全移除 |
| G3 | **功能等价迁移** | 16+ 张表、14 个 Blueprint 的全部功能在新架构下可运行，零功能回退 |

### 2.2 用户故事

#### 认证与用户管理
- US-01：作为**管理员**，我想通过 JWT 认证登录系统，以便安全地访问管理功能
- US-02：作为**管理员**，我想重置用户密码（而非使用硬编码默认密码），以便保障账户安全
- US-03：作为**用户**，我想修改自己的密码和个人信息，以便保持个人资料的准确性

#### 设备管理
- US-04：作为**设备工程师**，我想对设备进行增删改查和状态切换，以便跟踪设备全生命周期
- US-05：作为**设备工程师**，我想通过扫描二维码快速查看设备详情，以便现场高效操作
- US-06：作为**QA 经理**，我想提交设备状态变更审批，以便状态变更受控（合规要求）

#### 文档与审批
- US-07：作为**档案管理员**，我想上传/下载/版本管理设备文档，以便文档与设备关联且可追溯
- US-08：作为**QA 经理**，我想发起多步骤审批流程，以便文档发布受控
- US-09：作为**档案管理员**，我想借出/归还文档并追踪借阅状态，以便实物文档可控

#### 维护与备件
- US-10：作为**计量工程师**，我想创建维护计划并记录执行结果，以便设备按期维护不遗漏
- US-11：作为**设备工程师**，我想管理备件入库/消耗/预警，以便备件库存合理、加权平均价准确
- US-12：作为**设备工程师**，我想记录设备维修历史，以便分析设备可靠性

#### 电子签名与审计
- US-13：作为**合规人员**，我想使用 21 CFR Part 11 合规的电子签名系统，以便满足法规要求
- US-14：作为**审计员**，我想查看全操作审计日志（含变更前后值），以便满足审计追踪要求

#### 系统功能
- US-15：作为**管理员**，我想在仪表盘看到到期维护提醒、校准逾期统计、审批待办计数，以便及时处理
- US-16：作为**用户**，我想通过全局搜索跨设备/文档/备件查找信息，以便快速定位资源

---

## 3. 需求池

### P0 — Must Have（重构核心，不完成则无法替换 Flask）

| ID | 需求 | 当前状态 | 重构内容 |
|----|------|----------|----------|
| P0-01 | **补齐缺失的 ORM 模型** | 缺少 ElectronicSignature、DeviceStatusRequest、PasswordResetRequest 等模型 | 新建缺失模型，对齐 Flask 系统 16+ 张表 |
| P0-02 | **补齐缺失的 Service 层** | 仅 auth_service.py | 为每个模块创建 service 层，将手写 SQL 逻辑迁移为 ORM 操作 |
| P0-03 | **补齐缺失的 API 路由** | 缺少 esign、device_changes、search、settings、dashboard、password 路由 | 对齐 Flask 14 个 Blueprint 的全部 API |
| P0-04 | **补齐缺失的 Pydantic Schema** | 缺少 esign、device_changes、search、settings、dashboard、password schema | 为所有 API 创建完整的请求/响应 Schema |
| P0-05 | **统一数据库为 MySQL + 连接池** | SQLite/MySQL 双轨 + 无连接池 | SQLAlchemy 连接池 + 单一 MySQL，移除 SQLite 兼容代码 |
| P0-06 | **移除手写 SQL** | database.py 1600+ 行手写 SQL | 全部替换为 SQLAlchemy ORM 操作 |
| P0-07 | **统一鉴权体系** | Flask-Login + JWT 并存 | 统一为 JWT + FastAPI Depends，移除 Flask-Login |
| P0-08 | **RBAC 权限中间件** | 仅 require_admin，7 种角色无细粒度控制 | 基于角色的权限装饰器/依赖，覆盖 7 种角色 |
| P0-09 | **移除硬编码默认密码** | admin/admin123 硬编码 | 首次部署强制修改密码或随机生成 |
| P0-10 | **Alembic 迁移体系** | 已有 alembic/ 目录，但迁移脚本不完整 | 确保所有模型有对应迁移，增量迁移可执行 |
| P0-11 | **审计中间件增强** | 仅记录请求日志，不记录变更前后值 | 实现与 Flask 系统等价的 before/after 值审计 |
| P0-12 | **统一电子签名系统** | 两套签名系统并存 | 仅保留 21 CFR Part 11 合规签名，移除旧版 |

### P1 — Should Have（架构质量与体验提升）

| ID | 需求 | 当前状态 | 重构内容 |
|----|------|----------|----------|
| P1-01 | **前端 API 模块补齐** | 缺少 approvals、settings、search、dashboard API 模块 | 补齐所有 API 调用函数 |
| P1-02 | **前端页面功能对齐** | 14 个页面已有骨架，但功能不完整 | 逐页面与 Flask 版本对齐所有交互 |
| P1-03 | **电子签名前端页面** | 无 esign 页面 | 新增电子签名管理页面 |
| P1-04 | **设备二维码功能** | 后端无 QR 生成 | 使用 qrcode 库生成二维码图片 |
| P1-05 | **Excel 导出功能** | Flask 版有导出 | 使用 openpyxl 在 FastAPI 中实现导出 |
| P1-06 | **API 路由前缀统一** | maintenance 路由在 `/api/v1/` 而非 `/api/v1/maintenance/` | 统一为 `/api/v1/{module}/` 前缀 |
| P1-07 | **全局搜索后端** | Flask 版有全文搜索 | 在 FastAPI 中实现跨设备/文档/备件搜索 |
| P1-08 | **仪表盘数据 API** | Flask 版有 dashboard 统计 | 实现 Dashboard 聚合查询 API |
| P1-09 | **密码重置流程** | Flask 版有密码重置请求审批 | 迁移密码重置请求/审批功能 |
| P1-10 | **系统设置 CRUD** | 已有 SystemSetting 模型 | 实现完整的键值对配置管理 API |
| P1-11 | **类型标注完善** | 部分代码缺少类型标注 | 所有函数添加参数/返回值类型标注 |

### P2 — Nice to Have（锦上添花）

| ID | 需求 | 说明 |
|----|------|------|
| P2-01 | **API 文档自动生成** | FastAPI 自带 Swagger，确保 Schema 完整即可 |
| P2-02 | **单元测试补齐** | 现有测试覆盖不足，为核心模块补充 pytest 测试 |
| P2-03 | **数据库索引优化** | 分析慢查询，为高频查询字段添加索引 |
| P2-04 | **前端响应式优化** | 移动端适配 |
| P2-05 | **操作日志导出** | 审计日志支持 Excel 导出 |
| P2-06 | **备件库存预警通知** | 库存低于安全阈值时主动通知 |

---

## 4. UI 设计稿

> 以下为各页面的功能布局描述，基于已有 Vue 3 + Element Plus 组件体系。

### 4.1 登录页（Login.vue）
- 居中卡片式登录表单：用户名 + 密码 + 登录按钮
- 登录成功后跳转至 Dashboard
- 支持记住登录状态（Token 持久化至 localStorage）

### 4.2 主布局（Layout.vue）
- 左侧导航栏：Logo + 菜单项（Dashboard、设备、文档、审批、维护、备件、借阅、审计日志、系统设置、搜索）
- 顶部栏：当前用户信息、通知铃铛（审批/密码重置待办计数）、退出按钮
- 右侧主内容区：`<router-view>` 渲染页面
- 菜单根据用户角色动态显示/隐藏

### 4.3 仪表盘（Dashboard.vue）
- 统计卡片行：设备总数、待审批数、到期维护数、校准逾期数
- 到期维护提醒列表（最近 30 天）
- 校准逾期统计
- 审批/密码重置待办列表（根据角色显示）

### 4.4 设备管理（Devices.vue）
- 设备列表表格：设备编号、名称、型号、位置、状态（7 种状态标签色）、操作
- 状态筛选下拉框 + 关键词搜索
- 新增/编辑设备弹窗表单
- 状态切换操作（触发审批流程）
- 二维码生成按钮
- Excel 导出按钮
- 软删除（逻辑删除）

### 4.5 文档管理（Documents.vue）
- 文档列表表格：文档名称、类型、版本、关联设备、状态、校准到期日、操作
- 按设备筛选 + 状态筛选
- 上传文档入口（跳转 UploadDocument）
- 下载/删除操作
- 版本历史查看

### 4.6 上传文档（UploadDocument.vue）
- 文件上传组件（Element Plus Upload）
- 元数据表单：文档类型、版本号、关联设备、校准到期日、备注
- 提交后返回文档列表

### 4.7 审批管理（Approvals.vue）
- 审批请求列表：文档名、发起人、当前步骤、状态、操作
- 审批决定弹窗：通过/拒绝 + 意见填写
- 审批流程进度可视化（步骤条）

### 4.8 维护管理（Maintenance.vue）
- Tab 切换：维护计划 / 维护记录 / 维修记录
- 维护计划列表：设备、类型（6 种）、周期、下次到期日、状态
- 维护记录列表：计划、执行人、执行日期、结果
- 维修记录列表：设备、内容、执行人、执行日期
- 新增/编辑弹窗 + Excel 导出

### 4.9 备件管理（SpareParts.vue）
- Tab 切换：备件主数据 / 入库记录 / 消耗记录 / 预警记录 / 统计
- 备件主数据表格：编码、名称、规格、库存、加权平均价、安全库存范围
- 入库弹窗：数量、单价、批次号
- 消耗弹窗：数量、关联维护记录
- 预警列表：低于安全库存的备件
- 统计视图：库存趋势、消耗趋势

### 4.10 借阅管理（Borrowing.vue）
- 借阅记录列表：文档名、借阅人、部门、借出日、应还日、实还日、状态
- 借出操作弹窗
- 归还操作
- 逾期高亮显示

### 4.11 用户管理（Users.vue）
- 用户列表：用户名、角色、状态、操作
- 新增用户弹窗
- 编辑角色/状态
- 管理员重置密码

### 4.12 审计日志（AuditLogs.vue）
- 日志列表：时间、用户、操作、目标类型、目标 ID、详情
- 变更前后值对比（展开行）
- 按用户/操作类型/时间范围筛选

### 4.13 系统设置（Settings.vue）
- 键值对配置表格
- 新增/编辑/删除设置项

### 4.14 全局搜索（Search.vue）
- 搜索输入框
- 结果分区展示：设备匹配 / 文档匹配 / 备件匹配
- 点击结果跳转至详情

### 4.15 个人中心（Profile.vue）
- 用户信息展示
- 修改用户名
- 修改密码

### 4.16 电子签名（新增页面）
- 签名解锁/锁定状态
- 签名验证
- 签名记录查询

---

## 5. 待确认问题

| # | 问题 | 影响 | 建议默认值 |
|---|------|------|------------|
| Q1 | **数据库选择**：是否完全移除 SQLite 支持，仅保留 MySQL？ | 影响部署灵活性和 `database.py` 清理范围 | 是，仅 MySQL |
| Q2 | **Flask 过渡期**：是否需要 FastAPI 和 Flask 并行运行一段时间？ | 影响架构设计（是否需要代理层分流） | 否，直接切换 |
| Q3 | **电子签名合并策略**：两套签名系统具体差异是什么？应保留哪套？ | 影响 esign 模块重构范围 | 保留 21 CFR Part 11 合规版 |
| Q4 | **密码策略**：首次部署是否强制修改默认密码？还是随机生成初始密码？ | 影响安全基线 | 随机生成 + 首次登录强制修改 |
| Q5 | **审计日志存储**：审计日志是继续存数据库还是引入 ELK 等外部系统？ | 影响审计模块架构和性能 | 继续存数据库（当前规模足够） |
| Q6 | **前端部署方式**：Vue SPA 是独立部署还是打包进 FastAPI 静态文件？ | 影响部署架构和 Nginx 配置 | 独立部署（开发时 Vite dev server，生产时 Nginx） |
| Q7 | **测试基线**：重构前是否需要为 Flask 系统编写集成测试作为回归基线？ | 影响重构质量和风险控制 | 建议为核心流程编写冒烟测试 |
| Q8 | **API 版本策略**：是否所有 API 统一使用 `/api/v1/` 前缀？ | 影响路由设计一致性 | 是，统一 `/api/v1/{module}/` |

---

## 附录 A：现有代码差距分析

### 后端差距（`backend/app/`）

| 层级 | 已有 | 缺失 |
|------|------|------|
| **Models** | User, Device, Document, ApprovalRequest/Step, MaintenancePlan/Record/Repair, SparePart/Inbound/Consumption/Alert, BorrowRecord, AuditLog, SystemSetting | ElectronicSignature, DeviceStatusRequest, PasswordResetRequest |
| **API Routes** | auth, devices, documents, approvals, maintenance, spare_parts, borrowing, audit, users | esign, device_changes, search, settings, dashboard, password |
| **Schemas** | auth, device, document, borrowing, maintenance, spare_part, audit | approval, esign, device_change, search, settings, dashboard, password, user |
| **Services** | auth_service | device, document, approval, maintenance, spare_part, borrowing, esign, search, settings, dashboard, password, audit |
| **Middleware** | AuditMiddleware（基础请求日志） | RBAC 权限中间件、变更值审计中间件 |

### 前端差距（`frontend/src/`）

| 层级 | 已有 | 缺失 |
|------|------|------|
| **Pages** | Login, Dashboard, Devices, Documents, UploadDocument, Approvals, Maintenance, SpareParts, Users, Borrowing, AuditLogs, Settings, Search, Profile, Layout | ESign（电子签名） |
| **API Modules** | audit, auth, borrowing, devices, documents, maintenance, spare_parts, users | approvals, settings, search, dashboard, esign |
| **功能** | 基础页面骨架 | 各页面完整交互逻辑、角色菜单控制、通知联动 |

---

## 附录 B：Flask Blueprint → FastAPI Router 映射

| Flask Blueprint | FastAPI Router | 状态 |
|-----------------|----------------|------|
| `auth_bp` | `api/auth.py` | ✅ 已迁移（基础版） |
| `devices_bp` | `api/devices.py` | ⚠️ 需增强（缺 QR、导出、状态审批） |
| `documents_bp` | `api/documents.py` | ⚠️ 需增强（缺版本管理、校准到期） |
| `approvals_bp` | `api/approvals.py` | ⚠️ 需增强 |
| `borrowing_bp` | `api/borrowing.py` | ⚠️ 需增强 |
| `maintenance_bp` | `api/maintenance.py` | ⚠️ 需增强 |
| `spare_part_bp` | `api/spare_parts.py` | ⚠️ 需增强 |
| `users_bp` | `api/users.py` | ⚠️ 需增强 |
| `audit_bp` | `api/audit.py` | ⚠️ 需增强（缺变更值审计） |
| `esign_bp` | — | ❌ 未迁移 |
| `device_changes_bp` | — | ❌ 未迁移 |
| `search_bp` | — | ❌ 未迁移 |
| `settings_bp` | — | ❌ 未迁移 |
| `dashboard_bp` | — | ❌ 未迁移 |
| `password_bp` | — | ❌ 未迁移 |
