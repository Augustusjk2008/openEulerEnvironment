"""
代码生成界面
根据产品型号和工程类型自动生成项目代码
"""

import os
import sys
import json
import zipfile
from datetime import datetime
from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QScrollArea, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
from qfluentwidgets import (
    CardWidget, PrimaryPushButton, TransparentPushButton,
    SubtitleLabel, BodyLabel, CaptionLabel, StrongBodyLabel,
    FluentIcon as FIF, IconWidget, LineEdit, PushButton,
    ComboBox, TextEdit, InfoBar, InfoBarPosition
)


class CodeGenerateThread(QThread):
    """代码生成线程"""
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int, int)
    finished_signal = pyqtSignal(bool, str, str)  # (是否成功, 消息, 工程路径)

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.is_running = True

    def stop(self):
        self.is_running = False

    def run(self):
        try:
            model_type = self.config['model_type']
            project_type = self.config['project_type']
            project_file = self.config['project_file']
            output_dir = self.config['output_dir']

            self.log_signal.emit(f"开始生成代码...")
            self.log_signal.emit(f"型号: {model_type}")
            self.log_signal.emit(f"工程类型: {project_type}")
            self.log_signal.emit(f"工程模板: {os.path.basename(project_file)}")

            # 步骤1: 确保输出目录存在
            self.log_signal.emit(f"\n[1/1] 解压工程模板到: {output_dir}")
            os.makedirs(output_dir, exist_ok=True)

            # 步骤2: 直接解压到输出目录
            self._extract_zip(project_file, output_dir)
            self.progress_signal.emit(1, 1)

            self.log_signal.emit(f"\n✅ 代码生成完成！")
            self.log_signal.emit(f"工程路径: {output_dir}")
            self.finished_signal.emit(True, "代码生成成功！", output_dir)

        except Exception as e:
            self.log_signal.emit(f"\n❌ 生成失败: {str(e)}")
            self.finished_signal.emit(False, f"生成失败: {str(e)}", "")

    def _extract_zip(self, zip_path, target_path):
        """解压zip文件，并处理中文文件名乱码"""
        self.log_signal.emit(f"  正在解压 {os.path.basename(zip_path)}...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for info in zip_ref.infolist():
                # 解码文件名
                decoded_filename = self._decode_zip_filename(info.filename)

                # 跳过目录（以 / 结尾）
                if decoded_filename.endswith('/') or decoded_filename.endswith('\\'):
                    # 创建目录
                    dir_path = os.path.join(target_path, decoded_filename.rstrip('/\\'))
                    os.makedirs(dir_path, exist_ok=True)
                    continue

                # 解压文件到临时位置
                temp_path = zip_ref.extract(info, target_path)

                # 如果文件名需要解码，重命名文件
                if decoded_filename != info.filename:
                    final_path = os.path.join(target_path, decoded_filename)
                    # 确保目标目录存在
                    final_dir = os.path.dirname(final_path)
                    if final_dir:
                        os.makedirs(final_dir, exist_ok=True)
                    # 重命名
                    if os.path.exists(temp_path):
                        if os.path.exists(final_path):
                            # 如果目标文件已存在，先删除
                            if os.path.isfile(final_path):
                                os.remove(final_path)
                            else:
                                import shutil
                                shutil.rmtree(final_path)
                        os.rename(temp_path, final_path)

        self.log_signal.emit(f"  ✅ 解压完成")

    def _decode_zip_filename(self, filename):
        """解码 ZIP 文件中的文件名，处理中文乱码"""
        # 如果文件名只包含 ASCII 字符，直接返回
        try:
            if filename.isascii():
                return filename
        except:
            pass

        # 方法1: 尝试 CP437 -> GBK（Windows 中文系统最常见）
        try:
            decoded = filename.encode('cp437').decode('gbk')
            # 验证解码结果是否合理（包含可打印字符）
            if self._is_valid_filename(decoded):
                return decoded
        except:
            pass

        # 方法2: 尝试 CP437 -> UTF-8
        try:
            decoded = filename.encode('cp437').decode('utf-8')
            if self._is_valid_filename(decoded):
                return decoded
        except:
            pass

        # 方法3: 尝试 Latin-1 -> GBK
        try:
            decoded = filename.encode('latin-1').decode('gbk')
            if self._is_valid_filename(decoded):
                return decoded
        except:
            pass

        # 方法4: 尝试直接 UTF-8（某些工具使用 UTF-8 存储）
        try:
            decoded = filename.encode('latin-1').decode('utf-8')
            if self._is_valid_filename(decoded):
                return decoded
        except:
            pass

        # 方法5: 尝试 GB2312
        try:
            decoded = filename.encode('cp437').decode('gb2312')
            if self._is_valid_filename(decoded):
                return decoded
        except:
            pass

        # 如果都失败，返回原文件名
        return filename

    def _is_valid_filename(self, filename):
        """检查文件名是否有效（不包含非法字符）"""
        # 检查是否包含常见的中文、英文字符和符号
        if not filename:
            return False
        # 检查是否包含控制字符（除了常见的合法字符）
        for char in filename:
            code = ord(char)
            # 允许：中文、ASCII 可打印字符、常见路径符号
            if code < 32 and code not in (9, 10, 13):  # 排除控制字符
                return False
        return True


class CodeGenerationInterface(QWidget):
    """代码生成界面"""

    # 工程类型映射
    PROJECT_TYPES = {
        'Hello_World': 'Hello world',
        'MB_DDF': 'MB_DDF示例工程',
        'Helm_Control': '舵机控制工程',
        'Auto_Pilot': '自动驾驶仪工程',
        'Upgrade_And_Test': '监控和测试工程'
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("codeGenerationInterface")
        self.generate_thread = None
        self.recent_projects = self._load_recent_projects()
        self.program_dir = self._get_program_dir()
        self.last_generated_path = None  # 最后一次生成的工程路径
        self.last_generated_name = None  # 最后一次生成的工程名称
        self.recent_card = None  # 保存最近工程卡片引用，用于更新

        self.init_ui()

    def _get_program_dir(self):
        """获取程序所在目录"""
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        else:
            return os.path.dirname(os.path.abspath(__file__))

    def _load_recent_projects(self):
        """加载最近生成的工程列表"""
        return []

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(20)

        # 标题
        title = SubtitleLabel("代码生成")
        title.setStyleSheet("color: #2D3748; font-size: 28px;")
        layout.addWidget(title)

        # 说明文字
        desc = BodyLabel("根据产品型号和工程类型自动生成项目代码和目录结构")
        desc.setStyleSheet("color: #5A6A7A; font-size: 15px;")
        layout.addWidget(desc)

        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(20)

        # 配置选项卡片
        config_card = self._create_config_card()
        content_layout.addWidget(config_card)

        # 代码预览卡片
        preview_card = self._create_preview_card()
        content_layout.addWidget(preview_card)

        # 最近工程卡片
        self.recent_card = self._create_recent_projects_card()
        content_layout.addWidget(self.recent_card)

        # 日志区域
        log_label = StrongBodyLabel("生成日志")
        log_label.setStyleSheet("font-size: 16px; color: #2D3748;")
        content_layout.addWidget(log_label)

        self.log_text = TextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFixedHeight(200)
        self.log_text.setStyleSheet("""
            TextEdit {
                background-color: #1E1E1E;
                color: #D4D4D4;
                border: 1px solid #3E3E3E;
                border-radius: 6px;
                padding: 10px;
                font-family: 'Consolas', 'Microsoft YaHei UI', monospace;
                font-size: 13px;
            }
        """)
        content_layout.addWidget(self.log_text)

        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)

        # 初始化日志
        self._log("欢迎使用代码生成工具！")
        self._log('请配置工程参数后点击"生成代码"按钮')

        # 扫描并加载工程模板
        self._scan_templates()

        # 连接下拉框变化信号
        self.type_combo.currentIndexChanged.connect(self._update_preview)

    def _create_config_card(self):
        """创建配置选项卡片 - 紧凑布局2行"""
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

        title = StrongBodyLabel("工程配置")
        title.setStyleSheet("font-size: 16px; color: #2D3748;")
        layout.addWidget(title)

        # 配置网格 - 2行2列
        grid = QGridLayout()
        grid.setSpacing(12)
        grid.setColumnStretch(1, 1)

        # 第0行：产品型号 | 工程类型
        model_label = BodyLabel("产品型号:")
        model_label.setStyleSheet("font-size: 14px; color: #2D3748;")
        grid.addWidget(model_label, 0, 0)

        self.model_combo = ComboBox()
        self.model_combo.addItems(["微弹"])
        self.model_combo.setFixedHeight(36)
        self.model_combo.setStyleSheet("font-size: 14px;")
        self.model_combo.currentTextChanged.connect(self._update_preview)
        grid.addWidget(self.model_combo, 0, 1)

        type_label = BodyLabel("工程类型:")
        type_label.setStyleSheet("font-size: 14px; color: #2D3748;")
        grid.addWidget(type_label, 0, 2)

        self.type_combo = ComboBox()
        # 动态加载工程类型
        self.type_combo.setFixedHeight(36)
        self.type_combo.setStyleSheet("font-size: 14px;")
        grid.addWidget(self.type_combo, 0, 3)

        # 第1行：输出目录 + 浏览按钮 + 生成代码按钮
        dir_label = BodyLabel("输出目录:")
        dir_label.setStyleSheet("font-size: 14px; color: #2D3748;")
        grid.addWidget(dir_label, 1, 0)

        dir_layout = QHBoxLayout()
        dir_layout.setSpacing(10)

        self.dir_edit = LineEdit()
        self.dir_edit.setPlaceholderText("选择输出目录")
        self.dir_edit.setFixedHeight(36)
        self.dir_edit.setText(r"C:\Projects")
        self.dir_edit.setStyleSheet("font-size: 14px;")
        dir_layout.addWidget(self.dir_edit)

        browse_btn = PushButton("浏览")
        browse_btn.setFixedHeight(36)
        browse_btn.clicked.connect(self._browse_directory)
        dir_layout.addWidget(browse_btn)

        # 生成代码按钮
        self.generate_btn = PrimaryPushButton("生成代码")
        self.generate_btn.setFixedSize(100, 36)
        self.generate_btn.clicked.connect(self._start_generate)
        dir_layout.addWidget(self.generate_btn)

        grid.addLayout(dir_layout, 1, 1, 1, 3)

        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)
        layout.addLayout(grid)

        return card

    def _create_preview_card(self):
        """创建代码预览卡片"""
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
        layout.setSpacing(10)

        title = StrongBodyLabel("目录结构预览")
        title.setStyleSheet("font-size: 16px; color: #2D3748;")
        layout.addWidget(title)

        self.struct_preview = TextEdit()
        self.struct_preview.setReadOnly(True)
        self.struct_preview.setFixedHeight(200)
        self.struct_preview.setStyleSheet("""
            TextEdit {
                background-color: #F5F5F5;
                color: #2D3748;
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 6px;
                padding: 10px;
                font-family: 'Consolas', monospace;
                font-size: 12px;
            }
        """)
        self.struct_preview.setPlainText("请选择工程类型查看目录结构...")
        layout.addWidget(self.struct_preview)

        return card

    def _create_recent_projects_card(self):
        """创建最近工程卡片"""
        card = CardWidget()
        card.setStyleSheet("""
            CardWidget {
                background-color: rgba(249, 249, 249, 0.9);
                border-radius: 12px;
                border: 1px solid rgba(0, 0, 0, 0.06);
            }
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(10)

        title = StrongBodyLabel("最近生成的工程")
        title.setStyleSheet("font-size: 16px; color: #2D3748;")
        layout.addWidget(title)

        # 优先显示本次运行最后一次生成的工程
        if self.last_generated_path:
            # 工程名称和路径
            info_layout = QVBoxLayout()
            info_layout.setSpacing(5)

            name_label = BodyLabel(f"工程名称: {self.last_generated_name or '未知'}")
            name_label.setStyleSheet("font-size: 13px; color: #2D3748; font-weight: 600;")
            info_layout.addWidget(name_label)

            path_label = CaptionLabel(f"工程路径: {self.last_generated_path}")
            path_label.setStyleSheet("font-size: 11px; color: #7A8A9A;")
            info_layout.addWidget(path_label)

            layout.addLayout(info_layout)

            # 打开按钮
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            open_btn = TransparentPushButton("打开工程目录")
            open_btn.setFixedHeight(28)
            open_btn.clicked.connect(lambda checked, p=self.last_generated_path: self._open_project(p))
            button_layout.addWidget(open_btn)
            layout.addLayout(button_layout)
        else:
            empty_label = BodyLabel("暂无最近生成的工程")
            empty_label.setStyleSheet("font-size: 13px; color: #A0A0A0;")
            layout.addWidget(empty_label)

        return card

    def _update_recent_card(self):
        """更新最近工程卡片"""
        if self.recent_card is not None:
            # 移除旧卡片
            parent = self.recent_card.parent()
            if parent:
                parent.layout().removeWidget(self.recent_card)
            self.recent_card.deleteLater()

            # 创建新卡片
            self.recent_card = self._create_recent_projects_card()
            # 找到 content_widget 并添加新卡片
            scroll = self.findChild(QScrollArea)
            if scroll:
                content = scroll.widget()
                if content:
                    # 在 preview_card 之后插入
                    content.layout().insertWidget(2, self.recent_card)

    def _scan_templates(self):
        """扫描程序目录下的templates文件夹，加载工程模板"""
        programs_dir = os.path.join(self.program_dir, "programs")

        self.template_files = {}
        found_templates = []

        if os.path.exists(programs_dir):
            # 查找5个工程模板文件
            for template_name in ['Hello_World', 'MB_DDF', 'Helm_Control', 'Auto_Pilot', 'Upgrade_And_Test']:
                template_path = os.path.join(programs_dir, template_name)
                if os.path.exists(template_path):
                    self.template_files[template_name] = template_path
                    found_templates.append(template_name)
                    self._log(f"发现工程模板: {template_name}")
                else:
                    self._log(f"⚠️ 未找到工程模板: {template_name}")

        # 更新下拉框
        self.type_combo.clear()
        for template_name in found_templates:
            display_name = self.PROJECT_TYPES.get(template_name, template_name)
            self.type_combo.addItem(display_name, template_name)

        if found_templates:
            # 设置默认选中第一项
            self.type_combo.setCurrentIndex(0)
            self._update_preview()

    def _update_preview(self):
        """更新预览信息"""
        # 尝试多种方式获取数据
        current_index = self.type_combo.currentIndex()
        current_text = self.type_combo.currentText()
        current_data = self.type_combo.currentData()

        print(f"调试: currentIndex={current_index}, currentText={current_text}, currentData={current_data}")

        # 如果 currentData() 返回 None，尝试用 itemData()
        if current_data is None and current_index >= 0:
            current_data = self.type_combo.itemData(current_index)
            print(f"调试: 使用 itemData({current_index}) = {current_data}")

        # 如果还是 None，尝试通过文本反向查找
        if current_data is None:
            for template_name, display_name in self.PROJECT_TYPES.items():
                if display_name == current_text and template_name in self.template_files:
                    current_data = template_name
                    print(f"调试: 通过文本反向查找 = {current_data}")
                    break

        if not current_data:
            self.struct_preview.setPlainText("请选择工程类型")
            return

        template_file = self.template_files.get(current_data)
        if not template_file:
            self.struct_preview.setPlainText(f"未找到模板文件: {current_data}")
            return

        if not os.path.exists(template_file):
            self.struct_preview.setPlainText(f"模板文件不存在:\n{template_file}")
            return

        # 读取zip文件内容
        try:
            structure = self._get_zip_structure(template_file)
            self.struct_preview.setPlainText(structure)
        except Exception as e:
            self.struct_preview.setPlainText(f"无法读取模板文件:\n{str(e)}")

    def _get_zip_structure(self, zip_path):
        """获取zip文件的目录结构"""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                raw_files = zip_ref.namelist()

                if not raw_files:
                    return "空文件"

                # 修复中文文件名乱码 - 尝试多种编码
                files = []
                for f in raw_files:
                    # 尝试解码文件名
                    decoded_name = self._decode_zip_filename(f)
                    files.append(decoded_name)

                # 构建目录树
                tree = {}
                for file in files:
                    if file.endswith('/') or file.endswith('\\'):
                        continue
                    # 支持两种路径分隔符
                    parts = file.replace('\\', '/').split('/')
                    current = tree
                    for part in parts:
                        if part and part not in current:
                            current[part] = {}
                        if part:
                            current = current[part]

                # 生成树形文本
                return self._format_tree(tree, "")
        except Exception as e:
            return f"读取失败: {str(e)}"

    def _decode_zip_filename(self, filename):
        """解码 ZIP 文件中的文件名，处理中文乱码"""
        # 如果文件名只包含 ASCII 字符，直接返回
        try:
            if filename.isascii():
                return filename
        except:
            pass

        # 方法1: 尝试 CP437 -> GBK（Windows 中文系统最常见）
        try:
            decoded = filename.encode('cp437').decode('gbk')
            if self._is_valid_filename(decoded):
                return decoded
        except:
            pass

        # 方法2: 尝试 CP437 -> UTF-8
        try:
            decoded = filename.encode('cp437').decode('utf-8')
            if self._is_valid_filename(decoded):
                return decoded
        except:
            pass

        # 方法3: 尝试 Latin-1 -> GBK
        try:
            decoded = filename.encode('latin-1').decode('gbk')
            if self._is_valid_filename(decoded):
                return decoded
        except:
            pass

        # 方法4: 尝试直接 UTF-8（某些工具使用 UTF-8 存储）
        try:
            decoded = filename.encode('latin-1').decode('utf-8')
            if self._is_valid_filename(decoded):
                return decoded
        except:
            pass

        # 方法5: 尝试 GB2312
        try:
            decoded = filename.encode('cp437').decode('gb2312')
            if self._is_valid_filename(decoded):
                return decoded
        except:
            pass

        # 如果都失败，返回原文件名
        return filename

    def _is_valid_filename(self, filename):
        """检查文件名是否有效（不包含非法字符）"""
        if not filename:
            return False
        for char in filename:
            code = ord(char)
            if code < 32 and code not in (9, 10, 13):
                return False
        return True

    def _format_tree(self, tree, prefix, is_last=True):
        """格式化树形结构"""
        lines = []
        items = list(tree.keys())

        for i, item in enumerate(items):
            is_last_item = (i == len(items) - 1)
            connector = "└── " if is_last_item else "├── "

            lines.append(f"{prefix}{connector}{item}")

            if tree[item]:
                # 有子项 - 使用 extend 拆分递归返回的字符串
                new_prefix = prefix + ("    " if is_last_item else "│   ")
                subtree = self._format_tree(tree[item], new_prefix, is_last_item)
                lines.extend(subtree.split('\n'))

        return "\n".join(lines)

    def _browse_directory(self):
        """浏览目录"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "选择输出目录",
            self.dir_edit.text()
        )
        if directory:
            self.dir_edit.setText(directory)

    def _start_generate(self):
        """开始生成"""
        # 验证输入 - 使用多种方式获取选中项
        current_index = self.type_combo.currentIndex()
        current_text = self.type_combo.currentText()
        current_data = self.type_combo.currentData()

        self._log(f"调试: currentIndex={current_index}, currentText={current_text}, currentData={current_data}")

        # 如果 currentData() 返回 None，尝试用 itemData()
        if current_data is None and current_index >= 0:
            current_data = self.type_combo.itemData(current_index)
            self._log(f"调试: 使用 itemData({current_index}) = {current_data}")

        # 如果还是 None，尝试通过文本反向查找
        if current_data is None:
            for template_name, display_name in self.PROJECT_TYPES.items():
                if display_name == current_text and template_name in self.template_files:
                    current_data = template_name
                    self._log(f"调试: 通过文本反向查找 = {current_data}")
                    break

        self._log(f"调试: template_files = {list(self.template_files.keys())}")

        if not current_data or current_data not in self.template_files:
            InfoBar.warning("提示", "未找到可用工程模板", duration=2000, parent=self.window())
            return

        project_file = self.template_files.get(current_data)
        self._log(f"调试: project_file = {project_file}")

        if not project_file or not os.path.exists(project_file):
            InfoBar.warning("提示", f"模板文件不存在: {project_file}", duration=2000, parent=self.window())
            return

        if not self.dir_edit.text().strip():
            InfoBar.warning("提示", "请选择输出目录", duration=2000, parent=self.window())
            return

        # 收集配置
        # 获取工程名称（使用模板名称）
        project_name = current_data  # current_data 就是模板名（如 Hello_World）

        config = {
            'model_type': self.model_combo.text(),
            'project_type': self.PROJECT_TYPES.get(current_data, current_data),
            'project_file': project_file,
            'output_dir': self.dir_edit.text().strip(),
            'project_name': project_name  # 添加工程名称
        }

        # 保存当前工程名称，用于完成时更新最近工程卡片
        self.current_project_name = project_name

        # 清空日志
        self.log_text.clear()
        self._log(f"开始生成: {config['project_type']}")

        # 禁用按钮
        self.generate_btn.setEnabled(False)
        self.generate_btn.setText("生成中...")

        # 如果有旧线程在运行，先清理
        if self.generate_thread is not None:
            try:
                if self.generate_thread.isRunning():
                    self.generate_thread.wait()
                self.generate_thread.deleteLater()
            except:
                pass
            self.generate_thread = None

        # 创建并启动生成线程
        self.generate_thread = CodeGenerateThread(config)
        self.generate_thread.log_signal.connect(self._log)
        self.generate_thread.finished_signal.connect(self._on_generate_finished)
        self.generate_thread.start()

    def _log(self, message):
        """添加日志"""
        self.log_text.append(message)

    def _on_generate_finished(self, success, message, project_path):
        """生成完成"""
        # 保存线程引用并立即清空，防止重复调用
        thread = self.generate_thread
        self.generate_thread = None

        self.generate_btn.setEnabled(True)
        self.generate_btn.setText("生成代码")

        if success:
            InfoBar.success("完成", message, duration=3000, parent=self.window())
            # 更新最后一次生成的工程路径和名称
            self.last_generated_path = project_path
            self.last_generated_name = getattr(self, 'current_project_name', None)
            # 刷新最近工程卡片
            self._update_recent_card()
        else:
            InfoBar.error("失败", message, duration=3000, parent=self.window())

        # 正确清理线程 - Win7 兼容性修复
        if thread is not None:
            # 断开信号连接，防止再次触发
            try:
                thread.finished_signal.disconnect(self._on_generate_finished)
                thread.log_signal.disconnect(self._log)
            except:
                pass

            # 等待线程完全结束
            if thread.isRunning():
                thread.wait()

            # 使用 deleteLater 安全删除
            thread.deleteLater()
            thread = None

    def _open_project(self, project_path):
        """打开工程目录"""
        import subprocess
        try:
            subprocess.Popen(['explorer', project_path])
        except Exception as e:
            self._log(f"打开目录失败: {str(e)}")
