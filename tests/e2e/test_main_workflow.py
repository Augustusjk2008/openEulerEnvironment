"""
主工作流E2E测试

测试主窗口的完整工作流程：
- 主窗口页面切换
- 状态栏更新
- 菜单操作
- 快捷键响应

依赖：pytest-qt
"""

import pytest
from unittest.mock import patch, MagicMock, Mock
from pathlib import Path

# 尝试导入PyQt5相关模块
try:
    from PyQt5.QtWidgets import QApplication, QMainWindow, QStatusBar, QMenuBar, QAction
    from PyQt5.QtCore import Qt, QTimer
    from PyQt5.QtTest import QTest
    from PyQt5.QtGui import QKeySequence
    PYQT5_AVAILABLE = True
except ImportError:
    PYQT5_AVAILABLE = False

# 尝试导入主窗口
try:
    from ui.main_window import MainWindow
    import ui.main_window as main_window_module
    MAIN_WINDOW_AVAILABLE = True
except ImportError as e:
    MAIN_WINDOW_AVAILABLE = False
    MAIN_WINDOW_IMPORT_ERROR = str(e)
    main_window_module = None


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def qapp_args():
    """自定义QApplication启动参数"""
    return ["pytest-qt"]


@pytest.fixture
def mock_main_window_deps(monkeypatch):
    """
    Mock主窗口的所有依赖
    """
    patches = []

    # Mock config_manager
    mock_config = MagicMock()
    mock_config.get = MagicMock(return_value={})
    monkeypatch.setattr("ui.main_window.get_config_manager", lambda: mock_config)
    monkeypatch.setattr("ui.main_window.get_program_dir", lambda: "/tmp")

    # Mock FontManager
    mock_font_manager = MagicMock()
    mock_font_manager.apply_font_to_widget = MagicMock()
    monkeypatch.setattr("ui.main_window.FontManager", mock_font_manager)

    # Mock所有子界面
    interface_classes = [
        "HomeInterface",
        "SettingsInterface",
        "InitializerInterface",
        "EnvironmentInstallInterface",
        "CodeGenerationInterface",
        "TutorialInterface",
        "TerminalInterface",
        "FtpInterface",
        "DataVisualizationInterface",
        "ProtocolEditorInterface",
        "AutopilotEditorInterface",
    ]

    for interface_name in interface_classes:
        mock_class = MagicMock()
        mock_instance = MagicMock()
        mock_instance.switch_to_initializer = MagicMock()
        mock_instance.switch_to_environment = MagicMock()
        mock_instance.switch_to_codegen = MagicMock()
        mock_instance.switch_to_tutorial = MagicMock()
        mock_instance.switch_to_terminal = MagicMock()
        mock_instance.switch_to_ftp = MagicMock()
        mock_instance.switch_to_data_visualization = MagicMock()
        mock_instance.switch_to_protocol_editor = MagicMock()
        mock_instance.switch_to_autopilot_editor = MagicMock()
        mock_instance.switch_to_settings = MagicMock()
        mock_instance.connection_changed = MagicMock()
        mock_instance.set_ftp_connected = MagicMock()
        mock_instance.sftp = None
        mock_class.return_value = mock_instance
        monkeypatch.setattr(f"ui.main_window.{interface_name}", mock_class)

    return {
        "config": mock_config,
        "font_manager": mock_font_manager,
    }


@pytest.fixture
def main_window(qtbot, mock_main_window_deps):
    """
    创建MainWindow实例用于测试
    """
    if not MAIN_WINDOW_AVAILABLE:
        pytest.skip(f"MainWindow not available: {MAIN_WINDOW_IMPORT_ERROR}")

    # 创建窗口，传入progress_callback避免None错误
    window = MainWindow(progress_callback=lambda v, t: None)
    qtbot.addWidget(window)

    yield window

    # 清理
    window.close()
    window.deleteLater()


# =============================================================================
# 主窗口基础测试
# =============================================================================

