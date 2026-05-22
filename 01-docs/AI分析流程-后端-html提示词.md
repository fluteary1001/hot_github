# AI 分析流程 - 后端 HTML 提示词详解

## 一、HTML 生成流程概述

```
阶段1: 生成 MD 文件 → 阶段2: 读取 MD 内容 → 构建 prompt → 调用 AI → 生成 HTML 文件
```

HTML 文件**依赖**对应的 Markdown 文件，必须先生成 MD。

---

## 二、前置条件检查

### 2.1 文件路径映射

| 文档类型 | MD 路径 | HTML 路径 |
|----------|---------|-----------|
| `design_html` | `{项目名}-设计说明书-{日期}.md` | `{项目名}-设计说明书-{日期}.html` |
| `usage_html` | `{项目名}-使用说明书-{日期}.md` | `{项目名}-使用说明书-{日期}.html` |
| `value_html` | `{项目名}-价值点分析-{日期}.md` | `{项目名}-价值点分析-{日期}.html` |

### 2.2 依赖检查

```python
# doc_generator.py 第 279-282 行
md_type = doc_type.replace("_html", "_md")
md_path = output_path.replace(".html", ".md")
if not os.path.exists(md_path):
    return False, f"MD文件不存在: {md_path}"
```

**如果 MD 文件不存在**：直接返回失败，不调用 AI。

---

## 三、基础提示词（prompt）

### 3.1 提示词模板

```python
# doc_generator.py 第 288-298 行
prompt = f"""请将以下 Markdown 转换为精美 HTML 并保存到 {output_path}。

标题：{title}
Markdown 内容：
{md_content}

要求：
1. 完整 HTML 结构
2. 现代 CSS 样式
3. 响应式布局
4. 代码高亮样式"""
```

### 3.2 变量说明

| 变量 | 来源 | 示例值 |
|------|------|--------|
| `output_path` | 参数传入 | `/path/to/项目名-设计说明书-20260517.html` |
| `title` | `doc_type.split('_')[0].title()` | `项目名 Design` 或 `项目名 Usage` 或 `项目名 Value` |
| `md_content` | 读取 MD 文件 | 完整的 Markdown 文本内容 |

### 3.3 实际提示词示例

```
请将以下 Markdown 转换为精美 HTML 并保存到 /path/to/claude-code-设计说明书-20260517.html。

标题：claude-code Design
Markdown 内容：
# claude-code 设计说明书

生成时间: 2026-05-17 10:30:00

---

## 一、项目概述

Claude Code 是一个命令行工具...

## 二、系统架构设计

### 2.1 整体架构

...（完整 MD 内容）

要求：
1. 完整 HTML 结构
2. 现代 CSS 样式
3. 响应式布局
4. 代码高亮样式
```

---

## 四、系统提示词（system_prompt）

```python
# doc_generator.py 第 300 行
system_prompt = "你是一个前端开发者。"
```

**作用**：定义 AI 的角色，使其以前端开发者的视角生成 HTML。

---

## 五、CLI 模式完整提示词

CLI 模式会在基础提示词后追加文件写入要求：

```python
# doc_generator.py 第 334-343 行
full_prompt = f"""{prompt}

输出文件路径：{output_path}

要求：
1. 文件第一行为标题：# {title}
2. 第二行为生成时间：生成时间: {date_str}
3. 第三行为分隔线：---
4. 从第四行开始是正文内容
5. 直接将内容写入文件，不要输出到终端"""
```

### 5.1 CLI 完整提示词示例

```
请将以下 Markdown 转换为精美 HTML 并保存到 /path/to/claude-code-设计说明书-20260517.html。

标题：claude-code Design
Markdown 内容：
# claude-code 设计说明书

生成时间: 2026-05-17 10:30:00

---

## 一、项目概述
...

要求：
1. 完整 HTML 结构
2. 现代 CSS 样式
3. 响应式布局
4. 代码高亮样式

输出文件路径：/path/to/claude-code-设计说明书-20260517.html

要求：
1. 文件第一行为标题：# claude-code Design
2. 第二行为生成时间：生成时间: 2026-05-17 10:30:00
3. 第三行为分隔线：---
4. 从第四行开始是正文内容
5. 直接将内容写入文件，不要输出到终端
```

