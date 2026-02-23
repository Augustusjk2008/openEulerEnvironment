"""
pytest全局配置和fixture定义文件

此文件定义了：
1. 自定义标记（ubuntu_vm, real_device等）
2. 全局fixture（qtbot, temp_config_dir等）
3. 测试环境初始化和清理

使用方式：
    这些fixture会自动被pytest发现，无需显式导入。
    在测试函数中直接使用fixture名称作为参数即可。

环境变量：
    UBUNTU_VM_AVAILABLE=1 - 启用需要Ubuntu虚拟机的测试
    REAL_DEVICE_TEST=1 - 启用需要真实目标板的测试
"""

import os
import sys
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

# 添加src目录到Python路径
# 确保测试可以导入src下的模块
PROJECT_ROOT = Path(__file__).parent.resolve()
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

# =============================================================================
# Mock外部依赖（必须在导入任何UI模块之前）
# =============================================================================

# Mock PyQt5 (必须在导入任何使用PyQt5的模块之前)
pyqt5_mock = MagicMock()
sys.modules['PyQt5'] = pyqt5_mock
sys.modules['PyQt5.QtWidgets'] = MagicMock()
sys.modules['PyQt5.QtCore'] = MagicMock()
sys.modules['PyQt5.QtGui'] = MagicMock()
sys.modules['PyQt5.QtTest'] = MagicMock()

# Mock sip (PyQt5依赖)
sys.modules['sip'] = MagicMock()

# Mock matplotlib的Qt后端
sys.modules['matplotlib'] = MagicMock()
sys.modules['matplotlib.backends'] = MagicMock()
sys.modules['matplotlib.backends.backend_qt5agg'] = MagicMock()
sys.modules['matplotlib.backends.backend_qtagg'] = MagicMock()
sys.modules['matplotlib.backends.qt_compat'] = MagicMock()
sys.modules['matplotlib.figure'] = MagicMock()
sys.modules['matplotlib.pyplot'] = MagicMock()

# Mock qfluentwidgets
qfluent_mock = MagicMock()
sys.modules['qfluentwidgets'] = qfluent_mock
sys.modules['qfluentwidgets.common'] = MagicMock()
sys.modules['qfluentwidgets.components'] = MagicMock()
sys.modules['qfluentwidgets.window'] = MagicMock()
sys.modules['qfluentwidgets.components.widgets'] = MagicMock()

# Mock FluentWindow 基类
class MockFluentWindow:
    pass