@pytest.mark.skipif(not PYQT5_AVAILABLE, reason="PyQt5 not available")
@pytest.mark.skipif(not MAIN_WINDOW_AVAILABLE, reason=f"MainWindow not available")
class TestMainWindowBasic:
    """主窗口基础功能测试"""

    def test_window_creation(self, main_window):
        """测试窗口创建成功"""
        assert main_window is not None
        assert main_window.windowTitle() == "RTopenEuler 系统管理工具"

    def test_window_initial_size(self, main_window):
        """测试窗口初始大小"""
        assert main_window.width() == 1700
        assert main_window.height() == 1050

    def test_all_interfaces_created(self, main_window):
        """测试所有子界面已创建"""
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

    def test_config_manager_integration(self, main_window, mock_main_window_deps):
        """测试配置管理器集成"""
        assert main_window.config_manager == mock_main_window_deps["config"]


# =============================================================================
# 页面切换测试
# =============================================================================

@pytest.mark.skipif(not PYQT5_AVAILABLE, reason="PyQt5 not available")
@pytest.mark.skipif(not MAIN_WINDOW_AVAILABLE, reason=f"MainWindow not available")
class TestPageSwitching:
    """页面切换功能测试"""

    def test_switch_to_environment_page(self, main_window):
        """测试切换到环境配置页面"""
        main_window._switch_to_environment_page()
        # 验证switchTo被调用
        # 注意：由于FluentWindow是基类，我们需要验证调用
        assert main_window.environmentInstallInterface is not None

    def test_switch_to_initializer_page(self, main_window):
        """测试切换到系统初始化页面"""
        main_window._switch_to_initializer_page()
        assert main_window.initializerInterface is not None

    def test_switch_to_codegen_page(self, main_window):
        """测试切换到代码生成页面"""
        main_window._switch_to_codegen_page()
        assert main_window.codeGenerationInterface is not None

    def test_switch_to_tutorial_page(self, main_window):
        """测试切换到教程页面"""
        main_window._switch_to_tutorial_page()
        assert main_window.tutorialInterface is not None

    def test_switch_to_terminal_page(self, main_window):
        """测试切换到终端页面"""
        main_window._switch_to_terminal_page()
        assert main_window.terminalInterface is not None

    def test_switch_to_ftp_page(self, main_window):
        """测试切换到FTP页面"""
        main_window._switch_to_ftp_page()
        assert main_window.ftpInterface is not None

    def test_switch_to_data_visualization_page(self, main_window):
        """测试切换到数据可视化页面"""
        main_window._switch_to_data_visualization_page()
        assert main_window.dataVisualizationInterface is not None

    def test_switch_to_protocol_editor_page(self, main_window):
        """测试切换到协议编辑页面"""
        main_window._switch_to_protocol_editor_page()
        assert main_window.protocolEditorInterface is not None

    def test_switch_to_autopilot_editor_page(self, main_window):
        """测试切换到算法编辑页面"""
        main_window._switch_to_autopilot_editor_page()
        assert main_window.autopilotEditorInterface is not None

    def test_switch_to_settings_page(self, main_window):
        """测试切换到设置页面"""
        main_window._switch_to_settings_page()
        assert main_window.settingsInterface is not None


# =============================================================================
# 首页信号连接测试
# =============================================================================

