"""日志系统模块"""
import logging
import os
from pathlib import Path
from datetime import datetime, timedelta
from logging.handlers import TimedRotatingFileHandler


class LogManager:
    """日志管理类 - 支持日志轮转，最多保留7天"""

    def __init__(self, log_dir: str = "logs", log_level: int = logging.INFO):
        self.log_dir = Path(log_dir)
        self.log_level = log_level
        self._ensure_log_dir()
        self._setup_logger()

    def _ensure_log_dir(self):
        """确保日志目录存在"""
        if not self.log_dir.exists():
            self.log_dir.mkdir(parents=True, exist_ok=True)

    def _setup_logger(self):
        """设置日志器"""
        # 创建主日志器
        self.logger = logging.getLogger("github_manager")
        self.logger.setLevel(self.log_level)

        # 清除现有handlers
        self.logger.handlers.clear()

        # 日志文件路径
        log_file = self.log_dir / "app.log"

        # 使用 TimedRotatingFileHandler 实现日志轮转
        file_handler = TimedRotatingFileHandler(
            str(log_file),
            when='midnight',
            interval=1,
            backupCount=7,
            encoding='utf-8'
        )
        file_handler.setLevel(self.log_level)

        # 日志格式
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(module)s:%(funcName)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)

        # 添加handler
        self.logger.addHandler(file_handler)

        # 清理过期日志文件
        self._cleanup_old_logs()

    def _cleanup_old_logs(self):
        """清理超过7天的日志文件"""
        try:
            cutoff_date = datetime.now() - timedelta(days=7)
            for log_file in self.log_dir.glob("app.log*"):
                if log_file.stat().st_mtime < cutoff_date.timestamp():
                    log_file.unlink()
                    self.logger.debug(f"已清理过期日志: {log_file}")
        except Exception as e:
            self.logger.warning(f"清理日志失败: {e}")

    def get_logger(self, module_name: str = None) -> logging.Logger:
        """获取日志器"""
        if module_name:
            return logging.getLogger(f"github_manager.{module_name}")
        return self.logger

    def info(self, message: str):
        """记录INFO级别日志"""
        self.logger.info(message)

    def warning(self, message: str):
        """记录WARNING级别日志"""
        self.logger.warning(message)

    def error(self, message: str):
        """记录ERROR级别日志"""
        self.logger.error(message)

    def debug(self, message: str):
        """记录DEBUG级别日志"""
        self.logger.debug(message)

    def exception(self, message: str):
        """记录异常日志"""
        self.logger.exception(message)


# 全局日志管理器实例
_log_manager = None


def get_log_manager(log_dir: str = "logs") -> LogManager:
    """获取全局日志管理器实例"""
    global _log_manager
    if _log_manager is None:
        _log_manager = LogManager(log_dir=log_dir)
    return _log_manager


def get_logger(module_name: str = None) -> logging.Logger:
    """获取日志器"""
    return get_log_manager().get_logger(module_name)