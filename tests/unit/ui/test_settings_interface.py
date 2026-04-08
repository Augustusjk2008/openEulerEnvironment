"""
设置界面单元测试

测试SettingsInterface的各项功能：
- 各设置项正确加载
- 修改设置后保存
- 重置为默认值
- 设置变更实时生效

依赖：pytest-qt
"""

import pytest
from unittest.mock import patch, MagicMock, Mock, call
from pathlib import Path
import json

# 尝试导入PyQt5相关模块
try:
    from PyQt5.QtWidgets import QApplication, QRadioButton, QLineEdit
    from PyQt5.QtCore import Qt
    from PyQt5.QtTest import QTest
    PYQT5_AVAILABLE = True
except ImportError:
    PYQT5_AVAILABLE = False

# 尝试导入设置界面
try:
    from ui.interfaces.settings_interface import SettingsInterface
    import ui.interfaces.settings_interface as settings_interface_module
    SETTINGS_INTERFACE_AVAILABLE = True
except ImportError as e:
    SETTINGS_INTERFACE_AVAILABLE = False
    SETTINGS_INTERFACE_IMPORT_ERROR = str(e)
    settings_interface_module = None


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def qapp_args():
    """自定义QApplication启动参数"""
    return ["pytest-qt"]


@pytest.fixture
def mock_settings_deps(monkeypatch, tmp_path):
    """
    Mock设置界面的所有依赖
    """
    # 如果设置界面模块不可用，跳过此fixture
    if not SETTINGS_INTERFACE_AVAILABLE:
        pytest.skip(f"SettingsInterface not available: {SETTINGS_INTERFACE_IMPORT_ERROR}")

    # 创建临时配置文件
    config_file = tmp_path / "settings.json"
    default_config = {
        "font_size": "small",
        "default_output_dir": r"C:\Projects",
        "default_install_dir": r"C:\openEulerTools",
        "ssh_host": "192.168.1.100",
        "ssh_username": "root",
        "ssh_password": "password123",
        "auto_check_update": False,
        "show_log_timestamp": True,
        "confirm_before_init": True,
    }
    config_file.write_text(json.dumps(default_config, ensure_ascii=False, indent=4))

    # Mock ConfigManager
    mock_config = MagicMock()
    mock_config.get = MagicMock(side_effect=lambda key, default=None: default_config.get(key, default))
    mock_config.set = MagicMock(return_value=True)
    mock_config.reset_to_default = MagicMock()
    mock_config.get_all.return_value = default_config.copy()

    monkeypatch.setattr("ui.interfaces.settings_interface.get_config_manager", lambda: mock_config)

    # Mock FontManager
    mock_font = MagicMock()
    mock_font.get_font_size.return_value = 12
    mock_font.set_size = MagicMock()
    monkeypatch.setattr("ui.interfaces.settings_interface.FontManager", mock_font)

    # Mock InfoBar
    mock_infobar = MagicMock()
    mock_infobar.success = MagicMock()
    mock_infobar.error = MagicMock()
    mock_infobar.warning = MagicMock()
    monkeypatch.setattr("ui.interfaces.settings_interface.InfoBar", mock_infobar)

    # Mock QFileDialog
    mock_dialog = MagicMock()
    mock_dialog.getExistingDirectory.return_value = str(tmp_path / "new_dir")
    monkeypatch.setattr("ui.interfaces.settings_interface.QFileDialog", mock_dialog)

    # Mock QMessageBox
    mock_msgbox = MagicMock()
    mock_msgbox.Question = 4
    mock_msgbox.Yes = 16384
    mock_msgbox.No = 65536
    mock_msgbox.question.return_value = mock_msgbox.Yes
    monkeypatch.setattr("ui.interfaces.settings_interface.QMessageBox", mock_msgbox)

    return {
        "config": mock_config,
        "infobar": mock_infobar,
        "dialog": mock_dialog,
        "msgbox": mock_msgbox,
        "config_file": config_file,
        "default_config": default_config
    }


@pytest.fixture
def settings_interface(qtbot, mock_settings_deps):
    """
    创建SettingsInterface实例用于测试
    """
    if not SETTINGS_INTERFACE_AVAILABLE:
        pytest.skip(f"SettingsInterface not available: {SETTINGS_INTERFACE_IMPORT_ERROR}")

    # 重置mock状态
    mock_settings_deps["config"].reset_mock()
    mock_settings_deps["infobar"].reset_mock()

    interface = SettingsInterface()
    qtbot.addWidget(interface)

    yield interface

    # 清理
    interface.close()
    interface.deleteLater()


# =============================================================================
# 基础界面测试
# =============================================================================

