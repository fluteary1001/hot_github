"""历史热点管理模块"""
from datetime import datetime
from typing import Optional
from .database import ProjectDB
from .logger import get_logger

_logger = get_logger("history_manager")


class HistoryManager:
    """历史热点管理类"""

    def __init__(self, db: ProjectDB):
        self.db = db

    def get_tree_data(self) -> list[dict]:
        """获取完整树状结构数据"""
        years = self.db.get_trending_years()
        tree = []

        for year in years:
            year_node = {
                "label": f"{year}年",
                "value": str(year),
                "type": "year",
                "children": []
            }

            months = self.db.get_trending_months(year)
            for month_info in months:
                month = month_info['month']
                month_node = {
                    "label": f"{month}月",
                    "value": f"{year}-{month:02d}",
                    "type": "month",
                    "count": month_info['count'],
                    "children": []
                }

                weeks = self.db.get_trending_weeks(year, month)
                for week_info in weeks:
                    week = week_info['week']
                    # 计算周的日期范围
                    week_start, week_end = self._get_week_range(year, week)
                    week_node = {
                        "label": f"第{week}周 ({week_start}/{week_end})",
                        "value": f"{year}-W{week:02d}",
                        "type": "week",
                        "count": week_info['count'],
                        "children": []
                    }

                    days = self.db.get_trending_days(year, month, week)
                    for day_info in days:
                        day = day_info['day']
                        day_node = {
                            "label": f"{month}月{day}日",
                            "value": day_info['period_value'],
                            "type": "day",
                            "count": day_info['count'],
                            "collected_at": day_info['last_collected']
                        }
                        week_node["children"].append(day_node)

                    month_node["children"].append(week_node)

                year_node["children"].append(month_node)

            tree.append(year_node)

        return tree

    def _get_week_range(self, year: int, week: int) -> tuple:
        """计算周的日期范围"""
        from datetime import timedelta
        # ISO 周的第一天是周一
        jan4 = datetime(year, 1, 4)
        week1_monday = jan4 - timedelta(days=jan4.weekday())
        week_monday = week1_monday + timedelta(weeks=week - 1)
        week_sunday = week_monday + timedelta(days=6)
        return week_monday.month, week_sunday.day

    def get_period_detail(self, period_type: str, period_value: str) -> dict:
        """获取指定周期的热点详情"""
        history = self.db.get_trending_history(period_type, period_value)

        if not history:
            return {
                "period_type": period_type,
                "period_value": period_value,
                "collected_at": None,
                "projects": []
            }

        projects = []
        for item in history:
            project = {
                "rank": item['rank'],
                "name": item['project_name'],
                "full_name": item['full_name'],
                "html_url": item['html_url'],
                "description": item['description'],
                "stars": item['stars'],
                "stars_change": item['stars_change'],
                "language": item['language'],
                "clone_url": item['clone_url'],
                "downloaded": item['downloaded'],
                "project_id": item['project_id'],
                "history_id": item['id']
            }

            # 获取报告信息
            if item['project_id']:
                report = self.db.get_trending_report_by_history(item['id'])
                if report and report['status'] == 'completed':
                    project['reports'] = {
                        "design_html": report.get('design_html_path'),
                        "usage_html": report.get('usage_html_path'),
                        "value_html": report.get('value_html_path')
                    }

            projects.append(project)

        return {
            "period_type": period_type,
            "period_value": period_value,
            "collected_at": history[0]['collected_at'] if history else None,
            "projects": projects
        }

    def get_today_period_value(self) -> str:
        """获取今日的周期值"""
        return datetime.now().strftime('%Y-%m-%d')

    def get_this_week_period_value(self) -> str:
        """获取本周的周期值"""
        iso = datetime.now().isocalendar()
        return f"{iso[0]}-W{iso[1]:02d}"

    def get_this_month_period_value(self) -> str:
        """获取本月的周期值"""
        return datetime.now().strftime('%Y-%m')

    def get_period_type_from_value(self, period_value: str) -> str:
        """根据周期值判断周期类型"""
        if '-W' in period_value:
            return 'weekly'
        elif len(period_value.split('-')) == 3:
            return 'daily'
        else:
            return 'monthly'