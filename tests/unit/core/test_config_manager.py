"""
ConfigManager单元测试
测试配置管理器的各项功能
"""

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

# 确保src在路径中
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent / "src"))

from core.config_manager import ConfigManager, get_config_manager, get_program_dir, set_program_dir_override


@pytest.fixture
def temp_config_dir(tmp_path):
    """提供临时配置目录"""
    return tmp_path


@pytest.fixture
def isolated_config_manager(temp_config_dir, monkeypatch):
    """提供隔离的配置管理器实例"""
    # 设置程序目录覆盖，使用临时目录
    set_program_dir_override(str(temp_config_dir))

    # 创建新的配置管理器实例
    manager = ConfigManager()

    yield manager

    # 清理：重置单例和覆盖
    import core.config_manager as cm
    cm._config_manager = None
    set_program_dir_override(None)


class TestConfigManagerBasic:
    """测试配置管理器基本功能"""

    def test_default_config_values(self, isolated_config_manager):
        """测试默认配置值"""
        manager = isolated_config_manager

        assert manager.get("font_size") == "small"
        assert manager.get("remember_window_pos") is False
        assert manager.get("window_pos") is None
        assert manager.get("default_output_dir") == r"C:\Projects"
        assert manager.get("default_install_dir") == r"C:\openEulerTools"
        assert manager.get("ssh_host") == ""
        assert manager.get("ssh_username") == ""
        assert manager.get("ssh_password") == ""
        assert manager.get("ftp_host") == ""
        assert manager.get("ftp_username") == ""
        assert manager.get("ftp_password") == ""
        assert manager.get("auto_check_update") is False
        assert manager.get("show_log_timestamp") is True
        assert manager.get("confirm_before_init") is True
        assert manager.get("protocol_csv_dir") == ""
        assert manager.get("autopilot_json_dir") == ""

    def test_get_with_default(self, isolated_config_manager):
        """测试获取配置时使用默认值"""
        manager = isolated_config_manager

        # 不存在的键，使用提供的默认值
        assert manager.get("nonexistent_key", "default_value") == "default_value"
        assert manager.get("nonexistent_key") is None

    def test_set_and_get(self, isolated_config_manager):
        """测试设置和获取配置"""
        manager = isolated_config_manager

        # 设置新值
        assert manager.set("ssh_host", "192.168.1.1") is True
        assert manager.get("ssh_host") == "192.168.1.1"

        # 设置另一个值
        assert manager.set("ssh_username", "testuser") is True
        assert manager.get("ssh_username") == "testuser"

    def test_set_persists_to_file(self, isolated_config_manager, temp_config_dir):
        """测试设置会持久化到文件"""
        manager = isolated_config_manager

        manager.set("ssh_host", "192.168.1.100")
        manager.set("ssh_username", "persistent_user")

        # 创建新实例，应该读取到保存的值
        manager2 = ConfigManager()
        assert manager2.get("ssh_host") == "192.168.1.100"
        assert manager2.get("ssh_username") == "persistent_user"


class TestFontSizeMap:
    """测试字体大小映射功能"""

    def test_font_size_map_values(self):
        """测试字体大小映射值"""
        assert ConfigManager.FONT_SIZE_MAP["small"] == 10
        assert ConfigManager.FONT_SIZE_MAP["medium"] == 13
        assert ConfigManager.FONT_SIZE_MAP["large"] == 16

    def test_get_font_size(self, isolated_config_manager):
        """测试获取字体大小"""
        manager = isolated_config_manager

        manager.set("font_size", "small")
        assert manager.get_font_size() == 10

        manager.set("font_size", "medium")
        assert manager.get_font_size() == 13

        manager.set("font_size", "large")
        assert manager.get_font_size() == 16

    def test_get_font_size_invalid(self, isolated_config_manager):
        """测试获取无效字体大小时返回默认值"""
        manager = isolated_config_manager

        # 设置无效值
        manager.config["font_size"] = "invalid_size"
        # 应该返回默认值9
        assert manager.get_font_size() == 9

    def test_set_font_size_valid(self, isolated_config_manager):
        """测试设置有效字体大小"""
        manager = isolated_config_manager

        assert manager.set_font_size("small") is True
        assert manager.get("font_size") == "small"

        assert manager.set_font_size("medium") is True
        assert manager.get("font_size") == "medium"

        assert manager.set_font_size("large") is True
        assert manager.get("font_size") == "large"

    def test_set_font_size_invalid(self, isolated_config_manager):
        """测试设置无效字体大小"""
        manager = isolated_config_manager

        assert manager.set_font_size("huge") is False
        assert manager.set_font_size("tiny") is False
        assert manager.set_font_size(123) is False


