#!/usr/bin/env python3
"""
当前测试环境验证脚本。

该脚本服务于 `run_tests.ps1` 的第 4 步，只验证“当前测试是否可运行”：
- pytest 是否可用
- tests/ 入口是否可正常收集
- pytest-cov 是否可用，覆盖率报告是否可生成
- 环境标记是否存在

历史 Phase 1 文档、可选目录、以及开发态的 src/ 修改不会再被当作失败。
"""

import io
import re
import subprocess
import sys
from pathlib import Path
from typing import List

# 设置 stdout/stderr 编码以支持 Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


class Colors:
    """终端颜色输出。"""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"


class VerificationResult:
    """验证结果。"""

    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"

    def __init__(self, name: str, status: str, message: str = "", details: List[str] = None):
        self.name = name
        self.status = status
        self.message = message
        self.details = details or []

    @property
    def passed(self) -> bool:
        return self.status != self.FAIL

    @property
    def failed(self) -> bool:
        return self.status == self.FAIL

    @classmethod
    def ok(cls, name: str, message: str = "", details: List[str] = None):
        return cls(name, cls.PASS, message, details)

    @classmethod
    def warn(cls, name: str, message: str = "", details: List[str] = None):
        return cls(name, cls.WARN, message, details)

    @classmethod
    def fail(cls, name: str, message: str = "", details: List[str] = None):
        return cls(name, cls.FAIL, message, details)

    def __str__(self):
        if self.status == self.PASS:
            status = f"{Colors.GREEN}[PASS]{Colors.RESET}"
        elif self.status == self.WARN:
            status = f"{Colors.YELLOW}[WARN]{Colors.RESET}"
        else:
            status = f"{Colors.RED}[FAIL]{Colors.RESET}"
        return f"{status} {self.name}: {self.message}"


