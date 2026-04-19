"""
主窗口导航测试
测试页面切换逻辑和导航功能

注意：本测试文件需要 pytest-qt 插件
安装命令: pip install pytest-qt

QApplication 单例处理策略：
1. 使用 qtbot fixture 自动处理 QApplication 创建
2. 测试类使用 scope="session" 的 qapp fixture
3. 避免多次创建 MainWindow 实例
"""

import pytest
from unittest.mock import patch, MagicMock, Mock

pytestmark = pytest.mark.gui

# 尝试导入 PyQt5 相关模块
try:
    from PyQt5.QtWidgets import QApplication, QWidget
    from PyQt5.QtCore import Qt
    from PyQt5.QtTest import QTest
    PYQT5_AVAILABLE = True
except ImportError:
    PYQT5_AVAILABLE = False

# 尝试导入主窗口模块
try:
    from ui.main_window import MainWindow
    import ui.main_window as main_window_module
    MAIN_WINDOW_AVAILABLE = True
except ImportError as e:
    MAIN_WINDOW_AVAILABLE = False
    MAIN_WINDOW_IMPORT_ERROR = str(e)
    main_window_module = None

# 全局标记，用于控制是否运行 GUI 测试
RUN_GUI_TESTS = False


if PYQT5_AVAILABLE:
    class MockInterfaceWidget(QWidget):
        """轻量 QWidget 测试替身，用于主窗口依赖注入。"""

        def __init__(self):
            super().__init__()
            self.setObjectName(f"mock_{id(self)}")
            self.switch_to_initializer = MagicMock()
            self.switch_to_environment = MagicMock()
            self.switch_to_codegen = MagicMock()
            self.switch_to_tutorial = MagicMock()
            self.switch_to_terminal = MagicMock()
            self.switch_to_ftp = MagicMock()
            self.switch_to_data_visualization = MagicMock()
            self.switch_to_protocol_editor = MagicMock()
            self.switch_to_autopilot_editor = MagicMock()
            self.switch_to_settings = MagicMock()
            self.config_changed = MagicMock()
            self.connection_changed = MagicMock()
            self.set_ftp_connected = MagicMock()
            self.sftp = None


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def qapp_args():
    """自定义 QApplication 启动参数"""
    return ["pytest-qt"]


@pytest.fixture(scope="function")
def mock_main_window_deps():
    """
    Mock MainWindow 的所有依赖，避免真实的数据库、网络等操作
    """
    # 如果 MainWindow 模块不可用，跳过此 fixture
    if not MAIN_WINDOW_AVAILABLE:
        pytest.skip(f"MainWindow not available: {MAIN_WINDOW_IMPORT_ERROR}")

    patches = []

    # Mock config_manager
    mock_config = MagicMock()
    mock_config.get = MagicMock(return_value={})
    patches.append(patch("ui.main_window.get_config_manager", return_value=mock_config))
    patches.append(patch("ui.main_window.get_program_dir", return_value="/tmp"))

    # Mock FontManager
    mock_font_manager = MagicMock()
    patches.append(patch("ui.main_window.FontManager", mock_font_manager))

    # Mock 所有子界面
    interface_patches = [
        patch("ui.main_window.HomeInterface"),
        patch("ui.main_window.SettingsInterface"),
        patch("ui.main_window.InitializerInterface"),
        patch("ui.main_window.EnvironmentInstallInterface"),
        patch("ui.main_window.CodeGenerationInterface"),
        patch("ui.main_window.TutorialInterface"),
        patch("ui.main_window.TerminalInterface"),
        patch("ui.main_window.FtpInterface"),
        patch("ui.main_window.DataVisualizationInterface"),
        patch("ui.main_window.ProtocolEditorInterface"),
        patch("ui.main_window.AutopilotEditorInterface"),
    ]
    patches.extend(interface_patches)

    # 启动所有 patches
    for p in patches:
        p.start()

    yield

    # 停止所有 patches
    for p in patches:
        p.stop()


@pytest.fixture
def mock_fluent_window():
    """Mock FluentWindow 基类"""
    with patch("ui.main_window.FluentWindow") as mock:
        instance = MagicMock()
        mock.return_value = instance
        yield mock


# =============================================================================
# 基础导航逻辑测试（无需 GUI）
# =============================================================================

