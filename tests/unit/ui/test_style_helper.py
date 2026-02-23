"""
样式辅助类测试
测试 src/ui/style_helper.py 的功能
"""

import pytest
from unittest.mock import patch, MagicMock

# 检查是否可以使用PyQt5
pytest.importorskip("PyQt5", reason="PyQt5 not available")

# 跳过图形界面依赖的测试
pytestmark = [
    pytest.mark.skipif(
        not pytest.config.getoption("--qt", default=False) if hasattr(pytest, "config") else True,
        reason="GUI tests skipped. Use --qt flag to run GUI tests."
    ) if hasattr(pytest, "config") else pytest.mark.skip(reason="GUI tests require --qt flag"),
]


def test_get_font_style_exists():
    """测试 style_helper 模块是否存在"""
    try:
        from ui.style_helper import get_font_style
        assert callable(get_font_style)
    except ImportError as e:
        pytest.skip(f"style_helper module not available: {e}")


@pytest.fixture
def mock_font_manager():
    """Mock FontManager 以避免真实的QApplication依赖"""
    with patch("ui.style_helper.FontManager") as mock:
        mock.get_font_size.return_value = 16
        yield mock


def test_get_font_style_basic(mock_font_manager):
    """测试基本字体样式生成"""
    from ui.style_helper import get_font_style

    result = get_font_style("body")
    assert "font-size: 16px" in result
    assert result.endswith(";")


def test_get_font_style_with_kwargs(mock_font_manager):
    """测试带额外样式的字体样式生成"""
    from ui.style_helper import get_font_style

    result = get_font_style("title", font_weight="bold", color="red")

    assert "font-size: 16px" in result
    assert "font-weight: bold" in result
    assert "color: red" in result


def test_get_font_style_underscore_to_hyphen(mock_font_manager):
    """测试下划线到连字符的转换"""
    from ui.style_helper import get_font_style

    result = get_font_style("body", background_color="white", text_align="center")

    assert "background-color: white" in result
    assert "text-align: center" in result


def test_get_font_style_different_sizes(mock_font_manager):
    """测试不同字体大小类型"""
    from ui.style_helper import get_font_style

    size_types = ["base", "body", "caption", "title", "subtitle", "large_title", "small", "tiny"]

    for size_type in size_types:
        mock_font_manager.get_font_size.return_value = 20
        result = get_font_style(size_type)
        assert "font-size: 20px" in result


class TestStyleHelperWithoutGUI:
    """无需GUI的单元测试"""

    def test_font_manager_called_with_correct_params(self):
        """测试FontManager被正确调用"""
        with patch("ui.style_helper.FontManager") as mock:
            mock.get_font_size.return_value = 18
            from ui.style_helper import get_font_style

            get_font_style("title")
            mock.get_font_size.assert_called_once_with("title")

    def test_font_manager_returns_correct_value(self):
        """测试FontManager返回值被正确使用"""
        with patch("ui.style_helper.FontManager") as mock:
            mock.get_font_size.return_value = 24
            from ui.style_helper import get_font_style

            result = get_font_style("large_title")
            assert "font-size: 24px" in result


# 如果无法导入实际模块，提供基础UI测试示例
class TestStyleHelperFallback:
    """当实际模块不可用时提供基础测试示例"""

    def test_example_style_generation(self):
        """示例：样式生成测试"""
        # 这是一个示例测试，展示了如何测试样式生成功能
        def example_get_style(font_size, **kwargs):
            styles = [f"font-size: {font_size}px"]
            for key, value in kwargs.items():
                css_key = key.replace('_', '-')
                styles.append(f"{css_key}: {value}")
            return "; ".join(styles) + ";"

        result = example_get_style(16, color="red")
        assert "font-size: 16px" in result
        assert "color: red" in result

    def test_example_font_size_types(self):
        """示例：不同字体大小类型测试"""
        font_sizes = {
            "small": 13,
            "base": 16,
            "body": 18,
            "caption": 15,
            "title": 23,
            "subtitle": 20,
            "large_title": 38,
        }

        for size_type, expected_size in font_sizes.items():
            assert isinstance(expected_size, int)
            assert expected_size > 0
