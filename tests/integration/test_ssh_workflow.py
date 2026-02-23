"""
SSH工作流集成测试

需要Ubuntu虚拟机环境（192.168.56.132）
通过环境变量 UBUNTU_VM_AVAILABLE=1 启用
"""

import os
import pytest
import tempfile
import hashlib
import socket
import time

# 导入测试工具
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.test_helpers import (
    check_env_available,
    get_test_config,
    wait_for_condition,
    generate_test_file,
    calculate_file_hash
)

# 从conftest导入标记
from tests.integration.conftest import ubuntu_vm


@pytest.fixture
def ssh_config():
    """获取SSH配置"""
    return get_test_config()


@pytest.fixture
def temp_test_file():
    """创建临时测试文件"""
    temp_file = generate_test_file(size=1024)
    yield temp_file
    # 清理
    if os.path.exists(temp_file):
        os.remove(temp_file)


@ubuntu_vm
class TestSSHConnection:
    """SSH连接集成测试"""

    def test_ssh_basic_connection_success(self, ssh_config):
        """测试基础SSH连接成功"""
        try:
            from src.core.ssh_utils import SSHClientFactory
        except ImportError:
            pytest.skip("SSHClientFactory未实现")

        config = ssh_config.get("ubuntu_vm", {})
        if not config:
            pytest.skip("未找到Ubuntu VM配置")

        # 检查环境是否可用
        if not check_env_available(config.get("host"), config.get("port", 22)):
            pytest.skip(f"Ubuntu VM {config.get('host')} 不可达")

        client = None
        try:
            client = SSHClientFactory.connect(
                host=config.get("host"),
                username=config.get("username"),
                password=config.get("password"),
                timeout=10
            )
            assert client is not None, "SSH连接失败"
            assert client.get_transport() is not None, "SSH传输层未建立"
            assert client.get_transport().is_active(), "SSH连接未激活"
        finally:
            if client:
                client.close()

    def test_ssh_connection_failure_wrong_password(self, ssh_config):
        """测试SSH连接失败 - 错误密码"""
        try:
            import paramiko
            from src.core.ssh_utils import SSHClientFactory
        except ImportError:
            pytest.skip("SSHClientFactory或paramiko未实现")

        config = ssh_config.get("ubuntu_vm", {})
        if not check_env_available(config.get("host"), config.get("port", 22)):
            pytest.skip(f"Ubuntu VM {config.get('host')} 不可达")

        with pytest.raises(paramiko.AuthenticationException):
            SSHClientFactory.connect(
                host=config.get("host"),
                username=config.get("username"),
                password="wrong_password_12345",
                timeout=10
            )

    def test_ssh_connection_failure_wrong_host(self):
        """测试SSH连接失败 - 错误主机"""
        try:
            import paramiko
            from src.core.ssh_utils import SSHClientFactory
        except ImportError:
            pytest.skip("SSHClientFactory或paramiko未实现")

        with pytest.raises((paramiko.SSHException, socket.error, TimeoutError)):
            SSHClientFactory.connect(
                host="192.168.255.255",  # 不可达的主机
                username="testuser",
                password="testpass",
                timeout=2
            )

    def test_ssh_connection_timeout(self):
        """测试SSH连接超时处理"""
        try:
            import paramiko
            from src.core.ssh_utils import SSHClientFactory
        except ImportError:
            pytest.skip("SSHClientFactory或paramiko未实现")

        start_time = time.time()
        with pytest.raises((paramiko.SSHException, socket.error, TimeoutError)):
            SSHClientFactory.connect(
                host="192.168.255.255",  # 不可达的主机
                username="testuser",
                password="testpass",
                timeout=3
            )
        elapsed = time.time() - start_time
        # 验证超时机制生效（允许一定误差）
        assert elapsed < 10, "连接未在预期时间内超时"


