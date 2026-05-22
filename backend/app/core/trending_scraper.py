"""GitHub Trending 爬虫模块"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from .logger import get_logger

_logger = get_logger("trending_scraper")


class TrendingScraper:
    """GitHub Trending 页面爬虫"""

    BASE_URL = "https://github.com/trending"

    def __init__(self, token: str = "", timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        })
        if token:
            self.session.headers.update({"Authorization": f"token {token}"})

    def get_trending(self, since: str = "daily", language: str = "", limit: int = 25) -> list[dict]:
        """获取 GitHub Trending 项目列表

        Args:
            since: 时间范围 "daily", "weekly", "monthly"
            language: 编程语言筛选
            limit: 最大返回数量

        Returns:
            项目列表
        """
        url = self.BASE_URL
        params = {"since": since}
        if language:
            params["spoken_language_code"] = language

        _logger.info(f"获取官方热点: since={since}, language={language}")

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return self._parse_trending_page(response.text, limit)
        except requests.RequestException as e:
            _logger.error(f"获取 Trending 页面失败: {e}")
            return []

    def _parse_trending_page(self, html: str, limit: int) -> list[dict]:
        """解析 Trending 页面 HTML"""
        soup = BeautifulSoup(html, "html.parser")
        results = []

        articles = soup.select("article.Box-row")
        _logger.info(f"找到 {len(articles)} 个项目")

        for article in articles[:limit]:
            try:
                repo = self._parse_repo_article(article)
                if repo:
                    results.append(repo)
            except Exception as e:
                _logger.warning(f"解析项目失败: {e}")
                continue

        return results

    def _parse_repo_article(self, article) -> dict:
        """解析单个项目条目"""
        link = article.select_one("h2 a")
        if not link:
            return None

        href = link.get("href", "")
        if href.startswith("/"):
            href = href[1:]

        full_name = href
        name = full_name.split("/")[-1] if "/" in full_name else full_name
        url = f"https://github.com/{full_name}"

        desc_elem = article.select_one("p.col-9")
        description = desc_elem.get_text(strip=True) if desc_elem else ""

        lang_elem = article.select_one("[itemprop='programmingLanguage']")
        language = lang_elem.get_text(strip=True) if lang_elem else ""

        stars = self._parse_count(article.select_one("a[href*='/stargazers']"))
        forks = self._parse_count(article.select_one("a[href*='/forks']"))

        stars_today_elem = article.select_one("span.d-inline-block.float-sm-right")
        stars_today = 0
        if stars_today_elem:
            stars_today_text = stars_today_elem.get_text(strip=True)
            stars_today = self._parse_stars_today(stars_today_text)

        return {
            "name": name,
            "full_name": full_name,
            "html_url": url,
            "clone_url": f"https://github.com/{full_name}.git",
            "description": description,
            "stars": stars,
            "forks": forks,
            "language": language,
            "stars_today": stars_today,
            "daily_stars": stars_today,
            "topics": [],
            "created_at": "",
            "updated_at": "",
            "owner": full_name.split("/")[0] if "/" in full_name else ""
        }

    def _parse_count(self, elem) -> int:
        """解析数字"""
        if not elem:
            return 0
        text = elem.get_text(strip=True).replace(",", "")
        try:
            return int(text)
        except ValueError:
            return 0

    def _parse_stars_today(self, text: str) -> int:
        """解析今日 Stars 数"""
        import re
        match = re.search(r"([\d,]+)", text)
        if match:
            return int(match.group(1).replace(",", ""))
        return 0