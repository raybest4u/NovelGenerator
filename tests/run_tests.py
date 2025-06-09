
# tests/run_tests.py
"""
测试运行脚本
"""

import sys
import pytest

if __name__ == "__main__":
    # 运行所有测试
    exit_code = pytest.main([
        "tests/",
        "-v",
        "--tb=short",
        "--cov=fantasy_novel_mcp",
        "--cov-report=html",
        "--cov-report=term-missing"
    ])

    sys.exit(exit_code)
