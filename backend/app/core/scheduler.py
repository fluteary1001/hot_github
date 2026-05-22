"""定时任务调度器模块"""
import asyncio
import threading
from datetime import datetime
from typing import Optional
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from .database import ProjectDB
from .history_manager import HistoryManager
from .trending_scraper import TrendingScraper
from .downloader import ProjectDownloader
from .doc_generator import WebDocGenerator
from .logger import get_logger

_logger = get_logger("scheduler")


class TrendingScheduler:
    """热点采集调度器"""

    def __init__(self, db: ProjectDB, settings, shutdown_event: threading.Event):
        self.db = db
        self.settings = settings
        self.shutdown_event = shutdown_event
        self.history_manager = HistoryManager(db)
        self.scheduler = BackgroundScheduler()
        self._setup_jobs()

    def _setup_jobs(self):
        """配置定时任务"""

        # 每天 22:00 采集日热点
        self.scheduler.add_job(
            self.collect_daily_trending,
            CronTrigger(hour=22, minute=0),
            id='daily_trending',
            name='每日热点采集',
            replace_existing=True
        )

        # 每周一 22:00 采集周热点
        self.scheduler.add_job(
            self.collect_weekly_trending,
            CronTrigger(day_of_week='mon', hour=22, minute=0),
            id='weekly_trending',
            name='每周热点采集',
            replace_existing=True
        )

        # 每月1日 22:00 采集月热点
        self.scheduler.add_job(
            self.collect_monthly_trending,
            CronTrigger(day=1, hour=22, minute=0),
            id='monthly_trending',
            name='每月热点采集',
            replace_existing=True
        )

        # 凌晨 00:30 开始自动下载和分析
        self.scheduler.add_job(
            self.process_auto_download_and_analysis,
            CronTrigger(hour=0, minute=30),
            id='auto_analysis',
            name='自动下载与分析',
            replace_existing=True
        )

        # 失败重试任务，每小时检查一次
        self.scheduler.add_job(
            self.retry_failed_analysis,
            CronTrigger(minute=0),  # 每小时整点
            id='retry_analysis',
            name='失败重试',
            replace_existing=True
        )

        _logger.info("定时任务已配置完成")

    def start(self):
        """启动调度器"""
        self.scheduler.start()
        _logger.info(f"调度器已启动，当前任务列表: {[job.id for job in self.scheduler.get_jobs()]}")

    def shutdown(self):
        """关闭调度器"""
        _logger.info("开始关闭调度器...")

        # 先暂停所有任务
        try:
            jobs = self.scheduler.get_jobs()
            _logger.info(f"当前有 {len(jobs)} 个任务")
            for job in jobs:
                try:
                    self.scheduler.pause_job(job.id)
                    _logger.info(f"已暂停任务: {job.id}")
                except Exception as e:
                    _logger.warning(f"暂停任务 {job.id} 失败: {e}")
        except Exception as e:
            _logger.error(f"获取任务列表失败: {e}")

        # 关闭调度器
        try:
            _logger.info("正在关闭 BackgroundScheduler...")
            self.scheduler.shutdown(wait=False)
            _logger.info("BackgroundScheduler.shutdown() 返回")
        except Exception as e:
            _logger.error(f"调度器关闭异常: {e}")

        _logger.info("调度器关闭完成")

    def collect_daily_trending(self):
        """采集每日热点"""
        if self.shutdown_event.is_set():
            return

        task_name = 'daily_trending'
        _logger.info(f"开始执行: {task_name}")

        try:
            self.db.update_scheduler_task(task_name, 'running')

            scraper = TrendingScraper(
                self.settings.GITHUB_TOKEN,
                timeout=self.settings.GITHUB_API_TIMEOUT
            )

            period_value = self.history_manager.get_today_period_value()
            limit = self.settings.TRENDING_OFFICIAL_LIMIT

            results = scraper.get_trending(since='daily', limit=limit)
            saved = self.db.save_trending_history(results, 'daily', period_value)

            self.db.update_scheduler_task(
                task_name, 'completed',
                result=f"保存了 {saved} 个项目",
                last_run_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            _logger.info(f"每日热点采集完成: {saved} 个项目")

            # 采集后立即下载
            if self.settings.HISTORY_TRENDING_AUTO_DOWNLOAD:
                self._auto_download_trending(period_value)

        except Exception as e:
            _logger.error(f"每日热点采集失败: {e}")
            self.db.update_scheduler_task(task_name, 'failed', result=str(e))

    def collect_weekly_trending(self):
        """采集每周热点"""
        if self.shutdown_event.is_set():
            return

        task_name = 'weekly_trending'
        _logger.info(f"开始执行: {task_name}")

        try:
            self.db.update_scheduler_task(task_name, 'running')

            scraper = TrendingScraper(
                self.settings.GITHUB_TOKEN,
                timeout=self.settings.GITHUB_API_TIMEOUT
            )

            period_value = self.history_manager.get_this_week_period_value()
            limit = self.settings.TRENDING_OFFICIAL_LIMIT

            results = scraper.get_trending(since='weekly', limit=limit)
            saved = self.db.save_trending_history(results, 'weekly', period_value)

            self.db.update_scheduler_task(
                task_name, 'completed',
                result=f"保存了 {saved} 个项目",
                last_run_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            _logger.info(f"每周热点采集完成: {saved} 个项目")

        except Exception as e:
            _logger.error(f"每周热点采集失败: {e}")
            self.db.update_scheduler_task(task_name, 'failed', result=str(e))

    def collect_monthly_trending(self):
        """采集每月热点"""
        if self.shutdown_event.is_set():
            return

        task_name = 'monthly_trending'
        _logger.info(f"开始执行: {task_name}")

        try:
            self.db.update_scheduler_task(task_name, 'running')

            scraper = TrendingScraper(
                self.settings.GITHUB_TOKEN,
                timeout=self.settings.GITHUB_API_TIMEOUT
            )

            period_value = self.history_manager.get_this_month_period_value()
            limit = self.settings.TRENDING_OFFICIAL_LIMIT

            results = scraper.get_trending(since='monthly', limit=limit)
            saved = self.db.save_trending_history(results, 'monthly', period_value)

            self.db.update_scheduler_task(
                task_name, 'completed',
                result=f"保存了 {saved} 个项目",
                last_run_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            _logger.info(f"每月热点采集完成: {saved} 个项目")

        except Exception as e:
            _logger.error(f"每月热点采集失败: {e}")
            self.db.update_scheduler_task(task_name, 'failed', result=str(e))

    def _auto_download_trending(self, period_value: str):
        """自动下载热点项目"""
        _logger.info(f"开始自动下载热点项目: {period_value}")

        pending = self.db.get_pending_download_history(period_value)
        downloader = ProjectDownloader(self.settings.DOWNLOAD_PATH)
        download_path = Path(self.settings.DOWNLOAD_PATH)

        for item in pending:
            if self.shutdown_event.is_set():
                break

            try:
                clone_url = item['clone_url']
                project_name = item['project_name']
                full_name = item['full_name']

                # 1. 先检查数据库中是否已存在该项目
                existing = self.db.get_project_by_name(full_name)
                if existing:
                    # 已存在，执行更新并标记为已下载
                    _logger.info(f"项目已存在于数据库，执行更新: {project_name}")
                    downloader.update_project(existing['local_path'])
                    self.db.update_trending_downloaded(item['id'], existing['id'])
                    _logger.info(f"已标记为已下载: {project_name}")
                    continue

                # 2. 检查本地目录是否已存在
                local_path = download_path / project_name
                if local_path.exists() and (local_path / '.git').exists():
                    # 本地已存在有效仓库，直接添加到数据库并标记
                    _logger.info(f"本地目录已存在有效仓库: {local_path}")
                    project_info = {
                        'name': project_name,
                        'full_name': full_name,
                        'html_url': item['html_url'],
                        'description': item['description'],
                        'stars': item['stars'],
                        'language': item['language'],
                        'clone_url': clone_url,
                        'local_path': str(local_path)
                    }
                    project_id = self.db.add_project(project_info)
                    self.db.update_trending_downloaded(item['id'], project_id)
                    _logger.info(f"已添加到数据库并标记为已下载: {project_name}")
                    continue

                # 3. 执行克隆下载
                _logger.info(f"下载新项目: {project_name}")
                success, result = downloader.clone_project(clone_url, project_name)

                if success:
                    # 保存到 projects 表
                    project_info = {
                        'name': project_name,
                        'full_name': full_name,
                        'html_url': item['html_url'],
                        'description': item['description'],
                        'stars': item['stars'],
                        'language': item['language'],
                        'clone_url': clone_url,
                        'local_path': result  # result 是本地路径
                    }
                    project_id = self.db.add_project(project_info)
                    self.db.update_trending_downloaded(item['id'], project_id)
                    _logger.info(f"下载完成: {project_name}")
                else:
                    # 4. 克隆失败，再次检查本地是否实际已存在
                    if local_path.exists() and (local_path / '.git').exists():
                        # 本地实际已存在，可能是之前下载成功的
                        _logger.info(f"克隆失败但本地已存在有效仓库，标记为已下载: {project_name}")
                        project_info = {
                            'name': project_name,
                            'full_name': full_name,
                            'html_url': item['html_url'],
                            'description': item['description'],
                            'stars': item['stars'],
                            'language': item['language'],
                            'clone_url': clone_url,
                            'local_path': str(local_path)
                        }
                        project_id = self.db.add_project(project_info)
                        self.db.update_trending_downloaded(item['id'], project_id)
                    else:
                        _logger.error(f"下载失败: {project_name}, {result}")

            except Exception as e:
                _logger.error(f"下载失败 {item['project_name']}: {e}")
                # 异常时也检查本地是否存在
                try:
                    local_path = download_path / item['project_name']
                    if local_path.exists() and (local_path / '.git').exists():
                        _logger.info(f"异常但本地已存在，标记为已下载: {item['project_name']}")
                        project_info = {
                            'name': item['project_name'],
                            'full_name': item['full_name'],
                            'html_url': item['html_url'],
                            'description': item.get('description', ''),
                            'stars': item.get('stars', 0),
                            'language': item.get('language', ''),
                            'clone_url': item.get('clone_url', ''),
                            'local_path': str(local_path)
                        }
                        project_id = self.db.add_project(project_info)
                        self.db.update_trending_downloaded(item['id'], project_id)
                except Exception as e2:
                    _logger.error(f"异常恢复失败: {e2}")

    def process_auto_download_and_analysis(self):
        """处理自动下载和分析"""
        if self.shutdown_event.is_set():
            return

        task_name = 'auto_analysis'
        _logger.info(f"开始执行: {task_name}")

        try:
            self.db.update_scheduler_task(task_name, 'running')

            # 获取今日采集的热点
            today = self.history_manager.get_today_period_value()
            history = self.db.get_trending_history('daily', today)

            if not history:
                _logger.info("今日无热点数据，跳过分析")
                self.db.update_scheduler_task(task_name, 'completed', result="无数据")
                return

            # 等待下载完成
            pending_downloads = [h for h in history if not h['downloaded']]
            if pending_downloads:
                _logger.info(f"等待 {len(pending_downloads)} 个项目下载完成")
                self._auto_download_trending(today)

            # 执行 AI 分析
            if self.settings.HISTORY_TRENDING_AUTO_ANALYSIS:
                self._run_analysis_for_history(history)

            self.db.update_scheduler_task(
                task_name, 'completed',
                result=f"分析了 {len(history)} 个项目",
                last_run_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )

        except Exception as e:
            _logger.error(f"自动分析失败: {e}")
            self.db.update_scheduler_task(task_name, 'failed', result=str(e))

    def _run_analysis_for_history(self, history: list[dict]):
        """为历史热点执行 AI 分析"""
        generator = WebDocGenerator(
            download_path=self.settings.DOWNLOAD_PATH,
            api_key=self.settings.CLAUDE_API_KEY,
            model=self.settings.CLAUDE_MODEL,
            base_url=self.settings.CLAUDE_BASE_URL,
            max_tokens=self.settings.CLAUDE_MAX_TOKENS,
            cli_timeout=self.settings.CLAUDE_CLI_TIMEOUT,
            api_timeout=self.settings.CLAUDE_API_TIMEOUT,
            retry_count=self.settings.CLAUDE_RETRY_COUNT,
            analysis_method=self.settings.ANALYSIS_METHOD
        )

        failed_projects = []

        for item in history:
            if self.shutdown_event.is_set():
                break

            if not item['downloaded'] or not item['project_id']:
                continue

            project = self.db.get_project(item['project_id'])
            if not project or not project['local_path']:
                continue

            # 检查是否已生成报告
            existing_report = self.db.get_trending_report_by_history(item['id'])
            if existing_report and existing_report['status'] == 'completed':
                _logger.info(f"报告已存在，跳过: {item['project_name']}")
                continue

            _logger.info(f"开始生成报告: {item['project_name']}")

            try:
                # 创建报告记录
                report_id = self.db.create_trending_report(
                    item['id'], item['project_name'], item['project_id']
                )
                self.db.update_trending_report(report_id, {'status': 'processing'})

                # 生成报告
                local_path = project['local_path']
                project_name = item['project_name']

                results = generator.generate_all_docs(
                    local_path,
                    project_name,
                    progress_callback=lambda k, s: None,
                    shutdown_event=self.shutdown_event,
                    generate_html=True,
                    generate_pptx=False  # 只生成 HTML
                )

                # 更新报告路径
                docs_dir = Path(self.settings.DOWNLOAD_PATH) / "01-docs"
                self.db.update_trending_report(report_id, {
                    'status': 'completed',
                    'design_html_path': str(docs_dir / f"{project_name}-设计说明书.html"),
                    'usage_html_path': str(docs_dir / f"{project_name}-使用说明书.html"),
                    'value_html_path': str(docs_dir / f"{project_name}-价值点分析.html")
                })

                _logger.info(f"报告生成完成: {item['project_name']}")

            except Exception as e:
                _logger.error(f"报告生成失败 {item['project_name']}: {e}")
                failed_projects.append(item['project_name'])

                # 更新失败状态
                if existing_report:
                    self.db.update_trending_report(existing_report['id'], {
                        'status': 'failed',
                        'error_message': str(e),
                        'retry_count': existing_report['retry_count'] + 1
                    })
                else:
                    report_id = self.db.create_trending_report(
                        item['id'], item['project_name'], item['project_id']
                    )
                    self.db.update_trending_report(report_id, {
                        'status': 'failed',
                        'error_message': str(e)
                    })

        if failed_projects:
            _logger.warning(f"失败的项目: {failed_projects}")

    def retry_failed_analysis(self):
        """重试失败的分析任务"""
        if self.shutdown_event.is_set():
            return

        task_name = 'retry_analysis'
        max_retry = getattr(self.settings, 'HISTORY_TRENDING_MAX_RETRY', 3)

        failed_reports = self.db.get_failed_reports_for_retry(max_retry)

        if not failed_reports:
            return

        _logger.info(f"开始重试 {len(failed_reports)} 个失败任务")

        for report in failed_reports:
            if self.shutdown_event.is_set():
                break

            try:
                history = self.db.get_trending_history(
                    report.get('period_type', 'daily'),
                    report.get('period_value', '')
                )
                history_item = next(
                    (h for h in history if h['id'] == report['history_id']), None
                )

                if not history_item:
                    continue

                self._run_single_analysis(history_item, report)

            except Exception as e:
                _logger.error(f"重试失败 {report['project_name']}: {e}")

    def _run_single_analysis(self, history_item: dict, report: dict):
        """执行单个项目的分析"""
        generator = WebDocGenerator(
            download_path=self.settings.DOWNLOAD_PATH,
            api_key=self.settings.CLAUDE_API_KEY,
            model=self.settings.CLAUDE_MODEL,
            base_url=self.settings.CLAUDE_BASE_URL,
            max_tokens=self.settings.CLAUDE_MAX_TOKENS,
            cli_timeout=self.settings.CLAUDE_CLI_TIMEOUT,
            api_timeout=self.settings.CLAUDE_API_TIMEOUT,
            retry_count=self.settings.CLAUDE_RETRY_COUNT,
            analysis_method=self.settings.ANALYSIS_METHOD
        )

        project = self.db.get_project(history_item['project_id'])
        if not project:
            return

        self.db.update_trending_report(report['id'], {'status': 'processing'})

        try:
            results = generator.generate_all_docs(
                project['local_path'],
                history_item['project_name'],
                progress_callback=lambda k, s: None,
                shutdown_event=self.shutdown_event,
                generate_html=True,
                generate_pptx=False
            )

            docs_dir = Path(self.settings.DOWNLOAD_PATH) / "01-docs"
            self.db.update_trending_report(report['id'], {
                'status': 'completed',
                'design_html_path': str(docs_dir / f"{history_item['project_name']}-设计说明书.html"),
                'usage_html_path': str(docs_dir / f"{history_item['project_name']}-使用说明书.html"),
                'value_html_path': str(docs_dir / f"{history_item['project_name']}-价值点分析.html")
            })

        except Exception as e:
            self.db.update_trending_report(report['id'], {
                'status': 'failed',
                'error_message': str(e),
                'retry_count': report['retry_count'] + 1
            })
            raise

    def manual_collect(self, period_type: str = 'daily') -> dict:
        """手动触发热点采集"""
        _logger.info(f"手动触发热点采集: {period_type}")

        try:
            scraper = TrendingScraper(
                self.settings.GITHUB_TOKEN,
                timeout=self.settings.GITHUB_API_TIMEOUT
            )

            if period_type == 'daily':
                period_value = self.history_manager.get_today_period_value()
            elif period_type == 'weekly':
                period_value = self.history_manager.get_this_week_period_value()
            else:
                period_value = self.history_manager.get_this_month_period_value()

            limit = self.settings.TRENDING_OFFICIAL_LIMIT
            results = scraper.get_trending(since=period_type, limit=limit)
            saved = self.db.save_trending_history(results, period_type, period_value)

            # 自动下载
            if self.settings.HISTORY_TRENDING_AUTO_DOWNLOAD:
                self._auto_download_trending(period_value)

            return {
                "success": True,
                "period_type": period_type,
                "period_value": period_value,
                "saved_count": saved
            }

        except Exception as e:
            _logger.error(f"手动采集失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }