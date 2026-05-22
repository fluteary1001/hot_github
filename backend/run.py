"""运行脚本"""
import uvicorn
from app.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        # 优雅关闭超时时间
        timeout_graceful_shutdown=5
    )
