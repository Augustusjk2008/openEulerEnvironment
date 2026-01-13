from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional
import os
import posixpath
import stat
import tempfile

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFileDialog,
    QScrollArea,
    QCheckBox,
    QSplitter,
    QSizePolicy,
    QDialog,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QMessageBox,
)
from qfluentwidgets import (
    CardWidget,
    SubtitleLabel,
    BodyLabel,
    StrongBodyLabel,
    LineEdit,
    PushButton,
    PrimaryPushButton,
    ComboBox,
    InfoBar,
    FluentIcon as FIF,
    IconWidget,
)
from matplotlib import rcParams
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from core.font_manager import FontManager
from core.slog_parser import LogField, parse_slog_file
import paramiko

rcParams["font.family"] = "sans-serif"
rcParams["font.sans-serif"] = [
    "Microsoft YaHei",
    "SimHei",
    "Noto Sans CJK SC",
    "Arial Unicode MS",
    "DejaVu Sans",
]
rcParams["axes.unicode_minus"] = False


class DataVisualizationInterface(QWidget):
    """数据可视化界面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("dataVisualizationInterface")
        self._series: Dict[str, List[float]] = {}
        self._checkboxes: Dict[str, QCheckBox] = {}
        self._record_count = 0
        self._current_path: Optional[Path] = None
        self._current_remote_path: Optional[str] = None
        self._temp_path: Optional[str] = None
        self._download_worker = None
        self._last_remote_dir: Optional[str] = None
        self._init_ui()
        self._render_empty_plot("请选择 SLOG 文件并勾选要绘制的条目")

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(20)

        title = SubtitleLabel("数据可视化")
        title.setStyleSheet(
            f"color: #2D3748; font-size: {FontManager.get_font_size('large_title')}px;"
        )
        layout.addWidget(title)

        desc = BodyLabel("选择 .slog 文件后，在左侧勾选需要绘制的条目。")
        desc.setStyleSheet(
            f"color: #5A6A7A; font-size: {FontManager.get_font_size('body')}px;"
        )
        layout.addWidget(desc)

        layout.addWidget(self._create_file_card())
        layout.addWidget(self._create_plot_card(), 1)

    def _create_file_card(self) -> CardWidget:
        card = CardWidget()
        card.setStyleSheet(
            """
            CardWidget {
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 12px;
                border: 1px solid rgba(0, 0, 0, 0.06);
            }
            """
        )
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(12)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        icon = IconWidget(FIF.PIE_SINGLE)
        icon.setFixedSize(28, 28)
        header_layout.addWidget(icon)

        title = StrongBodyLabel("文件选择")
        title.setStyleSheet(f"font-size: {FontManager.get_font_size('title')}px; color: #2D3748;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        row_layout = QHBoxLayout()
        row_layout.setSpacing(12)

        self.path_edit = LineEdit()
        self.path_edit.setReadOnly(True)
        self.path_edit.setPlaceholderText("请选择 .slog 文件")
        self.path_edit.setFixedHeight(36)
        row_layout.addWidget(self.path_edit, 1)

        self.browse_btn = PushButton("浏览文件")
        self.browse_btn.setFixedHeight(36)
        self.browse_btn.clicked.connect(self._on_browse_clicked)
        row_layout.addWidget(self.browse_btn)

        self.remote_browse_btn = PushButton("选择远程文件")
        self.remote_browse_btn.setFixedHeight(36)
        self.remote_browse_btn.clicked.connect(self._on_remote_browse_clicked)
        self.remote_browse_btn.setEnabled(False)
        row_layout.addWidget(self.remote_browse_btn)

        layout.addLayout(row_layout)
        return card

    def _create_plot_card(self) -> CardWidget:
        card = CardWidget()
        card.setStyleSheet(
            """
            CardWidget {
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 12px;
                border: 1px solid rgba(0, 0, 0, 0.06);
            }
            """
        )

        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(16)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(8)

        left_panel = QWidget()
        left_panel.setMinimumWidth(260)
        left_panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)

        left_title = StrongBodyLabel("条目选择")
        left_title.setStyleSheet(f"font-size: {FontManager.get_font_size('title')}px; color: #2D3748;")
        left_layout.addWidget(left_title)

        self._checkbox_container = QWidget()
        self._checkbox_container.setMinimumWidth(240)
        self._checkbox_layout = QVBoxLayout(self._checkbox_container)
        self._checkbox_layout.setContentsMargins(0, 0, 0, 0)
        self._checkbox_layout.setSpacing(6)
        self._checkbox_layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(
            """
            QScrollArea {
                border: 1px solid rgba(0, 0, 0, 0.08);
                border-radius: 8px;
                background-color: rgba(255, 255, 255, 0.6);
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
            """
        )
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setWidget(self._checkbox_container)
        left_layout.addWidget(scroll, 1)

        right_panel = QWidget()
        right_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)

        right_title = StrongBodyLabel("数据展示")
        right_title.setStyleSheet(f"font-size: {FontManager.get_font_size('title')}px; color: #2D3748;")
        right_layout.addWidget(right_title)

        self.figure = Figure(figsize=(6, 4))
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background-color: white;")
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.toolbar.setStyleSheet("background-color: transparent;")
        right_layout.addWidget(self.toolbar)
        right_layout.addWidget(self.canvas, 1)

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([280, 900])

        layout.addWidget(splitter, 1)
        return card

    def _on_browse_clicked(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "选择 SLOG 文件",
            "",
            "SLOG Files (*.slog);;All Files (*.*)",
        )
        if not path:
            return
        self._cleanup_temp_file()
        self._current_remote_path = None
        self._load_file(Path(path))

    def _on_remote_browse_clicked(self):
        sftp = self._get_sftp()
        if sftp is None:
            InfoBar.warning("提示", "请先连接 FTP", duration=2000, parent=self.window())
            self._update_remote_button_state()
            return

        start_dir = self._last_remote_dir or self._get_remote_dir()
        dialog = RemoteFileDialog(sftp, start_dir=start_dir, parent=self.window())
        if dialog.exec_() != QDialog.Accepted:
            return
        remote_path = dialog.selected_path
        if not remote_path:
            return
        self._last_remote_dir = posixpath.dirname(remote_path) or "/"
        self._start_remote_download(remote_path)

    def _load_file(self, path: Path, display_path: Optional[str] = None):
        try:
            slog = parse_slog_file(path)
        except Exception as exc:
            InfoBar.error("读取失败", f"无法解析 SLOG 文件: {exc}", duration=4000, parent=self.window())
            self._reset_state()
            return

        self._current_path = path
        self.path_edit.setText(display_path or str(path))
        self._build_series(slog.schema.fields, slog.records)
        self._build_checkboxes()
        self._render_empty_plot("请勾选要绘制的条目")

    def _reset_state(self):
        self._cleanup_temp_file()
        self._current_path = None
        self._current_remote_path = None
        self.path_edit.clear()
        self._series.clear()
        self._record_count = 0
        self._clear_checkboxes()
        self._render_empty_plot("请选择 SLOG 文件并勾选要绘制的条目")

    def _build_series(self, fields: List[LogField], records: List[dict]):
        self._series.clear()
        self._record_count = len(records)
        if not records:
            return

        for field in fields:
            if field.count <= 1:
                self._series[field.name] = []
            else:
                for idx in range(field.count):
                    self._series[f"{field.name}[{idx}]"] = []

        for record in records:
            for field in fields:
                value = record.get(field.name)
                if isinstance(value, list):
                    for idx in range(field.count):
                        key = f"{field.name}[{idx}]"
                        if key not in self._series:
                            continue
                        if idx >= len(value):
                            self._series[key].append(float("nan"))
                        else:
                            self._series[key].append(float(value[idx]))
                else:
                    if field.name not in self._series:
                        continue
                    if value is None:
                        self._series[field.name].append(float("nan"))
                    else:
                        self._series[field.name].append(float(value))

    def _build_checkboxes(self):
        self._clear_checkboxes()
        if not self._series:
            return

        for name in self._series.keys():
            checkbox = QCheckBox(name)
            checkbox.setToolTip(name)
            checkbox.stateChanged.connect(self._on_series_selection_changed)
            self._checkbox_layout.insertWidget(self._checkbox_layout.count() - 1, checkbox)
            self._checkboxes[name] = checkbox

    def _clear_checkboxes(self):
        while self._checkbox_layout.count() > 1:
            item = self._checkbox_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._checkboxes.clear()

    def _on_series_selection_changed(self):
        selected = [name for name, cb in self._checkboxes.items() if cb.isChecked()]
        if not selected:
            self._render_empty_plot("请勾选要绘制的条目")
            return

        self.figure.clear()
        axes = self.figure.add_subplot(111)
        x_values = list(range(1, self._record_count + 1))
        for name in selected:
            y_values = self._series.get(name, [])
            if y_values:
                axes.plot(x_values, y_values, label=name)

        axes.set_xlabel("数据条目序号")
        axes.set_ylabel("数据值")
        axes.grid(True, linestyle="--", alpha=0.3)
        axes.legend(fontsize=8)
        self.figure.tight_layout()
        self.canvas.draw_idle()

    def _render_empty_plot(self, message: str):
        self.figure.clear()
        axes = self.figure.add_subplot(111)
        axes.text(
            0.5,
            0.5,
            message,
            ha="center",
            va="center",
            transform=axes.transAxes,
            color="#7A8A9A",
        )
        axes.set_xticks([])
        axes.set_yticks([])
        self.figure.tight_layout()
        self.canvas.draw_idle()

    def _get_ftp_interface(self):
        window = self.window()
        return getattr(window, "ftpInterface", None)

    def _get_sftp(self):
        ftp = self._get_ftp_interface()
        if ftp is None:
            return None
        return getattr(ftp, "sftp", None)

    def _get_remote_dir(self):
        ftp = self._get_ftp_interface()
        if ftp is None:
            return "/"
        return getattr(ftp, "remote_dir", "/") or "/"

    def _get_ftp_credentials(self):
        ftp = self._get_ftp_interface()
        if ftp is None:
            return None
        host = ftp.host_edit.text().strip()
        username = ftp.user_edit.text().strip()
        password = ftp.pass_edit.text()
        if not host or not username:
            return None
        return host, username, password

    def _start_remote_download(self, remote_path: str):
        credentials = self._get_ftp_credentials()
        if not credentials:
            InfoBar.warning("提示", "FTP 连接信息不完整", duration=2000, parent=self.window())
            return
        if self._download_worker is not None:
            return
        if not remote_path.lower().endswith(".slog"):
            InfoBar.warning("提示", "请选择 .slog 文件", duration=2000, parent=self.window())
            return

        base_name = os.path.basename(remote_path)
        temp_dir = tempfile.mkdtemp(prefix="slog_cache_")
        local_path = os.path.join(temp_dir, base_name)

        host, username, password = credentials
        self.remote_browse_btn.setEnabled(False)
        self._current_remote_path = remote_path
        self._download_worker = RemoteDownloadWorker(
            host, username, password, remote_path, local_path
        )
        self._download_worker.finished_signal.connect(self._on_remote_download_finished)
        self._download_worker.start()

    def _on_remote_download_finished(self, success: bool, local_path: str, message: str):
        self.remote_browse_btn.setEnabled(True)
        self._download_worker = None
        if not success:
            if local_path and os.path.exists(local_path):
                try:
                    os.remove(local_path)
                except Exception:
                    pass
            temp_dir = os.path.dirname(local_path) if local_path else ""
            if temp_dir and os.path.isdir(temp_dir):
                try:
                    os.rmdir(temp_dir)
                except Exception:
                    pass
            InfoBar.error("下载失败", message, duration=3000, parent=self.window())
            return

        self._cleanup_temp_file()
        self._temp_path = local_path
        display_path = f"远程: {self._current_remote_path}"
        self._load_file(Path(local_path), display_path=display_path)

    def _cleanup_temp_file(self):
        if not self._temp_path:
            return
        try:
            if os.path.isfile(self._temp_path):
                os.remove(self._temp_path)
            temp_dir = os.path.dirname(self._temp_path)
            if os.path.isdir(temp_dir):
                os.rmdir(temp_dir)
        except Exception:
            pass
        self._temp_path = None

    def set_ftp_connected(self, connected: bool):
        self.remote_browse_btn.setEnabled(bool(connected))

    def _update_remote_button_state(self):
        self.remote_browse_btn.setEnabled(self._get_sftp() is not None)

    def showEvent(self, event):
        super().showEvent(event)
        self._update_remote_button_state()

    def closeEvent(self, event):
        self._cleanup_temp_file()
        super().closeEvent(event)


class RemoteDownloadWorker(QThread):
    finished_signal = pyqtSignal(bool, str, str)

    def __init__(self, host: str, username: str, password: str, remote_path: str, local_path: str):
        super().__init__()
        self.host = host
        self.username = username
        self.password = password
        self.remote_path = remote_path
        self.local_path = local_path

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
            sftp.get(self.remote_path, self.local_path)
            self.finished_signal.emit(True, self.local_path, "")
        except Exception as exc:
            self.finished_signal.emit(False, self.local_path, f"无法下载远端文件: {exc}")
        finally:
            if sftp is not None:
                sftp.close()
            if ssh is not None:
                ssh.close()


class RemoteFileDialog(QDialog):
    def __init__(self, sftp, start_dir="/", parent=None):
        super().__init__(parent)
        self.sftp = sftp
        self.selected_path = None
        self.current_dir = self._normalize_remote_path(start_dir)
        self._all_entries = []
        self._init_ui()
        self._refresh_list()

    def _init_ui(self):
        self.setWindowTitle("选择远程 SLOG 文件")
        self.resize(720, 420)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        path_row = QHBoxLayout()
        path_row.setSpacing(8)
        self.path_edit = LineEdit()
        self.path_edit.setReadOnly(True)
        self.path_edit.setText(self.current_dir)
        self.path_edit.setFixedHeight(32)
        path_row.addWidget(self.path_edit, 1)

        self.up_btn = PushButton("上一级")
        self.up_btn.setFixedHeight(32)
        self.up_btn.clicked.connect(self._go_up)
        path_row.addWidget(self.up_btn)

        self.refresh_btn = PushButton("刷新")
        self.refresh_btn.setFixedHeight(32)
        self.refresh_btn.clicked.connect(self._refresh_list)
        path_row.addWidget(self.refresh_btn)

        layout.addLayout(path_row)

        filter_row = QHBoxLayout()
        filter_row.setSpacing(8)

        filter_label = BodyLabel("过滤:")
        filter_row.addWidget(filter_label)

        self.filter_combo = ComboBox()
        self.filter_combo.setFixedHeight(32)
        self.filter_combo.addItem("仅 .slog", userData="slog")
        self.filter_combo.addItem("全部文件", userData="all")
        self.filter_combo.addItem("仅文件夹", userData="dir")
        self.filter_combo.currentIndexChanged.connect(self._apply_filters)
        filter_row.addWidget(self.filter_combo)

        self.search_edit = LineEdit()
        self.search_edit.setPlaceholderText("搜索文件/目录")
        self.search_edit.setFixedHeight(32)
        self.search_edit.textChanged.connect(self._apply_filters)
        filter_row.addWidget(self.search_edit, 1)

        layout.addLayout(filter_row)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["名称", "类型", "大小"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.cellDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.table, 1)

        action_row = QHBoxLayout()
        action_row.addStretch()
        self.select_btn = PrimaryPushButton("选择文件")
        self.select_btn.setFixedHeight(34)
        self.select_btn.clicked.connect(self._select_current)
        action_row.addWidget(self.select_btn)
        cancel_btn = PushButton("取消")
        cancel_btn.setFixedHeight(34)
        cancel_btn.clicked.connect(self.reject)
        action_row.addWidget(cancel_btn)
        layout.addLayout(action_row)

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

    def _refresh_list(self):
        try:
            entries = []
            for entry in self.sftp.listdir_attr(self.current_dir):
                is_dir = stat.S_ISDIR(entry.st_mode)
                entries.append({
                    "name": entry.filename,
                    "is_dir": is_dir,
                    "size": entry.st_size if not is_dir else None,
                })
            entries.sort(key=lambda item: (not item["is_dir"], item["name"].lower()))
            self._all_entries = entries
            self._apply_filters()
            self.path_edit.setText(self.current_dir)
        except Exception as exc:
            QMessageBox.warning(self, "读取失败", f"无法读取远端目录: {exc}")

    def _apply_filters(self):
        keyword = self.search_edit.text().strip().lower()
        mode = self.filter_combo.currentData()
        filtered = []
        for entry in self._all_entries:
            name = entry["name"].lower()
            is_dir = entry["is_dir"]
            if keyword and keyword not in name:
                continue
            if mode == "dir" and not is_dir:
                continue
            if mode == "slog" and not is_dir and not name.endswith(".slog"):
                continue
            filtered.append(entry)
        self._populate_table(filtered)

    def _populate_table(self, entries):
        self.table.setRowCount(len(entries))
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
            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, type_item)
            self.table.setItem(row, 2, size_item)

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

    def _go_up(self):
        parent = posixpath.dirname(self.current_dir.rstrip("/"))
        if not parent:
            parent = "/"
        self.current_dir = parent
        self._refresh_list()

    def _on_item_double_clicked(self, row, _column):
        item = self.table.item(row, 0)
        if not item:
            return
        data = item.data(Qt.UserRole) or {}
        if data.get("is_dir"):
            self.current_dir = self._normalize_remote_path(
                posixpath.join(self.current_dir, data["name"])
            )
            self._refresh_list()
        else:
            if not data.get("name", "").lower().endswith(".slog"):
                QMessageBox.information(self, "提示", "请选择 .slog 文件")
                return
            self.selected_path = self._normalize_remote_path(
                posixpath.join(self.current_dir, data["name"])
            )
            self.accept()

    def _select_current(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "提示", "请选择远端文件")
            return
        item = self.table.item(row, 0)
        if not item:
            return
        data = item.data(Qt.UserRole) or {}
        if data.get("is_dir"):
            QMessageBox.information(self, "提示", "请选择文件而不是文件夹")
            return
        if not data.get("name", "").lower().endswith(".slog"):
            QMessageBox.information(self, "提示", "请选择 .slog 文件")
            return
        self.selected_path = self._normalize_remote_path(
            posixpath.join(self.current_dir, data["name"])
        )
        self.accept()