class FrameworkVerifier:
    """当前仓库测试环境验证器。"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.results: List[VerificationResult] = []
        self.src_dir = project_root / "src"
        self.tests_dir = project_root / "tests"
        self.docs_dir = project_root / "docs"
        self.pytest_ini = self.tests_dir / "pytest.ini"
        self.tests_target = str(self.tests_dir.relative_to(self.project_root))

    def log_info(self, message: str):
        """输出信息。"""
        print(f"{Colors.BLUE}[INFO]{Colors.RESET} {message}")

    def _run_command(self, args: List[str], timeout: int = 10):
        return subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=self.project_root,
        )

    def _run_pytest(self, pytest_args: List[str], timeout: int = 30):
        args = [sys.executable, "-m", "pytest"]
        if self.pytest_ini.exists():
            args.extend(["-c", str(self.pytest_ini)])
        args.extend(pytest_args)
        return self._run_command(args, timeout=timeout)

    @staticmethod
    def _combined_output(result: subprocess.CompletedProcess) -> str:
        return "\n".join(part for part in [result.stdout.strip(), result.stderr.strip()] if part)

    @staticmethod
    def _parse_collected_count(text: str) -> int:
        match = re.search(r"collected\s+(\d+)\s+items?", text)
        return int(match.group(1)) if match else 0

    # ============ 目录结构检查 ============

    def check_directory_structure(self) -> VerificationResult:
        """检查当前测试运行所需目录。"""
        name = "目录结构规范"
        required_dirs = [
            self.tests_dir / "unit",
            self.tests_dir / "integration",
            self.tests_dir / "e2e",
            self.tests_dir / "fixtures",
            self.tests_dir / "config",
            self.tests_dir / "utils",
        ]

        missing_required = [
            str(path.relative_to(self.project_root))
            for path in required_dirs
            if not path.exists()
        ]
        if missing_required:
            return VerificationResult.fail(
                name,
                f"缺少当前测试运行所需目录: {', '.join(missing_required)}",
                missing_required,
            )

        return VerificationResult.ok(name, "当前测试运行所需目录齐全")

    # ============ pytest 检查 ============

    def check_pytest_available(self) -> VerificationResult:
        """检查 pytest 是否可用。"""
        name = "pytest可用性"
        try:
            result = self._run_command([sys.executable, "-m", "pytest", "--version"], timeout=10)
        except subprocess.TimeoutExpired:
            return VerificationResult.fail(name, "pytest检查超时")
        except FileNotFoundError:
            return VerificationResult.fail(name, "pytest未安装")
        except Exception as exc:
            return VerificationResult.fail(name, f"检查异常: {exc}")

        if result.returncode != 0:
            return VerificationResult.fail(name, self._combined_output(result)[:200])

        version = result.stdout.strip().splitlines()[0]
        return VerificationResult.ok(name, f"pytest已安装: {version}")

    def check_pytest_can_run(self) -> VerificationResult:
        """检查 pytest 是否可以正常收集测试。"""
        name = "pytest运行测试"
        unit_target = str((self.tests_dir / "unit").relative_to(self.project_root))

        try:
            result = self._run_pytest([unit_target, "-v", "--collect-only"], timeout=60)
        except subprocess.TimeoutExpired:
            return VerificationResult.fail(name, "pytest收集测试超时")
        except Exception as exc:
            return VerificationResult.fail(name, f"运行异常: {exc}")

        output = self._combined_output(result)
        if result.returncode != 0:
            return VerificationResult.fail(name, f"pytest运行失败: {output[:200]}")

        collected = self._parse_collected_count(output)
        if collected == 0:
            return VerificationResult.warn(name, "pytest可运行，但未收集到测试")

        return VerificationResult.ok(name, f"pytest可以运行，发现 {collected} 个测试项")

    # ============ 覆盖率检查 ============

    def check_coverage_available(self) -> VerificationResult:
        """检查 pytest-cov 是否可用。"""
        name = "覆盖率工具"
        try:
            result = self._run_pytest([self.tests_target, "--cov=src", "--help"], timeout=20)
        except subprocess.TimeoutExpired:
            return VerificationResult.fail(name, "覆盖率工具检查超时")
        except Exception as exc:
            return VerificationResult.fail(name, f"检查异常: {exc}")

        if result.returncode != 0:
            return VerificationResult.fail(name, f"pytest-cov检查失败: {self._combined_output(result)[:200]}")

        if "--cov" not in result.stdout:
            return VerificationResult.fail(name, "pytest帮助中未发现 --cov 参数")

        return VerificationResult.ok(name, "pytest-cov已安装")

    def check_coverage_can_generate(self) -> VerificationResult:
        """检查覆盖率报告是否可以生成。"""
        name = "覆盖率报告生成"
        try:
            result = self._run_pytest(
                [self.tests_target, "--cov=src", "--cov-report=term", "--collect-only"],
                timeout=120,
            )
        except subprocess.TimeoutExpired:
            return VerificationResult.fail(name, "覆盖率生成检查超时")
        except Exception as exc:
            return VerificationResult.fail(name, f"检查异常: {exc}")

        output = self._combined_output(result)
        if "INTERNALERROR" in output:
            return VerificationResult.fail(name, f"覆盖率生成出现内部错误: {output[:200]}")

        if result.returncode not in (0, 5):
            return VerificationResult.fail(name, f"覆盖率生成检查失败: {output[:200]}")

        return VerificationResult.ok(name, "覆盖率报告可以生成")

    # ============ 环境标记检查 ============

    def check_environment_marks(self) -> VerificationResult:
        """检查环境标记是否存在。"""
        name = "环境标记"
        conftest_files = list(self.tests_dir.rglob("conftest.py"))

        if not conftest_files:
            return VerificationResult.fail(
                name,
                "未找到tests目录下的conftest.py文件",
                ["需要在tests/目录下提供conftest.py定义环境标记"],
            )

        marks_found = []
        for conftest_file in conftest_files:
            content = conftest_file.read_text(encoding="utf-8")
            if "@ubuntu_vm" in content or "ubuntu_vm" in content:
                marks_found.append(f"{conftest_file.relative_to(self.project_root)}: ubuntu_vm")
            if "@real_device" in content or "real_device" in content:
                marks_found.append(f"{conftest_file.relative_to(self.project_root)}: real_device")

        if not marks_found:
            return VerificationResult.fail(
                name,
                "未找到 ubuntu_vm 或 real_device 标记",
                ["需要在 tests/conftest.py 中定义这些标记"],
            )

        return VerificationResult.ok(name, f"发现 {len(marks_found)} 个环境标记定义", marks_found)

    # ============ 运行所有检查 ============

    def run_all_checks(self) -> List[VerificationResult]:
        """运行所有验证检查。"""
        self.log_info("开始当前测试环境验证...")
        print("-" * 60)

        checks = [
            self.check_directory_structure,
            self.check_pytest_available,
            self.check_pytest_can_run,
            self.check_coverage_available,
            self.check_coverage_can_generate,
            self.check_environment_marks,
        ]

        for check in checks:
            result = check()
            self.results.append(result)
            print(result)
            print("-" * 60)

        return self.results

    def generate_report(self) -> str:
        """生成验证报告。"""
        passed = sum(1 for result in self.results if result.status == VerificationResult.PASS)
        warned = sum(1 for result in self.results if result.status == VerificationResult.WARN)
        failed = sum(1 for result in self.results if result.status == VerificationResult.FAIL)

        report = [
            "=" * 60,
            "当前测试环境验证报告",
            "=" * 60,
            f"通过: {passed}",
            f"提示: {warned}",
            f"失败: {failed}",
            "",
        ]

        if failed == 0 and warned == 0:
            report.append(f"{Colors.GREEN}[OK] 所有检查通过，测试环境准备就绪。{Colors.RESET}")
        elif failed == 0:
            report.append(f"{Colors.GREEN}[OK] 关键检查通过；存在提示项，但不影响测试运行。{Colors.RESET}")
        else:
            report.append(f"{Colors.YELLOW}[WARN] 存在会影响测试运行的问题，需要处理。{Colors.RESET}")

        report.extend(["", "详细结果:", "-" * 60])

        markers = {
            VerificationResult.PASS: "[OK]",
            VerificationResult.WARN: "[!]",
            VerificationResult.FAIL: "[X]",
        }
        for result in self.results:
            report.append(f"{markers[result.status]} {result.name}")
            if result.details and result.status != VerificationResult.PASS:
                for detail in result.details[:5]:
                    report.append(f"    - {detail}")

        return "\n".join(report)


def main():
    """主函数。"""
    project_root = Path(__file__).parent.parent
    verifier = FrameworkVerifier(project_root)

    verifier.run_all_checks()
    report = verifier.generate_report()

    print("\n" + report)

    return 0 if not any(result.failed for result in verifier.results) else 1


if __name__ == "__main__":
    sys.exit(main())
