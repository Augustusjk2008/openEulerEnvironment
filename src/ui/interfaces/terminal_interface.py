"""
终端界面
使用内嵌 SSH 终端与远程交互
"""

import locale
import shutil
import paramiko
import pyte
import codecs
from wcwidth import wcwidth
from PyQt5.QtCore import Qt, QProcess, QTimer, QObject, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QTextCursor, QKeySequence, QFont, QFontMetrics, QTextCharFormat, QColor
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QApplication, QSizePolicy
from qfluentwidgets import (
    CardWidget, SubtitleLabel, BodyLabel, StrongBodyLabel, CaptionLabel,
    LineEdit, PushButton, PrimaryPushButton, FluentIcon as FIF,
    IconWidget, InfoBar, TextEdit
)
from core.config_manager import get_config_manager
from core.font_manager import FontManager
from core.ssh_utils import SSHClientFactory, SSHConnectWorker


HISTORY_LINES = 2000
MIN_COLUMNS = 20
MIN_LINES = 5
ANSI_COLOR_MAP = {
    "black": "#000000",
    "red": "#cd3131",
    "green": "#0dbc79",
    "brown": "#e5e510",
    "blue": "#2472c8",
    "magenta": "#bc3fbc",
    "cyan": "#11a8cd",
    "white": "#e5e5e5",
    "brightblack": "#666666",
    "brightred": "#f14c4c",
    "brightgreen": "#23d18b",
    "brightbrown": "#f5f543",
    "brightblue": "#3b8eea",
    "brightmagenta": "#d670d6",
    "brightcyan": "#29b8db",
    "brightwhite": "#ffffff",
}


