"""
教程与文档界面
提供 PDF 和 DOCX 格式的教程文档浏览功能
"""

import os
import sys
import subprocess
from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QScrollArea, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QDesktopServices, QCursor
from PyQt5.QtCore import QUrl
from qfluentwidgets import (
    CardWidget, PrimaryPushButton, TransparentPushButton,
    SubtitleLabel, BodyLabel, CaptionLabel, StrongBodyLabel,
    FluentIcon as FIF, IconWidget, LineEdit, PushButton,
    InfoBar, InfoBarPosition
)
from core.font_manager import FontManager
from core.config_manager import get_program_dir


DEFAULT_VISIBLE_VERSIONS = 3


class ClickableLabel(QLabel):
    """可点击的标签（超链接样式）"""
    clicked = pyqtSignal()

    def __init__(self, text, color="#0078D4"):
        super().__init__(text)
        self.setStyleSheet(f"""
            QLabel {{
                color: {color};
            }}
            QLabel:hover {{
                text-decoration: underline;
            }}
        """)
        self.setCursor(QCursor(Qt.PointingHandCursor))

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


class ClickableFrame(QFrame):
    """可点击的容器"""
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(QCursor(Qt.PointingHandCursor))

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


class TutorialInterface(QWidget):
    """教程与文档界面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("tutorialInterface")
        self.program_dir = self._get_program_dir()
        self._expanded_version_item = None
        self._versions_expanded = False
        self._version_items = []

        self.init_ui()
        self._scan_documents()
        self._scan_versions()

    def _get_program_dir(self):
        """获取程序所在目录"""
        return get_program_dir()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(20)

        # 标题区域
        title_layout = QVBoxLayout()
        title_layout.setSpacing(8)

        title = SubtitleLabel("教程与文档")
        title.setStyleSheet(f"color: #2D3748; font-size: {FontManager.get_font_size('large_title')}px;")
        title_layout.addWidget(title)

        desc = BodyLabel("查看配置指南、代码示例、常见问题，快速掌握系统使用方法")
        desc.setStyleSheet(f"color: #5A6A7A; font-size: {FontManager.get_font_size('body')}px;")
        desc.setWordWrap(True)
        title_layout.addWidget(desc)

        layout.addLayout(title_layout)

        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(20)

        # 快速开始卡片
        self.quick_start_card = self._create_quick_start_card()
        content_layout.addWidget(self.quick_start_card)

        # 文档区域（PDF 和 Word 左右排列）
        docs_container = QWidget()
        docs_layout = QHBoxLayout(docs_container)
        docs_layout.setSpacing(15)

        self.pdf_card = self._create_pdf_card()
        self.docx_card = self._create_docx_card()

        docs_layout.addWidget(self.pdf_card, 1)
        docs_layout.addWidget(self.docx_card, 1)

        content_layout.addWidget(docs_container)

        # 版本信息卡片
        self.version_card = self._create_versions_card()
        content_layout.addWidget(self.version_card)

        # 帮助与反馈卡片
        self.help_card = self._create_help_card()
        content_layout.addWidget(self.help_card)

        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)

    def _create_quick_start_card(self):
        """创建快速开始卡片"""
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

        icon = IconWidget(FIF.SPEED_HIGH)
        icon.setFixedSize(32, 32)
        title_layout.addWidget(icon)

        title = StrongBodyLabel("快速开始")
        title.setStyleSheet(f"font-size: {FontManager.get_font_size('title')}px; color: #2D3748;")
        title_layout.addWidget(title)

        title_layout.addStretch()
        layout.addLayout(title_layout)

        # 内容
        content_layout = QVBoxLayout()
        content_layout.setSpacing(12)

        # 新手指南
        guide_text = BodyLabel(
            "👋 欢迎使用 RTopenEuler 系统管理工具！如果您是第一次使用，"
            "建议按照以下顺序快速上手："
        )
        guide_text.setStyleSheet(f"color: #2D3748; font-size: {FontManager.get_font_size('body')}px;")
        guide_text.setWordWrap(True)
        content_layout.addWidget(guide_text)

        # 步骤列表
        steps_layout = QVBoxLayout()
        steps_layout.setSpacing(8)
        steps_layout.setContentsMargins(20, 0, 0, 0)

        steps = [
            ("1", "配置开发环境", "安装编译器、工具链和依赖库"),
            ("2", "生成示例代码", "选择工程类型生成标准代码模板"),
            ("3", "查看教程文档", "阅读详细的配置和使用指南"),
            ("4", "初始化设备", "通过网络完成 CCU 设备初始化"),
        ]

        for num, title, desc in steps:
            step_layout = QHBoxLayout()
            step_layout.setSpacing(12)

            # 步骤编号
            num_label = QLabel(num)
            num_label.setFixedSize(28, 28)
            num_label.setStyleSheet(f"""
                QLabel {{
                    background-color: #0078D4;
                    color: white;
                    border-radius: 14px;
                    font-weight: bold;
                }}
            """)
            num_label.setAlignment(Qt.AlignCenter)
            step_layout.addWidget(num_label)

            # 步骤内容
            step_content = QVBoxLayout()
            step_content.setSpacing(2)

            step_title = StrongBodyLabel(title)
            step_title.setStyleSheet(f"font-size: {FontManager.get_font_size('body')}px; color: #2D3748;")
            step_content.addWidget(step_title)

            step_desc = CaptionLabel(desc)
            step_desc.setStyleSheet(f"color: #7A8A9A;")
            step_content.addWidget(step_desc)

            step_layout.addLayout(step_content)
            step_layout.addStretch()

            steps_layout.addLayout(step_layout)

        content_layout.addLayout(steps_layout)
        layout.addLayout(content_layout)

        return card

    def _create_pdf_card(self):
        """创建 PDF 文档卡片"""
        card = CardWidget()
        card.setStyleSheet("""
            CardWidget {
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 12px;
                border: 1px solid rgba(0, 0, 0, 0.06);
            }
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        # 标题
        title_layout = QHBoxLayout()
        title_layout.setSpacing(10)

        icon = IconWidget(FIF.DOCUMENT)
        icon.setFixedSize(28, 28)
        title_layout.addWidget(icon)

        title = StrongBodyLabel("PDF 文档")
        title.setStyleSheet(f"font-size: {FontManager.get_font_size('subtitle')}px; color: #D83B01;")
        title_layout.addWidget(title)

        self.pdf_count_label = CaptionLabel("(0)")
        self.pdf_count_label.setStyleSheet("color: #7A8A9A;")
        title_layout.addWidget(self.pdf_count_label)

        title_layout.addStretch()

        # 刷新按钮
        refresh_pdf_btn = PushButton("刷新")
        refresh_pdf_btn.setFixedHeight(28)
        refresh_pdf_btn.setFixedWidth(60)
        refresh_pdf_btn.clicked.connect(lambda: self._scan_documents(refresh=True))
        title_layout.addWidget(refresh_pdf_btn)

        layout.addLayout(title_layout)

        # PDF 文档列表容器
        self.pdf_list_widget = QWidget()
        self.pdf_list_layout = QVBoxLayout(self.pdf_list_widget)
        self.pdf_list_layout.setSpacing(6)
        self.pdf_list_layout.setContentsMargins(0, 0, 0, 0)

        # 空状态提示
        self.pdf_empty_label = BodyLabel("暂无文档")
        self.pdf_empty_label.setStyleSheet("color: #A0A0A0; padding: 15px;")
        self.pdf_empty_label.setAlignment(Qt.AlignCenter)
        self.pdf_list_layout.addWidget(self.pdf_empty_label)

        layout.addWidget(self.pdf_list_widget)

        return card

    def _create_docx_card(self):
        """创建 DOCX 文档卡片"""
        card = CardWidget()
        card.setStyleSheet("""
            CardWidget {
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 12px;
                border: 1px solid rgba(0, 0, 0, 0.06);
            }
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        # 标题
        title_layout = QHBoxLayout()
        title_layout.setSpacing(10)

        icon = IconWidget(FIF.DOCUMENT)
        icon.setFixedSize(28, 28)
        title_layout.addWidget(icon)

        title = StrongBodyLabel("Word 文档")
        title.setStyleSheet(f"font-size: {FontManager.get_font_size('subtitle')}px; color: #0078D4;")
        title_layout.addWidget(title)

        self.docx_count_label = CaptionLabel("(0)")
        self.docx_count_label.setStyleSheet("color: #7A8A9A;")
        title_layout.addWidget(self.docx_count_label)

        title_layout.addStretch()

        # 刷新按钮
        refresh_docx_btn = PushButton("刷新")
        refresh_docx_btn.setFixedHeight(28)
        refresh_docx_btn.setFixedWidth(60)
        refresh_docx_btn.clicked.connect(lambda: self._scan_documents(refresh=True))
        title_layout.addWidget(refresh_docx_btn)

        layout.addLayout(title_layout)

        # DOCX 文档列表容器
        self.docx_list_widget = QWidget()
        self.docx_list_layout = QVBoxLayout(self.docx_list_widget)
        self.docx_list_layout.setSpacing(6)
        self.docx_list_layout.setContentsMargins(0, 0, 0, 0)

        # 空状态提示
        self.docx_empty_label = BodyLabel("暂无文档")
        self.docx_empty_label.setStyleSheet("color: #A0A0A0; padding: 15px;")
        self.docx_empty_label.setAlignment(Qt.AlignCenter)
        self.docx_list_layout.addWidget(self.docx_empty_label)

        layout.addWidget(self.docx_list_widget)

        return card

    def _create_versions_card(self):
        """创建版本信息卡片"""
        card = CardWidget()
        card.setStyleSheet("""
            CardWidget {
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 12px;
                border: 1px solid rgba(0, 0, 0, 0.06);
            }
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        # 标题
        title_layout = QHBoxLayout()
        title_layout.setSpacing(10)

        icon = IconWidget(FIF.SYNC)
        icon.setFixedSize(28, 28)
        title_layout.addWidget(icon)

        title = StrongBodyLabel("版本信息")
        title.setStyleSheet(f"font-size: {FontManager.get_font_size('subtitle')}px; color: #2D3748;")
        title_layout.addWidget(title)

        self.version_count_label = CaptionLabel("(0)")
        self.version_count_label.setStyleSheet("color: #7A8A9A;")
        title_layout.addWidget(self.version_count_label)

        title_layout.addStretch()

        refresh_versions_btn = PushButton("刷新")
        refresh_versions_btn.setFixedHeight(28)
        refresh_versions_btn.setFixedWidth(60)
        refresh_versions_btn.clicked.connect(lambda: self._scan_versions(refresh=True))
        title_layout.addWidget(refresh_versions_btn)

        layout.addLayout(title_layout)

        # 版本列表容器
        self.version_list_widget = QWidget()
        self.version_list_layout = QVBoxLayout(self.version_list_widget)
        self.version_list_layout.setSpacing(10)
        self.version_list_layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(self.version_list_widget)

        self.version_toggle_btn = TransparentPushButton("展开更多")
        self.version_toggle_btn.setFixedHeight(28)
        self.version_toggle_btn.setVisible(False)
        self.version_toggle_btn.clicked.connect(self._toggle_versions_expanded)
        layout.addWidget(self.version_toggle_btn, alignment=Qt.AlignCenter)

        return card

    def _create_help_card(self):
        """创建帮助与反馈卡片"""
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
        layout.setSpacing(12)

        # 标题
        title_layout = QHBoxLayout()
        title_layout.setSpacing(10)

        icon = IconWidget(FIF.HELP)
        icon.setFixedSize(28, 28)
        title_layout.addWidget(icon)

        title = StrongBodyLabel("帮助与反馈")
        title.setStyleSheet(f"font-size: {FontManager.get_font_size('title')}px; color: #2D3748;")
        title_layout.addWidget(title)

        title_layout.addStretch()
        layout.addLayout(title_layout)

        # 内容
        info_layout = QVBoxLayout()
        info_layout.setSpacing(8)

        info_text = BodyLabel(
            "如果您在使用过程中遇到问题，或有任何建议和意见，"
            "欢迎通过以下方式联系我们："
        )
        info_text.setStyleSheet(f"color: #5A6A7A; font-size: {FontManager.get_font_size('body')}px;")
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)

        # 联系方式
        contact_layout = QHBoxLayout()
        contact_layout.setSpacing(20)

        contact_items = [
            ("📧", "技术支持", "+86-13386129803"),
            ("📝", "问题反馈", "请提供详细的错误信息和操作步骤"),
        ]

        for icon, label, value in contact_items:
            item_layout = QVBoxLayout()
            item_layout.setSpacing(2)

            item_label = CaptionLabel(f"{icon} {label}")
            item_label.setStyleSheet("color: #7A8A9A;")
            item_layout.addWidget(item_label)

            value_label = BodyLabel(value)
            value_label.setStyleSheet("color: #2D3748;")
            item_layout.addWidget(value_label)

            contact_layout.addLayout(item_layout)

        contact_layout.addStretch()
        info_layout.addLayout(contact_layout)

        layout.addLayout(info_layout)

        return card

    def _scan_documents(self, refresh=False):
        """扫描文档目录"""
        # 清空现有列表
        self._clear_layout(self.pdf_list_layout)
        self._clear_layout(self.docx_list_layout)

        # 扫描 PDF 文档
        pdf_dir = os.path.join(self.program_dir, "docs", "pdf")
        pdf_files = []
        if os.path.exists(pdf_dir):
            for file in os.listdir(pdf_dir):
                if file.lower().endswith('.pdf'):
                    pdf_files.append(file)

        # 扫描 DOCX 文档
        docx_dir = os.path.join(self.program_dir, "docs", "docx")
        docx_files = []
        if os.path.exists(docx_dir):
            for file in os.listdir(docx_dir):
                if file.lower().endswith('.docx'):
                    docx_files.append(file)

        # 更新 PDF 列表
        self.pdf_count_label.setText(f"({len(pdf_files)})")
        if pdf_files:
            self.pdf_empty_label.hide()
            for pdf_file in sorted(pdf_files):
                item = self._create_document_item(pdf_file, os.path.join(pdf_dir, pdf_file), 'pdf')
                self.pdf_list_layout.addWidget(item)
        else:
            self.pdf_empty_label.show()

        # 更新 DOCX 列表
        self.docx_count_label.setText(f"({len(docx_files)})")
        if docx_files:
            self.docx_empty_label.hide()
            for docx_file in sorted(docx_files):
                item = self._create_document_item(docx_file, os.path.join(docx_dir, docx_file), 'docx')
                self.docx_list_layout.addWidget(item)
        else:
            self.docx_empty_label.show()

        if refresh:
            InfoBar.success("刷新完成", f"已更新文档列表：PDF {len(pdf_files)} 个，Word {len(docx_files)} 个",
                          duration=2000, parent=self.window())

    def _scan_versions(self, refresh=False):
        """扫描版本信息目录"""
        self._clear_layout(self.version_list_layout)
        self._expanded_version_item = None
        self._version_items = []

        versions_dir = self._get_versions_dir()
        version_files = []
        if os.path.exists(versions_dir):
            for file in os.listdir(versions_dir):
                if file.lower().endswith('.txt'):
                    version_files.append(file)

        version_files = sorted(version_files, key=self._version_sort_key, reverse=True)
        self.version_count_label.setText(f"({len(version_files)})")

        if version_files:
            for idx, version_file in enumerate(version_files):
                version = Path(version_file).stem
                content = self._read_version_file(os.path.join(versions_dir, version_file))
                release_date = self._extract_release_date(content)
                item = self._create_version_item(version, content, release_date)
                item.setVisible(self._versions_expanded or idx < DEFAULT_VISIBLE_VERSIONS)
                self.version_list_layout.addWidget(item)
                self._version_items.append(item)
        else:
            empty_label = BodyLabel("暂无版本信息")
            empty_label.setStyleSheet("color: #A0A0A0; padding: 15px;")
            empty_label.setAlignment(Qt.AlignCenter)
            self.version_list_layout.addWidget(empty_label)

        self._update_version_toggle(len(version_files))

        if refresh:
            InfoBar.success("刷新完成", f"已更新版本信息：{len(version_files)} 个",
                          duration=2000, parent=self.window())

    def _get_versions_dir(self):
        return os.path.join(self.program_dir, "versions")

    def _version_sort_key(self, filename):
        parts = []
        for part in Path(filename).stem.split("."):
            if part.isdigit():
                parts.append((0, int(part)))
            else:
                parts.append((1, part))
        return parts

    def _read_version_file(self, filepath):
        for encoding in ("utf-8", "gbk"):
            try:
                with open(filepath, "r", encoding=encoding, errors="replace") as file:
                    return file.read().strip()
            except OSError:
                break
        return ""

    def _extract_release_date(self, content):
        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.lower().startswith("release date:"):
                return line.split(":", 1)[1].strip()
            return ""
        return ""

    def _create_version_item(self, version, content, release_date):
        item = QFrame()
        item.setStyleSheet("""
            QFrame {
                background-color: rgba(248, 249, 251, 0.9);
                border-radius: 8px;
                border: 1px solid rgba(0, 0, 0, 0.06);
            }
        """)

        layout = QVBoxLayout(item)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        header = ClickableFrame()
        header.setStyleSheet("background-color: transparent;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        if release_date:
            title_text = f"版本 {version} 发布日期：{release_date}"
        else:
            title_text = f"版本 {version}"
        title = StrongBodyLabel(title_text)
        title.setStyleSheet(f"font-size: {FontManager.get_font_size('body')}px; color: #2D3748;")
        title.setAttribute(Qt.WA_TransparentForMouseEvents)
        header_layout.addWidget(title)

        header_layout.addStretch()

        arrow = QLabel(">")
        arrow.setStyleSheet("color: #7A8A9A;")
        arrow.setAttribute(Qt.WA_TransparentForMouseEvents)
        header_layout.addWidget(arrow)

        layout.addWidget(header)

        content = content.strip()
        if not content:
            content = "暂无版本说明。"

        content_label = BodyLabel(content)
        content_label.setStyleSheet(f"color: #5A6A7A; font-size: {FontManager.get_font_size('body')}px;")
        content_label.setWordWrap(True)
        content_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        content_label.setVisible(False)
        layout.addWidget(content_label)

        item._is_expanded = False

        def set_expanded(expanded):
            item._is_expanded = expanded
            content_label.setVisible(expanded)
            arrow.setText("v" if expanded else ">")

        item._set_expanded = set_expanded
        header.clicked.connect(lambda: self._toggle_version_item(item))

        return item

    def _toggle_version_item(self, item):
        if item._is_expanded:
            item._set_expanded(False)
            self._expanded_version_item = None
            return

        if self._expanded_version_item and self._expanded_version_item is not item:
            self._expanded_version_item._set_expanded(False)

        item._set_expanded(True)
        self._expanded_version_item = item

    def _toggle_versions_expanded(self):
        if not self._version_items:
            return
        self._versions_expanded = not self._versions_expanded
        for idx, item in enumerate(self._version_items):
            item.setVisible(self._versions_expanded or idx < DEFAULT_VISIBLE_VERSIONS)
        if not self._versions_expanded and self._expanded_version_item is not None:
            if self._expanded_version_item not in self._version_items[:DEFAULT_VISIBLE_VERSIONS]:
                self._expanded_version_item._set_expanded(False)
                self._expanded_version_item = None
        self._update_version_toggle(len(self._version_items))

    def _update_version_toggle(self, total_versions):
        if total_versions <= DEFAULT_VISIBLE_VERSIONS:
            self._versions_expanded = False
            self.version_toggle_btn.setVisible(False)
            return
        self.version_toggle_btn.setVisible(True)
        if self._versions_expanded:
            self.version_toggle_btn.setText("收起")
        else:
            hidden_count = total_versions - DEFAULT_VISIBLE_VERSIONS
            self.version_toggle_btn.setText(f"展开更多 ({hidden_count})")

    def _create_document_item(self, filename, filepath, file_type):
        """创建文档列表项（超链接样式）"""
        item = QWidget()
        item.setStyleSheet("background-color: transparent;")

        layout = QHBoxLayout(item)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        # 文件图标（小）
        icon_label = QLabel("📄")
        icon_label.setFixedSize(16, 16)
        layout.addWidget(icon_label)

        # 文件名（超链接样式，使用 ClickableLabel）
        display_name = Path(filename).stem
        if file_type == 'pdf':
            color = "#D83B01"
        else:
            color = "#0078D4"
        link_label = ClickableLabel(display_name, color)
        link_label.clicked.connect(lambda: self._open_document(filepath))
        layout.addWidget(link_label)

        layout.addStretch()

        return item

    def _clear_layout(self, layout):
        """清空布局中的所有控件"""
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _open_document(self, filepath):
        """打开文档"""
        try:
            # 使用系统默认应用打开文件
            if sys.platform == 'win32':
                os.startfile(filepath)
            elif sys.platform == 'darwin':
                subprocess.run(['open', filepath])
            else:
                subprocess.run(['xdg-open', filepath])
        except Exception as e:
            InfoBar.error("打开失败", f"无法打开文档：{str(e)}",
                        duration=3000, parent=self.window())
