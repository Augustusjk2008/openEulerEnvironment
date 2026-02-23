"""
Mock配置管理器
用于测试时隔离真实配置文件
"""

from typing import Dict, Any, Optional


class MockConfigManager:
    """Mock配置管理器，用于测试"""

    DEFAULT_CONFIG = {
        "font_size": "small",
        "remember_window_pos": False,
        "window_pos": None,
        "default_output_dir": r"C:\Projects",
        "default_install_dir": r"C:\openEulerTools",
        "ssh_host": "",
        "ssh_username": "",
        "ssh_password": "",
        "ftp_host": "",
        "ftp_username": "",
        "ftp_password": "",
        "auto_check_update": False,
        "show_log_timestamp": True,
        "confirm_before_init": True,
        "protocol_csv_dir": "",
        "autopilot_json_dir": "",
    }

    FONT_SIZE_MAP = {
        "small": 10,
        "medium": 13,
        "large": 16,
    }

    def __init__(self, initial_config: Optional[Dict[str, Any]] = None):
        """
        初始化Mock配置管理器

        Args:
            initial_config: 初始配置字典，默认为None（使用默认配置）
        """
        self.config = self.DEFAULT_CONFIG.copy()
        if initial_config:
            self.config.update(initial_config)
        self._saved = False
        self._save_count = 0

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> bool:
        """设置配置项"""
        self.config[key] = value
        self._saved = True
        self._save_count += 1
        return True

    def get_font_size(self) -> int:
        """获取字体大小"""
        size_name = self.get("font_size", "small")
        return self.FONT_SIZE_MAP.get(size_name, 9)

    def set_font_size(self, size_name: str) -> bool:
        """设置字体大小"""
        if size_name in self.FONT_SIZE_MAP:
            return self.set("font_size", size_name)
        return False

    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self.config.copy()

    def reset_to_default(self) -> bool:
        """重置为默认配置"""
        self.config = self.DEFAULT_CONFIG.copy()
        self._saved = True
        self._save_count += 1
        return True

    def was_saved(self) -> bool:
        """检查配置是否被保存过"""
        return self._saved

    def get_save_count(self) -> int:
        """获取保存次数"""
        return self._save_count

    def reset_save_tracking(self):
        """重置保存跟踪状态"""
        self._saved = False
        self._save_count = 0


def create_mock_config_manager(**kwargs) -> MockConfigManager:
    """
    创建Mock配置管理器的工厂函数

    Args:
        **kwargs: 自定义配置项

    Returns:
        MockConfigManager实例
    """
    return MockConfigManager(kwargs)
