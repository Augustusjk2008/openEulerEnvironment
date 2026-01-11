"""
Login/Register window shown before the main app.
"""

import os
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QLabel, QSizePolicy
)
from qfluentwidgets import (
    CardWidget, SubtitleLabel, BodyLabel, StrongBodyLabel, CaptionLabel,
    LineEdit, PushButton, PrimaryPushButton, InfoBar
)

from core.auth_manager import AuthManager
from core.config_manager import get_program_dir
from core.font_manager import FontManager


class LoginWindow(QWidget):
    login_success = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.auth_manager = AuthManager()
        self.setWindowTitle("RTopenEuler 登录")
        self.setFixedSize(1120, 680)
        self.setStyleSheet("""
            QWidget#loginWindow {
                background: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:1, y2:1,
                    stop:0 #F3F7F5, stop:0.55 #E7F0EC, stop:1 #DCEBE6
                );
            }
        """)
        self.setObjectName("loginWindow")

        self._init_ui()
        self._set_mode("login")
        self._center_window()

    def _center_window(self):
        desktop = QApplication.desktop().availableGeometry()
        self.move(
            desktop.width() // 2 - self.width() // 2,
            desktop.height() // 2 - self.height() // 2
        )

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(36, 36, 36, 36)
        layout.setSpacing(30)

        hero_panel = self._create_hero_panel()
        form_panel = self._create_form_panel()

        layout.addWidget(hero_panel, 3)
        layout.addWidget(form_panel, 2)

    def _create_hero_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        title = StrongBodyLabel("RTopenEuler 系统管理工具")
        title.setStyleSheet(f"font-size: {FontManager.get_font_size('large_title')}px; color: #1F2D3D;")
        layout.addWidget(title)

        subtitle = BodyLabel("更快的开发、更稳的部署、更顺畅的远程协作")
        subtitle.setStyleSheet(f"font-size: {FontManager.get_font_size('subtitle')}px; color: #50606D;")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        highlight = CaptionLabel("一体化工具链 · 远程终端 · FTP 文件管理")
        highlight.setStyleSheet("color: #14866D; font-size: 12px; letter-spacing: 1px;")
        layout.addWidget(highlight)

        image_label = HeroImageLabel()
        image_path = os.path.join(get_program_dir(), "assets", "login_hero.png")
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                image_label.set_source(pixmap)
        else:
            image_label.setText("此处可放置一张更具冲击力的项目主视觉图")
            image_label.setStyleSheet("color: rgba(0, 0, 0, 0.45);")
        layout.addWidget(image_label, 1)

        tip = CaptionLabel("首次使用请先注册，邀请码请联系管理员获取。")
        tip.setStyleSheet("color: rgba(0, 0, 0, 0.45); font-size: 11px;")
        layout.addWidget(tip)

        return panel


    def _create_form_panel(self):
        panel = CardWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        title = StrongBodyLabel("欢迎使用")
        title.setStyleSheet(f"font-size: {FontManager.get_font_size('large_title')}px; color: #1F2D3D;")
        layout.addWidget(title)

        desc = BodyLabel("请先登录或注册账号后继续")
        desc.setStyleSheet("color: #6B7C88;")
        layout.addWidget(desc)

        toggle_layout = QHBoxLayout()
        toggle_layout.setSpacing(10)

        self.login_tab_btn = PushButton("登录")
        self.register_tab_btn = PushButton("注册")
        for btn in (self.login_tab_btn, self.register_tab_btn):
            btn.setFixedHeight(36)
            btn.setStyleSheet("""
                PushButton {
                    border-radius: 18px;
                    padding: 6px 18px;
                    border: 1px solid rgba(0, 0, 0, 0.12);
                    color: #50606D;
                    background-color: rgba(255, 255, 255, 0.8);
                }
                PushButton[active="true"] {
                    background-color: #14866D;
                    border: 1px solid #14866D;
                    color: white;
                }
            """)
        self.login_tab_btn.clicked.connect(lambda: self._set_mode("login"))
        self.register_tab_btn.clicked.connect(lambda: self._set_mode("register"))
        toggle_layout.addWidget(self.login_tab_btn)
        toggle_layout.addWidget(self.register_tab_btn)
        toggle_layout.addStretch()
        layout.addLayout(toggle_layout)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._create_login_form())
        self.stack.addWidget(self._create_register_form())
        layout.addWidget(self.stack, 1)

        return panel

    def _create_login_form(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(14)
        layout.setContentsMargins(0, 0, 0, 0)

        self.login_user = LineEdit()
        self.login_user.setPlaceholderText("用户名")
        self.login_user.setFixedHeight(40)
        layout.addWidget(self.login_user)

        self.login_pass = LineEdit()
        self.login_pass.setPlaceholderText("密码")
        self.login_pass.setEchoMode(LineEdit.Password)
        self.login_pass.setFixedHeight(40)
        layout.addWidget(self.login_pass)

        self.login_btn = PrimaryPushButton("登录并进入")
        self.login_btn.setFixedHeight(42)
        self.login_btn.clicked.connect(self._handle_login)
        layout.addWidget(self.login_btn)

        hint = CaptionLabel("首次使用请先注册账号")
        hint.setStyleSheet("color: #6B7C88;")
        layout.addWidget(hint)
        layout.addStretch()

        self.login_pass.returnPressed.connect(self._handle_login)
        self.login_user.returnPressed.connect(self._handle_login)
        return container

    def _create_register_form(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(14)
        layout.setContentsMargins(0, 0, 0, 0)

        self.reg_user = LineEdit()
        self.reg_user.setPlaceholderText("用户名")
        self.reg_user.setFixedHeight(40)
        layout.addWidget(self.reg_user)

        self.reg_pass = LineEdit()
        self.reg_pass.setPlaceholderText("密码")
        self.reg_pass.setEchoMode(LineEdit.Password)
        self.reg_pass.setFixedHeight(40)
        layout.addWidget(self.reg_pass)

        self.reg_pass_confirm = LineEdit()
        self.reg_pass_confirm.setPlaceholderText("确认密码")
        self.reg_pass_confirm.setEchoMode(LineEdit.Password)
        self.reg_pass_confirm.setFixedHeight(40)
        layout.addWidget(self.reg_pass_confirm)

        self.reg_invite = LineEdit()
        self.reg_invite.setPlaceholderText("16位邀请码")
        self.reg_invite.setFixedHeight(40)
        layout.addWidget(self.reg_invite)

        invite_hint = CaptionLabel("邀请码需与管理员提供的固定码一致")
        invite_hint.setStyleSheet("color: #6B7C88;")
        layout.addWidget(invite_hint)

        self.register_btn = PrimaryPushButton("注册账号")
        self.register_btn.setFixedHeight(42)
        self.register_btn.clicked.connect(self._handle_register)
        layout.addWidget(self.register_btn)
        layout.addStretch()

        self.reg_invite.returnPressed.connect(self._handle_register)
        return container

    def _set_mode(self, mode):
        if mode == "login":
            self.stack.setCurrentIndex(0)
            self.login_tab_btn.setProperty("active", True)
            self.register_tab_btn.setProperty("active", False)
        else:
            self.stack.setCurrentIndex(1)
            self.login_tab_btn.setProperty("active", False)
            self.register_tab_btn.setProperty("active", True)
        self.login_tab_btn.style().unpolish(self.login_tab_btn)
        self.login_tab_btn.style().polish(self.login_tab_btn)
        self.register_tab_btn.style().unpolish(self.register_tab_btn)
        self.register_tab_btn.style().polish(self.register_tab_btn)

    def _handle_login(self):
        username = self.login_user.text().strip()
        password = self.login_pass.text()
        success, message = self.auth_manager.authenticate(username, password)
        if not success:
            InfoBar.error("登录失败", message, duration=2500, parent=self)
            return
        InfoBar.success("登录成功", "欢迎进入系统管理工具", duration=1800, parent=self)
        self.login_success.emit(username)

    def _handle_register(self):
        username = self.reg_user.text().strip()
        password = self.reg_pass.text()
        confirm = self.reg_pass_confirm.text()
        invite = self.reg_invite.text().strip()
        if password != confirm:
            InfoBar.warning("提示", "两次输入的密码不一致", duration=2200, parent=self)
            return
        success, message = self.auth_manager.register_user(username, password, invite)
        if not success:
            InfoBar.error("注册失败", message, duration=2500, parent=self)
            return
        InfoBar.success("注册成功", "请使用新账号登录", duration=2000, parent=self)
        self.login_user.setText(username)
        self.login_pass.setText("")
        self._set_mode("login")

class HeroImageLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._source = None
        self.setMinimumHeight(320)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background: transparent;")

    def set_source(self, pixmap):
        self._source = pixmap
        self._update_pixmap()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_pixmap()

    def _update_pixmap(self):
        if self._source is None or self.size().isEmpty():
            return
        scaled = self._source.scaled(
            self.size(),
            Qt.KeepAspectRatioByExpanding,
            Qt.SmoothTransformation
        )
        self.setPixmap(scaled)

