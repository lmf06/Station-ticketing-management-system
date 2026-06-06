# ADR-001: 使用 Vue 3 + Flask + MySQL 构建本地可部署售票系统

## Status
Accepted

## Date
2026-06-06

## Context
课程设计要求独立完成数据库应用系统，后台数据库使用 MySQL 或 SQL Server，前台开发工具自选。选题为汽车客运站售票管理系统，核心业务包括预售票、退票、换票和节假日浮动票价。

## Decision
采用 Vue 3 + Vite 构建前端，Flask 提供 REST API，Flask-SQLAlchemy 管理模型，PyMySQL 连接 MySQL 8.x。认证使用 Flask-Login 的 session cookie，角色分为旅客、售票员和管理员。

## Alternatives Considered

### Vue + Spring Boot
工程规范更强，但配置、代码量和调试成本更高，不利于 1 周课程设计周期内完成完整演示。

### Flask 模板一体化
部署更轻，但前后端边界不够清晰，页面交互和管理端表格维护体验较弱。

### SQLite 作为主数据库
启动方便，但不满足课程对 MySQL 平台的要求。SQLite 仅用于自动化测试隔离。

## Consequences
- MySQL 脚本可直接作为数据库建立和报告材料。
- Flask API 与 Vue 页面分离，便于展示接口、数据库和界面之间的数据流。
- 购票、退票、换票通过后端服务统一处理，便于保证事务和权限。
