import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from PyQt5.QtCore import Qt, QSize, pyqtSignal, QTimer, QRectF
from PyQt5.QtGui import QColor, QBrush, QFontMetrics, QPainter
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QFileDialog,
    QSplitter,
    QTabWidget,
    QComboBox,
    QCheckBox,
    QSpinBox,
    QTreeWidget,
    QTreeWidgetItem,
    QAbstractItemView,
    QMenu,
    QFormLayout,
    QPlainTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QListWidget,
    QListWidgetItem,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsRectItem,
    QGraphicsPolygonItem,
    QGraphicsLineItem,
    QGraphicsPathItem,
    QGraphicsSimpleTextItem,
    QApplication,
)
from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QPen, QPolygonF, QPainterPath

from qfluentwidgets import (
    CardWidget,
    SubtitleLabel,
    BodyLabel,
    StrongBodyLabel,
    LineEdit,
    PushButton,
    PrimaryPushButton,
    ToolButton,
    InfoBar,
    FluentIcon as FIF,
    IconWidget,
)

from core.config_manager import get_config_manager, get_program_dir
from core.font_manager import FontManager
from core.autopilot_document import (
    ValidationIssue,
    create_default_document,
    dump_json_text,
    ensure_program_ids,
    find_program_node_by_id,
    load_json,
    normalize_controller_document,
    save_json,
    validate_document,
)
from core.autopilot_codegen_cpp import generate_cpp_header


@dataclass
class ProgramNodeRef:
    node_id: str
    path: str


class _ProgramTree(QTreeWidget):
    moved = pyqtSignal(str, str, int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderHidden(False)
        self.setColumnCount(2)
        self.setHeaderLabels(["条目", "说明"])
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self._drag_snapshot: Optional[Tuple[str, str, int]] = None

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if item is not None:
            parent = item.parent()
            parent_id = parent.data(0, Qt.UserRole + 2) if parent is not None else ""
            parent_kind = parent.data(0, Qt.UserRole + 3) if parent is not None else ""
            idx = parent.indexOfChild(item) if parent is not None else self.indexOfTopLevelItem(item)
            self._drag_snapshot = (str(parent_id), str(parent_kind), int(idx))
        else:
            self._drag_snapshot = None
        super().startDrag(supportedActions)

    def dropEvent(self, event):
        item = self.currentItem()
        before = self._drag_snapshot
        super().dropEvent(event)
        if item is None or before is None:
            self._drag_snapshot = None
            return
        parent = item.parent()
        parent_id = parent.data(0, Qt.UserRole + 2) if parent is not None else ""
        parent_kind = parent.data(0, Qt.UserRole + 3) if parent is not None else ""
        after_idx = parent.indexOfChild(item) if parent is not None else self.indexOfTopLevelItem(item)
        before_parent_id, before_parent_kind, before_idx = before
        if str(parent_id) != str(before_parent_id) or str(parent_kind) != str(before_parent_kind):
            self._drag_snapshot = None
            return
        if int(after_idx) == int(before_idx):
            self._drag_snapshot = None
            return
        moved_item_id = str(item.data(0, Qt.UserRole))
        self.moved.emit(moved_item_id, str(parent_kind), int(before_idx), int(after_idx))
        self._drag_snapshot = None


class _GraphView(QGraphicsView):
    node_clicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHint(QPainter.Antialiasing, True)
        self.setScene(QGraphicsScene(self))
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self._items_by_id: Dict[str, Dict[str, Any]] = {}
        self._selected_id: Optional[str] = None
        self._zoom = 1.0
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)

    def rebuild(self, graph_spec: Dict[str, Any]):
        scene = self.scene()
        scene.clear()
        self._items_by_id.clear()

        pen = QPen(QColor(0, 0, 0, 40))
        pen.setWidth(1)
        arrow_pen = QPen(QColor(70, 90, 110, 140))
        arrow_pen.setWidth(2)

        box_w = 240
        box_h = 56
        x0 = 520
        y0 = 30
        x_gap = 340
        y_gap = 110

        def add_round_rect(node_id: str, x: float, y: float, label: str, fill: QColor):
            path = QPainterPath()
            path.addRoundedRect(x, y, box_w, box_h, 12, 12)
            item = QGraphicsPathItem(path)
            item.setBrush(QBrush(fill))
            item.setPen(pen)
            item.setData(0, node_id)
            text = QGraphicsSimpleTextItem("", item)
            fm = QFontMetrics(text.font())
            elided = fm.elidedText(label, Qt.ElideRight, box_w - 18)
            text.setText(elided)
            br = text.boundingRect()
            text.setPos(x + (box_w - br.width()) / 2, y + (box_h - br.height()) / 2)
            scene.addItem(item)
            self._items_by_id[node_id] = {"item": item, "pen": QPen(pen)}
            top = QPointF(x + box_w / 2, y)
            bottom = QPointF(x + box_w / 2, y + box_h)
            return top, bottom

        def add_rect(node_id: str, x: float, y: float, label: str, fill: QColor):
            rect = QGraphicsRectItem(x, y, box_w, box_h)
            rect.setBrush(QBrush(fill))
            rect.setPen(pen)
            rect.setData(0, node_id)
            text = QGraphicsSimpleTextItem("", rect)
            fm = QFontMetrics(text.font())
            elided = fm.elidedText(label, Qt.ElideRight, box_w - 18)
            text.setText(elided)
            br = text.boundingRect()
            text.setPos(x + (box_w - br.width()) / 2, y + (box_h - br.height()) / 2)
            scene.addItem(rect)
            self._items_by_id[node_id] = {"item": rect, "pen": QPen(pen)}
            top = QPointF(x + box_w / 2, y)
            bottom = QPointF(x + box_w / 2, y + box_h)
            return top, bottom

        def add_diamond(node_id: str, x: float, y: float, label: str, fill: QColor):
            cx = x + box_w / 2
            cy = y + box_h / 2
            poly = QPolygonF([
                QPointF(cx, y),
                QPointF(x + box_w, cy),
                QPointF(cx, y + box_h),
                QPointF(x, cy),
            ])
            item = QGraphicsPolygonItem(poly)
            item.setBrush(QBrush(fill))
            item.setPen(pen)
            item.setData(0, node_id)
            text = QGraphicsSimpleTextItem("", item)
            fm = QFontMetrics(text.font())
            elided = fm.elidedText(label, Qt.ElideRight, box_w - 26)
            text.setText(elided)
            br = text.boundingRect()
            text.setPos(x + (box_w - br.width()) / 2, y + (box_h - br.height()) / 2)
            scene.addItem(item)
            self._items_by_id[node_id] = {"item": item, "pen": QPen(pen)}
            top = QPointF(cx, y)
            bottom = QPointF(cx, y + box_h)
            left = QPointF(x, cy)
            right = QPointF(x + box_w, cy)
            return top, bottom, left, right

        def add_arrow(p1: QPointF, p2: QPointF, text: Optional[str] = None):
            line = QGraphicsLineItem(p1.x(), p1.y(), p2.x(), p2.y())
            line.setPen(arrow_pen)
            scene.addItem(line)
            dx = p2.x() - p1.x()
            dy = p2.y() - p1.y()
            l = (dx * dx + dy * dy) ** 0.5
            if l > 0:
                ux = dx / l
                uy = dy / l
                size = 8
                left = QPointF(p2.x() - ux * size - uy * (size * 0.7), p2.y() - uy * size + ux * (size * 0.7))
                right = QPointF(p2.x() - ux * size + uy * (size * 0.7), p2.y() - uy * size - ux * (size * 0.7))
                head = QGraphicsPolygonItem(QPolygonF([p2, left, right]))
                head.setBrush(QBrush(QColor(70, 90, 110, 170)))
                head.setPen(QPen(Qt.NoPen))
                scene.addItem(head)
            if text:
                t = QGraphicsSimpleTextItem(text)
                t.setBrush(QBrush(QColor("#4C6A92")))
                t.setPos((p1.x() + p2.x()) / 2 + 6, (p1.y() + p2.y()) / 2 - 10)
                scene.addItem(t)

        colors = graph_spec.get("colors", {})
        nodes_by_id = graph_spec.get("nodes_by_id", {})
        root_ids = graph_spec.get("root_ids", [])

        def node_title(node_id: str) -> str:
            it = nodes_by_id.get(node_id, {})
            return str(it.get("title", ""))

        def node_kind(node_id: str) -> str:
            it = nodes_by_id.get(node_id, {})
            return str(it.get("kind", ""))

        def node_children(node_id: str) -> Tuple[List[str], List[str]]:
            it = nodes_by_id.get(node_id, {})
            then_ids = it.get("then", [])
            else_ids = it.get("else", [])
            if not isinstance(then_ids, list):
                then_ids = []
            if not isinstance(else_ids, list):
                else_ids = []
            return [str(x) for x in then_ids], [str(x) for x in else_ids]

        def layout_seq(node_ids: List[str], x: float, y: float) -> Tuple[Optional[QPointF], Optional[QPointF], float]:
            prev_bottom: Optional[QPointF] = None
            first_top: Optional[QPointF] = None
            cur_y = y

            for node_id in node_ids:
                kind = node_kind(node_id)
                label = node_title(node_id)
                fill = QColor(str(colors.get(kind, "#FFFFFF")))
                if kind == "start_end":
                    top, bottom = add_round_rect(node_id, x, cur_y, label, fill)
                    if first_top is None:
                        first_top = top
                    if prev_bottom is not None:
                        add_arrow(prev_bottom, top)
                    prev_bottom = bottom
                    cur_y += y_gap
                elif kind == "if":
                    top, bottom, left, right = add_diamond(node_id, x, cur_y, label, fill)
                    if first_top is None:
                        first_top = top
                    if prev_bottom is not None:
                        add_arrow(prev_bottom, top)

                    then_ids, else_ids = node_children(node_id)
                    then_first, then_last, then_end_y = layout_seq(then_ids, x - x_gap, cur_y + y_gap)
                    else_first, else_last, else_end_y = layout_seq(else_ids, x + x_gap, cur_y + y_gap)

                    merge_y = max(then_end_y, else_end_y, cur_y + y_gap)
                    merge_point = QPointF(x + box_w / 2, merge_y + 10)

                    if then_first is not None:
                        add_arrow(left, then_first, "Yes")
                    else:
                        add_arrow(left, merge_point, "Yes")
                    if else_first is not None:
                        add_arrow(right, else_first, "No")
                    else:
                        add_arrow(right, merge_point, "No")

                    if then_last is not None:
                        add_arrow(then_last, merge_point)
                    if else_last is not None:
                        add_arrow(else_last, merge_point)

                    prev_bottom = merge_point
                    cur_y = merge_point.y() + y_gap
                else:
                    top, bottom = add_rect(node_id, x, cur_y, label, fill)
                    if first_top is None:
                        first_top = top
                    if prev_bottom is not None:
                        add_arrow(prev_bottom, top)
                    prev_bottom = bottom
                    cur_y += y_gap

            return first_top, prev_bottom, cur_y

        _, last, end_y = layout_seq([str(x) for x in root_ids], x0, y0)

        group_pen = QPen(QColor(0, 0, 0, 70))
        group_pen.setWidth(2)
        group_pen.setStyle(Qt.DashLine)
        group_text_brush = QBrush(QColor("#4C6A92"))

        for g in graph_spec.get("groups", []) if isinstance(graph_spec.get("groups"), list) else []:
            if not isinstance(g, dict):
                continue
            module_ids = g.get("module_ids", [])
            if not isinstance(module_ids, list) or not module_ids:
                continue
            rect: Optional[QRectF] = None
            for mid in module_ids:
                meta = self._items_by_id.get(str(mid))
                it = meta.get("item") if isinstance(meta, dict) else None
                if it is None:
                    continue
                r = it.sceneBoundingRect()
                rect = r if rect is None else rect.united(r)
            if rect is None:
                continue
            pad = 18
            box = QRectF(rect.x() - pad, rect.y() - pad, rect.width() + pad * 2, rect.height() + pad * 2)
            frame = QGraphicsRectItem(box)
            frame.setPen(group_pen)
            frame.setBrush(QBrush(Qt.NoBrush))
            frame.setZValue(-20)
            scene.addItem(frame)
            label = str(g.get("label", "") or "")
            if label:
                t = QGraphicsSimpleTextItem(label)
                t.setBrush(group_text_brush)
                br = t.boundingRect()
                t.setPos(box.x() - br.width() - 10, box.y() + (box.height() - br.height()) / 2)
                t.setZValue(-19)
                scene.addItem(t)

        if last is None:
            scene.setSceneRect(0, 0, 1100, 720)
        else:
            scene.setSceneRect(0, 0, 1400, max(720, int(end_y + 40)))
        if self._selected_id:
            self.set_selected(self._selected_id)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_in()
            elif delta < 0:
                self.zoom_out()
            event.accept()
            return
        super().wheelEvent(event)

    def zoom_in(self):
        self._apply_zoom(1.15)

    def zoom_out(self):
        self._apply_zoom(1 / 1.15)

    def reset_view(self):
        self._zoom = 1.0
        self.resetTransform()
        rect = self.scene().sceneRect()
        if rect.width() > 0 and rect.height() > 0:
            self.fitInView(rect, Qt.KeepAspectRatio)
            self._apply_zoom(1.25)

    def _apply_zoom(self, factor: float):
        new_zoom = self._zoom * factor
        if new_zoom < 0.2 or new_zoom > 50.0:
            return
        self._zoom = new_zoom
        self.scale(factor, factor)

    def set_selected(self, node_id: Optional[str]):
        if self._selected_id and self._selected_id in self._items_by_id:
            meta = self._items_by_id[self._selected_id]
            it = meta.get("item")
            base_pen = meta.get("pen")
            if it is not None and base_pen is not None and hasattr(it, "setPen"):
                it.setPen(QPen(base_pen))
        self._selected_id = node_id
        if node_id and node_id in self._items_by_id:
            meta = self._items_by_id[node_id]
            it = meta.get("item")
            base_pen = meta.get("pen")
            if it is not None and base_pen is not None and hasattr(it, "setPen"):
                p = QPen(base_pen)
                p.setColor(QColor(30, 64, 175, 200))
                p.setWidth(3)
                it.setPen(p)

    def mousePressEvent(self, event):
        pos = self.mapToScene(event.pos())
        items = self.scene().items(pos)
        for it in items:
            node_id = it.data(0) if hasattr(it, "data") else None
            if isinstance(node_id, str) and node_id:
                self.node_clicked.emit(node_id)
                break
        super().mousePressEvent(event)


class AutopilotEditorInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("autopilotEditorInterface")
        self.config_manager = get_config_manager()
        self.current_file: Optional[str] = None
        self._dirty = False
        self._suppress_updates = False
        self.doc: Dict[str, Any] = create_default_document()
        ensure_program_ids(self.doc)
        self._normalize_doc_for_editor()
        self._port_dims: Dict[str, int] = {}
        self._graph_spec: Dict[str, Any] = {}
        self._graph_first_render = True
        self._init_ui()
        self._refresh_all()

    def _show_bar(self, level: str, title: str, content: str):
        def show():
            if level == "success":
                InfoBar.success(title=title, content=content, parent=self)
            elif level == "warning":
                InfoBar.warning(title=title, content=content, parent=self)
            else:
                InfoBar.error(title=title, content=content, parent=self)

        QTimer.singleShot(0, show)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(14)

        title = SubtitleLabel("算法工作台")
        title.setStyleSheet(f"color: #2D3748; font-size: {FontManager.get_font_size('large_title')}px;")
        layout.addWidget(title)

        desc = BodyLabel("加载/编辑/校验/保存控制器描述文件，支持 Program 树编辑与只读图形联动。")
        desc.setStyleSheet(f"color: #5A6A7A; font-size: {FontManager.get_font_size('body')}px;")
        layout.addWidget(desc)

        layout.addWidget(self._create_toolbar_card())
        layout.addWidget(self._create_tabs(), 1)

    def _create_toolbar_card(self) -> CardWidget:
        card = CardWidget()
        card.setStyleSheet("""
            CardWidget {
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 12px;
                border: 1px solid rgba(0, 0, 0, 0.06);
            }
        """)
        row = QHBoxLayout(card)
        row.setContentsMargins(18, 14, 18, 14)
        row.setSpacing(10)

        icon = IconWidget(FIF.IOT)
        icon.setFixedSize(24, 24)
        row.addWidget(icon)

        self.path_edit = LineEdit()
        self.path_edit.setReadOnly(True)
        self.path_edit.setPlaceholderText("未打开文件")
        self.path_edit.setFixedHeight(34)
        row.addWidget(self.path_edit, 1)

        open_btn = PrimaryPushButton("打开")
        open_btn.setFixedHeight(34)
        open_btn.clicked.connect(self._open_file)
        row.addWidget(open_btn)

        new_btn = PushButton("新建")
        new_btn.setFixedHeight(34)
        new_btn.clicked.connect(self._new_file)
        row.addWidget(new_btn)

        save_btn = PushButton("保存")
        save_btn.setFixedHeight(34)
        save_btn.clicked.connect(self._save_file)
        row.addWidget(save_btn)

        save_as_btn = PushButton("另存为")
        save_as_btn.setFixedHeight(34)
        save_as_btn.clicked.connect(self._save_as)
        row.addWidget(save_as_btn)

        validate_btn = PushButton("校验")
        validate_btn.setFixedHeight(34)
        validate_btn.clicked.connect(self._validate)
        row.addWidget(validate_btn)

        example_btn = ToolButton(FIF.DOCUMENT, self)
        example_btn.setFixedSize(34, 34)
        example_btn.setIconSize(QSize(18, 18))
        example_btn.setToolTip("打开示例控制器描述文件")
        example_btn.clicked.connect(self._open_example)
        row.addWidget(example_btn)

        return card

    def _create_tabs(self) -> QTabWidget:
        tabs = QTabWidget()
        tabs.setDocumentMode(True)

        self.program_tab = QWidget()
        self.graph_tab = QWidget()
        self.json_tab = QWidget()
        self.data_tab = QWidget()

        tabs.addTab(self.program_tab, "Program")
        tabs.addTab(self.graph_tab, "Graph")
        tabs.addTab(self.json_tab, "Code")
        tabs.addTab(self.data_tab, "Data")

        self._init_program_tab()
        self._init_graph_tab()
        self._init_json_tab()
        self._init_data_tab()

        return tabs

    def _init_program_tab(self):
        layout = QHBoxLayout(self.program_tab)
        layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Horizontal)

        self.program_card = CardWidget()
        self.program_card.setStyleSheet("""
            CardWidget {
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 12px;
                border: 1px solid rgba(0, 0, 0, 0.06);
            }
        """)
        left = QVBoxLayout(self.program_card)
        left.setContentsMargins(16, 14, 16, 14)
        left.setSpacing(10)

        header = QHBoxLayout()
        header.setSpacing(8)
        header.addWidget(IconWidget(FIF.LIBRARY))
        name = StrongBodyLabel("Program 树")
        name.setStyleSheet(f"font-size: {FontManager.get_font_size('title')}px; color: #2D3748;")
        header.addWidget(name)
        header.addStretch()
        left.addLayout(header)

        tool_row = QHBoxLayout()
        tool_row.setSpacing(8)

        add_btn = PushButton("添加")
        add_btn.setFixedHeight(30)
        add_btn.clicked.connect(self._add_node_menu)
        tool_row.addWidget(add_btn)

        del_btn = PushButton("删除")
        del_btn.setFixedHeight(30)
        del_btn.clicked.connect(self._delete_selected_node)
        tool_row.addWidget(del_btn)

        up_btn = PushButton("上移")
        up_btn.setFixedHeight(30)
        up_btn.clicked.connect(lambda: self._move_selected(-1))
        tool_row.addWidget(up_btn)

        down_btn = PushButton("下移")
        down_btn.setFixedHeight(30)
        down_btn.clicked.connect(lambda: self._move_selected(1))
        tool_row.addWidget(down_btn)

        copy_btn = PushButton("复制")
        copy_btn.setFixedHeight(30)
        copy_btn.clicked.connect(self._copy_selected)
        tool_row.addWidget(copy_btn)

        paste_btn = PushButton("粘贴")
        paste_btn.setFixedHeight(30)
        paste_btn.clicked.connect(self._paste_to_selected)
        tool_row.addWidget(paste_btn)

        tool_row.addStretch()
        left.addLayout(tool_row)

        self.tree = _ProgramTree()
        self.tree.itemSelectionChanged.connect(self._on_tree_selected)
        self.tree.moved.connect(self._on_tree_item_moved)
        left.addWidget(self.tree, 1)

        splitter.addWidget(self.program_card)

        right_splitter = QSplitter(Qt.Vertical)

        self.inspector_card = CardWidget()
        self.inspector_card.setStyleSheet("""
            CardWidget {
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 12px;
                border: 1px solid rgba(0, 0, 0, 0.06);
            }
        """)
        inspector_layout = QVBoxLayout(self.inspector_card)
        inspector_layout.setContentsMargins(16, 14, 16, 14)
        inspector_layout.setSpacing(10)

        header2 = QHBoxLayout()
        header2.setSpacing(8)
        header2.addWidget(IconWidget(FIF.EDIT))
        name2 = StrongBodyLabel("属性")
        name2.setStyleSheet(f"font-size: {FontManager.get_font_size('title')}px; color: #2D3748;")
        header2.addWidget(name2)
        header2.addStretch()
        inspector_layout.addLayout(header2)

        self.form = QFormLayout()
        self.form.setHorizontalSpacing(12)
        self.form.setVerticalSpacing(10)
        inspector_layout.addLayout(self.form, 1)

        right_splitter.addWidget(self.inspector_card)

        self.problems_card = CardWidget()
        self.problems_card.setStyleSheet("""
            CardWidget {
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 12px;
                border: 1px solid rgba(0, 0, 0, 0.06);
            }
        """)
        problems_layout = QVBoxLayout(self.problems_card)
        problems_layout.setContentsMargins(16, 14, 16, 14)
        problems_layout.setSpacing(10)

        header3 = QHBoxLayout()
        header3.setSpacing(8)
        header3.addWidget(IconWidget(FIF.HELP))
        name3 = StrongBodyLabel("Problems")
        name3.setStyleSheet(f"font-size: {FontManager.get_font_size('title')}px; color: #2D3748;")
        header3.addWidget(name3)
        header3.addStretch()

        copy_btn = PushButton("复制全部")
        copy_btn.setFixedHeight(30)
        copy_btn.clicked.connect(self._copy_all_problems)
        header3.addWidget(copy_btn)

        problems_layout.addLayout(header3)

        self.problems_table = QTableWidget(0, 3)
        self.problems_table.setHorizontalHeaderLabels(["级别", "路径", "信息"])
        self.problems_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.problems_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.problems_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.problems_table.verticalHeader().setVisible(False)
        self.problems_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.problems_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.problems_table.setMinimumHeight(200)
        problems_layout.addWidget(self.problems_table, 1)

        right_splitter.addWidget(self.problems_card)
        right_splitter.setSizes([420, 260])

        splitter.addWidget(right_splitter)
        splitter.setSizes([640, 860])

        layout.addWidget(splitter, 1)

    def _init_graph_tab(self):
        layout = QVBoxLayout(self.graph_tab)
        layout.setContentsMargins(0, 0, 0, 0)

        card = CardWidget()
        card.setStyleSheet("""
            CardWidget {
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 12px;
                border: 1px solid rgba(0, 0, 0, 0.06);
            }
        """)
        c = QVBoxLayout(card)
        c.setContentsMargins(16, 14, 16, 14)
        c.setSpacing(10)

        header = QHBoxLayout()
        header.setSpacing(8)
        header.addWidget(IconWidget(FIF.PIE_SINGLE))
        title = StrongBodyLabel("Graph（只读）")
        title.setStyleSheet(f"font-size: {FontManager.get_font_size('title')}px; color: #2D3748;")
        header.addWidget(title)
        header.addStretch()

        zoom_in_btn = ToolButton(FIF.ADD, self)
        zoom_in_btn.setFixedSize(34, 34)
        zoom_in_btn.setIconSize(QSize(18, 18))
        zoom_in_btn.setToolTip("放大 (Ctrl+滚轮)")
        zoom_in_btn.clicked.connect(lambda: self.graph.zoom_in())
        header.addWidget(zoom_in_btn)

        zoom_out_btn = ToolButton(FIF.REMOVE, self)
        zoom_out_btn.setFixedSize(34, 34)
        zoom_out_btn.setIconSize(QSize(18, 18))
        zoom_out_btn.setToolTip("缩小 (Ctrl+滚轮)")
        zoom_out_btn.clicked.connect(lambda: self.graph.zoom_out())
        header.addWidget(zoom_out_btn)

        reset_btn = ToolButton(FIF.SYNC, self)
        reset_btn.setFixedSize(34, 34)
        reset_btn.setIconSize(QSize(18, 18))
        reset_btn.setToolTip("恢复视图")
        reset_btn.clicked.connect(lambda: self.graph.reset_view())
        header.addWidget(reset_btn)

        c.addLayout(header)

        self.graph = _GraphView()
        self.graph.node_clicked.connect(self._on_graph_node_clicked)

        split = QSplitter(Qt.Horizontal)
        split.addWidget(self.graph)

        detail_wrap = QWidget()
        detail_layout = QVBoxLayout(detail_wrap)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        detail_layout.setSpacing(8)
        detail_layout.addWidget(StrongBodyLabel("详情"))
        self.graph_detail = QPlainTextEdit()
        self.graph_detail.setReadOnly(True)
        self.graph_detail.setMinimumHeight(160)
        self.graph_detail.setLineWrapMode(QPlainTextEdit.NoWrap)
        detail_layout.addWidget(self.graph_detail, 1)
        split.addWidget(detail_wrap)
        split.setSizes([900, 360])

        c.addWidget(split, 1)

        layout.addWidget(card, 1)

    def _init_json_tab(self):
        layout = QVBoxLayout(self.json_tab)
        layout.setContentsMargins(0, 0, 0, 0)

        card = CardWidget()
        card.setStyleSheet("""
            CardWidget {
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 12px;
                border: 1px solid rgba(0, 0, 0, 0.06);
            }
        """)
        c = QVBoxLayout(card)
        c.setContentsMargins(16, 14, 16, 14)
        c.setSpacing(10)

        header = QHBoxLayout()
        header.setSpacing(8)
        header.addWidget(IconWidget(FIF.DOCUMENT))
        title = StrongBodyLabel("Code（只读）")
        title.setStyleSheet(f"font-size: {FontManager.get_font_size('title')}px; color: #2D3748;")
        header.addWidget(title)
        header.addStretch()
        c.addLayout(header)

        split = QSplitter(Qt.Horizontal)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)
        left_layout.addWidget(StrongBodyLabel("JSON"))
        self.json_view = QPlainTextEdit()
        self.json_view.setReadOnly(True)
        self.json_view.setLineWrapMode(QPlainTextEdit.NoWrap)
        left_layout.addWidget(self.json_view, 1)
        split.addWidget(left)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)
        right_layout.addWidget(StrongBodyLabel("C++"))
        self.cpp_view = QPlainTextEdit()
        self.cpp_view.setReadOnly(True)
        self.cpp_view.setLineWrapMode(QPlainTextEdit.NoWrap)
        right_layout.addWidget(self.cpp_view, 1)
        split.addWidget(right)
        split.setSizes([650, 650])

        c.addWidget(split, 1)

        layout.addWidget(card, 1)

    def _init_data_tab(self):
        layout = QVBoxLayout(self.data_tab)
        layout.setContentsMargins(0, 0, 0, 0)

        card = CardWidget()
        card.setStyleSheet("""
            CardWidget {
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 12px;
                border: 1px solid rgba(0, 0, 0, 0.06);
            }
        """)
        c = QVBoxLayout(card)
        c.setContentsMargins(16, 14, 16, 14)
        c.setSpacing(10)

        header = QHBoxLayout()
        header.setSpacing(8)
        header.addWidget(IconWidget(FIF.LIBRARY))
        title = StrongBodyLabel("数据编辑")
        title.setStyleSheet(f"font-size: {FontManager.get_font_size('title')}px; color: #2D3748;")
        header.addWidget(title)
        header.addStretch()
        c.addLayout(header)

        state_row = QHBoxLayout()
        state_row.setSpacing(10)

        state_row.addWidget(StrongBodyLabel("STATE集合"))
        self.states_edit = LineEdit()
        self.states_edit.setPlaceholderText("用逗号分隔，例如：Step1,Step2,Step3")
        self.states_edit.setFixedHeight(32)
        self.states_edit.editingFinished.connect(self._states_changed)
        state_row.addWidget(self.states_edit, 1)

        state_row.addWidget(StrongBodyLabel("初始STATE"))
        self.current_state_combo = QComboBox()
        self.current_state_combo.setFixedHeight(32)
        self.current_state_combo.currentIndexChanged.connect(self._states_changed)
        state_row.addWidget(self.current_state_combo)

        c.addLayout(state_row)

        tool_row = QHBoxLayout()
        tool_row.setSpacing(10)
        add_btn = PushButton("添加条目")
        add_btn.setFixedHeight(32)
        add_btn.clicked.connect(self._symbols_add_row)
        tool_row.addWidget(add_btn)
        del_btn = PushButton("删除条目")
        del_btn.setFixedHeight(32)
        del_btn.clicked.connect(self._symbols_del_row)
        tool_row.addWidget(del_btn)
        tool_row.addStretch()
        c.addLayout(tool_row)

        self.symbols_table = QTableWidget(0, 8)
        self.symbols_table.setHorizontalHeaderLabels([
            "名称",
            "属性",
            "类别",
            "迭代",
            "类型",
            "维度",
            "初值",
            "说明",
        ])
        for col in range(self.symbols_table.columnCount()):
            self.symbols_table.horizontalHeader().setSectionResizeMode(col, QHeaderView.Stretch)
        self.symbols_table.verticalHeader().setVisible(False)
        self.symbols_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.symbols_table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
        self.symbols_table.itemChanged.connect(lambda _: self._symbols_changed())
        c.addWidget(self.symbols_table, 1)

        layout.addWidget(card, 1)

    def _init_ports_page(self):
        layout = QVBoxLayout(self.ports_page)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        splitter = QSplitter(Qt.Horizontal)

        self.inputs_table = QTableWidget(0, 3)
        self.inputs_table.setHorizontalHeaderLabels(["id", "type", "unit"])
        self._setup_kv_table(self.inputs_table)
        self.inputs_table.itemChanged.connect(lambda _: self._ports_changed())

        self.outputs_table = QTableWidget(0, 3)
        self.outputs_table.setHorizontalHeaderLabels(["id", "type", "unit"])
        self._setup_kv_table(self.outputs_table)
        self.outputs_table.itemChanged.connect(lambda _: self._ports_changed())

        splitter.addWidget(self._wrap_table_with_toolbar("输入端口", self.inputs_table, self._add_input_port, self._del_input_port))
        splitter.addWidget(self._wrap_table_with_toolbar("输出端口", self.outputs_table, self._add_output_port, self._del_output_port))
        splitter.setSizes([520, 520])
        layout.addWidget(splitter, 1)

    def _init_scalars_page(self):
        layout = QVBoxLayout(self.scalars_page)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        self.scalars_table = QTableWidget(0, 2)
        self.scalars_table.setHorizontalHeaderLabels(["name", "value"])
        self.scalars_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.scalars_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.scalars_table.verticalHeader().setVisible(False)
        self.scalars_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.scalars_table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
        self.scalars_table.itemChanged.connect(lambda _: self._scalars_changed())

        layout.addWidget(self._wrap_table_with_toolbar("变量", self.scalars_table, self._add_scalar, self._del_scalar), 1)

    def _init_sequences_page(self):
        layout = QVBoxLayout(self.sequences_page)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        self.sequences_table = QTableWidget(0, 3)
        self.sequences_table.setHorizontalHeaderLabels(["name", "init[0]", "len"])
        self.sequences_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.sequences_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.sequences_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.sequences_table.verticalHeader().setVisible(False)
        self.sequences_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.sequences_table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
        self.sequences_table.itemChanged.connect(lambda _: self._sequences_changed())

        layout.addWidget(self._wrap_table_with_toolbar("序列", self.sequences_table, self._add_sequence, self._del_sequence), 1)

    def _init_commit_page(self):
        layout = QVBoxLayout(self.commit_page)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        row = QHBoxLayout()
        row.setSpacing(10)
        self.shift_list = QListWidget()
        self.shift_list.itemChanged.connect(lambda _: self._commit_changed())
        row.addWidget(self.shift_list, 1)

        btns = QVBoxLayout()
        btns.setSpacing(8)
        add_btn = PushButton("添加")
        add_btn.setFixedHeight(32)
        add_btn.clicked.connect(self._commit_add)
        btns.addWidget(add_btn)
        del_btn = PushButton("删除")
        del_btn.setFixedHeight(32)
        del_btn.clicked.connect(self._commit_del)
        btns.addWidget(del_btn)
        btns.addStretch()
        row.addLayout(btns)

        layout.addLayout(row, 1)

    def _wrap_table_with_toolbar(self, title: str, table: QTableWidget, add_cb, del_cb) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        header = QHBoxLayout()
        header.setSpacing(8)
        header.addWidget(StrongBodyLabel(title))
        header.addStretch()
        add_btn = PushButton("添加")
        add_btn.setFixedHeight(30)
        add_btn.clicked.connect(add_cb)
        header.addWidget(add_btn)
        del_btn = PushButton("删除")
        del_btn.setFixedHeight(30)
        del_btn.clicked.connect(del_cb)
        header.addWidget(del_btn)
        layout.addLayout(header)
        layout.addWidget(table, 1)
        return w

    def _setup_kv_table(self, table: QTableWidget):
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)

    def _open_example(self):
        path = os.path.join(get_program_dir(), "references", "autopilot", "AutoPilotDescription.json")
        if os.path.exists(path):
            self._load_file(path)
        else:
            self._show_bar("error", "未找到示例", path)

    def _new_file(self):
        self.doc = create_default_document()
        ensure_program_ids(self.doc)
        self._normalize_doc_for_editor()
        self._graph_first_render = True
        self.current_file = None
        self._dirty = True
        self._refresh_all()
        self._show_bar("success", "已新建", "未保存")

    def _open_file(self):
        start_dir = self.config_manager.get("autopilot_json_dir", "") or get_program_dir()
        path, _ = QFileDialog.getOpenFileName(self, "打开控制器 JSON", start_dir, "JSON Files (*.json)")
        if not path:
            return
        self._load_file(path)

    def _load_file(self, path: str):
        try:
            doc = load_json(path)
        except Exception as e:
            self._show_bar("error", "打开失败", str(e))
            return
        self.doc = doc
        ensure_program_ids(self.doc)
        self._normalize_doc_for_editor()
        self._graph_first_render = True
        self.current_file = path
        self.config_manager.set("autopilot_json_dir", os.path.dirname(path))
        self._dirty = False
        self._refresh_all()
        self._show_bar("success", "已打开", os.path.basename(path))

    def _save_as(self):
        start_dir = self.config_manager.get("autopilot_json_dir", "") or get_program_dir()
        path, _ = QFileDialog.getSaveFileName(self, "另存为控制器 JSON", start_dir, "JSON Files (*.json)")
        if not path:
            return
        self.current_file = path
        self.config_manager.set("autopilot_json_dir", os.path.dirname(path))
        self._save_file()

    def _save_file(self):
        if not self.current_file:
            self._save_as()
            return
        try:
            for r in range(self.symbols_table.rowCount()) if hasattr(self, "symbols_table") and self.symbols_table is not None else []:
                spin = self._cell_spin(r, 5)
                if spin is not None:
                    spin.interpretText()
            self._symbols_changed()
            ensure_program_ids(self.doc)
            save_json(self.current_file, self.doc)
        except Exception as e:
            self._show_bar("error", "保存失败", str(e))
            return
        self._dirty = False
        self._refresh_json()
        self._show_bar("success", "已保存", os.path.basename(self.current_file))

    def _set_dirty(self):
        if self._suppress_updates:
            return
        self._dirty = True
        self._refresh_json()

    def _validate(self):
        issues = validate_document(self.doc)
        self._show_issues(issues)
        error_count = sum(1 for x in issues if x.level == "error")
        if error_count:
            self._show_bar("warning", "校验完成", f"{error_count} 个错误")
        else:
            self._show_bar("success", "校验通过", "未发现错误")

    def _show_issues(self, issues: List[ValidationIssue]):
        self.problems_table.setRowCount(0)
        for it in issues:
            row = self.problems_table.rowCount()
            self.problems_table.insertRow(row)
            level_item = QTableWidgetItem(it.level)
            if it.level == "error":
                level_item.setForeground(QColor("#C00000"))
            elif it.level == "warning":
                level_item.setForeground(QColor("#B36B00"))
            self.problems_table.setItem(row, 0, level_item)
            self.problems_table.setItem(row, 1, QTableWidgetItem(it.path))
            self.problems_table.setItem(row, 2, QTableWidgetItem(it.message))

    def _copy_all_problems(self):
        lines = ["级别\t路径\t信息"]
        for r in range(self.problems_table.rowCount()):
            level = self.problems_table.item(r, 0).text() if self.problems_table.item(r, 0) else ""
            path = self.problems_table.item(r, 1).text() if self.problems_table.item(r, 1) else ""
            msg = self.problems_table.item(r, 2).text() if self.problems_table.item(r, 2) else ""
            lines.append(f"{level}\t{path}\t{msg}")
        QApplication.clipboard().setText("\n".join(lines))
        self._show_bar("success", "已复制", f"{max(0, self.problems_table.rowCount())} 条")

    def _refresh_all(self):
        self.path_edit.setText(self.current_file or "")
        self._refresh_tree()
        self._refresh_json()
        self._refresh_data()
        self._refresh_graph()
        self._validate()

    def _refresh_json(self):
        try:
            text = dump_json_text(self.doc)
        except Exception:
            text = ""
        self.json_view.setPlainText(text)
        try:
            cpp = generate_cpp_header(self.doc, self.current_file)
        except Exception as e:
            cpp = f"// 生成失败: {e}\n"
        if hasattr(self, "cpp_view") and self.cpp_view is not None:
            self.cpp_view.setPlainText(cpp)
        if self.current_file:
            suffix = " *" if self._dirty else ""
            self.path_edit.setText(self.current_file + suffix)
        else:
            self.path_edit.setText("未打开文件" + (" *" if self._dirty else ""))

    def _refresh_tree(self):
        self._suppress_updates = True
        try:
            self.tree.clear()
            program = self.doc.get("program", [])
            if not isinstance(program, list):
                program = []
            for node in program:
                item = self._make_tree_item(node)
                self.tree.addTopLevelItem(item)
            self.tree.expandAll()
        finally:
            self._suppress_updates = False

    def _make_tree_item(self, node: Any) -> QTreeWidgetItem:
        if not isinstance(node, dict):
            it = QTreeWidgetItem(["<invalid>", ""])
            it.setData(0, Qt.UserRole, "")
            return it

        node_id = str(node.get("_id") or "")
        label = self._node_label(node)
        comment = str(node.get("comment", "") or "")
        it = QTreeWidgetItem([label, comment])
        it.setData(0, Qt.UserRole, node_id)

        if node.get("op") == "if":
            then_item = QTreeWidgetItem(["then", ""])
            then_item.setData(0, Qt.UserRole + 2, node_id)
            then_item.setData(0, Qt.UserRole + 3, "then")
            it.addChild(then_item)
            for child in node.get("then", []) if isinstance(node.get("then"), list) else []:
                then_item.addChild(self._make_tree_item(child))

            else_item = QTreeWidgetItem(["else", ""])
            else_item.setData(0, Qt.UserRole + 2, node_id)
            else_item.setData(0, Qt.UserRole + 3, "else")
            it.addChild(else_item)
            for child in node.get("else", []) if isinstance(node.get("else"), list) else []:
                else_item.addChild(self._make_tree_item(child))

        return it

    def _node_label(self, node: Dict[str, Any]) -> str:
        op = node.get("op")
        if op == "function":
            name = str(node.get("name", "") or "").strip() or "未命名"
            return f"==== {name} ===="
        if op == "assign":
            return f"assign  {node.get('lhs', '')} = {node.get('rhs', '')}"
        if op == "clamp":
            return f"clamp  {node.get('lhs', '')} = clamp({node.get('rhs', '')})"
        if op == "piecewise":
            return f"piecewise  {node.get('lhs', '')}"
        if op == "select":
            return f"select  {node.get('lhs', '')}"
        if op == "if":
            return f"if  ({node.get('cond', '')})"
        return str(op)

    def _refresh_graph(self):
        program = self.doc.get("program", [])
        if not isinstance(program, list):
            program = []
        self._graph_spec = self._build_graph_spec(program)
        self.graph.rebuild(self._graph_spec)
        if self._graph_first_render:
            self.graph.reset_view()
            self._graph_first_render = False
        cur = self._current_node_id()
        module_id = self._graph_spec.get("module_by_node_id", {}).get(cur) if cur else None
        if isinstance(module_id, str) and module_id:
            self.graph.set_selected(module_id)
            self._set_graph_detail(module_id)
        else:
            self.graph.set_selected(None)

    def _iter_nodes_preorder(self):
        program = self.doc.get("program", [])
        if not isinstance(program, list):
            return
        stack: List[Dict[str, Any]] = []

        def walk(nodes: List[Any]):
            for node in nodes:
                if not isinstance(node, dict):
                    continue
                yield node, ""
                if node.get("op") == "if":
                    then_nodes = node.get("then", [])
                    else_nodes = node.get("else", [])
                    if isinstance(then_nodes, list):
                        yield from walk(then_nodes)
                    if isinstance(else_nodes, list):
                        yield from walk(else_nodes)

        yield from walk(program)

    def _current_node_id(self) -> Optional[str]:
        item = self.tree.currentItem()
        if item is None:
            return None
        node_id = item.data(0, Qt.UserRole)
        if isinstance(node_id, str) and node_id:
            return node_id
        return None

    def _on_tree_selected(self):
        if self._suppress_updates:
            return
        node_id = self._current_node_id()
        self._build_property_form(node_id)
        module_id = self._graph_spec.get("module_by_node_id", {}).get(node_id) if node_id else None
        if isinstance(module_id, str) and module_id:
            self.graph.set_selected(module_id)
            self._set_graph_detail(module_id)
        else:
            self.graph.set_selected(None)
            if hasattr(self, "graph_detail"):
                self.graph_detail.setPlainText("")

    def _on_graph_node_clicked(self, graph_id: str):
        rep = self._graph_spec.get("rep_node_by_graph_id", {}).get(graph_id, "")
        if isinstance(rep, str) and rep:
            self._select_tree_by_id(rep)
        self.graph.set_selected(graph_id)
        self._set_graph_detail(graph_id)

    def _set_graph_detail(self, graph_id: str):
        if not hasattr(self, "graph_detail"):
            return
        detail = self._graph_spec.get("detail_by_graph_id", {}).get(graph_id, "")
        if isinstance(detail, str):
            self.graph_detail.setPlainText(detail)
        else:
            self.graph_detail.setPlainText("")

    def _build_graph_spec(self, program: List[Any]) -> Dict[str, Any]:
        op_cn = {
            "assign": "赋值",
            "clamp": "限幅",
            "piecewise": "分段",
            "select": "分类",
        }
        colors = {
            "assign": "#E6F2FF",
            "clamp": "#FFF2CC",
            "piecewise": "#F2E6FF",
            "select": "#E8F5E9",
            "if": "#F3F4F6",
            "start_end": "#E6FFFB",
        }

        nodes_by_id: Dict[str, Any] = {}
        detail_by_graph_id: Dict[str, str] = {}
        rep_node_by_graph_id: Dict[str, str] = {}
        module_by_node_id: Dict[str, str] = {}
        groups: List[Dict[str, Any]] = []

        def group_label(name: str, comment: str) -> str:
            c = (comment or "").strip()
            return c or ""

        default_group = {"id": "__func_default__", "name": "默认函数", "comment": "", "module_ids": []}
        groups.append(default_group)

        def node_detail_lines(n: Dict[str, Any]) -> List[str]:
            op = n.get("op")
            comment = n.get("comment", "")
            suffix = f"  # {comment.strip()}" if isinstance(comment, str) and comment.strip() else ""
            if op == "assign":
                return [f"{op_cn['assign']}  {n.get('lhs', '')} = {n.get('rhs', '')}{suffix}"]
            if op == "clamp":
                return [f"{op_cn['clamp']}  {n.get('lhs', '')} = clamp({n.get('rhs', '')}, {n.get('min', '')}, {n.get('max', '')}){suffix}"]
            if op == "piecewise":
                cases = n.get("cases", [])
                lhs = str(n.get("lhs", ""))
                lines = [f"{op_cn['piecewise']}  {lhs}{suffix}"]
                if isinstance(cases, list):
                    for i, c in enumerate(cases):
                        if not isinstance(c, dict):
                            continue
                        when = str(c.get("when", ""))
                        value = str(c.get("value", ""))
                        lines.append(f"  {i + 1}) when {when} => {value}")
                lines.append(f"  else => {n.get('else', '')}")
                return lines
            if op == "select":
                return [f"{op_cn['select']}  {n.get('lhs', '')} = ({n.get('cond', '')} ? {n.get('true', '')} : {n.get('false', '')}){suffix}"]
            if op == "if":
                return [f"if  ({n.get('cond', '')}){suffix}"]
            return [str(op)]

        def module_detail_text(mod_id: str, mod: Dict[str, Any]) -> str:
            kind = mod.get("kind", "")
            if kind == "start_end":
                return str(mod.get("title", ""))
            if kind == "if":
                return str(mod.get("title", ""))
            items = mod.get("items", [])
            if not isinstance(items, list):
                items = []
            header = str(mod.get("title", ""))
            lines = [header]
            for i, item in enumerate(items, start=1):
                if isinstance(item, dict):
                    dlines = node_detail_lines(item)
                    if not dlines:
                        continue
                    lines.append(f"{i}. {dlines[0]}")
                    for extra in dlines[1:]:
                        lines.append(f"   {extra}")
            return "\n".join(lines)

        def build_seq(nodes: List[Any], current_group: Dict[str, Any]) -> List[str]:
            ids: List[str] = []
            i = 0
            pending_func_marker: Optional[str] = None
            while i < len(nodes):
                n = nodes[i]
                if not isinstance(n, dict):
                    i += 1
                    continue
                op = n.get("op")
                node_id = str(n.get("_id") or "")
                if op == "function":
                    name = str(n.get("name", "") or "").strip() or "未命名"
                    comment = str(n.get("comment", "") or "").strip()
                    gid = f"__func_{node_id}" if node_id else f"__func_{len(groups)}"
                    current_group = {"id": gid, "name": name, "comment": comment, "module_ids": []}
                    groups.append(current_group)
                    if node_id:
                        module_by_node_id[node_id] = ""
                        pending_func_marker = node_id
                    i += 1
                    continue
                if op == "if":
                    then_nodes = n.get("then", [])
                    else_nodes = n.get("else", [])
                    then_ids = build_seq(then_nodes if isinstance(then_nodes, list) else [], current_group)
                    else_ids = build_seq(else_nodes if isinstance(else_nodes, list) else [], current_group)
                    title = f"if ({n.get('cond', '')})"
                    nodes_by_id[node_id] = {"kind": "if", "title": title, "then": then_ids, "else": else_ids}
                    detail_by_graph_id[node_id] = module_detail_text(node_id, nodes_by_id[node_id])
                    rep_node_by_graph_id[node_id] = node_id
                    module_by_node_id[node_id] = node_id
                    ids.append(node_id)
                    current_group["module_ids"].append(node_id)
                    if pending_func_marker and not module_by_node_id.get(pending_func_marker):
                        module_by_node_id[pending_func_marker] = node_id
                        pending_func_marker = None
                    i += 1
                    continue

                if op in op_cn:
                    group: List[Dict[str, Any]] = [n]
                    j = i + 1
                    while j < len(nodes):
                        n2 = nodes[j]
                        if not isinstance(n2, dict):
                            break
                        if n2.get("op") != op:
                            break
                        group.append(n2)
                        j += 1
                    mod_id = node_id
                    title = op_cn[op]
                    if len(group) > 1:
                        title = f"{title}×{len(group)}"
                    nodes_by_id[mod_id] = {"kind": op, "title": title, "items": group}
                    detail_by_graph_id[mod_id] = module_detail_text(mod_id, nodes_by_id[mod_id])
                    rep_node_by_graph_id[mod_id] = str(group[0].get("_id") or "")
                    for it in group:
                        nid = str(it.get("_id") or "")
                        if nid:
                            module_by_node_id[nid] = mod_id
                    ids.append(mod_id)
                    current_group["module_ids"].append(mod_id)
                    if pending_func_marker and not module_by_node_id.get(pending_func_marker):
                        module_by_node_id[pending_func_marker] = mod_id
                        pending_func_marker = None
                    i = j
                    continue

                nodes_by_id[node_id] = {"kind": "assign", "title": node_detail_lines(n)[0], "items": [n]}
                detail_by_graph_id[node_id] = module_detail_text(node_id, nodes_by_id[node_id])
                rep_node_by_graph_id[node_id] = node_id
                module_by_node_id[node_id] = node_id
                ids.append(node_id)
                current_group["module_ids"].append(node_id)
                if pending_func_marker and not module_by_node_id.get(pending_func_marker):
                    module_by_node_id[pending_func_marker] = node_id
                    pending_func_marker = None
                i += 1
            return ids

        start_id = "__start__"
        end_id = "__end__"
        nodes_by_id[start_id] = {"kind": "start_end", "title": "周期开始"}
        nodes_by_id[end_id] = {"kind": "start_end", "title": "周期结束"}
        detail_by_graph_id[start_id] = "周期开始"
        detail_by_graph_id[end_id] = "周期结束"

        seq_ids = build_seq(program, default_group)
        root_ids = [start_id] + seq_ids + [end_id]

        return {
            "root_ids": root_ids,
            "nodes_by_id": nodes_by_id,
            "colors": colors,
            "detail_by_graph_id": detail_by_graph_id,
            "rep_node_by_graph_id": rep_node_by_graph_id,
            "module_by_node_id": module_by_node_id,
            "groups": [{"id": g["id"], "label": group_label(str(g.get("name", "")), str(g.get("comment", ""))), "module_ids": list(g.get("module_ids", []))} for g in groups if isinstance(g, dict)],
        }

    def _select_tree_by_id(self, node_id: str):
        it = self._find_tree_item(node_id)
        if it is not None:
            self.tree.setCurrentItem(it)

    def _find_tree_item(self, node_id: str) -> Optional[QTreeWidgetItem]:
        root_count = self.tree.topLevelItemCount()
        for i in range(root_count):
            found = self._find_tree_item_rec(self.tree.topLevelItem(i), node_id)
            if found is not None:
                return found
        return None

    def _find_tree_item_rec(self, it: QTreeWidgetItem, node_id: str) -> Optional[QTreeWidgetItem]:
        if str(it.data(0, Qt.UserRole)) == node_id:
            return it
        for i in range(it.childCount()):
            found = self._find_tree_item_rec(it.child(i), node_id)
            if found is not None:
                return found
        return None

    def _clear_form(self):
        while self.form.rowCount():
            self.form.removeRow(0)

    def _build_property_form(self, node_id: Optional[str]):
        self._suppress_updates = True
        try:
            self._clear_form()
            if not node_id:
                return
            found = find_program_node_by_id(self.doc, node_id)
            if not found:
                return
            node, _path = found
            op = node.get("op")
            self._add_form_row("op", str(op or ""), read_only=True)
            self._add_form_row("comment", str(node.get("comment", "")), on_change=lambda v: self._set_node_field(node_id, "comment", v))
            if op == "if":
                self._add_form_row("cond", str(node.get("cond", "")), on_change=lambda v: self._set_node_field(node_id, "cond", v))
            elif op == "function":
                self._add_form_row("name", str(node.get("name", "")), on_change=lambda v: self._set_node_field(node_id, "name", v))
            elif op == "assign":
                self._add_form_row("lhs", str(node.get("lhs", "")), on_change=lambda v: self._set_node_field(node_id, "lhs", v))
                self._add_form_row("rhs", str(node.get("rhs", "")), on_change=lambda v: self._set_node_field(node_id, "rhs", v))
            elif op == "clamp":
                self._add_form_row("lhs", str(node.get("lhs", "")), on_change=lambda v: self._set_node_field(node_id, "lhs", v))
                self._add_form_row("rhs", str(node.get("rhs", "")), on_change=lambda v: self._set_node_field(node_id, "rhs", v))
                self._add_form_row("min", str(node.get("min", "")), on_change=lambda v: self._set_node_field(node_id, "min", self._coerce_number_or_str(v)))
                self._add_form_row("max", str(node.get("max", "")), on_change=lambda v: self._set_node_field(node_id, "max", self._coerce_number_or_str(v)))
            elif op == "select":
                self._add_form_row("lhs", str(node.get("lhs", "")), on_change=lambda v: self._set_node_field(node_id, "lhs", v))
                self._add_form_row("cond", str(node.get("cond", "")), on_change=lambda v: self._set_node_field(node_id, "cond", v))
                self._add_form_row("true", str(node.get("true", "")), on_change=lambda v: self._set_node_field(node_id, "true", self._coerce_number_or_str(v)))
                self._add_form_row("false", str(node.get("false", "")), on_change=lambda v: self._set_node_field(node_id, "false", self._coerce_number_or_str(v)))
            elif op == "piecewise":
                self._add_form_row("lhs", str(node.get("lhs", "")), on_change=lambda v: self._set_node_field(node_id, "lhs", v))
                cases_widget = QWidget()
                v = QVBoxLayout(cases_widget)
                v.setContentsMargins(0, 0, 0, 0)
                v.setSpacing(8)

                btn_row = QHBoxLayout()
                btn_row.setSpacing(8)
                add_case_btn = PushButton("添加分支")
                add_case_btn.setFixedHeight(30)
                del_case_btn = PushButton("删除分支")
                del_case_btn.setFixedHeight(30)
                btn_row.addWidget(add_case_btn)
                btn_row.addWidget(del_case_btn)
                btn_row.addStretch()
                v.addLayout(btn_row)

                table = QTableWidget(0, 2)
                table.setHorizontalHeaderLabels(["when", "value"])
                table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
                table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
                table.verticalHeader().setVisible(False)
                table.setSelectionBehavior(QAbstractItemView.SelectRows)
                table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
                v.addWidget(table, 1)

                def load_cases_into_table():
                    found2 = find_program_node_by_id(self.doc, node_id)
                    if not found2:
                        return
                    node2, _ = found2
                    cases2 = node2.get("cases", [])
                    if not isinstance(cases2, list):
                        cases2 = []
                    table.blockSignals(True)
                    try:
                        table.setRowCount(0)
                        for c in cases2:
                            if not isinstance(c, dict):
                                continue
                            r = table.rowCount()
                            table.insertRow(r)
                            table.setItem(r, 0, QTableWidgetItem(str(c.get("when", ""))))
                            table.setItem(r, 1, QTableWidgetItem(str(c.get("value", ""))))
                    finally:
                        table.blockSignals(False)

                def write_cases_from_table():
                    found2 = find_program_node_by_id(self.doc, node_id)
                    if not found2:
                        return
                    node2, _ = found2
                    cases2: List[Dict[str, Any]] = []
                    for r in range(table.rowCount()):
                        when = (table.item(r, 0).text() if table.item(r, 0) else "").strip()
                        value = (table.item(r, 1).text() if table.item(r, 1) else "").strip()
                        if not when and not value:
                            continue
                        cases2.append({"when": when, "value": value})
                    node2["cases"] = cases2
                    self._after_doc_changed(rebuild_tree=False)

                table.itemChanged.connect(lambda _=None: write_cases_from_table())

                def add_case():
                    r = table.rowCount()
                    table.insertRow(r)
                    table.setItem(r, 0, QTableWidgetItem(""))
                    table.setItem(r, 1, QTableWidgetItem(""))
                    write_cases_from_table()

                def del_case():
                    r = table.currentRow()
                    if r >= 0:
                        table.removeRow(r)
                        write_cases_from_table()

                add_case_btn.clicked.connect(add_case)
                del_case_btn.clicked.connect(del_case)

                load_cases_into_table()
                self.form.addRow("cases", cases_widget)
                self._add_form_row("else", str(node.get("else", "")), on_change=lambda v2: self._set_node_field(node_id, "else", self._coerce_number_or_str(v2)))
            self._add_form_row("_id", str(node_id), read_only=True)
        finally:
            self._suppress_updates = False

    def _add_form_row(self, label: str, value: str, read_only: bool = False, on_change=None):
        edit = LineEdit()
        edit.setText(value)
        edit.setFixedHeight(32)
        edit.setReadOnly(read_only)
        if on_change is not None and not read_only:
            def _emit_change(e=edit):
                try:
                    text = e.text()
                except RuntimeError:
                    return
                QTimer.singleShot(0, lambda t=text: on_change(t))

            edit.editingFinished.connect(_emit_change)
        self.form.addRow(label, edit)

    def _coerce_number_or_str(self, text: str):
        s = (text or "").strip()
        if s == "":
            return ""
        try:
            if "." in s or "e" in s.lower():
                return float(s)
            return int(s)
        except Exception:
            return s

    def _set_piecewise_case_field(self, node_id: str, idx: int, key: str, value: Any):
        found = find_program_node_by_id(self.doc, node_id)
        if not found:
            return
        node, _ = found
        cases = node.get("cases")
        if not isinstance(cases, list):
            cases = []
            node["cases"] = cases
        while len(cases) <= idx:
            cases.append({"when": "", "value": ""})
        if isinstance(cases[idx], dict):
            cases[idx][key] = value
            self._after_doc_changed(rebuild_tree=False)

    def _set_node_field(self, node_id: str, key: str, value: Any):
        found = find_program_node_by_id(self.doc, node_id)
        if not found:
            return
        node, _ = found
        node[key] = value
        self._after_doc_changed(rebuild_tree=True)

    def _after_doc_changed(self, rebuild_tree: bool):
        self._set_dirty()
        if rebuild_tree:
            cur = self._current_node_id()
            self._refresh_tree()
            if cur:
                self._select_tree_by_id(cur)
        self._refresh_graph()
        self._validate()

    def _add_node_menu(self):
        menu = QMenu(self)
        menu.addAction("assign").triggered.connect(lambda: self._add_node("assign"))
        menu.addAction("clamp").triggered.connect(lambda: self._add_node("clamp"))
        menu.addAction("piecewise").triggered.connect(lambda: self._add_node("piecewise"))
        menu.addAction("select").triggered.connect(lambda: self._add_node("select"))
        menu.addAction("if").triggered.connect(lambda: self._add_node("if"))
        menu.addAction("function").triggered.connect(lambda: self._add_node("function"))
        btn = self.sender()
        if btn is not None:
            menu.exec_(btn.mapToGlobal(btn.rect().bottomLeft()))

    def _default_node(self, op: str) -> Dict[str, Any]:
        base = {"op": op, "_id": "", "comment": ""}
        ensure_program_ids({"program": [base]})
        if op == "assign":
            base.update({"lhs": "", "rhs": ""})
        elif op == "clamp":
            base.update({"lhs": "", "rhs": "", "min": 0.0, "max": 0.0})
        elif op == "piecewise":
            base.update({"lhs": "", "cases": [{"when": "", "value": ""}], "else": ""})
        elif op == "select":
            base.update({"lhs": "", "cond": "", "true": "", "false": ""})
        elif op == "if":
            base.update({"cond": "", "then": [], "else": []})
        elif op == "function":
            base.update({"name": "NewFunc"})
        return base

    def _get_container_for_selected(self) -> Tuple[List[Any], int]:
        program = self.doc.get("program")
        if not isinstance(program, list):
            self.doc["program"] = []
            program = self.doc["program"]

        item = self.tree.currentItem()
        if item is None:
            return program, len(program)

        branch = item.data(0, Qt.UserRole + 3)
        parent_id = item.data(0, Qt.UserRole + 2)
        if isinstance(branch, str) and branch in {"then", "else"} and isinstance(parent_id, str) and parent_id:
            found = find_program_node_by_id(self.doc, parent_id)
            if found:
                node, _ = found
                container = node.get(branch)
                if not isinstance(container, list):
                    node[branch] = []
                    container = node[branch]
                return container, len(container)

        parent = item.parent()
        if parent is None:
            idx = self.tree.indexOfTopLevelItem(item)
            return program, max(0, idx + 1)

        parent_branch = parent.data(0, Qt.UserRole + 3)
        parent_id2 = parent.data(0, Qt.UserRole + 2)
        if isinstance(parent_branch, str) and parent_branch in {"then", "else"} and isinstance(parent_id2, str) and parent_id2:
            found = find_program_node_by_id(self.doc, parent_id2)
            if found:
                node, _ = found
                container = node.get(parent_branch)
                if not isinstance(container, list):
                    node[parent_branch] = []
                    container = node[parent_branch]
                idx = parent.indexOfChild(item)
                return container, max(0, idx + 1)

        idx = parent.indexOfChild(item)
        return program, max(0, idx + 1)

    def _add_node(self, op: str):
        container, insert_at = self._get_container_for_selected()
        node = self._default_node(op)
        container.insert(insert_at, node)
        self._after_doc_changed(rebuild_tree=True)
        self._select_tree_by_id(str(node.get("_id") or ""))

    def _delete_selected_node(self):
        node_id = self._current_node_id()
        if not node_id:
            return
        self._delete_node_by_id(node_id)
        self._after_doc_changed(rebuild_tree=True)

    def _delete_node_by_id(self, node_id: str) -> bool:
        def remove_from(nodes: List[Any]) -> bool:
            for i, n in enumerate(list(nodes)):
                if isinstance(n, dict) and n.get("_id") == node_id:
                    nodes.pop(i)
                    return True
                if isinstance(n, dict) and n.get("op") == "if":
                    then_nodes = n.get("then", [])
                    else_nodes = n.get("else", [])
                    if isinstance(then_nodes, list) and remove_from(then_nodes):
                        return True
                    if isinstance(else_nodes, list) and remove_from(else_nodes):
                        return True
            return False

        program = self.doc.get("program")
        if not isinstance(program, list):
            return False
        return remove_from(program)

    def _move_selected(self, delta: int):
        node_id = self._current_node_id()
        if not node_id:
            return
        container, idx = self._find_container_index(node_id)
        if container is None or idx is None:
            return
        new_idx = idx + delta
        if new_idx < 0 or new_idx >= len(container):
            return
        container[idx], container[new_idx] = container[new_idx], container[idx]
        self._after_doc_changed(rebuild_tree=True)
        self._select_tree_by_id(node_id)

    def _find_container_index(self, node_id: str) -> Tuple[Optional[List[Any]], Optional[int]]:
        def walk(nodes: List[Any]) -> Tuple[Optional[List[Any]], Optional[int]]:
            for i, n in enumerate(nodes):
                if isinstance(n, dict) and n.get("_id") == node_id:
                    return nodes, i
                if isinstance(n, dict) and n.get("op") == "if":
                    then_nodes = n.get("then", [])
                    else_nodes = n.get("else", [])
                    if isinstance(then_nodes, list):
                        c, idx = walk(then_nodes)
                        if c is not None:
                            return c, idx
                    if isinstance(else_nodes, list):
                        c, idx = walk(else_nodes)
                        if c is not None:
                            return c, idx
            return None, None

        program = self.doc.get("program")
        if not isinstance(program, list):
            return None, None
        return walk(program)

    def _copy_selected(self):
        node_id = self._current_node_id()
        if not node_id:
            return
        found = find_program_node_by_id(self.doc, node_id)
        if not found:
            return
        node, _ = found
        text = dump_json_text(node)
        QApplication.clipboard().setText(text)
        self._show_bar("success", "已复制", "节点 JSON 已放入剪贴板")

    def _paste_to_selected(self):
        text = QApplication.clipboard().text() or ""
        text = text.strip()
        if not text:
            return
        try:
            import json as _json

            data = _json.loads(text)
        except Exception:
            self._show_bar("error", "粘贴失败", "剪贴板不是有效 JSON")
            return
        if not isinstance(data, dict) or "op" not in data:
            self._show_bar("error", "粘贴失败", "需要粘贴一个 program 节点对象")
            return
        data = dict(data)
        data["_id"] = ""
        ensure_program_ids({"program": [data]})
        container, insert_at = self._get_container_for_selected()
        container.insert(insert_at, data)
        self._after_doc_changed(rebuild_tree=True)
        self._select_tree_by_id(str(data.get("_id") or ""))

    def _on_tree_item_moved(self, node_id: str, parent_kind: str, old_idx: int, new_idx: int):
        container, idx = self._find_container_index(node_id)
        if container is None or idx is None:
            return
        if idx != old_idx:
            old_idx = idx
        if new_idx < 0 or new_idx >= len(container):
            return
        node = container.pop(old_idx)
        container.insert(new_idx, node)
        self._after_doc_changed(rebuild_tree=True)
        self._select_tree_by_id(node_id)

    def _refresh_data(self):
        self._suppress_updates = True
        try:
            self._normalize_doc_for_editor()
            self._refresh_states_editor()
            self._refresh_symbols_table()
        finally:
            self._suppress_updates = False

    def _normalize_doc_for_editor(self):
        self.doc = normalize_controller_document(self.doc)

    def _refresh_states_editor(self):
        state = self.doc.get("state", {})
        states = state.get("states", []) if isinstance(state.get("states"), list) else []
        cur = state.get("STATE", "") if isinstance(state.get("STATE"), str) else ""
        self.states_edit.setText(",".join([str(x) for x in states if isinstance(x, str) and x]))
        self.current_state_combo.blockSignals(True)
        try:
            self.current_state_combo.clear()
            for s in states:
                if isinstance(s, str) and s:
                    self.current_state_combo.addItem(s)
            idx = self.current_state_combo.findText(cur)
            if idx >= 0:
                self.current_state_combo.setCurrentIndex(idx)
            elif self.current_state_combo.count() > 0:
                self.current_state_combo.setCurrentIndex(0)
        finally:
            self.current_state_combo.blockSignals(False)

    def _states_changed(self):
        if self._suppress_updates:
            return
        raw = (self.states_edit.text() or "").strip()
        parts = [x.strip() for x in raw.split(",") if x.strip()]
        states: List[str] = []
        for x in parts:
            if x not in states:
                states.append(x)
        state = self.doc.setdefault("state", {})
        state["states"] = states if states else [state.get("STATE", "Step1")]
        cur = self.current_state_combo.currentText().strip() if self.current_state_combo.count() else ""
        if cur and cur in state["states"]:
            state["STATE"] = cur
        elif state["states"]:
            state["STATE"] = state["states"][0]
        self._after_doc_changed(rebuild_tree=False)

    def _symbols_add_row(self):
        r = self.symbols_table.rowCount()
        self.symbols_table.insertRow(r)
        self._symbols_init_row_widgets(r)
        self._symbols_changed()

    def _symbols_del_row(self):
        r = self.symbols_table.currentRow()
        if r >= 0:
            self.symbols_table.removeRow(r)
            self._symbols_changed()

    def _symbols_init_row_widgets(self, row: int):
        io_combo = QComboBox()
        io_combo.addItems(["内部", "输入", "输出"])
        io_combo.setCurrentText("内部")
        io_combo.currentIndexChanged.connect(lambda _=None: self._symbols_changed())
        self.symbols_table.setCellWidget(row, 1, io_combo)

        kind_combo = QComboBox()
        kind_combo.addItems(["常数", "变量", "序列"])
        kind_combo.setCurrentText("变量")
        kind_combo.currentIndexChanged.connect(lambda _=None, r=row: self._on_symbol_kind_changed(r))
        self.symbols_table.setCellWidget(row, 2, kind_combo)

        iter_wrap, iter_cb = self._make_centered_checkbox()
        iter_cb.stateChanged.connect(lambda _=None: self._symbols_changed())
        self.symbols_table.setCellWidget(row, 3, iter_wrap)

        type_combo = QComboBox()
        type_combo.addItems(["f32", "f64", "int", "uint"])
        type_combo.currentIndexChanged.connect(lambda _=None: self._symbols_changed())
        self.symbols_table.setCellWidget(row, 4, type_combo)

        dim_spin = QSpinBox()
        dim_spin.setRange(1, 1024)
        dim_spin.setValue(1)
        dim_spin.valueChanged.connect(lambda _=None: self._symbols_changed())
        dim_spin.editingFinished.connect(self._symbols_changed)
        self.symbols_table.setCellWidget(row, 5, dim_spin)

        self.symbols_table.setItem(row, 0, QTableWidgetItem(""))
        self.symbols_table.setItem(row, 6, QTableWidgetItem("0"))
        self.symbols_table.setItem(row, 7, QTableWidgetItem(""))

        self._apply_symbol_row_enabled(row)

    def _make_centered_checkbox(self) -> Tuple[QFrame, QCheckBox]:
        wrap = QFrame()
        layout = QHBoxLayout(wrap)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)
        cb = QCheckBox(wrap)
        layout.addWidget(cb)
        return wrap, cb

    def _on_symbol_kind_changed(self, row: int):
        self._apply_symbol_row_enabled(row)
        self._symbols_changed()

    def _apply_symbol_row_enabled(self, row: int):
        kind = self._cell_combo_text(row, 2)
        is_seq = kind == "序列"
        iter_cb = self._cell_checkbox(row, 3)
        if iter_cb is not None:
            iter_cb.setEnabled(is_seq)
            if is_seq and iter_cb.checkState() == Qt.Unchecked:
                iter_cb.setChecked(True)
        dim_spin = self._cell_spin(row, 5)
        if dim_spin is not None:
            dim_spin.setEnabled(not is_seq)
            if is_seq and int(dim_spin.value()) != 1:
                dim_spin.setValue(1)

    def _refresh_symbols_table(self):
        self.symbols_table.setRowCount(0)
        data = self.doc.get("data", {}) if isinstance(self.doc.get("data"), dict) else {}

        kind_order = {"constant": 0, "scalar": 1, "sequence": 2}
        names = sorted(
            [k for k in data.keys() if isinstance(k, str) and k],
            key=lambda n: (kind_order.get(str(data.get(n, {}).get("kind", "")), 99), n),
        )

        kind_cn = {"constant": "常数", "scalar": "变量", "sequence": "序列"}

        for name in names:
            meta = data.get(name, {})
            if not isinstance(meta, dict):
                continue
            row = self.symbols_table.rowCount()
            self.symbols_table.insertRow(row)
            self._symbols_init_row_widgets(row)

            self.symbols_table.item(row, 0).setText(name)

            io_cn = {"internal": "内部", "input": "输入", "output": "输出"}.get(str(meta.get("io") or "internal"), "内部")
            io_combo = self._cell_combo(row, 1)
            if io_combo is not None:
                idx = io_combo.findText(io_cn)
                if idx >= 0:
                    io_combo.setCurrentIndex(idx)

            kind = kind_cn.get(str(meta.get("kind", "")), "变量")
            kind_combo = self._cell_combo(row, 2)
            if kind_combo is not None:
                idx = kind_combo.findText(kind)
                if idx >= 0:
                    kind_combo.setCurrentIndex(idx)

            iter_cb = self._cell_checkbox(row, 3)
            if iter_cb is not None:
                iter_cb.setChecked(bool(meta.get("iterate")) if kind == "序列" else False)

            dtype = str(meta.get("type") or "f64")
            if dtype not in {"f32", "f64", "int", "uint"}:
                dtype = "f64"
            type_combo = self._cell_combo(row, 4)
            if type_combo is not None:
                idx = type_combo.findText(dtype)
                if idx >= 0:
                    type_combo.setCurrentIndex(idx)

            dim = meta.get("dim", 1)
            try:
                dim_i = int(dim)
            except Exception:
                dim_i = 1
            dim_i = max(1, dim_i)
            if kind == "序列":
                dim_i = 1
            dim_spin = self._cell_spin(row, 5)
            if dim_spin is not None:
                dim_spin.setValue(dim_i)

            init_item = self.symbols_table.item(row, 6)
            init = meta.get("init")
            if init_item is not None:
                if isinstance(init, list):
                    init_item.setText(",".join([str(x) for x in init]))
                else:
                    init_item.setText(str(init if init is not None else 0))

            desc_item = self.symbols_table.item(row, 7)
            if desc_item is not None:
                desc_item.setText(str(meta.get("desc") or ""))

            self._apply_symbol_row_enabled(row)

    def _symbols_changed(self):
        if self._suppress_updates:
            return
        kind_map = {"常数": "constant", "变量": "scalar", "序列": "sequence"}
        io_map = {"内部": "internal", "输入": "input", "输出": "output"}
        data: Dict[str, Any] = {}

        for r in range(self.symbols_table.rowCount()):
            name_item = self.symbols_table.item(r, 0)
            name = (name_item.text() if name_item else "").strip()
            if not name:
                continue

            io_cn = self._cell_combo_text(r, 1) or "内部"
            io = io_map.get(io_cn, "internal")
            kind_cn = self._cell_combo_text(r, 2) or "变量"
            kind = kind_map.get(kind_cn, "scalar")
            iterate = self._cell_checkbox_checked(r, 3)
            dtype = self._cell_combo_text(r, 4) or "f64"
            dim = self._cell_spin_value(r, 5, 1)
            init_text = (self.symbols_table.item(r, 6).text() if self.symbols_table.item(r, 6) else "").strip()
            desc = (self.symbols_table.item(r, 7).text() if self.symbols_table.item(r, 7) else "").strip()

            entry: Dict[str, Any] = {"io": io, "kind": kind, "type": dtype, "dim": max(1, int(dim))}
            if kind == "sequence":
                entry["dim"] = 1
                v0 = self._coerce_typed_array(dtype, init_text, 1)
                entry["init"] = [v0]
            else:
                init_val = self._coerce_typed_array(dtype, init_text, entry["dim"])
                entry["init"] = init_val
            if desc:
                entry["desc"] = desc
            if kind == "sequence" and iterate:
                entry["iterate"] = True
            data[name] = entry

        self.doc["data"] = data
        self._after_doc_changed(rebuild_tree=False)

    def _parse_port_type(self, t: str) -> Tuple[str, int]:
        s = (t or "").strip()
        if not s:
            return "", 1
        if "[" in s and s.endswith("]"):
            base, _, tail = s.partition("[")
            try:
                dim = int(tail[:-1])
            except Exception:
                dim = 1
            return base.strip(), max(1, dim)
        return s, 1

    def _build_port_type(self, dtype: str, dim: int) -> str:
        dim = max(1, int(dim))
        if dim == 1:
            return dtype
        return f"{dtype}[{dim}]"

    def _coerce_typed_value(self, dtype: str, text: str):
        s = (text or "").strip()
        if dtype in {"int", "uint"}:
            try:
                v = int(float(s)) if s else 0
            except Exception:
                v = 0
            if dtype == "uint":
                v = max(0, v)
            return v
        try:
            return float(s) if s else 0.0
        except Exception:
            return 0.0

    def _coerce_typed_array(self, dtype: str, text: str, dim: int):
        dim = max(1, int(dim))
        raw = (text or "").strip()
        if dim == 1:
            return self._coerce_typed_value(dtype, raw)
        parts = [p.strip() for p in raw.split(",") if p.strip() != ""]
        if not parts:
            parts = ["0"]
        values = [self._coerce_typed_value(dtype, p) for p in parts]
        if len(values) == 1:
            values = values * dim
        if len(values) < dim:
            values = values + [values[-1]] * (dim - len(values))
        if len(values) > dim:
            values = values[:dim]
        return values

    def _cell_checkbox(self, row: int, col: int) -> Optional[QCheckBox]:
        w = self.symbols_table.cellWidget(row, col)
        if isinstance(w, QCheckBox):
            return w
        if w is not None:
            cb = w.findChild(QCheckBox)
            if isinstance(cb, QCheckBox):
                return cb
        return None

    def _cell_checkbox_checked(self, row: int, col: int) -> bool:
        w = self._cell_checkbox(row, col)
        return bool(w.isChecked()) if w is not None else False

    def _cell_combo(self, row: int, col: int) -> Optional[QComboBox]:
        w = self.symbols_table.cellWidget(row, col)
        return w if isinstance(w, QComboBox) else None

    def _cell_combo_text(self, row: int, col: int) -> str:
        w = self._cell_combo(row, col)
        return str(w.currentText()).strip() if w is not None else ""

    def _cell_spin(self, row: int, col: int) -> Optional[QSpinBox]:
        w = self.symbols_table.cellWidget(row, col)
        return w if isinstance(w, QSpinBox) else None

    def _cell_spin_value(self, row: int, col: int, default: int) -> int:
        w = self._cell_spin(row, col)
        return int(w.value()) if w is not None else int(default)

    def _ports_changed(self):
        if self._suppress_updates:
            return
        ports = self.doc.setdefault("ports", {"inputs": [], "outputs": []})
        ports["inputs"] = self._read_ports_table(self.inputs_table)
        ports["outputs"] = self._read_ports_table(self.outputs_table)
        self._after_doc_changed(rebuild_tree=False)

    def _read_ports_table(self, table: QTableWidget) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        for r in range(table.rowCount()):
            pid = (table.item(r, 0).text() if table.item(r, 0) else "").strip()
            ptype = (table.item(r, 1).text() if table.item(r, 1) else "").strip()
            unit = (table.item(r, 2).text() if table.item(r, 2) else "").strip()
            if not pid:
                continue
            it: Dict[str, Any] = {"id": pid}
            if ptype:
                it["type"] = ptype
            if unit:
                it["unit"] = unit
            items.append(it)
        return items

    def _refresh_ports_tables(self):
        ports = self.doc.get("ports", {}) if isinstance(self.doc.get("ports"), dict) else {}
        inputs = ports.get("inputs", []) if isinstance(ports.get("inputs"), list) else []
        outputs = ports.get("outputs", []) if isinstance(ports.get("outputs"), list) else []
        self._fill_ports_table(self.inputs_table, inputs)
        self._fill_ports_table(self.outputs_table, outputs)

    def _fill_ports_table(self, table: QTableWidget, ports: List[Any]):
        table.setRowCount(0)
        for p in ports:
            if not isinstance(p, dict):
                continue
            r = table.rowCount()
            table.insertRow(r)
            table.setItem(r, 0, QTableWidgetItem(str(p.get("id", ""))))
            table.setItem(r, 1, QTableWidgetItem(str(p.get("type", ""))))
            table.setItem(r, 2, QTableWidgetItem(str(p.get("unit", ""))))

    def _add_input_port(self):
        self.inputs_table.insertRow(self.inputs_table.rowCount())
        self._ports_changed()

    def _del_input_port(self):
        r = self.inputs_table.currentRow()
        if r >= 0:
            self.inputs_table.removeRow(r)
            self._ports_changed()

    def _add_output_port(self):
        self.outputs_table.insertRow(self.outputs_table.rowCount())
        self._ports_changed()

    def _del_output_port(self):
        r = self.outputs_table.currentRow()
        if r >= 0:
            self.outputs_table.removeRow(r)
            self._ports_changed()

    def _scalars_changed(self):
        if self._suppress_updates:
            return
        state = self.doc.setdefault("state", {"STATE": "Step1", "scalars": {}, "sequences": {}})
        scalars: Dict[str, Any] = {}
        for r in range(self.scalars_table.rowCount()):
            name = (self.scalars_table.item(r, 0).text() if self.scalars_table.item(r, 0) else "").strip()
            val_text = (self.scalars_table.item(r, 1).text() if self.scalars_table.item(r, 1) else "").strip()
            if not name:
                continue
            scalars[name] = self._coerce_number_or_str(val_text)
        state["scalars"] = scalars
        self._after_doc_changed(rebuild_tree=False)

    def _refresh_scalars_table(self):
        state = self.doc.get("state", {}) if isinstance(self.doc.get("state"), dict) else {}
        scalars = state.get("scalars", {}) if isinstance(state.get("scalars"), dict) else {}
        self.scalars_table.setRowCount(0)
        for k in sorted(scalars.keys()):
            r = self.scalars_table.rowCount()
            self.scalars_table.insertRow(r)
            self.scalars_table.setItem(r, 0, QTableWidgetItem(str(k)))
            self.scalars_table.setItem(r, 1, QTableWidgetItem(str(scalars.get(k))))

    def _add_scalar(self):
        self.scalars_table.insertRow(self.scalars_table.rowCount())
        self._scalars_changed()

    def _del_scalar(self):
        r = self.scalars_table.currentRow()
        if r >= 0:
            self.scalars_table.removeRow(r)
            self._scalars_changed()

    def _sequences_changed(self):
        if self._suppress_updates:
            return
        state = self.doc.setdefault("state", {"STATE": "Step1", "scalars": {}, "sequences": {}})
        sequences: Dict[str, Any] = {}
        for r in range(self.sequences_table.rowCount()):
            name = (self.sequences_table.item(r, 0).text() if self.sequences_table.item(r, 0) else "").strip()
            init0_text = (self.sequences_table.item(r, 1).text() if self.sequences_table.item(r, 1) else "").strip()
            length_text = (self.sequences_table.item(r, 2).text() if self.sequences_table.item(r, 2) else "").strip()
            if not name:
                continue
            init0 = self._coerce_number_or_str(init0_text)
            try:
                ln = int(length_text) if length_text else 1
            except Exception:
                ln = 1
            ln = max(1, ln)
            try:
                init0f = float(init0) if isinstance(init0, (int, float)) else float(str(init0))
            except Exception:
                init0f = 0.0
            sequences[name] = {"init": [init0f] * ln}
        state["sequences"] = sequences
        self._after_doc_changed(rebuild_tree=False)

    def _refresh_sequences_table(self):
        state = self.doc.get("state", {}) if isinstance(self.doc.get("state"), dict) else {}
        sequences = state.get("sequences", {}) if isinstance(state.get("sequences"), dict) else {}
        self.sequences_table.setRowCount(0)
        for k in sorted(sequences.keys()):
            seq = sequences.get(k)
            init = []
            if isinstance(seq, dict) and isinstance(seq.get("init"), list):
                init = seq.get("init") or []
            init0 = init[0] if init else 0.0
            ln = len(init) if init else 1
            r = self.sequences_table.rowCount()
            self.sequences_table.insertRow(r)
            self.sequences_table.setItem(r, 0, QTableWidgetItem(str(k)))
            self.sequences_table.setItem(r, 1, QTableWidgetItem(str(init0)))
            self.sequences_table.setItem(r, 2, QTableWidgetItem(str(ln)))

    def _add_sequence(self):
        self.sequences_table.insertRow(self.sequences_table.rowCount())
        self._sequences_changed()

    def _del_sequence(self):
        r = self.sequences_table.currentRow()
        if r >= 0:
            self.sequences_table.removeRow(r)
            self._sequences_changed()

    def _commit_changed(self):
        if self._suppress_updates:
            return
        commit = self.doc.setdefault("commit", {"shift_sequences": []})
        names: List[str] = []
        for i in range(self.shift_list.count()):
            it = self.shift_list.item(i)
            if it is None:
                continue
            name = (it.text() or "").strip()
            if name:
                names.append(name)
        commit["shift_sequences"] = names
        self._after_doc_changed(rebuild_tree=False)

    def _refresh_commit_list(self):
        commit = self.doc.get("commit", {}) if isinstance(self.doc.get("commit"), dict) else {}
        seqs = commit.get("shift_sequences", []) if isinstance(commit.get("shift_sequences"), list) else []
        self.shift_list.clear()
        for s in seqs:
            it = QListWidgetItem(str(s))
            self.shift_list.addItem(it)

    def _commit_add(self):
        state = self.doc.get("state", {}) if isinstance(self.doc.get("state"), dict) else {}
        sequences = state.get("sequences", {}) if isinstance(state.get("sequences"), dict) else {}
        names = sorted(sequences.keys())
        if not names:
            self._show_bar("warning", "无可选序列", "请先在 Sequences 中添加")
            return
        existing = {self.shift_list.item(i).text() for i in range(self.shift_list.count()) if self.shift_list.item(i)}
        for name in names:
            if name not in existing:
                self.shift_list.addItem(QListWidgetItem(name))
                self._commit_changed()
                return

    def _commit_del(self):
        r = self.shift_list.currentRow()
        if r >= 0:
            self.shift_list.takeItem(r)
            self._commit_changed()
