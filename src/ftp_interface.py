"""
FTP 客户端界面
用于在本地与远端之间浏览、上传、下载与移动文件
"""

import os
import posixpath
import shutil
import stat
import time
import paramiko
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject, pyqtSlot
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QInputDialog, QMessageBox
)
from qfluentwidgets import (
    CardWidget, SubtitleLabel, BodyLabel, StrongBodyLabel, CaptionLabel,
    LineEdit, PushButton, PrimaryPushButton, FluentIcon as FIF, IconWidget,
    InfoBar
)
from config_manager import get_config_manager
from font_manager import FontManager


class SftpConnectWorker(QObject):
    connected = pyqtSignal(object, object)
    failed = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, host, username, password, timeout=10):
        super().__init__()
        self.host = host
        self.username = username
        self.password = password
        self.timeout = timeout

    @pyqtSlot()
    def run(self):
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        connect_kwargs = {
            "hostname": self.host,
            "username": self.username,
            "timeout": self.timeout,
        }
        if self.password:
            connect_kwargs.update({
                "password": self.password,
                "look_for_keys": False,
                "allow_agent": False,
            })
        try:
            client.connect(**connect_kwargs)
            sftp = client.open_sftp()
            self.connected.emit(client, sftp)
        except Exception as exc:
            client.close()
            self.failed.emit(str(exc))
        finally:
            self.finished.emit()


class TransferWorker(QThread):
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, host, username, password, action, local_path, remote_path, delete_source=False):
        super().__init__()
        self.host = host
        self.username = username
        self.password = password
        self.action = action
        self.local_path = local_path
        self.remote_path = remote_path
        self.delete_source = delete_source

    def run(self):
        ssh = None
        sftp = None
        try:
            ssh = paramiko.SSHClient()
            ssh.load_system_host_keys()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            connect_kwargs = {
                "hostname": self.host,
                "username": self.username,
                "timeout": 30,
            }
            if self.password:
                connect_kwargs.update({
                    "password": self.password,
                    "look_for_keys": False,
                    "allow_agent": False,
                })
            ssh.connect(**connect_kwargs)
            sftp = ssh.open_sftp()

            if self.action == "upload":
                self._upload(sftp, self.local_path, self.remote_path)
                if self.delete_source:
                    self._delete_local(self.local_path)
            elif self.action == "download":
                self._download(sftp, self.remote_path, self.local_path)
                if self.delete_source:
                    self._delete_remote(sftp, self.remote_path)
            else:
                raise ValueError("未知传输类型")

            self.finished_signal.emit(True, "传输完成")
        except Exception as exc:
            self.finished_signal.emit(False, f"传输失败: {exc}")
        finally:
            if sftp is not None:
                sftp.close()
            if ssh is not None:
                ssh.close()

    def _ensure_remote_dir(self, sftp, remote_path):
        if remote_path in ("", "/"):
            return
        parts = remote_path.strip("/").split("/")
        current = ""
        for part in parts:
            current = f"{current}/{part}" if current else f"/{part}"
            try:
                sftp.stat(current)
            except Exception:
                sftp.mkdir(current)

    def _upload(self, sftp, local_path, remote_path):
        if os.path.isdir(local_path):
            self._ensure_remote_dir(sftp, remote_path)
            for root, _, files in os.walk(local_path):
                rel = os.path.relpath(root, local_path)
                rel = "" if rel == "." else rel.replace("\\", "/")
                target_dir = remote_path if not rel else posixpath.join(remote_path, rel)
                self._ensure_remote_dir(sftp, target_dir)
                for filename in files:
                    local_file = os.path.join(root, filename)
                    remote_file = posixpath.join(target_dir, filename)
                    sftp.put(local_file, remote_file)
        else:
            remote_dir = posixpath.dirname(remote_path)
            self._ensure_remote_dir(sftp, remote_dir)
            sftp.put(local_path, remote_path)

    def _download(self, sftp, remote_path, local_path):
        info = sftp.stat(remote_path)
        if stat.S_ISDIR(info.st_mode):
            os.makedirs(local_path, exist_ok=True)
            for entry in sftp.listdir_attr(remote_path):
                remote_child = posixpath.join(remote_path, entry.filename)
                local_child = os.path.join(local_path, entry.filename)
                if stat.S_ISDIR(entry.st_mode):
                    self._download(sftp, remote_child, local_child)
                else:
                    os.makedirs(os.path.dirname(local_child), exist_ok=True)
                    sftp.get(remote_child, local_child)
        else:
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            sftp.get(remote_path, local_path)

    def _delete_remote(self, sftp, remote_path):
        try:
            info = sftp.stat(remote_path)
        except Exception:
            return
        if stat.S_ISDIR(info.st_mode):
            for entry in sftp.listdir_attr(remote_path):
                child = posixpath.join(remote_path, entry.filename)
                if stat.S_ISDIR(entry.st_mode):
                    self._delete_remote(sftp, child)
                else:
                    sftp.remove(child)
            sftp.rmdir(remote_path)
        else:
            sftp.remove(remote_path)

    def _delete_local(self, local_path):
        if os.path.isdir(local_path):
            shutil.rmtree(local_path)
        else:
            os.remove(local_path)


