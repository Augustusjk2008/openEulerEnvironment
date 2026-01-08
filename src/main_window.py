import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QIcon, QFont
from qfluentwidgets import FluentWindow, NavigationItemPosition, FluentIcon, setTheme, Theme
from config_manager import get_config_manager
from font_manager import FontManager

# 导入自定义界面
from home_interface import HomeInterface
from settings_interface import SettingsInterface
from initializer_interface import InitializerInterface
from environment_install_interface import EnvironmentInstallInterface
from code_generation_interface import CodeGenerationInterface
from tutorial_interface import TutorialInterface


class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()

        # 加载配置
        self.config_manager = get_config_manager()

        # 初始化界面
        self.homeInterface = HomeInterface(self)
        self.environmentInstallInterface = EnvironmentInstallInterface(self)
        self.initializerInterface = InitializerInterface(self)
        self.codeGenerationInterface = CodeGenerationInterface(self)
        self.tutorialInterface = TutorialInterface(self)
        self.settingsInterface = SettingsInterface(self)

        # 连接设置界面信号
        self.settingsInterface.config_changed.connect(self._on_config_changed)

        self.init_navigation()
        self.init_window()

        # 所有界面创建完成后，强制应用字体到所有组件
        FontManager.apply_font_to_widget(self)

    def init_window(self):
        self.resize(1400, 1000)
        self.setWindowTitle('RTopenEuler 系统管理工具')

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
        self.initializer_key = self.addSubInterface(self.initializerInterface, FluentIcon.SYNC, '系统初始化')
        self.tutorial_key = self.addSubInterface(self.tutorialInterface, FluentIcon.HELP, '教程文档')

        # 在底部添加设置界面
        self.addSubInterface(self.settingsInterface, FluentIcon.SETTING, '设置', NavigationItemPosition.BOTTOM)

        # 连接主页面的跳转信号
        self.homeInterface.switch_to_initializer.connect(self._switch_to_initializer_page)
        self.homeInterface.switch_to_environment.connect(self._switch_to_environment_page)
        self.homeInterface.switch_to_codegen.connect(self._switch_to_codegen_page)
        self.homeInterface.switch_to_tutorial.connect(self._switch_to_tutorial_page)

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

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 在创建窗口之前，先加载配置并应用全局字体
    config_manager = get_config_manager()
    font_size_name = config_manager.get("font_size", "small")
    FontManager.apply_global_font(font_size_name)

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
