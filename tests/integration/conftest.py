"""
集成测试配置和fixture

此模块提供集成测试所需的配置和fixture，包括：
- VM配置fixture
- ubuntu_vm标记用于控制测试执行
"""

import pytest
import os


@pytest.fixture(scope="session")
def vm_config():
    """
    提供VM测试配置

    Returns:
        dict: 包含VM连接信息的字典

    Example:
        def test_ssh_connection(vm_config):
            ssh = SSHClient()
            ssh.connect(
                host=vm_config["host"],
                port=vm_config["port"],
                username=vm_config["username"],
                password=vm_config["password"]
            )
    """
    # 自动检测VM是否可用，如果可用则自动启用测试
    import subprocess
    try:
        result = subprocess.run(
            ["ssh", "-o", "PasswordAuthentication=no", "-o", "ConnectTimeout=2",
             "jiangkai@192.168.56.132", "echo ok"],
            capture_output=True,
            timeout=5
        )
        vm_reachable = result.returncode == 0
    except:
        vm_reachable = False

    # 如果VM可达，自动设置环境变量
    if vm_reachable:
        os.environ["UBUNTU_VM_AVAILABLE"] = "1"

    return {
        "host": "192.168.56.132",
        "port": 22,
        "username": "jiangkai",
        "password": None,  # 使用SSH密钥，不需要密码
        "key_filename": os.path.expanduser("~/.ssh/id_rsa"),
        "test_dir": "/home/jiangkai/sftp_test",
    }


@pytest.fixture(scope="session")
def vm_available():
    """
    检查VM是否可用

    Returns:
        bool: VM是否可连接
    """
    import socket

    host = "192.168.56.132"
    port = 22
    timeout = 2.0

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


# 检测VM是否可用
def _is_vm_available():
    """检测VM是否可用"""
    import subprocess
    try:
        result = subprocess.run(
            ["ssh", "-o", "PasswordAuthentication=no", "-o", "ConnectTimeout=2",
             "jiangkai@192.168.56.132", "echo ok"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except:
        return False

# 标记需要VM的测试
# 自动检测VM是否可用，如果可用则自动启用测试
_VM_AVAILABLE = _is_vm_available()
if _VM_AVAILABLE:
    os.environ["UBUNTU_VM_AVAILABLE"] = "1"

ubuntu_vm = pytest.mark.skipif(
    not _VM_AVAILABLE,
    reason="需要Ubuntu虚拟机192.168.56.132（请确保SSH免密登录已配置）"
)
