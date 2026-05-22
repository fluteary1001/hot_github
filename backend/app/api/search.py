"""搜索下载API路由"""
from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from typing import List
import uuid

from app.schemas import (
    SearchQuery, SearchByUrlQuery, DownloadRequest, Project, Message
)
from app.core.github_api import GitHubAPI
from app.core.database import ProjectDB
from app.core.downloader import ProjectDownloader
from app.config import settings
from app.api.auth import get_current_user
from app.api.websocket import ProgressManager
from app.core.logger import get_logger

_logger = get_logger("search_api")

router = APIRouter()

# 存储下载任务状态
download_tasks = {}


def get_db(request: Request) -> ProjectDB:
    """获取数据库实例"""
    return request.app.state.db


@router.post("/", response_model=List[Project])
async def search_repositories(
    query: SearchQuery,
    user = Depends(get_current_user)
):
    """搜索GitHub项目"""
    _logger.info(f"搜索请求: query={query.query}, limit={query.limit}")
    api = GitHubAPI(settings.GITHUB_TOKEN, timeout=settings.GITHUB_API_TIMEOUT)
    results = api.search_repositories(query.query, query.limit)
    _logger.info(f"搜索完成: 返回 {len(results)} 个结果")
    return results


@router.post("/url", response_model=Project)
async def search_by_url(
    query: SearchByUrlQuery,
    user = Depends(get_current_user)
):
    """通过URL获取项目信息"""
    _logger.info(f"URL搜索请求: url={query.url}")
    api = GitHubAPI(settings.GITHUB_TOKEN, timeout=settings.GITHUB_API_TIMEOUT)
    result = api.get_repository_by_url(query.url)
    if not result:
        _logger.warning(f"URL搜索未找到项目: {query.url}")
        raise HTTPException(status_code=404, detail="未找到项目")
    _logger.info(f"URL搜索成功: {result.get('full_name', 'unknown')}")
    return result


@router.post("/download")
async def start_download(
    request: DownloadRequest,
    background_tasks: BackgroundTasks,
    db: ProjectDB = Depends(get_db),
    user = Depends(get_current_user)
):
    """启动下载任务"""
    task_id = str(uuid.uuid4())

    _logger.info(f"收到下载请求: clone_url={request.clone_url}, project_name={request.project_name}, task_id={task_id}")

    # 初始化任务状态
    download_tasks[task_id] = {
        "status": "pending",
        "progress": 0,
        "message": "准备下载...",
        "project_name": request.project_name
    }

    # 在后台执行下载
    def download_task():
        _logger.info(f"[任务 {task_id}] 开始执行后台下载任务")
        download_tasks[task_id]["status"] = "downloading"
        download_tasks[task_id]["message"] = "正在下载..."
        ProgressManager.update_download_progress(task_id, 10, "downloading", "开始下载...")

        downloader = ProjectDownloader(settings.DOWNLOAD_PATH)

        # 定义进度回调
        def progress_callback(msg: str):
            download_tasks[task_id]["message"] = msg
            _logger.info(f"[任务 {task_id}] 进度回调: {msg}")
            # 根据消息内容估算进度
            if "克隆成功" in msg:
                ProgressManager.update_download_progress(task_id, 90, "downloading", msg)
            elif "准备克隆" in msg:
                ProgressManager.update_download_progress(task_id, 20, "downloading", msg)
            elif "执行 git clone" in msg:
                ProgressManager.update_download_progress(task_id, 50, "downloading", msg)

        downloader.status_callback = progress_callback

        _logger.info(f"[任务 {task_id}] 调用 downloader.clone_project: {request.clone_url}")
        success, result = downloader.clone_project(
            request.clone_url,
            request.project_name
        )

        if success:
            _logger.info(f"[任务 {task_id}] 克隆成功，本地路径: {result}")
            # 添加到数据库
            api = GitHubAPI(settings.GITHUB_TOKEN, timeout=settings.GITHUB_API_TIMEOUT)
            repo_info = api.get_repository_by_url(request.clone_url)

            if repo_info:
                repo_info['local_path'] = result
                db.add_project(repo_info)
                _logger.info(f"[任务 {task_id}] 已写入数据库: {repo_info.get('full_name', 'unknown')}")
            else:
                _logger.warning(f"[任务 {task_id}] 克隆成功但无法获取仓库信息: {request.clone_url}")

            download_tasks[task_id]["status"] = "completed"
            download_tasks[task_id]["progress"] = 100
            download_tasks[task_id]["message"] = "下载完成"
            download_tasks[task_id]["local_path"] = result
            ProgressManager.update_download_progress(task_id, 100, "completed", "下载完成")
        else:
            _logger.error(f"[任务 {task_id}] 克隆失败: {result}")
            download_tasks[task_id]["status"] = "failed"
            download_tasks[task_id]["message"] = result
            ProgressManager.update_download_progress(task_id, 0, "failed", result)

    background_tasks.add_task(download_task)
    _logger.info(f"下载任务已提交: task_id={task_id}")

    return {"task_id": task_id, "project_name": request.project_name}


@router.get("/download/{task_id}")
async def get_download_status(task_id: str, user = Depends(get_current_user)):
    """获取下载任务状态"""
    if task_id not in download_tasks:
        _logger.warning(f"查询不存在的任务: {task_id}")
        raise HTTPException(status_code=404, detail="任务不存在")

    return download_tasks[task_id]


@router.get("/test-connection")
async def test_connection(user = Depends(get_current_user)):
    """测试GitHub连接"""
    _logger.info("测试GitHub连接")
    downloader = ProjectDownloader(settings.DOWNLOAD_PATH)
    success, message = downloader.test_github_connection()
    _logger.info(f"GitHub连接测试结果: success={success}, message={message}")
    return {"success": success, "message": message}
