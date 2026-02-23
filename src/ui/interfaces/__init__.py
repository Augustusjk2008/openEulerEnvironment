"""
UI界面模块

包含所有用户界面界面类。
"""

# 延迟导入 - 只在需要时才导入子模块
# 这样可以避免在测试时由于缺少依赖导致的导入错误

# 子模块列表
__all__ = [
    "login_interface",
    "settings_interface",
    "initializer_interface",
    "environment_install_interface",
    "terminal_interface",
    "ftp_interface",
    "data_visualization_interface",
    "protocol_editor_interface",
    "autopilot_editor_interface",
    "code_generation_interface",
    "tutorial_interface",
]

def __getattr__(name):
    """延迟加载子模块"""
    if name in __all__:
        module = __import__(f'ui.interfaces.{name}', fromlist=[name])
        return module
    raise AttributeError(f"module 'ui.interfaces' has no attribute '{name}'")

