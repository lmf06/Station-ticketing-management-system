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
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

2. 配置 MySQL。先用有权限的 MySQL 账号执行：

```sql
CREATE USER IF NOT EXISTS 'station_user'@'localhost' IDENTIFIED BY 'station_pass';
GRANT ALL PRIVILEGES ON station_ticketing.* TO 'station_user'@'localhost';
FLUSH PRIVILEGES;
```

然后导入数据库脚本：

```powershell
mysql -uroot -p < sql\mysql_schema.sql
mysql -uroot -p < sql\mysql_seed.sql
```

也可以复制 `.env.example` 为 `.env`，把 `DATABASE_URL` 改成本机 MySQL 账号。

3. 启动后端：

```powershell
.\.venv\Scripts\python.exe backend\run.py
```

4. 启动前端：

```powershell
cd frontend
npm install
npm run dev
```

访问 `http://127.0.0.1:5173`。

## 验证

```powershell
.\.venv\Scripts\python.exe -m pytest -q
cd frontend
npm run build
```

当前已覆盖的后端场景：节假日浮动票价、购票占座、余票不足拒绝、退票释放座位、换票生成新票、管理员权限控制、统一错误响应。