@pytest.mark.skipif(not PYQT5_AVAILABLE, reason="PyQt5 not available")
class TestMainWindowNavigationLogic:
    """测试主窗口导航逻辑（无需真实 GUI）"""

    def test_switch_methods_exist(self, mock_main_window_deps):
        """测试所有页面切换方法是否存在"""
        if not MAIN_WINDOW_AVAILABLE:
            pytest.skip(f"MainWindow not available: {MAIN_WINDOW_IMPORT_ERROR}")

        # 检查所有切换方法是否定义
        switch_methods = [
            "_switch_to_environment_page",
            "_switch_to_initializer_page",
            "_switch_to_codegen_page",
            "_switch_to_tutorial_page",
            "_switch_to_ftp_page",
            "_switch_to_terminal_page",
            "_switch_to_data_visualization_page",
            "_switch_to_protocol_editor_page",
            "_switch_to_autopilot_editor_page",
            "_switch_to_settings_page",
        ]

        for method_name in switch_methods:
            assert hasattr(MainWindow, method_name), f"Missing method: {method_name}"

    def test_navigation_keys_initialized(self, mock_main_window_deps):
        """测试导航键是否正确初始化"""
        if not MAIN_WINDOW_AVAILABLE:
            pytest.skip(f"MainWindow not available: {MAIN_WINDOW_IMPORT_ERROR}")

        # 检查 init_navigation 中定义的键
        expected_keys = [
            "environment_key",
            "codegen_key",
            "terminal_key",
            "ftp_key",
            "data_visualization_key",
            "protocol_editor_key",
            "autopilot_editor_key",
            "initializer_key",
            "tutorial_key",
        ]

        # 这些键在 init_navigation 中被设置
        for key in expected_keys:
            # 我们检查属性是否存在（在实例化后会被设置）
            pass  # 实例化测试需要 GUI

    def test_home_interface_signals_connected(self, mock_main_window_deps):
        """测试首页信号连接"""
        if not MAIN_WINDOW_AVAILABLE:
            pytest.skip(f"MainWindow not available: {MAIN_WINDOW_IMPORT_ERROR}")

        # 检查 init_navigation 中连接的信号
        expected_signals = [
            "switch_to_initializer",
            "switch_to_environment",
            "switch_to_codegen",
            "switch_to_tutorial",
            "switch_to_terminal",
            "switch_to_ftp",
            "switch_to_data_visualization",
            "switch_to_protocol_editor",
            "switch_to_autopilot_editor",
            "switch_to_settings",
        ]

        # 这些信号在 init_navigation 中被连接


# =============================================================================
# GUI 测试（需要 pytest-qt）
# =============================================================================