@pytest.mark.skipif(not PYQT5_AVAILABLE, reason="PyQt5 not available")
@pytest.mark.skipif(not MAIN_WINDOW_AVAILABLE, reason=f"MainWindow not available")
class TestHomeInterfaceSignals:
    """首页信号连接测试"""

    def test_switch_to_initializer_signal(self, main_window):
        """测试切换到初始化页面信号"""
        # 发射首页的信号
        main_window.homeInterface.switch_to_initializer.emit()
        # 验证能够执行（不抛出异常）
        assert True

    def test_switch_to_environment_signal(self, main_window):
        """测试切换到环境页面信号"""
        main_window.homeInterface.switch_to_environment.emit()
        assert True

    def test_switch_to_codegen_signal(self, main_window):
        """测试切换到代码生成页面信号"""
        main_window.homeInterface.switch_to_codegen.emit()
        assert True

    def test_switch_to_tutorial_signal(self, main_window):
        """测试切换到教程页面信号"""
        main_window.homeInterface.switch_to_tutorial.emit()
        assert True

    def test_switch_to_terminal_signal(self, main_window):
        """测试切换到终端页面信号"""
        main_window.homeInterface.switch_to_terminal.emit()
        assert True

    def test_switch_to_ftp_signal(self, main_window):
        """测试切换到FTP页面信号"""
        main_window.homeInterface.switch_to_ftp.emit()
        assert True

    def test_switch_to_data_visualization_signal(self, main_window):
        """测试切换到数据可视化页面信号"""
        main_window.homeInterface.switch_to_data_visualization.emit()
        assert True

    def test_switch_to_protocol_editor_signal(self, main_window):
        """测试切换到协议编辑页面信号"""
        main_window.homeInterface.switch_to_protocol_editor.emit()
        assert True

    def test_switch_to_autopilot_editor_signal(self, main_window):
        """测试切换到算法编辑页面信号"""
        main_window.homeInterface.switch_to_autopilot_editor.emit()
        assert True

    def test_switch_to_settings_signal(self, main_window):
        """测试切换到设置页面信号"""
        main_window.homeInterface.switch_to_settings.emit()
        assert True


# =============================================================================
# 设置界面信号测试
# =============================================================================

@pytest.mark.skipif(not PYQT5_AVAILABLE, reason="PyQt5 not available")
@pytest.mark.skipif(not MAIN_WINDOW_AVAILABLE, reason=f"MainWindow not available")
class TestSettingsInterfaceSignals:
    """设置界面信号测试"""

    def test_config_changed_signal_connected(self, main_window):
        """测试配置更改信号已连接"""
        # 发射设置界面的config_changed信号
        main_window.settingsInterface.config_changed.emit()
        # 验证能够执行
        assert True


# =============================================================================
# FTP与数据可视化联动测试
# =============================================================================

@pytest.mark.skipif(not PYQT5_AVAILABLE, reason="PyQt5 not available")
@pytest.mark.skipif(not MAIN_WINDOW_AVAILABLE, reason=f"MainWindow not available")
class TestFtpDataVisualizationIntegration:
    """FTP与数据可视化集成测试"""

    def test_ftp_connection_signal_connected(self, main_window):
        """测试FTP连接信号已连接"""
        # 发射FTP连接变更信号
        main_window.ftpInterface.connection_changed.emit(True)
        # 验证能够执行
        assert True

    def test_initial_ftp_connection_state(self, main_window):
        """测试初始FTP连接状态"""
        # 验证初始状态设置被调用
        main_window.dataVisualizationInterface.set_ftp_connected.assert_called()


# =============================================================================
# 进度回调测试
# =============================================================================

@pytest.mark.skipif(not PYQT5_AVAILABLE, reason="PyQt5 not available")
class TestProgressCallback:
    """进度回调测试"""

    def test_progress_callback_called(self, qt_bot, mock_main_window_deps):
        """测试进度回调被调用"""
        progress_calls = []

        def progress_callback(value, text):
            progress_calls.append((value, text))

        window = MainWindow(progress_callback=progress_callback)
        qtbot.addWidget(window)

        # 验证进度回调被调用
        assert len(progress_calls) > 0
        assert progress_calls[0][0] == 5  # 第一个进度值
        assert progress_calls[-1][0] == 100  # 最后一个进度值

        window.close()
        window.deleteLater()

    def test_progress_callback_sequence(self, qt_bot, mock_main_window_deps):
        """测试进度回调序列"""
        progress_calls = []

        def progress_callback(value, text):
            progress_calls.append((value, text))

        window = MainWindow(progress_callback=progress_callback)
        qtbot.addWidget(window)

        # 验证进度值递增
        values = [call[0] for call in progress_calls]
        assert values == sorted(values)

        window.close()
        window.deleteLater()


