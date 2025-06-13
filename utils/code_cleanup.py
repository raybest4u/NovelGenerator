# utils/code_cleanup.py
"""
代码清理和重复检测工具
帮助识别和清理项目中的重复代码、未使用文件等
"""
import os
import ast
import re
import hashlib
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
from dataclasses import dataclass, field
from collections import defaultdict, Counter
import importlib.util

from loguru import logger


@dataclass
class DuplicateCode:
    """重复代码信息"""
    files: List[str]
    lines: List[Tuple[int, int]]  # (start_line, end_line)
    code: str
    similarity: float
    type: str  # "function", "class", "block"


@dataclass
class UnusedFile:
    """未使用文件信息"""
    file_path: str
    reason: str
    size: int
    last_modified: float


@dataclass
class CodeIssue:
    """代码问题"""
    file_path: str
    line_number: int
    issue_type: str
    description: str
    severity: str  # "low", "medium", "high"


@dataclass
class CleanupReport:
    """清理报告"""
    duplicate_codes: List[DuplicateCode] = field(default_factory=list)
    unused_files: List[UnusedFile] = field(default_factory=list)
    code_issues: List[CodeIssue] = field(default_factory=list)
    total_files_scanned: int = 0
    total_lines_scanned: int = 0
    duplicate_lines: int = 0
    potential_savings: Dict[str, Any] = field(default_factory=dict)


