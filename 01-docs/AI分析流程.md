# AI 分析流程

## 一、流程总览

```
用户点击"AI分析" → 前端 POST /api/docs/generate/{id} → 后端启动后台任务
       ↓                                                    ↓
  弹出进度对话框                                    后台：读取项目代码 → 生成9个文档
       ↓                                                    ↓
  每2秒轮询 GET /api/docs/status/{task_id}  ←────  更新 doc_tasks 内存状态
       ↓
  完成/失败 → 关闭对话框
```

---

## 二、触发入口

**前端**：`ProjectsPage.vue` 项目卡片中的"AI分析"按钮

**条件**：项目必须有 `local_path`（已下载到本地），否则提示"请先下载"

---

## 三、后端 API

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/docs/generate/{project_id}` | POST | 启动文档生成，返回 `task_id` |
| `/api/docs/status/{task_id}` | GET | 查询任务进度和各文档状态 |
| `/api/docs/{project_id}` | GET | 获取项目已生成的文档列表 |
| `/api/docs/file/{project_id}/{doc_name}` | GET | 下载文档文件 |
| `/ws/docs/{task_id}` | WebSocket | 实时推送生成进度（备用） |

---

## 四、后端处理流程

### 4.1 启动任务

`POST /api/docs/generate/{project_id}` → `docs_gen.py:generate_docs()`

1. 从数据库查询项目，获取 `local_path` 和 `name`
2. 生成 `task_id`（UUID）
3. 初始化 `doc_tasks[task_id]`，包含 9 个文档的状态（均为"等待中"）
4. 将生成函数注册为 FastAPI BackgroundTask
5. 立即返回 `task_id` 给前端

### 4.2 后台生成

`generate_task()` 在后台线程执行：

```
1. 创建 WebDocGenerator 实例（读取 config.json 中的 AI 配置）
2. 调用 generator.generate_all_docs(local_path, project_name, progress_callback)
```

### 4.3 生成9个文档（分3阶段串行）

`WebDocGenerator.generate_all_docs()` 按阶段顺序执行：

**阶段1：Markdown 文档**
| 文档类型 | 文件名 | 内容 |
|---------|--------|------|
| `design_md` | `{项目名}-设计说明书-{日期}.md` | 架构设计、模块划分、设计模式 |
| `usage_md` | `{项目名}-使用说明书-{日期}.md` | 安装配置、功能说明、使用示例 |
| `value_md` | `{项目名}-价值点分析-{日期}.md` | 竞争力、竞品对比、市场前景 |

**阶段2：HTML 文档**（依赖阶段1的 MD）
| 文档类型 | 文件名 | 说明 |
|---------|--------|------|
| `design_html` | `{项目名}-设计说明书-{日期}.html` | MD → HTML，带现代 CSS 样式 |
| `usage_html` | `{项目名}-使用说明书-{日期}.html` | 同上 |
| `value_html` | `{项目名}-价值点分析-{日期}.html` | 同上 |

**阶段3：PPTX 文档**（依赖阶段2的 HTML）
| 文档类型 | 文件名 | 说明 |
|---------|--------|------|
| `design_pptx` | `{项目名}-设计说明书-{日期}.pptx` | HTML → PPTX |
| `usage_pptx` | `{项目名}-使用说明书-{日期}.pptx` | 同上 |
| `value_pptx` | `{项目名}-价值点分析-{日期}.pptx` | 同上 |

### 4.4 单个文档生成过程

`WebDocGenerator.generate_doc()`：

1. **检查文件是否已存在** → 已存在则标记"已存在"，跳过
2. **收集项目代码摘要** `_get_project_code_summary()`
   - 遍历项目目录树（排除 `.git`、`node_modules`、`__pycache__` 等）
   - 读取关键文件内容（README、main.py、index.js、config.* 等，每个最多 2000 字符）
3. **根据文档类型构建 prompt**
4. **调用 AI 生成**（根据 `analysis_method` 配置选择模式）

### 4.5 两种 AI 调用模式

**CLI 模式**（`analysis_method: "cli"`，默认）：

```
subprocess.run(["claude", "-p", "--print", "--append-system-prompt", ...], input=prompt, timeout=cli_timeout)
```

- 通过 stdin 传入 prompt，要求 claude CLI 直接将内容写入文件
- 失败后自动重试（最多 `retry_count` 次），间隔 `5 * attempt` 秒
- 超时由 `claude_cli_timeout` 控制（默认 600 秒）

**API 模式**（`analysis_method: "api"`）：

```
POST {base_url}/v1/messages  或  POST https://api.anthropic.com/v1/messages
Headers: x-api-key / Authorization: Bearer
Body: { model, max_tokens, system, messages }
```

- 请求超时由 `claude_api_timeout` 控制（默认 300 秒）
- 返回文本由代码写入文件（添加标题、时间戳头部）

### 4.6 进度回调

每完成一个文档，`progress_callback` 更新 `doc_tasks[task_id]`：
- 更新对应 `doc_key` 的状态（"生成中"/"已生成"/"已存在"/"失败"）
- 重新计算总进度百分比 = 已完成数 / 9 × 100

---

## 五、前端轮询流程

`ProjectsPage.vue` → `docsApi.getStatus(taskId)` 每 2 秒轮询

```
启动分析 → 获取 task_id → 打开进度对话框 → 开始轮询
                                    ↓
                      GET /api/docs/status/{task_id}
                                    ↓
                      更新对话框中的进度条和文档状态列表
                                    ↓
                      status === "completed" || "failed" → 停止轮询
```

对话框显示内容：
- 项目名称
- 总进度条（百分比）
- 状态消息
- 9 个文档的独立状态列表（图标 + 名称 + 状态文字）

---

## 六、输出文件位置

所有文档保存到 `{download_path}/01-docs/` 目录下。

默认配置下为 `./github_projects/01-docs/`：

```
github_projects/01-docs/
├── {项目名}-设计说明书-20260517.md
├── {项目名}-使用说明书-20260517.md
├── {项目名}-价值点分析-20260517.md
├── {项目名}-设计说明书-20260517.html
├── {项目名}-使用说明书-20260517.html
├── {项目名}-价值点分析-20260517.html
├── {项目名}-设计说明书-20260517.pptx
├── {项目名}-使用说明书-20260517.pptx
└── {项目名}-价值点分析-20260517.pptx
```

---

## 七、涉及的配置参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `analysis_method` | AI 调用模式：`"cli"` 或 `"api"` | `"cli"` |
| `claude_api_key` | API 模式必需的密钥 | 空 |
| `claude_model` | AI 模型名称 | `"glm-5"` |
| `claude_base_url` | API 代理地址（空则用官方） | 空 |
| `claude_max_tokens` | API 模式最大 token 数 | `16000` |
| `claude_cli_timeout` | CLI 模式超时（秒） | `1200` |
| `claude_api_timeout` | API 模式超时（秒） | `1200` |
| `claude_retry_count` | 失败重试次数 | `3` |
| `download_path` | 项目和文档的根目录 | `"../github_projects"` |

---

## 八、关键代码文件

| 文件 | 职责 |
|------|------|
| `frontend/src/pages/ProjectsPage.vue` | AI 分析按钮、进度对话框、轮询逻辑 |
| `frontend/src/api/project.ts` | `docsApi` 接口封装（generate、getStatus、getDocs） |
| `backend/app/api/docs_gen.py` | 文档生成 API 路由、任务管理 |
| `backend/app/core/doc_generator.py` | `WebDocGenerator` 核心生成器 |
| `backend/app/api/websocket.py` | WebSocket 实时推送（备用） |