@pytest.mark.skipif(not PYQT5_AVAILABLE, reason="PyQt5 not available")
@pytest.mark.skipif(not SETTINGS_INTERFACE_AVAILABLE, reason=f"SettingsInterface not available")
class TestSettingsInterfaceBasic:
    """设置界面基础功能测试"""

    def test_interface_creation(self, settings_interface):
        """测试界面创建成功"""
        assert settings_interface is not None
        assert settings_interface.objectName() == "settingsInterface"

    def test_config_manager_initialized(self, settings_interface, mock_settings_deps):
        """测试配置管理器已初始化"""
        assert settings_interface.config_manager == mock_settings_deps["config"]

    def test_font_settings_card_exists(self, settings_interface):
        """测试字体设置卡片存在"""
        assert hasattr(settings_interface, 'font_card')
        assert settings_interface.font_card is not None

    def test_directory_settings_card_exists(self, settings_interface):
        """测试目录设置卡片存在"""
        assert hasattr(settings_interface, 'dir_card')
        assert settings_interface.dir_card is not None

    def test_ssh_settings_card_exists(self, settings_interface):
        """测试SSH设置卡片存在"""
        assert hasattr(settings_interface, 'ssh_card')
        assert settings_interface.ssh_card is not None

    def test_other_settings_card_exists(self, settings_interface):
        """测试其他设置卡片存在"""
        assert hasattr(settings_interface, 'other_card')
        assert settings_interface.other_card is not None

    def test_save_button_exists(self, settings_interface):
        """测试保存按钮存在"""
        assert hasattr(settings_interface, 'save_btn')
        assert settings_interface.save_btn is not None
        assert settings_interface.save_btn.text() == "保存设置"

    def test_reset_button_exists(self, settings_interface):
        """测试重置按钮存在"""
        assert hasattr(settings_interface, 'reset_btn')
        assert settings_interface.reset_btn is not None
        assert settings_interface.reset_btn.text() == "恢复默认设置"


# =============================================================================
# 设置加载测试
# =============================================================================

@pytest.mark.skipif(not PYQT5_AVAILABLE, reason="PyQt5 not available")
@pytest.mark.skipif(not SETTINGS_INTERFACE_AVAILABLE, reason=f"SettingsInterface not available")
class TestSettingsLoading:
    """设置加载测试"""

    def test_font_size_loaded(self, settings_interface, mock_settings_deps):
        """测试字体大小设置已加载"""
        # 验证radio button组存在
        assert hasattr(settings_interface, 'font_button_group')

        # 获取选中的按钮
        checked_button = None
        for button in settings_interface.font_button_group.buttons():
            if button.isChecked():
                checked_button = button
                break

        # 应该有一个被选中的按钮
        assert checked_button is not None
        # 验证值与配置一致
        assert checked_button.property("value") == mock_settings_deps["default_config"]["font_size"]

    def test_output_directory_loaded(self, settings_interface, mock_settings_deps):
        """测试输出目录设置已加载"""
        assert hasattr(settings_interface, 'output_dir_edit')
        expected_path = mock_settings_deps["default_config"]["default_output_dir"]
        assert settings_interface.output_dir_edit.text() == expected_path

    def test_install_directory_loaded(self, settings_interface, mock_settings_deps):
        """测试安装目录设置已加载"""
        assert hasattr(settings_interface, 'install_dir_edit')
        expected_path = mock_settings_deps["default_config"]["default_install_dir"]
        assert settings_interface.install_dir_edit.text() == expected_path

    def test_ssh_host_loaded(self, settings_interface, mock_settings_deps):
        """测试SSH主机设置已加载"""
        assert hasattr(settings_interface, 'ssh_host_edit')
        expected_host = mock_settings_deps["default_config"]["ssh_host"]
        assert settings_interface.ssh_host_edit.text() == expected_host

    def test_ssh_username_loaded(self, settings_interface, mock_settings_deps):
        """测试SSH用户名设置已加载"""
        assert hasattr(settings_interface, 'ssh_user_edit')
        expected_user = mock_settings_deps["default_config"]["ssh_username"]
        assert settings_interface.ssh_user_edit.text() == expected_user

    def test_ssh_password_loaded(self, settings_interface, mock_settings_deps):
        """测试SSH密码设置已加载"""
        assert hasattr(settings_interface, 'ssh_pass_edit')
        expected_pass = mock_settings_deps["default_config"]["ssh_password"]
        assert settings_interface.ssh_pass_edit.text() == expected_pass

    def test_auto_update_switch_loaded(self, settings_interface, mock_settings_deps):
        """测试自动更新开关设置已加载"""
        assert hasattr(settings_interface, 'update_switch')
        expected_value = mock_settings_deps["default_config"]["auto_check_update"]
        assert settings_interface.update_switch.isChecked() == expected_value

    def test_log_timestamp_switch_loaded(self, settings_interface, mock_settings_deps):
        """测试日志时间戳开关设置已加载"""
        assert hasattr(settings_interface, 'log_switch')
        expected_value = mock_settings_deps["default_config"]["show_log_timestamp"]
        assert settings_interface.log_switch.isChecked() == expected_value

    def test_confirm_init_switch_loaded(self, settings_interface, mock_settings_deps):
        """测试初始化确认开关设置已加载"""
        assert hasattr(settings_interface, 'confirm_switch')
        expected_value = mock_settings_deps["default_config"]["confirm_before_init"]
        assert settings_interface.confirm_switch.isChecked() == expected_value


