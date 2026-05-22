"""热点项目API路由"""
from fastapi import APIRouter, Depends, Request
from typing import List

from app.schemas import TrendingQuery, StarredQuery, Project
from app.core.github_api import GitHubAPI
from app.core.trending_scraper import TrendingScraper
from app.config import settings
from app.api.auth import get_current_user
from app.core.logger import get_logger

_logger = get_logger("trending_api")

router = APIRouter()


def get_db(request: Request):
    """获取数据库实例"""
    return request.app.state.db


@router.get("/official", response_model=List[Project])
async def get_official_trending(
    since: str = "daily",
    language: str = "",
    limit: int = None,
    user = Depends(get_current_user)
):
    """获取GitHub官方Trending"""
    if limit is None:
        limit = settings.TRENDING_OFFICIAL_LIMIT
    _logger.info(f"获取官方热点: since={since}, language={language}, limit={limit}")
    scraper = TrendingScraper(settings.GITHUB_TOKEN, timeout=settings.GITHUB_API_TIMEOUT)
    results = scraper.get_trending(since=since, language=language, limit=limit)
    _logger.info(f"官方热点返回: {len(results)} 个项目")
    return results


@router.get("/stars", response_model=List[Project])
async def get_starred_projects(
    category: str = "ALL",
    pushed_period: str = "不限制",
    created_period: str = "不限制",
    limit: int = None,
    user = Depends(get_current_user)
):
    """获取高星项目（按主题筛选）"""
    if limit is None:
        limit = settings.TRENDING_STARRED_LIMIT
    _logger.info(f"获取高星项目: category={category}, pushed={pushed_period}, created={created_period}, limit={limit}")
    categories = settings.TRENDING_CATEGORIES
    category_config = categories.get(category, {"topics": [], "min_stars": 50})

    api = GitHubAPI(settings.GITHUB_TOKEN, timeout=settings.GITHUB_API_TIMEOUT)
    results = api.get_trending(
        category_config,
        pushed_period=pushed_period,
        created_period=created_period,
        max_results=limit
    )
    _logger.info(f"高星项目返回: {len(results)} 个项目")
    return results


@router.get("/categories")
async def get_categories(user = Depends(get_current_user)):
    """获取所有主题分类"""
    categories = settings.TRENDING_CATEGORIES
    _logger.info(f"获取分类列表: {list(categories.keys())}")
    return {"categories": list(categories.keys())}