"""
测试工具函数模块

提供环境检查、测试数据准备、等待/重试等辅助功能
"""

import os
import time
import socket
import hashlib
import tempfile
import yaml
from typing import Optional, Callable, Any, Dict, Tuple


def check_env_available(host: str, port: int, timeout: float = 2.0) -> bool:
    """
    检查测试环境是否可用

    Args:
        host: 目标主机地址
        port: 目标端口
        timeout: 连接超时时间（秒）

    Returns:
        True if 环境可用, False otherwise
    """
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


def get_test_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    读取测试环境配置

    Args:
        config_path: 配置文件路径，默认为 tests/config/test_env.yaml

    Returns:
        配置字典
    """
    if config_path is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(base_dir, "config", "test_env.yaml")

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        config = {}
    except Exception as e:
        print(f"Warning: 无法读取配置文件: {e}")
        config = {}

    # 从环境变量获取密码（覆盖配置文件）
    if config.get("ubuntu_vm"):
        if os.environ.get("UBUNTU_VM_PASSWORD"):
            config["ubuntu_vm"]["password"] = os.environ.get("UBUNTU_VM_PASSWORD")

    if config.get("real_device"):
        if os.environ.get("REAL_DEVICE_PASSWORD"):
            config["real_device"]["password"] = os.environ.get("REAL_DEVICE_PASSWORD")

    return config


def wait_for_condition(
    condition: Callable[[], bool],
    timeout: float = 30.0,
    interval: float = 0.5,
    description: str = "condition"
) -> Tuple[bool, float]:
    """
    等待条件满足

    Args:
        condition: 条件检查函数，返回True表示满足
        timeout: 最大等待时间（秒）
        interval: 检查间隔（秒）
        description: 条件描述（用于日志）

    Returns:
        (是否成功, 实际等待时间)
    """
    start_time = time.time()
    elapsed = 0.0

    while elapsed < timeout:
        if condition():
            return True, elapsed
        time.sleep(interval)
        elapsed = time.time() - start_time

    return False, elapsed


def retry_operation(
    operation: Callable[[], Any],
    max_retries: int = 3,
    delay: float = 1.0,
    exceptions: Tuple[type, ...] = (Exception,),
    description: str = "operation"
) -> Tuple[bool, Any]:
    """
    重试操作直到成功或达到最大重试次数

    Args:
        operation: 要执行的操作函数
        max_retries: 最大重试次数
        delay: 重试间隔（秒）
        exceptions: 需要捕获的异常类型
        description: 操作描述（用于日志）

    Returns:
        (是否成功, 操作结果或None)
    """
    last_exception = None

    for attempt in range(max_retries):
        try:
            result = operation()
            return True, result
        except exceptions as e:
            last_exception = e
            if attempt < max_retries - 1:
                time.sleep(delay)

    return False, last_exception


def generate_test_file(size: int = 1024, suffix: str = ".bin") -> str:
    """
    生成测试文件

    Args:
        size: 文件大小（字节）
        suffix: 文件后缀

    Returns:
        临时文件路径
    """
    fd, path = tempfile.mkstemp(suffix=suffix)
    try:
        # 生成随机内容
        chunk_size = 4096
        remaining = size

        with os.fdopen(fd, 'wb') as f:
            while remaining > 0:
                write_size = min(chunk_size, remaining)
                f.write(os.urandom(write_size))
                remaining -= write_size
    except Exception:
        os.close(fd)
        raise

    return path


def generate_test_text_file(content: str = None, suffix: str = ".txt") -> str:
    """
    生成文本测试文件

    Args:
        content: 文件内容，None则生成默认内容
        suffix: 文件后缀

    Returns:
        临时文件路径
    """
    if content is None:
        content = f"Test content generated at {time.time()}\nLine 2\nLine 3\n"

    fd, path = tempfile.mkstemp(suffix=suffix, text=True)
    with os.fdopen(fd, 'w') as f:
        f.write(content)

    return path


def calculate_file_hash(filepath: str, algorithm: str = "md5") -> str:
    """
    计算文件哈希值

    Args:
        filepath: 文件路径
        algorithm: 哈希算法 (md5, sha1, sha256)

    Returns:
        十六进制哈希字符串
    """
    hash_obj = hashlib.new(algorithm)

    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_obj.update(chunk)

    return hash_obj.hexdigest()


def ensure_test_directories(config: Dict[str, Any]) -> Dict[str, str]:
    """
    确保测试数据目录存在

    Args:
        config: 测试配置字典

    Returns:
        目录路径字典
    """
    test_data = config.get("test_data", {})
    dirs = {}

    for key in ["base_dir", "upload_dir", "download_dir", "temp_dir"]:
        path = test_data.get(key, f"tests/test_data/{key}")
        dirs[key] = path
        os.makedirs(path, exist_ok=True)

    return dirs


def cleanup_test_files(directory: str, pattern: str = "test_*") -> int:
    """
    清理测试文件

    Args:
        directory: 目标目录
        pattern: 文件匹配模式

    Returns:
        删除的文件数量
    """
    import glob

    count = 0
    search_path = os.path.join(directory, pattern)

    for filepath in glob.glob(search_path):
        try:
            if os.path.isfile(filepath):
                os.remove(filepath)
                count += 1
        except Exception:
            pass

    return count


def get_free_port(start_port: int = 10000, end_port: int = 65535) -> int:
    """
    获取可用端口

    Args:
        start_port: 起始端口
        end_port: 结束端口

    Returns:
        可用端口号
    """
    import random

    for _ in range(100):  # 最多尝试100次
        port = random.randint(start_port, end_port)
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('127.0.0.1', port))
            sock.close()
            return port
        except OSError:
            continue

    raise RuntimeError("无法找到可用端口")


def create_large_test_file(size_mb: int, output_dir: str = None) -> str:
    """
    创建大文件用于传输测试

    Args:
        size_mb: 文件大小（MB）
        output_dir: 输出目录，None则使用临时目录

    Returns:
        文件路径
    """
    if output_dir is None:
        output_dir = tempfile.gettempdir()

    filepath = os.path.join(output_dir, f"large_test_{size_mb}mb_{int(time.time())}.bin")

    chunk_size = 1024 * 1024  # 1MB
    chunks = size_mb

    with open(filepath, 'wb') as f:
        for _ in range(chunks):
            f.write(os.urandom(chunk_size))

    return filepath


class TestTimer:
    """测试计时器上下文管理器"""

    def __init__(self, description: str = "Operation"):
        self.description = description
        self.start_time = None
        self.elapsed = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed = time.time() - self.start_time
        status = "FAILED" if exc_type else "OK"
        print(f"[{status}] {self.description}: {self.elapsed:.3f}s")
        return False


class MockSSHClient:
    """
    模拟SSH客户端用于单元测试

    模拟SSHClient的行为，无需真实SSH连接
    """

    def __init__(self):
        self.connected = False
        self.host = None
        self.commands_executed = []
        self.files_uploaded = []
        self.files_downloaded = []

    def connect(self, host: str, port: int = 22, username: str = None,
                password: str = None, **kwargs) -> bool:
        """模拟连接"""
        self.host = host
        self.connected = True
        return True

    def disconnect(self):
        """模拟断开连接"""
        self.connected = False

    def execute(self, command: str) -> Tuple[str, str, int]:
        """模拟执行命令"""
        self.commands_executed.append(command)
        # 模拟一些基本命令
        if command.startswith("echo"):
            return command[5:].strip().strip("'\"") + "\n", "", 0
        elif command.startswith("ls"):
            return "file1\nfile2\n", "", 0
        elif command.startswith("md5sum"):
            return "d41d8cd98f00b204e9800998ecf8427e  file\n", "", 0
        else:
            return "", "", 0

    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """模拟上传文件"""
        self.files_uploaded.append((local_path, remote_path))
        return True

    def download_file(self, remote_path: str, local_path: str) -> bool:
        """模拟下载文件"""
        self.files_downloaded.append((remote_path, local_path))
        return True
