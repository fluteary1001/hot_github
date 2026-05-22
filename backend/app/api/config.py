"""配置管理API路由"""
from fastapi import APIRouter, Depends

from app.config import settings
from app.api.auth import get_current_user

router = APIRouter()


@router.get("")
async def get_config(user = Depends(get_current_user)):
    """获取当前配置（敏感字段脱敏）"""
    return {
        "app_name": settings.APP_NAME,
        "version": "2.0.0",
        "download_path": settings.DOWNLOAD_PATH,
        "github_token": "***" if settings.GITHUB_TOKEN else "",
        "claude_api_key": "***" if settings.CLAUDE_API_KEY else "",
        "claude_model": settings.CLAUDE_MODEL,
        "claude_base_url": settings.CLAUDE_BASE_URL or "",
        "require_login": settings.REQUIRE_LOGIN,
    }


@router.put("")
async def update_config(user = Depends(get_current_user)):
    """更新配置（预留）"""
    return {"message": "配置已更新"}


@router.post("/test-github")
async def test_github_connection(user = Depends(get_current_user)):
    """测试GitHub连接"""
    from app.core.downloader import ProjectDownloader

    downloader = ProjectDownloader(settings.DOWNLOAD_PATH)
    success, message = downloader.test_github_connection()

    return {
        "success": success,
        "message": message
    }