# =============================================================================
# 设置保存测试
# =============================================================================

@pytest.mark.skipif(not PYQT5_AVAILABLE, reason="PyQt5 not available")
@pytest.mark.skipif(not SETTINGS_INTERFACE_AVAILABLE, reason=f"SettingsInterface not available")
class TestSettingsSaving:
    """设置保存测试"""

    def test_save_font_size(self, settings_interface, mock_settings_deps):
        """测试保存字体大小设置"""
        # 选择"中"字体
        for button in settings_interface.font_button_group.buttons():
            if button.property("value") == "medium":
                button.setChecked(True)
                break

        # 点击保存按钮
        settings_interface._save_settings()

        # 验证配置被保存
        mock_settings_deps["config"].set.assert_any_call("font_size", "medium")

    def test_save_output_directory(self, settings_interface, mock_settings_deps):
        """测试保存输出目录设置"""
        new_path = r"D:\NewOutput"
        settings_interface.output_dir_edit.setText(new_path)

        settings_interface._save_settings()

        mock_settings_deps["config"].set.assert_any_call("default_output_dir", new_path)

    def test_save_install_directory(self, settings_interface, mock_settings_deps):
        """测试保存安装目录设置"""
        new_path = r"D:\NewInstall"
        settings_interface.install_dir_edit.setText(new_path)

        settings_interface._save_settings()

        mock_settings_deps["config"].set.assert_any_call("default_install_dir", new_path)

    def test_save_ssh_settings(self, settings_interface, mock_settings_deps):
        """测试保存SSH设置"""
        settings_interface.ssh_host_edit.setText("192.168.2.200")
        settings_interface.ssh_user_edit.setText("admin")
        settings_interface.ssh_pass_edit.setText("newpassword")

        settings_interface._save_settings()

        mock_settings_deps["config"].set.assert_any_call("ssh_host", "192.168.2.200")
        mock_settings_deps["config"].set.assert_any_call("ssh_username", "admin")
        mock_settings_deps["config"].set.assert_any_call("ssh_password", "newpassword")

    def test_save_switch_settings(self, settings_interface, mock_settings_deps):
        """测试保存开关设置"""
        settings_interface.update_switch.setChecked(True)
        settings_interface.log_switch.setChecked(False)
        settings_interface.confirm_switch.setChecked(False)

        settings_interface._save_settings()

        mock_settings_deps["config"].set.assert_any_call("auto_check_update", True)
        mock_settings_deps["config"].set.assert_any_call("show_log_timestamp", False)
        mock_settings_deps["config"].set.assert_any_call("confirm_before_init", False)

    def test_save_shows_success_message(self, settings_interface, mock_settings_deps):
        """测试保存后显示成功消息"""
        settings_interface._save_settings()

        mock_settings_deps["infobar"].success.assert_called_once()

    def test_save_emits_config_changed_signal(self, settings_interface, qtbot):
        """测试保存后发射配置更改信号"""
        with qtbot.waitSignal(settings_interface.config_changed, timeout=1000):
            settings_interface._save_settings()

    def test_save_button_click(self, settings_interface, mock_settings_deps, qtbot):
        """测试点击保存按钮"""
        qtbot.mouseClick(settings_interface.save_btn, Qt.LeftButton)

        # 验证保存被调用
        assert mock_settings_deps["config"].set.called


# =============================================================================
# 重置默认设置测试
# =============================================================================