qfluent_mock.FluentWindow = MockFluentWindow
qfluent_mock.NavigationItemPosition = MagicMock()
qfluent_mock.FluentIcon = MagicMock()
qfluent_mock.Icon = MagicMock()
qfluent_mock.Theme = MagicMock()
qfluent_mock.setTheme = MagicMock()
qfluent_mock.InfoBar = MagicMock()
qfluent_mock.InfoBarPosition = MagicMock()
qfluent_mock.PushButton = MagicMock()
qfluent_mock.PrimaryPushButton = MagicMock()
qfluent_mock.ComboBox = MagicMock()
qfluent_mock.LineEdit = MagicMock()
qfluent_mock.TextEdit = MagicMock()
qfluent_mock.PlainTextEdit = MagicMock()
qfluent_mock.TableWidget = MagicMock()
qfluent_mock.ListWidget = MagicMock()
qfluent_mock.TreeWidget = MagicMock()
qfluent_mock.SwitchButton = MagicMock()
qfluent_mock.Slider = MagicMock()
qfluent_mock.SpinBox = MagicMock()
qfluent_mock.DoubleSpinBox = MagicMock()
qfluent_mock.CardWidget = MagicMock()
qfluent_mock.SimpleCardWidget = MagicMock()
qfluent_mock.GroupHeaderCardWidget = MagicMock()
qfluent_mock.ExpandGroupSettingCard = MagicMock()
qfluent_mock.SettingCardGroup = MagicMock()
qfluent_mock.OptionsSettingCard = MagicMock()
qfluent_mock.PushSettingCard = MagicMock()
qfluent_mock.SingleDirectionScrollArea = MagicMock()
qfluent_mock.SmoothScrollArea = MagicMock()
qfluent_mock.PillPushButton = MagicMock()
qfluent_mock.FluentIconBase = MagicMock()
qfluent_mock.SubtitleLabel = MagicMock()
qfluent_mock.BodyLabel = MagicMock()
qfluent_mock.CaptionLabel = MagicMock()
qfluent_mock.TitleLabel = MagicMock()
qfluent_mock.StrongBodyLabel = MagicMock()
qfluent_mock.ToolTipFilter = MagicMock()
qfluent_mock.ToolTipPosition = MagicMock()
qfluent_mock.HyperlinkButton = MagicMock()
qfluent_mock.ToolButton = MagicMock()
qfluent_mock.PrimaryToolButton = MagicMock()
qfluent_mock.DropDownPushButton = MagicMock()
qfluent_mock.DropDownToolButton = MagicMock()
qfluent_mock.RoundMenu = MagicMock()
qfluent_mock.Action = MagicMock()
qfluent_mock.MenuAnimationType = MagicMock()
qfluent_mock.MessageBoxBase = MagicMock()
qfluent_mock.Dialog = MagicMock()
qfluent_mock.Flyout = MagicMock()
qfluent_mock.FlyoutAnimationType = MagicMock()
qfluent_mock.ToggleButton = MagicMock()
qfluent_mock.IndeterminateProgressBar = MagicMock()
qfluent_mock.ProgressBar = MagicMock()
qfluent_mock.StateTooltip = MagicMock()
qfluent_mock.ScrollArea = MagicMock()
qfluent_mock.ScrollBar = MagicMock()
qfluent_mock.ComboBoxSettingCard = MagicMock()
qfluent_mock.SpinBoxSettingCard = MagicMock()
qfluent_mock.LineEditSettingCard = MagicMock()
qfluent_mock.SwitchSettingCard = MagicMock()
qfluent_mock.CustomColorSettingCard = MagicMock()
qfluent_mock.setCustomStyleSheet = MagicMock()
qfluent_mock.isDarkTheme = MagicMock(return_value=False)
qfluent_mock.ThemeColor = MagicMock()

# Mock pyte (终端模拟)
sys.modules['pyte'] = MagicMock()
sys.modules['pyte.screens'] = MagicMock()
sys.modules['pyte.streams'] = MagicMock()
sys.modules['pyte.charsets'] = MagicMock()
sys.modules['pyte.control'] = MagicMock()
sys.modules['pyte.escape'] = MagicMock()
sys.modules['pyte.graphics'] = MagicMock()

# Mock其他可能的依赖
sys.modules['qrcode'] = MagicMock()
sys.modules['PIL'] = MagicMock()
sys.modules['PIL.Image'] = MagicMock()
sys.modules['PIL.ImageDraw'] = MagicMock()
sys.modules['PIL.ImageFont'] = MagicMock()

import pytest


# =============================================================================
# 自定义标记定义
# =============================================================================

def pytest_configure(config):
    """
    配置pytest，注册自定义标记

    在pytest收集测试之前调用，用于注册自定义标记。
    """
    # 注册Ubuntu VM标记
    config.addinivalue_line(
        "markers",
        "ubuntu_vm: marks tests that require an Ubuntu VM "
        "(skipped unless UBUNTU_VM_AVAILABLE=1)"
    )
    # 注册真实设备标记
    config.addinivalue_line(
        "markers",
        "real_device: marks tests that require a real target device "
        "(skipped unless REAL_DEVICE_TEST=1)"
    )
    # 注册慢速测试标记
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    # 注册GUI标记
    config.addinivalue_line(
        "markers",
        "gui: marks tests that require GUI"
    )