class TestResetToDefault:
    """测试重置为默认配置功能"""

    def test_reset_to_default(self, isolated_config_manager):
        """测试重置为默认配置"""
        manager = isolated_config_manager

        # 修改一些配置
        manager.set("ssh_host", "modified_host")
        manager.set("ssh_username", "modified_user")
        manager.set("font_size", "large")

        # 重置
        assert manager.reset_to_default() is True

        # 验证恢复默认值
        assert manager.get("ssh_host") == ""
        assert manager.get("ssh_username") == ""
        assert manager.get("font_size") == "small"

    def test_reset_persists(self, isolated_config_manager, temp_config_dir):
        """测试重置会持久化到文件"""
        manager = isolated_config_manager

        manager.set("ssh_host", "modified_host")
        manager.reset_to_default()

        # 创建新实例验证
        manager2 = ConfigManager()
        assert manager2.get("ssh_host") == ""


class TestGetAll:
    """测试获取所有配置"""

    def test_get_all_returns_copy(self, isolated_config_manager):
        """测试get_all返回配置副本"""
        manager = isolated_config_manager

        all_config = manager.get_all()

        # 修改返回的字典不应影响原配置
        all_config["ssh_host"] = "modified"
        assert manager.get("ssh_host") != "modified"

    def test_get_all_contains_all_keys(self, isolated_config_manager):
        """测试get_all包含所有配置键"""
        manager = isolated_config_manager

        all_config = manager.get_all()
        default_keys = set(ConfigManager.DEFAULT_CONFIG.keys())
        actual_keys = set(all_config.keys())

        assert default_keys == actual_keys


class TestConfigFileOperations:
    """测试配置文件操作"""

    def test_config_file_created_on_init(self, temp_config_dir, monkeypatch):
        """测试初始化时创建配置文件"""
        set_program_dir_override(str(temp_config_dir))

        # 删除可能存在的配置文件
        config_file = temp_config_dir / "settings.json"
        if config_file.exists():
            config_file.unlink()

        # 创建新实例
        manager = ConfigManager()

        # 验证配置文件被创建
        assert config_file.exists()

        # 验证内容
        with open(config_file, "r", encoding="utf-8") as f:
            saved_config = json.load(f)
        assert saved_config["font_size"] == "small"

        # 清理
        import core.config_manager as cm
        cm._config_manager = None
        set_program_dir_override(None)

    def test_load_existing_config(self, temp_config_dir, monkeypatch):
        """测试加载现有配置文件"""
        # 预先创建配置文件
        config_file = temp_config_dir / "settings.json"
        custom_config = {
            "font_size": "large",
            "ssh_host": "192.168.1.50",
            "custom_key": "custom_value",
        }
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(custom_config, f)

        set_program_dir_override(str(temp_config_dir))
        manager = ConfigManager()

        # 验证加载了现有配置
        assert manager.get("font_size") == "large"
        assert manager.get("ssh_host") == "192.168.1.50"
        assert manager.get("custom_key") == "custom_value"

        # 清理
        import core.config_manager as cm
        cm._config_manager = None
        set_program_dir_override(None)

    def test_merge_with_defaults(self, temp_config_dir, monkeypatch):
        """测试配置合并默认值"""
        # 创建部分配置
        config_file = temp_config_dir / "settings.json"
        partial_config = {"font_size": "medium"}
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(partial_config, f)

        set_program_dir_override(str(temp_config_dir))
        manager = ConfigManager()

        # 验证既有自定义值，也有默认值
        assert manager.get("font_size") == "medium"
        assert manager.get("ssh_host") == ""  # 默认值
        assert manager.get("remember_window_pos") is False  # 默认值

        # 清理
        import core.config_manager as cm
        cm._config_manager = None
        set_program_dir_override(None)

    def test_invalid_json_handling(self, temp_config_dir, monkeypatch, capsys):
        """测试无效JSON处理"""
        # 创建无效JSON文件
        config_file = temp_config_dir / "settings.json"
        config_file.write_text("invalid json content")

        set_program_dir_override(str(temp_config_dir))
        manager = ConfigManager()

        # 验证使用默认配置
        assert manager.get("font_size") == "small"

        # 清理
        import core.config_manager as cm
        cm._config_manager = None
        set_program_dir_override(None)


