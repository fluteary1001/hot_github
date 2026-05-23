"""配置管理模块 - 从 backend/config.json 和 .env 加载"""
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# 加载 .env 文件
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)


def _default_config_path() -> Path:
    """获取默认配置文件路径: backend/config.json"""
    return Path(__file__).parent.parent / "config.json"


# JSON key -> Settings 属性名 的映射表
_FIELD_MAP = {
    'app_name': 'APP_NAME',
    'debug': 'DEBUG',
    'cors_origins': 'CORS_ORIGINS',
    'download_path': 'DOWNLOAD_PATH',
    'db_path': 'DB_PATH',
    'log_dir': 'LOG_DIR',
    'github_token': 'GITHUB_TOKEN',
    'github_api_timeout': 'GITHUB_API_TIMEOUT',
    'max_search_results': 'MAX_SEARCH_RESULTS',
    'claude_api_key': 'CLAUDE_API_KEY',
    'claude_model': 'CLAUDE_MODEL',
    'claude_base_url': 'CLAUDE_BASE_URL',
    'claude_max_tokens': 'CLAUDE_MAX_TOKENS',
    'claude_cli_timeout': 'CLAUDE_CLI_TIMEOUT',
    'claude_api_timeout': 'CLAUDE_API_TIMEOUT',
    'claude_retry_count': 'CLAUDE_RETRY_COUNT',
    'analysis_method': 'ANALYSIS_METHOD',
    'require_login': 'REQUIRE_LOGIN',
    'secret_key': 'SECRET_KEY',
    'algorithm': 'ALGORITHM',
    'access_token_expire_minutes': 'ACCESS_TOKEN_EXPIRE_MINUTES',
    'users': 'USERS',
    'trending_enabled': 'TRENDING_ENABLED',
    'trending_official_limit': 'TRENDING_OFFICIAL_LIMIT',
    'trending_starred_limit': 'TRENDING_STARRED_LIMIT',
    'trending_categories': 'TRENDING_CATEGORIES',
    'docs_generate_html': 'DOCS_GENERATE_HTML',
    'docs_generate_pptx': 'DOCS_GENERATE_PPTX',
    # 历史热点配置
    'history_trending_enabled': 'HISTORY_TRENDING_ENABLED',
    'history_trending_auto_download': 'HISTORY_TRENDING_AUTO_DOWNLOAD',
    'history_trending_auto_analysis': 'HISTORY_TRENDING_AUTO_ANALYSIS',
    'history_trending_max_retry': 'HISTORY_TRENDING_MAX_RETRY',
}


class Settings:
    """应用配置 - 仅从 backend/config.json 读取"""

    def __init__(self):
        # 服务器配置
        self.APP_NAME: str = "Hot Github"
        self.DEBUG: bool = True
        self.CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

        # 路径配置
        self.DOWNLOAD_PATH: str = "~/github_projects"
        self.DB_PATH: str = "projects.db"
        self.LOG_DIR: str = "logs"

        # GitHub配置
        self.GITHUB_TOKEN: Optional[str] = None
        self.GITHUB_API_TIMEOUT: int = 30
        self.MAX_SEARCH_RESULTS: int = 5

        # Claude配置
        self.CLAUDE_API_KEY: Optional[str] = None
        self.CLAUDE_MODEL: str = "claude-sonnet-4-6"
        self.CLAUDE_BASE_URL: Optional[str] = None
        self.CLAUDE_MAX_TOKENS: int = 8192
        self.CLAUDE_CLI_TIMEOUT: int = 600
        self.CLAUDE_API_TIMEOUT: int = 300
        self.CLAUDE_RETRY_COUNT: int = 3
        self.ANALYSIS_METHOD: str = "cli"

        # 认证配置
        self.REQUIRE_LOGIN: bool = False
        self.SECRET_KEY: str = "your-secret-key-change-in-production"
        self.ALGORITHM: str = "HS256"
        self.ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

        # 用户配置
        self.USERS: Dict[str, str] = {"admin": "admin123"}

        # Trending配置
        self.TRENDING_ENABLED: bool = True
        self.TRENDING_OFFICIAL_LIMIT: int = 25
        self.TRENDING_STARRED_LIMIT: int = 20
        self.TRENDING_CATEGORIES: Dict[str, Any] = {
            "ALL": {"topics": [], "min_stars": 50},
            "AI": {"topics": ["ai", "machine-learning", "llm"], "min_stars": 100},
        }

        # 文档生成配置
        self.DOCS_GENERATE_HTML: bool = True
        self.DOCS_GENERATE_PPTX: bool = True

        # 历史热点配置
        self.HISTORY_TRENDING_ENABLED: bool = True
        self.HISTORY_TRENDING_AUTO_DOWNLOAD: bool = True
        self.HISTORY_TRENDING_AUTO_ANALYSIS: bool = True
        self.HISTORY_TRENDING_MAX_RETRY: int = 3

        # 自动加载配置文件
        self.load_from_json()

    def load_from_json(self, config_path: str = None) -> None:
        """从JSON文件加载配置，覆盖默认值"""
        if config_path is None:
            config_path = str(_default_config_path())

        path = Path(config_path)
        if not path.exists():
            return

        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for json_key, attr_name in _FIELD_MAP.items():
            if json_key in data:
                setattr(self, attr_name, data[json_key])

        # 从 .env 加载敏感信息（优先级高于 config.json）
        self.GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", self.GITHUB_TOKEN)
        self.CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", self.CLAUDE_API_KEY)
        self.SECRET_KEY = os.getenv("SECRET_KEY", self.SECRET_KEY)

    def save_to_json(self, config_path: str = None) -> None:
        """保存当前配置到JSON文件"""
        if config_path is None:
            config_path = str(_default_config_path())

        path = Path(config_path)
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {}

        for json_key, attr_name in _FIELD_MAP.items():
            data[json_key] = getattr(self, attr_name)

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


# 全局配置实例 - 构造时自动从 config.json 加载
settings = Settings()
