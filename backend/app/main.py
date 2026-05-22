"""FastAPI应用入口"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pathlib import Path
import signal
import sys
import threading

from app.config import settings, _default_config_path
from app.api import projects, search, trending, docs_gen, auth, websocket, config, history_trending
from app.core.database import ProjectDB
from app.core.scheduler import TrendingScheduler
from app.core.logger import get_log_manager

# 初始化日志
log_manager = get_log_manager(log_dir=settings.LOG_DIR)
logger = log_manager.get_logger("main")

# 全局关闭标志（使用 threading.Event 支持跨线程）
shutdown_event = threading.Event()


def signal_handler(signum, frame):
    """信号处理器 - 直接退出进程"""
    logger.info(f"收到信号 {signum}，立即退出")
    # 设置关闭标志，让后台任务停止
    shutdown_event.set()
    # 直接退出进程
    sys.exit(0)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info(f"{settings.APP_NAME} API 启动中...")
    logger.info(f"配置已加载: {_default_config_path()}")

    # 注册信号处理器（Windows 兼容）
    try:
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        logger.info("信号处理器已注册: SIGINT, SIGTERM")
    except (ValueError, OSError) as e:
        logger.warning(f"信号处理器注册失败: {e}")

    # 初始化数据库（db_path 相对于 backend/ 目录）
    db_path = Path(__file__).parent.parent / settings.DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)
    app.state.db = ProjectDB(str(db_path))
    app.state.shutdown_event = shutdown_event
    logger.info(f"数据库已初始化: {db_path}")

    # 初始化定时任务调度器
    if settings.HISTORY_TRENDING_ENABLED:
        scheduler = TrendingScheduler(app.state.db, settings, shutdown_event)
        scheduler.start()
        app.state.scheduler = scheduler
        logger.info("历史热点调度器已启动")
    else:
        app.state.scheduler = None
        logger.info("历史热点功能已禁用")

    logger.info(f"{settings.APP_NAME} API 启动完成，等待请求...")

    yield

    # 关闭时（正常关闭流程，Ctrl+C 会直接 sys.exit 跳过这里）
    logger.info("进入关闭阶段...")

    if app.state.scheduler:
        logger.info("正在关闭调度器...")
        try:
            app.state.scheduler.shutdown()
            logger.info("调度器关闭成功")
        except Exception as e:
            logger.error(f"调度器关闭异常: {e}")

    shutdown_event.set()
    logger.info(f"{settings.APP_NAME} API 关闭完成")


# 创建FastAPI应用
app = FastAPI(
    title=f"{settings.APP_NAME} API",
    description="GitHub项目管理Web API - 搜索、下载、管理GitHub项目",
    version="2.0.0",
    lifespan=lifespan
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(projects.router, prefix="/api/projects", tags=["项目管理"])
app.include_router(search.router, prefix="/api/search", tags=["搜索下载"])
app.include_router(trending.router, prefix="/api/trending", tags=["热点项目"])
app.include_router(docs_gen.router, prefix="/api/docs", tags=["文档生成"])
app.include_router(config.router, prefix="/api/config", tags=["系统配置"])
app.include_router(history_trending.router, prefix="/api/history", tags=["历史热点"])
app.include_router(websocket.router, tags=["WebSocket"])


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": settings.APP_NAME,
        "version": "2.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy"}
