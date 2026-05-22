# AI 分析流程 - 后端详解

## 一、整体架构

```
前端请求 → FastAPI BackgroundTasks → 三阶段并行生成 → AI 调用（CLI/API）
    ↓              ↓                        ↓                    ↓
立即返回 task_id    后台线程执行              每阶段3线程并行         每个文档独立调用
```

**关键点**：
- 使用 FastAPI 的 `BackgroundTasks` 机制，后台线程执行
- **三阶段并行**：每阶段 3 个线程同时生成同类型文档
- 阶段间串行：MD → HTML → PPTX，保证依赖关系
- 每个文档生成时，通过 `progress_callback` 更新内存中的任务状态

---

## 二、线程模型

### 2.1 线程数量

| 阶段 | 线程 | 说明 |
|------|------|------|
| 请求处理 | FastAPI 工作线程 | 处理 `/api/docs/generate/{id}` 请求 |
| 后台任务 | 1 个主线程 | `BackgroundTasks.add_task()` 创建 |
| 阶段1 (MD) | **3 个并行线程** | 同时生成 design_md、usage_md、value_md |
| 阶段2 (HTML) | **3 个并行线程** | 同时生成 design_html、usage_html、value_html |
| 阶段3 (PPTX) | **3 个并行线程** | 同时生成 design_pptx、usage_pptx、value_pptx |

**结论**：每个阶段最多 **3 个并行线程**，阶段间串行等待。

### 2.2 为什么采用三阶段并行？

| 方案 | 优点 | 缺点 |
|------|------|------|
| 全串行（旧） | 简单、无并发问题 | 耗时长（9×T） |
| 全并行 | 最快 | API 限流、依赖冲突、OOM |
| **三阶段并行（新）** | 平衡速度与稳定性 | 需要阶段间同步 |

**优化效果**：
- 理论耗时：从 `9×T` 降至 `3×T`（假设同类型文档耗时相近）
- 实际效果：约减少 60% 总耗时

### 2.3 ThreadPoolExecutor 实现

```python
# doc_generator.py
with ThreadPoolExecutor(max_workers=3) as executor:
    futures = []
    for doc_type, filename in doc_list:
        future = executor.submit(generate_single_doc, doc_type, filename)
        futures.append(future)
    
    # 等待所有线程完成
    for future in futures:
        success, result, filename = future.result()
```

### 2.4 FastAPI BackgroundTasks 原理

```python
# docs_gen.py
background_tasks.add_task(generate_task)
```

- `add_task()` 将函数加入请求结束后的待执行队列
- 请求返回后，FastAPI 在**独立线程**中执行该函数
- 不阻塞当前请求，立即返回响应

---

## 三、任务状态管理

### 3.1 内存存储

```python
# docs_gen.py 第 18 行
doc_tasks: Dict[str, Dict[str, Any]] = {}
```

- 全局字典，存储所有进行中/已完成的任务
- Key: `task_id`（UUID）
- Value: 任务状态字典

### 3.2 任务状态结构

```python
{
    "status": "pending" | "generating" | "completed" | "failed",
    "progress": 0-100,
    "project_id": 123,
    "project_name": "项目名",
    "docs": {
        "design_md": "等待中" | "生成中" | "已生成" | "已存在" | "失败",
        "usage_md": "...",
        # ... 共 9 个文档状态
    },
    "message": "当前状态描述",
    "results": { ... }  # 完成后包含生成结果
}
```

### 3.3 进度回调机制

```python
# docs_gen.py 第 82-90 行
def progress_callback(doc_key: str, status: str):
    if task_id in doc_tasks:
        doc_tasks[task_id]["docs"][doc_key] = status
        # 计算总体进度
        completed = sum(1 for s in doc_tasks[task_id]["docs"].values()
                      if s in ["已生成", "已存在"])
        total = len(doc_tasks[task_id]["docs"])
        doc_tasks[task_id]["progress"] = int(completed / total * 100)
```

- 每个文档状态变化时调用
- 实时更新 `progress` 百分比
- 前端通过轮询 `GET /api/docs/status/{task_id}` 获取最新状态

---

## 四、文档生成流程

### 4.1 三阶段并行执行

```python
# doc_generator.py

# 阶段1: Markdown 文档（3个并行）
with ThreadPoolExecutor(max_workers=3) as executor:
    futures = [
        executor.submit(generate_single_doc, "design_md", filename1),
        executor.submit(generate_single_doc, "usage_md", filename2),
        executor.submit(generate_single_doc, "value_md", filename3)
    ]
    # 等待所有完成
    for future in futures:
        result = future.result()

# 阶段2: HTML 文档（3个并行，依赖阶段1的MD）
with ThreadPoolExecutor(max_workers=3) as executor:
    futures = [
        executor.submit(generate_single_doc, "design_html", filename4),
        executor.submit(generate_single_doc, "usage_html", filename5),
        executor.submit(generate_single_doc, "value_html", filename6)
    ]
    # 等待所有完成
    ...

# 阶段3: PPTX 文档（3个并行，依赖阶段2的HTML）
with ThreadPoolExecutor(max_workers=3) as executor:
    futures = [
        executor.submit(generate_single_doc, "design_pptx", filename7),
        executor.submit(generate_single_doc, "usage_pptx", filename8),
        executor.submit(generate_single_doc, "value_pptx", filename9)
    ]
    # 等待所有完成
    ...
```

