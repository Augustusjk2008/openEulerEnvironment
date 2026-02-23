"""
SSH工具模块单元测试
测试SSH配置、工厂方法和连接功能（使用Mock，不依赖真实网络）
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import paramiko

# 确保src和tests在路径中（用于直接运行测试文件）
_project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_project_root / "src"))
sys.path.insert(0, str(_project_root))

from core.ssh_utils import (
    SSHConfig,
    SSHClientFactory,
    SSHConnectionContext,
    BaseSSHWorker,
    SSHConnectWorker,
    SFTPTransferWorker,
    SSHCommandWorker,
)

from tests.fixtures.mocks.mock_config import MockConfigManager
from tests.fixtures.mocks.mock_ssh_server import MockSSHClient, MockSFTPClient, MockSFTPAttributes, mock_paramiko_for_testing


class TestSSHConfig:
    """测试SSH配置类"""

    def test_from_config_manager_ssh_prefix(self):
        """测试从配置管理器读取SSH配置"""
        config_manager = MockConfigManager({
            "ssh_host": "192.168.1.100",
            "ssh_username": "testuser",
            "ssh_password": "testpass",
        })

        config = SSHConfig.from_config_manager(config_manager, prefix="ssh")

        assert config["host"] == "192.168.1.100"
        assert config["username"] == "testuser"
        assert config["password"] == "testpass"

    def test_from_config_manager_ftp_prefix(self):
        """测试从配置管理器读取FTP配置"""
        config_manager = MockConfigManager({
            "ftp_host": "ftp.example.com",
            "ftp_username": "ftpuser",
            "ftp_password": "ftppass",
        })

        config = SSHConfig.from_config_manager(config_manager, prefix="ftp")

        assert config["host"] == "ftp.example.com"
        assert config["username"] == "ftpuser"
        assert config["password"] == "ftppass"

    def test_from_config_manager_default_values(self):
        """测试从配置管理器读取默认值"""
        config_manager = MockConfigManager({})

        config = SSHConfig.from_config_manager(config_manager, prefix="ssh")

        assert config["host"] == ""
        assert config["username"] == ""
        assert config["password"] == ""

    def test_from_config_manager_partial_config(self):
        """测试从配置管理器读取部分配置"""
        config_manager = MockConfigManager({
            "ssh_host": "192.168.1.1",
            "ssh_password": "secret",
        })

        config = SSHConfig.from_config_manager(config_manager, prefix="ssh")

        assert config["host"] == "192.168.1.1"
        assert config["username"] == ""
        assert config["password"] == "secret"

    def test_validate_valid_config(self):
        """测试验证有效配置"""
        config = {
            "host": "192.168.1.100",
            "username": "user",
            "password": "pass",
        }

        is_valid, error = SSHConfig.validate(config)

        assert is_valid is True
        assert error == ""

    def test_validate_missing_host(self):
        """测试验证缺少主机地址"""
        config = {
            "host": "",
            "username": "user",
            "password": "pass",
        }

        is_valid, error = SSHConfig.validate(config)

        assert is_valid is False
        assert "主机地址不能为空" in error

    def test_validate_missing_username(self):
        """测试验证缺少用户名"""
        config = {
            "host": "192.168.1.100",
            "username": "",
            "password": "pass",
        }

        is_valid, error = SSHConfig.validate(config)

        assert is_valid is False
        assert "用户名不能为空" in error

    def test_validate_missing_password(self):
        """测试验证缺少密码"""
        config = {
            "host": "192.168.1.100",
            "username": "user",
            "password": "",
        }

        is_valid, error = SSHConfig.validate(config)

        assert is_valid is False
        assert "密码不能为空" in error

    def test_validate_none_values(self):
        """测试验证None值"""
        config = {
            "host": None,
            "username": "user",
            "password": "pass",
        }

        is_valid, error = SSHConfig.validate(config)

        assert is_valid is False
        assert "主机地址不能为空" in error


class TestSSHClientFactory:
    """测试SSH客户端工厂类"""

    def test_create_client(self, monkeypatch):
        """测试创建SSH客户端"""
        mock_client = MockSSHClient()
        monkeypatch.setattr(paramiko, "SSHClient", lambda: mock_client)

        client = SSHClientFactory.create_client()

        assert client is mock_client
        assert client.system_host_keys_loaded is True
        assert client.host_key_policy is not None

    def test_build_connect_kwargs_basic(self):
        """测试构建基本连接参数"""
        kwargs = SSHClientFactory.build_connect_kwargs(
            host="192.168.1.100",
            username="testuser",
        )

        assert kwargs["hostname"] == "192.168.1.100"
        assert kwargs["username"] == "testuser"
        assert kwargs["timeout"] == 10
        assert "password" not in kwargs

    def test_build_connect_kwargs_with_password(self):
        """测试构建带密码的连接参数"""
        kwargs = SSHClientFactory.build_connect_kwargs(
            host="192.168.1.100",
            username="testuser",
            password="secret123",
        )

        assert kwargs["hostname"] == "192.168.1.100"
        assert kwargs["username"] == "testuser"
        assert kwargs["password"] == "secret123"
        assert kwargs["look_for_keys"] is False
        assert kwargs["allow_agent"] is False
        assert kwargs["timeout"] == 10

    def test_build_connect_kwargs_custom_timeout(self):
        """测试构建自定义超时连接参数"""
        kwargs = SSHClientFactory.build_connect_kwargs(
            host="192.168.1.100",
            username="testuser",
            timeout=30,
        )

        assert kwargs["timeout"] == 30

    def test_build_connect_kwargs_extra_kwargs(self):
        """测试构建带额外参数的连接参数"""
        kwargs = SSHClientFactory.build_connect_kwargs(
            host="192.168.1.100",
            username="testuser",
            port=2222,
            key_filename="/path/to/key",
        )

        assert kwargs["hostname"] == "192.168.1.100"
        assert kwargs["port"] == 2222
        assert kwargs["key_filename"] == "/path/to/key"

    def test_connect_success(self, monkeypatch):
        """测试成功连接"""
        mock_client = MockSSHClient()
        monkeypatch.setattr(paramiko, "SSHClient", lambda: mock_client)

        client = SSHClientFactory.connect(
            host="192.168.1.100",
            username="testuser",
            password="secret",
        )

        assert client is mock_client
        assert client.connected is True
        assert client.connect_kwargs["hostname"] == "192.168.1.100"
        assert client.connect_kwargs["username"] == "testuser"

    def test_connect_failure(self, monkeypatch):
        """测试连接失败"""
        mock_client = MockSSHClient(should_fail_connect=True)
        monkeypatch.setattr(paramiko, "SSHClient", lambda: mock_client)

        with pytest.raises(paramiko.SSHException):
            SSHClientFactory.connect(
                host="192.168.1.100",
                username="testuser",
            )

    def test_connect_auth_failure(self, monkeypatch):
        """测试认证失败"""
        mock_client = MockSSHClient(auth_failure=True)
        monkeypatch.setattr(paramiko, "SSHClient", lambda: mock_client)

        with pytest.raises(paramiko.AuthenticationException):
            SSHClientFactory.connect(
                host="192.168.1.100",
                username="testuser",
                password="wrongpass",
            )


class TestSSHConnectionContext:
    """测试SSH连接上下文管理器"""

    def test_context_manager_enter_exit(self):
        """测试上下文管理器进入和退出"""
        mock_client = MockSSHClient()
        mock_client.connected = True

        with SSHConnectionContext(mock_client) as ctx:
            assert ctx.client is mock_client
            assert ctx.sftp is None

        assert mock_client.closed is True

    def test_open_sftp_success(self):
        """测试成功打开SFTP"""
        mock_client = MockSSHClient()
        mock_client.connected = True

        with SSHConnectionContext(mock_client) as ctx:
            sftp = ctx.open_sftp()
            assert sftp is not None
            assert ctx.sftp is sftp

    def test_open_sftp_without_client(self):
        """测试无客户端时打开SFTP"""
        with SSHConnectionContext(None) as ctx:
            with pytest.raises(RuntimeError) as exc_info:
                ctx.open_sftp()
            assert "SSH client is not connected" in str(exc_info.value)

    def test_close_with_sftp(self):
        """测试关闭时同时关闭SFTP"""
        mock_client = MockSSHClient()
        mock_client.connected = True

        ctx = SSHConnectionContext(mock_client)
        sftp = ctx.open_sftp()

        ctx.close()

        assert sftp.closed is True
        assert mock_client.closed is True

    def test_close_without_exception(self):
        """测试关闭时不抛出异常"""
        mock_client = MagicMock()
        mock_client.close.side_effect = Exception("Close error")

        ctx = SSHConnectionContext(mock_client)
        # 不应抛出异常
        ctx.close()

    def test_exit_returns_false(self):
        """测试__exit__返回False"""
        mock_client = MockSSHClient()

        ctx = SSHConnectionContext(mock_client)
        result = ctx.__exit__(None, None, None)

        assert result is False


class TestBaseSSHWorker:
    """测试SSH工作线程基类"""

    def test_init(self):
        """测试初始化"""
        worker = BaseSSHWorker(
            host="192.168.1.100",
            username="testuser",
            password="secret",
            timeout=20,
        )

        assert worker.host == "192.168.1.100"
        assert worker.username == "testuser"
        assert worker.password == "secret"
        assert worker.timeout == 20
        assert worker._client is None

    def test_get_client_creates_new(self, monkeypatch):
        """测试获取客户端时创建新连接"""
        mock_client = MockSSHClient()
        monkeypatch.setattr(paramiko, "SSHClient", lambda: mock_client)

        worker = BaseSSHWorker(
            host="192.168.1.100",
            username="testuser",
            password="secret",
        )

        client = worker.get_client()

        assert client is mock_client
        assert worker._client is mock_client

    def test_get_client_reuses_existing(self, monkeypatch):
        """测试获取客户端时复用现有连接"""
        mock_client = MockSSHClient()
        monkeypatch.setattr(paramiko, "SSHClient", lambda: mock_client)

        worker = BaseSSHWorker(
            host="192.168.1.100",
            username="testuser",
            password="secret",
        )

        client1 = worker.get_client()
        client2 = worker.get_client()

        assert client1 is client2

    def test_close_client(self, monkeypatch):
        """测试关闭客户端"""
        mock_client = MockSSHClient()
        monkeypatch.setattr(paramiko, "SSHClient", lambda: mock_client)

        worker = BaseSSHWorker(
            host="192.168.1.100",
            username="testuser",
            password="secret",
        )

        worker.get_client()
        worker.close_client()

        assert mock_client.closed is True
        assert worker._client is None

    def test_safe_close_self_client(self, monkeypatch):
        """测试安全关闭自己的客户端"""
        mock_client = MockSSHClient()
        monkeypatch.setattr(paramiko, "SSHClient", lambda: mock_client)

        worker = BaseSSHWorker(
            host="192.168.1.100",
            username="testuser",
            password="secret",
        )

        worker.get_client()
        worker.safe_close()

        assert mock_client.closed is True
        assert worker._client is None

    def test_safe_close_external_client(self):
        """测试安全关闭外部客户端"""
        mock_client = MockSSHClient()

        worker = BaseSSHWorker(
            host="192.168.1.100",
            username="testuser",
            password="secret",
        )

        worker.safe_close(mock_client)

        assert mock_client.closed is True

    def test_translate_exception_bad_host_key(self):
        """测试转换BadHostKeyException"""
        worker = BaseSSHWorker("host", "user", "pass")
        exc = paramiko.BadHostKeyException("host", MagicMock(), MagicMock())

        msg = worker.translate_exception(exc)

        assert "主机密钥验证失败" in msg

    def test_translate_exception_auth(self):
        """测试转换AuthenticationException"""
        worker = BaseSSHWorker("host", "user", "pass")
        exc = paramiko.AuthenticationException("auth failed")

        msg = worker.translate_exception(exc)

        assert "认证失败" in msg
        assert "用户名或密码错误" in msg

    def test_translate_exception_ssh(self):
        """测试转换SSHException"""
        worker = BaseSSHWorker("host", "user", "pass")
        exc = paramiko.SSHException("ssh error")

        msg = worker.translate_exception(exc)

        assert "SSH连接错误" in msg

    def test_translate_exception_timeout(self):
        """测试转换TimeoutError"""
        worker = BaseSSHWorker("host", "user", "pass")
        exc = TimeoutError("timeout")

        msg = worker.translate_exception(exc)

        assert "连接超时" in msg

    def test_translate_exception_generic(self):
        """测试转换通用异常"""
        worker = BaseSSHWorker("host", "user", "pass")
        exc = ValueError("generic error")

        msg = worker.translate_exception(exc)

        assert "连接失败" in msg
        assert "generic error" in msg

    def test_safe_close_with_exception(self, monkeypatch):
        """测试安全关闭时处理异常"""
        mock_client = MagicMock()
        mock_client.close.side_effect = Exception("Close error")

        worker = BaseSSHWorker("host", "user", "pass")
        worker._client = mock_client

        # 不应抛出异常
        worker.safe_close()
        assert worker._client is None

    def test_safe_close_external_with_exception(self):
        """测试安全关闭外部客户端时处理异常"""
        mock_client = MagicMock()
        mock_client.close.side_effect = Exception("Close error")

        worker = BaseSSHWorker("host", "user", "pass")

        # 不应抛出异常
        worker.safe_close(mock_client)
        # 外部客户端关闭不影响worker._client
        assert worker._client is None

    def test_close_client_with_exception(self, monkeypatch):
        """测试关闭客户端时处理异常"""
        mock_client = MockSSHClient()
        mock_client.close = MagicMock(side_effect=Exception("Close error"))
        monkeypatch.setattr(paramiko, "SSHClient", lambda: mock_client)

        worker = BaseSSHWorker("host", "user", "pass")
        worker.get_client()
        worker.close_client()

        # 即使抛出异常，_client也应该被设为None
        assert worker._client is None


class TestSSHConnectionContextExtended:
    """SSH连接上下文管理器扩展测试"""

    def test_close_sftp_with_exception(self):
        """测试关闭SFTP时处理异常"""
        mock_client = MockSSHClient()
        mock_client.connected = True

        mock_sftp = MockSFTPClient(should_fail_close=True)

        ctx = SSHConnectionContext(mock_client)
        ctx.sftp = mock_sftp

        # 不应抛出异常
        ctx.close()
        assert ctx.sftp is None
        assert mock_client.closed is True


class TestSSHConnectWorker:
    """测试SSH连接工作线程"""

    def test_init(self):
        """测试初始化"""
        worker = SSHConnectWorker(
            host="192.168.1.100",
            username="testuser",
            password="secret",
            timeout=15,
        )

        assert worker.host == "192.168.1.100"
        assert worker.username == "testuser"
        assert worker.password == "secret"
        assert worker.timeout == 15


class TestSFTPTransferWorker:
    """测试SFTP传输工作线程"""

    def test_init_upload(self):
        """测试初始化上传任务"""
        worker = SFTPTransferWorker(
            host="192.168.1.100",
            username="testuser",
            password="secret",
            action="upload",
            local_path="/local/file.txt",
            remote_path="/remote/file.txt",
            delete_source=False,
            timeout=30,
        )

        assert worker.host == "192.168.1.100"
        assert worker.action == "upload"
        assert worker.local_path == "/local/file.txt"
        assert worker.remote_path == "/remote/file.txt"
        assert worker.delete_source is False

    def test_init_download(self):
        """测试初始化下载任务"""
        worker = SFTPTransferWorker(
            host="192.168.1.100",
            username="testuser",
            password="secret",
            action="download",
            local_path="/local/file.txt",
            remote_path="/remote/file.txt",
            delete_source=True,
        )

        assert worker.action == "download"
        assert worker.delete_source is True

    def test_count_local_files_file(self, tmp_path):
        """测试统计单个文件"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        worker = SFTPTransferWorker(
            host="host",
            username="user",
            password="pass",
            action="upload",
            local_path=str(test_file),
            remote_path="/remote/test.txt",
        )

        count = worker._count_local_files(str(test_file))
        assert count == 1

    def test_count_local_files_directory(self, tmp_path):
        """测试统计目录中的文件"""
        # 创建目录结构
        (tmp_path / "subdir").mkdir()
        (tmp_path / "file1.txt").write_text("content")
        (tmp_path / "file2.txt").write_text("content")
        (tmp_path / "subdir" / "file3.txt").write_text("content")

        worker = SFTPTransferWorker(
            host="host",
            username="user",
            password="pass",
            action="upload",
            local_path=str(tmp_path),
            remote_path="/remote/",
        )

        count = worker._count_local_files(str(tmp_path))
        assert count == 3

    def test_delete_local_file(self, tmp_path):
        """测试删除本地文件"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        worker = SFTPTransferWorker(
            host="host",
            username="user",
            password="pass",
            action="upload",
            local_path=str(test_file),
            remote_path="/remote/test.txt",
        )

        worker._delete_local(str(test_file))
        assert not test_file.exists()

    def test_delete_local_directory(self, tmp_path):
        """测试删除本地目录"""
        test_dir = tmp_path / "testdir"
        test_dir.mkdir()
        (test_dir / "file.txt").write_text("content")

        worker = SFTPTransferWorker(
            host="host",
            username="user",
            password="pass",
            action="upload",
            local_path=str(test_dir),
            remote_path="/remote/testdir",
        )

        worker._delete_local(str(test_dir))
        assert not test_dir.exists()

    def test_ensure_remote_dir(self):
        """测试确保远程目录存在"""
        mock_sftp = MockSFTPClient()

        worker = SFTPTransferWorker(
            host="host",
            username="user",
            password="pass",
            action="upload",
            local_path="/local",
            remote_path="/remote/path/to/dir",
        )

        worker._ensure_remote_dir(mock_sftp, "/remote/path/to/dir")

        assert "/remote" in mock_sftp.created_dirs
        assert "/remote/path" in mock_sftp.created_dirs
        assert "/remote/path/to" in mock_sftp.created_dirs
        assert "/remote/path/to/dir" in mock_sftp.created_dirs

    def test_ensure_remote_dir_root(self):
        """测试确保根目录存在（边界情况）"""
        mock_sftp = MockSFTPClient()

        worker = SFTPTransferWorker(
            host="host",
            username="user",
            password="pass",
            action="upload",
            local_path="/local",
            remote_path="/",
        )

        # 根目录应该直接返回，不创建任何目录
        worker._ensure_remote_dir(mock_sftp, "")
        worker._ensure_remote_dir(mock_sftp, "/")

        assert len(mock_sftp.created_dirs) == 0

    def test_ensure_remote_dir_existing(self):
        """测试确保已存在目录"""
        mock_sftp = MockSFTPClient()
        mock_sftp.dirs["/existing"] = {}

        worker = SFTPTransferWorker(
            host="host",
            username="user",
            password="pass",
            action="upload",
            local_path="/local",
            remote_path="/existing/path",
        )

        worker._ensure_remote_dir(mock_sftp, "/existing/path")

        # /existing已存在，只创建/path
        assert "/existing" not in mock_sftp.created_dirs
        assert "/existing/path" in mock_sftp.created_dirs

    def test_upload_file(self, tmp_path):
        """测试上传单个文件"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        worker = SFTPTransferWorker(
            host="host",
            username="user",
            password="pass",
            action="upload",
            local_path=str(test_file),
            remote_path="/remote/test.txt",
        )

        mock_sftp = MockSFTPClient()
        worker._upload(mock_sftp, str(test_file), "/remote/test.txt")

        assert len(mock_sftp.uploaded_files) == 1
        assert mock_sftp.uploaded_files[0] == (str(test_file), "/remote/test.txt")

    def test_upload_directory(self, tmp_path):
        """测试上传目录"""
        # 创建目录结构
        (tmp_path / "subdir").mkdir()
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "subdir" / "file2.txt").write_text("content2")

        worker = SFTPTransferWorker(
            host="host",
            username="user",
            password="pass",
            action="upload",
            local_path=str(tmp_path),
            remote_path="/remote/dest",
        )

        mock_sftp = MockSFTPClient()
        worker._upload(mock_sftp, str(tmp_path), "/remote/dest")

        assert len(mock_sftp.uploaded_files) == 2
        assert "/remote/dest" in mock_sftp.created_dirs

    def test_download_file(self, tmp_path):
        """测试下载文件"""
        worker = SFTPTransferWorker(
            host="host",
            username="user",
            password="pass",
            action="download",
            local_path=str(tmp_path / "local.txt"),
            remote_path="/remote/test.txt",
        )

        mock_sftp = MockSFTPClient()
        mock_sftp.files["/remote/test.txt"] = b"test content"

        worker._download(mock_sftp, "/remote/test.txt", str(tmp_path / "local.txt"))

        assert len(mock_sftp.downloaded_files) == 1
        assert (tmp_path / "local.txt").parent.exists()

    def test_download_directory(self, tmp_path):
        """测试下载目录"""
        worker = SFTPTransferWorker(
            host="host",
            username="user",
            password="pass",
            action="download",
            local_path=str(tmp_path / "local_dir"),
            remote_path="/remote/dir",
        )

        mock_sftp = MockSFTPClient()
        mock_sftp.dirs["/remote/dir"] = {}
        import stat as stat_module
        mock_sftp.add_listdir_entry("/remote/dir", MockSFTPAttributes(
            is_dir=False, filename="file1.txt", st_mode=stat_module.S_IFREG | 0o644
        ))
        mock_sftp.files["/remote/dir/file1.txt"] = b"content"

        worker._download(mock_sftp, "/remote/dir", str(tmp_path / "local_dir"))

        assert (tmp_path / "local_dir").exists()

    def test_delete_remote_file(self):
        """测试删除远程文件"""
        worker = SFTPTransferWorker(
            host="host",
            username="user",
            password="pass",
            action="upload",
            local_path="/local",
            remote_path="/remote",
        )

        mock_sftp = MockSFTPClient()
        mock_sftp.files["/remote/file.txt"] = b"content"

        worker._delete_remote(mock_sftp, "/remote/file.txt")

        assert "/remote/file.txt" not in mock_sftp.files
        assert "/remote/file.txt" in mock_sftp.removed_files

    def test_delete_remote_directory(self):
        """测试删除远程目录"""
        worker = SFTPTransferWorker(
            host="host",
            username="user",
            password="pass",
            action="upload",
            local_path="/local",
            remote_path="/remote",
        )

        mock_sftp = MockSFTPClient()
        import stat as stat_module
        mock_sftp.dirs["/remote/dir"] = {}
        mock_sftp.add_listdir_entry("/remote/dir", MockSFTPAttributes(
            is_dir=False, filename="file.txt", st_mode=stat_module.S_IFREG | 0o644
        ))
        mock_sftp.files["/remote/dir/file.txt"] = b"content"

        worker._delete_remote(mock_sftp, "/remote/dir")

        assert "/remote/dir/file.txt" in mock_sftp.removed_files

    def test_delete_remote_nonexistent(self):
        """测试删除不存在的远程文件"""
        worker = SFTPTransferWorker(
            host="host",
            username="user",
            password="pass",
            action="upload",
            local_path="/local",
            remote_path="/remote",
        )

        mock_sftp = MockSFTPClient()

        # 不应抛出异常
        worker._delete_remote(mock_sftp, "/nonexistent/path")


