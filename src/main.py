import os
import sys
from PyQt5.QtWidgets import QApplication

# 将 src 目录添加到 sys.path 以支持绝对导入
src_dir = os.path.dirname(os.path.abspath(__file__))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from core.config_manager import get_config_manager, set_program_dir_override
from core.font_manager import FontManager
from ui.main_window import MainWindow, _parse_args
from ui.interfaces.login_interface import LoginWindow

def main():
    args, qt_args = _parse_args(sys.argv[1:])
    if args.program_dir:
        program_dir = os.path.abspath(args.program_dir)
        if not os.path.isdir(program_dir):
            print(f"指定目录不存在: {program_dir}")
            sys.exit(1)
        set_program_dir_override(program_dir)

    app = QApplication([sys.argv[0]] + qt_args)

    # 在创建窗口之前，先加载配置并应用全局字体
    config_manager = get_config_manager()
    font_size_name = config_manager.get("font_size", "small")
    FontManager.apply_global_font(font_size_name)

    main_holder = {}
    login_window = LoginWindow()

    def _on_login_success(_username):
        main_holder["window"] = MainWindow()
        main_holder["window"].show()
        login_window.close()

    login_window.login_success.connect(_on_login_success)
    login_window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