### 4.2 阶段依赖关系

| 阶段 | 文档类型 | 依赖 | 并行数 |
|------|----------|------|--------|
| 阶段1 | MD | 无 | 3 |
| 阶段2 | HTML | 阶段1 的 MD 文件 | 3 |
| 阶段3 | PPTX | 阶段2 的 HTML 文件 | 3 |

### 4.3 单个文档生成步骤

```
1. 检查文件是否已存在 → 存在则跳过，标记"已存在"
2. 收集项目代码摘要 → _get_project_code_summary()
3. 构建 prompt → 根据文档类型选择模板
4. 调用 AI 生成 → CLI 或 API 模式
5. 写入文件 → API 模式需手动写入，CLI 模式已写入
6. 更新进度 → progress_callback()
```

### 4.4 项目代码摘要收集

```python
# doc_generator.py 第 53-82 行
def _get_project_code_summary(self, project_path: str, max_files: int = 50) -> str:
```

**收集内容**：
1. **目录结构**：遍历项目目录树（排除 `.git`、`node_modules`、`__pycache__` 等）
2. **关键文件内容**：读取 README、main.py、index.js、config.* 等文件（每个最多 2000 字符）

**排除规则**：
- 目录：`.` 开头、`node_modules`、`__pycache__`、`venv`、`dist`、`build`
- 文件：`.` 开头、`package-lock.json`、`yarn.lock`

**限制**：
- 目录结构最多 100 行
- 关键文件最多 20 个
- 每个文件内容最多 2000 字符

---

## 五、CLI 模式详解

### 5.1 命令构造

```python
# doc_generator.py 第 108-110 行
cmd = [claude_path, "-p", "--print"]
if system_prompt:
    cmd.extend(["--append-system-prompt", system_prompt])
```

**参数说明**：

| 参数 | 说明 |
|------|------|
| `-p` | 非交互模式，从 stdin 读取 prompt |
| `--print` | 将结果输出到 stdout |
| `--append-system-prompt` | 追加系统提示（定义 AI 角色） |

### 5.2 完整调用示例

```bash
claude -p --print --append-system-prompt "你是一个专业的技术文档分析师。" <<'EOF'
请分析以下 GitHub 项目 xxx，生成详细的设计说明书（Markdown格式）。

项目代码摘要:
...

输出文件路径：/path/to/output.md

要求：
1. 文件第一行为标题：# xxx 设计说明书
2. 第二行为生成时间：生成时间: 2026-05-17 10:30:00
3. 第三行为分隔线：---
4. 从第四行开始是正文内容
5. 直接将内容写入文件，不要输出到终端
EOF
```

### 5.3 调用方式

```python
# doc_generator.py 第 119-128 行
result = subprocess.run(
    cmd,
    input=file_prompt,          # prompt 通过 stdin 传入
    capture_output=True,        # 捕获 stdout/stderr
    text=True,
    encoding='utf-8',
    errors='replace',
    timeout=self.cli_timeout    # 默认 600 秒（10分钟）
)
```

**关键点**：
- `input=file_prompt`：prompt 通过 stdin 传入，避免命令行参数长度限制
- `capture_output=True`：捕获输出，不打印到终端
- `timeout`：超时后抛出 `subprocess.TimeoutExpired`

### 5.4 重试机制

```python
# doc_generator.py 第 113-148 行
for attempt in range(1, self.retry_count + 1):  # 默认重试 3 次
    try:
        result = subprocess.run(...)
        if result.returncode == 0:
            if os.path.exists(output_path):
                return True, output_path
            # CLI 返回成功但文件未生成
        # 失败，继续重试
    except subprocess.TimeoutExpired:
        last_error = f"CLI调用超时（{self.cli_timeout // 60}分钟）"
    
    if attempt < self.retry_count:
        time.sleep(5 * attempt)  # 退避等待：5s, 10s, 15s
```

**重试策略**：
- 最多重试 `retry_count` 次（默认 3 次）
- 每次失败后等待 `5 * attempt` 秒（指数退避）
- 超时、返回码非零、文件未生成都会触发重试

### 5.5 成功判断

```python
if result.returncode == 0 and os.path.exists(output_path):
    return True, output_path
```

- CLI 返回码为 0 **且** 文件实际存在才算成功
- 防止 CLI 返回成功但未实际写入文件的情况

---

## 六、API 模式详解

### 6.1 请求构造

```python
# doc_generator.py 第 156-175 行
if self.base_url:
    api_url = f"{self.base_url}/v1/messages"
    headers = {
        "Authorization": f"Bearer {self.api_key}",
        "content-type": "application/json"
    }
else:
    api_url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": self.api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
```

