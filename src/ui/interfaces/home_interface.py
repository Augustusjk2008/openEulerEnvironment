"""
主页界面
采用 Fluent Widgets 简洁、规整、轻量的设计语言
以浅灰底 + 低饱和蓝 / 绿点缀为基调，无多余动态特效
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QSizePolicy, QPushButton, QScrollArea
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap
from qfluentwidgets import (
    CardWidget, TransparentPushButton, TransparentToolButton,
    SubtitleLabel, BodyLabel, CaptionLabel, StrongBodyLabel,
    FluentIcon as FIF, IconWidget
)
from PyQt5.QtGui import QPalette, QColor
from core.font_manager import FontManager

class NavigationBar(QFrame):
    """顶部简洁导航栏"""
    settingsButtonClicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(80)
        self.setStyleSheet("""
            NavigationBar {
                background-color: transparent;
                border: none;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(30, 15, 30, 15)
        layout.setSpacing(20)

        # 左侧：Logo + 程序名称
        left_layout = QHBoxLayout()
        left_layout.setSpacing(12)

        # Logo 图标（使用 FluentIcon）
        self.logo_label = IconWidget(FIF.DEVELOPER_TOOLS)
        self.logo_label.setFixedSize(36, 36)

        # 程序名称
        self.app_name = SubtitleLabel("803所 RTopenEuler 系统管理工具")
        self.app_name.setStyleSheet(f"font-size: {FontManager.get_font_size('large_title')}px; font-weight: 600;")

        # 设置按钮
        self.settings_button = TransparentToolButton(FIF.SETTING, self)
        self.settings_button.setFixedSize(48, 48)
        self.settings_button.setIconSize(QSize(32, 32))
        self.settings_button.setToolTip("设置")
        self.settings_button.clicked.connect(self.settingsButtonClicked)

        left_layout.addWidget(self.logo_label)
        left_layout.addWidget(self.app_name)
        layout.addLayout(left_layout)
        layout.addStretch()
        layout.addWidget(self.settings_button)


class FunctionCard(CardWidget):
    """功能卡片"""

    def __init__(self, icon, title, description, button_text, color="#0078D4", parent=None):
        super().__init__(parent)
        self.setFixedSize(360, 240)
        self.setStyleSheet(f"""
            CardWidget {{
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 12px;
                border: 1px solid rgba(0, 0, 0, 0.06);
            }}
            CardWidget:hover {{
                background-color: rgba(255, 255, 255, 0.95);
                border: 1px solid rgba(0, 0, 0, 0.1);
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(10)

        # 图标
        icon_widget = IconWidget(icon)
        icon_widget.setFixedSize(48, 48)
        layout.addWidget(icon_widget, 0, Qt.AlignCenter)

        # 标题
        title_label = StrongBodyLabel(title)
        title_label.setStyleSheet(f"font-size: {FontManager.get_font_size('subtitle')}px; font-weight: 600; color: #2D3748;")
        layout.addWidget(title_label)

        # 说明文字
        desc_label = BodyLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(f"font-size: {FontManager.get_font_size('body')}px; color: #5A6A7A;")
        desc_label.setMaximumHeight(55)
        layout.addWidget(desc_label)

        layout.addStretch(1)

        # 操作按钮 - 统一使用轮廓样式
        self.button = TransparentPushButton(button_text)
        self.button.setFixedHeight(36)
        self.button.setStyleSheet(f"""
            TransparentPushButton {{
                border: 1px solid {color};
                border-radius: 6px;
                color: {color};
            }}
            TransparentPushButton:hover {{
                background-color: {color};
                color: white;
                border: 1px solid {color};
            }}
        """)

        self.button.setFixedWidth(180)
        layout.addWidget(self.button, 0, Qt.AlignCenter)


class FunctionArea(QWidget):
    """核心功能区（4列3行卡片布局）"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(980)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 10, 30, 10)
        layout.setSpacing(20)

        # 卡片网格布局
        grid_layout = QGridLayout()
        grid_layout.setSpacing(30)
        grid_layout.setContentsMargins(0, 10, 0, 0)

        # 卡片 1：开发环境配置（蓝色）
        self.card1 = FunctionCard(
            icon=FIF.APPLICATION,
            title="开发环境配置",
            description="一键部署编译器、依赖库、工具链，无需手动配置环境变量",
            button_text="立即配置",
            color="#0078D4"
        )

        # 卡片 2：自动代码生成（绿色）
        self.card2 = FunctionCard(
            icon=FIF.EDIT,
            title="自动代码生成",
            description="生成初始化模板、示例工程，减少重复开发",
            button_text="选择代码生成",
            color="#107C10"
        )

        # 卡片 3：设备初始化向导（紫色）
        self.card3 = FunctionCard(
            icon=FIF.SYNC,
            title="设备初始化向导",
            description="完成 CCU 基础参数配置、驱动环境加载，需要网络连接 CCU 设备",
            button_text="启动向导",
            color="#6B4BB3"
        )

        # 卡片 4：教程与文档（橙色）
        self.card4 = FunctionCard(
            icon=FIF.HELP,
            title="教程与文档",
            description="查看配置指南、代码示例、常见问题，快速上手全功能",
            button_text="浏览教程",
            color="#D83B01"
        )

        # 卡片 5：远程终端（深蓝色）
        self.card5 = FunctionCard(
            icon=FIF.DEVELOPER_TOOLS,
            title="远程终端",
            description="通过 SSH 远程登录 CCU 设备，执行命令并查看输出",
            button_text="打开终端",
            color="#005A9E"
        )

        # 卡片 6：FTP 客户端（青绿色）
        self.card6 = FunctionCard(
            icon=FIF.FOLDER,
            title="FTP 客户端",
            description="本地与远程文件的上传、下载和移动，方便直接管理设备文件",
            button_text="打开 FTP",
            color="#008272"
        )

        # 卡片 7：数据可视化（蓝绿色）
        self.card7 = FunctionCard(
            icon=FIF.PIE_SINGLE,
            title="数据可视化",
            description="读取 SLOG 数据并按条目序号绘制曲线，可勾选需要展示的字段",
            button_text="打开可视化",
            color="#0078A8"
        )

        # 卡片 8：协议编辑（灰蓝色）
        self.card8 = FunctionCard(
            icon=FIF.LIBRARY,
            title="协议建模",
            description="编辑协议结构并生成 pack/unpack 与序列化代码",
            button_text="打开编辑器",
            color="#4C6A92"
        )

        # 卡片 9：算法编辑（青蓝色）
        self.card9 = FunctionCard(
            icon=FIF.IOT,
            title="飞控算法工作台",
            description="编辑控制器描述文件，支持 Program 与流程图联动",
            button_text="打开工作台",
            color="#0F766E"
        )

        # 添加卡片到网格（4列3行）
        grid_layout.addWidget(self.card1, 0, 0)
        grid_layout.addWidget(self.card2, 0, 1)
        grid_layout.addWidget(self.card5, 0, 2)
        grid_layout.addWidget(self.card6, 0, 3)

        grid_layout.addWidget(self.card7, 1, 0)
        grid_layout.addWidget(self.card8, 1, 1)
        grid_layout.addWidget(self.card9, 1, 2)
        grid_layout.addWidget(self.card3, 1, 3)

        grid_layout.addWidget(self.card4, 2, 0)

        # 居中对齐网格
        grid_layout.setColumnStretch(0, 1)
        grid_layout.setColumnStretch(1, 1)
        grid_layout.setColumnStretch(2, 1)
        grid_layout.setColumnStretch(3, 1)

        # 创建一个容器来居中显示
        container = QWidget()
        container.setLayout(grid_layout)
        container.setMaximumWidth(1650)

        container_layout = QHBoxLayout()
        container_layout.addStretch()
        container_layout.addWidget(container)
        container_layout.addStretch()

        layout.addLayout(container_layout)


class AuxiliaryArea(QFrame):
    """辅助信息区（通栏浅背景卡片）"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(100)
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(249, 249, 249, 0.8);
                border-radius: 12px;
                border: none;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(10)

        # 新手指引
        guide_title = StrongBodyLabel("新手指引")
        guide_title.setStyleSheet(f"font-size: {FontManager.get_font_size('title')}px; color: #2D3748;")

        guide_text = BodyLabel("首次使用建议：直接查看教程中的《00.本程序怎么使用》，然后按顺序执行即可。")
        guide_text.setStyleSheet(f"font-size: {FontManager.get_font_size('body')}px; color: #5A6A7A;")
        guide_text.setWordWrap(True)

        layout.addWidget(guide_title)
        layout.addWidget(guide_text)


class StatusBar(QFrame):
    """底部状态栏"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(50)
        self.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: none;
                border-top: 1px solid rgba(0, 0, 0, 0.06);
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(30, 10, 30, 10)

        # 左侧：版本信息
        version_label = CaptionLabel("v0.0.6 抢先版")
        version_label.setStyleSheet(f"color: #7A8A9A; font-size: {FontManager.get_font_size('caption')}px;")

        layout.addWidget(version_label)
        layout.addStretch()


class HomeInterface(QWidget):
    """主页界面"""

    # 定义页面跳转信号
    switch_to_initializer = pyqtSignal()
    switch_to_environment = pyqtSignal()
    switch_to_codegen = pyqtSignal()
    switch_to_tutorial = pyqtSignal()
    switch_to_terminal = pyqtSignal()
    switch_to_ftp = pyqtSignal()
    switch_to_data_visualization = pyqtSignal()
    switch_to_protocol_editor = pyqtSignal()
    switch_to_autopilot_editor = pyqtSignal()
    switch_to_settings = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent  # 保存父窗口引用
        self.setObjectName("homeInterface")

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 创建滚动区域以支持小屏幕
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background-color: transparent;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: rgba(0, 0, 0, 0.2);
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: rgba(0, 0, 0, 0.3);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        # 内容容器
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # 1. 顶部导航栏
        self.navigation_bar = NavigationBar()
        content_layout.addWidget(self.navigation_bar)

        # 添加间距
        content_layout.addSpacing(10)

        # 2. 核心功能区
        self.function_area = FunctionArea()
        content_layout.addWidget(self.function_area)

        # 添加间距
        content_layout.addSpacing(20)

        # 3. 辅助信息区
        auxiliary_container = QWidget()
        auxiliary_layout = QVBoxLayout(auxiliary_container)
        auxiliary_layout.setContentsMargins(30, 0, 30, 0)
        auxiliary_layout.setSpacing(0)

        self.auxiliary_area = AuxiliaryArea()
        auxiliary_layout.addWidget(self.auxiliary_area)

        content_layout.addWidget(auxiliary_container)

        # 添加弹性间距
        content_layout.addStretch()

        # 4. 底部状态栏
        self.status_bar = StatusBar()
        content_layout.addWidget(self.status_bar)

        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

        # 连接信号
        self._connect_signals()

    def _connect_signals(self):
        """连接信号槽"""
        # 导航栏按钮
        self.navigation_bar.settingsButtonClicked.connect(self.switch_to_settings)

        # 功能卡片按钮
        self.function_area.card1.button.clicked.connect(self._on_env_config_clicked)
        self.function_area.card2.button.clicked.connect(self._on_code_generate_clicked)
        self.function_area.card3.button.clicked.connect(self._on_init_wizard_clicked)
        self.function_area.card4.button.clicked.connect(self._on_tutorial_clicked)
        self.function_area.card5.button.clicked.connect(self._on_terminal_clicked)
        self.function_area.card6.button.clicked.connect(self._on_ftp_clicked)
        self.function_area.card7.button.clicked.connect(self._on_data_visualization_clicked)
        self.function_area.card8.button.clicked.connect(self._on_protocol_editor_clicked)
        self.function_area.card9.button.clicked.connect(self._on_autopilot_editor_clicked)

    def _on_env_config_clicked(self):
        """开发环境配置按钮点击事件 - 跳转到环境配置页面"""
        self.switch_to_environment.emit()

    def _on_code_generate_clicked(self):
        """自动代码生成按钮点击事件 - 跳转到代码生成页面"""
        self.switch_to_codegen.emit()

    def _on_init_wizard_clicked(self):
        """设备初始化向导按钮点击事件 - 跳转到初始化页面"""
        self.switch_to_initializer.emit()

    def _on_tutorial_clicked(self):
        """教程与文档按钮点击事件 - 跳转到教程页面"""
        self.switch_to_tutorial.emit()

    def _on_ftp_clicked(self):
        """FTP 客户端按钮点击事件 - 跳转到 FTP 页面"""
        self.switch_to_ftp.emit()

    def _on_data_visualization_clicked(self):
        """数据可视化按钮点击事件 - 跳转到数据可视化页面"""
        self.switch_to_data_visualization.emit()

    def _on_terminal_clicked(self):
        """远程终端按钮点击事件 - 跳转到终端页面"""
        self.switch_to_terminal.emit()

    def _on_protocol_editor_clicked(self):
        """协议编辑按钮点击事件 - 跳转到协议编辑页面"""
        self.switch_to_protocol_editor.emit()

    def _on_autopilot_editor_clicked(self):
        """算法编辑按钮点击事件 - 跳转到算法编辑页面"""
        self.switch_to_autopilot_editor.emit()