@ubuntu_vm
class TestSSHCommandExecution:
    """SSH命令执行集成测试"""

    @pytest.fixture
    def connected_client(self, ssh_config):
        """提供已连接的SSH客户端"""
        try:
            from src.core.ssh_utils import SSHClientFactory
        except ImportError:
            pytest.skip("SSHClientFactory未实现")

        config = ssh_config.get("ubuntu_vm", {})
        if not check_env_available(config.get("host"), config.get("port", 22)):
            pytest.skip(f"Ubuntu VM {config.get('host')} 不可达")

        client = SSHClientFactory.connect(
            host=config.get("host"),
            username=config.get("username"),
            password=config.get("password"),
            timeout=10
        )
        yield client
        client.close()

    def test_execute_simple_echo(self, connected_client):
        """测试执行简单echo命令"""
        stdin, stdout, stderr = connected_client.exec_command("echo 'hello world'")
        exit_code = stdout.channel.recv_exit_status()
        output = stdout.read().decode('utf-8').strip()

        assert exit_code == 0, f"命令执行失败: {stderr.read().decode()}"
        assert output == "hello world", f"输出不匹配: {output}"

    def test_execute_pwd(self, connected_client):
        """测试执行pwd命令"""
        stdin, stdout, stderr = connected_client.exec_command("pwd")
        exit_code = stdout.channel.recv_exit_status()
        output = stdout.read().decode('utf-8').strip()

        assert exit_code == 0, f"命令执行失败: {stderr.read().decode()}"
        assert "/home" in output or "/tmp" in output or output.startswith("/"), f"意外的当前目录: {output}"

    def test_execute_ls(self, connected_client):
        """测试执行ls命令"""
        stdin, stdout, stderr = connected_client.exec_command("ls -la")
        exit_code = stdout.channel.recv_exit_status()
        output = stdout.read().decode('utf-8')

        assert exit_code == 0, f"命令执行失败: {stderr.read().decode()}"
        assert len(output) > 0, "ls命令无输出"

    def test_execute_complex_pipeline(self, connected_client):
        """测试执行复杂命令（管道）"""
        stdin, stdout, stderr = connected_client.exec_command("echo 'line1\nline2\nline3' | wc -l")
        exit_code = stdout.channel.recv_exit_status()
        output = stdout.read().decode('utf-8').strip()

        assert exit_code == 0, f"命令执行失败: {stderr.read().decode()}"
        assert output == "3", f"管道命令输出不匹配: {output}"

    def test_execute_with_redirection(self, connected_client):
        """测试执行带重定向的命令"""
        # 创建临时文件
        stdin, stdout, stderr = connected_client.exec_command("echo 'test content' > /tmp/test_redirect.txt && cat /tmp/test_redirect.txt")
        exit_code = stdout.channel.recv_exit_status()
        output = stdout.read().decode('utf-8').strip()

        assert exit_code == 0, f"命令执行失败: {stderr.read().decode()}"
        assert "test content" in output, f"重定向输出不匹配: {output}"

        # 清理
        connected_client.exec_command("rm -f /tmp/test_redirect.txt")

    def test_execute_command_with_args(self, connected_client):
        """测试执行带参数的命令"""
        stdin, stdout, stderr = connected_client.exec_command("echo $HOME")
        exit_code = stdout.channel.recv_exit_status()
        output = stdout.read().decode('utf-8').strip()

        assert exit_code == 0, f"命令执行失败: {stderr.read().decode()}"
        assert "/home/" in output, f"环境变量输出不匹配: {output}"

    def test_execute_invalid_command(self, connected_client):
        """测试执行无效命令"""
        stdin, stdout, stderr = connected_client.exec_command("nonexistent_command_12345")
        exit_code = stdout.channel.recv_exit_status()
        error_output = stderr.read().decode('utf-8')

        assert exit_code != 0, "无效命令应该返回非零退出码"
        assert len(error_output) > 0 or exit_code > 0, "应该有错误信息或非零退出码"

    def test_execute_multiple_commands(self, connected_client):
        """测试连续执行多个命令"""
        commands = [
            ("echo 'first'", "first"),
            ("echo 'second'", "second"),
            ("echo 'third'", "third"),
        ]

        for cmd, expected in commands:
            stdin, stdout, stderr = connected_client.exec_command(cmd)
            exit_code = stdout.channel.recv_exit_status()
            output = stdout.read().decode('utf-8').strip()

            assert exit_code == 0, f"命令 '{cmd}' 执行失败"
            assert expected in output, f"命令 '{cmd}' 输出不匹配: {output}"


@ubuntu_vm
class TestSSHAuthenticationFailure:
    """SSH认证失败处理测试"""

    def test_auth_failure_wrong_username(self, ssh_config):
        """测试错误用户名认证失败"""
        try:
            import paramiko
            from src.core.ssh_utils import SSHClientFactory
        except ImportError:
            pytest.skip("依赖未安装")

        config = ssh_config.get("ubuntu_vm", {})
        if not check_env_available(config.get("host"), config.get("port", 22)):
            pytest.skip(f"Ubuntu VM {config.get('host')} 不可达")

        with pytest.raises(paramiko.AuthenticationException):
            SSHClientFactory.connect(
                host=config.get("host"),
                username="nonexistent_user_12345",
                password=config.get("password"),
                timeout=10
            )

    @pytest.mark.skip(reason="VM使用公钥认证，空密码也能登录成功，此测试不适用")
    def test_auth_failure_empty_password(self, ssh_config):
        """测试空密码认证失败"""
        try:
            import paramiko
            from src.core.ssh_utils import SSHClientFactory
        except ImportError:
            pytest.skip("依赖未安装")

        config = ssh_config.get("ubuntu_vm", {})
        if not check_env_available(config.get("host"), config.get("port", 22)):
            pytest.skip(f"Ubuntu VM {config.get('host')} 不可达")

        with pytest.raises(paramiko.AuthenticationException):
            SSHClientFactory.connect(
                host=config.get("host"),
                username=config.get("username"),
                password="",
                timeout=10
            )


@ubuntu_vm
class TestSSHConnectionRetry:
    """SSH连接重试机制测试"""

    def test_connection_retry_on_failure(self, ssh_config):
        """测试连接失败时的重试行为"""
        try:
            import paramiko
            from src.core.ssh_utils import SSHClientFactory
        except ImportError:
            pytest.skip("依赖未安装")

        config = ssh_config.get("ubuntu_vm", {})

        # 使用错误端口测试重试
        start_time = time.time()
        with pytest.raises((paramiko.SSHException, socket.error, TimeoutError)):
            SSHClientFactory.connect(
                host=config.get("host"),
                username=config.get("username"),
                password=config.get("password"),
                timeout=2,
                port=22222  # 错误端口
            )
        elapsed = time.time() - start_time

        # 验证超时机制（应该快速失败而不是长时间重试）
        assert elapsed < 15, "连接重试时间过长"
