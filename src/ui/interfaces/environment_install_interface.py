"""
环境配置界面
实现 openEuler 开发环境的安装配置功能
"""

import os
import json
import zipfile
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QScrollArea, QFileDialog, QProgressBar, QMessageBox,
    QApplication
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
from qfluentwidgets import (
    CardWidget, PrimaryPushButton, TransparentPushButton,
    SubtitleLabel, BodyLabel, CaptionLabel, StrongBodyLabel,
    FluentIcon as FIF, IconWidget, LineEdit, PushButton,
    CheckBox, ToolButton, ProgressBar, TextEdit
)
import winreg
import ctypes
from core.font_manager import FontManager
from core.config_manager import get_program_dir


class InstallThread(QThread):
    """安装线程"""
    progress_update = pyqtSignal(str, int)  # (消息, 进度百分比)
    log_update = pyqtSignal(str)  # 日志消息
    finished = pyqtSignal(bool, str)  # (是否成功, 消息)

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.is_running = True

    def stop(self):
        self.is_running = False

    def run(self):
        try:
            target_dir = self.config['target_dir']
            source_dir = self.config['source_dir']

            # 步骤列表
            steps = []
            if self.config.get('install_cmake', False):
                steps.append(('安装 CMake', self._install_cmake))
            if self.config.get('install_openssh', False):
                steps.append(('安装 OpenSSH', self._install_openssh))
            if self.config.get('extract_toolchain', False):
                steps.append(('安装工具链', self._extract_toolchain))
            if self.config.get('extract_libs', False):
                steps.append(('安装库文件', self._extract_libs))
            if self.config.get('extract_mingw', False):
                steps.append(('安装 MinGW64', self._extract_mingw))
            if self.config.get('extract_vscode', False):
                steps.append(('安装 VSCode', self._extract_vscode))
                # VSCode 扩展作为 VSCode 的子步骤
                if self.config.get('install_vscode_extensions', False):
                    steps.append(('安装 VSCode 插件', self._extract_vscode_extensions))

            total_steps = len(steps)
            if total_steps == 0:
                self.finished.emit(False, "请至少选择一个安装步骤")
                return

            for i, (step_name, step_func) in enumerate(steps):
                if not self.is_running:
                    self.finished.emit(False, "用户取消安装")
                    return

                self.log_update.emit(f"\n{'='*50}")
                self.log_update.emit(f"步骤 {i+1}/{total_steps}: {step_name}")
                self.log_update.emit(f"{'='*50}")

                success = step_func(target_dir, source_dir)
                progress = int((i + 1) * 100 / total_steps)
                self.progress_update.emit(f"{step_name} - {'完成' if success else '失败'}", progress)

                if not success:
                    self.log_update.emit(f"⚠️ {step_name} 失败，但继续执行后续步骤")

            # 添加到 PATH
            if self.config.get('add_to_path', False):
                self.log_update.emit(f"\n{'='*50}")
                self.log_update.emit("添加环境变量到 PATH")
                self.log_update.emit(f"{'='*50}")
                self._add_to_path(target_dir)

            # 写入安装信息
            self._write_install_info(target_dir)

            self.finished.emit(True, "安装完成！")
            self.log_update.emit(f"\n✅ 安装成功完成！")

        except subprocess.SubprocessError as e:
            self.finished.emit(False, f"安装命令执行失败: {str(e)}")
            self.log_update.emit(f"❌ 命令执行错误: {str(e)}")
        except OSError as e:
            self.finished.emit(False, f"系统错误: {str(e)}")
            self.log_update.emit(f"❌ 系统错误: {str(e)}")
        except zipfile.BadZipFile as e:
            self.finished.emit(False, f"压缩文件损坏: {str(e)}")
            self.log_update.emit(f"❌ 压缩文件错误: {str(e)}")

    def _install_cmake(self, target_dir, source_dir):
        msi_path = str(Path(source_dir) / "cmake.msi")
        if not os.path.exists(msi_path):
            self.log_update.emit(f"⚠️ 未找到 cmake.msi，跳过此步骤")
            return False

        self.log_update.emit(f"🔧 正在安装 CMake...")
        try:
            subprocess.run(
                ["msiexec", "/i", msi_path, "/quiet", "/norestart"],
                check=True,
                capture_output=True
            )
            self.log_update.emit(f"✅ CMake 安装完成")
            return True
        except subprocess.CalledProcessError as e:
            self.log_update.emit(f"❌ CMake 安装失败: 返回码 {e.returncode}")
            return False
        except subprocess.SubprocessError as e:
            self.log_update.emit(f"❌ CMake 安装失败: {str(e)}")
            return False
        except FileNotFoundError:
            self.log_update.emit(f"❌ msiexec 命令未找到")
            return False

    def _install_openssh(self, target_dir, source_dir):
        """安装 OpenSSH"""
        msi_path = str(Path(source_dir) / "OpenSSH.msi")
        if not os.path.exists(msi_path):
            self.log_update.emit(f"⚠️ 未找到 OpenSSH.msi，跳过此步骤")
            return False

        self.log_update.emit(f"🔧 正在安装 OpenSSH...")
        try:
            subprocess.run(
                ["msiexec", "/i", msi_path, "/quiet", "/norestart"],
                check=True,
                capture_output=True
            )
            self.log_update.emit(f"✅ OpenSSH 安装完成")
            return True
        except subprocess.CalledProcessError as e:
            self.log_update.emit(f"❌ OpenSSH 安装失败: 返回码 {e.returncode}")
            return False
        except subprocess.SubprocessError as e:
            self.log_update.emit(f"❌ OpenSSH 安装失败: {str(e)}")
            return False
        except FileNotFoundError:
            self.log_update.emit(f"❌ msiexec 命令未找到")
            return False

    def _extract_zip(self, zip_path, target_path, name):
        """使用 Python zipfile 安装"""
        if not os.path.exists(zip_path):
            self.log_update.emit(f"⚠️ 未找到 {name}，跳过此步骤")
            return False

        self.log_update.emit(f"📦 正在安装 {name} 到 {target_path}")
        target_path_obj = Path(target_path)
        try:
            target_path_obj.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # 获取文件列表
                file_list = zip_ref.namelist()
                total_files = len(file_list)

                for i, file in enumerate(file_list):
                    if not self.is_running:
                        return False
                    zip_ref.extract(file, target_path)
                    if i % 10 == 0:  # 每10个文件更新一次
                        progress = int((i + 1) * 100 / total_files)
                        self.progress_update.emit(f"安装 {name}", progress)

            self.log_update.emit(f"✅ {name} 安装完成")
            return True
        except zipfile.BadZipFile:
            self.log_update.emit(f"❌ 安装 {name} 失败: 压缩文件损坏或格式不支持")
            return False
        except PermissionError:
            self.log_update.emit(f"❌ 安装 {name} 失败: 权限不足")
            return False
        except OSError as e:
            self.log_update.emit(f"❌ 安装 {name} 失败: {str(e)}")
            return False

    def _extract_toolchain(self, target_dir, source_dir):
        return self._extract_zip(
            str(Path(source_dir) / "Toolchain"),
            target_dir,
            "工具链"
        )

    def _extract_libs(self, target_dir, source_dir):
        return self._extract_zip(
            str(Path(source_dir) / "libs"),
            target_dir,
            "库文件"
        )

    def _extract_mingw(self, target_dir, source_dir):
        return self._extract_zip(
            str(Path(source_dir) / "mingw64"),
            target_dir,
            "MinGW64"
        )

    def _extract_vscode(self, target_dir, source_dir):
        vscode_dir = str(Path(target_dir) / "VSCode")
        result = self._extract_zip(
            str(Path(source_dir) / "VSCode"),
            vscode_dir,
            "VSCode"
        )

        # 安装完成后创建桌面快捷方式
        if result:
            self._create_vscode_shortcut(vscode_dir)

        return result

    def _create_vscode_shortcut(self, vscode_dir):
        """创建 VSCode 桌面快捷方式"""
        try:
            code_exe = Path(vscode_dir) / "Code.exe"
            if not code_exe.exists():
                self.log_update.emit(f"⚠️ 未找到 Code.exe，跳过创建快捷方式")
                return

            # 获取桌面路径
            desktop = Path.home() / "Desktop"
            shortcut_path = str(desktop / "Code.lnk")

            # 使用 PowerShell 创建快捷方式
            ps_script = f'''
            $WshShell = New-Object -comObject WScript.Shell
            $Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
            $Shortcut.TargetPath = "{code_exe}"
            $Shortcut.WorkingDirectory = "{vscode_dir}"
            $Shortcut.Description = "Visual Studio Code"
            $Shortcut.Save()
            '''

            subprocess.run(
                ["powershell", "-Command", ps_script],
                check=True,
                capture_output=True,
                text=True
            )

            self.log_update.emit(f"✅ 已创建桌面快捷方式: {shortcut_path}")

        except subprocess.CalledProcessError as e:
            self.log_update.emit(f"⚠️ 创建快捷方式失败: PowerShell 返回错误 (返回码 {e.returncode})")
        except subprocess.SubprocessError as e:
            self.log_update.emit(f"⚠️ 创建快捷方式失败: {str(e)}")
        except OSError as e:
            self.log_update.emit(f"⚠️ 创建快捷方式失败: {str(e)}")

    def _add_to_path(self, target_dir):
        """添加到系统 PATH"""
        paths_to_add = []
        target_path = Path(target_dir)

        # MinGW64 bin
        mingw_bin = target_path / "mingw64" / "bin"
        if mingw_bin.exists():
            paths_to_add.append(str(mingw_bin))

        # ARM Toolchain bin
        toolchain_base = target_path / "Arm GNU Toolchain aarch64-none-linux-gnu"
        if toolchain_base.exists():
            for item in toolchain_base.iterdir():
                item_path = item / "bin"
                if item_path.exists():
                    paths_to_add.append(str(item_path))
                    break

        # CMake bin (如果安装了CMake)
        cmake_bin = Path(r"C:\Program Files\CMake\bin")
        if cmake_bin.exists():
            paths_to_add.append(str(cmake_bin))

        # VSCode (如果安装了VSCode)
        vscode_dir = target_path / "VSCode"
        if vscode_dir.exists():
            # 优先添加 bin 目录 (包含 code 命令)
            vscode_bin = vscode_dir / "bin"
            if vscode_bin.exists():
                paths_to_add.append(str(vscode_bin))
            # 同时也添加根目录 (包含 Code.exe)
            if (vscode_dir / "Code.exe").exists():
                paths_to_add.append(str(vscode_dir))

        # 添加到用户环境变量
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Environment",
                0,
                winreg.KEY_READ | winreg.KEY_WRITE
            )

            try:
                current_path, _ = winreg.QueryValueEx(key, "Path")
            except FileNotFoundError:
                current_path = ""

            current_paths = current_path.split(';') if current_path else []
            added_count = 0

            for path in paths_to_add:
                if path not in current_paths and os.path.exists(path):
                    if current_path:
                        current_path += ';' + path
                    else:
                        current_path = path
                    self.log_update.emit(f"✅ 添加到 PATH: {path}")
                    added_count += 1

            winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, current_path)
            winreg.CloseKey(key)

            # 通知系统环境变量已更改
            import ctypes
            HWND_BROADCAST = 0xFFFF
            WM_SETTINGCHANGE = 0x1A
            SMTO_ABORTIFHUNG = 0x0002
            result = ctypes.c_long()
            ctypes.windll.user32.SendMessageTimeoutW(
                HWND_BROADCAST,
                WM_SETTINGCHANGE,
                0,
                "Environment",
                SMTO_ABORTIFHUNG,
                5000,
                ctypes.byref(result)
            )

            if added_count == 0:
                self.log_update.emit(f"ℹ️ 所有路径已在 PATH 中")

        except PermissionError:
            self.log_update.emit(f"❌ 更新 PATH 失败: 权限不足，请以管理员身份运行")
        except OSError as e:
            self.log_update.emit(f"❌ 更新 PATH 失败: {str(e)}")

    def _extract_vscode_extensions(self, target_dir, source_dir):
        """安装VSCode插件"""
        extensions_file = str(Path(source_dir) / "extensions")
        if not Path(extensions_file).exists():
            self.log_update.emit(f"⚠️ 未找到 extensions，跳过VSCode插件安装")
            return False

        # 获取当前用户目录
        vscode_extensions_dir = Path.home() / ".vscode"

        self.log_update.emit(f"📦 正在安装VSCode插件到 {vscode_extensions_dir}")
        try:
            vscode_extensions_dir.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(extensions_file, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                total_files = len(file_list)

                for i, file in enumerate(file_list):
                    if not self.is_running:
                        return False
                    zip_ref.extract(file, str(vscode_extensions_dir))
                    if i % 10 == 0:
                        progress = int((i + 1) * 100 / total_files)
                        self.progress_update.emit(f"安装VSCode插件", progress)

            self.log_update.emit(f"✅ VSCode插件安装完成")
            return True
        except zipfile.BadZipFile:
            self.log_update.emit(f"❌ 安装VSCode插件失败: 压缩文件损坏")
            return False
        except PermissionError:
            self.log_update.emit(f"❌ 安装VSCode插件失败: 权限不足")
            return False
        except OSError as e:
            self.log_update.emit(f"❌ 安装VSCode插件失败: {str(e)}")
            return False

    def _write_install_info(self, target_dir):
        """写入安装信息"""
        info = {
            "schema_version": 1,
            "product": "openEulerEnvironment",
            "version": "1.0.0",
            "install_state": "complete",
            "installed_at_utc": datetime.utcnow().isoformat() + "Z",
            "paths": {
                "root": target_dir
            }
        }

        info_path = Path(target_dir) / "openEuler_install_info.json"
        try:
            info_path.parent.mkdir(parents=True, exist_ok=True)
            with open(info_path, 'w', encoding='utf-8') as f:
                json.dump(info, f, indent=2, ensure_ascii=False)
            self.log_update.emit(f"✅ 安装信息已写入")
        except PermissionError:
            self.log_update.emit(f"⚠️ 写入安装信息失败: 权限不足")
        except OSError as e:
            self.log_update.emit(f"⚠️ 写入安装信息失败: {str(e)}")


class EnvironmentInstallInterface(QWidget):
    """环境配置界面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("environmentInstallInterface")
        self.install_thread = None

        # 获取程序所在目录与模块目录
        self.program_dir = get_program_dir()
        self.source_dir = self._get_source_dir()

        self.init_ui()

    def _get_source_dir(self):
        return str(Path(self.program_dir) / "modules")

    def _is_admin(self):
        """检查是否以管理员权限运行"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except Exception:
            return False

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(20)

        # 标题
        title = SubtitleLabel("开发环境配置")
        title.setStyleSheet(f"color: #2D3748; font-size: {FontManager.get_font_size('large_title')}px;")
        layout.addWidget(title)

        # 说明文字
        desc = BodyLabel("配置 openEuler 开发所需的编译工具链、依赖库和开发工具")
        desc.setStyleSheet(f"color: #5A6A7A; font-size: {FontManager.get_font_size('body')}px;")
        layout.addWidget(desc)

        # 管理员权限提示
        if not self._is_admin():
            admin_warning = CardWidget()
            admin_warning.setStyleSheet("""
                CardWidget {
                    background-color: #FFF3CD;
                    border: 2px solid #FFC107;
                    border-radius: 8px;
                }
            """)
            warning_layout = QHBoxLayout(admin_warning)
            warning_layout.setContentsMargins(16, 12, 16, 12)

            warning_text = BodyLabel("⚠️ 注意应以管理员身份运行：否则 CMake 和 OpenSSH 安装可能失败")
            warning_text.setStyleSheet("color: #856404; font-size: 14px; font-weight: bold;")

            warning_layout.addWidget(warning_text, 1)
            layout.addWidget(admin_warning)

        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(20)

        # 安装目录卡片
        dir_card = self._create_directory_card()
        content_layout.addWidget(dir_card)

        # 安装选项卡片
        options_card = self._create_options_card()
        content_layout.addWidget(options_card)

        # 操作按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # 如果不是管理员，显示"以管理员身份安装"按钮
        if not self._is_admin():
            self.elevate_btn = PushButton("🛡️ 以管理员身份运行")
            self.elevate_btn.setFixedSize(200, 40)
            self.elevate_btn.setStyleSheet("""
                PushButton {
                    background-color: #FFFFFF;
                    color: #2D3748;
                    border: 1px solid #E2E8F0;
                    border-radius: 6px;
                    font-weight: bold;
                }
                PushButton:hover {
                    background-color: #F7FAFC;
                    border-color: #CBD5E0;
                }
                PushButton:pressed {
                    background-color: #EDF2F7;
                }
            """)
            self.elevate_btn.clicked.connect(self._restart_as_admin)
            button_layout.addWidget(self.elevate_btn)
            button_layout.addSpacing(20)

        self.start_btn = PrimaryPushButton("开始安装")
        self.start_btn.setFixedSize(140, 40)
        self.start_btn.clicked.connect(self._start_install)

        button_layout.addWidget(self.start_btn)
        button_layout.addStretch()
        content_layout.addLayout(button_layout)

        # 进度条
        self.progress_bar = ProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(8)
        content_layout.addWidget(self.progress_bar)

        # 日志区域
        log_label = StrongBodyLabel("安装日志")
        log_label.setStyleSheet(f"font-size: {FontManager.get_font_size('title')}px; color: #2D3748;")
        content_layout.addWidget(log_label)

        self.log_text = TextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFixedHeight(200)
        self.log_text.setStyleSheet(f"""
            TextEdit {{
                background-color: #1E1E1E;
                color: #D4D4D4;
                border: 1px solid #3E3E3E;
                border-radius: 6px;
                padding: 10px;
                font-family: 'Consolas', 'Microsoft YaHei UI', monospace;
            }}
        """)
        content_layout.addWidget(self.log_text)

        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)

        # 初始化日志
        self._log("欢迎使用开发环境配置工具！")
        self._log(f"源文件目录: {self.source_dir}")
        self._log("请选择安装目录并勾选需要安装的组件")

    def _create_directory_card(self):
        """创建安装目录卡片"""
        card = CardWidget()
        card.setFixedHeight(120)
        card.setStyleSheet("""
            CardWidget {
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 12px;
                border: 1px solid rgba(0, 0, 0, 0.06);
            }
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 18, 24, 18)

        title = StrongBodyLabel("安装目录")
        title.setStyleSheet(f"font-size: {FontManager.get_font_size('title')}px; color: #2D3748;")
        layout.addWidget(title)

        # 目录选择行
        dir_layout = QHBoxLayout()
        dir_layout.setSpacing(10)

        self.install_dir_edit = LineEdit()
        self.install_dir_edit.setPlaceholderText("选择安装目录")
        self.install_dir_edit.setText(r"C:\openEulerEnvironment")
        self.install_dir_edit.setFixedHeight(36)
        self.install_dir_edit.setStyleSheet("""
            LineEdit {
                border-radius: 6px;
            }
        """)
        dir_layout.addWidget(self.install_dir_edit)

        browse_btn = ToolButton(FIF.FOLDER, self)
        browse_btn.setFixedSize(36, 36)
        browse_btn.clicked.connect(self._browse_directory)
        dir_layout.addWidget(browse_btn)

        layout.addLayout(dir_layout)
        return card

    def _create_options_card(self):
        """创建安装选项卡片"""
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
        layout.setSpacing(15)

        title = StrongBodyLabel("安装组件")
        title.setStyleSheet(f"font-size: {FontManager.get_font_size('title')}px; color: #2D3748;")
        layout.addWidget(title)

        # 创建复选框网格 - 使用4行2列布局
        grid = QGridLayout()
        grid.setSpacing(12)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        self.checkboxes = {}

        # 定义所有选项及其位置 (行, 列)
        options = [
            ('install_cmake', '安装 CMake', 'cmake.msi', FIF.SETTING, 0, 0),
            ('install_openssh', '安装 OpenSSH', 'OpenSSH.msi', FIF.SEND, 0, 1),
            ('extract_toolchain', '安装工具链', 'Toolchain', FIF.APPLICATION, 1, 0),
            ('extract_libs', '安装库文件', 'libs', FIF.LIBRARY, 1, 1),
            ('extract_mingw', '安装 MinGW64', 'mingw64', FIF.DEVELOPER_TOOLS, 2, 0),
            ('add_to_path', '添加到 PATH', '', FIF.SYNC, 3, 0),
        ]

        # 处理普通选项
        for key, name, filename, icon, row, col in options:
            checkbox = CheckBox(name)
            checkbox.setChecked(True)
            checkbox.setStyleSheet("color: #2D3748;")
            self.checkboxes[key] = (checkbox, filename)

            # 检查文件是否存在
            if filename:
                file_path = Path(self.source_dir) / filename
                if not file_path.exists():
                    checkbox.setChecked(False)
                    checkbox.setEnabled(False)
                    name_label = BodyLabel(f" ({filename} 未找到)")
                    name_label.setStyleSheet("color: #D83B01;")

                    row_widget = QWidget()
                    row_layout = QHBoxLayout(row_widget)
                    row_layout.setContentsMargins(0, 0, 0, 0)
                    row_layout.setSpacing(6)
                    row_layout.addWidget(checkbox)
                    row_layout.addWidget(name_label)
                    row_layout.addStretch()

                    grid.addWidget(row_widget, row, col)
                else:
                    grid.addWidget(checkbox, row, col)
            else:
                grid.addWidget(checkbox, row, col)

        # VSCode 选项单独处理（放在第2行第1列，占两行位置）
        vscode_container = QWidget()
        vscode_layout = QVBoxLayout(vscode_container)
        vscode_layout.setContentsMargins(0, 0, 0, 0)
        vscode_layout.setSpacing(8)

        vscode_checkbox = CheckBox('安装 VSCode')
        vscode_checkbox.setChecked(True)
        vscode_checkbox.setStyleSheet("color: #2D3748;")

        # 检查 VSCode 是否存在
        vscode_path = Path(self.source_dir) / "VSCode"
        if not vscode_path.exists():
            vscode_checkbox.setChecked(False)
            vscode_checkbox.setEnabled(False)
            vscode_label = BodyLabel(" (VSCode 未找到)")
            vscode_label.setStyleSheet("color: #D83B01;")

            vscode_row = QWidget()
            vscode_row_layout = QHBoxLayout(vscode_row)
            vscode_row_layout.setContentsMargins(0, 0, 0, 0)
            vscode_row_layout.setSpacing(6)
            vscode_row_layout.addWidget(vscode_checkbox)
            vscode_row_layout.addWidget(vscode_label)
            vscode_row_layout.addStretch()
            vscode_layout.addWidget(vscode_row)
        else:
            vscode_layout.addWidget(vscode_checkbox)

        self.checkboxes['extract_vscode'] = (vscode_checkbox, 'VSCode')

        # VSCode 插件子选项
        self.vscode_ext_checkbox = CheckBox("安装 VSCode 插件")
        self.vscode_ext_checkbox.setChecked(True)
        self.vscode_ext_checkbox.setStyleSheet("color: #5A6A7A;")

        # 检查 extensions 是否存在
        extensions_path = Path(self.source_dir) / "extensions"
        if not extensions_path.exists():
            self.vscode_ext_checkbox.setChecked(False)
            self.vscode_ext_checkbox.setEnabled(False)
            ext_label = BodyLabel(" (extensions 未找到)")
            ext_label.setStyleSheet("color: #D83B01;")

            ext_row = QWidget()
            ext_row_layout = QHBoxLayout(ext_row)
            ext_row_layout.setContentsMargins(0, 0, 0, 0)
            ext_row_layout.setSpacing(6)
            ext_row_layout.addWidget(self.vscode_ext_checkbox)
            ext_row_layout.addWidget(ext_label)
            ext_row_layout.addStretch()
            vscode_layout.addWidget(ext_row)
        else:
            vscode_layout.addWidget(self.vscode_ext_checkbox)

        # VSCode 复选框状态变化时，控制扩展复选框
        vscode_checkbox.stateChanged.connect(
            lambda state: self.vscode_ext_checkbox.setEnabled(state == Qt.Checked)
        )

        # VSCode 容器放在第2行第1列，跨越两行
        grid.addWidget(vscode_container, 2, 1, 2, 1)

        layout.addLayout(grid)

        # 全选/取消全选
        select_layout = QHBoxLayout()
        select_layout.addStretch()

        select_all_btn = TransparentPushButton("全选")
        select_all_btn.clicked.connect(self._select_all)
        select_layout.addWidget(select_all_btn)

        deselect_all_btn = TransparentPushButton("取消全选")
        deselect_all_btn.clicked.connect(self._deselect_all)
        select_layout.addWidget(deselect_all_btn)

        select_layout.addStretch()
        layout.addLayout(select_layout)

        return card

    def _browse_directory(self):
        """浏览目录"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "选择安装目录",
            self.install_dir_edit.text()
        )
        if directory:
            self.install_dir_edit.setText(directory)

    def _select_all(self):
        """全选"""
        for key, (checkbox, _) in self.checkboxes.items():
            if checkbox.isEnabled():
                checkbox.setChecked(True)

    def _deselect_all(self):
        """取消全选"""
        for key, (checkbox, _) in self.checkboxes.items():
            checkbox.setChecked(False)

    def _log(self, message):
        """添加日志"""
        self.log_text.append(message)

    def _restart_as_admin(self):
        """以管理员身份重新启动程序（支持Win7/Win10/Win11）"""
        import sys

        try:
            # 获取当前可执行文件路径
            if getattr(sys, 'frozen', False):
                # PyInstaller打包后的程序
                program = sys.executable
                params = ""
            else:
                # Python脚本模式 - 需要启动python.exe并传入脚本
                program = sys.executable
                # 构建参数：脚本路径 + 其他参数
                script_path = os.path.abspath(sys.argv[0])
                params = f'"{script_path}"'
                if len(sys.argv) > 1:
                    params += " " + " ".join(f'"{arg}"' for arg in sys.argv[1:])

            # 使用ShellExecuteW请求提升权限（Win7+支持）
            ret = ctypes.windll.shell32.ShellExecuteW(
                None,           # hwnd
                "runas",        # lpOperation - 请求管理员权限
                program,        # lpFile
                params,         # lpParameters
                None,           # lpDirectory
                1               # nShowCmd - SW_SHOWNORMAL
            )

            # 检查返回值：
            # > 32 表示成功
            # <= 32 表示失败（Win7下常见错误码：
            #   5 = 用户拒绝UAC，8 = 内存不足，31 = 没有关联程序等）
            if ret > 32:
                # 成功启动，关闭当前实例
                QApplication.quit()
            elif ret == 5:
                QMessageBox.information(self, "提示", "您取消了权限提升。\n部分组件可能无法正常安装。")
            else:
                QMessageBox.warning(self, "警告", f"无法启动管理员权限程序（错误码：{ret}）")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"权限提升失败：{e}")

    def _start_install(self):
        """开始安装"""
        # 收集配置
        config = {
            'target_dir': self.install_dir_edit.text(),
            'source_dir': self.source_dir,
        }

        for key, (checkbox, _) in self.checkboxes.items():
            config[key] = checkbox.isChecked()

        # 添加 VSCode 扩展选项
        config['install_vscode_extensions'] = self.vscode_ext_checkbox.isChecked()

        # 验证至少选择一项
        if not any(config[key] for key in self.checkboxes.keys()):
            QMessageBox.warning(self, "提示", "请至少选择一个安装步骤")
            return

        # 清空日志
        self.log_text.clear()

        # 禁用按钮
        self.start_btn.setEnabled(False)
        self.start_btn.setText("安装中...")

        # 创建并启动安装线程
        self.install_thread = InstallThread(config)
        self.install_thread.progress_update.connect(self._on_progress_update)
        self.install_thread.log_update.connect(self._log)
        self.install_thread.finished.connect(self._on_install_finished)
        self.install_thread.start()

    def _on_progress_update(self, message, progress):
        """进度更新"""
        self.progress_bar.setValue(progress)

    def _on_install_finished(self, success, message):
        """安装完成"""
        self.start_btn.setEnabled(True)
        self.start_btn.setText("开始安装")

        if success:
            QMessageBox.information(self, "完成", message)
        else:
            QMessageBox.warning(self, "完成", message)

        self.install_thread = None