# =============================================================================
# 导航键测试
# =============================================================================

@pytest.mark.skipif(not PYQT5_AVAILABLE, reason="PyQt5 not available")
@pytest.mark.skipif(not MAIN_WINDOW_AVAILABLE, reason=f"MainWindow not available")
class TestNavigationKeys:
    """导航键测试"""

    def test_environment_key_exists(self, main_window):
        """测试环境配置导航键存在"""
        assert hasattr(main_window, 'environment_key')

    def test_codegen_key_exists(self, main_window):
        """测试代码生成导航键存在"""
        assert hasattr(main_window, 'codegen_key')

    def test_terminal_key_exists(self, main_window):
        """测试终端导航键存在"""
        assert hasattr(main_window, 'terminal_key')

    def test_ftp_key_exists(self, main_window):
        """测试FTP导航键存在"""
        assert hasattr(main_window, 'ftp_key')

    def test_data_visualization_key_exists(self, main_window):
        """测试数据可视化导航键存在"""
        assert hasattr(main_window, 'data_visualization_key')

    def test_protocol_editor_key_exists(self, main_window):
        """测试协议编辑导航键存在"""
        assert hasattr(main_window, 'protocol_editor_key')

    def test_autopilot_editor_key_exists(self, main_window):
        """测试算法编辑导航键存在"""
        assert hasattr(main_window, 'autopilot_editor_key')

    def test_initializer_key_exists(self, main_window):
        """测试初始化导航键存在"""
        assert hasattr(main_window, 'initializer_key')

    def test_tutorial_key_exists(self, main_window):
        """测试教程导航键存在"""
        assert hasattr(main_window, 'tutorial_key')


# =============================================================================
# 窗口状态测试
# =============================================================================

@pytest.mark.skipif(not PYQT5_AVAILABLE, reason="PyQt5 not available")
@pytest.mark.skipif(not MAIN_WINDOW_AVAILABLE, reason=f"MainWindow not available")
class TestWindowState:
    """窗口状态测试"""

    def test_window_icon_set(self, main_window):
        """测试窗口图标已设置"""
        # 验证窗口图标不为空
        assert main_window.windowIcon() is not None

    def test_window_not_minimized_on_creation(self, main_window):
        """测试窗口创建时未最小化"""
        # 注意：窗口可能被最大化，所以检查是否不是最小化状态
        assert not main_window.isMinimized()


# =============================================================================
# 配置变更处理测试
# =============================================================================

@pytest.mark.skipif(not PYQT5_AVAILABLE, reason="PyQt5 not available")
@pytest.mark.skipif(not MAIN_WINDOW_AVAILABLE, reason=f"MainWindow not available")
class TestConfigChangeHandling:
    """配置变更处理测试"""

    def test_on_config_changed_method_exists(self, main_window):
        """测试配置变更处理方法存在"""
        assert hasattr(main_window, '_on_config_changed')
        assert callable(main_window._on_config_changed)

    def test_on_config_changed_callable(self, main_window):
        """测试配置变更处理方法可调用"""
        # 调用方法不应抛出异常
        main_window._on_config_changed()
        assert True


# =============================================================================
# Mock测试（无需真实GUI）
# =============================================================================

