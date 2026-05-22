"""项目下载器模块 - 支持异步和进度回调"""
import os
import subprocess
import shutil
import socket
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Callable, Optional
from .logger import get_logger

_logger = get_logger("downloader")


class ProjectDownloader:
    """项目下载管理类"""

    def __init__(self, download_path: str, status_callback: Optional[Callable] = None):
        if download_path.startswith("~"):
            download_path = str(Path(download_path).expanduser())
        self.download_path = Path(download_path)
        self.status_callback = status_callback
        _logger.info(f"初始化下载器，下载路径: {self.download_path}")
        self._ensure_download_path()

    def _log(self, message: str):
        """输出状态日志"""
        _logger.info(message)
        if self.status_callback:
            self.status_callback(message)

    def _ensure_download_path(self):
        """确保下载目录存在"""
        if not self.download_path.exists():
            self.download_path.mkdir(parents=True, exist_ok=True)
            self._log(f"创建下载目录: {self.download_path}")

    def test_github_connection(self) -> tuple[bool, str]:
        """测试是否能连接到 GitHub"""
        self._log("测试 GitHub 连接...")
        try:
            socket.gethostbyname('github.com')
            self._log("DNS 解析成功: github.com")

            result = subprocess.run(
                ['git', 'ls-remote', '--heads', 'https://github.com/git/git.git'],
                capture_output=True,
                text=True,
                timeout=15
            )
            if result.returncode == 0:
                self._log("GitHub 连接测试成功")
                return True, "连接正常"
            else:
                error = result.stderr.strip()
                self._log(f"GitHub 连接测试失败: {error}")
                return False, f"连接失败: {error}"
        except socket.gaierror as e:
            self._log(f"DNS 解析失败: {e}")
            return False, "DNS 解析失败，无法解析 github.com"
        except subprocess.TimeoutExpired:
            self._log("连接超时")
            return False, "连接超时，可能需要配置代理"
        except Exception as e:
            self._log(f"连接测试异常: {e}")
            return False, f"连接异常: {e}"

    def clone_project(self, clone_url: str, project_name: str) -> tuple[bool, str]:
        """克隆项目到本地"""
        target_path = self.download_path / project_name

        _logger.info(f"开始克隆项目: {project_name}")
        _logger.info(f"克隆URL: {clone_url}")
        _logger.info(f"目标路径: {target_path}")

        self._log(f"准备克隆项目: {project_name}")
        self._log(f"克隆URL: {clone_url}")
        self._log(f"目标路径: {target_path}")

        if target_path.exists():
            _logger.warning(f"目录已存在，跳过克隆: {target_path}")
            return False, f"目录已存在: {target_path}"

        connected, msg = self.test_github_connection()
        if not connected:
            self._log(f"网络问题: {msg}")
            self._log("建议: 配置 git 代理或使用镜像站点")
            return False, f"网络连接失败: {msg}"

        try:
            self._log("执行 git clone 命令...")
            process = subprocess.Popen(
                ['git', 'clone', '--progress', clone_url, str(target_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            while True:
                line = process.stderr.readline()
                if line:
                    self._log(f"[git] {line.strip()}")
                if process.poll() is not None:
                    remaining = process.stderr.read()
                    if remaining:
                        self._log(f"[git] {remaining.strip()}")
                    break

            if process.returncode == 0:
                self._log("克隆成功！")
                _logger.info(f"项目克隆成功: {project_name} -> {target_path}")
                return True, str(target_path)
            else:
                stdout, stderr = process.communicate()
                error_msg = stderr or stdout or "未知错误"
                self._log(f"克隆失败: {error_msg}")
                _logger.error(f"项目克隆失败: {project_name}, 错误: {error_msg}")
                return False, f"克隆失败: {error_msg}"
        except subprocess.TimeoutExpired:
            self._log("克隆超时")
            return False, "克隆超时"
        except FileNotFoundError:
            self._log("未找到git命令")
            return False, "未找到git命令，请确保git已安装"
        except Exception as e:
            self._log(f"克隆异常: {e}")
            _logger.exception(f"项目克隆异常: {project_name}")
            return False, f"克隆异常: {e}"

    async def clone_project_async(
        self,
        clone_url: str,
        project_name: str,
        progress_callback: Optional[Callable] = None
    ) -> tuple[bool, str]:
        """异步克隆项目"""
        target_path = self.download_path / project_name

        if target_path.exists():
            return False, f"目录已存在: {target_path}"

        connected, msg = self.test_github_connection()
        if not connected:
            return False, f"网络连接失败: {msg}"

        def run_clone():
            return self.clone_project(clone_url, project_name)

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, run_clone)
        return result

    def update_project(self, project_path: str) -> tuple[bool, str]:
        """执行 git pull 更新项目代码"""
        _logger.info(f"开始更新项目: {project_path}")

        path = Path(project_path)
        if not path.exists():
            return False, f"项目目录不存在: {project_path}"

        git_dir = path / '.git'
        if not git_dir.exists():
            return False, "项目不是git仓库，无法更新"

        try:
            self._log(f"正在更新项目: {project_path}")
            result = subprocess.run(
                ['git', 'pull'],
                cwd=str(path),
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode == 0:
                output = result.stdout.strip() or "已是最新版本"
                _logger.info(f"项目更新成功: {project_path}")
                self._log(f"更新成功: {output}")
                return True, output
            else:
                error = result.stderr.strip() or "更新失败"
                _logger.warning(f"项目更新失败: {project_path}, {error}")
                return False, error
        except subprocess.TimeoutExpired:
            return False, "更新超时"
        except Exception as e:
            _logger.exception(f"项目更新异常: {project_path}")
            return False, f"更新异常: {e}"

    def delete_project(self, project_path: str, shortcut_path: str = None) -> bool:
        """删除项目目录和快捷方式"""
        try:
            if Path(project_path).exists():
                shutil.rmtree(project_path)

            if shortcut_path and Path(shortcut_path).exists():
                Path(shortcut_path).unlink()

            return True
        except OSError as e:
            _logger.error(f"删除失败: {e}")
            return False

    def get_project_info_from_local(self, project_path: str) -> dict:
        """从本地项目获取基本信息"""
        path = Path(project_path)
        info = {
            'name': path.name,
            'local_path': str(path),
            'is_manual': 1
        }

        git_dir = path / '.git'
        if git_dir.exists():
            try:
                result = subprocess.run(
                    ['git', 'remote', 'get-url', 'origin'],
                    cwd=str(path),
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    info['clone_url'] = result.stdout.strip()
                    if 'github.com' in info['clone_url']:
                        parts = info['clone_url'].replace('.git', '').split('/')
                        if len(parts) >= 2:
                            info['full_name'] = f"{parts[-2]}/{parts[-1]}"
                            info['html_url'] = f"https://github.com/{info['full_name']}"
            except Exception:
                pass

        return info