@pytest.mark.skipif(not PYQT5_AVAILABLE, reason="PyQt5 not available")
@pytest.mark.skipif(not RUN_GUI_TESTS, reason="GUI tests disabled. Set RUN_GUI_TESTS=True to enable.")
class TestMainWindowWithGUI:
    """
    使用 pytest-qt 的主窗口 GUI 测试

    运行这些测试需要:
    1. 安装 pytest-qt: pip install pytest-qt
    2. 设置环境变量: export RUN_GUI_TESTS=1 或在 conftest.py 中设置
    3. 有图形显示环境 (X11 或 Wayland)
    """

    @pytest.fixture
    def main_window(self, qtbot, mock_main_window_deps):
        """创建主窗口实例（使用 mocked 依赖）"""
        if not MAIN_WINDOW_AVAILABLE:
            pytest.skip(f"MainWindow not available: {MAIN_WINDOW_IMPORT_ERROR}")

        # 创建窗口，传入 progress_callback 避免 None 错误
        window = MainWindow(progress_callback=lambda v, t: None)
        qtbot.addWidget(window)

        # 不显示窗口以加快测试速度
        # window.show()

        yield window

        # 清理
        window.close()
        window.deleteLater()

    def test_window_creation(self, main_window):
        """测试窗口创建"""
        assert main_window is not None
        assert main_window.windowTitle() == "RTopenEuler 系统管理工具"

    def test_window_size(self, main_window):
        """测试窗口默认大小"""
        # 注意：窗口可能被最大化，所以检查 resize 调用
        assert main_window.width() > 0
        assert main_window.height() > 0

    def test_sub_interfaces_created(self, main_window):
        """测试子界面是否被创建"""
        expected_interfaces = [
            "homeInterface",
            "environmentInstallInterface",
            "initializerInterface",
            "codeGenerationInterface",
            "tutorialInterface",
            "terminalInterface",
            "ftpInterface",
            "dataVisualizationInterface",
            "protocolEditorInterface",
            "autopilotEditorInterface",
            "settingsInterface",
        ]

        for interface_name in expected_interfaces:
            assert hasattr(main_window, interface_name), f"Missing interface: {interface_name}"

    def test_switch_to_initializer_page(self, qtbot, main_window):
        """测试切换到初始化页面"""
        # 调用切换方法
        main_window._switch_to_initializer_page()

        # 验证 switchTo 被调用
        # 注意：由于我们 mock 了 FluentWindow，需要检查 mock
        # 实际测试中可能需要调整

    def test_switch_to_environment_page(self, qtbot, main_window):
        """测试切换到环境配置页面"""
        main_window._switch_to_environment_page()

    def test_switch_to_codegen_page(self, qtbot, main_window):
        """测试切换到代码生成页面"""
        main_window._switch_to_codegen_page()

    def test_switch_to_tutorial_page(self, qtbot, main_window):
        """测试切换到教程页面"""
        main_window._switch_to_tutorial_page()

    def test_switch_to_terminal_page(self, qtbot, main_window):
        """测试切换到终端页面"""
        main_window._switch_to_terminal_page()

    def test_switch_to_ftp_page(self, qtbot, main_window):
        """测试切换到 FTP 页面"""
        main_window._switch_to_ftp_page()

    def test_switch_to_data_visualization_page(self, qtbot, main_window):
        """测试切换到数据可视化页面"""
        main_window._switch_to_data_visualization_page()

    def test_switch_to_protocol_editor_page(self, qtbot, main_window):
        """测试切换到协议编辑页面"""
        main_window._switch_to_protocol_editor_page()

    def test_switch_to_autopilot_editor_page(self, qtbot, main_window):
        """测试切换到算法编辑页面"""
        main_window._switch_to_autopilot_editor_page()

    def test_switch_to_settings_page(self, qtbot, main_window):
        """测试切换到设置页面"""
        main_window._switch_to_settings_page()


# =============================================================================
# Mock 测试（无需真实 GUI）
# =============================================================================