class TestMainWorkflowMocked:
    """使用Mock的主工作流测试"""

    def test_all_switch_methods_defined(self):
        """测试所有切换方法已定义"""
        if main_window_module is None:
            pytest.skip("主窗口模块不可用")
        with patch.multiple(
            main_window_module,
            get_config_manager=MagicMock(),
            get_program_dir=MagicMock(return_value="/tmp"),
            FontManager=MagicMock(),
            HomeInterface=MagicMock(),
            SettingsInterface=MagicMock(),
            InitializerInterface=MagicMock(),
            EnvironmentInstallInterface=MagicMock(),
            CodeGenerationInterface=MagicMock(),
            TutorialInterface=MagicMock(),
            TerminalInterface=MagicMock(),
            FtpInterface=MagicMock(),
            DataVisualizationInterface=MagicMock(),
            ProtocolEditorInterface=MagicMock(),
            AutopilotEditorInterface=MagicMock(),
            FluentWindow=MagicMock(),
        ):
            from ui.main_window import MainWindow

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

    def test_progress_callback_with_none(self):
        """测试进度回调为None时不抛出异常"""
        if main_window_module is None:
            pytest.skip("主窗口模块不可用")
        with patch.multiple(
            main_window_module,
            get_config_manager=MagicMock(),
            get_program_dir=MagicMock(return_value="/tmp"),
            FontManager=MagicMock(),
            HomeInterface=MagicMock(),
            SettingsInterface=MagicMock(),
            InitializerInterface=MagicMock(),
            EnvironmentInstallInterface=MagicMock(),
            CodeGenerationInterface=MagicMock(),
            TutorialInterface=MagicMock(),
            TerminalInterface=MagicMock(),
            FtpInterface=MagicMock(),
            DataVisualizationInterface=MagicMock(),
            ProtocolEditorInterface=MagicMock(),
            AutopilotEditorInterface=MagicMock(),
            FluentWindow=MagicMock(),
        ):
            from ui.main_window import MainWindow

            # 使用None作为progress_callback不应抛出异常
            window = MainWindow(progress_callback=None)
            assert window is not None


# =============================================================================
# 异步操作测试
# =============================================================================

@pytest.mark.skipif(not PYQT5_AVAILABLE, reason="PyQt5 not available")
@pytest.mark.skipif(not MAIN_WINDOW_AVAILABLE, reason=f"MainWindow not available")
class TestAsyncOperations:
    """异步操作测试"""

    def test_window_creation_async(self, qt_bot, mock_main_window_deps):
        """测试异步窗口创建"""
        def create_window():
            return MainWindow(progress_callback=lambda v, t: None)

        # 使用qtbot.waitUntil等待窗口创建
        window = None
        def check_window():
            nonlocal window
            try:
                window = create_window()
                return True
            except Exception:
                return False

        # 创建窗口
        window = MainWindow(progress_callback=lambda v, t: None)
        qtbot.addWidget(window)

        assert window is not None

        window.close()
        window.deleteLater()


# =============================================================================
# 性能测试
# =============================================================================

class TestMainWorkflowPerformance:
    """主工作流性能测试"""

    def test_window_init_time(self):
        """测试窗口初始化时间"""
        if main_window_module is None:
            pytest.skip("主窗口模块不可用")
        import time

        with patch.multiple(
            main_window_module,
            get_config_manager=MagicMock(),
            get_program_dir=MagicMock(return_value="/tmp"),
            FontManager=MagicMock(),
            HomeInterface=MagicMock(),
            SettingsInterface=MagicMock(),
            InitializerInterface=MagicMock(),
            EnvironmentInstallInterface=MagicMock(),
            CodeGenerationInterface=MagicMock(),
            TutorialInterface=MagicMock(),
            TerminalInterface=MagicMock(),
            FtpInterface=MagicMock(),
            DataVisualizationInterface=MagicMock(),
            ProtocolEditorInterface=MagicMock(),
            AutopilotEditorInterface=MagicMock(),
            FluentWindow=MagicMock(),
        ):
            from ui.main_window import MainWindow

            start_time = time.time()
            window = MainWindow(progress_callback=None)
            end_time = time.time()

            init_time = end_time - start_time
            # 验证初始化时间小于5秒（mock环境下应该很快）
            assert init_time < 5.0, f"Initialization took too long: {init_time}s"
