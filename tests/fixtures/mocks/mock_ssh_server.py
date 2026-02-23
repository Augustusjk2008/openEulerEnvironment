"""
Mock SSH服务器和客户端
用于测试SSH相关功能而不依赖真实网络
"""

from typing import Dict, Any, List, Optional, Tuple, Callable
from unittest.mock import MagicMock
import paramiko


class MockSSHClient:
    """Mock SSH客户端"""

    def __init__(self, should_fail_connect: bool = False, auth_failure: bool = False):
        self.should_fail_connect = should_fail_connect
        self.auth_failure = auth_failure
        self.connected = False
        self.host_key_policy = None
        self.system_host_keys_loaded = False
        self.commands_executed: List[Tuple[str, Dict[str, Any]]] = []
        self.sftp_sessions: List['MockSFTPClient'] = []
        self.closed = False
        self.connect_kwargs: Optional[Dict[str, Any]] = None

    def load_system_host_keys(self):
        """Mock加载系统主机密钥"""
        self.system_host_keys_loaded = True

    def set_missing_host_key_policy(self, policy):
        """Mock设置缺失主机密钥策略"""
        self.host_key_policy = policy

    def connect(self, **kwargs):
        """Mock连接"""
        if self.auth_failure:
            raise paramiko.AuthenticationException("Authentication failed")
        if self.should_fail_connect:
            raise paramiko.SSHException("Connection failed")
        self.connect_kwargs = kwargs
        self.connected = True

    def exec_command(self, command: str) -> Tuple[Any, 'MockChannel', 'MockChannel']:
        """Mock执行命令"""
        if not self.connected:
            raise paramiko.SSHException("Not connected")
        self.commands_executed.append((command, {}))
        stdin = MagicMock()
        stdout = MockChannel()
        stderr = MockChannel()
        return stdin, stdout, stderr

    def open_sftp(self) -> 'MockSFTPClient':
        """Mock打开SFTP会话"""
        if not self.connected:
            raise paramiko.SSHException("Not connected")
        sftp = MockSFTPClient()
        self.sftp_sessions.append(sftp)
        return sftp

    def close(self):
        """Mock关闭连接"""
        self.connected = False
        self.closed = True


class MockChannel:
    """Mock SSH通道"""

    def __init__(self, output: bytes = b"", error: bytes = b"", exit_status: int = 0):
        self._output = output
        self._error = error
        self._exit_status = exit_status
        self._read_pos = 0

    def read(self) -> bytes:
        """Mock读取数据"""
        result = self._output[self._read_pos:]
        self._read_pos = len(self._output)
        return result

    @property
    def channel(self) -> 'MockChannel':
        """Mock通道属性"""
        return self

    def recv_exit_status(self) -> int:
        """Mock接收退出状态"""
        return self._exit_status


class MockSFTPClient:
    """Mock SFTP客户端"""

    def __init__(self, should_fail_stat=False, should_fail_close=False):
        self.files: Dict[str, bytes] = {}
        self.dirs: Dict[str, Dict[str, Any]] = {}
        self.closed = False
        self.uploaded_files: List[Tuple[str, str]] = []
        self.downloaded_files: List[Tuple[str, str]] = []
        self.removed_files: List[str] = []
        self.created_dirs: List[str] = []
        self.should_fail_stat = should_fail_stat
        self.should_fail_close = should_fail_close
        self._listdir_entries: Dict[str, List['MockSFTPAttributes']] = {}

    def put(self, local_path: str, remote_path: str):
        """Mock上传文件"""
        self.uploaded_files.append((local_path, remote_path))
        self.files[remote_path] = b"mock file content"

    def get(self, remote_path: str, local_path: str):
        """Mock下载文件"""
        self.downloaded_files.append((remote_path, local_path))
        if remote_path not in self.files:
            raise IOError(f"File not found: {remote_path}")

    def stat(self, path: str) -> 'MockSFTPAttributes':
        """Mock获取文件状态"""
        if self.should_fail_stat:
            raise IOError(f"Stat failed for: {path}")
        if path in self.files:
            return MockSFTPAttributes(is_dir=False)
        if path in self.dirs:
            return MockSFTPAttributes(is_dir=True)
        raise IOError(f"File not found: {path}")

    def mkdir(self, path: str):
        """Mock创建目录"""
        self.created_dirs.append(path)
        self.dirs[path] = {}

    def rmdir(self, path: str):
        """Mock删除目录"""
        if path in self.dirs:
            del self.dirs[path]

    def remove(self, path: str):
        """Mock删除文件"""
        self.removed_files.append(path)
        if path in self.files:
            del self.files[path]

    def listdir_attr(self, path: str) -> List['MockSFTPAttributes']:
        """Mock列出目录属性"""
        return self._listdir_entries.get(path, [])

    def add_listdir_entry(self, path: str, entry: 'MockSFTPAttributes'):
        """添加目录列表项用于测试"""
        if path not in self._listdir_entries:
            self._listdir_entries[path] = []
        self._listdir_entries[path].append(entry)

    def close(self):
        """Mock关闭SFTP会话"""
        if self.should_fail_close:
            raise Exception("Close failed")
        self.closed = True


class MockSFTPAttributes:
    """Mock SFTP属性"""

    def __init__(self, is_dir: bool = False, filename: str = "", st_mode: int = 0):
        self.is_dir = is_dir
        self.filename = filename
        if st_mode:
            self.st_mode = st_mode
        else:
            import stat as stat_module
            self.st_mode = stat_module.S_IFDIR | 0o755 if is_dir else stat_module.S_IFREG | 0o644


def create_mock_ssh_client(**kwargs) -> MockSSHClient:
    """
    创建Mock SSH客户端的工厂函数

    Args:
        **kwargs: 传递给MockSSHClient的参数

    Returns:
        MockSSHClient实例
    """
    return MockSSHClient(**kwargs)


def create_mock_sftp_client() -> MockSFTPClient:
    """
    创建Mock SFTP客户端的工厂函数

    Returns:
        MockSFTPClient实例
    """
    return MockSFTPClient()


def mock_paramiko_for_testing(monkeypatch, client: Optional[MockSSHClient] = None):
    """
    使用monkeypatch模拟paramiko.SSHClient

    Args:
        monkeypatch: pytest的monkeypatch fixture
        client: 可选的MockSSHClient实例，默认为None（自动创建）

    Returns:
        MockSSHClient实例
    """
    mock_client = client or MockSSHClient()

    def mock_ssh_client_constructor(*args, **kwargs):
        return mock_client

    monkeypatch.setattr(paramiko, "SSHClient", mock_ssh_client_constructor)
    return mock_client
