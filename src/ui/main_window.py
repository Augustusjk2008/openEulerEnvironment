import os
import warnings
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout
from PyQt5.QtGui import QIcon
from qfluentwidgets import FluentWindow, NavigationItemPosition, FluentIcon
from core.config_manager import get_config_manager, get_program_dir
from core.font_manager import FontManager

# 导入自定义界面
from ui.interfaces.home_interface import HomeInterface
from ui.interfaces.settings_interface import SettingsInterface
from ui.interfaces.initializer_interface import InitializerInterface
from ui.interfaces.environment_install_interface import EnvironmentInstallInterface
from ui.interfaces.code_generation_interface import CodeGenerationInterface
from ui.interfaces.tutorial_interface import TutorialInterface
from ui.interfaces.terminal_interface import TerminalInterface
from ui.interfaces.ftp_interface import FtpInterface
from ui.interfaces.data_visualization_interface import DataVisualizationInterface
from ui.interfaces.protocol_editor_interface import ProtocolEditorInterface
from ui.interfaces.autopilot_editor_interface import AutopilotEditorInterface

warnings.filterwarnings(
    "ignore",
    message="sipPyTypeDict\\(\\) is deprecated.*",
    category=DeprecationWarning
)


class _LazyInterfaceHost(QWidget):
    """导航先注册，真实页面在首次切换时再创建。"""

    def __init__(self, object_name, loader, on_loaded=None, parent=None):
        super().__init__(parent)
        self.setObjectName(object_name)
        self._loader = loader
        self._on_loaded = on_loaded
        self._widget = None
        self._loading = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

    def is_loaded(self):
        return self._widget is not None

    def widget(self):
        return self._widget

    def ensure_loaded(self):
        if self._widget is not None or self._loading:
            return self._widget

        self._loading = True
        try:
            widget = self._loader()
            self.layout().addWidget(widget)
            self._widget = widget
            if self._on_loaded:
                self._on_loaded(widget)
        finally:
            self._loading = False

        return self._widget

    def showEvent(self, event):
        self.ensure_loaded()
        super().showEvent(event)

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)

        widget = self.ensure_loaded()
        if widget is None:
            raise AttributeError(name)
        return getattr(widget, name)


