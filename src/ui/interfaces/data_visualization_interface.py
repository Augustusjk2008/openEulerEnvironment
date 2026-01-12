from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFileDialog,
    QScrollArea,
    QCheckBox,
    QSplitter,
    QSizePolicy,
)
from qfluentwidgets import (
    CardWidget,
    SubtitleLabel,
    BodyLabel,
    StrongBodyLabel,
    LineEdit,
    PushButton,
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
        self._load_file(Path(path))

    def _load_file(self, path: Path):
        try:
            slog = parse_slog_file(path)
        except Exception as exc:
            InfoBar.error("读取失败", f"无法解析 SLOG 文件: {exc}", duration=4000, parent=self.window())
            self._reset_state()
            return

        self._current_path = path
        self.path_edit.setText(str(path))
        self._build_series(slog.schema.fields, slog.records)
        self._build_checkboxes()
        self._render_empty_plot("请勾选要绘制的条目")

    def _reset_state(self):
        self._current_path = None
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
