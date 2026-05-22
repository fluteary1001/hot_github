"""GitHub API封装模块"""
import re
import requests
from datetime import datetime, timedelta
from typing import Optional
from .logger import get_logger

_logger = get_logger("github_api")


class GitHubAPI:
    """GitHub REST API封装类"""

    BASE_URL = "https://api.github.com"

    def __init__(self, token: str = "", timeout: int = 30):
        self.token = token
        self.timeout = timeout
        self.session = requests.Session()
        if token:
            self.session.headers.update({"Authorization": f"token {token}"})
        self.session.headers.update({
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GitHub-Project-Downloader"
        })

    def search_repositories(self, query: str, limit: int = 5) -> list[dict]:
        """搜索GitHub仓库"""
        url = f"{self.BASE_URL}/search/repositories"
        params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": limit
        }

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            return [self._parse_repo(item) for item in data.get('items', [])]
        except requests.RequestException as e:
            _logger.error(f"搜索失败: {e}")
            return []

    def get_repository(self, owner: str, repo: str) -> Optional[dict]:
        """获取单个仓库信息"""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}"

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return self._parse_repo(response.json())
        except requests.RequestException as e:
            _logger.error(f"获取仓库信息失败: {e}")
            return None

    def get_repository_by_url(self, url: str) -> Optional[dict]:
        """通过URL获取仓库信息"""
        owner, repo = self._parse_github_url(url)
        if owner and repo:
            return self.get_repository(owner, repo)
        return None

    def get_readme(self, owner: str, repo: str) -> str:
        """获取README内容"""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/readme"

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            download_url = data.get('download_url')
            if download_url:
                content_response = self.session.get(download_url, timeout=self.timeout)
                return content_response.text
        except requests.RequestException:
            pass
        return ""

    def _parse_repo(self, item: dict) -> dict:
        """解析仓库信息"""
        return {
            'name': item.get('name', ''),
            'full_name': item.get('full_name', ''),
            'html_url': item.get('html_url', ''),
            'description': item.get('description', '') or '',
            'stars': item.get('stargazers_count', 0),
            'forks': item.get('forks_count', 0),
            'language': item.get('language', '') or '',
            'topics': item.get('topics', []),
            'clone_url': item.get('clone_url', ''),
            'created_at': item.get('created_at', ''),
            'updated_at': item.get('updated_at', ''),
            'owner': item.get('owner', {}).get('login', '')
        }

    def _parse_github_url(self, url: str) -> tuple[Optional[str], Optional[str]]:
        """解析GitHub URL，提取owner和repo"""
        patterns = [
            r'github\.com/([^/]+)/([^/]+)/?',
            r'github\.com:([^/]+)/([^/]+)\.git'
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1), match.group(2).replace('.git', '')

        return None, None

    def get_trending(self, category_config: dict, pushed_period: str = "1周", created_period: str = "不限制", max_results: int = 20) -> list[dict]:
        """获取高星项目"""
        period_days = {
            "不限制": None,
            "1天": 1,
            "2天": 2,
            "3天": 3,
            "1周": 7,
            "2周": 14,
            "3周": 21,
            "1月": 30,
            "2月": 60,
            "3月": 90,
            "半年": 180,
            "1年": 365,
            "2年": 730,
            "3年": 1095,
            "5年": 1825,
            "10年": 3650,
        }

        today = datetime.now().date()
        topics = category_config.get("topics", [])
        min_stars = category_config.get("min_stars", 100)

        query_parts = []

        pushed_days = period_days.get(pushed_period)
        if pushed_days is not None:
            pushed_date = (today - timedelta(days=pushed_days)).strftime("%Y-%m-%d")
            query_parts.append(f"pushed:>{pushed_date}")

        created_days = period_days.get(created_period)
        if created_days is not None:
            created_date = (today - timedelta(days=created_days)).strftime("%Y-%m-%d")
            query_parts.append(f"created:>{created_date}")

        query_parts.append(f"stars:>{min_stars}")

        per_topic_limit = 50
        all_results = {}

        if not topics:
            query = " ".join(query_parts)
            _logger.info(f"查询: {query}")
            results = self._search_with_query(query, 100)
            for item in results:
                full_name = item.get("full_name", "")
                if full_name and full_name not in all_results:
                    all_results[full_name] = item
        else:
            for topic in topics:
                query = f"topic:{topic} " + " ".join(query_parts)
                _logger.info(f"查询 [{topic}]: {query}")
                results = self._search_with_query(query, per_topic_limit)
                for item in results:
                    full_name = item.get("full_name", "")
                    if full_name and full_name not in all_results:
                        all_results[full_name] = item

        results = list(all_results.values())
        for item in results:
            item["daily_stars"] = self._calculate_daily_stars(item)

        results.sort(key=lambda x: x.get("daily_stars", 0), reverse=True)

        return results[:max_results]

    def _search_with_query(self, query: str, limit: int) -> list[dict]:
        """执行搜索查询"""
        url = f"{self.BASE_URL}/search/repositories"
        params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": limit
        }

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            return [self._parse_repo(item) for item in data.get("items", [])]
        except requests.RequestException as e:
            _logger.error(f"搜索失败: {e}")
            return []

    def _calculate_daily_stars(self, repo: dict) -> float:
        """计算日均 stars"""
        stars = repo.get("stars", 0)
        created_at = repo.get("created_at", "")

        if not created_at or stars == 0:
            return 0.0

        try:
            created_date = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ").date()
            today = datetime.now().date()
            days = (today - created_date).days

            if days <= 0:
                days = 1

            return round(stars / days, 1)
        except (ValueError, TypeError):
            return 0.0