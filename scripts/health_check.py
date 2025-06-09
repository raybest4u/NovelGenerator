# scripts/health_check.py
# !/usr/bin/env python3
"""
健康检查脚本
用于监控系统状态和服务健康
"""

import asyncio
import aiohttp
import json
import sys
import time
from typing import Dict, Any, List
from datetime import datetime


class HealthChecker:
    """健康检查器"""

    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.checks = []

    async def check_api_health(self) -> Dict[str, Any]:
        """检查API健康状态"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/health", timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return {
                            "name": "API Health",
                            "status": "healthy",
                            "details": data
                        }
                    else:
                        return {
                            "name": "API Health",
                            "status": "unhealthy",
                            "error": f"HTTP {resp.status}"
                        }
        except Exception as e:
            return {
                "name": "API Health",
                "status": "unhealthy",
                "error": str(e)
            }

    async def check_database_connection(self) -> Dict[str, Any]:
        """检查数据库连接"""
        try:
            from data.models import create_database_session

            db = create_database_session()
            # 简单查询测试连接
            db.execute("SELECT 1")
            db.close()

            return {
                "name": "Database Connection",
                "status": "healthy",
                "details": {"connection": "ok"}
            }
        except Exception as e:
            return {
                "name": "Database Connection",
                "status": "unhealthy",
                "error": str(e)
            }

    async def check_llm_connection(self) -> Dict[str, Any]:
        """检查LLM连接"""
        try:
            from core.llm_client import get_llm_service

            llm_service = get_llm_service()
            # 发送简单测试请求
            response = await llm_service.generate_text("测试", use_history=False)

            return {
                "name": "LLM Connection",
                "status": "healthy",
                "details": {
                    "response_time": response.response_time,
                    "model": response.model
                }
            }
        except Exception as e:
            return {
                "name": "LLM Connection",
                "status": "unhealthy",
                "error": str(e)
            }

    async def check_disk_space(self) -> Dict[str, Any]:
        """检查磁盘空间"""
        try:
            import shutil

            total, used, free = shutil.disk_usage('/')
            free_percent = (free / total) * 100

            status = "healthy"
            if free_percent < 10:
                status = "critical"
            elif free_percent < 20:
                status = "warning"

            return {
                "name": "Disk Space",
                "status": status,
                "details": {
                    "free_percent": round(free_percent, 2),
                    "free_gb": round(free / (1024 ** 3), 2),
                    "total_gb": round(total / (1024 ** 3), 2)
                }
            }
        except Exception as e:
            return {
                "name": "Disk Space",
                "status": "unhealthy",
                "error": str(e)
            }

    async def check_memory_usage(self) -> Dict[str, Any]:
        """检查内存使用"""
        try:
            import psutil

            memory = psutil.virtual_memory()

            status = "healthy"
            if memory.percent > 90:
                status = "critical"
            elif memory.percent > 80:
                status = "warning"

            return {
                "name": "Memory Usage",
                "status": status,
                "details": {
                    "percent": memory.percent,
                    "available_gb": round(memory.available / (1024 ** 3), 2),
                    "total_gb": round(memory.total / (1024 ** 3), 2)
                }
            }
        except Exception as e:
            return {
                "name": "Memory Usage",
                "status": "unhealthy",
                "error": str(e)
            }

    async def run_all_checks(self) -> Dict[str, Any]:
        """运行所有健康检查"""
        checks = [
            self.check_api_health(),
            self.check_database_connection(),
            self.check_llm_connection(),
            self.check_disk_space(),
            self.check_memory_usage()
        ]

        results = await asyncio.gather(*checks, return_exceptions=True)

        # 处理异常
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "name": f"Check {i + 1}",
                    "status": "error",
                    "error": str(result)
                })
            else:
                processed_results.append(result)

        # 计算总体状态
        overall_status = "healthy"
        for check in processed_results:
            if check["status"] in ["critical", "error"]:
                overall_status = "critical"
                break
            elif check["status"] == "warning" and overall_status == "healthy":
                overall_status = "warning"

        return {
            "timestamp": datetime.now().isoformat(),
            "overall_status": overall_status,
            "checks": processed_results
        }


async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Fantasy Novel MCP 健康检查")
    parser.add_argument("--url", default="http://localhost:8080", help="服务地址")
    parser.add_argument("--format", choices=["json", "text"], default="text", help="输出格式")
    parser.add_argument("--exit-code", action="store_true", help="根据健康状态返回退出码")

    args = parser.parse_args()

    checker = HealthChecker(args.url)
    result = await checker.run_all_checks()

    if args.format == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        # 文本格式输出
        print(f"健康检查报告 - {result['timestamp']}")
        print("=" * 50)
        print(f"总体状态: {result['overall_status'].upper()}")
        print()

        for check in result['checks']:
            status_symbol = {
                "healthy": "✅",
                "warning": "⚠️",
                "unhealthy": "❌",
                "critical": "🚨",
                "error": "💥"
            }.get(check['status'], "❓")

            print(f"{status_symbol} {check['name']}: {check['status'].upper()}")

            if 'details' in check:
                for key, value in check['details'].items():
                    print(f"   {key}: {value}")

            if 'error' in check:
                print(f"   错误: {check['error']}")

            print()

    # 根据健康状态返回退出码
    if args.exit_code:
        if result['overall_status'] in ['critical', 'error']:
            sys.exit(2)
        elif result['overall_status'] == 'warning':
            sys.exit(1)
        else:
            sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())


