from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout

class SettingsInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("settingsInterface")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("应用设置界面", self))
