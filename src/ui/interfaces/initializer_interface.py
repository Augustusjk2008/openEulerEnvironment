import os
import sys
import time
import datetime
from pathlib import Path
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFileDialog
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from qfluentwidgets import (PushButton, TextEdit, TitleLabel, SubtitleLabel,
                            StrongBodyLabel, CardWidget, CheckBox, InfoBar, InfoBarPosition)
from core.config_manager import get_config_manager, get_program_dir
from core.font_manager import FontManager
from core.ssh_utils import SSHConfig, SFTPTransferWorker, SSHCommandWorker


class InitializerInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("initializerInterface")
        self.config_manager = get_config_manager()
        self.local_project_path = ""
        self.worker = None
        self.upload_worker = None
        self.init_ui()
        # 初始化时自动设置默认路径
        self._set_default_path()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # 标题部分
        title_card = CardWidget(self)
        title_layout = QVBoxLayout(title_card)
        self.title_label = TitleLabel('CCU系统出厂初始化工具', title_card)
        self.title_label.setStyleSheet(
            f"font-size: {FontManager.get_font_size('large_title')}px; color: #2D3748;"
        )
        self.status_label = SubtitleLabel('准备就绪', title_card)
        self.status_label.setTextColor("#2196F3", "#2196F3")
        title_layout.addWidget(self.title_label)
        title_layout.addWidget(self.status_label)
        layout.addWidget(title_card)

        # 设置部分
        config_card = CardWidget(self)
        config_layout = QVBoxLayout(config_card)

        path_layout = QHBoxLayout()
        self.path_display = StrongBodyLabel("未选择项目路径", config_card)
        self.browse_button = PushButton('浏览项目目录', config_card)
        self.browse_button.clicked.connect(self.browse_project_path)
        path_layout.addWidget(self.path_display)
        path_layout.addStretch(1)
        path_layout.addWidget(self.browse_button)

        self.upload_checkbox = CheckBox("执行文件上传步骤", config_card)
        self.upload_checkbox.setChecked(True)

        config_layout.addLayout(path_layout)
        config_layout.addWidget(self.upload_checkbox)
        layout.addWidget(config_card)

        # 操作按钮
        button_layout = QHBoxLayout()
        self.one_click_button = PushButton('一键初始化', self)
        self.one_click_button.clicked.connect(self.one_click_initialization)

        self.clear_button = PushButton('清空日志', self)
        self.clear_button.clicked.connect(self.clear_log)

        button_layout.addWidget(self.one_click_button)
        button_layout.addStretch(1)
        button_layout.addWidget(self.clear_button)
        layout.addLayout(button_layout)

        # 日志显示
        self.log_text = TextEdit(self)
        self.log_text.setReadOnly(True)
        self.log_text.setPlaceholderText("系统日志输出...")
        layout.addWidget(self.log_text)

        self.log_message("系统出厂初始化工具已启动")

    def log_message(self, message):
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")

    def _get_program_dir(self) -> Path:
        """获取程序所在目录"""
        return Path(get_program_dir())

    def _set_default_path(self):
        """自动设置默认的上传文件夹路径"""
        program_dir = self._get_program_dir()
        default_path = program_dir / "files_to_upload"

        if default_path.exists():
            self.local_project_path = str(default_path)
            self.path_display.setText(str(default_path))
            self.log_message(f"自动定位上传文件夹: {default_path}")

    def browse_project_path(self):
        # 设置默认打开路径为程序所在目录下的 files_to_upload
        program_dir = self._get_program_dir()
        default_path = program_dir / "files_to_upload"
        start_dir = str(default_path) if default_path.exists() else str(program_dir)

        path = QFileDialog.getExistingDirectory(self, "选择项目目录", start_dir)
        if path:
            self.local_project_path = path
            self.path_display.setText(path)
            self.log_message(f"已选择项目路径: {path}")

    def clear_log(self):
        self.log_text.clear()

    def one_click_initialization(self):
        # 尝试自动定位 files_to_upload 目录
        program_dir = self._get_program_dir()
        local_path = program_dir / "references" / "openEulerReset" / "files_to_upload"
        if local_path.exists() and not self.local_project_path:
            self.local_project_path = str(local_path)
            self.path_display.setText(str(local_path))
            self.log_message(f"自动定位项目路径: {local_path}")

        if self.upload_checkbox.isChecked() and not self.local_project_path:
            InfoBar.warning("提示", "请先选择项目路径再进行一键初始化", duration=2000, parent=self.window())
            return

        self.log_message("开始一键初始化流程...")
        if self.upload_checkbox.isChecked():
            self.start_upload()
        else:
            self.start_init_commands()

    def start_upload(self):
        # 使用SSHConfig获取配置并验证
        ssh_config = SSHConfig.from_config_manager(self.config_manager, "ssh")
        is_valid, error_msg = SSHConfig.validate(ssh_config)

        if not is_valid:
            InfoBar.warning("配置缺失", f"请在设置中配置SSH连接信息: {error_msg}", duration=3000, parent=self.window())
            self.one_click_button.setEnabled(True)
            return

        # 注意：原代码中上传到 "/"，这里保持一致
        self.upload_worker = SFTPTransferWorker(
            host=ssh_config["host"],
            username=ssh_config["username"],
            password=ssh_config["password"],
            action="upload",
            local_path=self.local_project_path,
            remote_path="/",
            delete_source=False,
            timeout=30
        )
        self.upload_worker.status_updated.connect(self.status_label.setText)
        self.upload_worker.progress_updated.connect(
            lambda current, total: self.log_message(f"上传进度: {current}/{total}")
        )
        self.upload_worker.transfer_finished.connect(self.on_upload_finished)
        self.one_click_button.setEnabled(False)
        self.upload_worker.start()

    def on_upload_finished(self, success, message):
        if success:
            self.log_message("文件上传成功，进入指令初始化阶段")
            self.start_init_commands()
        else:
            self.one_click_button.setEnabled(True)
            InfoBar.error("错误", f"上传失败: {message}", duration=3000, parent=self.window())

    def start_init_commands(self):
        # 使用SSHConfig获取配置并验证
        ssh_config = SSHConfig.from_config_manager(self.config_manager, "ssh")
        is_valid, error_msg = SSHConfig.validate(ssh_config)

        if not is_valid:
            InfoBar.warning("配置缺失", f"请在设置中配置SSH连接信息: {error_msg}", duration=3000, parent=self.window())
            self.one_click_button.setEnabled(True)
            return

        # 定义完整初始化步骤
        commands = []

        # 步骤0: 配置时间
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        commands.append(("配置时间",
            f"date -s \"{current_time}\"",
            False))

        # 步骤1: 创建文件夹结构
        commands.append(("创建文件夹结构",
            "mkdir -p /home/sast8 && mkdir -p /home/sast8/user_tests && mkdir -p /home/sast8/user_apps && mkdir -p /home/sast8/user_libs && mkdir -p /home/sast8/user_libs/shared_libs && mkdir -p /home/sast8/user_libs/static_libs && mkdir -p /home/sast8/user_modules && mkdir -p /home/sast8/user_modules/resize && mkdir -p /home/sast8/user_modules/xdma_803",
            False))

        # 步骤2: 文件上传（日志记录）
        if self.upload_checkbox.isChecked() and self.local_project_path:
            commands.append(("上传文件到目标设备",
                f"echo '文件上传已完成：从 {self.local_project_path} 到设备'",
                False))

        # 步骤3: 配置动态库路径
        commands.append(("配置动态库路径",
            "cd /etc && mkdir -p ld.so.conf.d && cd ld.so.conf.d && touch sast8_libs.conf && echo '/home/sast8/user_libs/shared_libs' > /etc/ld.so.conf.d/sast8_libs.conf && ldconfig",
            False))

        # 步骤4: 硬盘扩容
        commands.append(("硬盘扩容",
            "cd /home/sast8/user_modules/resize && chmod +x resize2fs-arm64 && ./resize2fs-arm64 /dev/mmcblk0p3",
            True))

        # 步骤5: 执行安全测试
        commands.append(("执行安全测试",
            "cd /home/sast8/user_tmp && chmod +x * && ./device_hash_and_sign.sh && ./test_secure",
            True))

        # 步骤6: 清理测试文件
        commands.append(("清理测试文件",
            "cd /home/sast8/user_tmp && rm -f *",
            False))

        # 步骤7: 清理不需要的脚本
        commands.append(("清理不需要的文件",
            "rm -f /etc/volatile.cache /etc/issue.net",
            False))

        # 步骤8: root用户设置密码
        commands.append(("为root用户设置密码",
            f"echo '{ssh_config['username']}:{ssh_config['password']}' | chpasswd || echo '密码已为目标值，跳过'",
            False))

        # 步骤9: 重启系统
        commands.append(("重启系统", "reboot", False))

        self.worker = SSHCommandWorker(
            host=ssh_config["host"],
            username=ssh_config["username"],
            password=ssh_config["password"],
            commands=commands,
            timeout=30
        )
        self.worker.command_output.connect(self.log_message)
        self.worker.command_error.connect(self.log_message)
        self.worker.command_started.connect(self.status_label.setText)
        self.worker.all_finished.connect(self.on_init_finished)
        self.one_click_button.setEnabled(False)
        self.worker.start()

    def on_init_finished(self, success, message):
        self.one_click_button.setEnabled(True)
        if success:
            self.status_label.setText("初始化完成")
            InfoBar.success("完成", "系统出厂初始化已完成！", duration=5000, parent=self.window())
        else:
            InfoBar.error("失败", f"初始化过程中出错: {message}", duration=3000, parent=self.window())
