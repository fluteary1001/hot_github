"""项目管理API路由"""
from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List, Optional

from app.schemas import (
    Project, ProjectImport, ProjectUpdate, Message
)
from app.core.database import ProjectDB
from app.core.downloader import ProjectDownloader
from app.config import settings
from app.api.auth import get_current_user

router = APIRouter()


def get_db(request: Request) -> ProjectDB:
    """获取数据库实例"""
    return request.app.state.db


@router.get("/", response_model=List[Project])
async def get_projects(
    keyword: Optional[str] = None,
    db: ProjectDB = Depends(get_db),
    user = Depends(get_current_user)
):
    """获取所有项目或搜索项目"""
    if keyword:
        return db.search_projects(keyword)
    return db.get_all_projects()


@router.get("/{project_id}", response_model=Project)
async def get_project(
    project_id: int,
    db: ProjectDB = Depends(get_db),
    user = Depends(get_current_user)
):
    """获取单个项目详情"""
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project


@router.post("/import", response_model=Project)
async def import_project(
    request: ProjectImport,
    db: ProjectDB = Depends(get_db),
    user = Depends(get_current_user)
):
    """导入已有项目"""
    from pathlib import Path

    path = Path(request.path)
    if not path.exists():
        raise HTTPException(status_code=400, detail="项目目录不存在")

    project_name = request.project_name or path.name

    # 获取项目信息
    downloader = ProjectDownloader(settings.DOWNLOAD_PATH)
    info = downloader.get_project_info_from_local(str(path))
    info['name'] = project_name
    info['local_path'] = str(path)

    # 添加到数据库
    project_id = db.add_project(info)
    return db.get_project(project_id)


@router.put("/{project_id}", response_model=Project)
async def update_project(
    project_id: int,
    update: ProjectUpdate,
    db: ProjectDB = Depends(get_db),
    user = Depends(get_current_user)
):
    """更新项目信息"""
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    update_data = update.model_dump(exclude_unset=True)
    if update_data:
        db.update_project(project_id, update_data)

    return db.get_project(project_id)


@router.delete("/{project_id}", response_model=Message)
async def delete_project(
    project_id: int,
    delete_files: bool = False,
    db: ProjectDB = Depends(get_db),
    user = Depends(get_current_user)
):
    """删除项目"""
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 可选：删除本地文件
    if delete_files and project.get('local_path'):
        downloader = ProjectDownloader(settings.DOWNLOAD_PATH)
        downloader.delete_project(
            project['local_path'],
            project.get('shortcut_path')
        )

    # 从数据库删除
    success = db.delete_project(project_id)
    if not success:
        raise HTTPException(status_code=500, detail="删除失败")

    return Message(message="项目已删除")


@router.post("/{project_id}/update", response_model=Message)
async def update_project_code(
    project_id: int,
    db: ProjectDB = Depends(get_db),
    user = Depends(get_current_user)
):
    """执行 git pull 更新项目"""
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    local_path = project.get('local_path')
    if not local_path:
        raise HTTPException(status_code=400, detail="项目没有本地路径")

    downloader = ProjectDownloader(settings.DOWNLOAD_PATH)
    success, message = downloader.update_project(local_path)

    if not success:
        raise HTTPException(status_code=500, detail=message)

    return Message(message=message)
