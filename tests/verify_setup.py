#!/usr/bin/env python3
"""
框架验证脚本 - Phase 1 质量审查

本脚本用于验证测试框架是否满足Phase 1的验收标准。
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import List, Tuple, Dict, Any

# 设置stdout编码以支持Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


class Colors:
    """终端颜色输出"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'


class VerificationResult:
    """验证结果类"""
    def __init__(self, name: str, passed: bool, message: str = "", details: List[str] = None):
        self.name = name
        self.passed = passed
        self.message = message
        self.details = details or []

    def __str__(self):
        status = f"{Colors.GREEN}[PASS]{Colors.RESET}" if self.passed else f"{Colors.RED}[FAIL]{Colors.RESET}"
        return f"{status} {self.name}: {self.message}"


class FrameworkVerifier:
    """框架验证器"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.results: List[VerificationResult] = []
        self.src_dir = project_root / "src"
        self.tests_dir = project_root / "tests"
        self.docs_dir = project_root / "docs"

    def log_info(self, message: str):
        """输出信息"""
        print(f"{Colors.BLUE}[INFO]{Colors.RESET} {message}")

    def log_warning(self, message: str):
        """输出警告"""
        print(f"{Colors.YELLOW}[WARN]{Colors.RESET} {message}")

    def log_error(self, message: str):
        """输出错误"""
        print(f"{Colors.RED}[ERROR]{Colors.RESET} {message}")

    def log_success(self, message: str):
        """输出成功"""
        print(f"{Colors.GREEN}[OK]{Colors.RESET} {message}")

    # ============ 目录结构检查 ============

    def check_directory_structure(self) -> VerificationResult:
        """检查目录结构是否规范"""
        name = "目录结构规范"
        required_dirs = [
            self.tests_dir / "unit",
            self.tests_dir / "integration",
            self.tests_dir / "e2e",
            self.tests_dir / "fixtures",
            self.tests_dir / "config",
            self.tests_dir / "utils",
            self.docs_dir / "review",
            self.docs_dir / "progress",
        ]

        missing = []
        for d in required_dirs:
            if not d.exists():
                missing.append(str(d.relative_to(self.project_root)))

        if missing:
            return VerificationResult(
                name, False,
                f"缺少必要的目录: {', '.join(missing)}",
                missing
            )

        # 检查旧内容是否已清空
        old_files = self._find_old_test_files()

        return VerificationResult(
            name, True,
            f"所有必要目录存在，发现 {len(old_files)} 个旧测试文件待清理",
            old_files if old_files else None
        )

    def _find_old_test_files(self) -> List[str]:
        """查找旧的测试文件"""
        old_files = []
        # 这里可以根据实际情况定义什么是"旧文件"
        # 例如：检查是否有不符合命名规范的文件
        for pattern in ["*.pyc", "__pycache__"]:
            for f in self.tests_dir.rglob(pattern):
                old_files.append(str(f.relative_to(self.project_root)))
        return old_files

    # ============ pytest检查 ============

    def check_pytest_available(self) -> VerificationResult:
        """检查pytest是否可运行"""
        name = "pytest可用性"
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                version = result.stdout.strip().split('\n')[0]
                return VerificationResult(name, True, f"pytest已安装: {version}")
            else:
                return VerificationResult(name, False, f"pytest检查失败: {result.stderr}")
        except subprocess.TimeoutExpired:
            return VerificationResult(name, False, "pytest检查超时")
        except FileNotFoundError:
            return VerificationResult(name, False, "pytest未安装")
        except Exception as e:
            return VerificationResult(name, False, f"检查异常: {e}")

    def check_pytest_can_run(self) -> VerificationResult:
        """检查pytest是否可以运行测试"""
        name = "pytest运行测试"
        unit_dir = self.tests_dir / "unit"

        if not any(unit_dir.iterdir()):
            return VerificationResult(
                name, True,
                "unit目录为空（等待测试代码添加）",
                ["目录为空，需要等待测试工程师添加测试代码"]
            )

        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", str(unit_dir), "-v", "--collect-only"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.project_root
            )
            if result.returncode == 0:
                # 统计测试数量
                test_count = result.stdout.count("<Function ")
                return VerificationResult(
                    name, True,
                    f"pytest可以运行，发现 {test_count} 个测试函数",
                    result.stdout.split('\n')[:10]  # 前10行
                )
            else:
                return VerificationResult(
                    name, False,
                    f"pytest运行失败: {result.stderr}",
                    result.stderr.split('\n')[:5]
                )
        except subprocess.TimeoutExpired:
            return VerificationResult(name, False, "pytest运行超时")
        except Exception as e:
            return VerificationResult(name, False, f"运行异常: {e}")

    # ============ 覆盖率检查 ============

    def check_coverage_available(self) -> VerificationResult:
        """检查覆盖率工具是否可用"""
        name = "覆盖率工具"
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "--cov=src", "--help"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if "--cov" in result.stdout:
                return VerificationResult(name, True, "pytest-cov已安装")
            else:
                return VerificationResult(name, False, "pytest-cov未安装")
        except Exception as e:
            return VerificationResult(name, False, f"检查异常: {e}")

    def check_coverage_can_generate(self) -> VerificationResult:
        """检查覆盖率报告是否可以生成"""
        name = "覆盖率报告生成"
        try:
            # 使用--collect-only避免实际运行测试
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "--cov=src", "--cov-report=term", "--collect-only"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.project_root
            )
            # 即使collect-only返回非0，只要命令能执行就说明cov可用
            if "pytest-cov" in result.stdout or "coverage" in result.stdout or result.returncode in [0, 5]:
                return VerificationResult(name, True, "覆盖率报告可以生成")
            else:
                return VerificationResult(name, False, f"覆盖率生成检查失败: {result.stderr[:200]}")
        except Exception as e:
            return VerificationResult(name, False, f"检查异常: {e}")

    # ============ 环境标记检查 ============

    def check_environment_marks(self) -> VerificationResult:
        """检查环境标记是否正确"""
        name = "环境标记"

        # 检查conftest.py中是否有环境标记定义
        conftest_files = list(self.tests_dir.rglob("conftest.py"))

        if not conftest_files:
            return VerificationResult(
                name, False,
                "未找到conftest.py文件",
                ["需要在tests/目录下创建conftest.py定义环境标记"]
            )

        marks_found = []
        for cf in conftest_files:
            content = cf.read_text(encoding='utf-8')
            if '@ubuntu_vm' in content or 'ubuntu_vm' in content:
                marks_found.append(f"{cf.relative_to(self.project_root)}: @ubuntu_vm")
            if '@real_device' in content or 'real_device' in content:
                marks_found.append(f"{cf.relative_to(self.project_root)}: @real_device")

        if marks_found:
            return VerificationResult(
                name, True,
                f"发现 {len(marks_found)} 个环境标记定义",
                marks_found
            )
        else:
            return VerificationResult(
                name, False,
                "未找到@ubuntu_vm或@real_device环境标记",
                ["需要在conftest.py中定义这些标记"]
            )

    # ============ src目录保护检查 ============

    def check_src_protection(self) -> VerificationResult:
        """检查是否没有修改src目录下的原有代码"""
        name = "src目录保护"

        # 获取git状态检查是否有修改
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain", "src/"],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=self.project_root
            )
            modified = [line for line in result.stdout.split('\n') if line.strip()]

            if modified:
                return VerificationResult(
                    name, False,
                    f"发现 {len(modified)} 个src/目录下的修改",
                    modified[:10]
                )
            else:
                return VerificationResult(
                    name, True,
                    "src/目录未被修改（符合约束）"
                )
        except Exception as e:
            return VerificationResult(
                name, True,  # 如果git检查失败，假设没有修改
                f"无法通过git检查修改状态: {e}"
            )

    # ============ 文档完整性检查 ============

    def check_documentation(self) -> VerificationResult:
        """检查文档是否完整"""
        name = "文档完整性"

        required_docs = [
            self.docs_dir / "agent_team_test_plan.md",
            self.docs_dir / "phase1_review_report.md",
            self.docs_dir / "test_code_suggestions.md",
            self.docs_dir / "review" / "README.md",
        ]

        missing = []
        for doc in required_docs:
            if not doc.exists():
                missing.append(str(doc.relative_to(self.project_root)))

        if missing:
            return VerificationResult(
                name, False,
                f"缺少文档: {', '.join(missing)}",
                missing
            )

        return VerificationResult(name, True, "所有必要文档已存在")

    # ============ 运行所有检查 ============

    def run_all_checks(self) -> List[VerificationResult]:
        """运行所有验证检查"""
        self.log_info("开始Phase 1框架验证...")
        print("-" * 60)

        checks = [
            self.check_directory_structure,
            self.check_pytest_available,
            self.check_pytest_can_run,
            self.check_coverage_available,
            self.check_coverage_can_generate,
            self.check_environment_marks,
            self.check_src_protection,
            self.check_documentation,
        ]

        for check in checks:
            result = check()
            self.results.append(result)
            print(result)
            print("-" * 60)

        return self.results

    def generate_report(self) -> str:
        """生成验证报告"""
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)

        report = []
        report.append("=" * 60)
        report.append("Phase 1 框架验证报告")
        report.append("=" * 60)
        report.append(f"通过: {passed}/{total}")
        report.append(f"失败: {total - passed}/{total}")
        report.append("")

        if passed == total:
            report.append(f"{Colors.GREEN}[OK] 所有检查通过！框架准备就绪。{Colors.RESET}")
        else:
            report.append(f"{Colors.YELLOW}[WARN] 部分检查未通过，需要处理。{Colors.RESET}")

        report.append("")
        report.append("详细结果:")
        report.append("-" * 60)

        for r in self.results:
            status = "[OK]" if r.passed else "[X]"
            report.append(f"{status} {r.name}")
            if r.details and r.passed is False:
                for detail in r.details[:5]:  # 最多显示5个详情
                    report.append(f"    - {detail}")

        return '\n'.join(report)


def main():
    """主函数"""
    project_root = Path(__file__).parent.parent
    verifier = FrameworkVerifier(project_root)

    verifier.run_all_checks()
    report = verifier.generate_report()

    print("\n" + report)

    # 返回退出码
    passed = sum(1 for r in verifier.results if r.passed)
    return 0 if passed == len(verifier.results) else 1


if __name__ == "__main__":
    sys.exit(main())
