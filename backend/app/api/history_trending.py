"""历史热点API路由"""
from fastapi import APIRouter, Depends, Request, HTTPException
from typing import Optional

from app.core.database import ProjectDB
from app.core.history_manager import HistoryManager
from app.core.scheduler import TrendingScheduler
from app.api.auth import get_current_user
from app.core.logger import get_logger

_logger = get_logger("history_trending_api")

router = APIRouter()


def get_db(request: Request) -> ProjectDB:
    """获取数据库实例"""
    return request.app.state.db


def get_scheduler(request: Request) -> TrendingScheduler:
    """获取调度器实例"""
    return request.app.state.scheduler


@router.get("/tree")
async def get_tree_data(
    request: Request,
    user=Depends(get_current_user)
):
    """获取历史热点树状结构"""
    db = get_db(request)
    manager = HistoryManager(db)
    tree = manager.get_tree_data()
    return {"data": tree}


@router.get("/years")
async def get_years(
    request: Request,
    user=Depends(get_current_user)
):
    """获取有数据的年份列表"""
    db = get_db(request)
    years = db.get_trending_years()
    return {"years": years}


@router.get("/months")
async def get_months(
    request: Request,
    year: int,
    db: ProjectDB = Depends(get_db),
    user=Depends(get_current_user)
):
    """获取指定年份的月份数据"""
    months = db.get_trending_months(year)
    return {"year": year, "months": months}


@router.get("/weeks")
async def get_weeks(
    request: Request,
    year: int,
    month: int,
    db: ProjectDB = Depends(get_db),
    user=Depends(get_current_user)
):
    """获取指定月份的周数据"""
    weeks = db.get_trending_weeks(year, month)
    return {"year": year, "month": month, "weeks": weeks}


@router.get("/days")
async def get_days(
    request: Request,
    year: int,
    month: int,
    week: Optional[int] = None,
    db: ProjectDB = Depends(get_db),
    user=Depends(get_current_user)
):
    """获取指定周或月份的日数据"""
    days = db.get_trending_days(year, month, week)
    return {"year": year, "month": month, "week": week, "days": days}


@router.get("/detail")
async def get_detail(
    request: Request,
    period_type: str,
    period_value: str,
    db: ProjectDB = Depends(get_db),
    user=Depends(get_current_user)
):
    """获取指定周期的热点详情"""
    manager = HistoryManager(db)
    detail = manager.get_period_detail(period_type, period_value)
    return detail


@router.post("/collect")
async def manual_collect(
    request: Request,
    period_type: str = "daily",
    user=Depends(get_current_user)
):
    """手动触发热点采集"""
    scheduler = get_scheduler(request)
    result = scheduler.manual_collect(period_type)

    if result["success"]:
        return {
            "message": "采集成功",
            "period_type": result["period_type"],
            "period_value": result["period_value"],
            "saved_count": result["saved_count"]
        }
    else:
        raise HTTPException(status_code=500, detail=result["error"])


@router.get("/scheduler/status")
async def get_scheduler_status(
    request: Request,
    task_name: Optional[str] = None,
    db: ProjectDB = Depends(get_db),
    user=Depends(get_current_user)
):
    """获取定时任务状态"""
    if task_name:
        task = db.get_scheduler_task(task_name)
        return {"task": task}
    else:
        # 返回所有任务状态
        tasks = ['daily_trending', 'weekly_trending', 'monthly_trending', 'auto_analysis', 'retry_analysis']
        result = {}
        for t in tasks:
            result[t] = db.get_scheduler_task(t)
        return {"tasks": result}