class TerminalTextEdit(TextEdit):
    """简易终端输入控件"""

    def __init__(self, input_handler, focus_handler, resize_handler=None, parent=None):
        super().__init__(parent)
        self._input_handler = input_handler
        self._focus_handler = focus_handler
        self._resize_handler = resize_handler
        self.setUndoRedoEnabled(False)
        self.setAcceptRichText(False)
        self.setReadOnly(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setTabChangesFocus(False)

    def keyPressEvent(self, event):
        # 1. 处理常规快捷键
        if event.matches(QKeySequence.Copy):
            if self.textCursor().hasSelection():
                self.copy()
                return

        if event.matches(QKeySequence.Paste):
            text = QApplication.clipboard().text()
            if text:
                self._input_handler(text)
            return

        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._input_handler("\n")
            return

        if event.key() == Qt.Key_Backspace:
            self._input_handler("\b")
            return

        if event.key() == Qt.Key_Tab:
            self._input_handler("\t")
            return

        key_map = {
            Qt.Key_Up: "\x1b[A",
            Qt.Key_Down: "\x1b[B",
            Qt.Key_Right: "\x1b[C",
            Qt.Key_Left: "\x1b[D",
            Qt.Key_Home: "\x1b[H",
            Qt.Key_End: "\x1b[F",
            Qt.Key_Delete: "\x1b[3~",
            Qt.Key_Insert: "\x1b[2~",
            Qt.Key_PageUp: "\x1b[5~",
            Qt.Key_PageDown: "\x1b[6~",
        }
        if event.key() in key_map:
            self._input_handler(key_map[event.key()])
            return

        if event.modifiers() & Qt.ControlModifier:
            if event.key() == Qt.Key_C:
                if self.textCursor().hasSelection():
                    self.copy()
                else:
                    self._input_handler("\x03")
                return
            if event.key() == Qt.Key_D:
                self._input_handler("\x04")
                return
            if event.key() == Qt.Key_Z:
                self._input_handler("\x1A")
                return

        text = event.text()
        if text:
            self._input_handler(text)
            return

        super().keyPressEvent(event)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        if self._focus_handler:
            self._focus_handler(True)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        if self._focus_handler:
            self._focus_handler(False)

    def focusNextPrevChild(self, next):
        return False

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._resize_handler:
            self._resize_handler()


class TerminalInterface(QWidget):
    """终端界面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("terminalInterface")
        self.config_manager = get_config_manager()
        self.local_encoding = locale.getpreferredencoding(False)
        self.remote_encoding = "utf-8"
        self._decoder = codecs.getincrementaldecoder(self.remote_encoding)(errors='replace')
        self._stderr_decoder = codecs.getincrementaldecoder(self.remote_encoding)(errors='replace')
        self.ssh_client = None
        self.ssh_channel = None
        self.key_fix_process = QProcess(self)
        self._poll_timer = QTimer(self)
        self._key_fix_needed = False
        self._connect_thread = None
        self._connect_worker = None
        self._connect_in_progress = False
        self._connect_cancelled = False
        self._screen = None
        self._stream = None
        self._format_cache = {}
        self._default_fg = QColor("#D4D4D4")
        self._default_bg = QColor("#1E1E1E")
        # 增量更新优化：保存上一帧屏幕状态
        self._last_screen_lines = []
        self._last_cursor_pos = None
        # 批量数据处理
        self._pending_data = []
        self._pending_timer = None
        self._default_format = QTextCharFormat()
        self._default_format.setForeground(self._default_fg)
        self._default_format.setBackground(self._default_bg)
        self._cursor_char = "█"
        self._cursor_visible = False

        self._init_ui()
        self._load_defaults()
        self._init_process()
        self._init_terminal_emulator()

        app = QApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self._stop_terminal)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(20)

        title = SubtitleLabel("远程终端")
        title.setStyleSheet(f"color: #2D3748; font-size: {FontManager.get_font_size('large_title')}px;")
        layout.addWidget(title)

        desc = BodyLabel("点击登录后直接发起 SSH 会话，终端内容将实时显示")
        desc.setStyleSheet(f"color: #5A6A7A; font-size: {FontManager.get_font_size('body')}px;")
        layout.addWidget(desc)

        connection_card = self._create_connection_card()
        layout.addWidget(connection_card)

        terminal_card = self._create_terminal_card()
        layout.addWidget(terminal_card, 1)

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

        icon = IconWidget(FIF.DEVELOPER_TOOLS)
        icon.setFixedSize(28, 28)
        header_layout.addWidget(icon)

        title = StrongBodyLabel("连接信息")
        title.setStyleSheet(f"font-size: {FontManager.get_font_size('title')}px; color: #2D3748;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        self.status_label = CaptionLabel("SSH 未连接")
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
        self.pass_edit.setPlaceholderText("SSH 登录密码")
        self.pass_edit.setEchoMode(LineEdit.Password)
        grid.addWidget(self.pass_edit, 2, 1)

        layout.addLayout(grid)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)

        self.connect_btn = PrimaryPushButton("登录 SSH")
        self.connect_btn.setFixedHeight(36)
        self.connect_btn.clicked.connect(self._on_connect_clicked)
        button_layout.addWidget(self.connect_btn)

        self.disconnect_btn = PushButton("断开 SSH")
        self.disconnect_btn.setFixedHeight(36)
        self.disconnect_btn.clicked.connect(self._on_disconnect_clicked)
        button_layout.addWidget(self.disconnect_btn)

        self.restart_btn = PushButton("重启终端")
        self.restart_btn.setFixedHeight(36)
        self.restart_btn.clicked.connect(self._restart_terminal)
        button_layout.addWidget(self.restart_btn)

        self.fix_key_btn = PushButton("修复密钥")
        self.fix_key_btn.setFixedHeight(36)
        self.fix_key_btn.setEnabled(False)
        self.fix_key_btn.clicked.connect(self._on_fix_key_clicked)
        button_layout.addWidget(self.fix_key_btn)

        self.clear_btn = PushButton("清屏")
        self.clear_btn.setFixedHeight(36)
        self.clear_btn.clicked.connect(self._clear_output)
        button_layout.addWidget(self.clear_btn)

        button_layout.addStretch()

        layout.addLayout(button_layout)
        return card

    def _create_terminal_card(self):
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

        title = StrongBodyLabel("终端输出")
        title.setStyleSheet(f"font-size: {FontManager.get_font_size('title')}px; color: #2D3748;")
        layout.addWidget(title)

        self.output_text = TerminalTextEdit(
            self._handle_user_input,
            self._set_cursor_visible,
            self._on_terminal_resized,
        )
        self.output_text.setLineWrapMode(TextEdit.NoWrap)
        self.output_text.setFont(QFont("Consolas", FontManager.get_font_size("body")))
        self.output_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.output_text.setStyleSheet("""
            TextEdit {
                background-color: #1E1E1E;
                color: #D4D4D4;
                border: 1px solid #3E3E3E;
                border-radius: 6px;
                padding: 10px;
                font-family: 'Consolas', 'Microsoft YaHei UI', monospace;
            }
        """)
        layout.addWidget(self.output_text, 1)
        return card

    def _load_defaults(self):
        # 从配置文件加载SSH连接信息，无默认值（避免硬编码敏感信息）
        self.host_edit.setText(self.config_manager.get("ssh_host", ""))
        self.user_edit.setText(self.config_manager.get("ssh_username", ""))
        self.pass_edit.setText(self.config_manager.get("ssh_password", ""))

    def _init_process(self):
        self.key_fix_process.setProcessChannelMode(QProcess.MergedChannels)
        self.key_fix_process.readyReadStandardOutput.connect(self._on_key_fix_ready_read)
        self.key_fix_process.finished.connect(self._on_key_fix_finished)
        # 优化：降低轮询频率从50ms到100ms，减少CPU占用
        self._poll_timer.setInterval(100)
        self._poll_timer.timeout.connect(self._poll_ssh_output)
        # 批量数据缓冲区，用于累积数据后统一处理
        self._pending_data = []
        self._pending_timer = QTimer(self)
        self._pending_timer.setSingleShot(True)
        self._pending_timer.timeout.connect(self._flush_pending_data)

    def _init_terminal_emulator(self):
        self._ensure_terminal_size()

    def _on_terminal_resized(self):
        self._ensure_terminal_size()
        self._refresh_view()

    def _calc_terminal_size(self):
        metrics = QFontMetrics(self.output_text.font())
        char_width = max(metrics.horizontalAdvance("M"), 1)
        char_height = max(metrics.height(), 1)
        viewport = self.output_text.viewport().size()
        columns = max(int(viewport.width() / char_width), MIN_COLUMNS)
        lines = max(int(viewport.height() / char_height), MIN_LINES)
        return columns, lines

    def _ensure_terminal_size(self):
        columns, lines = self._calc_terminal_size()
        if self._screen is None:
            self._screen = pyte.HistoryScreen(columns, lines, history=HISTORY_LINES)
            self._stream = pyte.Stream(self._screen)
            return

        if columns != self._screen.columns or lines != self._screen.lines:
            self._screen.resize(lines=lines, columns=columns)
            if self.ssh_channel is not None and not self.ssh_channel.closed:
                try:
                    self.ssh_channel.resize_pty(width=columns, height=lines)
                except (paramiko.SSHException, IOError, OSError):
                    pass

    def _color_for(self, name, default_color):
        if isinstance(name, tuple) and len(name) == 3:
            return QColor(name[0], name[1], name[2])
        if isinstance(name, str):
            if name == "default":
                return default_color
            if len(name) == 6 and all(ch in "0123456789abcdef" for ch in name.lower()):
                return QColor(f"#{name}")
            mapped = ANSI_COLOR_MAP.get(name)
            if mapped is not None:
                return QColor(mapped)
        return default_color

    def _format_for_char(self, char):
        fg_name = char.fg
        bg_name = char.bg
        reverse = char.reverse
        if reverse:
            fg_name, bg_name = bg_name, fg_name
        key = (
            fg_name,
            bg_name,
            char.bold,
            char.italics,
            char.underscore,
            char.strikethrough,
        )
        if (
            fg_name == "default"
            and bg_name == "default"
            and not char.bold
            and not char.italics
            and not char.underscore
            and not char.strikethrough
        ):
            return self._default_format
        cached = self._format_cache.get(key)
        if cached is not None:
            return cached

        fmt = QTextCharFormat()
        fmt.setForeground(self._color_for(fg_name, self._default_fg))
        fmt.setBackground(self._color_for(bg_name, self._default_bg))
        if char.bold:
            fmt.setFontWeight(QFont.Bold)
        if char.italics:
            fmt.setFontItalic(True)
        if char.underscore:
            fmt.setFontUnderline(True)
        if char.strikethrough:
            fmt.setFontStrikeOut(True)
        self._format_cache[key] = fmt
        return fmt

    def _collect_screen_lines(self):
        if self._screen is None:
            return [], 0
        history = getattr(self._screen, "history", None)
        history_top = list(history.top) if history is not None else []
        history_bottom = list(history.bottom) if history is not None else []
        lines = history_top[:]
        for y in range(self._screen.lines):
            lines.append(self._screen.buffer[y])
        if history_bottom:
            lines.extend(history_bottom)
        return lines, len(history_top)

    def _line_right_bound(self, line, cursor_col):
        right_bound = -1
        for x in range(self._screen.columns - 1, -1, -1):
            if line[x].data != " ":
                right_bound = x
                break
        if cursor_col is not None:
            right_bound = max(right_bound, cursor_col)
        return right_bound

    def _restart_terminal(self):
        self._on_connect_clicked()

    def _start_connect_worker(self, host, username, password):
        if self._connect_in_progress:
            return
        self._connect_in_progress = True
        self._connect_cancelled = False
        self.connect_btn.setEnabled(False)
        self.status_label.setText("SSH 连接中（请稍候）")
        self.status_label.setStyleSheet(f"color: #D97706; font-size: {FontManager.get_font_size('caption')}px;")

        thread = QThread(self)
        worker = SSHConnectWorker(host, username, password)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.connected.connect(self._on_connect_success)
        worker.host_key_error.connect(self._on_host_key_error)
        worker.auth_failed.connect(self._on_auth_failed)
        worker.error_occurred.connect(self._on_error_occurred)
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

    def _stop_terminal(self):
        if self._connect_in_progress:
            self._connect_cancelled = True
        if self.ssh_channel is not None:
            try:
                self.ssh_channel.close()
            except (paramiko.SSHException, IOError, OSError):
                pass
        if self.ssh_client is not None:
            try:
                self.ssh_client.close()
            except (paramiko.SSHException, IOError, OSError):
                pass
        self.ssh_channel = None
        self.ssh_client = None
        if self._poll_timer.isActive():
            self._poll_timer.stop()
        if self.key_fix_process.state() != QProcess.NotRunning:
            self.key_fix_process.terminate()
            if not self.key_fix_process.waitForFinished(1500):
                self.key_fix_process.kill()
                self.key_fix_process.waitForFinished(1500)
        self.status_label.setText("SSH 已断开")
        self.status_label.setStyleSheet(f"color: #D83B01; font-size: {FontManager.get_font_size('caption')}px;")
        self._set_cursor_visible(False)

    def _flush_pending_data(self):
        """批量刷新累积的数据"""
        if not self._pending_data:
            return
        # 合并所有待处理数据
        combined_text = "".join(self._pending_data)
        self._pending_data.clear()
        self._append_output(combined_text)

    def _append_output(self, text):
        if not text:
            return
        if self._stream is None:
            self._ensure_terminal_size()
        self._stream.feed(text)
        # 使用增量更新而非全量重绘
        self._refresh_view_incremental()

    def _send_raw(self, text):
        if self.ssh_channel is None or self.ssh_channel.closed:
            return
        try:
            # 统一使用 utf-8 发送
            if isinstance(text, str):
                data = text.encode(self.remote_encoding)
            else:
                data = text
            self.ssh_channel.send(data)
        except (paramiko.SSHException, IOError, OSError, UnicodeEncodeError):
            return

    def _handle_user_input(self, data):
        if not data:
            return
        self._send_raw(data)

    def _poll_ssh_output(self):
        if self.ssh_channel is None:
            if self._poll_timer.isActive():
                self._poll_timer.stop()
            return

        try:
            has_data = False
            # 批量读取所有可用数据
            while self.ssh_channel.recv_ready():
                data = self.ssh_channel.recv(4096)
                if data:
                    text = self._decoder.decode(data)
                    self._pending_data.append(text)
                    has_data = True
                else:
                    break
            while self.ssh_channel.recv_stderr_ready():
                data = self.ssh_channel.recv_stderr(4096)
                if data:
                    text = self._stderr_decoder.decode(data)
                    self._pending_data.append(text)
                    has_data = True
                else:
                    break

            # 有数据时启动延迟刷新定时器（批量处理）
            if has_data:
                if not self._pending_timer.isActive():
                    self._pending_timer.start(50)  # 50ms后统一刷新

        except (paramiko.SSHException, IOError, OSError) as exc:
            self._append_output(f"\r\n[连接异常] {exc}\r\n")
            self._stop_terminal()
            return
        except UnicodeDecodeError as exc:
            self._append_output(f"\r\n[解码错误] 无法解码服务器响应: {exc}\r\n")
            return

        if self.ssh_channel.exit_status_ready() or self.ssh_channel.closed:
            self._stop_terminal()

    def _on_connect_clicked(self):
        host = self.host_edit.text().strip()
        username = self.user_edit.text().strip()
        password = self.pass_edit.text()

        if not host or not username:
            InfoBar.warning("提示", "请填写完整的 SSH 连接信息。", duration=2000, parent=self.window())
            return

        if self._connect_in_progress:
            return

        if self.ssh_channel is not None:
            self._stop_terminal()

        self._key_fix_needed = False
        self.fix_key_btn.setEnabled(False)
        self._ensure_terminal_size()

        self._append_output(f"\r\n$ ssh {username}@{host}\r\n")
        self._start_connect_worker(host, username, password)

    def _on_disconnect_clicked(self):
        if self._connect_in_progress:
            self._connect_cancelled = True
            self.status_label.setText("SSH 连接取消中")
            self.status_label.setStyleSheet(f"color: #D97706; font-size: {FontManager.get_font_size('caption')}px;")
            return
        if self.ssh_channel is not None and not self.ssh_channel.closed:
            self._send_raw("exit\n")
        self._stop_terminal()

    def _on_connect_success(self, client):
        self._connect_in_progress = False
        self.connect_btn.setEnabled(True)
        if self._connect_cancelled:
            client.close()
            self.status_label.setText("SSH 已取消")
            self.status_label.setStyleSheet(f"color: #D83B01; font-size: {FontManager.get_font_size('caption')}px;")
            return

        columns = self._screen.columns if self._screen is not None else MIN_COLUMNS
        lines = self._screen.lines if self._screen is not None else MIN_LINES
        try:
            channel = client.invoke_shell(term="xterm", width=columns, height=lines)
        except paramiko.SSHException as exc:
            client.close()
            self.status_label.setText("SSH 连接失败")
            self.status_label.setStyleSheet(f"color: #D83B01; font-size: {FontManager.get_font_size('caption')}px;")
            InfoBar.error("无法连接", f"SSH 会话创建失败：{exc}", duration=4000, parent=self.window())
            self._append_output(f"\r\n[连接失败] SSH错误: {exc}\r\n")
            self._set_cursor_visible(False)
            return
        except (IOError, OSError) as exc:
            client.close()
            self.status_label.setText("SSH 连接失败")
            self.status_label.setStyleSheet(f"color: #D83B01; font-size: {FontManager.get_font_size('caption')}px;")
            InfoBar.error("无法连接", f"I/O 错误：{exc}", duration=4000, parent=self.window())
            self._append_output(f"\r\n[连接失败] I/O错误: {exc}\r\n")
            self._set_cursor_visible(False)
            return

        self.ssh_client = client
        self.ssh_channel = channel
        # 重置解码器状态
        self._decoder.reset()
        self._stderr_decoder.reset()
        self._poll_timer.start()
        self.status_label.setText("SSH 已连接")
        self.status_label.setStyleSheet(f"color: #107C10; font-size: {FontManager.get_font_size('caption')}px;")
        self._set_cursor_visible(self.output_text.hasFocus())

    def _on_host_key_error(self, message):
        self._connect_in_progress = False
        self.connect_btn.setEnabled(True)
        if self._connect_cancelled:
            self.status_label.setText("SSH 已取消")
            self.status_label.setStyleSheet(f"color: #D83B01; font-size: {FontManager.get_font_size('caption')}px;")
            return

        self.status_label.setText("SSH 连接失败")
        self.status_label.setStyleSheet(f"color: #D83B01; font-size: {FontManager.get_font_size('caption')}px;")
        self._key_fix_needed = True
        self.fix_key_btn.setEnabled(True)
        InfoBar.error("主机密钥异常", "检测到主机密钥异常，可点击“修复密钥”。", duration=4000, parent=self.window())
        self._append_output(f"\r\n[主机密钥异常] {message}\r\n")
        self._set_cursor_visible(False)

    def _on_auth_failed(self, message):
        self._connect_in_progress = False
        self.connect_btn.setEnabled(True)
        if self._connect_cancelled:
            self.status_label.setText("SSH 已取消")
            self.status_label.setStyleSheet(f"color: #D83B01; font-size: {FontManager.get_font_size('caption')}px;")
            return

        self.status_label.setText("SSH 连接失败")
        self.status_label.setStyleSheet(f"color: #D83B01; font-size: {FontManager.get_font_size('caption')}px;")
        InfoBar.error("无法登录", "SSH 认证失败，请检查用户名或密码。", duration=4000, parent=self.window())
        self._append_output(f"\r\n[认证失败] {message}\r\n")
        self._set_cursor_visible(False)

    def _on_error_occurred(self, message):
        self._connect_in_progress = False
        self.connect_btn.setEnabled(True)
        if self._connect_cancelled:
            self.status_label.setText("SSH 已取消")
            self.status_label.setStyleSheet(f"color: #D83B01; font-size: {FontManager.get_font_size('caption')}px;")
            return

        self.status_label.setText("SSH 连接失败")
        self.status_label.setStyleSheet(f"color: #D83B01; font-size: {FontManager.get_font_size('caption')}px;")
        InfoBar.error("无法连接", f"连接 SSH 失败：{message}", duration=4000, parent=self.window())
        self._append_output(f"\r\n[连接失败] {message}\r\n")
        self._set_cursor_visible(False)

    def _on_key_fix_ready_read(self):
        data = self.key_fix_process.readAllStandardOutput()
        if not data:
            return
        text = bytes(data).decode(self.local_encoding, errors="replace")
        self._append_output(text)

    def _on_key_fix_finished(self):
        self._key_fix_needed = False
        self.fix_key_btn.setEnabled(False)

    def _on_fix_key_clicked(self):
        host = self.host_edit.text().strip()
        if not host:
            InfoBar.warning("提示", "请先填写主机地址。", duration=2000, parent=self.window())
            return

        keygen_path = shutil.which("ssh-keygen")
        if not keygen_path:
            InfoBar.error("无法修复", "未检测到 ssh-keygen。", duration=3000, parent=self.window())
            return

        if self.key_fix_process.state() != QProcess.NotRunning:
            return

        if self.ssh_channel is not None:
            self._stop_terminal()

        self._append_output(f"\r\n$ \"{keygen_path}\" -R {host}\r\n")
        self.key_fix_process.start(keygen_path, ["-R", host])

    def _clear_output(self):
        if self._screen is not None:
            self._screen.reset()
        self._last_screen_lines = []
        self._last_cursor_pos = None
        self._refresh_view()

    def _set_cursor_visible(self, visible):
        self._cursor_visible = visible
        self._refresh_view()

    def closeEvent(self, event):
        self._stop_terminal()
        super().closeEvent(event)

    def __del__(self):
        try:
            self._stop_terminal()
        except (RuntimeError, AttributeError, TypeError):
            # 忽略析构时可能出现的各种错误
            pass

    def _refresh_view(self):
        if self._screen is None:
            self.output_text.setPlainText("")
            return

        lines, history_len = self._collect_screen_lines()
        cursor_line = history_len + self._screen.cursor.y if self._cursor_visible else None
        cursor_col = self._screen.cursor.x if self._cursor_visible else None
        if cursor_col is not None:
            cursor_col = min(cursor_col, self._screen.columns - 1)

        self.output_text.blockSignals(True)
        doc = self.output_text.document()
        doc.clear()
        cursor = QTextCursor(doc)

        for row_idx, line in enumerate(lines):
            active_cursor_col = cursor_col if row_idx == cursor_line else None
            right_bound = self._line_right_bound(line, active_cursor_col)
            if right_bound >= 0:
                current_fmt = None
                run_text = []
                skip_next = False
                for x in range(min(right_bound + 1, self._screen.columns)):
                    if skip_next:
                        skip_next = False
                        continue
                    cell = line[x]
                    char_data = cell.data or " "
                    if active_cursor_col is not None and x == active_cursor_col:
                        char_data = self._cursor_char
                    fmt = self._format_for_char(cell)
                    if fmt is not current_fmt:
                        if run_text:
                            cursor.insertText("".join(run_text), current_fmt or self._default_format)
                            run_text = []
                        current_fmt = fmt
                    run_text.append(char_data)
                    if wcwidth(char_data) == 2:
                        skip_next = True
                if run_text:
                    cursor.insertText("".join(run_text), current_fmt or self._default_format)
            if row_idx < len(lines) - 1:
                cursor.insertText("\n", self._default_format)

        self.output_text.blockSignals(False)
        end_cursor = self.output_text.textCursor()
        end_cursor.movePosition(QTextCursor.End)
        self.output_text.setTextCursor(end_cursor)
        self.output_text.ensureCursorVisible()

    def _needs_full_refresh(self, lines, cursor_line, cursor_col):
        """判断是否需要全量刷新"""
        # 首次渲染
        if not self._last_screen_lines:
            return True
        # 行数变化
        if len(self._last_screen_lines) != len(lines):
            return True
        # 光标移动超过一定距离
        last_line, _ = self._last_cursor_pos or (None, None)
        if last_line is not None and cursor_line is not None:
            if abs(last_line - cursor_line) > 5:  # 光标跳跃超过5行
                return True
        return False

    def _refresh_view_incremental(self):
        """优化的视图刷新，减少不必要的重绘"""
        if self._screen is None:
            self.output_text.setPlainText("")
            self._last_screen_lines = []
            return

        lines, history_len = self._collect_screen_lines()
        cursor_line = history_len + self._screen.cursor.y if self._cursor_visible else None
        cursor_col = self._screen.cursor.x if self._cursor_visible else None
        if cursor_col is not None:
            cursor_col = min(cursor_col, self._screen.columns - 1)

        # 转换为可比较的行字符串
        current_lines = [self._line_to_string(line) for line in lines]

        # 判断是否需要全量刷新
        if self._needs_full_refresh(lines, cursor_line, cursor_col):
            self._refresh_view()
            self._last_screen_lines = current_lines
            self._last_cursor_pos = (cursor_line, cursor_col)
            return

        # 计算变更行数
        changed_count = sum(1 for i, line in enumerate(current_lines)
                           if i >= len(self._last_screen_lines) or self._last_screen_lines[i] != line)

        # 变更太多时全量刷新更高效
        if changed_count > len(lines) * 0.25:  # 超过25%行变更
            self._refresh_view()
            self._last_screen_lines = current_lines
            self._last_cursor_pos = (cursor_line, cursor_col)
            return

        # 没有实际内容变更，只更新光标
        if changed_count == 0 and self._last_cursor_pos == (cursor_line, cursor_col):
            return

        # 内容有变更，执行全量刷新（但跳过重绘后的光标定位）
        self._refresh_view_fast(cursor_line, cursor_col)
        self._last_screen_lines = current_lines
        self._last_cursor_pos = (cursor_line, cursor_col)

    def _line_to_string(self, line):
        """将行转换为字符串用于比较"""
        chars = []
        for x in range(self._screen.columns):
            cell = line[x]
            data = cell.data or " "
            chars.append(data)
            if wcwidth(data) == 2:
                chars.append(" ")
        return "".join(chars)

    def _refresh_view_fast(self, cursor_line, cursor_col):
        """快速刷新，不移动光标到末尾"""
        if self._screen is None:
            return

        lines, history_len = self._collect_screen_lines()

        self.output_text.blockSignals(True)
        doc = self.output_text.document()
        doc.clear()
        cursor = QTextCursor(doc)

        for row_idx, line in enumerate(lines):
            active_cursor_col = cursor_col if row_idx == cursor_line else None
            right_bound = self._line_right_bound(line, active_cursor_col)
            if right_bound >= 0:
                current_fmt = None
                run_text = []
                skip_next = False
                for x in range(min(right_bound + 1, self._screen.columns)):
                    if skip_next:
                        skip_next = False
                        continue
                    cell = line[x]
                    char_data = cell.data or " "
                    if active_cursor_col is not None and x == active_cursor_col:
                        char_data = self._cursor_char
                    fmt = self._format_for_char(cell)
                    if fmt is not current_fmt:
                        if run_text:
                            cursor.insertText("".join(run_text), current_fmt or self._default_format)
                            run_text = []
                        current_fmt = fmt
                    run_text.append(char_data)
                    if wcwidth(char_data) == 2:
                        skip_next = True
                if run_text:
                    cursor.insertText("".join(run_text), current_fmt or self._default_format)
            if row_idx < len(lines) - 1:
                cursor.insertText("\n", self._default_format)

        self.output_text.blockSignals(False)

        # 只在光标位置有效时移动光标
        if cursor_line is not None:
            cursor = self.output_text.textCursor()
            cursor.movePosition(QTextCursor.Start)
            for _ in range(cursor_line):
                cursor.movePosition(QTextCursor.Down)
            cursor.movePosition(QTextCursor.StartOfLine)
            if cursor_col > 0:
                cursor.movePosition(QTextCursor.Right, QTextCursor.MoveAnchor, min(cursor_col, self._screen.columns - 1))
            self.output_text.setTextCursor(cursor)
            self.output_text.ensureCursorVisible()