def pytest_collection_modifyitems(config, items):
    """
    修改测试收集行为

    根据环境变量自动跳过标记的测试：
    - 如果没有UBUNTU_VM_AVAILABLE=1，跳过@ubuntu_vm标记的测试
    - 如果没有REAL_DEVICE_TEST=1，跳过@real_device标记的测试
    """
    # 检查环境变量
    ubuntu_vm_available = os.environ.get("UBUNTU_VM_AVAILABLE", "") == "1"
    real_device_available = os.environ.get("REAL_DEVICE_TEST", "") == "1"

    for item in items:
        # 处理ubuntu_vm标记
        if "ubuntu_vm" in item.keywords and not ubuntu_vm_available:
            item.add_marker(
                pytest.mark.skip(
                    reason="需要Ubuntu虚拟机 (设置 UBUNTU_VM_AVAILABLE=1 启用)"
                )
            )

        # 处理real_device标记
        if "real_device" in item.keywords and not real_device_available:
            item.add_marker(
                pytest.mark.skip(
                    reason="需要真实目标板 (设置 REAL_DEVICE_TEST=1 启用)"
                )
            )


# =============================================================================
# Session级Fixture
# =============================================================================

@pytest.fixture(scope="session")
def project_root():
    """
    提供项目根目录路径

    Returns:
        Path: 项目根目录的Path对象

    Example:
        def test_something(project_root):
            config_path = project_root / "config" / "default.json"
    """
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def src_path():
    """
    提供src目录路径

    Returns:
        Path: src目录的Path对象
    """
    return SRC_PATH


@pytest.fixture(scope="session")
def test_dir():
    """
    提供tests目录路径

    Returns:
        Path: tests目录的Path对象
    """
    return Path(__file__).parent


@pytest.fixture(scope="session")
def ubuntu_vm_config():
    """
    提供Ubuntu虚拟机配置

    环境变量UBUNTU_VM_AVAILABLE=1时可用

    Returns:
        dict: 包含VM连接信息的字典，如果未启用则返回None

    Example:
        @pytest.mark.ubuntu_vm
        def test_ssh_connection(ubuntu_vm_config):
            ssh = SSHClient()
            ssh.connect(ubuntu_vm_config['host'], ...)
    """
    if os.environ.get("UBUNTU_VM_AVAILABLE") != "1":
        return None

    return {
        "host": "192.168.56.132",
        "port": 22,
        "username": os.environ.get("UBUNTU_VM_USER", "openeuler"),
        "password": os.environ.get("UBUNTU_VM_PASS", "openeuler"),
    }


@pytest.fixture(scope="session")
def real_device_config():
    """
    提供真实目标板配置

    环境变量REAL_DEVICE_TEST=1时可用

    Returns:
        dict: 包含设备连接信息的字典，如果未启用则返回None

    Example:
        @pytest.mark.real_device
        def test_device_init(real_device_config):
            ssh = SSHClient()
            ssh.connect(real_device_config['host'], ...)
    """
    if os.environ.get("REAL_DEVICE_TEST") != "1":
        return None

    return {
        "host": "192.168.1.29",
        "port": 22,
        "username": os.environ.get("DEVICE_USER", "root"),
        "password": os.environ.get("DEVICE_PASS", ""),
    }


# =============================================================================
# Qt相关Fixture
# =============================================================================

@pytest.fixture(scope="function")
def qt_app(qapp):
    """
    提供QApplication实例

    这是pytest-qt插件qapp fixture的包装，确保QApplication可用。

    Args:
        qapp: pytest-qt提供的QApplication fixture

    Returns:
        QApplication: Qt应用程序实例

    Example:
        def test_window(qt_app):
            window = MainWindow()
            window.show()
    """
    return qapp


@pytest.fixture(scope="function")
def qt_bot(qtbot):
    """
    提供QtBot实例用于GUI测试

    这是pytest-qt插件qtbot fixture的包装，提供更方便的接口。

    Args:
        qtbot: pytest-qt提供的QtBot fixture

    Returns:
        QtBot: Qt测试机器人实例

    Example:
        def test_button_click(qt_bot):
            button = QPushButton("Click me")
            qt_bot.addWidget(button)
            qt_bot.mouseClick(button, Qt.LeftButton)
    """
    return qtbot