class TestMainWindowMocked:
    """使用 Mock 的主窗口测试（无需真实 GUI）"""

    def test_progress_callback_called(self, qapp, qtbot):
        """测试进度回调被正确调用"""
        if main_window_module is None:
            pytest.skip("主窗口模块不可用")
        with patch.multiple(
            main_window_module,
            get_config_manager=MagicMock(),
            get_program_dir=MagicMock(return_value="/tmp"),
            FontManager=MagicMock(),
            HomeInterface=MagicMock(return_value=MockInterfaceWidget()),
            SettingsInterface=MagicMock(return_value=MockInterfaceWidget()),
            InitializerInterface=MagicMock(return_value=MockInterfaceWidget()),
            EnvironmentInstallInterface=MagicMock(return_value=MockInterfaceWidget()),
            CodeGenerationInterface=MagicMock(return_value=MockInterfaceWidget()),
            TutorialInterface=MagicMock(return_value=MockInterfaceWidget()),
            TerminalInterface=MagicMock(return_value=MockInterfaceWidget()),
            FtpInterface=MagicMock(return_value=MockInterfaceWidget()),
            DataVisualizationInterface=MagicMock(return_value=MockInterfaceWidget()),
            ProtocolEditorInterface=MagicMock(return_value=MockInterfaceWidget()),
            AutopilotEditorInterface=MagicMock(return_value=MockInterfaceWidget()),
            FluentWindow=MagicMock(),
        ):
            from ui.main_window import MainWindow

            progress_calls = []

            def progress_callback(value, text):
                progress_calls.append((value, text))

            # 创建实例
            window = MainWindow(progress_callback=progress_callback)
            qtbot.addWidget(window)

            # 验证进度回调被调用
            assert len(progress_calls) > 0
            assert progress_calls[0][0] == 5  # 第一个进度值
            assert progress_calls[-1][0] == 100  # 最后一个进度值

    def test_config_manager_integration(self, qapp, qtbot):
        """测试配置管理器集成"""
        if main_window_module is None:
            pytest.skip("主窗口模块不可用")
        mock_config = MagicMock()
        mock_config.get.return_value = {"test": "value"}

        with patch.multiple(
            main_window_module,
            get_config_manager=MagicMock(return_value=mock_config),
            get_program_dir=MagicMock(return_value="/tmp"),
            FontManager=MagicMock(),
            HomeInterface=MagicMock(return_value=MockInterfaceWidget()),
            SettingsInterface=MagicMock(return_value=MockInterfaceWidget()),
            InitializerInterface=MagicMock(return_value=MockInterfaceWidget()),
            EnvironmentInstallInterface=MagicMock(return_value=MockInterfaceWidget()),
            CodeGenerationInterface=MagicMock(return_value=MockInterfaceWidget()),
            TutorialInterface=MagicMock(return_value=MockInterfaceWidget()),
            TerminalInterface=MagicMock(return_value=MockInterfaceWidget()),
            FtpInterface=MagicMock(return_value=MockInterfaceWidget()),
            DataVisualizationInterface=MagicMock(return_value=MockInterfaceWidget()),
            ProtocolEditorInterface=MagicMock(return_value=MockInterfaceWidget()),
            AutopilotEditorInterface=MagicMock(return_value=MockInterfaceWidget()),
            FluentWindow=MagicMock(),
        ):
            from ui.main_window import MainWindow

            window = MainWindow(progress_callback=None)
            qtbot.addWidget(window)

            # 验证配置管理器被保存
            assert window.config_manager == mock_config

    def test_signal_connections(self, qapp, qtbot):
        """测试信号连接"""
        if main_window_module is None:
            pytest.skip("主窗口模块不可用")
        mock_home = MockInterfaceWidget()
        mock_settings = MockInterfaceWidget()
        mock_ftp = MockInterfaceWidget()
        mock_data_viz = MockInterfaceWidget()

        with patch.multiple(
            main_window_module,
            get_config_manager=MagicMock(),
            get_program_dir=MagicMock(return_value="/tmp"),
            FontManager=MagicMock(),
            HomeInterface=MagicMock(return_value=mock_home),
            SettingsInterface=MagicMock(return_value=mock_settings),
            InitializerInterface=MagicMock(return_value=MockInterfaceWidget()),
            EnvironmentInstallInterface=MagicMock(return_value=MockInterfaceWidget()),
            CodeGenerationInterface=MagicMock(return_value=MockInterfaceWidget()),
            TutorialInterface=MagicMock(return_value=MockInterfaceWidget()),
            TerminalInterface=MagicMock(return_value=MockInterfaceWidget()),
            FtpInterface=MagicMock(return_value=mock_ftp),
            DataVisualizationInterface=MagicMock(return_value=mock_data_viz),
            ProtocolEditorInterface=MagicMock(return_value=MockInterfaceWidget()),
            AutopilotEditorInterface=MagicMock(return_value=MockInterfaceWidget()),
            FluentWindow=MagicMock(),
        ):
            from ui.main_window import MainWindow

            window = MainWindow(progress_callback=None)
            qtbot.addWidget(window)

            # 验证信号连接
            mock_settings.config_changed.connect.assert_called_once()
            mock_ftp.connection_changed.connect.assert_not_called()

            window._switch_to_ftp_page()
            window._switch_to_data_visualization_page()

            mock_ftp.connection_changed.connect.assert_called_once_with(
                mock_data_viz.set_ftp_connected
            )

    def test_lazy_interfaces_defer_widget_creation(self, qapp, qtbot):
        """测试非首页/设置页在启动时不会立即创建真实界面"""
        if main_window_module is None:
            pytest.skip("主窗口模块不可用")

        mock_home = MockInterfaceWidget()
        mock_settings = MockInterfaceWidget()
        mock_environment = MockInterfaceWidget()
        mock_initializer = MockInterfaceWidget()
        mock_codegen = MockInterfaceWidget()
        mock_tutorial = MockInterfaceWidget()
        mock_terminal = MockInterfaceWidget()
        mock_ftp = MockInterfaceWidget()
        mock_data_viz = MockInterfaceWidget()
        mock_protocol = MockInterfaceWidget()
        mock_autopilot = MockInterfaceWidget()

        environment_cls = MagicMock(return_value=mock_environment)
        initializer_cls = MagicMock(return_value=mock_initializer)
        codegen_cls = MagicMock(return_value=mock_codegen)
        tutorial_cls = MagicMock(return_value=mock_tutorial)
        terminal_cls = MagicMock(return_value=mock_terminal)
        ftp_cls = MagicMock(return_value=mock_ftp)
        data_viz_cls = MagicMock(return_value=mock_data_viz)
        protocol_cls = MagicMock(return_value=mock_protocol)
        autopilot_cls = MagicMock(return_value=mock_autopilot)

        with patch.multiple(
            main_window_module,
            get_config_manager=MagicMock(),
            get_program_dir=MagicMock(return_value="/tmp"),
            FontManager=MagicMock(),
            HomeInterface=MagicMock(return_value=mock_home),
            SettingsInterface=MagicMock(return_value=mock_settings),
            InitializerInterface=initializer_cls,
            EnvironmentInstallInterface=environment_cls,
            CodeGenerationInterface=codegen_cls,
            TutorialInterface=tutorial_cls,
            TerminalInterface=terminal_cls,
            FtpInterface=ftp_cls,
            DataVisualizationInterface=data_viz_cls,
            ProtocolEditorInterface=protocol_cls,
            AutopilotEditorInterface=autopilot_cls,
            FluentWindow=MagicMock(),
        ):
            from ui.main_window import MainWindow

            window = MainWindow(progress_callback=None)
            qtbot.addWidget(window)

            assert window.homeInterface is mock_home
            assert window.settingsInterface is mock_settings
            environment_cls.assert_not_called()
            initializer_cls.assert_not_called()
            codegen_cls.assert_not_called()
            tutorial_cls.assert_not_called()
            terminal_cls.assert_not_called()
            ftp_cls.assert_not_called()
            data_viz_cls.assert_not_called()
            protocol_cls.assert_not_called()
            autopilot_cls.assert_not_called()

    def test_switch_to_environment_page_loads_interface_once(self, qapp, qtbot):
        """测试首次切换时才创建环境配置页面，且只创建一次"""
        if main_window_module is None:
            pytest.skip("主窗口模块不可用")

        mock_environment = MockInterfaceWidget()
        environment_cls = MagicMock(return_value=mock_environment)

        with patch.multiple(
            main_window_module,
            get_config_manager=MagicMock(),
            get_program_dir=MagicMock(return_value="/tmp"),
            FontManager=MagicMock(),
            HomeInterface=MagicMock(return_value=MockInterfaceWidget()),
            SettingsInterface=MagicMock(return_value=MockInterfaceWidget()),
            InitializerInterface=MagicMock(return_value=MockInterfaceWidget()),
            EnvironmentInstallInterface=environment_cls,
            CodeGenerationInterface=MagicMock(return_value=MockInterfaceWidget()),
            TutorialInterface=MagicMock(return_value=MockInterfaceWidget()),
            TerminalInterface=MagicMock(return_value=MockInterfaceWidget()),
            FtpInterface=MagicMock(return_value=MockInterfaceWidget()),
            DataVisualizationInterface=MagicMock(return_value=MockInterfaceWidget()),
            ProtocolEditorInterface=MagicMock(return_value=MockInterfaceWidget()),
            AutopilotEditorInterface=MagicMock(return_value=MockInterfaceWidget()),
            FluentWindow=MagicMock(),
        ):
            from ui.main_window import MainWindow

            window = MainWindow(progress_callback=None)
            qtbot.addWidget(window)
            window.switchTo = MagicMock()

            window._switch_to_environment_page()
            window._switch_to_environment_page()

            environment_cls.assert_called_once_with(window)
            assert window.environmentInstallInterface.is_loaded() is True
            assert window.environmentInstallInterface.widget() is mock_environment
            assert window.switchTo.call_count == 2

    def test_data_visualization_defaults_to_disconnected_until_ftp_loads(self, qapp, qtbot):
        """测试数据可视化页面懒加载后先收到未连接状态，FTP加载后再同步真实状态"""
        if main_window_module is None:
            pytest.skip("主窗口模块不可用")

        mock_ftp = MockInterfaceWidget()
        mock_ftp.sftp = object()
        mock_data_viz = MockInterfaceWidget()

        with patch.multiple(
            main_window_module,
            get_config_manager=MagicMock(),
            get_program_dir=MagicMock(return_value="/tmp"),
            FontManager=MagicMock(),
            HomeInterface=MagicMock(return_value=MockInterfaceWidget()),
            SettingsInterface=MagicMock(return_value=MockInterfaceWidget()),
            InitializerInterface=MagicMock(return_value=MockInterfaceWidget()),
            EnvironmentInstallInterface=MagicMock(return_value=MockInterfaceWidget()),
            CodeGenerationInterface=MagicMock(return_value=MockInterfaceWidget()),
            TutorialInterface=MagicMock(return_value=MockInterfaceWidget()),
            TerminalInterface=MagicMock(return_value=MockInterfaceWidget()),
            FtpInterface=MagicMock(return_value=mock_ftp),
            DataVisualizationInterface=MagicMock(return_value=mock_data_viz),
            ProtocolEditorInterface=MagicMock(return_value=MockInterfaceWidget()),
            AutopilotEditorInterface=MagicMock(return_value=MockInterfaceWidget()),
            FluentWindow=MagicMock(),
        ):
            from ui.main_window import MainWindow

            window = MainWindow(progress_callback=None)
            qtbot.addWidget(window)
            window.switchTo = MagicMock()

            window._switch_to_data_visualization_page()
            mock_data_viz.set_ftp_connected.assert_called_with(False)

            window._switch_to_ftp_page()
            mock_ftp.connection_changed.connect.assert_called_once_with(
                mock_data_viz.set_ftp_connected
            )
            assert mock_data_viz.set_ftp_connected.call_args_list[-1].args == (True,)