**两种认证方式**：

| 场景 | URL | 认证头 |
|------|-----|--------|
| 官方 API | `https://api.anthropic.com/v1/messages` | `x-api-key: {key}` |
| 第三方代理 | `{base_url}/v1/messages` | `Authorization: Bearer {key}` |

### 6.2 请求体

```python
payload = {
    "model": self.model,           # 如 "claude-sonnet-4-6"
    "max_tokens": self.max_tokens, # 默认 8192
    "system": system_prompt,       # 系统提示
    "messages": [{"role": "user", "content": prompt}]
}
```

### 6.3 调用方式

```python
# doc_generator.py 第 177-191 行
response = requests.post(
    api_url,
    headers=headers,
    json=payload,
    timeout=self.api_timeout  # 默认 300 秒（5分钟）
)
```

### 6.4 响应处理

```python
if response.status_code == 200:
    data = response.json()
    content = data.get("content", [])
    text = ""
    for item in content:
        if item.get("type") == "text":
            text += item.get("text", "")
    return True, text
```

### 6.5 文件写入

API 模式返回的是文本内容，需要手动写入文件：

```python
# doc_generator.py 第 351-360 行
if success:
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# {title}\n\n")
        f.write(f"生成时间: {date_str}\n\n")
        f.write("---\n\n")
        f.write(result)  # AI 返回的正文
```

---

## 七、配置参数影响

| 配置参数 | 影响位置 | 说明 |
|----------|----------|------|
| `analysis_method` | `generate_doc()` | 决定使用 CLI 还是 API |
| `claude_api_key` | `_call_api_direct()` | API 模式必需 |
| `claude_model` | API payload | 使用的模型 |
| `claude_base_url` | `_call_api_direct()` | API 端点地址 |
| `claude_max_tokens` | API payload | 最大生成 token 数 |
| `claude_cli_timeout` | `subprocess.run()` | CLI 超时时间 |
| `claude_api_timeout` | `requests.post()` | API 超时时间 |
| `claude_retry_count` | `_call_cli_for_file()` | CLI 重试次数 |
| `download_path` | `generate_all_docs()` | 文档输出目录 |

---

## 八、错误处理

### 8.1 CLI 模式错误

| 错误类型 | 处理方式 |
|----------|----------|
| `FileNotFoundError` | 直接返回失败，不重试 |
| `TimeoutExpired` | 记录错误，重试 |
| `returncode != 0` | 记录 stderr，重试 |
| 文件未生成 | 记录 stdout，重试 |

### 8.2 API 模式错误

| 错误类型 | 处理方式 |
|----------|----------|
| 无 API Key | 直接返回失败 |
| HTTP 错误 | 返回状态码和错误信息 |
| 响应内容为空 | 返回失败 |
| 网络异常 | 返回异常信息 |

### 8.3 任务级错误

```python
# docs_gen.py 第 110-112 行
except Exception as e:
    doc_tasks[task_id]["status"] = "failed"
    doc_tasks[task_id]["message"] = f"生成失败: {str(e)}"
```

- 任何未捕获的异常都会标记任务失败
- 错误信息存储在 `message` 字段，前端可显示

---

## 九、性能特征

### 9.1 时间估算

假设单个文档生成耗时 T，则总耗时：

| 方案 | 耗时公式 | 说明 |
|------|----------|------|
| 全串行（旧） | `9 × T` | 每个文档顺序生成 |
| **三阶段并行（新）** | `3 × T` | 每阶段 3 个并行 |

**优化效果**：理论耗时减少约 **66%**

实际耗时取决于：
- 项目代码量（影响 prompt 长度）
- AI 模型响应速度
- 网络延迟
- 是否有文件已存在（跳过）

### 9.2 资源消耗

| 资源 | 消耗 |
|------|------|
| CPU | 低（主要是 I/O 等待） |
| 内存 | 中高（并行时 3 个 prompt + 响应，约 30-150MB） |
| 网络 | 高（3 个并行 AI API 调用） |
| 磁盘 | 低（写入 9 个文件） |

### 9.3 并发限制

- **单任务**：每阶段最多 3 个并行线程
- **多任务**：可以同时启动多个项目的生成任务（不同 `task_id`）
- **实际限制**：AI API 速率限制是主要瓶颈

---

## 十、关键代码位置

| 功能 | 文件 | 行号 |
|------|------|------|
| 任务启动 | `docs_gen.py` | 41-120 |
| 后台任务函数 | `docs_gen.py` | 92-112 |
| 进度回调 | `docs_gen.py` | 82-90 |
| 生成器初始化 | `docs_gen.py` | 26-38 |
| 全部文档生成 | `doc_generator.py` | 373-449 |
| 单个文档生成 | `doc_generator.py` | 193-371 |
| CLI 调用 | `doc_generator.py` | 84-149 |
| API 调用 | `doc_generator.py` | 151-191 |
| 代码摘要收集 | `doc_generator.py` | 53-82 |