class CodeAnalyzer:
    """代码分析器"""

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.python_files: List[Path] = []
        self.import_graph: Dict[str, Set[str]] = defaultdict(set)
        self.function_hashes: Dict[str, List[Tuple[str, int, str]]] = defaultdict(list)
        self.class_hashes: Dict[str, List[Tuple[str, int, str]]] = defaultdict(list)

        # 排除的目录和文件
        self.exclude_dirs = {'.git', '__pycache__', '.pytest_cache', 'venv', '.env', 'node_modules'}
        self.exclude_files = {'__init__.py'}  # 某些情况下可能为空但仍然需要

    def scan_project(self):
        """扫描项目文件"""
        logger.info(f"📁 扫描项目: {self.project_root}")

        self.python_files = []
        for file_path in self.project_root.rglob("*.py"):
            # 跳过排除的目录
            if any(excluded in file_path.parts for excluded in self.exclude_dirs):
                continue
            self.python_files.append(file_path)

        logger.info(f"找到 {len(self.python_files)} 个Python文件")

    def parse_file(self, file_path: Path) -> Tuple[ast.AST, str]:
        """解析Python文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content, filename=str(file_path))
            return tree, content
        except Exception as e:
            logger.warning(f"解析文件失败 {file_path}: {e}")
            return None, ""

    def extract_imports(self, tree: ast.AST, file_path: Path) -> Set[str]:
        """提取导入信息"""
        imports = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module)

        return imports

    def extract_functions_and_classes(self, tree: ast.AST, content: str, file_path: Path):
        """提取函数和类定义"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_code = ast.get_source_segment(content, node)
                if func_code:
                    func_hash = hashlib.md5(func_code.encode()).hexdigest()
                    self.function_hashes[func_hash].append((str(file_path), node.lineno, func_code))

            elif isinstance(node, ast.ClassDef):
                class_code = ast.get_source_segment(content, node)
                if class_code:
                    class_hash = hashlib.md5(class_code.encode()).hexdigest()
                    self.class_hashes[class_hash].append((str(file_path), node.lineno, class_code))

    def build_import_graph(self):
        """构建导入依赖图"""
        logger.info("🔗 构建导入依赖图...")

        for file_path in self.python_files:
            tree, content = self.parse_file(file_path)
            if tree:
                imports = self.extract_imports(tree, file_path)
                self.import_graph[str(file_path)] = imports
                self.extract_functions_and_classes(tree, content, file_path)

    def find_duplicate_functions(self) -> List[DuplicateCode]:
        """查找重复函数"""
        duplicates = []

        for func_hash, locations in self.function_hashes.items():
            if len(locations) > 1:
                duplicate = DuplicateCode(
                    files=[loc[0] for loc in locations],
                    lines=[(loc[1], loc[1] + loc[2].count('\n')) for loc in locations],
                    code=locations[0][2],
                    similarity=1.0,  # 完全匹配
                    type="function"
                )
                duplicates.append(duplicate)

        logger.info(f"找到 {len(duplicates)} 个重复函数")
        return duplicates

    def find_duplicate_classes(self) -> List[DuplicateCode]:
        """查找重复类"""
        duplicates = []

        for class_hash, locations in self.class_hashes.items():
            if len(locations) > 1:
                duplicate = DuplicateCode(
                    files=[loc[0] for loc in locations],
                    lines=[(loc[1], loc[1] + loc[2].count('\n')) for loc in locations],
                    code=locations[0][2],
                    similarity=1.0,
                    type="class"
                )
                duplicates.append(duplicate)

        logger.info(f"找到 {len(duplicates)} 个重复类")
        return duplicates

    def find_unused_files(self) -> List[UnusedFile]:
        """查找未使用的文件"""
        logger.info("🔍 查找未使用文件...")

        # 获取所有被导入的模块
        imported_modules = set()
        for imports in self.import_graph.values():
            imported_modules.update(imports)

        # 转换为文件路径格式
        imported_files = set()
        for module in imported_modules:
            # 简单的模块名到文件路径转换
            module_parts = module.split('.')
            for file_path in self.python_files:
                if any(part in str(file_path) for part in module_parts):
                    imported_files.add(str(file_path))

        unused_files = []
        for file_path in self.python_files:
            file_str = str(file_path)

            # 跳过主程序和配置文件
            if any(name in file_str for name in
                   ['main.py', 'settings.py', 'config.py', '__init__.py']):
                continue

            # 检查是否被导入或引用
            if file_str not in imported_files:
                # 进一步检查是否在代码中被字符串引用
                is_referenced = False
                for other_file in self.python_files:
                    if other_file == file_path:
                        continue

                    try:
                        with open(other_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if file_path.stem in content:
                                is_referenced = True
                                break
                    except Exception:
                        continue

                if not is_referenced:
                    stat = os.stat(file_path)
                    unused_files.append(UnusedFile(
                        file_path=file_str,
                        reason="未被导入或引用",
                        size=stat.st_size,
                        last_modified=stat.st_mtime
                    ))

        logger.info(f"找到 {len(unused_files)} 个可能未使用的文件")
        return unused_files

    def find_code_issues(self) -> List[CodeIssue]:
        """查找代码问题"""
        logger.info("🐛 查找代码问题...")

        issues = []

        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                for i, line in enumerate(lines, 1):
                    line_stripped = line.strip()

                    # 检查长行
                    if len(line) > 120:
                        issues.append(CodeIssue(
                            file_path=str(file_path),
                            line_number=i,
                            issue_type="long_line",
                            description=f"行过长 ({len(line)} 字符)",
                            severity="low"
                        ))

                    # 检查TODO/FIXME
                    if any(
                        keyword in line_stripped.upper() for keyword in ['TODO', 'FIXME', 'XXX']):
                        issues.append(CodeIssue(
                            file_path=str(file_path),
                            line_number=i,
                            issue_type="todo",
                            description="未完成的TODO/FIXME",
                            severity="medium"
                        ))

                    # 检查重复的装饰器模式
                    if '@' in line and any(
                        pattern in line for pattern in ['cached', 'retry', 'method_cache']):
                        # 简单检查是否有重复的装饰器模式
                        if i > 1 and '@' in lines[i - 2] and any(
                            pattern in lines[i - 2] for pattern in ['cached', 'retry']):
                            issues.append(CodeIssue(
                                file_path=str(file_path),
                                line_number=i,
                                issue_type="duplicate_decorator",
                                description="可能存在重复的装饰器模式",
                                severity="medium"
                            ))

            except Exception as e:
                logger.warning(f"检查文件问题失败 {file_path}: {e}")

        logger.info(f"找到 {len(issues)} 个代码问题")
        return issues


class CodeCleanupTool:
    """代码清理工具"""

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.analyzer = CodeAnalyzer(project_root)

    def analyze_project(self) -> CleanupReport:
        """分析项目"""
        logger.info("🔍 开始项目分析...")

        # 扫描项目
        self.analyzer.scan_project()

        # 构建依赖图
        self.analyzer.build_import_graph()

        # 查找问题
        duplicate_functions = self.analyzer.find_duplicate_functions()
        duplicate_classes = self.analyzer.find_duplicate_classes()
        unused_files = self.analyzer.find_unused_files()
        code_issues = self.analyzer.find_code_issues()

        # 统计信息
        total_lines = 0
        duplicate_lines = 0

        for file_path in self.analyzer.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = len(f.readlines())
                    total_lines += lines
            except Exception:
                continue

        for dup in duplicate_functions + duplicate_classes:
            duplicate_lines += sum(end - start + 1 for start, end in dup.lines)

        # 生成报告
        report = CleanupReport(
            duplicate_codes=duplicate_functions + duplicate_classes,
            unused_files=unused_files,
            code_issues=code_issues,
            total_files_scanned=len(self.analyzer.python_files),
            total_lines_scanned=total_lines,
            duplicate_lines=duplicate_lines,
            potential_savings={
                "duplicate_code_lines": duplicate_lines,
                "unused_files_size": sum(f.size for f in unused_files),
                "unused_files_count": len(unused_files)
            }
        )

        logger.info("✅ 项目分析完成")
        return report

    def generate_cleanup_script(self, report: CleanupReport, output_file: Path):
        """生成清理脚本"""
        logger.info(f"📝 生成清理脚本: {output_file}")

        script_content = f"""#!/usr/bin/env python3
# 自动生成的代码清理脚本
# 生成时间: {__import__('datetime').datetime.now()}

import os
import shutil
from pathlib import Path

def backup_file(file_path):
    \"\"\"备份文件\"\"\"
    backup_path = str(file_path) + '.backup'
    shutil.copy2(file_path, backup_path)
    print(f"已备份: {{file_path}} -> {{backup_path}}")

def remove_unused_files():
    \"\"\"移除未使用的文件\"\"\"
    unused_files = [
"""

        for unused_file in report.unused_files:
            script_content += f'        "{unused_file.file_path}",\n'

        script_content += """    ]

    for file_path in unused_files:
        if os.path.exists(file_path):
            print(f"移除未使用文件: {file_path}")
            # 取消注释下面的行来实际删除文件
            # backup_file(file_path)
            # os.remove(file_path)

def show_duplicate_code():
    \"\"\"显示重复代码\"\"\"
    duplicates = [
"""

        for i, dup in enumerate(report.duplicate_codes):
            script_content += f"""        {{
            "id": {i},
            "type": "{dup.type}",
            "files": {dup.files},
            "lines": {dup.lines}
        }},
"""

        script_content += """    ]

    for dup in duplicates:
        print(f"重复{dup['type']}: {dup['files']}")
        print(f"行数: {dup['lines']}")
        print("-" * 50)

if __name__ == "__main__":
    print("🧹 代码清理脚本")
    print("="*50)

    print("\\n📊 分析报告:")
    print(f"扫描文件: {report.total_files_scanned}")
    print(f"扫描行数: {report.total_lines_scanned}")
    print(f"重复代码行数: {report.duplicate_lines}")
    print(f"未使用文件: {len(report.unused_files)}")
    print(f"代码问题: {len(report.code_issues)}")

    print("\\n🔍 重复代码:")
    show_duplicate_code()

    print("\\n🗑️  未使用文件:")
    remove_unused_files()

    print("\\n⚠️  注意: 请仔细检查后再执行实际的文件删除操作！")
"""

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(script_content)

        # 设置执行权限
        output_file.chmod(0o755)

        logger.info(f"清理脚本已生成: {output_file}")

    def generate_report(self, report: CleanupReport, output_file: Path):
        """生成详细报告"""
        logger.info(f"📄 生成分析报告: {output_file}")

        report_content = f"""# 代码清理分析报告

生成时间: {__import__('datetime').datetime.now()}
项目路径: {self.project_root}

## 📊 总体统计

- 扫描文件数: {report.total_files_scanned}
- 扫描行数: {report.total_lines_scanned:,}
- 重复代码行数: {report.duplicate_lines:,}
- 未使用文件数: {len(report.unused_files)}
- 代码问题数: {len(report.code_issues)}

## 🔄 重复代码

找到 {len(report.duplicate_codes)} 处重复代码：

"""

        for i, dup in enumerate(report.duplicate_codes, 1):
            report_content += f"""### 重复代码 #{i}

- 类型: {dup.type}
- 相似度: {dup.similarity:.1%}
- 涉及文件:
"""
            for file_path, (start, end) in zip(dup.files, dup.lines):
                report_content += f"  - `{file_path}` (行 {start}-{end})\n"

            report_content += f"""
```python
{dup.code[:200]}{'...' if len(dup.code) > 200 else ''}
```

"""

        report_content += f"""## 🗑️ 未使用文件

找到 {len(report.unused_files)} 个可能未使用的文件：

"""

        for unused in sorted(report.unused_files, key=lambda x: x.size, reverse=True):
            size_kb = unused.size / 1024
            report_content += f"- `{unused.file_path}` ({size_kb:.1f} KB) - {unused.reason}\n"

        report_content += f"""
## 🐛 代码问题

找到 {len(report.code_issues)} 个代码问题：

"""

        issue_groups = defaultdict(list)
        for issue in report.code_issues:
            issue_groups[issue.issue_type].append(issue)

        for issue_type, issues in issue_groups.items():
            report_content += f"""### {issue_type.replace('_', ' ').title()}

"""
            for issue in issues[:10]:  # 只显示前10个
                report_content += f"- `{issue.file_path}:{issue.line_number}` - {issue.description}\n"

            if len(issues) > 10:
                report_content += f"- ... 还有 {len(issues) - 10} 个类似问题\n"

        report_content += f"""
## 💡 优化建议

### 重复代码优化
1. 将重复的函数提取到工具模块中
2. 创建基类来消除重复的类定义
3. 使用装饰器模式统一重复的功能

### 文件清理
1. 删除未使用的文件（请先确认）
2. 合并功能相似的小文件
3. 重新组织目录结构

### 代码质量
1. 修复长行问题，提高可读性
2. 处理TODO/FIXME标记
3. 统一代码风格和模式

## 📈 预期收益

- 减少代码行数: ~{report.duplicate_lines:,} 行
- 减少文件数: ~{len(report.unused_files)} 个
- 节省磁盘空间: ~{report.potential_savings.get('unused_files_size', 0) / 1024:.1f} KB
"""

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_content)

        logger.info(f"分析报告已生成: {output_file}")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="代码清理和分析工具")
    parser.add_argument("project_path", help="项目根目录路径")
    parser.add_argument("--output-dir", default="cleanup_results", help="输出目录")
    parser.add_argument("--generate-script", action="store_true", help="生成清理脚本")

    args = parser.parse_args()

    project_path = Path(args.project_path)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    # 创建清理工具
    cleanup_tool = CodeCleanupTool(project_path)

    # 分析项目
    report = cleanup_tool.analyze_project()

    # 生成报告
    report_file = output_dir / "cleanup_report.md"
    cleanup_tool.generate_report(report, report_file)

    # 生成清理脚本
    if args.generate_script:
        script_file = output_dir / "cleanup_script.py"
        cleanup_tool.generate_cleanup_script(report, script_file)

    print(f"""
🎉 分析完成！

📊 统计结果:
- 扫描文件: {report.total_files_scanned}
- 重复代码: {len(report.duplicate_codes)} 处
- 未使用文件: {len(report.unused_files)} 个
- 代码问题: {len(report.code_issues)} 个

📁 输出文件:
- 详细报告: {report_file}
{f"- 清理脚本: {output_dir / 'cleanup_script.py'}" if args.generate_script else ""}

💡 建议: 请仔细检查报告后再执行任何文件删除操作。
    """)


if __name__ == "__main__":
    main()