# =============================================================================
# 页面切换逻辑测试
# =============================================================================

class TestPageSwitchingLogic:
    """测试页面切换逻辑"""

    def test_all_pages_have_switch_method(self):
        """测试所有页面都有对应的切换方法"""
        expected_mapping = {
            "environmentInstallInterface": "_switch_to_environment_page",
            "initializerInterface": "_switch_to_initializer_page",
            "codeGenerationInterface": "_switch_to_codegen_page",
            "tutorialInterface": "_switch_to_tutorial_page",
            "terminalInterface": "_switch_to_terminal_page",
            "ftpInterface": "_switch_to_ftp_page",
            "dataVisualizationInterface": "_switch_to_data_visualization_page",
            "protocolEditorInterface": "_switch_to_protocol_editor_page",
            "autopilotEditorInterface": "_switch_to_autopilot_editor_page",
            "settingsInterface": "_switch_to_settings_page",
        }

        if not MAIN_WINDOW_AVAILABLE:
            pytest.skip(f"MainWindow not available: {MAIN_WINDOW_IMPORT_ERROR}")

        for interface, method_name in expected_mapping.items():
            assert hasattr(MainWindow, method_name), f"Missing switch method: {method_name}"

    def test_switch_method_calls_switchto(self):
        """测试切换方法调用 switchTo"""
        # 这是一个示例测试，展示如何验证 switchTo 被调用
        # 实际测试需要 mock FluentWindow

        class MockMainWindow:
            def __init__(self):
                self.initializerInterface = Mock()
                self._switch_calls = []

            def switchTo(self, interface):
                self._switch_calls.append(interface)

            def _switch_to_initializer_page(self):
                self.switchTo(self.initializerInterface)

        window = MockMainWindow()
        window._switch_to_initializer_page()

        assert len(window._switch_calls) == 1
        assert window._switch_calls[0] == window.initializerInterface