@pytest.mark.skipif(not PYQT5_AVAILABLE, reason="PyQt5 not available")
@pytest.mark.skipif(not SETTINGS_INTERFACE_AVAILABLE, reason=f"SettingsInterface not available")
class TestSettingsReset:
    """重置默认设置测试"""

    def test_reset_to_default_confirmed(self, settings_interface, mock_settings_deps):
        """测试确认重置为默认值"""
        # 模拟用户点击"是"
        mock_settings_deps["msgbox"].question.return_value = mock_settings_deps["msgbox"].Yes

        # 点击重置按钮
        settings_interface._reset_to_default()

        # 验证重置被调用
        mock_settings_deps["config"].reset_to_default.assert_called_once()

    def test_reset_cancelled(self, settings_interface, mock_settings_deps):
        """测试取消重置"""
        # 模拟用户点击"否"
        mock_settings_deps["msgbox"].question.return_value = mock_settings_deps["msgbox"].No

        # 点击重置按钮
        settings_interface._reset_to_default()

        # 验证重置未被调用
        mock_settings_deps["config"].reset_to_default.assert_not_called()

    def test_reset_shows_confirmation_dialog(self, settings_interface, mock_settings_deps):
        """测试重置显示确认对话框"""
        settings_interface._reset_to_default()

        # 验证确认对话框被显示
        mock_settings_deps["msgbox"].question.assert_called_once()
        call_args = mock_settings_deps["msgbox"].question.call_args
        assert "确认重置" in str(call_args)

    def test_reset_reloads_settings(self, settings_interface, mock_settings_deps):
        """测试重置后重新加载设置"""
        mock_settings_deps["msgbox"].question.return_value = mock_settings_deps["msgbox"].Yes

        # 修改一些设置
        settings_interface.ssh_host_edit.setText("modified_host")

        # 重置
        settings_interface._reset_to_default()

        # 验证重新加载被调用（通过检查get被调用）
        assert mock_settings_deps["config"].get.called


# =============================================================================
# 目录浏览测试
# =============================================================================

@pytest.mark.skipif(not PYQT5_AVAILABLE, reason="PyQt5 not available")
@pytest.mark.skipif(not SETTINGS_INTERFACE_AVAILABLE, reason=f"SettingsInterface not available")
class TestDirectoryBrowsing:
    """目录浏览测试"""

    def test_browse_output_directory(self, settings_interface, mock_settings_deps):
        """测试浏览输出目录"""
        new_dir = r"D:\SelectedOutput"
        mock_settings_deps["dialog"].getExistingDirectory.return_value = new_dir

        settings_interface._browse_output_dir()

        # 验证目录被设置
        assert settings_interface.output_dir_edit.text() == new_dir

    def test_browse_install_directory(self, settings_interface, mock_settings_deps):
        """测试浏览安装目录"""
        new_dir = r"D:\SelectedInstall"
        mock_settings_deps["dialog"].getExistingDirectory.return_value = new_dir

        settings_interface._browse_install_dir()

        # 验证目录被设置
        assert settings_interface.install_dir_edit.text() == new_dir

    def test_browse_cancelled(self, settings_interface, mock_settings_deps):
        """测试取消浏览"""
        original_path = settings_interface.output_dir_edit.text()
        mock_settings_deps["dialog"].getExistingDirectory.return_value = ""

        settings_interface._browse_output_dir()

        # 验证路径未改变
        assert settings_interface.output_dir_edit.text() == original_path


# =============================================================================
# 字体设置测试
# =============================================================================

@pytest.mark.skipif(not PYQT5_AVAILABLE, reason="PyQt5 not available")
@pytest.mark.skipif(not SETTINGS_INTERFACE_AVAILABLE, reason=f"SettingsInterface not available")
class TestFontSettings:
    """字体设置测试"""

    def test_font_radio_buttons_exist(self, settings_interface):
        """测试字体单选按钮存在"""
        buttons = settings_interface.font_button_group.buttons()
        assert len(buttons) == 3

        # 检查按钮标签
        labels = [btn.text() for btn in buttons]
        assert "小" in labels
        assert "中" in labels
        assert "大" in labels

    def test_font_size_change(self, settings_interface, mock_settings_deps):
        """测试字体大小更改"""
        # 选择"大"字体
        for button in settings_interface.font_button_group.buttons():
            if button.property("value") == "large":
                button.setChecked(True)
                break

        # 保存设置
        settings_interface._save_settings()

        # 验证配置被保存为large
        mock_settings_deps["config"].set.assert_any_call("font_size", "large")

    def test_font_change_shows_restart_hint(self, settings_interface, mock_settings_deps):
        """测试字体更改显示重启提示"""
        # 先保存一次当前字体
        settings_interface._save_settings()

        # 更改字体大小
        for button in settings_interface.font_button_group.buttons():
            if button.property("value") == "large":
                button.setChecked(True)
                break

        # 再次保存
        settings_interface._save_settings()

        # 验证成功消息被调用（包含重启提示）
        calls = mock_settings_deps["infobar"].success.call_args_list
        assert len(calls) >= 2  # 至少两次保存调用


