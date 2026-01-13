import argparse
import os
import sys
from PyQt5.QtWidgets import QApplication

# 将 src 目录添加到 sys.path 以支持绝对导入
src_dir = os.path.dirname(os.path.abspath(__file__))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from core.config_manager import get_config_manager, set_program_dir_override
from core.font_manager import FontManager
from ui.interfaces.login_interface import LoginWindow
from ui.loading_dialog import LoadingDialog

def _parse_args(argv):
    parser = argparse.ArgumentParser(description="RTopenEuler 系统管理工具")
    parser.add_argument("-d", "--dir", dest="program_dir", help="指定程序资源目录")
    parser.add_argument("--skip-login", action="store_true", help="跳过登录界面直接进入主页")
    return parser.parse_known_args(argv)

def _create_main_window(progress_callback=None):
    from ui.main_window import MainWindow
    return MainWindow(progress_callback=progress_callback)

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

    def _start_main_window():
        loading_dialog = LoadingDialog()
        loading_dialog.set_progress(0, "正在初始化主窗口...")
        loading_dialog.show()
        QApplication.processEvents()

        def _update_progress(value, text=None):
            loading_dialog.set_progress(value, text)
            QApplication.processEvents()

        main_holder["window"] = _create_main_window(_update_progress)
        main_holder["window"].show()
        loading_dialog.close()
        main_holder["loading"] = loading_dialog
    
    if args.skip_login:
        # 如果指定了跳过登录，直接创建并显示主窗口
        _start_main_window()
    else:
        # 否则显示登录界面
        login_window = LoginWindow()
        
        def _on_login_success(_username):
            login_window.close()
            _start_main_window()
            
        login_window.login_success.connect(_on_login_success)
        login_window.show()
        # 保持引用以防被垃圾回收
        main_holder["login"] = login_window
        
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
