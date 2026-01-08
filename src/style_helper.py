"""
样式助手模块
提供动态样式生成功能，避免硬编码字体大小
"""

from font_manager import FontManager


def get_font_style(size_type="body", **kwargs):
    """
    生成包含 font-size 的样式字符串

    参数:
        size_type: 字体大小类型 (base, body, caption, title, subtitle, large_title, small, tiny)
        **kwargs: 其他样式属性

    返回:
        格式化的样式字符串
    """
    font_size = FontManager.get_font_size(size_type)

    # 处理额外的样式属性
    styles = [f"font-size: {font_size}px"]
    for key, value in kwargs.items():
        # 将下划线命名转换为连字符命名
        css_key = key.replace('_', '-')
        styles.append(f"{css_key}: {value}")

    return "; ".join(styles) + ";"