### 5.2 问题分析

**注意**：CLI 模式的追加要求是针对 Markdown 文件的格式，对 HTML 文件不适用：

| 要求 | 对 HTML 的影响 |
|------|----------------|
| `文件第一行为标题：# {title}` | ❌ HTML 不应以此开头 |
| `第二行为生成时间` | ❌ HTML 格式不同 |
| `第三行为分隔线：---` | ❌ 这是 Markdown 语法 |

**实际效果**：AI 会忽略这些不适用的要求，按照基础提示词中的"完整 HTML 结构"生成。

---

## 六、API 模式处理

API 模式不使用追加要求，直接使用基础提示词：

```python
# doc_generator.py 第 350-360 行
success, result = self._call_api_direct(prompt, system_prompt)
if success:
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# {title}\n\n")
        f.write(f"生成时间: {date_str}\n\n")
        f.write("---\n\n")
        f.write(result)
```

**问题**：API 模式会在 HTML 文件开头写入 Markdown 格式的标题，这是不正确的。

---

## 七、三种 HTML 文档的提示词差异

| 文档类型 | title 变量值 | 其他差异 |
|----------|--------------|----------|
| `design_html` | `{项目名} Design` | 无 |
| `usage_html` | `{项目名} Usage` | 无 |
| `value_html` | `{项目名} Value` | 无 |

**提示词模板相同**，仅 `title` 和 `md_content` 不同。

---

## 八、提示词改进（已实施）

### 8.1 改进内容

**1. 优化 HTML 基础提示词**：

```python
prompt = f"""请将以下 Markdown 转换为精美的 HTML 页面并保存到 {output_path}。

标题：{title}
Markdown 内容：
{md_content}

HTML 要求：
1. 使用 HTML5 文档结构（<!DOCTYPE html>）
2. 设置 UTF-8 字符编码
3. 内嵌现代 CSS 样式（不使用外部文件）
4. 响应式布局，适配移动端
5. 代码块使用语法高亮样式
6. 表格、列表等元素美观呈现
7. 深色主题，风格统一
8. 添加目录导航（如有多个章节）
9. 页面底部显示生成时间"""
```

**2. CLI 模式针对 HTML 类型跳过 Markdown 格式要求**：

```python
if doc_type.endswith("_html"):
    # HTML 类型：直接写入，不需要 Markdown 格式头部
    full_prompt = f"""{prompt}

输出文件路径：{output_path}

要求：
直接将完整的 HTML 内容写入文件，不要输出到终端"""
else:
    # MD/PPTX 类型：添加 Markdown 格式头部要求
    full_prompt = f"""{prompt}
...
"""
```

**3. API 模式针对 HTML 类型直接写入内容**：

```python
if doc_type.endswith("_html"):
    # HTML 类型：直接写入 AI 返回的内容
    f.write(result)
else:
    # MD/PPTX 类型：添加 Markdown 格式头部
    f.write(f"# {title}\n\n")
    ...
```

### 8.2 改进效果

| 改进项 | 改进前 | 改进后 |
|--------|--------|--------|
| HTML 结构要求 | 笼统的"完整 HTML 结构" | 明确 HTML5、UTF-8、DOCTYPE 等 |
| CSS 样式要求 | "现代 CSS 样式" | 指定内嵌样式、深色主题、语法高亮 |
| CLI 追加要求 | 对 HTML 写入 Markdown 格式头部 | HTML 类型跳过不适用的要求 |
| API 文件写入 | 对 HTML 写入 Markdown 格式头部 | HTML 类型直接写入 AI 返回内容 |

---

## 九、关键代码位置

| 功能 | 文件 | 行号 |
|------|------|------|
| HTML 类型判断 | `doc_generator.py` | 277 |
| MD 文件读取 | `doc_generator.py` | 279-285 |
| 标题生成 | `doc_generator.py` | 287 |
| 基础提示词 | `doc_generator.py` | 288-298 |
| 系统提示词 | `doc_generator.py` | 300 |
| CLI 追加要求 | `doc_generator.py` | 334-343 |
| API 文件写入 | `doc_generator.py` | 351-360 |
