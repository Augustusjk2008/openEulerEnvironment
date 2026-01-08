import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QIcon
from qfluentwidgets import FluentWindow, NavigationItemPosition, FluentIcon, setTheme, Theme

# 导入自定义界面
from home_interface import HomeInterface
from settings_interface import SettingsInterface
from initializer_interface import InitializerInterface
from environment_install_interface import EnvironmentInstallInterface
from code_generation_interface import CodeGenerationInterface


class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()

        # 初始化界面
        self.homeInterface = HomeInterface(self)
        self.environmentInstallInterface = EnvironmentInstallInterface(self)
        self.initializerInterface = InitializerInterface(self)
        self.codeGenerationInterface = CodeGenerationInterface(self)
        self.settingsInterface = SettingsInterface(self)

        self.init_navigation()
        self.init_window()

    def init_window(self):
        self.resize(1000, 750)
        self.setWindowTitle('RTopenEuler 系统管理工具')

        # 设置固定大小，禁止调整窗口大小（包括最大化）
        self.setMinimumSize(1000, 750)
        self.setMaximumSize(1000, 750)

        # 居中显示
        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)

    def init_navigation(self):
        # 添加子界面到导航栏
        self.addSubInterface(self.homeInterface, FluentIcon.HOME, '首页')
        self.environment_key = self.addSubInterface(self.environmentInstallInterface, FluentIcon.APPLICATION, '环境配置')
        self.codegen_key = self.addSubInterface(self.codeGenerationInterface, FluentIcon.EDIT, '代码生成')
        self.initializer_key = self.addSubInterface(self.initializerInterface, FluentIcon.SYNC, '系统初始化')

        # 在底部添加设置界面
        self.addSubInterface(self.settingsInterface, FluentIcon.SETTING, '设置', NavigationItemPosition.BOTTOM)

        # 连接主页面的跳转信号
        self.homeInterface.switch_to_initializer.connect(self._switch_to_initializer_page)
        self.homeInterface.switch_to_environment.connect(self._switch_to_environment_page)
        self.homeInterface.switch_to_codegen.connect(self._switch_to_codegen_page)

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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
