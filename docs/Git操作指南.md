# Git 操作指南 —— 车站售票管理系统

## 当前状态

你的代码已保存为 **v1.0** 版本，有两个历史记录：

```
* f6da840 (tag: v1.0) v1.0: 车站售票管理系统 - 完整功能版本
* bb0f265 chore: initial commit
```

---

## 一、日常提交流程（新建版本）

每次做了有意义的修改后，执行以下三步保存为新版本：

```bash
# 第1步：查看改了什么
git status

# 第2步：把所有改动加入暂存区
git add -A

# 第3步：提交，写清楚这次改了什么
git commit -m "v1.1: 修复了XXX问题"

# 第4步（可选）：打标签方便以后回退
git tag -a v1.1 -m "修复了XXX问题"
```

**提交信息规范建议：**
- `v1.1: 修复登录页面样式错乱`
- `v1.2: 新增退票功能`
- `v1.2.1: 修复退票金额计算错误`

---

## 二、回退到历史版本

### 场景A：只是回去看看旧代码（不改动当前版本）

```bash
# 查看提交历史
git log --oneline

# 切到 v1.0 的代码看一眼
git checkout v1.0

# 看完回到最新版本
git checkout main
```

### 场景B：当前代码改坏了，想丢弃所有未提交的修改

```bash
# 丢弃所有改动，恢复到最近一次提交的状态
git checkout .

# 或者指定某个文件
git checkout -- backend/app/models.py
```

### 场景C：后悔了某次提交，想撤销它（保留改动内容）

```bash
# 撤销最近一次提交，改动回到工作区（可以重新修改再提交）
git reset --soft HEAD~1
```

### 场景D：彻底回退到某个历史版本（丢弃之后的所有改动）

```bash
# 先查看要回退到哪个版本
git log --oneline

# 硬回退到指定版本（比如 v1.0），之后的所有更改都会被丢弃
git reset --hard v1.0

# 如果已经推送过远程仓库，需要强制推送（谨慎！）
# git push --force
```

**`--hard` vs `--soft` 的区别：**
| 参数 | 效果 |
|------|------|
| `--soft` | 回退提交记录，但改动保留在工作区，可以重新修改 |
| `--mixed`（默认） | 回退提交记录，改动保留但取消暂存 |
| `--hard` | 彻底回退，所有改动全部丢弃 |

---

## 三、分支管理（推荐）

分支让你可以同时维护稳定版本和开发新功能：

```bash
# 创建并切换到 v2-dev 分支（基于当前代码开发 v2）
git checkout -b v2-dev

# 在 v2-dev 上开发……提交……
git add -A
git commit -m "v2-dev: 正在开发XXX功能"

# 查看所有分支
git branch -a

# 切换回主分支
git checkout main

# 等 v2 开发完成，合并到主分支
git checkout main
git merge v2-dev

# 合并后可以删除开发分支
git branch -d v2-dev
```

**建议的分支策略：**
```
main（主分支）
├── v1.0 (tag)
├── v1.1 (tag)
└── v2-dev（开发分支）
    └── 完成后合并回 main → 打 tag v2.0
```

---

## 四、查看历史和对比

```bash
# 查看提交历史（简洁版）
git log --oneline

# 查看提交历史（带改动内容）
git log -p

# 查看某个文件的改动历史
git log --oneline -- backend/app/models.py

# 对比两次提交的差异
git diff v1.0..v1.1

# 查看当前改了哪些内容（未提交的）
git diff

# 查看有哪些文件改动但未提交
git status
```

---

## 五、常见问题处理

### 提交了不该提交的文件（如 .env 里的密码）

```bash
# 从 git 跟踪中移除，但保留本地文件
git rm --cached .env

# 确保 .gitignore 里有它
echo ".env" >> .gitignore

# 提交这个移除操作
git add .gitignore
git commit -m "从版本控制中移除 .env"
```

### 提交信息写错了

```bash
# 修改最近一次提交的信息
git commit --amend -m "正确的新提交信息"
```

### 想放弃某次 add 操作（取消暂存）

```bash
# 取消暂存某个文件
git restore --staged backend/app/models.py

# 取消暂存所有文件
git restore --staged .
```

---

## 六、你的项目 .gitignore 已配置

以下内容不会被 git 跟踪（已写入 `.gitignore`）：

```
__pycache__/          # Python 缓存
*.pyc                 # 编译文件
.venv/                # 虚拟环境
.env                  # 环境变量（含密码）
instance/             # Flask 实例文件夹
frontend/node_modules/ # 前端依赖
frontend/dist/        # 前端构建产物
.idea/ .vscode/       # IDE 配置
*.log                 # 日志文件
```

---

## 七、Quick Reference（速查表）

| 操作 | 命令 |
|------|------|
| 保存新版本 | `git add -A && git commit -m "描述"` |
| 打标签 | `git tag -a v1.1 -m "描述"` |
| 查看历史 | `git log --oneline` |
| 回到旧版本看看 | `git checkout v1.0` |
| 回到最新 | `git checkout main` |
| 丢弃未提交改动 | `git checkout .` |
| 撤销最近一次提交 | `git reset --soft HEAD~1` |
| 彻底回退到 v1.0 | `git reset --hard v1.0` |
| 查看当前状态 | `git status` |
| 创建新分支 | `git checkout -b 分支名` |
| 切换分支 | `git checkout 分支名` |
| 合并分支 | `git merge 分支名` |
| 查看差异 | `git diff` |