class TestProgramDirOverride:
    """测试程序目录覆盖功能"""

    def test_set_program_dir_override(self, tmp_path):
        """测试设置程序目录覆盖"""
        test_path = str(tmp_path / "test_dir")

        set_program_dir_override(test_path)

        assert get_program_dir() == str(Path(test_path).resolve())

        # 清理
        set_program_dir_override(None)

    def test_set_program_dir_override_none(self, tmp_path):
        """测试重置程序目录覆盖为None"""
        test_path = str(tmp_path / "test_dir")

        set_program_dir_override(test_path)
        set_program_dir_override(None)

        # 应该返回实际程序目录
        program_dir = get_program_dir()
        assert "test_dir" not in program_dir

    def test_get_program_dir_with_override(self, tmp_path):
        """测试带覆盖的程序目录获取"""
        original_dir = get_program_dir()

        override_path = str(tmp_path / "override")
        set_program_dir_override(override_path)

        assert get_program_dir() == str(Path(override_path).resolve())

        # 清理
        set_program_dir_override(None)
        assert get_program_dir() == original_dir


class TestSingleton:
    """测试单例模式"""

    def test_get_config_manager_singleton(self, temp_config_dir, monkeypatch):
        """测试配置管理器单例"""
        set_program_dir_override(str(temp_config_dir))

        manager1 = get_config_manager()
        manager2 = get_config_manager()

        assert manager1 is manager2

        # 清理
        import core.config_manager as cm
        cm._config_manager = None
        set_program_dir_override(None)

    def test_singleton_state_shared(self, temp_config_dir, monkeypatch):
        """测试单例状态共享"""
        set_program_dir_override(str(temp_config_dir))

        manager1 = get_config_manager()
        manager1.set("ssh_host", "shared_host")

        manager2 = get_config_manager()
        assert manager2.get("ssh_host") == "shared_host"

        # 清理
        import core.config_manager as cm
        cm._config_manager = None
        set_program_dir_override(None)


class TestEdgeCases:
    """测试边界情况"""

    def test_empty_string_value(self, isolated_config_manager):
        """测试空字符串值"""
        manager = isolated_config_manager

        manager.set("ssh_host", "")
        assert manager.get("ssh_host") == ""

    def test_none_value(self, isolated_config_manager):
        """测试None值"""
        manager = isolated_config_manager

        manager.set("window_pos", None)
        assert manager.get("window_pos") is None

    def test_boolean_values(self, isolated_config_manager):
        """测试布尔值"""
        manager = isolated_config_manager

        manager.set("remember_window_pos", True)
        assert manager.get("remember_window_pos") is True

        manager.set("remember_window_pos", False)
        assert manager.get("remember_window_pos") is False

    def test_integer_values(self, isolated_config_manager):
        """测试整数值"""
        manager = isolated_config_manager

        manager.set("custom_int", 42)
        assert manager.get("custom_int") == 42

    def test_list_values(self, isolated_config_manager):
        """测试列表值"""
        manager = isolated_config_manager

        manager.set("window_pos", [100, 200])
        assert manager.get("window_pos") == [100, 200]

    def test_nested_dict_values(self, isolated_config_manager):
        """测试嵌套字典值"""
        manager = isolated_config_manager

        nested = {"key1": "value1", "key2": {"nested": "value"}}
        manager.set("nested_config", nested)
        assert manager.get("nested_config") == nested
