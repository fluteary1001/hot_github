"""文档生成API路由"""
from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from fastapi.responses import FileResponse, Response
from typing import List, Dict, Any
from pathlib import Path
import uuid
import asyncio

from app.schemas import DocGenerateRequest, Message
from app.core.database import ProjectDB
from app.core.doc_generator import WebDocGenerator
from app.config import settings
from app.api.auth import get_current_user
from app.core.logger import get_logger

_logger = get_logger("docs_gen_api")

router = APIRouter()

# 存储文档生成任务状态
doc_tasks: Dict[str, Dict[str, Any]] = {}


def get_db(request: Request) -> ProjectDB:
    """获取数据库实例"""
    return request.app.state.db


def get_shutdown_event(request: Request):
    """获取关闭事件"""
    return request.app.state.shutdown_event


def get_generator() -> WebDocGenerator:
    """获取文档生成器实例"""
    return WebDocGenerator(
        download_path=settings.DOWNLOAD_PATH,
        api_key=settings.CLAUDE_API_KEY,
        model=settings.CLAUDE_MODEL,
        base_url=settings.CLAUDE_BASE_URL,
        max_tokens=settings.CLAUDE_MAX_TOKENS,
        cli_timeout=settings.CLAUDE_CLI_TIMEOUT,
        api_timeout=settings.CLAUDE_API_TIMEOUT,
        retry_count=settings.CLAUDE_RETRY_COUNT,
        analysis_method=settings.ANALYSIS_METHOD
    )


@router.post("/generate/{project_id}")
async def generate_docs(
    project_id: int,
    request: Request,
    background_tasks: BackgroundTasks,
    db: ProjectDB = Depends(get_db),
    user = Depends(get_current_user)
):
    """启动文档生成任务"""
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    local_path = project.get('local_path')
    if not local_path:
        raise HTTPException(status_code=400, detail="项目没有本地路径")

    project_name = project.get('name', Path(local_path).name)

    # 生成任务ID
    task_id = str(uuid.uuid4())

    # 获取关闭事件
    shutdown_event = request.app.state.shutdown_event

    # 初始化任务状态
    doc_tasks[task_id] = {
        "status": "pending",
        "progress": 0,
        "project_id": project_id,
        "project_name": project_name,
        "docs": {
            "design_md": "等待中",
            "usage_md": "等待中",
            "value_md": "等待中",
            "design_html": "等待中",
            "usage_html": "等待中",
            "value_html": "等待中",
            "design_pptx": "等待中",
            "usage_pptx": "等待中",
            "value_pptx": "等待中"
        },
        "message": "准备生成文档..."
    }

    def progress_callback(doc_key: str, status: str):
        """进度回调"""
        if task_id in doc_tasks:
            doc_tasks[task_id]["docs"][doc_key] = status
            # 计算总体进度
            completed = sum(1 for s in doc_tasks[task_id]["docs"].values()
                          if s in ["已生成", "已存在"])
            total = len(doc_tasks[task_id]["docs"])
            doc_tasks[task_id]["progress"] = int(completed / total * 100)

    def generate_task():
        """后台文档生成任务"""
        try:
            # 检查是否已关闭
            if shutdown_event.is_set():
                doc_tasks[task_id]["status"] = "cancelled"
                doc_tasks[task_id]["message"] = "任务已取消（服务关闭）"
                return

            doc_tasks[task_id]["status"] = "generating"
            doc_tasks[task_id]["message"] = "正在生成文档..."

            generator = get_generator()
            results = generator.generate_all_docs(
                local_path,
                project_name,
                progress_callback,
                shutdown_event,
                generate_html=settings.DOCS_GENERATE_HTML,
                generate_pptx=settings.DOCS_GENERATE_PPTX
            )

            # 检查是否被取消
            if shutdown_event.is_set():
                doc_tasks[task_id]["status"] = "cancelled"
                doc_tasks[task_id]["message"] = "任务已取消（服务关闭）"
                return

            doc_tasks[task_id]["status"] = "completed"
            doc_tasks[task_id]["progress"] = 100
            doc_tasks[task_id]["message"] = f"生成完成: {len(results['generated'])}个文件"
            doc_tasks[task_id]["results"] = results

        except Exception as e:
            doc_tasks[task_id]["status"] = "failed"
            doc_tasks[task_id]["message"] = f"生成失败: {str(e)}"

    background_tasks.add_task(generate_task)

    return {
        "task_id": task_id,
        "project_id": project_id,
        "project_name": project_name
    }


