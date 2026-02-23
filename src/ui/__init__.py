"""
UI模块

包含所有用户界面相关组件和界面类。
"""

# 延迟导入 - 只在需要时才导入子模块
# 这样可以避免在测试时由于缺少依赖导致的导入错误

def __getattr__(name):
    """延迟加载子模块"""
    # 只处理已知的子模块，其他属性返回None以避免导入错误
    if name == 'main_window':
        from . import main_window as module
        return module
    elif name == 'loading_dialog':
        from . import loading_dialog as module
        return module
    elif name == 'style_helper':
        from . import style_helper as module
        return module
    # 对于其他属性（如测试模块），返回None而不是抛出异常
    # 这样可以避免在测试导入时出现ModuleNotFoundError
    return None

__all__ = [
    "main_window",
    "loading_dialog",
    "style_helper",
]
