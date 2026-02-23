"""
应用设置界面
提供应用程序全局设置功能
"""

import os
import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QScrollArea, QFileDialog, QMessageBox, QButtonGroup, QRadioButton
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from qfluentwidgets import (
    CardWidget, PrimaryPushButton, PushButton,
    SubtitleLabel, BodyLabel, CaptionLabel, StrongBodyLabel,
    FluentIcon as FIF, IconWidget, LineEdit,
    CheckBox, InfoBar, InfoBarPosition, ComboBox, SwitchButton
)
from core.config_manager import get_config_manager
from core.font_manager import FontManager
from PyQt5.QtWidgets import QLabel as StdLabel


class SettingsInterface(QWidget):
    """应用设置界面"""

    # 配置更改信号
    config_changed = pyqtSignal()
    font_size_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("settingsInterface")
        self.config_manager = get_config_manager()

        self.init_ui()
        self._load_settings()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(20)

        # 标题
        title = SubtitleLabel("应用设置")
        title.setStyleSheet(f"color: #2D3748; font-size: {FontManager.get_font_size('large_title')}px;")
        layout.addWidget(title)

        # 说明
        desc = BodyLabel("配置应用程序的全局参数和偏好设置")
        desc.setStyleSheet(f"color: #5A6A7A; font-size: {FontManager.get_font_size('body')}px;")
        layout.addWidget(desc)

        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(20)

        # 字体设置卡片
        self.font_card = self._create_font_settings_card()
        content_layout.addWidget(self.font_card)

        # 目录设置卡片
        self.dir_card = self._create_directory_settings_card()
        content_layout.addWidget(self.dir_card)

        # SSH 设置卡片
        self.ssh_card = self._create_ssh_settings_card()
        content_layout.addWidget(self.ssh_card)

        # 其他设置卡片
        self.other_card = self._create_other_settings_card()
        content_layout.addWidget(self.other_card)

        # 操作按钮区
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)

        self.reset_btn = PushButton("恢复默认设置")
        self.reset_btn.setFixedHeight(36)
        self.reset_btn.clicked.connect(self._reset_to_default)
        button_layout.addWidget(self.reset_btn)

        button_layout.addStretch()

        self.save_btn = PrimaryPushButton("保存设置")
        self.save_btn.setFixedHeight(36)
        self.save_btn.setFixedWidth(120)
        self.save_btn.clicked.connect(self._save_settings)
        button_layout.addWidget(self.save_btn)

        content_layout.addLayout(button_layout)
        content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll)

    def _create_font_settings_card(self):
        """创建字体设置卡片"""
        card = CardWidget()
        card.setStyleSheet("""
            CardWidget {
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 12px;
                border: 1px solid rgba(0, 0, 0, 0.06);
            }
        """)

        layout = QHBoxLayout(card)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(15)

        # 标题
        title_layout = QHBoxLayout()
        title_layout.setSpacing(10)

        icon = IconWidget(FIF.DEVELOPER_TOOLS)
        icon.setFixedSize(28, 28)
        title_layout.addWidget(icon)

        title = StrongBodyLabel("字体设置")
        title.setStyleSheet(f"font-size: {FontManager.get_font_size('title')}px; color: #2D3748;")
        title_layout.addWidget(title)

        title_layout.addStretch()
        layout.addLayout(title_layout)

        # 说明
        desc = BodyLabel("调整程序字体大小，需要重启应用生效")
        desc.setStyleSheet(f"color: #7A8A9A; font-size: {FontManager.get_font_size('caption')}px;")
        layout.addWidget(desc)

        # 字体大小选项
        self.font_button_group = QButtonGroup(self)

        font_options = [
            ("小", "small", "当前默认字体大小"),
            ("中", "medium", "适合大多数显示器"),
            ("大", "large", "适合高分辨率显示器"),
        ]

        for i, (label, value, tooltip) in enumerate(font_options):
            radio = QRadioButton(label)
            radio.setStyleSheet("""
                QRadioButton {
                    color: #2D3748;
                    spacing: 8px;
                }
                QRadioButton::indicator {
                    width: 18px;
                    height: 18px;
                }
                QRadioButton::indicator:checked {
                    background-color: #0078D4;
                    border: 2px solid #0078D4;
                    border-radius: 9px;
                }
                QRadioButton::indicator:unchecked {
                    background-color: white;
                    border: 2px solid #A0A0A0;
                    border-radius: 9px;
                }
            """)
            radio.setToolTip(tooltip)
            radio.setProperty("value", value)
            self.font_button_group.addButton(radio, i)
            layout.addWidget(radio)

        # 连接信号（在所有控件创建后）
        for button in self.font_button_group.buttons():
            button.toggled.connect(self._on_font_radio_toggled)

        # 初始化预览
        self._update_font_preview()

        return card

    def _create_directory_settings_card(self):
        """创建目录设置卡片"""
        card = CardWidget()
        card.setStyleSheet("""
            CardWidget {
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 12px;
                border: 1px solid rgba(0, 0, 0, 0.06);
            }
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(15)

        # 标题
        title_layout = QHBoxLayout()
        title_layout.setSpacing(10)

        icon = IconWidget(FIF.FOLDER)
        icon.setFixedSize(28, 28)
        title_layout.addWidget(icon)

        title = StrongBodyLabel("目录设置")
        title.setStyleSheet(f"font-size: {FontManager.get_font_size('title')}px; color: #2D3748;")
        title_layout.addWidget(title)

        title_layout.addStretch()
        layout.addLayout(title_layout)

        # 输出目录
        output_layout = QVBoxLayout()
        output_layout.setSpacing(5)

        output_label = BodyLabel("默认输出目录（代码生成）")
        output_label.setStyleSheet(f"font-size: {FontManager.get_font_size('body')}px; color: #2D3748;")
        output_layout.addWidget(output_label)

        output_path_layout = QHBoxLayout()
        output_path_layout.setSpacing(10)

        self.output_dir_edit = LineEdit()
        self.output_dir_edit.setFixedHeight(36)
        self.output_dir_edit.setPlaceholderText("选择代码生成的默认输出目录")
        output_path_layout.addWidget(self.output_dir_edit)

        output_browse_btn = PushButton("浏览...")
        output_browse_btn.setFixedHeight(36)
        output_browse_btn.setFixedWidth(80)
        output_browse_btn.clicked.connect(self._browse_output_dir)
        output_path_layout.addWidget(output_browse_btn)

        output_layout.addLayout(output_path_layout)
        layout.addLayout(output_layout)

        # 安装目录
        install_layout = QVBoxLayout()
        install_layout.setSpacing(5)

        install_label = BodyLabel("默认安装目录（环境配置）")
        install_label.setStyleSheet(f"font-size: {FontManager.get_font_size('body')}px; color: #2D3748;")
        install_layout.addWidget(install_label)

        install_path_layout = QHBoxLayout()
        install_path_layout.setSpacing(10)

        self.install_dir_edit = LineEdit()
        self.install_dir_edit.setFixedHeight(36)
        self.install_dir_edit.setPlaceholderText("选择开发工具的默认安装目录")
        install_path_layout.addWidget(self.install_dir_edit)

        install_browse_btn = PushButton("浏览...")
        install_browse_btn.setFixedHeight(36)
        install_browse_btn.setFixedWidth(80)
        install_browse_btn.clicked.connect(self._browse_install_dir)
        install_path_layout.addWidget(install_browse_btn)

        install_layout.addLayout(install_path_layout)
        layout.addLayout(install_layout)

        return card

    def _create_ssh_settings_card(self):
        """创建 SSH 设置卡片"""
        card = CardWidget()
        card.setStyleSheet("""
            CardWidget {
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 12px;
                border: 1px solid rgba(0, 0, 0, 0.06);
            }
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(15)

        # 标题
        title_layout = QHBoxLayout()
        title_layout.setSpacing(10)

        icon = IconWidget(FIF.SYNC)
        icon.setFixedSize(28, 28)
        title_layout.addWidget(icon)

        title = StrongBodyLabel("SSH 连接设置")
        title.setStyleSheet(f"font-size: {FontManager.get_font_size('title')}px; color: #2D3748;")
        title_layout.addWidget(title)

        title_layout.addStretch()
        layout.addLayout(title_layout)

        # 说明
        desc = BodyLabel("配置 CCU 设备的 SSH 连接参数，用于设备初始化功能")
        desc.setStyleSheet(f"color: #7A8A9A; font-size: {FontManager.get_font_size('caption')}px;")
        layout.addWidget(desc)

        # SSH 参数网格
        grid = QGridLayout()
        grid.setSpacing(12)
        grid.setColumnStretch(1, 1)

        # 主机地址
        host_label = BodyLabel("主机地址:")
        host_label.setStyleSheet(f"font-size: {FontManager.get_font_size('body')}px; color: #2D3748;")
        grid.addWidget(host_label, 0, 0)

        self.ssh_host_edit = LineEdit()
        self.ssh_host_edit.setFixedHeight(36)
        self.ssh_host_edit.setPlaceholderText("例如: 192.168.137.100")
        grid.addWidget(self.ssh_host_edit, 0, 1)

        # 用户名
        user_label = BodyLabel("用户名:")
        user_label.setStyleSheet(f"font-size: {FontManager.get_font_size('body')}px; color: #2D3748;")
        grid.addWidget(user_label, 1, 0)

        self.ssh_user_edit = LineEdit()
        self.ssh_user_edit.setFixedHeight(36)
        self.ssh_user_edit.setPlaceholderText("例如: root")
        grid.addWidget(self.ssh_user_edit, 1, 1)

        # 密码
        pass_label = BodyLabel("密码:")
        pass_label.setStyleSheet(f"font-size: {FontManager.get_font_size('body')}px; color: #2D3748;")
        grid.addWidget(pass_label, 2, 0)

        self.ssh_pass_edit = LineEdit()
        self.ssh_pass_edit.setFixedHeight(36)
        self.ssh_pass_edit.setPlaceholderText("SSH 登录密码")
        self.ssh_pass_edit.setEchoMode(LineEdit.Password)
        grid.addWidget(self.ssh_pass_edit, 2, 1)

        layout.addLayout(grid)

        return card

    def _create_other_settings_card(self):
        """创建其他设置卡片"""
        card = CardWidget()
        card.setStyleSheet("""
            CardWidget {
                background-color: rgba(249, 249, 249, 0.9);
                border-radius: 12px;
                border: 1px solid rgba(0, 0, 0, 0.06);
            }
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(15)

        # 标题
        title_layout = QHBoxLayout()
        title_layout.setSpacing(10)

        icon = IconWidget(FIF.SETTING)
        icon.setFixedSize(28, 28)
        title_layout.addWidget(icon)

        title = StrongBodyLabel("其他设置")
        title.setStyleSheet(f"font-size: {FontManager.get_font_size('title')}px; color: #2D3748;")
        title_layout.addWidget(title)

        title_layout.addStretch()
        layout.addLayout(title_layout)

        # 开关选项网格
        grid = QGridLayout()
        grid.setSpacing(15)
        grid.setColumnStretch(1, 1)

        # 自动检查更新
        update_label = BodyLabel("自动检查更新")
        update_label.setStyleSheet(f"font-size: {FontManager.get_font_size('body')}px; color: #2D3748;")
        grid.addWidget(update_label, 0, 0)

        self.update_switch = SwitchButton()
        self.update_switch.setFixedHeight(24)
        grid.addWidget(self.update_switch, 0, 1, Qt.AlignRight)

        # 显示日志时间戳
        log_label = BodyLabel("显示日志时间戳")
        log_label.setStyleSheet(f"font-size: {FontManager.get_font_size('body')}px; color: #2D3748;")
        grid.addWidget(log_label, 1, 0)

        self.log_switch = SwitchButton()
        self.log_switch.setFixedHeight(24)
        grid.addWidget(self.log_switch, 1, 1, Qt.AlignRight)

        # 初始化前确认
        confirm_label = BodyLabel("初始化前确认")
        confirm_label.setStyleSheet(f"font-size: {FontManager.get_font_size('body')}px; color: #2D3748;")
        grid.addWidget(confirm_label, 2, 0)

        self.confirm_switch = SwitchButton()
        self.confirm_switch.setFixedHeight(24)
        grid.addWidget(self.confirm_switch, 2, 1, Qt.AlignRight)

        layout.addLayout(grid)

        return card

    def _load_settings(self):
        """从配置管理器加载设置"""
        # 加载字体大小
        font_size = self.config_manager.get("font_size", "small")
        for button in self.font_button_group.buttons():
            if button.property("value") == font_size:
                button.setChecked(True)
                break

        # 加载目录设置
        self.output_dir_edit.setText(self.config_manager.get("default_output_dir", r"C:\Projects"))
        self.install_dir_edit.setText(self.config_manager.get("default_install_dir", r"C:\openEulerTools"))

        # 加载 SSH 设置（从settings.json读取，无硬编码默认值）
        self.ssh_host_edit.setText(self.config_manager.get("ssh_host", ""))
        self.ssh_user_edit.setText(self.config_manager.get("ssh_username", ""))
        self.ssh_pass_edit.setText(self.config_manager.get("ssh_password", ""))

        # 加载其他设置
        self.update_switch.setChecked(self.config_manager.get("auto_check_update", False))
        self.log_switch.setChecked(self.config_manager.get("show_log_timestamp", True))
        self.confirm_switch.setChecked(self.config_manager.get("confirm_before_init", True))

    def _save_settings(self):
        """保存设置到配置文件"""
        # 获取字体大小
        old_font_size = self.config_manager.get("font_size", "small")
        font_size = "small"
        for button in self.font_button_group.buttons():
            if button.isChecked():
                font_size = button.property("value")
                break

        # 保存所有配置
        self.config_manager.set("font_size", font_size)
        self.config_manager.set("default_output_dir", self.output_dir_edit.text())
        self.config_manager.set("default_install_dir", self.install_dir_edit.text())
        self.config_manager.set("ssh_host", self.ssh_host_edit.text())
        self.config_manager.set("ssh_username", self.ssh_user_edit.text())
        self.config_manager.set("ssh_password", self.ssh_pass_edit.text())
        self.config_manager.set("auto_check_update", self.update_switch.isChecked())
        self.config_manager.set("show_log_timestamp", self.log_switch.isChecked())
        self.config_manager.set("confirm_before_init", self.confirm_switch.isChecked())

        # 检查字体大小是否改变
        if old_font_size != font_size:
            InfoBar.success("保存成功", "字体大小已更改，请重启应用以查看效果",
                           duration=4000, parent=self.window())
        else:
            InfoBar.success("保存成功", "设置已保存",
                           duration=2000, parent=self.window())

        # 发送配置更改信号
        self.config_changed.emit()

    def _reset_to_default(self):
        """恢复默认设置"""
        reply = QMessageBox.question(
            self, "确认重置",
            "确定要恢复所有设置为默认值吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.config_manager.reset_to_default()
            self._load_settings()
            InfoBar.success("重置完成", "所有设置已恢复为默认值",
                           duration=2000, parent=self.window())

    def _browse_output_dir(self):
        """浏览输出目录"""
        directory = QFileDialog.getExistingDirectory(
            self, "选择默认输出目录", self.output_dir_edit.text()
        )
        if directory:
            self.output_dir_edit.setText(directory)

    def _browse_install_dir(self):
        """浏览安装目录"""
        directory = QFileDialog.getExistingDirectory(
            self, "选择默认安装目录", self.install_dir_edit.text()
        )
        if directory:
            self.install_dir_edit.setText(directory)

    def _on_font_radio_toggled(self):
        """字体大小单选框切换事件"""
        self._update_font_preview()

    def _update_font_preview(self):
        """更新字体预览"""
        # 获取当前选中的字体大小
        font_size = "small"
        for button in self.font_button_group.buttons():
            if button.isChecked():
                font_size = button.property("value")
                break

        # 临时更新 FontManager 的当前大小（不影响全局）
        FontManager.set_size(font_size)

        # 创建字体
        font = QFont()
        font.setFamily("Microsoft YaHei")
        font.setPointSize(FontManager.get_font_size("body"))

        # 更新预览标题和文本的字体
        if hasattr(self, 'preview_title') and self.preview_title:
            title_font = QFont(font)
            title_font.setBold(True)
            title_font.setPointSize(FontManager.get_font_size("title"))
            self.preview_title.setFont(title_font)

        if hasattr(self, 'preview_text') and self.preview_text:
            self.preview_text.setFont(font)