@pytest.fixture(scope="function")
def mock_qt_messagebox(monkeypatch):
    """
    模拟QMessageBox，避免测试时弹出对话框

    Returns:
        MagicMock: 配置好的QMessageBox模拟对象

    Example:
        def test_error_handling(mock_qt_messagebox):
            # 当代码调用QMessageBox.critical时，不会弹出对话框
            show_error("test error")
            mock_qt_messagebox.critical.assert_called_once()
    """
    mock_msgbox = MagicMock()
    mock_msgbox.Question = 4
    mock_msgbox.Yes = 16384
    mock_msgbox.No = 65536
    mock_msgbox.Ok = 1024
    mock_msgbox.Cancel = 4194304

    monkeypatch.setattr(
        "PyQt5.QtWidgets.QMessageBox",
        mock_msgbox
    )
    return mock_msgbox


@pytest.fixture(scope="function")
def mock_qt_filedialog(monkeypatch):
    """
    模拟QFileDialog，避免测试时弹出文件对话框

    Returns:
        MagicMock: 配置好的QFileDialog模拟对象

    Example:
        def test_file_open(mock_qt_filedialog):
            mock_qt_filedialog.getOpenFileName.return_value = ("/path/to/file", "")
            result = open_file_dialog()
            assert result == "/path/to/file"
    """
    mock_dialog = MagicMock()
    mock_dialog.getOpenFileName.return_value = ("", "")
    mock_dialog.getSaveFileName.return_value = ("", "")
    mock_dialog.getExistingDirectory.return_value = ""

    monkeypatch.setattr(
        "PyQt5.QtWidgets.QFileDialog",
        mock_dialog
    )
    return mock_dialog


# =============================================================================
# 配置和临时目录Fixture
# =============================================================================

@pytest.fixture(scope="function")
def temp_config_dir(tmp_path):
    """
    提供临时配置目录

    每个测试函数获得独立的临时目录，测试结束后自动清理。

    Args:
        tmp_path: pytest提供的临时路径fixture

    Returns:
        Path: 临时配置目录的Path对象

    Example:
        def test_config_save(temp_config_dir):
            config = ConfigManager(config_dir=temp_config_dir)
            config.save()
            assert (temp_config_dir / "config.json").exists()
    """
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True)
    return config_dir


@pytest.fixture(scope="function")
def temp_project_dir(tmp_path):
    """
    提供临时项目目录

    模拟一个完整的项目结构，用于测试项目相关功能。

    Args:
        tmp_path: pytest提供的临时路径fixture

    Returns:
        Path: 临时项目目录的Path对象
    """
    project_dir = tmp_path / "project"
    project_dir.mkdir(parents=True)

    # 创建标准项目子目录
    (project_dir / "src").mkdir()
    (project_dir / "include").mkdir()
    (project_dir / "config").mkdir()
    (project_dir / "build").mkdir()

    return project_dir


@pytest.fixture(scope="function")
def mock_settings(monkeypatch, temp_config_dir):
    """
    提供模拟的QSettings

    使用临时目录存储设置，避免污染用户真实配置。

    Args:
        monkeypatch: pytest monkeypatch fixture
        temp_config_dir: 临时配置目录fixture

    Returns:
        Path: 设置文件路径

    Example:
        def test_settings_save(mock_settings):
            settings = QSettings()
            settings.setValue("key", "value")
            # 设置保存在临时目录中
    """
    settings_file = temp_config_dir / "settings.ini"

    # 模拟QSettings使用临时文件
    original_init = None
    try:
        from PyQt5.QtCore import QSettings

        def mock_init(self, *args, **kwargs):
            # 强制使用IniFormat和临时文件路径
            super(QSettings, self).__init__(
                str(settings_file),
                QSettings.IniFormat
            )

        original_init = QSettings.__init__
        monkeypatch.setattr(QSettings, "__init__", mock_init)
    except ImportError:
        # 如果PyQt5未安装，创建一个模拟对象
        pass

    yield settings_file

    # 清理：恢复原始初始化方法
    if original_init:
        monkeypatch.setattr(QSettings, "__init__", original_init)


# =============================================================================
# 网络和SSH相关Fixture
# =============================================================================