class MainWindow(FluentWindow):
    def __init__(self, progress_callback=None):
        super().__init__()
        self._progress_callback = progress_callback
        self._ftp_data_visualization_connected = False

        # 加载配置
        self._emit_progress(5, "加载配置...")
        self.config_manager = get_config_manager()

        # 初始化界面
        self._emit_progress(12, "加载首页...")
        self.homeInterface = HomeInterface(self)
        self._emit_progress(22, "注册环境配置...")
        self.environmentInstallInterface = self._create_lazy_interface(
            "environmentInstallInterface",
            EnvironmentInstallInterface,
        )
        self._emit_progress(32, "注册系统初始化...")
        self.initializerInterface = self._create_lazy_interface(
            "initializerInterface",
            InitializerInterface,
        )
        self._emit_progress(42, "注册代码生成...")
        self.codeGenerationInterface = self._create_lazy_interface(
            "codeGenerationInterface",
            CodeGenerationInterface,
        )
        self._emit_progress(52, "注册教程文档...")
        self.tutorialInterface = self._create_lazy_interface(
            "tutorialInterface",
            TutorialInterface,
        )
        self._emit_progress(62, "注册远程终端...")
        self.terminalInterface = self._create_lazy_interface(
            "terminalInterface",
            TerminalInterface,
        )
        self._emit_progress(72, "注册 FTP 客户端...")
        self.ftpInterface = self._create_lazy_interface(
            "ftpInterface",
            FtpInterface,
            self._on_ftp_interface_loaded,
        )
        self._emit_progress(80, "注册数据可视化...")
        self.dataVisualizationInterface = self._create_lazy_interface(
            "dataVisualizationInterface",
            DataVisualizationInterface,
            self._on_data_visualization_interface_loaded,
        )
        self._emit_progress(84, "注册协议编辑...")
        self.protocolEditorInterface = self._create_lazy_interface(
            "protocolEditorInterface",
            ProtocolEditorInterface,
        )
        self._emit_progress(86, "注册算法编辑...")
        self.autopilotEditorInterface = self._create_lazy_interface(
            "autopilotEditorInterface",
            AutopilotEditorInterface,
        )
        self._emit_progress(88, "加载设置...")
        self.settingsInterface = SettingsInterface(self)

        # 连接设置界面信号
        self.settingsInterface.config_changed.connect(self._on_config_changed)

        self._emit_progress(92, "构建导航...")
        self.init_navigation()
        self._emit_progress(96, "初始化窗口...")
        self.init_window()

        # 所有界面创建完成后，强制应用字体到所有组件
        self._emit_progress(98, "应用字体...")
        FontManager.apply_font_to_widget(self)
        self._emit_progress(100, "初始化完成")

    def _emit_progress(self, value, text=None):
        if self._progress_callback:
            self._progress_callback(value, text)

    def _create_lazy_interface(self, object_name, factory, on_loaded=None):
        def _load_widget():
            return factory(self)

        def _handle_loaded(widget):
            FontManager.apply_font_to_widget(widget)
            if on_loaded:
                on_loaded(widget)

        return _LazyInterfaceHost(object_name, _load_widget, _handle_loaded, self)

    def _on_ftp_interface_loaded(self, _widget):
        self._sync_ftp_and_data_visualization()

    def _on_data_visualization_interface_loaded(self, widget):
        widget.set_ftp_connected(False)
        self._sync_ftp_and_data_visualization()

    def _sync_ftp_and_data_visualization(self):
        if not self.dataVisualizationInterface.is_loaded():
            return

        data_visualization = self.dataVisualizationInterface.widget()
        if not self.ftpInterface.is_loaded():
            data_visualization.set_ftp_connected(False)
            return

        ftp_interface = self.ftpInterface.widget()
        if not self._ftp_data_visualization_connected:
            ftp_interface.connection_changed.connect(data_visualization.set_ftp_connected)
            self._ftp_data_visualization_connected = True

        data_visualization.set_ftp_connected(ftp_interface.sftp is not None)

    def _switch_to_interface(self, interface):
        if isinstance(interface, _LazyInterfaceHost):
            interface.ensure_loaded()
        self.switchTo(interface)

    def init_window(self):
        self.resize(1700, 1050)
        self.setWindowTitle('RTopenEuler 系统管理工具')
        self.setWindowIcon(QIcon(os.path.join(get_program_dir(), "assets", "logo.png")))

        # 窗口最大化显示
        self.showMaximized()

    def _on_config_changed(self):
        """配置更改处理"""
        # 字体大小更改需要重启应用
        pass

    def init_navigation(self):
        # 添加子界面到导航栏
        self.addSubInterface(self.homeInterface, FluentIcon.HOME, '首页')
        self.environment_key = self.addSubInterface(self.environmentInstallInterface, FluentIcon.APPLICATION, '环境配置')
        self.codegen_key = self.addSubInterface(self.codeGenerationInterface, FluentIcon.EDIT, '代码生成')
        self.terminal_key = self.addSubInterface(self.terminalInterface, FluentIcon.DEVELOPER_TOOLS, '远程终端')
        self.ftp_key = self.addSubInterface(self.ftpInterface, FluentIcon.FOLDER, 'FTP客户端')
        self.data_visualization_key = self.addSubInterface(
            self.dataVisualizationInterface,
            FluentIcon.PIE_SINGLE,
            '数据可视化'
        )
        self.protocol_editor_key = self.addSubInterface(
            self.protocolEditorInterface,
            FluentIcon.LIBRARY,
            '协议编辑'
        )
        self.autopilot_editor_key = self.addSubInterface(
            self.autopilotEditorInterface,
            FluentIcon.IOT,
            '算法编辑'
        )
        self.initializer_key = self.addSubInterface(self.initializerInterface, FluentIcon.SYNC, '系统初始化')
        self.tutorial_key = self.addSubInterface(self.tutorialInterface, FluentIcon.HELP, '教程文档')

        # 在底部添加设置界面
        self.addSubInterface(self.settingsInterface, FluentIcon.SETTING, '设置', NavigationItemPosition.BOTTOM)

        # 连接主页面的跳转信号
        self.homeInterface.switch_to_initializer.connect(self._switch_to_initializer_page)
        self.homeInterface.switch_to_environment.connect(self._switch_to_environment_page)
        self.homeInterface.switch_to_codegen.connect(self._switch_to_codegen_page)
        self.homeInterface.switch_to_tutorial.connect(self._switch_to_tutorial_page)
        self.homeInterface.switch_to_terminal.connect(self._switch_to_terminal_page)
        self.homeInterface.switch_to_ftp.connect(self._switch_to_ftp_page)
        self.homeInterface.switch_to_data_visualization.connect(self._switch_to_data_visualization_page)
        self.homeInterface.switch_to_protocol_editor.connect(self._switch_to_protocol_editor_page)
        self.homeInterface.switch_to_autopilot_editor.connect(self._switch_to_autopilot_editor_page)
        self.homeInterface.switch_to_settings.connect(self._switch_to_settings_page)

    def _switch_to_environment_page(self):
        """切换到环境配置页面"""
        self._switch_to_interface(self.environmentInstallInterface)

    def _switch_to_initializer_page(self):
        """切换到系统初始化页面 - 等同于点击侧边栏按钮"""
        self._switch_to_interface(self.initializerInterface)

    def _switch_to_codegen_page(self):
        """切换到代码生成页面"""
        self._switch_to_interface(self.codeGenerationInterface)

    def _switch_to_tutorial_page(self):
        """切换到教程文档页面"""
        self._switch_to_interface(self.tutorialInterface)

    def _switch_to_ftp_page(self):
        """切换到 FTP 客户端页面"""
        self._switch_to_interface(self.ftpInterface)

    def _switch_to_terminal_page(self):
        """切换到远程终端页面"""
        self._switch_to_interface(self.terminalInterface)

    def _switch_to_data_visualization_page(self):
        """切换到数据可视化页面"""
        self._switch_to_interface(self.dataVisualizationInterface)

    def _switch_to_protocol_editor_page(self):
        """切换到协议编辑页面"""
        self._switch_to_interface(self.protocolEditorInterface)

    def _switch_to_autopilot_editor_page(self):
        """切换到算法编辑页面"""
        self._switch_to_interface(self.autopilotEditorInterface)

    def _switch_to_settings_page(self):
        """切换到设置页面"""
        self.switchTo(self.settingsInterface)