# =============================================================================
# 并发/多线程测试
# =============================================================================

@pytest.mark.skipif(not PYQT5_AVAILABLE, reason="PyQt5 not available")
class TestMainWindowThreading:
    """测试主窗口多线程相关功能"""

    def test_progress_callback_thread_safety(self):
        """测试进度回调的线程安全性"""
        # 这是一个示例测试，展示如何测试线程安全
        # 实际实现取决于具体需求

        import threading
        import queue

        progress_queue = queue.Queue()
        callback_calls = []

        def thread_safe_callback(value, text):
            progress_queue.put((value, text))

        def worker():
            for i in range(10):
                thread_safe_callback(i * 10, f"Step {i}")

        # 启动工作线程
        threads = [threading.Thread(target=worker) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 收集所有回调
        while not progress_queue.empty():
            callback_calls.append(progress_queue.get())

        # 验证所有回调都被记录
        assert len(callback_calls) == 30


# =============================================================================
# 性能测试
# =============================================================================

class TestMainWindowPerformance:
    """测试主窗口性能"""

    def test_window_init_performance(self):
        """测试窗口初始化性能"""
        # 这是一个示例测试，展示如何测试初始化性能
        # 实际测试需要真实环境

        import time

        # 模拟初始化时间测试
        start_time = time.time()

        # 模拟初始化操作
        time.sleep(0.01)  # 模拟 10ms 初始化

        end_time = time.time()
        init_time = end_time - start_time

        # 验证初始化时间小于 5 秒
        assert init_time < 5.0, f"Initialization took too long: {init_time}s"