@pytest.fixture(scope="function")
def mock_ssh_client(monkeypatch):
    """
    提供模拟的SSH客户端

    用于测试SSH相关功能，无需真实SSH连接。

    Returns:
        MagicMock: 配置好的SSH客户端模拟对象

    Example:
        def test_ssh_command(mock_ssh_client):
            mock_ssh_client.exec_command.return_value = (None, "output", "")
            result = run_remote_command("ls")
            assert result == "output"
    """
    mock_client = MagicMock()
    mock_transport = MagicMock()
    mock_sftp = MagicMock()

    mock_client.get_transport.return_value = mock_transport
    mock_client.open_sftp.return_value = mock_sftp
    mock_client.exec_command.return_value = (
        MagicMock(),  # stdin
        MagicMock(),  # stdout
        MagicMock(),  # stderr
    )

    # 模拟paramiko.SSHClient
    try:
        import paramiko
        monkeypatch.setattr(paramiko, "SSHClient", lambda: mock_client)
        monkeypatch.setattr(paramiko, "Transport", lambda *args, **kwargs: mock_transport)
    except ImportError:
        # 如果paramiko未安装，只返回mock对象
        pass

    return mock_client


@pytest.fixture(scope="function")
def mock_ftp_client(monkeypatch):
    """
    提供模拟的FTP客户端

    用于测试FTP相关功能，无需真实FTP连接。

    Returns:
        MagicMock: 配置好的FTP客户端模拟对象

    Example:
        def test_ftp_upload(mock_ftp_client):
            mock_ftp_client.storbinary.return_value = "226 Transfer complete"
            upload_file("/local/path", "/remote/path")
            mock_ftp_client.storbinary.assert_called_once()
    """
    mock_ftp = MagicMock()
    mock_ftp.login.return_value = "230 Login successful"
    mock_ftp.cwd.return_value = "250 Directory changed"
    mock_ftp.storbinary.return_value = "226 Transfer complete"
    mock_ftp.retrbinary.return_value = "226 Transfer complete"

    try:
        from ftplib import FTP
        monkeypatch.setattr("ftplib.FTP", lambda *args, **kwargs: mock_ftp)
    except ImportError:
        pass

    return mock_ftp


# =============================================================================
# 工具函数Fixture
# =============================================================================

@pytest.fixture(scope="function")
def sample_cpp_code():
    """
    提供示例C++代码

    Returns:
        str: 示例C++代码字符串

    Example:
        def test_cpp_parser(sample_cpp_code):
            result = parse_cpp(sample_cpp_code)
            assert "class" in result
    """
    return """
#include <iostream>
#include <string>

class TestClass {
public:
    TestClass() {}
    ~TestClass() {}

    void sayHello() {
        std::cout << "Hello, World!" << std::endl;
    }

private:
    int value_;
    std::string name_;
};

int main() {
    TestClass obj;
    obj.sayHello();
    return 0;
}
"""


@pytest.fixture(scope="function")
def sample_protocol_def():
    """
    提供示例协议定义

    Returns:
        dict: 示例协议定义字典

    Example:
        def test_protocol_parser(sample_protocol_def):
            result = parse_protocol(sample_protocol_def)
            assert result["name"] == "TestProtocol"
    """
    return {
        "name": "TestProtocol",
        "version": "1.0",
        "fields": [
            {"name": "header", "type": "uint8", "size": 1},
            {"name": "length", "type": "uint16", "size": 2},
            {"name": "payload", "type": "bytes", "size": "variable"},
            {"name": "checksum", "type": "uint32", "size": 4},
        ],
        "endian": "little",
    }


# =============================================================================
# 测试生命周期钩子
# =============================================================================

def pytest_runtest_setup(item):
    """
    每个测试运行前的设置

    可以在这里添加测试前的准备工作。
    """
    pass


def pytest_runtest_teardown(item, nextitem):
    """
    每个测试运行后的清理

    可以在这里添加测试后的清理工作。
    """
    pass


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """
    测试会话级别的环境设置

    在所有测试开始前执行一次，在所有测试结束后清理。
    """
    # 设置阶段
    # 创建报告目录
    reports_dir = PROJECT_ROOT / "tests" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    # 设置环境变量
    original_env = dict(os.environ)
    os.environ["QT_QPA_PLATFORM"] = "offscreen"

    yield

    # 清理阶段
    # 恢复原始环境变量
    os.environ.clear()
    os.environ.update(original_env)
