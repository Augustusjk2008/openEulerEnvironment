"""
集成测试配置和 fixture。
"""

import os
import socket
import subprocess

import pytest


def _vm_settings():
    host = os.environ.get("UBUNTU_VM_HOST", "").strip()
    username = os.environ.get("UBUNTU_VM_USER", "").strip()
    key_filename = os.environ.get("UBUNTU_VM_KEY", os.path.expanduser("~/.ssh/id_rsa"))
    test_dir = os.environ.get("UBUNTU_VM_TEST_DIR", "").strip()
    if not test_dir and username:
        test_dir = f"/home/{username}/sftp_test"

    return {
        "host": host,
        "port": 22,
        "username": username,
        "password": None,
        "key_filename": key_filename,
        "test_dir": test_dir,
    }


def _is_vm_available():
    config = _vm_settings()
    host = config["host"]
    username = config["username"]
    if not host or not username:
        return False

    try:
        result = subprocess.run(
            ["ssh", "-o", "PasswordAuthentication=no", "-o", "ConnectTimeout=2", f"{username}@{host}", "echo ok"],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except Exception:
        return False


@pytest.fixture(scope="session")
def vm_config():
    """提供 VM 测试配置。"""
    config = _vm_settings()
    if _is_vm_available():
        os.environ["UBUNTU_VM_AVAILABLE"] = "1"
    return config


@pytest.fixture(scope="session")
def vm_available():
    """检查 VM 是否可用。"""
    config = _vm_settings()
    host = config["host"]
    port = config["port"]
    timeout = 2.0

    if not host:
        return False

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


_VM_AVAILABLE = _is_vm_available()
if _VM_AVAILABLE:
    os.environ["UBUNTU_VM_AVAILABLE"] = "1"

ubuntu_vm = pytest.mark.skipif(
    not _VM_AVAILABLE,
    reason="需要通过 UBUNTU_VM_HOST 和 UBUNTU_VM_USER 提供可访问的 Ubuntu VM",
)
