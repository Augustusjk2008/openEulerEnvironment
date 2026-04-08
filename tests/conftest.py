"""
pytest全局配置和fixture定义文件

此文件定义了：
1. 自定义标记（ubuntu_vm, real_device等）
2. 全局fixture（qtbot, temp_config_dir等）
3. 测试环境初始化和清理
"""

import os
import sys
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# 添加src目录到Python路径
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

try:
    import pytestqt  # noqa: F401
except ImportError:
    PYTEST_QT_AVAILABLE = False
else:
    PYTEST_QT_AVAILABLE = True


def pytest_configure(config):
    """配置pytest，注册自定义标记"""
    config.addinivalue_line(
        "markers",
        "ubuntu_vm: marks tests that require an Ubuntu VM"
    )
    config.addinivalue_line(
        "markers",
        "real_device: marks tests that require a real target device"
    )
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow"
    )
    config.addinivalue_line(
        "markers",
        "gui: marks tests that require GUI"
    )


def pytest_collection_modifyitems(config, items):
    """根据环境变量自动跳过标记的测试"""
    ubuntu_vm_available = os.environ.get("UBUNTU_VM_AVAILABLE", "") == "1"
    real_device_available = os.environ.get("REAL_DEVICE_TEST", "") == "1"

    for item in items:
        if "ubuntu_vm" in item.keywords and not ubuntu_vm_available:
            item.add_marker(pytest.mark.skip(reason="需要Ubuntu虚拟机"))
        if "real_device" in item.keywords and not real_device_available:
            item.add_marker(pytest.mark.skip(reason="需要真实目标板"))


@pytest.fixture(scope="session")
def project_root():
    """提供项目根目录路径"""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def src_path():
    """提供src目录路径"""
    return SRC_PATH


@pytest.fixture(scope="session")
def test_dir():
    """提供tests目录路径"""
    return Path(__file__).parent


if not PYTEST_QT_AVAILABLE:
    @pytest.fixture(scope="session")
    def qapp():
        """提供QApplication实例fallback。"""
        return MagicMock()


    @pytest.fixture(scope="function")
    def qtbot(qapp):
        """提供QtBot实例fallback，当pytest-qt不可用时使用。"""
        return MagicMock()


@pytest.fixture(scope="function")
def temp_config_dir(tmp_path):
    """提供临时配置目录"""
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True)
    return config_dir


@pytest.fixture(scope="function")
def mock_ssh_client(monkeypatch):
    """提供模拟的SSH客户端"""
    mock_client = MagicMock()
    try:
        import paramiko
        monkeypatch.setattr(paramiko, "SSHClient", lambda: mock_client)
    except ImportError:
        pass
    return mock_client


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """测试会话级别的环境设置"""
    reports_dir = PROJECT_ROOT / "tests" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    original_env = dict(os.environ)
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    
    yield
    
    os.environ.clear()
    os.environ.update(original_env)
