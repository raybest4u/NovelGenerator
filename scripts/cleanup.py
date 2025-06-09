
# scripts/cleanup.py
# !/usr/bin/env python3
"""
清理脚本
清理临时文件、日志、缓存等
"""

import os
import shutil
import time
from pathlib import Path
from datetime import datetime, timedelta
from loguru import logger


class Cleaner:
    """清理器"""

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).parent.parent
        self.cleaned_files = 0
        self.freed_space = 0

    def clean_python_cache(self):
        """清理Python缓存"""
        logger.info("清理Python缓存...")

        patterns = ["__pycache__", "*.pyc", "*.pyo", "*.pyd"]

        for pattern in patterns:
            if pattern.startswith("*"):
                # 文件模式
                for file_path in self.project_root.rglob(pattern):
                    self._remove_file(file_path)
            else:
                # 目录模式
                for dir_path in self.project_root.rglob(pattern):
                    if dir_path.is_dir():
                        self._remove_directory(dir_path)

    def clean_logs(self, days: int = 7):
        """清理旧日志文件"""
        logger.info(f"清理{days}天前的日志...")

        logs_dir = self.project_root / "logs"
        if not logs_dir.exists():
            return

        cutoff_date = datetime.now() - timedelta(days=days)

        for log_file in logs_dir.glob("*.log*"):
            if log_file.stat().st_mtime < cutoff_date.timestamp():
                self._remove_file(log_file)

    def clean_temp_files(self):
        """清理临时文件"""
        logger.info("清理临时文件...")

        temp_patterns = [
            "*.tmp", "*.temp", ".tmp", "temp",
            "*.swp", "*.swo", "*~"
        ]

        for pattern in temp_patterns:
            for file_path in self.project_root.rglob(pattern):
                if file_path.is_file():
                    self._remove_file(file_path)
                elif file_path.is_dir() and pattern in ["temp", ".tmp"]:
                    self._remove_directory(file_path)

    def clean_generated_files(self, days: int = 30):
        """清理生成的文件"""
        logger.info(f"清理{days}天前的生成文件...")

        generated_dir = self.project_root / "data" / "generated"
        if not generated_dir.exists():
            return

        cutoff_date = datetime.now() - timedelta(days=days)

        for file_path in generated_dir.rglob("*"):
            if file_path.is_file() and file_path.stat().st_mtime < cutoff_date.timestamp():
                self._remove_file(file_path)

    def clean_test_artifacts(self):
        """清理测试产物"""
        logger.info("清理测试产物...")

        test_patterns = [
            ".pytest_cache", ".coverage", "htmlcov",
            ".tox", ".nox", "coverage.xml"
        ]

        for pattern in test_patterns:
            for path in self.project_root.rglob(pattern):
                if path.is_file():
                    self._remove_file(path)
                elif path.is_dir():
                    self._remove_directory(path)

    def clean_build_artifacts(self):
        """清理构建产物"""
        logger.info("清理构建产物...")

        build_patterns = [
            "build", "dist", "*.egg-info",
            ".eggs", "wheels"
        ]

        for pattern in build_patterns:
            for path in self.project_root.rglob(pattern):
                if path.is_dir():
                    self._remove_directory(path)

    def clean_docker_unused(self):
        """清理Docker未使用资源"""
        logger.info("清理Docker未使用资源...")

        try:
            import subprocess

            # 清理未使用的容器
            subprocess.run(["docker", "container", "prune", "-f"],
                           capture_output=True, check=False)

            # 清理未使用的镜像
            subprocess.run(["docker", "image", "prune", "-f"],
                           capture_output=True, check=False)

            # 清理未使用的网络
            subprocess.run(["docker", "network", "prune", "-f"],
                           capture_output=True, check=False)

            # 清理未使用的卷
            subprocess.run(["docker", "volume", "prune", "-f"],
                           capture_output=True, check=False)

            logger.info("Docker清理完成")

        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("Docker清理失败或Docker未安装")

    def _remove_file(self, file_path: Path):
        """删除文件"""
        try:
            size = file_path.stat().st_size
            file_path.unlink()
            self.cleaned_files += 1
            self.freed_space += size
            logger.debug(f"删除文件: {file_path}")
        except Exception as e:
            logger.warning(f"删除文件失败 {file_path}: {e}")

    def _remove_directory(self, dir_path: Path):
        """删除目录"""
        try:
            # 计算目录大小
            size = sum(f.stat().st_size for f in dir_path.rglob('*') if f.is_file())
            file_count = len(list(dir_path.rglob('*')))

            shutil.rmtree(dir_path)
            self.cleaned_files += file_count
            self.freed_space += size
            logger.debug(f"删除目录: {dir_path}")
        except Exception as e:
            logger.warning(f"删除目录失败 {dir_path}: {e}")

    def format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f}TB"

    def run_full_cleanup(self, log_days: int = 7, generated_days: int = 30,
                         include_docker: bool = False):
        """运行完整清理"""
        logger.info("开始完整清理...")
        start_time = time.time()

        # 执行各项清理
        self.clean_python_cache()
        self.clean_temp_files()
        self.clean_test_artifacts()
        self.clean_build_artifacts()
        self.clean_logs(log_days)
        self.clean_generated_files(generated_days)

        if include_docker:
            self.clean_docker_unused()

        # 输出统计
        end_time = time.time()
        duration = end_time - start_time

        logger.info("清理完成！")
        logger.info(f"清理文件数: {self.cleaned_files}")
        logger.info(f"释放空间: {self.format_size(self.freed_space)}")
        logger.info(f"耗时: {duration:.2f}秒")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Fantasy Novel MCP 清理工具")
    parser.add_argument("--log-days", type=int, default=7, help="保留日志的天数")
    parser.add_argument("--generated-days", type=int, default=30, help="保留生成文件的天数")
    parser.add_argument("--include-docker", action="store_true", help="清理Docker资源")
    parser.add_argument("--dry-run", action="store_true", help="只显示将要清理的内容")

    args = parser.parse_args()

    if args.dry_run:
        logger.info("干运行模式：只显示将要清理的内容")

    cleaner = Cleaner()
    cleaner.run_full_cleanup(
        log_days=args.log_days,
        generated_days=args.generated_days,
        include_docker=args.include_docker
    )


if __name__ == "__main__":
    main()