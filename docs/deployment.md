# 生产部署指南

项目发布物是一个无状态 OCI/Docker 容器：Vite 在构建阶段生成前端文件，运行阶段由 Gunicorn 承载 Flask API 和前端静态资源。MySQL、TLS 和域名由部署平台或云服务负责。

## 1. 必需环境变量

| 变量 | 生产要求 |
| --- | --- |
| `SECRET_KEY` | 至少使用随机生成的长字符串，不得提交到 Git |
| `DATABASE_URL` | 外部 MySQL 地址，推荐 `mysql+pymysql://...`；密码中的特殊字符需要 URL 编码 |
| `SESSION_COOKIE_SECURE` | HTTPS 部署必须为 `1` |
| `PORT` | 平台注入；未设置时为 `8000` |
| `CORS_ORIGINS` | 前后端分域时填写前端 HTTPS 域名；同域部署无需依赖 CORS |

可用以下命令生成密钥：

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

连接池和进程参数均有保守默认值，可通过 `.env.example` 中的 `DB_*` 与 `WEB_*` 变量覆盖。连接池配置按每个 Gunicorn worker 计算，应确保：

```text
WEB_CONCURRENCY × (DB_POOL_SIZE + DB_MAX_OVERFLOW)
```

不超过托管 MySQL 的连接上限。

## 2. 构建镜像

```powershell
docker build --pull --tag station-ticketing:local .
```

镜像使用 Node 22 构建前端，最终 Python 3.12 slim 阶段只安装生产依赖，并以 UID/GID `10001` 的非 root 用户运行。

## 3. 初始化数据库

先在 MySQL 服务中创建空数据库和权限受限的应用账号。首次部署执行一次：

```powershell
docker run --rm --env-file .env --workdir /app/backend station-ticketing:local flask --app run:app init-db
```

`init-db` 只创建表。`seed-demo` 会写入公开演示账号，仅允许在本地或临时演示环境执行：

```powershell
docker run --rm --env-file .env --workdir /app/backend station-ticketing:local flask --app run:app seed-demo
```

生产环境通过交互式隐藏提示创建首个管理员，密码至少 12 位：

```powershell
docker run --rm --interactive --tty --env-file .env --workdir /app/backend station-ticketing:local flask --app run:app create-admin --username admin --display-name "系统管理员"
```

非交互式发布流程可临时注入 `ADMIN_PASSWORD`，命令完成后立即删除该平台密钥；不要把密码写进构建参数、Dockerfile 或仓库文件。

已有数据库应按版本执行 `sql/migrations/` 中的迁移，不要通过重新运行建表脚本覆盖数据。

## 4. 运行与平台设置

本地模拟生产容器：

```powershell
docker run --rm --env-file .env --publish 8000:8000 station-ticketing:local
```

云平台配置：

1. 构建方式选择仓库根目录的 `Dockerfile`。
2. 注入生产环境变量，不上传 `.env`。
3. 将 HTTP 健康检查路径设置为 `/healthz`。
4. 若平台支持发布前命令，使用 `flask --app /app/backend/run.py init-db`；已有库改用对应迁移。
5. 让平台终止 TLS，并将 `SESSION_COOKIE_SECURE` 设为 `1`。
6. 将 MySQL 防火墙限制为平台出站地址，并启用服务商提供的 TLS 连接参数。

## 5. 验证

```powershell
Invoke-RestMethod http://127.0.0.1:8000/healthz
Invoke-RestMethod http://127.0.0.1:8000/readyz
```

- `/healthz` 只验证 Web 进程存活。
- `/readyz` 会执行轻量数据库查询；数据库不可用时返回 HTTP 503。
- `/` 应返回 Vue 页面，刷新前端子路由仍应返回 `index.html`。
- `/assets/*` 应带一年期 immutable 缓存，HTML 应要求重新验证。

## 6. 发布前检查

- 后端测试通过：`python -m pytest backend/tests -q`
- 前端构建通过：`npm --prefix frontend run build`
- 镜像构建通过：`docker build .`
- 生产环境未使用演示账号、演示密码或本地 `.env`
- 数据库已备份，迁移已在副本或预发布环境验证
- `/healthz`、`/readyz`、登录、购票、退票和换票流程均正常