# =============================================================================
# 信号测试
# =============================================================================

@pytest.mark.skipif(not PYQT5_AVAILABLE, reason="PyQt5 not available")
@pytest.mark.skipif(not SETTINGS_INTERFACE_AVAILABLE, reason=f"SettingsInterface not available")
class TestSettingsSignals:
    """设置界面信号测试"""

    def test_config_changed_signal(self, settings_interface, qtbot):
        """测试配置更改信号"""
        # 连接信号
        received = []
        settings_interface.config_changed.connect(lambda: received.append(1))

        # 保存设置
        settings_interface._save_settings()

        # 验证信号被发射
        assert len(received) == 1

    def test_font_size_changed_signal_exists(self, settings_interface):
        """测试字体大小更改信号存在"""
        assert hasattr(settings_interface, 'font_size_changed')


# =============================================================================
# Mock测试（无需真实GUI）
# =============================================================================

class TestSettingsInterfaceMocked:
    """使用Mock的设置界面测试"""

    def test_all_settings_saved(self, qapp):
        """测试所有设置项都被保存"""
        if settings_interface_module is None:
            pytest.skip("设置界面模块不可用")
        with patch.multiple(
            settings_interface_module,
            get_config_manager=MagicMock(),
            FontManager=MagicMock(),
            InfoBar=MagicMock(),
            QFileDialog=MagicMock(),
            QMessageBox=MagicMock(),
        ):
            from ui.interfaces.settings_interface import SettingsInterface

            default_config = {
                "font_size": "small",
                "default_output_dir": r"C:\Projects",
                "default_install_dir": r"C:\openEulerTools",
                "ssh_host": "",
                "ssh_username": "",
                "ssh_password": "",
                "auto_check_update": False,
                "show_log_timestamp": True,
                "confirm_before_init": True,
            }
            mock_config = MagicMock()
            mock_config.get = MagicMock(
                side_effect=lambda key, default=None: default_config.get(key, default)
            )
            mock_config.set = MagicMock(return_value=True)

            with patch("ui.interfaces.settings_interface.get_config_manager", return_value=mock_config):
                interface = SettingsInterface()

                # 设置各种值
                interface.output_dir_edit.setText(r"D:\Test")
                interface.install_dir_edit.setText(r"D:\Install")
                interface.ssh_host_edit.setText("192.168.1.1")
                interface.ssh_user_edit.setText("testuser")
                interface.ssh_pass_edit.setText("testpass")

                # 保存
                interface._save_settings()

                # 验证所有设置都被保存
                calls = mock_config.set.call_args_list
                keys_saved = [call[0][0] for call in calls]

                assert "default_output_dir" in keys_saved
                assert "default_install_dir" in keys_saved
                assert "ssh_host" in keys_saved
                assert "ssh_username" in keys_saved
                assert "ssh_password" in keys_saved
                interface.close()
                interface.deleteLater()


# =============================================================================
# 输入验证测试
# =============================================================================

@pytest.mark.skipif(not PYQT5_AVAILABLE, reason="PyQt5 not available")
@pytest.mark.skipif(not SETTINGS_INTERFACE_AVAILABLE, reason=f"SettingsInterface not available")
class TestSettingsInputValidation:
    """设置输入验证测试"""

    def test_ssh_host_input(self, settings_interface):
        """测试SSH主机输入"""
        # 测试有效IP地址
        settings_interface.ssh_host_edit.setText("192.168.1.100")
        assert settings_interface.ssh_host_edit.text() == "192.168.1.100"

        # 测试主机名
        settings_interface.ssh_host_edit.setText("example.com")
        assert settings_interface.ssh_host_edit.text() == "example.com"

    def test_empty_ssh_settings(self, settings_interface, mock_settings_deps):
        """测试空SSH设置"""
        settings_interface.ssh_host_edit.clear()
        settings_interface.ssh_user_edit.clear()
        settings_interface.ssh_pass_edit.clear()

        settings_interface._save_settings()

        # 验证空值也被保存
        mock_settings_deps["config"].set.assert_any_call("ssh_host", "")
        mock_settings_deps["config"].set.assert_any_call("ssh_username", "")
        mock_settings_deps["config"].set.assert_any_call("ssh_password", "")

    def test_long_path_input(self, settings_interface):
        """测试长路径输入"""
        long_path = "C:\/" + "a" * 200 + "\Projects"
        settings_interface.output_dir_edit.setText(long_path)
        assert settings_interface.output_dir_edit.text() == long_path
