
# scripts/performance_test.py
# !/usr/bin/env python3
"""
性能测试脚本
"""

import asyncio
import aiohttp
import time
import json
import statistics
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor


class PerformanceTester:
    """性能测试器"""

    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.results = []

    async def test_api_endpoint(self, endpoint: str, method: str = "GET",
                                data: Dict = None, concurrent: int = 1,
                                requests: int = 10) -> Dict[str, Any]:
        """测试API端点性能"""

        async def single_request(session):
            start_time = time.time()
            try:
                async with session.request(
                        method,
                        f"{self.base_url}{endpoint}",
                        json=data,
                        timeout=30
                ) as resp:
                    await resp.text()
                    end_time = time.time()
                    return {
                        "status": resp.status,
                        "response_time": end_time - start_time,
                        "success": 200 <= resp.status < 400
                    }
            except Exception as e:
                end_time = time.time()
                return {
                    "status": 0,
                    "response_time": end_time - start_time,
                    "success": False,
                    "error": str(e)
                }

        # 并发测试
        connector = aiohttp.TCPConnector(limit=concurrent)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = []

            # 创建请求任务
            for _ in range(requests):
                tasks.append(single_request(session))

            # 执行并发请求
            start_time = time.time()
            results = await asyncio.gather(*tasks)
            total_time = time.time() - start_time

        # 分析结果
        response_times = [r["response_time"] for r in results]
        success_count = sum(1 for r in results if r["success"])

        return {
            "endpoint": endpoint,
            "method": method,
            "concurrent": concurrent,
            "total_requests": requests,
            "successful_requests": success_count,
            "failed_requests": requests - success_count,
            "success_rate": success_count / requests,
            "total_time": total_time,
            "requests_per_second": requests / total_time,
            "avg_response_time": statistics.mean(response_times),
            "min_response_time": min(response_times),
            "max_response_time": max(response_times),
            "median_response_time": statistics.median(response_times),
            "p95_response_time": self._percentile(response_times, 95),
            "p99_response_time": self._percentile(response_times, 99)
        }

    def _percentile(self, data: List[float], percentile: int) -> float:
        """计算百分位数"""
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]

    async def test_health_endpoint(self):
        """测试健康检查端点"""
        return await self.test_api_endpoint("/health", "GET", concurrent=10, requests=50)

    async def test_chat_endpoint(self):
        """测试聊天端点"""
        data = {
            "message": "你好",
            "session_id": "test_session",
            "use_tools": False
        }
        return await self.test_api_endpoint("/chat", "POST", data, concurrent=5, requests=20)

    async def test_tool_call_endpoint(self):
        """测试工具调用端点"""
        data = {
            "tool_name": "name_generator",
            "parameters": {
                "name_type": "character",
                "count": 3
            }
        }
        return await self.test_api_endpoint("/tools/call", "POST", data, concurrent=3, requests=10)

    async def run_full_test_suite(self) -> Dict[str, Any]:
        """运行完整测试套件"""
        print("开始性能测试...")

        tests = [
            ("健康检查", self.test_health_endpoint()),
            ("聊天接口", self.test_chat_endpoint()),
            ("工具调用", self.test_tool_call_endpoint())
        ]

        results = {}

        for test_name, test_coro in tests:
            print(f"测试 {test_name}...")
            try:
                result = await test_coro
                results[test_name] = result
                print(f"✅ {test_name} 完成")
            except Exception as e:
                print(f"❌ {test_name} 失败: {e}")
                results[test_name] = {"error": str(e)}

        return results


async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Fantasy Novel MCP 性能测试")
    parser.add_argument("--url", default="http://localhost:8080", help="服务地址")
    parser.add_argument("--output", help="输出文件")

    args = parser.parse_args()

    tester = PerformanceTester(args.url)
    results = await tester.run_full_test_suite()

    # 输出结果
    print("\n" + "=" * 50)
    print("性能测试报告")
    print("=" * 50)

    for test_name, result in results.items():
        if "error" in result:
            print(f"\n❌ {test_name}: {result['error']}")
            continue

        print(f"\n📊 {test_name}")
        print(f"   端点: {result['endpoint']}")
        print(f"   成功率: {result['success_rate']:.1%}")
        print(f"   QPS: {result['requests_per_second']:.2f}")
        print(f"   平均响应时间: {result['avg_response_time']:.3f}s")
        print(f"   P95响应时间: {result['p95_response_time']:.3f}s")
        print(f"   P99响应时间: {result['p99_response_time']:.3f}s")

    # 保存结果
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 结果已保存到 {args.output}")


if __name__ == "__main__":
    asyncio.run(main())
