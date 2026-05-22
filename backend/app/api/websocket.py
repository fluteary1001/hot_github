"""WebSocket路由 - 实时推送下载和文档生成进度"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Any
import asyncio
import json

from app.core.logger import get_logger

_logger = get_logger("websocket")

router = APIRouter()

# 存储活跃的WebSocket连接
active_connections: Dict[str, WebSocket] = {}


async def broadcast_to_task(task_id: str, message: Dict[str, Any]):
    """向特定任务的WebSocket连接广播消息"""
    if task_id in active_connections:
        try:
            await active_connections[task_id].send_json(message)
            _logger.info(f"WebSocket广播成功: task_id={task_id}, type={message.get('type')}")
        except Exception as e:
            _logger.warning(f"WebSocket广播失败: task_id={task_id}, error={e}")
            active_connections.pop(task_id, None)
    else:
        _logger.debug(f"WebSocket广播跳过（无连接）: task_id={task_id}")


class ProgressManager:
    """进度管理器 - 用于从后台任务更新WebSocket"""

    _download_tasks: Dict[str, Dict[str, Any]] = {}
    _doc_tasks: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def update_download_progress(cls, task_id: str, progress: int, status: str, message: str = ""):
        """更新下载进度"""
        _logger.info(f"更新下载进度: task_id={task_id}, progress={progress}, status={status}, message={message}")
        cls._download_tasks[task_id] = {
            "progress": progress,
            "status": status,
            "message": message
        }
        # 异步广播（需要在事件循环中调用）
        try:
            asyncio.create_task(broadcast_to_task(task_id, {
                "type": "download_progress",
                "task_id": task_id,
                "progress": progress,
                "status": status,
                "message": message
            }))
        except RuntimeError as e:
            _logger.warning(f"创建广播任务失败（可能无事件循环）: task_id={task_id}, error={e}")

    @classmethod
    def update_doc_progress(cls, task_id: str, doc_key: str, status: str):
        """更新文档生成进度"""
        _logger.info(f"更新文档进度: task_id={task_id}, doc_key={doc_key}, status={status}")
        if task_id not in cls._doc_tasks:
            cls._doc_tasks[task_id] = {"docs": {}, "progress": 0}

        cls._doc_tasks[task_id]["docs"][doc_key] = status

        # 计算总体进度
        completed = sum(1 for s in cls._doc_tasks[task_id]["docs"].values()
                       if s in ["已生成", "已存在"])
        total = 9
        cls._doc_tasks[task_id]["progress"] = int(completed / total * 100)

        try:
            asyncio.create_task(broadcast_to_task(task_id, {
                "type": "doc_progress",
                "task_id": task_id,
                "doc_key": doc_key,
                "status": status,
                "progress": cls._doc_tasks[task_id]["progress"],
                "docs": cls._doc_tasks[task_id]["docs"]
            }))
        except RuntimeError as e:
            _logger.warning(f"创建广播任务失败（可能无事件循环）: task_id={task_id}, error={e}")

    @classmethod
    def get_download_status(cls, task_id: str) -> Dict[str, Any]:
        """获取下载状态"""
        return cls._download_tasks.get(task_id, {"status": "unknown"})

    @classmethod
    def get_doc_status(cls, task_id: str) -> Dict[str, Any]:
        """获取文档生成状态"""
        return cls._doc_tasks.get(task_id, {"status": "unknown", "docs": {}})


@router.websocket("/ws/download/{task_id}")
async def download_progress_ws(websocket: WebSocket, task_id: str):
    """实时推送下载进度"""
    await websocket.accept()
    active_connections[task_id] = websocket

    try:
        # 发送初始状态
        status = ProgressManager.get_download_status(task_id)
        await websocket.send_json({
            "type": "download_status",
            "task_id": task_id,
            **status
        })

        # 保持连接，等待消息或断开
        while True:
            try:
                # 等待客户端消息（心跳或关闭）
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                if data == "ping":
                    await websocket.send_json({"type": "pong"})
            except asyncio.TimeoutError:
                # 发送心跳
                await websocket.send_json({"type": "heartbeat", "task_id": task_id})

    except WebSocketDisconnect:
        pass
    finally:
        active_connections.pop(task_id, None)


@router.websocket("/ws/docs/{task_id}")
async def docs_progress_ws(websocket: WebSocket, task_id: str):
    """实时推送文档生成进度"""
    await websocket.accept()
    active_connections[task_id] = websocket

    try:
        # 发送初始状态
        status = ProgressManager.get_doc_status(task_id)
        await websocket.send_json({
            "type": "doc_status",
            "task_id": task_id,
            **status
        })

        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                if data == "ping":
                    await websocket.send_json({"type": "pong"})
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "heartbeat", "task_id": task_id})

    except WebSocketDisconnect:
        pass
    finally:
        active_connections.pop(task_id, None)


# 导出进度管理器供其他模块使用
__all__ = ['router', 'ProgressManager', 'broadcast_to_task']
