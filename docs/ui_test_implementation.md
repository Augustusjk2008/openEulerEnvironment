# UI测试实现文档

本文档详细说明了RTopenEuler项目的UI测试架构、实现策略和运行方式。

## 目录

- [测试架构](#测试架构)
- [Mock策略](#mock策略)
- [异步操作处理](#异步操作处理)
- [测试运行方式](#测试运行方式)
- [测试文件说明](#测试文件说明)
- [常见问题](#常见问题)

---

## 测试架构

### 1. 测试目录结构

```
tests/
├── conftest.py                    # 测试全局配置和Fixture
├── unit/
│   └── ui/
│       ├── test_login_interface.py        # 登录界面测试
│       ├── test_settings_interface.py     # 设置界面测试
│       └── test_main_window_navigation.py # 主窗口导航测试
├── e2e/
│   └── test_main_workflow.py              # 主工作流E2E测试
└── integration/
    └── ...                                 # 集成测试
```

### 2. 测试技术栈

- **测试框架**: pytest
- **Qt测试**: pytest-qt (提供qtbot fixture)
- **Mock工具**: unittest.mock
- **覆盖率**: pytest-cov

### 3. 测试分类

| 测试类型 | 位置 | 说明 |
|---------|------|------|
| 单元测试 | `tests/unit/ui/` | 测试单个UI组件 |
| E2E测试 | `tests/e2e/` | 测试完整工作流程 |
| 集成测试 | `tests/integration/` | 测试模块间集成 |

---

## Mock策略

### 1. QMessageBox Mock

**问题**: 测试时弹出QMessageBox会阻塞测试执行。

**解决方案**:

```python
@pytest.fixture
def mock_qt_messagebox(monkeypatch):
    """模拟QMessageBox，避免测试时弹出对话框"""
    mock_msgbox = MagicMock()
    mock_msgbox.Question = 4
    mock_msgbox.Yes = 16384
    mock_msgbox.No = 65536
    mock_msgbox.Ok = 1024
    mock_msgbox.Cancel = 4194304
    mock_msgbox.question.return_value = mock_msgbox.Yes  # 默认返回"是"

    monkeypatch.setattr(
        "PyQt5.QtWidgets.QMessageBox",
        mock_msgbox
    )
    return mock_msgbox
```

**使用示例**:

```python
def test_reset_to_default_confirmed(self, settings_interface, mock_qt_messagebox):
    """测试确认重置为默认值"""
    mock_qt_messagebox.question.return_value = mock_qt_messagebox.Yes

    settings_interface._reset_to_default()

    # 验证重置被调用
    mock_config.reset_to_default.assert_called_once()
```

### 2. QFileDialog Mock

**问题**: 文件对话框会阻塞测试并需要用户交互。

**解决方案**:

```python
@pytest.fixture
def mock_qt_filedialog(monkeypatch):
    """模拟QFileDialog，避免测试时弹出文件对话框"""
    mock_dialog = MagicMock()
    mock_dialog.getOpenFileName.return_value = ("", "")
    mock_dialog.getSaveFileName.return_value = ("", "")
    mock_dialog.getExistingDirectory.return_value = ""

    monkeypatch.setattr(
        "PyQt5.QtWidgets.QFileDialog",
        mock_dialog
    )
    return mock_dialog
```

**使用示例**:

```python
def test_browse_output_directory(self, settings_interface, mock_qt_filedialog):
    """测试浏览输出目录"""
    new_dir = r"D:\SelectedOutput"
    mock_qt_filedialog.getExistingDirectory.return_value = new_dir

    settings_interface._browse_output_dir()

    assert settings_interface.output_dir_edit.text() == new_dir
```

### 3. 配置管理器 Mock

```python
@pytest.fixture
def mock_config_manager(monkeypatch):
    """模拟配置管理器"""
    mock_config = MagicMock()
    mock_config.get = MagicMock(return_value="default_value")
    mock_config.set = MagicMock(return_value=True)
    mock_config.reset_to_default = MagicMock()

    monkeypatch.setattr(
        "ui.interfaces.settings_interface.get_config_manager",
        lambda: mock_config
    )
    return mock_config
```

### 4. 完整Mock Fixture示例

```python
@pytest.fixture
def mock_settings_deps(monkeypatch, tmp_path):
    """Mock设置界面的所有依赖"""
    # Mock ConfigManager
    mock_config = MagicMock()
    mock_config.get = MagicMock(side_effect=lambda key, default=None: default_config.get(key, default))
    mock_config.set = MagicMock(return_value=True)
    monkeypatch.setattr("ui.interfaces.settings_interface.get_config_manager", lambda: mock_config)

    # Mock FontManager
    mock_font = MagicMock()
    mock_font.get_font_size.return_value = 12
    monkeypatch.setattr("ui.interfaces.settings_interface.FontManager", mock_font)

    # Mock InfoBar
    mock_infobar = MagicMock()
    monkeypatch.setattr("ui.interfaces.settings_interface.InfoBar", mock_infobar)

    # Mock QFileDialog
    mock_dialog = MagicMock()
    monkeypatch.setattr("ui.interfaces.settings_interface.QFileDialog", mock_dialog)

    # Mock QMessageBox
    mock_msgbox = MagicMock()
    mock_msgbox.Yes = 16384
    mock_msgbox.question.return_value = mock_msgbox.Yes
    monkeypatch.setattr("ui.interfaces.settings_interface.QMessageBox", mock_msgbox)

    return {
        "config": mock_config,
        "infobar": mock_infobar,
        "dialog": mock_dialog,
        "msgbox": mock_msgbox,
    }
```

---

## 异步操作处理

### 1. 信号等待

使用`qtbot.waitSignal`等待异步信号:

```python
def test_save_emits_config_changed_signal(self, settings_interface, qtbot):
    """测试保存后发射配置更改信号"""
    with qtbot.waitSignal(settings_interface.config_changed, timeout=1000):
        settings_interface._save_settings()
```

### 2. 多信号等待

```python
def test_multiple_signals(self, qtbot):
    """测试多个信号"""
    with qtbot.waitSignals([self.signal1, self.signal2], timeout=2000):
        self.trigger_actions()
```

### 3. 回调等待

```python
def test_async_operation(self, qtbot):
    """测试异步操作"""
    def check_result():
        return self.operation_complete

    qtbot.waitUntil(check_result, timeout=5000)
```

### 4. QThread处理

```python
def test_thread_operation(self, qtbot):
    """测试线程操作"""
    thread = WorkerThread()
    thread.start()

    with qtbot.waitSignal(thread.finished, timeout=10000):
        pass

    assert thread.result is not None
```

### 5. 定时器处理

```python
def test_timer_based_operation(self, qtbot):
    """测试基于定时器的操作"""
    from PyQt5.QtCore import QTimer

    timer = QTimer()
    timer.setSingleShot(True)
    timer.start(100)

    with qtbot.waitSignal(timer.timeout, timeout=1000):
        pass
```

---

## 测试运行方式

### 1. 环境准备

在conda环境`pyqt5_env`中运行测试:

```bash
# 激活环境
conda activate pyqt5_env

# 安装依赖
pip install pytest pytest-qt pytest-cov
```

### 2. 运行所有UI测试

```bash
# 运行所有UI单元测试
pytest tests/unit/ui/ -v

# 运行E2E测试
pytest tests/e2e/ -v

# 运行所有测试
pytest tests/ -v
```

### 3. 运行特定测试文件

```bash
# 登录界面测试
pytest tests/unit/ui/test_login_interface.py -v

# 设置界面测试
pytest tests/unit/ui/test_settings_interface.py -v

# 主工作流E2E测试
pytest tests/e2e/test_main_workflow.py -v
```

### 4. 运行特定测试类或方法

```bash
# 运行特定测试类
pytest tests/unit/ui/test_login_interface.py::TestLoginFunctionality -v

# 运行特定测试方法
pytest tests/unit/ui/test_login_interface.py::TestLoginFunctionality::test_successful_login -v
```

### 5. 覆盖率测试

```bash
# 生成覆盖率报告
pytest tests/unit/ui/ --cov=src/ui --cov-report=html --cov-report=term

# 查看HTML报告
open tests/reports/htmlcov/index.html
```

### 6. 无头模式运行

在CI/CD环境或无显示器环境中:

```bash
# 设置环境变量
export QT_QPA_PLATFORM=offscreen

# 运行测试
pytest tests/unit/ui/ -v
```

Windows:
```powershell
$env:QT_QPA_PLATFORM="offscreen"
pytest tests/unit/ui/ -v
```

### 7. 调试模式

```bash
# 显示详细的测试输出
pytest tests/unit/ui/ -v -s

# 在第一个失败时停止
pytest tests/unit/ui/ -x

# 使用pdb调试失败的测试
pytest tests/unit/ui/ --pdb
```

---

## 测试文件说明

### 1. test_login_interface.py

测试登录界面的各项功能:

| 测试类 | 说明 |
|-------|------|
| `TestLoginInterfaceBasic` | 基础界面测试（窗口创建、元素存在性） |
| `TestLoginInputValidation` | 输入验证测试（空值、长度限制） |
| `TestLoginFunctionality` | 登录功能测试（成功/失败、信号） |
| `TestRegisterFunctionality` | 注册功能测试 |
| `TestHeroImageLabel` | HeroImageLabel组件测试 |

### 2. test_settings_interface.py

测试设置界面的各项功能:

| 测试类 | 说明 |
|-------|------|
| `TestSettingsInterfaceBasic` | 基础界面测试 |
| `TestSettingsLoading` | 设置加载测试 |
| `TestSettingsSaving` | 设置保存测试 |
| `TestSettingsReset` | 重置默认设置测试 |
| `TestDirectoryBrowsing` | 目录浏览测试 |
| `TestFontSettings` | 字体设置测试 |
| `TestSettingsSignals` | 信号测试 |

### 3. test_main_workflow.py

测试主窗口的完整工作流程:

| 测试类 | 说明 |
|-------|------|
| `TestMainWindowBasic` | 主窗口基础功能测试 |
| `TestPageSwitching` | 页面切换功能测试 |
| `TestHomeInterfaceSignals` | 首页信号连接测试 |
| `TestSettingsInterfaceSignals` | 设置界面信号测试 |
| `TestFtpDataVisualizationIntegration` | FTP与数据可视化集成测试 |
| `TestProgressCallback` | 进度回调测试 |
| `TestNavigationKeys` | 导航键测试 |

---

## 常见问题

### Q1: 测试时出现"QApplication already exists"错误

**原因**: 多次创建QApplication实例。

**解决**: 使用pytest-qt提供的`qapp` fixture，它会自动管理QApplication生命周期。

```python
# 正确
@pytest.fixture
def my_widget(qapp):  # 使用qapp fixture
    return MyWidget()

# 错误
def test_something():
    app = QApplication([])  # 不要手动创建
    ...
```

### Q2: 测试时弹出真实对话框

**原因**: Mock未正确设置或路径不正确。

**解决**: 确保Mock路径与被测代码中的导入路径一致。

```python
# 如果被测代码使用 from PyQt5.QtWidgets import QMessageBox
monkeypatch.setattr("PyQt5.QtWidgets.QMessageBox", mock_msgbox)

# 如果被测代码使用 from qfluentwidgets import InfoBar
# 需要Mock qfluentwidgets.InfoBar
```

### Q3: 信号测试超时

**原因**: 信号未发射或发射条件未满足。

**解决**: 检查信号连接和触发条件，增加超时时间。

```python
# 增加超时时间
with qtbot.waitSignal(self.signal, timeout=5000):
    self.trigger_action()
```

### Q4: 测试在CI环境中失败

**原因**: CI环境无显示器。

**解决**: 设置`QT_QPA_PLATFORM=offscreen`环境变量。

```yaml
# .github/workflows/test.yml
- name: Run UI tests
  env:
    QT_QPA_PLATFORM: offscreen
  run: pytest tests/unit/ui/ -v
```

### Q5: 测试覆盖率不准确

**原因**: Qt资源文件或自动生成的代码被计入。

**解决**: 配置`.coveragerc`排除特定文件。

```ini
[run]
source = src
omit =
    */__init__.py
    */resources_rc.py
    */ui_*.py
```

---

## 最佳实践

1. **使用Fixture管理资源**: 利用pytest的fixture机制管理测试资源和依赖。

2. **Mock外部依赖**: 始终Mock数据库、网络、文件系统等外部依赖。

3. **测试隔离**: 每个测试应该独立运行，不依赖其他测试的状态。

4. **有意义的命名**: 测试方法名应该清晰描述测试内容。

5. **使用qtbot**: 利用qtbot进行UI交互，它会自动处理事件循环。

6. **设置超时**: 为信号等待和异步操作设置合理的超时时间。

7. **清理资源**: 在fixture的清理阶段关闭窗口和释放资源。

---

## 参考资源

- [pytest-qt文档](https://pytest-qt.readthedocs.io/)
- [PyQt5测试指南](https://www.riverbankcomputing.com/static/Docs/PyQt5/)
- [Qt Test模块](https://doc.qt.io/qt-5/qtest.html)
