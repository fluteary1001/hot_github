"""Pydantic数据模型"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


# 项目相关
class ProjectBase(BaseModel):
    name: str
    full_name: Optional[str] = None
    html_url: Optional[str] = None
    description: Optional[str] = None
    stars: int = 0
    forks: int = 0
    language: Optional[str] = None
    topics: List[str] = []


class Project(ProjectBase):
    id: Optional[int] = None  # 搜索结果可能没有id
    local_path: Optional[str] = None
    shortcut_path: Optional[str] = None
    clone_url: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    downloaded_at: Optional[str] = None
    is_manual: int = 0

    class Config:
        from_attributes = True


class ProjectCreate(BaseModel):
    clone_url: str
    project_name: str


class ProjectImport(BaseModel):
    path: str
    project_name: Optional[str] = None


class ProjectUpdate(BaseModel):
    description: Optional[str] = None
    usage_guide: Optional[str] = None


# 搜索相关
class SearchQuery(BaseModel):
    query: str
    limit: int = 5


class SearchByUrlQuery(BaseModel):
    url: str


class DownloadRequest(BaseModel):
    clone_url: str
    project_name: str


# Trending相关
class TrendingQuery(BaseModel):
    since: str = "daily"  # daily, weekly, monthly
    language: str = ""
    limit: int = 25


class StarredQuery(BaseModel):
    category: str = "ALL"
    pushed_period: str = "不限制"
    created_period: str = "不限制"
    limit: int = 20


# 文档生成相关
class DocGenerateRequest(BaseModel):
    project_id: int
    doc_types: List[str] = ["design_md", "usage_md", "value_md"]


# 认证相关
class LoginRequest(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class User(BaseModel):
    username: str


# 通用响应
class Message(BaseModel):
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    detail: str
