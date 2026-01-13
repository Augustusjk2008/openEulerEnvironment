import os
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import (
    QDialog,
    QLabel,
    QProgressBar,
    QGridLayout,
    QVBoxLayout,
    QWidget,
    QSizePolicy,
)

from core.config_manager import get_program_dir


class LoadingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._source = None

        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setWindowModality(Qt.ApplicationModal)
        self.setFixedSize(720, 420)
        self._apply_icon()

        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.image_label, 0, 0)

        self._overlay = QWidget()
        overlay_layout = QVBoxLayout(self._overlay)
        overlay_layout.setContentsMargins(24, 0, 24, 24)
        overlay_layout.setSpacing(8)
        overlay_layout.addStretch()

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(16)
        overlay_layout.addWidget(self.progress_bar)

        self.progress_text = QLabel("")
        self.progress_text.setAlignment(Qt.AlignCenter)
        self.progress_text.setStyleSheet("color: white;")
        overlay_layout.addWidget(self.progress_text)

        layout.addWidget(self._overlay, 0, 0, Qt.AlignBottom)

        self._load_image()

    def _apply_icon(self):
        icon_path = os.path.join(get_program_dir(), "assets", "logo.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

    def _load_image(self):
        image_path = os.path.join(get_program_dir(), "assets", "loading.png")
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                self._source = pixmap
                self._update_pixmap()
                return
        self.image_label.setText("")

    def _update_pixmap(self):
        if self._source is None or self.image_label.size().isEmpty():
            return
        scaled = self._source.scaled(
            self.image_label.size(),
            Qt.KeepAspectRatioByExpanding,
            Qt.SmoothTransformation
        )
        self.image_label.setPixmap(scaled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_pixmap()

    def set_progress(self, value, text=None):
        if value is None:
            self.progress_bar.setRange(0, 0)
        else:
            if self.progress_bar.minimum() == 0 and self.progress_bar.maximum() == 0:
                self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(max(0, min(100, int(value))))
        if text:
            self.progress_text.setText(text)
        elif value is None:
            self.progress_text.setText("")
        else:
            self.progress_text.setText(f"{int(value)}%")
