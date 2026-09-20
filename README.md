# 车站售票管理系统

本项目是《数据库原理与应用课程设计》的汽车客运站售票管理系统，实现旅客购票、退票、换票，售票员窗口业务，管理员维护站点、线路、车辆、班次、节假日票价规则和用户数据。

## 技术栈

- 前端：Vue 3、Vite、Vue Router、Pinia、Element Plus、Axios
- 后端：Flask、Flask-SQLAlchemy、Flask-Login、PyMySQL
- 数据库：MySQL 8.x，InnoDB，utf8mb4，外键、事务和索引
- 测试：pytest，后端测试使用隔离内存数据库验证业务规则

## 目录

```text
backend/              Flask API、模型、服务、路由、测试
frontend/             Vue 前端
sql/                  MySQL 建表、种子数据、查询与事务示例
docs/                 课程设计说明、报告提纲、架构决策
Dockerfile            前端构建与 Flask/Gunicorn 生产镜像
```

## 演示账号

| 角色 | 账号 | 密码 |
| --- | --- | --- |
| 管理员 | admin | admin123 |
| 售票员 | staff | staff123 |
| 旅客 | passenger | passenger123 |

## 本地运行

1. 安装后端依赖：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt
```

2. 复制环境变量示例并设置随机密钥和本机数据库凭据：

```powershell
Copy-Item .env.example .env
```

然后用有权限的 MySQL 账号执行：

```sql
CREATE USER IF NOT EXISTS 'station_user'@'localhost' IDENTIFIED BY 'replace-with-a-strong-password';
GRANT ALL PRIVILEGES ON station_ticketing.* TO 'station_user'@'localhost';
FLUSH PRIVILEGES;
```

然后导入数据库脚本：

```powershell
cmd /c "mysql -uroot -p < sql\mysql_schema.sql"
cmd /c "mysql -uroot -p < sql\mysql_seed.sql"
```

如果数据库由旧版脚本创建且需要保留现有数据，请不要重新执行建表脚本，改为执行一次迁移：

```powershell
cmd /c "mysql -uroot -p station_ticketing < sql\migrations\001_add_orders_refunded_at.sql"
```

请确认 `.env` 中的 `DATABASE_URL` 与刚创建的 MySQL 用户一致；应用不会使用代码内置的默认口令。

3. 启动后端：

```powershell
.\.venv\Scripts\python.exe backend\run.py
```

4. 启动前端：

```powershell
cd frontend
npm ci
npm run dev
```

访问 `http://127.0.0.1:5173`。

## 本地 Docker 部署

本地阶段可使用 Docker Compose 同时启动网站和 MySQL：

```powershell
docker compose up --build --detach
docker compose ps
```

访问 `http://127.0.0.1:8000`。Compose 会创建持久化 MySQL 数据卷，并在首次启动时导入上方列出的演示账号；数据库端口不会暴露到宿主机。查看日志或停止服务：

```powershell
docker compose logs --follow app
docker compose down
```

`docker compose down` 会保留数据库数据；只有明确需要清空本地数据库时才使用 `docker compose down --volumes`。

## 验证

```powershell
.\.venv\Scripts\python.exe -m pytest -q
cd frontend
npm run build
```

当前已覆盖的后端场景：节假日浮动票价、购票占座、余票不足拒绝、退票释放座位、换票生成新票、管理员权限控制、统一错误响应。

## Docker 生产部署

生产镜像会先构建 Vue，再由 Gunicorn 运行 Flask 并从同一域名提供前端和 `/api`。数据库必须使用容器外部的 MySQL 8.x 服务。

```powershell
docker build --tag station-ticketing:local .
docker run --rm --env-file .env --publish 8000:8000 station-ticketing:local
```

首次连接空数据库时，只初始化表结构，不导入公开演示账号：

```powershell
docker run --rm --env-file .env --workdir /app/backend station-ticketing:local flask --app run:app init-db
```

公网环境随后通过隐藏密码提示创建首个管理员：

```powershell
docker run --rm --interactive --tty --env-file .env --workdir /app/backend station-ticketing:local flask --app run:app create-admin --username admin --display-name "系统管理员"
```

仅本地演示需要执行 `seed-demo`，公网环境不应使用 README 中的演示密码。

部署平台必须配置 `SECRET_KEY`、`DATABASE_URL` 和 `SESSION_COOKIE_SECURE=1`；平台可通过 `PORT` 指定监听端口。存活检查使用 `/healthz`，数据库就绪检查使用 `/readyz`。完整清单见 [生产部署指南](docs/deployment.md)。