class TestSSHCommandWorker:
    """测试SSH命令执行工作线程"""

    def test_init(self):
        """测试初始化"""
        commands = [
            ("step1", "echo hello", False),
            ("step2", "ls -la", False),
        ]

        worker = SSHCommandWorker(
            host="192.168.1.100",
            username="testuser",
            password="secret",
            commands=commands,
            timeout=30,
        )

        assert worker.host == "192.168.1.100"
        assert worker.username == "testuser"
        assert worker.password == "secret"
        assert len(worker.commands) == 2
        assert worker.timeout == 30

    def test_init_empty_commands(self):
        """测试初始化空命令列表"""
        worker = SSHCommandWorker(
            host="192.168.1.100",
            username="testuser",
            password="secret",
            commands=[],
        )

        assert worker.commands == []


class TestIntegration:
    """集成测试"""

    def test_full_ssh_flow(self, monkeypatch):
        """测试完整SSH流程"""
        mock_client = MockSSHClient()
        monkeypatch.setattr(paramiko, "SSHClient", lambda: mock_client)

        # 1. 验证配置
        config_manager = MockConfigManager({
            "ssh_host": "192.168.1.100",
            "ssh_username": "testuser",
            "ssh_password": "testpass",
        })
        config = SSHConfig.from_config_manager(config_manager)
        is_valid, _ = SSHConfig.validate(config)
        assert is_valid is True

        # 2. 创建连接
        client = SSHClientFactory.connect(**config)
        assert client.connected is True

        # 3. 使用上下文管理器
        with SSHConnectionContext(client) as ctx:
            sftp = ctx.open_sftp()
            assert sftp is not None

        assert client.closed is True

    def test_config_validation_integration(self):
        """测试配置验证集成"""
        # 有效配置
        valid_configs = [
            {"host": "192.168.1.1", "username": "user", "password": "pass"},
            {"host": "example.com", "username": "admin", "password": "secret"},
            {"host": "10.0.0.1", "username": "root", "password": "rootpass"},
        ]

        for config in valid_configs:
            is_valid, _ = SSHConfig.validate(config)
            assert is_valid is True, f"Config should be valid: {config}"

        # 无效配置
        invalid_configs = [
            {"host": "", "username": "user", "password": "pass"},
            {"host": "192.168.1.1", "username": "", "password": "pass"},
            {"host": "192.168.1.1", "username": "user", "password": ""},
            {"host": None, "username": "user", "password": "pass"},
        ]

        for config in invalid_configs:
            is_valid, _ = SSHConfig.validate(config)
            assert is_valid is False, f"Config should be invalid: {config}"