class FtpInterface(QWidget):
    """FTP 客户端界面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ftpInterface")
        self.config_manager = get_config_manager()
        self.ssh_client = None
        self.sftp = None
        self._connect_thread = None
        self._connect_worker = None
        self._transfer_worker = None
        self._transfer_context = None
        self.local_dir = os.path.expanduser("~")
        self.remote_dir = "/"

        self._init_ui()
        self._load_defaults()
        self._refresh_local_list()
        self._set_remote_controls_enabled(False)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(20)

        title = SubtitleLabel("FTP 客户端")
        title.setStyleSheet(f"color: #2D3748; font-size: {FontManager.get_font_size('large_title')}px;")
        layout.addWidget(title)

        desc = BodyLabel("支持本地与远端之间的文件浏览、上传、下载与移动")
        desc.setStyleSheet(f"color: #5A6A7A; font-size: {FontManager.get_font_size('body')}px;")
        layout.addWidget(desc)

        connection_card = self._create_connection_card()
        layout.addWidget(connection_card)

        browser_card = self._create_browser_card()
        layout.addWidget(browser_card, 1)

    def _create_connection_card(self):
        card = CardWidget()
        card.setStyleSheet("""
            CardWidget {
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 12px;
                border: 1px solid rgba(0, 0, 0, 0.06);
            }
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(12)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        icon = IconWidget(FIF.FOLDER)
        icon.setFixedSize(28, 28)
        header_layout.addWidget(icon)

        title = StrongBodyLabel("连接信息")
        title.setStyleSheet(f"font-size: {FontManager.get_font_size('title')}px; color: #2D3748;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        self.status_label = CaptionLabel("FTP 未连接")
        self.status_label.setStyleSheet(f"color: #D83B01; font-size: {FontManager.get_font_size('caption')}px;")
        header_layout.addWidget(self.status_label)

        layout.addLayout(header_layout)

        grid = QGridLayout()
        grid.setSpacing(12)
        grid.setColumnStretch(1, 1)

        host_label = BodyLabel("主机地址:")
        host_label.setStyleSheet(f"font-size: {FontManager.get_font_size('body')}px; color: #2D3748;")
        grid.addWidget(host_label, 0, 0)

        self.host_edit = LineEdit()
        self.host_edit.setFixedHeight(36)
        self.host_edit.setPlaceholderText("例如: 192.168.137.100")
        grid.addWidget(self.host_edit, 0, 1)

        user_label = BodyLabel("用户名:")
        user_label.setStyleSheet(f"font-size: {FontManager.get_font_size('body')}px; color: #2D3748;")
        grid.addWidget(user_label, 1, 0)

        self.user_edit = LineEdit()
        self.user_edit.setFixedHeight(36)
        self.user_edit.setPlaceholderText("例如: root")
        grid.addWidget(self.user_edit, 1, 1)

        pass_label = BodyLabel("密码:")
        pass_label.setStyleSheet(f"font-size: {FontManager.get_font_size('body')}px; color: #2D3748;")
        grid.addWidget(pass_label, 2, 0)

        self.pass_edit = LineEdit()
        self.pass_edit.setFixedHeight(36)
        self.pass_edit.setPlaceholderText("FTP 登录密码")
        self.pass_edit.setEchoMode(LineEdit.Password)
        grid.addWidget(self.pass_edit, 2, 1)

        layout.addLayout(grid)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)

        self.connect_btn = PrimaryPushButton("连接 FTP")
        self.connect_btn.setFixedHeight(36)
        self.connect_btn.clicked.connect(self._on_connect_clicked)
        button_layout.addWidget(self.connect_btn)

        self.disconnect_btn = PushButton("断开连接")
        self.disconnect_btn.setFixedHeight(36)
        self.disconnect_btn.clicked.connect(self._on_disconnect_clicked)
        button_layout.addWidget(self.disconnect_btn)

        self.save_btn = PushButton("保存为默认")
        self.save_btn.setFixedHeight(36)
        self.save_btn.clicked.connect(self._save_connection_settings)
        button_layout.addWidget(self.save_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        self.transfer_label = CaptionLabel("就绪")
        self.transfer_label.setStyleSheet(f"color: #7A8A9A; font-size: {FontManager.get_font_size('caption')}px;")
        layout.addWidget(self.transfer_label)

        return card

    def _create_browser_card(self):
        card = CardWidget()
        card.setStyleSheet("""
            CardWidget {
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 12px;
                border: 1px solid rgba(0, 0, 0, 0.06);
            }
        """)

        layout = QHBoxLayout(card)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(20)

        local_panel = self._create_local_panel()
        transfer_panel = self._create_transfer_panel()
        remote_panel = self._create_remote_panel()

        layout.addLayout(local_panel, 2)
        layout.addLayout(transfer_panel)
        layout.addLayout(remote_panel, 2)
        return card

    def _create_local_panel(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)

        title = StrongBodyLabel("本地文件")
        title.setStyleSheet(f"font-size: {FontManager.get_font_size('title')}px; color: #2D3748;")
        layout.addWidget(title)

        path_layout = QHBoxLayout()
        path_layout.setSpacing(8)

        self.local_path_edit = LineEdit()
        self.local_path_edit.setFixedHeight(32)
        self.local_path_edit.returnPressed.connect(self._on_local_path_entered)
        path_layout.addWidget(self.local_path_edit)

        self.local_browse_btn = PushButton("浏览...")
        self.local_browse_btn.setFixedHeight(32)
        self.local_browse_btn.clicked.connect(self._browse_local_dir)
        path_layout.addWidget(self.local_browse_btn)

        self.local_up_btn = PushButton("上一级")
        self.local_up_btn.setFixedHeight(32)
        self.local_up_btn.clicked.connect(self._local_go_up)
        path_layout.addWidget(self.local_up_btn)

        self.local_refresh_btn = PushButton("刷新")
        self.local_refresh_btn.setFixedHeight(32)
        self.local_refresh_btn.clicked.connect(self._refresh_local_list)
        path_layout.addWidget(self.local_refresh_btn)

        layout.addLayout(path_layout)

        self.local_table = self._create_file_table()
        self.local_table.cellDoubleClicked.connect(self._on_local_item_double_clicked)
        layout.addWidget(self.local_table, 1)

        local_actions = QHBoxLayout()
        local_actions.setSpacing(8)

        self.local_mkdir_btn = PushButton("新建文件夹")
        self.local_mkdir_btn.setFixedHeight(32)
        self.local_mkdir_btn.clicked.connect(self._local_mkdir)
        local_actions.addWidget(self.local_mkdir_btn)

        self.local_rename_btn = PushButton("重命名")
        self.local_rename_btn.setFixedHeight(32)
        self.local_rename_btn.clicked.connect(self._local_rename)
        local_actions.addWidget(self.local_rename_btn)

        self.local_delete_btn = PushButton("删除")
        self.local_delete_btn.setFixedHeight(32)
        self.local_delete_btn.clicked.connect(self._local_delete)
        local_actions.addWidget(self.local_delete_btn)

        local_actions.addStretch()
        layout.addLayout(local_actions)

        return layout

    def _create_transfer_panel(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.addStretch()

        self.upload_btn = PrimaryPushButton("上传 →")
        self.upload_btn.setFixedWidth(120)
        self.upload_btn.setFixedHeight(36)
        self.upload_btn.clicked.connect(self._upload_selected)
        layout.addWidget(self.upload_btn)

        self.download_btn = PrimaryPushButton("← 下载")
        self.download_btn.setFixedWidth(120)
        self.download_btn.setFixedHeight(36)
        self.download_btn.clicked.connect(self._download_selected)
        layout.addWidget(self.download_btn)

        self.move_to_remote_btn = PushButton("移动到远端")
        self.move_to_remote_btn.setFixedWidth(120)
        self.move_to_remote_btn.setFixedHeight(36)
        self.move_to_remote_btn.clicked.connect(self._move_to_remote)
        layout.addWidget(self.move_to_remote_btn)

        self.move_to_local_btn = PushButton("移动到本地")
        self.move_to_local_btn.setFixedWidth(120)
        self.move_to_local_btn.setFixedHeight(36)
        self.move_to_local_btn.clicked.connect(self._move_to_local)
        layout.addWidget(self.move_to_local_btn)

        layout.addStretch()
        self._transfer_buttons = [
            self.upload_btn,
            self.download_btn,
            self.move_to_remote_btn,
            self.move_to_local_btn,
        ]
        return layout

    def _create_remote_panel(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)

        title = StrongBodyLabel("远端文件")
        title.setStyleSheet(f"font-size: {FontManager.get_font_size('title')}px; color: #2D3748;")
        layout.addWidget(title)

        path_layout = QHBoxLayout()
        path_layout.setSpacing(8)

        self.remote_path_edit = LineEdit()
        self.remote_path_edit.setFixedHeight(32)
        self.remote_path_edit.returnPressed.connect(self._on_remote_path_entered)
        path_layout.addWidget(self.remote_path_edit)

        self.remote_enter_btn = PushButton("进入")
        self.remote_enter_btn.setFixedHeight(32)
        self.remote_enter_btn.clicked.connect(self._on_remote_path_entered)
        path_layout.addWidget(self.remote_enter_btn)

        self.remote_up_btn = PushButton("上一级")
        self.remote_up_btn.setFixedHeight(32)
        self.remote_up_btn.clicked.connect(self._remote_go_up)
        path_layout.addWidget(self.remote_up_btn)

        self.remote_refresh_btn = PushButton("刷新")
        self.remote_refresh_btn.setFixedHeight(32)
        self.remote_refresh_btn.clicked.connect(self._refresh_remote_list)
        path_layout.addWidget(self.remote_refresh_btn)

        layout.addLayout(path_layout)

        self.remote_table = self._create_file_table()
        self.remote_table.cellDoubleClicked.connect(self._on_remote_item_double_clicked)
        layout.addWidget(self.remote_table, 1)

        remote_actions = QHBoxLayout()
        remote_actions.setSpacing(8)

        self.remote_mkdir_btn = PushButton("新建文件夹")
        self.remote_mkdir_btn.setFixedHeight(32)
        self.remote_mkdir_btn.clicked.connect(self._remote_mkdir)
        remote_actions.addWidget(self.remote_mkdir_btn)

        self.remote_rename_btn = PushButton("重命名")
        self.remote_rename_btn.setFixedHeight(32)
        self.remote_rename_btn.clicked.connect(self._remote_rename)
        remote_actions.addWidget(self.remote_rename_btn)

        self.remote_delete_btn = PushButton("删除")
        self.remote_delete_btn.setFixedHeight(32)
        self.remote_delete_btn.clicked.connect(self._remote_delete)
        remote_actions.addWidget(self.remote_delete_btn)

        remote_actions.addStretch()
        layout.addLayout(remote_actions)

        self._remote_controls = [
            self.remote_path_edit,
            self.remote_enter_btn,
            self.remote_up_btn,
            self.remote_refresh_btn,
            self.remote_table,
            self.remote_mkdir_btn,
            self.remote_rename_btn,
            self.remote_delete_btn,
        ]
        return layout

    def _create_file_table(self):
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["名称", "类型", "大小", "修改时间"])
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setAlternatingRowColors(True)
        return table

    def _load_defaults(self):
        self.host_edit.setText(self.config_manager.get("ftp_host", "192.168.137.100"))
        self.user_edit.setText(self.config_manager.get("ftp_username", "root"))
        self.pass_edit.setText(self.config_manager.get("ftp_password", "Shanghaith8"))
        self.local_path_edit.setText(self.local_dir)
        self.remote_path_edit.setText(self.remote_dir)

    def _save_connection_settings(self):
        self.config_manager.set("ftp_host", self.host_edit.text().strip())
        self.config_manager.set("ftp_username", self.user_edit.text().strip())
        self.config_manager.set("ftp_password", self.pass_edit.text())
        InfoBar.success("已保存", "FTP 连接配置已保存为默认值", duration=2000, parent=self.window())

    def _set_remote_controls_enabled(self, enabled):
        for widget in self._remote_controls:
            widget.setEnabled(enabled)
        for button in self._transfer_buttons:
            button.setEnabled(enabled)
        self.disconnect_btn.setEnabled(enabled)

    def _set_transfer_in_progress(self, in_progress, message=""):
        for button in self._transfer_buttons:
            button.setEnabled(not in_progress)
        if in_progress:
            self.transfer_label.setText(message or "传输中...")
            self.transfer_label.setStyleSheet(f"color: #D97706; font-size: {FontManager.get_font_size('caption')}px;")
        else:
            self.transfer_label.setText("就绪")
            self.transfer_label.setStyleSheet(f"color: #7A8A9A; font-size: {FontManager.get_font_size('caption')}px;")

    def _on_connect_clicked(self):
        host = self.host_edit.text().strip()
        username = self.user_edit.text().strip()
        password = self.pass_edit.text()

        if not host or not username:
            InfoBar.warning("提示", "请填写完整的 FTP 连接信息", duration=2000, parent=self.window())
            return

        if self._connect_thread is not None:
            return

        self.status_label.setText("FTP 连接中...")
        self.status_label.setStyleSheet(f"color: #D97706; font-size: {FontManager.get_font_size('caption')}px;")

        thread = QThread(self)
        worker = SftpConnectWorker(host, username, password)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.connected.connect(self._on_connect_success)
        worker.failed.connect(self._on_connect_failed)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._on_connect_thread_finished)
        self._connect_thread = thread
        self._connect_worker = worker
        thread.start()

    def _on_connect_thread_finished(self):
        self._connect_thread = None
        self._connect_worker = None

    def _on_connect_success(self, ssh_client, sftp):
        self.ssh_client = ssh_client
        self.sftp = sftp
        self.status_label.setText("FTP 已连接")
        self.status_label.setStyleSheet(f"color: #107C10; font-size: {FontManager.get_font_size('caption')}px;")
        self._set_remote_controls_enabled(True)
        self._refresh_remote_list()

    def _on_connect_failed(self, message):
        self.status_label.setText("FTP 连接失败")
        self.status_label.setStyleSheet(f"color: #D83B01; font-size: {FontManager.get_font_size('caption')}px;")
        InfoBar.error("连接失败", f"无法连接 FTP: {message}", duration=4000, parent=self.window())

    def _on_disconnect_clicked(self):
        self._disconnect()

    def _disconnect(self):
        if self.sftp is not None:
            try:
                self.sftp.close()
            except Exception:
                pass
        if self.ssh_client is not None:
            try:
                self.ssh_client.close()
            except Exception:
                pass
        self.sftp = None
        self.ssh_client = None
        self.status_label.setText("FTP 未连接")
        self.status_label.setStyleSheet(f"color: #D83B01; font-size: {FontManager.get_font_size('caption')}px;")
        self._clear_table(self.remote_table)
        self._set_remote_controls_enabled(False)

    def _normalize_remote_path(self, path):
        if not path:
            return "/"
        path = path.replace("\\", "/")
        normalized = posixpath.normpath(path)
        if normalized in (".", ""):
            normalized = "/"
        if not normalized.startswith("/"):
            normalized = f"/{normalized}"
        return normalized

    def _on_local_path_entered(self):
        path = self.local_path_edit.text().strip()
        self._set_local_path(path)

    def _on_remote_path_entered(self):
        if self.sftp is None:
            return
        path = self.remote_path_edit.text().strip()
        self._set_remote_path(path)

    def _set_local_path(self, path):
        if not path:
            return
        path = os.path.abspath(os.path.expanduser(path))
        if not os.path.isdir(path):
            InfoBar.warning("提示", "本地目录不存在", duration=2000, parent=self.window())
            self.local_path_edit.setText(self.local_dir)
            return
        self.local_dir = path
        self.local_path_edit.setText(path)
        self._refresh_local_list()

    def _set_remote_path(self, path):
        if self.sftp is None:
            return
        normalized = self._normalize_remote_path(path)
        try:
            info = self.sftp.stat(normalized)
            if not stat.S_ISDIR(info.st_mode):
                raise ValueError("目标不是目录")
        except Exception:
            InfoBar.warning("提示", "远端目录不存在", duration=2000, parent=self.window())
            self.remote_path_edit.setText(self.remote_dir)
            return
        self.remote_dir = normalized
        self.remote_path_edit.setText(normalized)
        self._refresh_remote_list()

    def _browse_local_dir(self):
        directory = QFileDialog.getExistingDirectory(
            self, "选择本地目录", self.local_dir
        )
        if directory:
            self._set_local_path(directory)

    def _local_go_up(self):
        parent = os.path.dirname(self.local_dir.rstrip("\\/"))
        if parent and os.path.isdir(parent):
            self._set_local_path(parent)

    def _remote_go_up(self):
        if self.sftp is None:
            return
        parent = posixpath.dirname(self.remote_dir.rstrip("/"))
        if not parent:
            parent = "/"
        self._set_remote_path(parent)

    def _format_size(self, size):
        if size is None:
            return "-"
        units = ["B", "KB", "MB", "GB", "TB"]
        value = float(size)
        for unit in units:
            if value < 1024 or unit == units[-1]:
                return f"{value:.1f} {unit}"
            value /= 1024
        return f"{value:.1f} TB"

    def _refresh_local_list(self):
        try:
            entries = []
            for entry in os.scandir(self.local_dir):
                info = {
                    "name": entry.name,
                    "is_dir": entry.is_dir(),
                    "size": None if entry.is_dir() else entry.stat().st_size,
                    "mtime": entry.stat().st_mtime,
                }
                entries.append(info)
            entries.sort(key=lambda item: (not item["is_dir"], item["name"].lower()))
            self._populate_table(self.local_table, entries)
        except Exception as exc:
            InfoBar.error("刷新失败", f"无法读取本地目录: {exc}", duration=3000, parent=self.window())

    def _refresh_remote_list(self):
        if self.sftp is None:
            self._clear_table(self.remote_table)
            return
        try:
            entries = []
            for entry in self.sftp.listdir_attr(self.remote_dir):
                info = {
                    "name": entry.filename,
                    "is_dir": stat.S_ISDIR(entry.st_mode),
                    "size": None if stat.S_ISDIR(entry.st_mode) else entry.st_size,
                    "mtime": entry.st_mtime,
                }
                entries.append(info)
            entries.sort(key=lambda item: (not item["is_dir"], item["name"].lower()))
            self._populate_table(self.remote_table, entries)
        except Exception as exc:
            InfoBar.error("刷新失败", f"无法读取远端目录: {exc}", duration=3000, parent=self.window())

    def _populate_table(self, table, entries):
        table.setRowCount(len(entries))
        for row, item in enumerate(entries):
            name_item = QTableWidgetItem(item["name"])
            name_item.setData(Qt.UserRole, item)
            if item["is_dir"]:
                font = name_item.font()
                font.setBold(True)
                name_item.setFont(font)

            type_item = QTableWidgetItem("文件夹" if item["is_dir"] else "文件")
            size_item = QTableWidgetItem(self._format_size(item["size"]))
            size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            mtime = time.strftime("%Y-%m-%d %H:%M", time.localtime(item["mtime"]))
            time_item = QTableWidgetItem(mtime)

            table.setItem(row, 0, name_item)
            table.setItem(row, 1, type_item)
            table.setItem(row, 2, size_item)
            table.setItem(row, 3, time_item)

    def _clear_table(self, table):
        table.setRowCount(0)

    def _on_local_item_double_clicked(self, row, _column):
        item = self.local_table.item(row, 0)
        if not item:
            return
        data = item.data(Qt.UserRole) or {}
        if data.get("is_dir"):
            target = os.path.join(self.local_dir, data["name"])
            self._set_local_path(target)

    def _on_remote_item_double_clicked(self, row, _column):
        if self.sftp is None:
            return
        item = self.remote_table.item(row, 0)
        if not item:
            return
        data = item.data(Qt.UserRole) or {}
        if data.get("is_dir"):
            target = self._normalize_remote_path(posixpath.join(self.remote_dir, data["name"]))
            self._set_remote_path(target)

    def _get_selected_local_item(self):
        row = self.local_table.currentRow()
        if row < 0:
            InfoBar.warning("提示", "请先选择本地文件", duration=2000, parent=self.window())
            return None
        data = self.local_table.item(row, 0).data(Qt.UserRole)
        if not data:
            return None
        full_path = os.path.join(self.local_dir, data["name"])
        return data, full_path

    def _get_selected_remote_item(self):
        if self.sftp is None:
            InfoBar.warning("提示", "请先连接 FTP", duration=2000, parent=self.window())
            return None
        row = self.remote_table.currentRow()
        if row < 0:
            InfoBar.warning("提示", "请先选择远端文件", duration=2000, parent=self.window())
            return None
        data = self.remote_table.item(row, 0).data(Qt.UserRole)
        if not data:
            return None
        full_path = self._normalize_remote_path(posixpath.join(self.remote_dir, data["name"]))
        return data, full_path

    def _local_mkdir(self):
        name, ok = QInputDialog.getText(self, "新建文件夹", "请输入文件夹名称:")
        if not ok or not name:
            return
        path = os.path.join(self.local_dir, name)
        try:
            os.makedirs(path, exist_ok=False)
            self._refresh_local_list()
        except Exception as exc:
            InfoBar.error("创建失败", f"无法创建本地文件夹: {exc}", duration=3000, parent=self.window())

    def _remote_mkdir(self):
        if self.sftp is None:
            return
        name, ok = QInputDialog.getText(self, "新建文件夹", "请输入文件夹名称:")
        if not ok or not name:
            return
        path = self._normalize_remote_path(posixpath.join(self.remote_dir, name))
        try:
            self.sftp.mkdir(path)
            self._refresh_remote_list()
        except Exception as exc:
            InfoBar.error("创建失败", f"无法创建远端文件夹: {exc}", duration=3000, parent=self.window())

    def _local_rename(self):
        selected = self._get_selected_local_item()
        if not selected:
            return
        data, full_path = selected
        name, ok = QInputDialog.getText(self, "重命名", "请输入新的名称:", text=data["name"])
        if not ok or not name or name == data["name"]:
            return
        target = os.path.join(self.local_dir, name)
        try:
            os.rename(full_path, target)
            self._refresh_local_list()
        except Exception as exc:
            InfoBar.error("重命名失败", f"无法重命名本地文件: {exc}", duration=3000, parent=self.window())

    def _remote_rename(self):
        selected = self._get_selected_remote_item()
        if not selected:
            return
        data, full_path = selected
        name, ok = QInputDialog.getText(self, "重命名", "请输入新的名称:", text=data["name"])
        if not ok or not name or name == data["name"]:
            return
        target = self._normalize_remote_path(posixpath.join(self.remote_dir, name))
        try:
            self.sftp.rename(full_path, target)
            self._refresh_remote_list()
        except Exception as exc:
            InfoBar.error("重命名失败", f"无法重命名远端文件: {exc}", duration=3000, parent=self.window())

    def _local_delete(self):
        selected = self._get_selected_local_item()
        if not selected:
            return
        data, full_path = selected
        reply = QMessageBox.question(
            self, "确认删除", f"确认删除本地{'文件夹' if data['is_dir'] else '文件'}: {data['name']}?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        try:
            if data["is_dir"]:
                shutil.rmtree(full_path)
            else:
                os.remove(full_path)
            self._refresh_local_list()
        except Exception as exc:
            InfoBar.error("删除失败", f"无法删除本地文件: {exc}", duration=3000, parent=self.window())

    def _remote_delete(self):
        selected = self._get_selected_remote_item()
        if not selected:
            return
        data, full_path = selected
        reply = QMessageBox.question(
            self, "确认删除", f"确认删除远端{'文件夹' if data['is_dir'] else '文件'}: {data['name']}?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        try:
            self._delete_remote_path(full_path, data["is_dir"])
            self._refresh_remote_list()
        except Exception as exc:
            InfoBar.error("删除失败", f"无法删除远端文件: {exc}", duration=3000, parent=self.window())

    def _delete_remote_path(self, path, is_dir):
        if self.sftp is None:
            return
        if is_dir:
            for entry in self.sftp.listdir_attr(path):
                child = posixpath.join(path, entry.filename)
                if stat.S_ISDIR(entry.st_mode):
                    self._delete_remote_path(child, True)
                else:
                    self.sftp.remove(child)
            self.sftp.rmdir(path)
        else:
            self.sftp.remove(path)

    def _upload_selected(self):
        self._start_transfer("upload", delete_source=False)

    def _download_selected(self):
        self._start_transfer("download", delete_source=False)

    def _move_to_remote(self):
        self._start_transfer("upload", delete_source=True)

    def _move_to_local(self):
        self._start_transfer("download", delete_source=True)

    def _start_transfer(self, action, delete_source):
        if self._transfer_worker is not None:
            return
        if self.sftp is None:
            InfoBar.warning("提示", "请先连接 FTP", duration=2000, parent=self.window())
            return

        if action == "upload":
            selected = self._get_selected_local_item()
            if not selected:
                return
            data, local_path = selected
            remote_path = self._normalize_remote_path(posixpath.join(self.remote_dir, data["name"]))
        else:
            selected = self._get_selected_remote_item()
            if not selected:
                return
            data, remote_path = selected
            local_path = os.path.join(self.local_dir, data["name"])

        host = self.host_edit.text().strip()
        username = self.user_edit.text().strip()
        password = self.pass_edit.text()
        self._transfer_context = {
            "refresh_local": action == "download" or delete_source,
            "refresh_remote": action == "upload" or delete_source,
        }
        self._set_transfer_in_progress(True, "传输中...")
        self._transfer_worker = TransferWorker(
            host, username, password, action, local_path, remote_path, delete_source
        )
        self._transfer_worker.finished_signal.connect(self._on_transfer_finished)
        self._transfer_worker.start()

    def _on_transfer_finished(self, success, message):
        self._set_transfer_in_progress(False)
        refresh_local = False
        refresh_remote = False
        if self._transfer_context:
            refresh_local = self._transfer_context.get("refresh_local", False)
            refresh_remote = self._transfer_context.get("refresh_remote", False)
        self._transfer_context = None
        self._transfer_worker = None

        if success:
            InfoBar.success("完成", message, duration=2000, parent=self.window())
            if refresh_local:
                self._refresh_local_list()
            if refresh_remote:
                self._refresh_remote_list()
        else:
            InfoBar.error("失败", message, duration=3000, parent=self.window())

    def closeEvent(self, event):
        self._disconnect()
        super().closeEvent(event)
