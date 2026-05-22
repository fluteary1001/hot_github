# GitHub Manager Web 启动指南

## 1. 启动后端（FastAPI，端口 8000）

```bash
cd github_manager_web/backend

# 安装依赖
pip install -r requirements.txt

# 可选：编辑 backend/config.json 配置 GitHub Token 等

# 启动
python run.py
```

后端 API 地址：`http://localhost:8000`

## 2. 启动前端（Vue 3 + Vite，端口 5173）

```bash
cd github_manager_web/frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端访问地址：`http://localhost:5173`

## 3. 可选配置

编辑 `backend/config.json` 配置参数（详见 `01-docs/配置参数说明.md`）：

```json
{
  "github_token": "ghp_xxxx",
  "claude_api_key": "sk-ant-xxxx"
}
```

默认登录账号：`admin` / `admin123`

## 汇总命令
1. 后端： → 端口 8000
cd backend ; pip install -r requirements.txt ; python run.py
2. 前端：→ 端口 5173
cd frontend ; npm install ; npm run dev 

