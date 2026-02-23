# UI 测试策略文档

本文档描述了 RTopenEuler 项目的 UI 自动化测试策略，包括测试框架配置、最佳实践和常见问题解决方案。

## 目录

1. [测试框架概述](#测试框架概述)
2. [pytest-qt 配置](#pytest-qt-配置)
3. [QApplication 单例处理](#qapplication-单例处理)
4. [UI 测试最佳实践](#ui-测试最佳实践)
5. [图形界面依赖跳过机制](#图形界面依赖跳过机制)
6. [测试目录结构](#测试目录结构)
7. [运行测试](#运行测试)
8. [常见问题](#常见问题)

---

## 测试框架概述

本项目使用以下工具进行 UI 测试：

- **pytest**: Python 测试框架
- **pytest-qt**: PyQt5/PySide2 测试插件
- **QTest**: Qt 自带的测试工具（模拟点击、键盘输入等）

### 安装依赖

```bash
pip install pytest pytest-qt
```

### 可选依赖（用于 CI/CD）

```bash
# Linux 无头环境测试
sudo apt-get install xvfb
pip install pytest-xvfb
```

---

## pytest-qt 配置

### 基本配置 (pytest.ini)

```ini
[pytest]
qt_api = pyqt5
qt_no_exception_capture = 0
addopts = -v --tb=short
```

### 配置说明

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `qt_api` | 指定 Qt 绑定 (`pyqt5`, `pyside2`, `pyqt6`, `pyside6`) | 自动检测 |
| `qt_no_exception_capture` | 禁用异常捕获（调试用） | 0 |
| `qt_log_level_fail` | 失败的日志级别 | WARNING |

### 命令行选项

```bash
# 指定 Qt API
pytest --qt-api=pyqt5

# 禁用异常捕获
pytest --qt-no-exception-capture

# 显示 Qt 日志
pytest --qt-log
```

---

## QApplication 单例处理

### 问题背景

Qt 要求每个进程只能有一个 `QApplication` 实例。在测试中，如果不正确处理，会导致：

```
RuntimeError: Please destroy the QApplication singleton before creating a new QApplication instance.
```

### 解决方案

#### 1. 使用 qtbot fixture（推荐）

```python
def test_window(qtbot):
    """qtbot 会自动处理 QApplication"""
    window = MainWindow()
    qtbot.addWidget(window)
    # 测试代码...
```

#### 2. 使用 session 级别的 qapp fixture

```python
@pytest.fixture(scope="session")
def qapp():
    """自定义 QApplication"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
```

#### 3. 检查现有实例

```python
def get_or_create_qapp():
    """获取或创建 QApplication"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app
```

#### 4. 测试类级别的处理

```python
@pytest.mark.skipif(not PYQT5_AVAILABLE, reason="PyQt5 not available")
class TestMainWindow:
    @pytest.fixture(autouse=True)
    def setup(self, qtbot):
        """每个测试方法自动设置"""
        self.window = MainWindow()
        qtbot.addWidget(self.window)
        yield
        self.window.close()
        self.window.deleteLater()
```

### 清理策略

```python
@pytest.fixture
def main_window(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    yield window
    # 清理
    window.close()
    window.deleteLater()
    # 强制处理事件
    QApplication.processEvents()
```

---

## UI 测试最佳实践

### 1. Mock 外部依赖

```python
@pytest.fixture
def mock_deps():
    """Mock 所有外部依赖"""
    with patch("ui.main_window.get_config_manager") as mock_config, \
         patch("ui.main_window.FontManager") as mock_font:
        mock_config.return_value = MagicMock()
        yield
```

### 2. 避免真实网络/文件操作

```python
def test_without_network():
    """测试时禁用网络操作"""
    with patch("ui.ftp_interface.SFTPClient") as mock_sftp:
        mock_sftp.return_value.connect.return_value = True
        # 测试代码...
```

### 3. 使用 QTest 模拟用户操作

```python
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt

def test_button_click(qtbot, window):
    """模拟按钮点击"""
    button = window.findChild(QPushButton, "submitButton")
    qtbot.mouseClick(button, Qt.LeftButton)
    # 或者使用 QTest
    QTest.mouseClick(button, Qt.LeftButton)
```

### 4. 等待异步操作

```python
def test_async_operation(qtbot, window):
    """等待异步操作完成"""
    # 方法1: 使用 waitSignal
    with qtbot.waitSignal(window.operation_finished, timeout=5000):
        window.start_operation()

    # 方法2: 使用 waitUntil
    qtbot.waitUntil(lambda: window.status_label.text() == "完成", timeout=5000)

    # 方法3: 使用 wait
    qtbot.wait(1000)  # 等待 1 秒
```

### 5. 测试多线程

```python
def test_threading(qtbot, window):
    """测试多线程 UI 更新"""
    from PyQt5.QtCore import QThreadPool

    # 确保线程池任务完成
    QThreadPool.globalInstance().waitForDone(5000)

    # 处理所有事件
    QApplication.processEvents()
```

### 6. 避免界面卡顿

```python
# 不好的做法：阻塞主线程
def test_slow_operation_bad(window):
    window.run_long_task()  # 阻塞 10 秒
    assert window.result == "done"

# 好的做法：使用信号或回调
def test_slow_operation_good(qtbot, window):
    with qtbot.waitSignal(window.task_completed, timeout=15000):
        window.run_long_task_async()
```

---

## 图形界面依赖跳过机制

### 环境检测

```python
import os

# 检测是否在 CI 环境
IN_CI = os.environ.get("CI", "false").lower() == "true"

# 检测是否有显示环境
HAS_DISPLAY = os.environ.get("DISPLAY") is not None

# 检测是否强制跳过 GUI 测试
SKIP_GUI = os.environ.get("SKIP_GUI_TESTS", "false").lower() == "true"
```

### 跳过标记

```python
# 1. 基于模块可用性跳过
pytest.importorskip("PyQt5", reason="PyQt5 not installed")

# 2. 基于环境变量跳过
@pytest.mark.skipif(IN_CI, reason="Skipping GUI tests in CI")
def test_gui_feature():
    pass

# 3. 基于显示环境跳过
@pytest.mark.skipif(not HAS_DISPLAY, reason="No display environment")
def test_visual_component():
    pass

# 4. 自定义标记
@pytest.mark.gui  # 自定义标记
def test_gui_only():
    pass
```

### 条件执行

```bash
# 只运行非 GUI 测试
pytest -m "not gui"

# 只运行 GUI 测试
pytest -m gui

# 跳过 GUI 测试
pytest --ignore=tests/unit/ui/
```

### conftest.py 配置

```python
# tests/conftest.py
import pytest

def pytest_addoption(parser):
    """添加自定义命令行选项"""
    parser.addoption(
        "--run-gui",
        action="store_true",
        default=False,
        help="Run GUI tests"
    )

def pytest_collection_modifyitems(config, items):
    """根据选项跳过 GUI 测试"""
    if not config.getoption("--run-gui"):
        skip_gui = pytest.mark.skip(reason="Need --run-gui option")
        for item in items:
            if "gui" in item.keywords:
                item.add_marker(skip_gui)
```

---

## 测试目录结构

```
tests/
├── conftest.py                    # 全局 fixture 配置
├── unit/
│   ├── __init__.py
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── test_style_helper.py   # 样式辅助类测试
│   │   └── test_main_window_navigation.py  # 主窗口导航测试
│   └── ...
├── integration/
│   └── ...
└── e2e/
    ├── __init__.py                # E2E 测试框架占位
    └── test_workflows.py          # 端到端工作流测试
```

---

## 运行测试

### 基本命令

```bash
# 运行所有测试
pytest

# 运行 UI 测试
pytest tests/unit/ui/

# 运行特定测试文件
pytest tests/unit/ui/test_main_window_navigation.py

# 运行特定测试方法
pytest tests/unit/ui/test_main_window_navigation.py::TestMainWindow::test_window_creation
```

### 带选项运行

```bash
# 显示详细输出
pytest -v

# 显示打印输出
pytest -s

# 失败时停止
pytest -x

# 生成覆盖率报告
pytest --cov=src/ui --cov-report=html

# 并行运行（需要 pytest-xdist）
pytest -n auto
```

### CI/CD 环境

```bash
# Linux 无头环境
xvfb-run pytest tests/unit/ui/

# 或使用 pytest-xvfb
pytest tests/unit/ui/
```

---

## 常见问题

### Q1: RuntimeError: Please destroy the QApplication...

**原因**: 尝试创建多个 QApplication 实例

**解决**:
```python
# 检查现有实例
app = QApplication.instance()
if app is None:
    app = QApplication([])
```

### Q2: 测试在 CI 环境失败

**原因**: CI 环境没有图形显示

**解决**:
```bash
# 使用 xvfb
xvfb-run pytest

# 或跳过 GUI 测试
pytest -m "not gui"
```

### Q3: 信号槽连接测试失败

**原因**: 信号在测试结束前未触发

**解决**:
```python
with qtbot.waitSignal(window.signal, timeout=5000):
    window.trigger_signal()
```

### Q4: 内存泄漏警告

**原因**: QWidget 未正确清理

**解决**:
```python
@pytest.fixture
def widget(qtbot):
    w = MyWidget()
    qtbot.addWidget(w)
    yield w
    w.close()
    w.deleteLater()
```

### Q5: 样式测试失败

**原因**: 平台差异导致样式不同

**解决**:
```python
@pytest.mark.skipif(sys.platform != "win32", reason="Windows only")
def test_windows_style():
    pass
```

---

## 参考资源

- [pytest-qt 文档](https://pytest-qt.readthedocs.io/)
- [Qt Test 文档](https://doc.qt.io/qt-5/qtest.html)
- [PyQt5 文档](https://www.riverbankcomputing.com/static/Docs/PyQt5/)
- [Fluent Widgets](https://github.com/zhiyiYo/PyQt-Fluent-Widgets)

---

## 更新日志

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-02-16 | 1.0 | 初始版本 |
