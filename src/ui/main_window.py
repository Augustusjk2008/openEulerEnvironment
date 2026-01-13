import os
import warnings
from PyQt5.QtWidgets import QApplication
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

warnings.filterwarnings(
    "ignore",
    message="sipPyTypeDict\\(\\) is deprecated.*",
    category=DeprecationWarning
)

class MainWindow(FluentWindow):
    def __init__(self, progress_callback=None):
        super().__init__()
        self._progress_callback = progress_callback

        # 加载配置
        self._emit_progress(5, "加载配置...")
        self.config_manager = get_config_manager()

        # 初始化界面
        self._emit_progress(12, "加载首页...")
        self.homeInterface = HomeInterface(self)
        self._emit_progress(22, "加载环境配置...")
        self.environmentInstallInterface = EnvironmentInstallInterface(self)
        self._emit_progress(32, "加载系统初始化...")
        self.initializerInterface = InitializerInterface(self)
        self._emit_progress(42, "加载代码生成...")
        self.codeGenerationInterface = CodeGenerationInterface(self)
        self._emit_progress(52, "加载教程文档...")
        self.tutorialInterface = TutorialInterface(self)
        self._emit_progress(62, "加载远程终端...")
        self.terminalInterface = TerminalInterface(self)
        self._emit_progress(72, "加载 FTP 客户端...")
        self.ftpInterface = FtpInterface(self)
        self._emit_progress(80, "加载数据可视化...")
        self.dataVisualizationInterface = DataVisualizationInterface(self)
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

    def init_window(self):
        self.resize(1700, 1050)
        self.setWindowTitle('RTopenEuler 系统管理工具')
        self.setWindowIcon(QIcon(os.path.join(get_program_dir(), "assets", "logo.png")))

        # 居中显示
        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)

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
        self.homeInterface.switch_to_settings.connect(self._switch_to_settings_page)

    def _switch_to_environment_page(self):
        """切换到环境配置页面"""
        self.switchTo(self.environmentInstallInterface)

    def _switch_to_initializer_page(self):
        """切换到系统初始化页面 - 等同于点击侧边栏按钮"""
        # 直接使用 widget 切换
        self.switchTo(self.initializerInterface)

    def _switch_to_codegen_page(self):
        """切换到代码生成页面"""
        self.switchTo(self.codeGenerationInterface)

    def _switch_to_tutorial_page(self):
        """切换到教程文档页面"""
        self.switchTo(self.tutorialInterface)

    def _switch_to_ftp_page(self):
        """切换到 FTP 客户端页面"""
        self.switchTo(self.ftpInterface)

    def _switch_to_terminal_page(self):
        """切换到远程终端页面"""
        self.switchTo(self.terminalInterface)

    def _switch_to_data_visualization_page(self):
        """切换到数据可视化页面"""
        self.switchTo(self.dataVisualizationInterface)

    def _switch_to_settings_page(self):
        """切换到设置页面"""
        self.switchTo(self.settingsInterface)


