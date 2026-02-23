"""
配置文件管理模块
负责应用程序配置的读取、保存和管理
"""

import json
import os
import sys
from pathlib import Path

_program_dir_override = None


def set_program_dir_override(path):
    """设置程序资源目录"""
    global _program_dir_override
    if path:
        _program_dir_override = str(Path(path).resolve())
    else:
        _program_dir_override = None


def get_program_dir():
    """获取程序所在目录（支持命令行覆盖）"""
    if _program_dir_override:
        return _program_dir_override
    if getattr(sys, 'frozen', False):
        return str(Path(sys.executable).resolve().parent)
    return str(Path(__file__).resolve().parent)


class ConfigManager:
    """配置管理器"""

    # 默认配置（敏感信息如密码等应通过settings.json或界面输入）
    DEFAULT_CONFIG = {
        "font_size": "small",  # 字体大小: small, medium, large
        "remember_window_pos": False,  # 记住窗口位置
        "window_pos": None,  # 窗口位置 [x, y]
        "default_output_dir": r"C:\Projects",  # 默认输出目录
        "default_install_dir": r"C:\openEulerTools",  # 默认安装目录
        "ssh_host": "",  # SSH 主机地址（从settings.json读取）
        "ssh_username": "",  # SSH 用户名（从settings.json读取）
        "ssh_password": "",  # SSH 密码（从settings.json读取，不硬编码）
        "ftp_host": "",  # FTP 主机地址（从settings.json读取）
        "ftp_username": "",  # FTP 用户名（从settings.json读取）
        "ftp_password": "",  # FTP 密码（从settings.json读取，不硬编码）
        "auto_check_update": False,  # 自动检查更新
        "show_log_timestamp": True,  # 显示日志时间戳
        "confirm_before_init": True,  # 初始化前确认
        "protocol_csv_dir": "",  # 协议CSV目录
        "autopilot_json_dir": "",  # AutoPilot JSON 目录
    }

    # 字体大小映射
    FONT_SIZE_MAP = {
        "small": 10,     # 小（默认）
        "medium": 13,    # 中
        "large": 16,     # 大
    }

    def __init__(self):
        self.config_file = self._get_config_file_path()
        self.config = self._load_config()

    def _get_config_file_path(self):
        """获取配置文件路径"""
        base_dir = Path(get_program_dir())
        return base_dir / "settings.json"

    def _load_config(self):
        """加载配置文件"""
        config_path = Path(self.config_file)
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                # 合并配置，确保所有默认值都存在
                config = self.DEFAULT_CONFIG.copy()
                config.update(loaded_config)
                return config
            except (json.JSONDecodeError, IOError, OSError) as e:
                print(f"加载配置文件失败: {e}，使用默认配置")
                return self.DEFAULT_CONFIG.copy()
        else:
            # 配置文件不存在，创建默认配置文件
            self._save_config(self.DEFAULT_CONFIG)
            return self.DEFAULT_CONFIG.copy()

    def _save_config(self, config):
        """保存配置到文件"""
        try:
            config_path = Path(self.config_file)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
            return True
        except (IOError, OSError) as e:
            print(f"保存配置文件失败: {e}")
            return False

    def get(self, key, default=None):
        """获取配置项"""
        return self.config.get(key, default)

    def set(self, key, value):
        """设置配置项"""
        self.config[key] = value
        return self._save_config(self.config)

    def get_font_size(self):
        """获取字体大小"""
        size_name = self.get("font_size", "small")
        return self.FONT_SIZE_MAP.get(size_name, 9)

    def set_font_size(self, size_name):
        """设置字体大小"""
        if size_name in self.FONT_SIZE_MAP:
            return self.set("font_size", size_name)
        return False

    def get_all(self):
        """获取所有配置"""
        return self.config.copy()

    def reset_to_default(self):
        """重置为默认配置"""
        self.config = self.DEFAULT_CONFIG.copy()
        return self._save_config(self.config)


# 全局配置管理器实例
_config_manager = None


def get_config_manager():
    """获取配置管理器单例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
