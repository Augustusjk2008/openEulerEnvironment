"""
全局字体管理器
统一管理应用程序的字体大小和样式
"""

from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication, QWidget


class FontManager:
    """字体管理器"""

    # 字体大小配置
    FONT_SIZES = {
        "small": {
            "base": 13,
            "body": 16,
            "caption": 14,
            "title": 20,
            "subtitle": 18,
            "large_title": 34,
            "small": 15,
            "tiny": 14,
            "label": 18,
        },
        "medium": {
            "base": 16,
            "body": 18,
            "caption": 15,
            "title": 23,
            "subtitle": 20,
            "large_title": 38,
            "small": 16,
            "tiny": 15,
            "label": 18,
        },
        "large": {
            "base": 19,
            "body": 20,
            "caption": 17,
            "title": 26,
            "subtitle": 22,
            "large_title": 42,
            "small": 17,
            "tiny": 16,
            "label": 19,
        },
    }

    _current_size = "small"

    @classmethod
    def get_font_size(cls, size_name="body"):
        """获取指定类型的字体大小"""
        return cls.FONT_SIZES[cls._current_size].get(size_name, 13)

    @classmethod
    def set_size(cls, size):
        """设置字体大小类别"""
        if size in cls.FONT_SIZES:
            cls._current_size = size

    @classmethod
    def get_current_size(cls):
        """获取当前字体大小类别"""
        return cls._current_size

    @classmethod
    def apply_global_font(cls, size_name="small"):
        """应用全局字体和样式表"""
        cls.set_size(size_name)
        base_size = cls.get_font_size("base")

        font = QFont()
        font.setFamily("Microsoft YaHei")
        font.setPointSize(base_size)

        app = QApplication.instance()
        app.setFont(font)

        # 应用全局样式表
        app.setStyleSheet(cls._get_global_stylesheet())

        return font

    @classmethod
    def _get_global_stylesheet(cls):
        """生成全局样式表"""
        s = cls.FONT_SIZES[cls._current_size]

        # 全局样式表，使用更具体的选择器来覆盖内联样式
        stylesheet = f"""
            /* 全局字体样式 - {cls._current_size.upper()} */

            /* 基础组件 - 最高优先级 */
            * {{
                font-family: "Microsoft YaHei";
            }}

            QWidget {{
                font-size: {s['body']}px;
            }}

            /* Fluent-Widgets 组件 */
            SubtitleLabel, TitleLabel {{
                font-size: {s['title']}px;
            }}
            BodyLabel {{
                font-size: {s['body']}px;
            }}
            StrongBodyLabel {{
                font-size: {s['body']}px;
                font-weight: 600;
            }}
            CaptionLabel {{
                font-size: {s['caption']}px;
            }}

            /* 标准 Qt 组件 */
            QLabel {{
                font-size: {s['body']}px;
            }}
            QPushButton {{
                font-size: {s['body']}px;
            }}
            QLineEdit {{
                font-size: {s['body']}px;
            }}
            QTextEdit {{
                font-size: {s['body']}px;
            }}
            QComboBox, QComboBox QAbstractItemView {{
                font-size: {s['body']}px;
            }}
            QCheckBox {{
                font-size: {s['body']}px;
            }}
            QRadioButton {{
                font-size: {s['body']}px;
            }}

            /* Fluent-Widgets 按钮 */
            PushButton, PrimaryPushButton, TransparentPushButton {{
                font-size: {s['body']}px;
            }}
            LineEdit {{
                font-size: {s['body']}px;
            }}
            ComboBox {{
                font-size: {s['body']}px;
            }}
        """
        return stylesheet

    @classmethod
    def format_size(cls, element_type):
        """
        格式化字体大小，用于动态样式
        element_type: base, body, caption, title, subtitle, large_title, small, tiny, label
        """
        return cls.get_font_size(element_type)

    @classmethod
    def apply_font_to_widget(cls, widget):
        """
        递归设置组件及其子组件的字体
        这个方法可以强制覆盖内联样式
        """
        s = cls.FONT_SIZES[cls._current_size]

        # 设置组件自身的字体
        font = QFont("Microsoft YaHei")
        font.setPointSize(s['base'])
        widget.setFont(font)

        # 递归设置所有子组件
        for child in widget.findChildren(QWidget):
            # 根据组件类型设置不同的字体大小
            child_font = QFont("Microsoft YaHei")

            # 获取组件类名
            class_name = child.__class__.__name__

            # 根据组件类型设置字体大小
            if class_name in ['SubtitleLabel', 'TitleLabel']:
                child_font.setPointSize(s['title'])
            elif class_name == 'CaptionLabel':
                child_font.setPointSize(s['caption'])
            elif class_name == 'StrongBodyLabel':
                child_font.setPointSize(s['body'])
                child_font.setBold(True)
            elif class_name == 'BodyLabel':
                child_font.setPointSize(s['body'])
            else:
                child_font.setPointSize(s['body'])

            child.setFont(child_font)