@router.get("/status/{task_id}")
async def get_doc_status(task_id: str, user = Depends(get_current_user)):
    """获取文档生成任务状态"""
    if task_id not in doc_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")

    return doc_tasks[task_id]


@router.get("/{project_id}")
async def get_project_docs(
    project_id: int,
    db: ProjectDB = Depends(get_db),
    user = Depends(get_current_user)
):
    """获取项目的文档列表"""
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    local_path = project.get('local_path')
    if not local_path:
        return {"docs": []}

    # 查找文档目录
    docs_dir = Path(settings.DOWNLOAD_PATH) / "01-docs"
    if not docs_dir.exists():
        return {"docs": []}

    project_name = project.get('name', Path(local_path).name)

    docs = []
    for doc_file in docs_dir.glob(f"{project_name}-*"):
        if doc_file.is_file():
            docs.append({
                "name": doc_file.name,
                "path": str(doc_file),
                "size": doc_file.stat().st_size,
                "modified": doc_file.stat().st_mtime
            })

    return {"docs": sorted(docs, key=lambda x: x["name"])}


@router.get("/file/{project_id}/{doc_name}")
async def download_doc(
    project_id: int,
    doc_name: str,
    db: ProjectDB = Depends(get_db)
):
    """获取文档文件（HTML直接展示，其他类型下载）

    处理流程:
    1. 验证项目存在
    2. 确定文档目录
    3. 尝试精确匹配文件名
    4. 精确匹配失败时，尝试模糊匹配
    5. 返回文件内容或触发下载

    日志记录: 使用 [DOC_FILE] 前缀方便追踪
    """
    _logger.info(f"[DOC_FILE] ========== 开始处理文档文件请求 ==========")
    _logger.info(f"[DOC_FILE] 请求参数: project_id={project_id}, doc_name={doc_name}")

    # Step 1: 验证项目存在
    _logger.info(f"[DOC_FILE] Step 1: 验证项目存在")
    project = db.get_project(project_id)
    if not project:
        _logger.error(f"[DOC_FILE] 项目不存在: project_id={project_id}")
        raise HTTPException(status_code=404, detail="项目不存在")
    _logger.info(f"[DOC_FILE] 项目验证成功: id={project_id}, name={project.get('name')}, full_name={project.get('full_name')}")

    # Step 2: 确定文档目录
    _logger.info(f"[DOC_FILE] Step 2: 确定文档目录")
    docs_dir = Path(settings.DOWNLOAD_PATH) / "01-docs"
    _logger.info(f"[DOC_FILE] 文档目录: {docs_dir.absolute()} (exists={docs_dir.exists()})")

    if not docs_dir.exists():
        _logger.error(f"[DOC_FILE] 文档目录不存在: {docs_dir}")
        raise HTTPException(status_code=404, detail="文档目录不存在")

    # Step 3: 尝试精确匹配
    _logger.info(f"[DOC_FILE] Step 3: 尝试精确匹配文件")
    doc_path = docs_dir / doc_name
    _logger.info(f"[DOC_FILE] 精确匹配路径: {doc_path} (exists={doc_path.exists()})")

    # Step 4: 如果精确匹配失败，尝试模糊匹配
    if not doc_path.exists():
        _logger.info(f"[DOC_FILE] Step 4: 精确匹配失败，尝试模糊匹配")

        # 去掉扩展名获取基础名
        base_name = doc_name.rsplit('.', 1)[0] if '.' in doc_name else doc_name
        extension = doc_name.rsplit('.', 1)[1] if '.' in doc_name else ''
        glob_pattern = f"{base_name}*.{extension}" if extension else f"{base_name}*"

        _logger.info(f"[DOC_FILE] 模糊匹配参数: base_name={base_name}, extension={extension}")
        _logger.info(f"[DOC_FILE] glob模式: {glob_pattern}")

        # 查找匹配的文件
        matching_files = list(docs_dir.glob(glob_pattern))
        _logger.info(f"[DOC_FILE] 匹配到的文件数量: {len(matching_files)}")

        if matching_files:
            # 显示所有匹配的文件
            for i, f in enumerate(matching_files):
                mtime = f.stat().st_mtime
                _logger.info(f"[DOC_FILE] 匹配文件[{i}]: {f.name} (mtime={mtime})")

            # 按修改时间排序，取最新的
            matching_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            doc_path = matching_files[0]
            _logger.info(f"[DOC_FILE] 选择最新文件: {doc_path.name}")
        else:
            # 列出目录中所有文件，帮助诊断
            _logger.warning(f"[DOC_FILE] 模糊匹配失败，列出目录中所有文件:")
            all_files = list(docs_dir.glob("*"))
            for f in all_files[:20]:  # 最多显示20个
                _logger.warning(f"[DOC_FILE] 目录文件: {f.name}")
            _logger.error(f"[DOC_FILE] 文档不存在: {doc_name}")
            raise HTTPException(status_code=404, detail="文档不存在")
    else:
        _logger.info(f"[DOC_FILE] 精确匹配成功: {doc_path}")

    # Step 5: 确定文件类型和返回方式
    _logger.info(f"[DOC_FILE] Step 5: 准备返回文件")
    suffix = doc_path.suffix.lower()
    file_size = doc_path.stat().st_size
    _logger.info(f"[DOC_FILE] 文件信息: path={doc_path}, suffix={suffix}, size={file_size} bytes")

    media_types = {
        '.html': 'text/html',
        '.htm': 'text/html',
        '.md': 'text/markdown',
        '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    }
    media_type = media_types.get(suffix, 'application/octet-stream')
    _logger.info(f"[DOC_FILE] media_type: {media_type}")

    # HTML 文件直接展示，不设置 filename
    if suffix in ['.html', '.htm']:
        _logger.info(f"[DOC_FILE] HTML文件，内嵌展示模式")
        try:
            with open(doc_path, 'r', encoding='utf-8') as f:
                content = f.read()
            _logger.info(f"[DOC_FILE] 文件读取成功，内容长度: {len(content)} 字符")

            response = Response(
                content=content,
                media_type='text/html',
                headers={'Content-Disposition': 'inline'}
            )
            _logger.info(f"[DOC_FILE] ========== 返回HTML响应成功 ==========")
            return response
        except Exception as e:
            _logger.error(f"[DOC_FILE] 读取文件失败: {e}")
            raise HTTPException(status_code=500, detail=f"读取文件失败: {str(e)}")

    # 其他文件类型触发下载
    _logger.info(f"[DOC_FILE] 非HTML文件，触发下载")
    _logger.info(f"[DOC_FILE] ========== 返回文件下载响应 ==========")
    return FileResponse(
        path=str(doc_path),
        filename=doc_name,
        media_type=media_type
    )


@router.delete("/task/{task_id}")
async def cancel_doc_task(
    task_id: str,
    user = Depends(get_current_user)
):
    """取消/清理文档生成任务"""
    if task_id not in doc_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 简单删除任务记录（实际取消需要更复杂的实现）
    del doc_tasks[task_id]
    return Message(message="任务已删除")
