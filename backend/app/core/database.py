"""数据库操作模块"""
import sqlite3
import json
from datetime import datetime
from typing import Optional


class ProjectDB:
    """项目数据库管理类"""

    def __init__(self, db_path: str = "projects.db"):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """初始化数据库表"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                full_name TEXT UNIQUE,
                html_url TEXT,
                description TEXT,
                stars INTEGER DEFAULT 0,
                forks INTEGER DEFAULT 0,
                language TEXT,
                topics TEXT,
                local_path TEXT,
                shortcut_path TEXT,
                clone_url TEXT,
                created_at TEXT,
                updated_at TEXT,
                downloaded_at TEXT,
                usage_guide TEXT,
                competitors TEXT,
                is_manual INTEGER DEFAULT 0
            )
        ''')

        # 历史热点记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trending_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                period_type TEXT NOT NULL,
                period_value TEXT NOT NULL,
                year INTEGER NOT NULL,
                month INTEGER NOT NULL,
                week INTEGER,
                day INTEGER,
                rank INTEGER NOT NULL,
                project_name TEXT NOT NULL,
                full_name TEXT NOT NULL,
                html_url TEXT,
                description TEXT,
                stars INTEGER DEFAULT 0,
                stars_change INTEGER DEFAULT 0,
                language TEXT,
                clone_url TEXT,
                collected_at TEXT NOT NULL,
                downloaded INTEGER DEFAULT 0,
                project_id INTEGER,
                UNIQUE(period_type, period_value, full_name, rank)
            )
        ''')

        # AI分析报告记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trending_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                history_id INTEGER NOT NULL,
                project_id INTEGER,
                project_name TEXT NOT NULL,
                design_doc_path TEXT,
                usage_doc_path TEXT,
                value_doc_path TEXT,
                design_html_path TEXT,
                usage_html_path TEXT,
                value_html_path TEXT,
                status TEXT DEFAULT 'pending',
                error_message TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT,
                retry_count INTEGER DEFAULT 0,
                FOREIGN KEY (history_id) REFERENCES trending_history(id)
            )
        ''')

        # 定时任务状态表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scheduler_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_name TEXT UNIQUE NOT NULL,
                last_run_at TEXT,
                next_run_at TEXT,
                status TEXT DEFAULT 'idle',
                result TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT
            )
        ''')

        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_trending_history_period ON trending_history(period_type, period_value)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_trending_history_year_month ON trending_history(year, month)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_trending_reports_status ON trending_reports(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_trending_reports_history ON trending_reports(history_id)')

        conn.commit()
        conn.close()

    def add_project(self, project_info: dict) -> int:
        """添加项目到数据库"""
        conn = self._get_conn()
        cursor = conn.cursor()

        topics_json = json.dumps(project_info.get('topics', []), ensure_ascii=False)
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        try:
            cursor.execute('''
                INSERT INTO projects (
                    name, full_name, html_url, description, stars, forks,
                    language, topics, local_path, shortcut_path, clone_url,
                    created_at, updated_at, downloaded_at, usage_guide,
                    competitors, is_manual
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                project_info.get('name'),
                project_info.get('full_name'),
                project_info.get('html_url'),
                project_info.get('description'),
                project_info.get('stars', 0),
                project_info.get('forks', 0),
                project_info.get('language'),
                topics_json,
                project_info.get('local_path'),
                project_info.get('shortcut_path'),
                project_info.get('clone_url'),
                project_info.get('created_at'),
                project_info.get('updated_at'),
                now,
                project_info.get('usage_guide', ''),
                project_info.get('competitors', ''),
                project_info.get('is_manual', 0)
            ))
            project_id = cursor.lastrowid
            conn.commit()
        except sqlite3.IntegrityError:
            cursor.execute('''
                UPDATE projects SET
                    stars = ?, forks = ?, description = ?, language = ?,
                    topics = ?, updated_at = ?, local_path = ?
                WHERE full_name = ?
            ''', (
                project_info.get('stars', 0),
                project_info.get('forks', 0),
                project_info.get('description'),
                project_info.get('language'),
                topics_json,
                now,
                project_info.get('local_path'),
                project_info.get('full_name')
            ))
            cursor.execute('SELECT id FROM projects WHERE full_name = ?',
                          (project_info.get('full_name'),))
            project_id = cursor.fetchone()[0]
            conn.commit()
        finally:
            conn.close()

        return project_id

    def get_all_projects(self) -> list[dict]:
        """获取所有项目"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM projects ORDER BY downloaded_at DESC')
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_dict(row) for row in rows]

    def get_project(self, project_id: int) -> Optional[dict]:
        """根据ID获取项目"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM projects WHERE id = ?', (project_id,))
        row = cursor.fetchone()
        conn.close()
        return self._row_to_dict(row) if row else None

    def get_project_by_name(self, full_name: str) -> Optional[dict]:
        """根据完整名称获取项目"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM projects WHERE full_name = ?', (full_name,))
        row = cursor.fetchone()
        conn.close()
        return self._row_to_dict(row) if row else None

    def update_project(self, project_id: int, fields: dict) -> bool:
        """更新项目信息"""
        if not fields:
            return False

        set_clause = ', '.join([f'{k} = ?' for k in fields.keys()])
        values = list(fields.values()) + [project_id]

        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(f'UPDATE projects SET {set_clause} WHERE id = ?', values)
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success

    def delete_project(self, project_id: int) -> bool:
        """删除项目"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM projects WHERE id = ?', (project_id,))
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success

    def search_projects(self, keyword: str) -> list[dict]:
        """搜索项目"""
        conn = self._get_conn()
        cursor = conn.cursor()
        pattern = f'%{keyword}%'
        cursor.execute('''
            SELECT * FROM projects
            WHERE name LIKE ? OR description LIKE ? OR full_name LIKE ?
            ORDER BY downloaded_at DESC
        ''', (pattern, pattern, pattern))
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_dict(row) for row in rows]

    def _row_to_dict(self, row: sqlite3.Row) -> dict:
        """将数据库行转换为字典"""
        if row is None:
            return None

        result = dict(row)
        if result.get('topics'):
            try:
                result['topics'] = json.loads(result['topics'])
            except json.JSONDecodeError:
                result['topics'] = []
        else:
            result['topics'] = []
        return result

    # ==================== 历史热点相关操作 ====================

    def save_trending_history(self, items: list[dict], period_type: str, period_value: str) -> int:
        """保存热点历史记录

        Args:
            items: 热点项目列表
            period_type: 周期类型 daily/weekly/monthly
            period_value: 周期值 如 2026-05-18

        Returns:
            保存的记录数
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 解析周期信息
        year, month, week, day = self._parse_period_value(period_value, period_type)

        saved_count = 0
        for rank, item in enumerate(items, 1):
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO trending_history (
                        period_type, period_value, year, month, week, day,
                        rank, project_name, full_name, html_url, description,
                        stars, stars_change, language, clone_url, collected_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    period_type, period_value, year, month, week, day,
                    rank, item.get('name'), item.get('full_name'),
                    item.get('html_url'), item.get('description'),
                    item.get('stars', 0), item.get('stars_today', 0) or item.get('stars_change', 0),
                    item.get('language'), item.get('clone_url'), now
                ))
                saved_count += 1
            except sqlite3.IntegrityError:
                continue

        conn.commit()
        conn.close()
        return saved_count

    def _parse_period_value(self, period_value: str, period_type: str) -> tuple:
        """解析周期值"""
        from datetime import timedelta

        if period_type == 'daily':
            # 2026-05-18
            parts = period_value.split('-')
            year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
            # 计算周数
            dt = datetime(year, month, day)
            week = dt.isocalendar()[1]
            return year, month, week, day
        elif period_type == 'weekly':
            # 2026-W20
            parts = period_value.split('-W')
            year, week = int(parts[0]), int(parts[1])
            # 计算该周所属的主要月份（周一所在的月份）
            jan4 = datetime(year, 1, 4)
            week1_monday = jan4 - timedelta(days=jan4.weekday())
            week_monday = week1_monday + timedelta(weeks=week - 1)
            month = week_monday.month
            return year, month, week, 0
        elif period_type == 'monthly':
            # 2026-05
            parts = period_value.split('-')
            year, month = int(parts[0]), int(parts[1])
            return year, month, 0, 0
        return 0, 0, 0, 0

    def get_trending_history(self, period_type: str, period_value: str) -> list[dict]:
        """获取指定周期的热点历史"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM trending_history
            WHERE period_type = ? AND period_value = ?
            ORDER BY rank
        ''', (period_type, period_value))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_trending_years(self) -> list[int]:
        """获取有数据的年份列表"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT year FROM trending_history ORDER BY year DESC')
        rows = cursor.fetchall()
        conn.close()
        return [row['year'] for row in rows]

    def get_trending_months(self, year: int) -> list[dict]:
        """获取指定年份的月份数据"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT month, COUNT(*) as count,
                   MAX(collected_at) as last_collected
            FROM trending_history
            WHERE year = ? AND month > 0
            GROUP BY month
            ORDER BY month DESC
        ''', (year,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_trending_weeks(self, year: int, month: int) -> list[dict]:
        """获取指定月份的周数据"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT week, COUNT(*) as count,
                   MAX(collected_at) as last_collected
            FROM trending_history
            WHERE year = ? AND month = ? AND week > 0
            GROUP BY week
            ORDER BY week DESC
        ''', (year, month))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_trending_days(self, year: int, month: int, week: int = None) -> list[dict]:
        """获取指定周或月份的日数据"""
        conn = self._get_conn()
        cursor = conn.cursor()
        if week:
            cursor.execute('''
                SELECT day, period_value, COUNT(*) as count,
                       MAX(collected_at) as last_collected
                FROM trending_history
                WHERE year = ? AND month = ? AND week = ? AND day > 0
                GROUP BY day
                ORDER BY day DESC
            ''', (year, month, week))
        else:
            cursor.execute('''
                SELECT day, period_value, COUNT(*) as count,
                       MAX(collected_at) as last_collected
                FROM trending_history
                WHERE year = ? AND month = ? AND day > 0
                GROUP BY day
                ORDER BY day DESC
            ''', (year, month))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def update_trending_downloaded(self, history_id: int, project_id: int):
        """更新热点记录的下载状态"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE trending_history
            SET downloaded = 1, project_id = ?
            WHERE id = ?
        ''', (project_id, history_id))
        conn.commit()
        conn.close()

    def get_pending_download_history(self, period_value: str) -> list[dict]:
        """获取待下载的热点记录"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM trending_history
            WHERE period_value = ? AND downloaded = 0
            ORDER BY rank
        ''', (period_value,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    # ==================== 分析报告相关操作 ====================

    def create_trending_report(self, history_id: int, project_name: str, project_id: int = None) -> int:
        """创建分析报告记录"""
        conn = self._get_conn()
        cursor = conn.cursor()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT INTO trending_reports (
                history_id, project_id, project_name, status, created_at
            ) VALUES (?, ?, ?, 'pending', ?)
        ''', (history_id, project_id, project_name, now))
        report_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return report_id

    def update_trending_report(self, report_id: int, fields: dict):
        """更新分析报告"""
        fields['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        set_clause = ', '.join([f'{k} = ?' for k in fields.keys()])
        values = list(fields.values()) + [report_id]

        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(f'UPDATE trending_reports SET {set_clause} WHERE id = ?', values)
        conn.commit()
        conn.close()

    def get_trending_report_by_history(self, history_id: int) -> Optional[dict]:
        """根据历史记录ID获取报告"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM trending_reports WHERE history_id = ?', (history_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_pending_reports(self) -> list[dict]:
        """获取待处理的报告"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM trending_reports
            WHERE status IN ('pending', 'processing')
            ORDER BY created_at
        ''')
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_failed_reports_for_retry(self, max_retry: int = 3) -> list[dict]:
        """获取需要重试的失败报告"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM trending_reports
            WHERE status = 'failed'
            AND retry_count < ?
            AND datetime(updated_at) < datetime('now', '-1 hour')
        ''', (max_retry,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    # ==================== 定时任务相关操作 ====================

    def update_scheduler_task(self, task_name: str, status: str, result: str = None,
                               last_run_at: str = None, next_run_at: str = None):
        """更新定时任务状态"""
        conn = self._get_conn()
        cursor = conn.cursor()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        cursor.execute('SELECT id FROM scheduler_tasks WHERE task_name = ?', (task_name,))
        row = cursor.fetchone()

        if row:
            cursor.execute('''
                UPDATE scheduler_tasks SET
                    status = ?, result = ?, updated_at = ?,
                    last_run_at = COALESCE(?, last_run_at),
                    next_run_at = COALESCE(?, next_run_at)
                WHERE task_name = ?
            ''', (status, result, now, last_run_at, next_run_at, task_name))
        else:
            cursor.execute('''
                INSERT INTO scheduler_tasks (
                    task_name, status, result, last_run_at, next_run_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (task_name, status, result, last_run_at, next_run_at, now))

        conn.commit()
        conn.close()

    def get_scheduler_task(self, task_name: str) -> Optional[dict]:
        """获取定时任务状态"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM scheduler_tasks WHERE task_name = ?', (task_name,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None