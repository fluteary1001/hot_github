"""Web版文档生成器 - 适配FastAPI异步环境"""
import os
import glob
import subprocess
import shutil
import time
import threading
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Callable, Dict, Any
import requests

from app.core.logger import get_logger

_logger = get_logger("doc_generator_web")


class WebDocGenerator:
    """Web版文档生成器 - 支持异步和进度回调"""

    def __init__(
        self,
        download_path: str,
        api_key: str = None,
        model: str = "claude-sonnet-4-6",
        base_url: str = None,
        max_tokens: int = 8192,
        cli_timeout: int = 600,
        api_timeout: int = 300,
        retry_count: int = 3,
        analysis_method: str = "cli"
    ):
        self.download_path = download_path
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.max_tokens = max_tokens
        self.cli_timeout = cli_timeout
        self.api_timeout = api_timeout
        self.retry_count = retry_count
        self.analysis_method = analysis_method
        self._claude_path = None

        _logger.info(f"初始化Web文档生成器，模型: {model}, 方法: {analysis_method}")

    def _get_claude_path(self) -> Optional[str]:
        """获取 Claude CLI 路径（缓存）"""
        if self._claude_path is None:
            self._claude_path = shutil.which("claude")
        return self._claude_path

    def _get_project_code_summary(self, project_path: str, max_files: int = 50) -> str:
        """获取项目代码结构摘要"""
        path = Path(project_path)
        if not path.exists():
            return "项目目录不存在"

        structure = []
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv', 'dist', 'build']]
            level = root.replace(str(path), '').count(os.sep)
            indent = '  ' * level
            structure.append(f"{indent}{os.path.basename(root)}/")
            for file in files[:10]:
                if not file.startswith('.') and file not in ['package-lock.json', 'yarn.lock']:
                    structure.append(f"{indent}  {file}")

        key_files_content = []
        key_patterns = ['README*', '*.md', 'main.py', 'index.js', 'app.py', 'config.*']

        for pattern in key_patterns:
            for file_path in glob.glob(str(path / pattern)):
                if len(key_files_content) < max_files:
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read(2000)
                            key_files_content.append(f"\n=== {file_path} ===\n{content}")
                    except Exception:
                        pass

        return f"目录结构:\n" + '\n'.join(structure[:100]) + "\n\n关键文件内容:\n" + '\n'.join(key_files_content[:20])

    def _call_cli_for_file(
        self,
        prompt: str,
        output_path: str,
        system_prompt: str = "",
        progress_callback: Callable[[str, str], None] = None,
        doc_key: str = None,
        shutdown_event = None
    ) -> tuple[bool, str]:
        """调用 Claude Code CLI 直接生成文件"""
        claude_path = self._get_claude_path()
        if not claude_path:
            return False, "未找到 claude 命令，请安装 Claude Code CLI"

        # 使用绝对路径，避免路径歧义
        abs_output_path = os.path.abspath(output_path)

        file_prompt = f"""请根据以下要求生成文档，并直接保存到指定路径。

输出文件路径：{abs_output_path}

要求：
1. 直接将生成的内容写入到上述指定的文件路径（必须使用绝对路径）
2. 不要输出文件内容到终端，只输出确认信息
3. 确保文件写入成功后，输出 "文件已生成：{abs_output_path}"

{prompt}"""

        # 添加 --dangerously-skip-permissions 避免交互式确认提示
        cmd = [claude_path, "-p", "--print", "--dangerously-skip-permissions"]
        if system_prompt:
            cmd.extend(["--append-system-prompt", system_prompt])

        last_error = ""
        for attempt in range(1, self.retry_count + 1):
            # 检查是否已关闭
            if shutdown_event and shutdown_event.is_set():
                return False, "任务已取消"

            if progress_callback and doc_key:
                progress_callback(doc_key, f"生成中 ({attempt}/{self.retry_count})")

            _logger.info(f"CLI生成文件: {abs_output_path} (尝试 {attempt}/{self.retry_count})")

            try:
                # 使用 run 方法，直接传递 input 参数
                result = subprocess.run(
                    cmd,
                    input=file_prompt,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    timeout=self.cli_timeout
                )

                # 安全解码输出（处理编码问题）
                def safe_decode(text: str, max_len: int = 500) -> str:
                    if not text:
                        return "(空)"
                    cleaned = ''.join(c if c.isprintable() or c in '\n\r\t' else '?' for c in text)
                    return cleaned[:max_len] if len(cleaned) > max_len else cleaned

                if result.returncode == 0:
                    _logger.info(f"CLI返回成功，检查文件是否存在: {abs_output_path}")
                    _logger.info(f"  os.path.exists: {os.path.exists(abs_output_path)}")

                    docs_dir = os.path.dirname(abs_output_path)
                    if os.path.exists(docs_dir):
                        files_in_dir = os.listdir(docs_dir)
                        _logger.info(f"  目录中的文件: {[f for f in files_in_dir if 'claw-code' in f][:5]}")

                    if os.path.exists(abs_output_path):
                        _logger.info(f"CLI生成成功: {abs_output_path}")
                        return True, abs_output_path
                    output = result.stdout.strip() if result.stdout else ""
                    last_error = f"CLI返回成功但文件未生成。输出: {safe_decode(output, 200)}"
                    _logger.warning(f"CLI返回成功但文件未生成: {abs_output_path}")
                    _logger.warning(f"  输出片段: {safe_decode(output, 500)}")
                else:
                    stdout_preview = safe_decode(result.stdout, 500)
                    stderr_preview = safe_decode(result.stderr, 500)
                    last_error = f"CLI错误: {stderr_preview[:200]}"
                    _logger.warning(f"CLI调用失败 (尝试 {attempt}/{self.retry_count}): {output_path}")
                    _logger.warning(f"  返回码: {result.returncode}")
                    _logger.warning(f"  stderr: {stderr_preview}")
                    _logger.warning(f"  stdout: {stdout_preview}")

            except subprocess.TimeoutExpired:
                last_error = f"CLI调用超时（{self.cli_timeout // 60}分钟）"
                _logger.warning(f"CLI调用超时 (尝试 {attempt}/{self.retry_count}): {output_path}, 超时时间: {self.cli_timeout}秒")
            except FileNotFoundError:
                return False, "未找到 claude 命令"
            except Exception as e:
                last_error = f"CLI调用异常: {e}"
                _logger.warning(f"CLI调用异常 (尝试 {attempt}/{self.retry_count}): {output_path}, 异常: {e}")

            if attempt < self.retry_count:
                wait_time = 5 * attempt
                _logger.info(f"等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)

        return False, f"重试{self.retry_count}次后仍失败: {last_error}"

    def _call_api_direct(self, prompt: str, system_prompt: str = "") -> tuple[bool, str]:
        """直接调用 AI API"""
        if not self.api_key:
            return False, "未配置 API Key"

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

        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": system_prompt,
            "messages": [{"role": "user", "content": prompt}]
        }

        try:
            response = requests.post(api_url, headers=headers, json=payload, timeout=self.api_timeout)
            if response.status_code == 200:
                data = response.json()
                content = data.get("content", [])
                text = ""
                for item in content:
                    if item.get("type") == "text":
                        text += item.get("text", "")
                if text:
                    return True, text
                return False, "API返回内容为空"
            return False, f"API错误: {response.status_code}"
        except Exception as e:
            return False, f"API调用异常: {e}"

    def generate_doc(
        self,
        project_path: str,
        doc_type: str,
        output_path: str,
        progress_callback: Callable[[str, str], None] = None,
        shutdown_event = None
    ) -> tuple[bool, str]:
        """生成单个文档

        Args:
            project_path: 项目路径
            doc_type: 文档类型 (design_md, usage_md, value_md, design_html, etc.)
            output_path: 输出路径
            progress_callback: 进度回调 (doc_key, status)
            shutdown_event: 关闭事件，用于响应 Ctrl+C
        """
        project_name = Path(project_path).name
        code_summary = self._get_project_code_summary(project_path)
        date_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        doc_key = doc_type

        # 检查是否已关闭
        if shutdown_event and shutdown_event.is_set():
            return False, "任务已取消"

        if os.path.exists(output_path):
            if progress_callback:
                progress_callback(doc_key, "已存在")
            return True, "文件已存在，跳过"

        # 根据文档类型生成
        if doc_type == "design_md":
            title = f"{project_name} 设计说明书"
            system_prompt = "你是一个专业的技术文档分析师。"
            prompt = f"""请分析以下 GitHub 项目 {project_name}，生成详细的设计说明书（Markdown格式）。

项目代码摘要:
{code_summary}

要求包含章节：
1. 项目概述（定位、核心功能、目标用户）
2. 系统架构设计（整体架构、模块划分、技术栈）
3. 设计模式分析
4. 关键流程图（用文字描述）
5. 核心组件详解
6. 数据流分析
7. 技术亮点与创新点

请用 Markdown 格式输出，内容详细。"""

        elif doc_type == "usage_md":
            title = f"{project_name} 使用说明书"
            system_prompt = "你是一个专业的技术文档撰写者。"
            prompt = f"""请分析以下 GitHub 项目 {project_name}，生成详细的使用说明书（Markdown格式）。

项目代码摘要:
{code_summary}

要求包含章节：
1. 快速开始（安装、配置、运行）
2. 功能说明
3. 配置详解
4. 使用示例
5. 常见问题解答
6. 最佳实践建议
7. 注意事项与限制

请用 Markdown 格式输出，内容详细。"""

        elif doc_type == "value_md":
            title = f"{project_name} 价值分析报告"
            system_prompt = "你是一个专业的项目价值分析师。"
            prompt = f"""请分析以下 GitHub 项目 {project_name}，生成价值分析报告（Markdown格式）。

项目代码摘要:
{code_summary}

要求包含章节：
1. 项目价值概述
2. 核心竞争力分析
3. 与竞品对比
4. 市场需求分析
5. 技术创新点
6. 用户价值分析
7. 发展前景预测

请用 Markdown 格式输出，内容详细。"""

        elif doc_type.endswith("_html"):
            # HTML 转换
            md_type = doc_type.replace("_html", "_md")
            md_path = output_path.replace(".html", ".md")
            if not os.path.exists(md_path):
                return False, f"MD文件不存在: {md_path}"

            with open(md_path, 'r', encoding='utf-8') as f:
                md_content = f.read()

            title = f"{project_name} {doc_type.split('_')[0].title()}"
            # 使用绝对路径
            abs_output_path = os.path.abspath(output_path)
            prompt = f"""请将以下 Markdown 转换为精美的 HTML 页面并保存到指定路径。

输出文件路径：{abs_output_path}

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
9. 页面底部显示生成时间

要求：直接将完整的 HTML 内容写入文件，不要输出到终端"""

            system_prompt = "你是一个前端开发者。"

        elif doc_type.endswith("_pptx"):
            # PPTX 转换
            html_type = doc_type.replace("_pptx", "_html")
            html_path = output_path.replace(".pptx", ".html")
            if not os.path.exists(html_path):
                return False, f"HTML文件不存在: {html_path}"

            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            title = f"{project_name} {doc_type.split('_')[0].title()}"
            prompt = f"""请使用 pptx skill 从 HTML 创建演示文稿并保存到 {output_path}。

标题：{title}
HTML 内容：
{html_content}

要求：
1. 标题页居中
2. 章节结构幻灯片
3. 风格与 HTML 一致"""

            system_prompt = "你是一个演示文稿设计师。"
        else:
            return False, f"未知文档类型: {doc_type}"

        # 调用 AI 生成
        if progress_callback:
            progress_callback(doc_key, "生成中")

        if self.analysis_method == "cli":
            # CLI 模式：直接使用 prompt（已包含输出路径要求）
            # 对于 HTML 类型，prompt 已包含完整的输出要求
            # 对于 MD 类型，需要添加格式头部要求
            if not doc_type.endswith("_html"):
                # MD/PPTX 类型：添加 Markdown 格式头部要求
                abs_output_path = os.path.abspath(output_path)
                prompt = f"""{prompt}

输出文件路径：{abs_output_path}

要求：
1. 文件第一行为标题：# {title}
2. 第二行为生成时间：生成时间: {date_str}
3. 第三行为分隔线：---
4. 从第四行开始是正文内容
5. 直接将内容写入文件，不要输出到终端"""

            success, result = self._call_cli_for_file(
                prompt, output_path, system_prompt, progress_callback, doc_key, shutdown_event
            )
        else:
            # API 模式
            success, result = self._call_api_direct(prompt, system_prompt)
            if success:
                try:
                    with open(output_path, 'w', encoding='utf-8') as f:
                        if doc_type.endswith("_html"):
                            # HTML 类型：直接写入 AI 返回的内容
                            f.write(result)
                        else:
                            # MD/PPTX 类型：添加 Markdown 格式头部
                            f.write(f"# {title}\n\n")
                            f.write(f"生成时间: {date_str}\n\n")
                            f.write("---\n\n")
                            f.write(result)
                    result = output_path
                except Exception as e:
                    return False, f"写入文件失败: {e}"

        if success:
            if progress_callback:
                progress_callback(doc_key, "已生成")
            _logger.info(f"文档生成成功: {output_path}")
        else:
            if progress_callback:
                progress_callback(doc_key, "失败")
            _logger.error(f"文档生成失败: {result}")

        return success, result

    def generate_all_docs(
        self,
        project_path: str,
        project_name: str,
        progress_callback: Callable[[str, str], None] = None,
        shutdown_event = None,
        generate_html: bool = True,
        generate_pptx: bool = True
    ) -> Dict[str, Any]:
        """生成所有文档（三阶段并行版本）

        Args:
            project_path: 项目路径
            project_name: 项目名称
            progress_callback: 进度回调函数
            shutdown_event: 关闭事件，用于响应 Ctrl+C
            generate_html: 是否生成 HTML 文档（步骤2）
            generate_pptx: 是否生成 PPTX 文档（步骤3）

        执行流程：
            阶段1: 3个线程并行生成 MD 文档
            阶段2: 3个线程并行生成 HTML 文档（依赖阶段1，可配置关闭）
            阶段3: 3个线程并行生成 PPTX 文档（依赖阶段2，可配置关闭）
        """
        docs_dir = Path(self.download_path) / "01-docs"
        docs_dir.mkdir(parents=True, exist_ok=True)

        date_str = datetime.now().strftime('%Y%m%d')

        # 定义所有文档
        docs = [
            ("design_md", f"{project_name}-设计说明书-{date_str}.md"),
            ("usage_md", f"{project_name}-使用说明书-{date_str}.md"),
            ("value_md", f"{project_name}-价值点分析-{date_str}.md"),
            ("design_html", f"{project_name}-设计说明书-{date_str}.html"),
            ("usage_html", f"{project_name}-使用说明书-{date_str}.html"),
            ("value_html", f"{project_name}-价值点分析-{date_str}.html"),
            ("design_pptx", f"{project_name}-设计说明书-{date_str}.pptx"),
            ("usage_pptx", f"{project_name}-使用说明书-{date_str}.pptx"),
            ("value_pptx", f"{project_name}-价值点分析-{date_str}.pptx"),
        ]

        results = {
            "success": True,
            "generated": [],
            "skipped": [],
            "errors": []
        }

        # 检查关闭事件
        def check_shutdown():
            if shutdown_event and shutdown_event.is_set():
                _logger.info("检测到关闭信号，终止文档生成")
                return True
            return False

        # 单个文档生成函数（用于线程执行）
        def generate_single_doc(doc_type: str, filename: str) -> tuple:
            """生成单个文档，返回 (success, result, filename)"""
            output_path = str(docs_dir / filename)
            success, result = self.generate_doc(
                project_path, doc_type, output_path, progress_callback, shutdown_event
            )
            return success, result, filename

        # 阶段执行函数
        def execute_phase(doc_list: list, phase_name: str) -> list:
            """并行执行一个阶段的文档生成

            Args:
                doc_list: 该阶段的文档列表 [(doc_type, filename), ...]
                phase_name: 阶段名称

            Returns:
                每个文档的结果列表 [(success, result, filename), ...]
            """
            if check_shutdown():
                _logger.info(f"{phase_name}阶段被取消")
                return []

            _logger.info(f"开始{phase_name}阶段，并行生成 {len(doc_list)} 个文档")

            phase_results = []
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = []
                for doc_type, filename in doc_list:
                    future = executor.submit(generate_single_doc, doc_type, filename)
                    futures.append(future)

                # 等待所有线程完成
                for future in futures:
                    try:
                        success, result, filename = future.result()
                        phase_results.append((success, result, filename))
                    except Exception as e:
                        _logger.error(f"线程执行异常: {e}")
                        phase_results.append((False, str(e), "unknown"))

            _logger.info(f"{phase_name}阶段完成")
            return phase_results

        # 处理阶段结果
        def process_phase_results(phase_results: list):
            """处理阶段结果，更新总结果"""
            for success, result, filename in phase_results:
                if success:
                    if "跳过" in result:
                        results["skipped"].append(filename)
                    else:
                        results["generated"].append(filename)
                else:
                    results["errors"].append(f"{filename}: {result}")

        # 阶段1: MD（3个并行）
        phase1_results = execute_phase(docs[:3], "MD")
        if check_shutdown():
            results["errors"].append("任务已取消")
            return results
        process_phase_results(phase1_results)

        # 检查阶段1是否有严重错误（所有MD都失败则停止）
        md_success_count = sum(1 for s, r, f in phase1_results if s)
        if md_success_count == 0 and len(phase1_results) > 0:
            _logger.warning("阶段1全部失败，停止后续生成")
            results["success"] = False
            return results

        # 阶段2: HTML（3个并行，依赖阶段1的MD文件）
        if generate_html:
            phase2_results = execute_phase(docs[3:6], "HTML")
            if check_shutdown():
                results["errors"].append("任务已取消")
                return results
            process_phase_results(phase2_results)
        else:
            _logger.info("HTML生成已关闭，跳过阶段2")
            for doc_type, filename in docs[3:6]:
                results["skipped"].append(filename)

        # 阶段3: PPTX（3个并行，依赖阶段2的HTML文件）
        if generate_pptx:
            phase3_results = execute_phase(docs[6:], "PPTX")
            if check_shutdown():
                results["errors"].append("任务已取消")
                return results
            process_phase_results(phase3_results)
        else:
            _logger.info("PPTX生成已关闭，跳过阶段3")
            for doc_type, filename in docs[6:]:
                results["skipped"].append(filename)

        # 计算总体成功状态
        if results["errors"]:
            results["success"] = False

        return results
