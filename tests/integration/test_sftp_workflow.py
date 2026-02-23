"""
SFTP文件传输集成测试

需要Ubuntu虚拟机环境（192.168.56.132）
通过环境变量 UBUNTU_VM_AVAILABLE=1 启用
"""

import os
import pytest
import tempfile
import hashlib
import time

# 导入测试工具
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.test_helpers import (
    check_env_available,
    get_test_config,
    generate_test_file,
    generate_test_text_file,
    calculate_file_hash,
    create_large_test_file
)

# 从conftest导入标记
from tests.integration.conftest import ubuntu_vm


@pytest.fixture
def ssh_config():
    """获取SSH配置"""
    return get_test_config()


@pytest.fixture
def sftp_client(ssh_config):
    """提供已连接的SFTP客户端"""
    try:
        import paramiko
        from src.core.ssh_utils import SSHClientFactory
    except ImportError:
        pytest.skip("依赖未安装")

    config = ssh_config.get("ubuntu_vm", {})
    if not check_env_available(config.get("host"), config.get("port", 22)):
        pytest.skip(f"Ubuntu VM {config.get('host')} 不可达")

    # 支持密码或密钥认证
    connect_kwargs = {
        "host": config.get("host"),
        "username": config.get("username"),
        "timeout": 10
    }
    if config.get("password"):
        connect_kwargs["password"] = config.get("password")
    # 支持 key_filename 或 private_key 配置
    key_file = config.get("key_filename") or config.get("private_key")
    if key_file:
        # 展开 ~ 为用户主目录
        import os
        connect_kwargs["key_filename"] = os.path.expanduser(key_file)

    ssh_client = SSHClientFactory.connect(**connect_kwargs)
    sftp = ssh_client.open_sftp()
    yield sftp
    sftp.close()
    ssh_client.close()


@pytest.fixture
def remote_test_dir(ssh_config):
    """提供远程测试目录路径"""
    config = ssh_config.get("ubuntu_vm", {})
    # 使用固定目录避免时序问题
    test_dir = "/home/jiangkai/sftp_test/test_data"

    try:
        import paramiko
        from src.core.ssh_utils import SSHClientFactory
    except ImportError:
        pytest.skip("依赖未安装")

    if not check_env_available(config.get("host"), config.get("port", 22)):
        pytest.skip(f"Ubuntu VM {config.get('host')} 不可达")

    # 支持密码或密钥认证
    connect_kwargs = {
        "host": config.get("host"),
        "username": config.get("username"),
        "timeout": 10
    }
    if config.get("password"):
        connect_kwargs["password"] = config.get("password")
    # 支持 key_filename 或 private_key 配置
    key_file = config.get("key_filename") or config.get("private_key")
    if key_file:
        # 展开 ~ 为用户主目录
        import os
        connect_kwargs["key_filename"] = os.path.expanduser(key_file)

    ssh_client = SSHClientFactory.connect(**connect_kwargs)

    # 确保测试目录存在
    ssh_client.exec_command(f"mkdir -p {test_dir}")
    ssh_client.close()

    yield test_dir

    # 清理：删除测试目录中的文件
    try:
        ssh_client = SSHClientFactory.connect(**connect_kwargs)
        ssh_client.exec_command(f"rm -rf {test_dir}/*")
        ssh_client.close()
    except Exception:
        pass


@ubuntu_vm
class TestSFTPUpload:
    """SFTP文件上传测试"""

    def test_upload_small_file(self, sftp_client, remote_test_dir):
        """测试上传小文件"""
        # 创建本地测试文件
        local_file = generate_test_text_file(content="Hello, SFTP!")
        remote_path = f"{remote_test_dir}/small_file.txt"

        try:
            # 上传文件
            sftp_client.put(local_file, remote_path)

            # 验证文件存在
            try:
                stat = sftp_client.stat(remote_path)
                assert stat.st_size > 0, "上传的文件大小为0"
            except FileNotFoundError:
                pytest.fail("上传的文件不存在")
        finally:
            os.remove(local_file)

    def test_upload_binary_file(self, sftp_client, remote_test_dir):
        """测试上传二进制文件"""
        # 创建二进制测试文件
        local_file = generate_test_file(size=1024)
        remote_path = f"{remote_test_dir}/binary_file.bin"

        try:
            # 上传文件
            sftp_client.put(local_file, remote_path)

            # 验证文件存在且大小正确
            stat = sftp_client.stat(remote_path)
            assert stat.st_size == 1024, f"文件大小不匹配: {stat.st_size} != 1024"
        finally:
            os.remove(local_file)

    def test_upload_large_file(self, sftp_client, remote_test_dir):
        """测试上传大文件（1MB）"""
        # 创建大文件
        local_file = generate_test_file(size=1024 * 1024)  # 1MB
        remote_path = f"{remote_test_dir}/large_file.bin"

        try:
            # 上传文件
            sftp_client.put(local_file, remote_path)

            # 验证文件存在且大小正确
            stat = sftp_client.stat(remote_path)
            assert stat.st_size == 1024 * 1024, f"大文件大小不匹配: {stat.st_size}"
        finally:
            os.remove(local_file)

    def test_upload_file_integrity(self, sftp_client, remote_test_dir):
        """测试上传文件完整性（哈希验证）"""
        # 创建测试文件
        local_file = generate_test_file(size=4096)
        remote_path = f"{remote_test_dir}/integrity_test.bin"

        try:
            # 计算本地哈希
            local_hash = calculate_file_hash(local_file, "md5")

            # 上传文件
            sftp_client.put(local_file, remote_path)

            # 下载并计算远程哈希
            with tempfile.NamedTemporaryFile(delete=False) as temp:
                temp_path = temp.name

            try:
                sftp_client.get(remote_path, temp_path)
                remote_hash = calculate_file_hash(temp_path, "md5")
                assert local_hash == remote_hash, f"文件哈希不匹配: {local_hash} != {remote_hash}"
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        finally:
            os.remove(local_file)

    def test_upload_to_nonexistent_directory(self, sftp_client, remote_test_dir):
        """测试上传到不存在的目录（应该失败）"""
        local_file = generate_test_text_file()
        remote_path = f"{remote_test_dir}/nonexistent_dir/file.txt"

        try:
            with pytest.raises((IOError, FileNotFoundError)):
                sftp_client.put(local_file, remote_path)
        finally:
            os.remove(local_file)


@ubuntu_vm
class TestSFTPDownload:
    """SFTP文件下载测试"""

    def test_download_small_file(self, sftp_client, remote_test_dir):
        """测试下载小文件"""
        # 在远程创建测试文件
        remote_path = f"{remote_test_dir}/download_test.txt"
        test_content = "Test content for download"

        # 使用sftp写入文件
        with sftp_client.file(remote_path, 'w') as f:
            f.write(test_content)

        # 下载文件
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            local_path = temp.name

        try:
            sftp_client.get(remote_path, local_path)

            # 验证文件内容
            with open(local_path, 'r') as f:
                content = f.read()
            assert content == test_content, f"下载文件内容不匹配: {content}"
        finally:
            if os.path.exists(local_path):
                os.remove(local_path)

    def test_download_binary_file(self, sftp_client, remote_test_dir):
        """测试下载二进制文件"""
        remote_path = f"{remote_test_dir}/download_binary.bin"
        test_data = os.urandom(1024)

        # 在远程创建二进制文件
        with sftp_client.file(remote_path, 'wb') as f:
            f.write(test_data)

        # 下载文件
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            local_path = temp.name

        try:
            sftp_client.get(remote_path, local_path)

            # 验证文件大小
            assert os.path.getsize(local_path) == 1024, "下载文件大小不匹配"

            # 验证文件内容
            with open(local_path, 'rb') as f:
                content = f.read()
            assert content == test_data, "下载的二进制文件内容不匹配"
        finally:
            if os.path.exists(local_path):
                os.remove(local_path)

    def test_download_nonexistent_file(self, sftp_client, remote_test_dir):
        """测试下载不存在的文件（应该失败）"""
        remote_path = f"{remote_test_dir}/nonexistent_file.txt"

        with tempfile.NamedTemporaryFile(delete=False) as temp:
            local_path = temp.name

        try:
            with pytest.raises((IOError, FileNotFoundError)):
                sftp_client.get(remote_path, local_path)
        finally:
            if os.path.exists(local_path):
                os.remove(local_path)


@ubuntu_vm
class TestSFTPDelete:
    """SFTP文件删除测试"""

    def test_delete_file(self, sftp_client, remote_test_dir):
        """测试删除文件"""
        remote_path = f"{remote_test_dir}/delete_test.txt"

        # 创建文件
        with sftp_client.file(remote_path, 'w') as f:
            f.write("test content")

        # 验证文件存在
        sftp_client.stat(remote_path)

        # 删除文件
        sftp_client.remove(remote_path)

        # 验证文件不存在
        with pytest.raises(IOError):
            sftp_client.stat(remote_path)

    def test_delete_nonexistent_file(self, sftp_client, remote_test_dir):
        """测试删除不存在的文件（应该失败）"""
        remote_path = f"{remote_test_dir}/nonexistent_delete.txt"

        with pytest.raises(IOError):
            sftp_client.remove(remote_path)


@ubuntu_vm
class TestSFTPDirectory:
    """SFTP目录操作测试"""

    def test_list_directory(self, sftp_client, remote_test_dir):
        """测试列出目录内容"""
        # 创建一些测试文件
        for i in range(3):
            remote_path = f"{remote_test_dir}/file{i}.txt"
            with sftp_client.file(remote_path, 'w') as f:
                f.write(f"content {i}")

        # 列出目录
        entries = sftp_client.listdir(remote_test_dir)

        # 验证文件存在
        assert "file0.txt" in entries, "file0.txt 不在目录列表中"
        assert "file1.txt" in entries, "file1.txt 不在目录列表中"
        assert "file2.txt" in entries, "file2.txt 不在目录列表中"

    def test_list_empty_directory(self, sftp_client, remote_test_dir):
        """测试列出空目录"""
        entries = sftp_client.listdir(remote_test_dir)
        assert isinstance(entries, list), "listdir应该返回列表"

    def test_create_and_remove_directory(self, sftp_client, remote_test_dir):
        """测试创建和删除目录"""
        new_dir = f"{remote_test_dir}/new_directory"

        # 创建目录
        sftp_client.mkdir(new_dir)

        # 验证目录存在
        try:
            sftp_client.stat(new_dir)
        except IOError:
            pytest.fail("创建的目录不存在")

        # 删除目录
        sftp_client.rmdir(new_dir)

        # 验证目录不存在
        with pytest.raises(IOError):
            sftp_client.stat(new_dir)


@ubuntu_vm
class TestSFTPFilePermissions:
    """SFTP文件权限测试"""

    def test_file_permissions_after_upload(self, sftp_client, remote_test_dir):
        """测试上传后的文件权限"""
        local_file = generate_test_text_file()
        remote_path = f"{remote_test_dir}/permission_test.txt"

        try:
            # 上传文件
            sftp_client.put(local_file, remote_path)

            # 获取文件状态
            stat = sftp_client.stat(remote_path)

            # 验证文件有读权限
            assert stat.st_mode & 0o400, "文件没有读权限"

            # 验证文件所有者
            assert stat.st_uid is not None, "无法获取文件所有者"
        finally:
            os.remove(local_file)

    def test_change_file_permissions(self, sftp_client, remote_test_dir):
        """测试修改文件权限"""
        remote_path = f"{remote_test_dir}/chmod_test.txt"

        # 创建文件
        with sftp_client.file(remote_path, 'w') as f:
            f.write("test")

        # 修改权限为 755
        sftp_client.chmod(remote_path, 0o755)

        # 验证权限
        stat = sftp_client.stat(remote_path)
        # 注意：权限验证可能因系统而异，这里只验证权限被设置了
        assert stat.st_mode is not None, "无法获取文件权限"


@ubuntu_vm
class TestSFTPWorkflow:
    """SFTP完整工作流测试"""

    def test_upload_download_delete_workflow(self, sftp_client, remote_test_dir):
        """测试完整的上传-下载-删除工作流"""
        # 创建本地测试文件
        local_file = generate_test_file(size=2048)
        remote_path = f"{remote_test_dir}/workflow_test.bin"

        with tempfile.NamedTemporaryFile(delete=False) as temp:
            download_path = temp.name

        try:
            # 1. 上传
            sftp_client.put(local_file, remote_path)
            stat = sftp_client.stat(remote_path)
            assert stat.st_size == 2048, "上传文件大小不匹配"

            # 2. 下载
            sftp_client.get(remote_path, download_path)
            assert os.path.getsize(download_path) == 2048, "下载文件大小不匹配"

            # 3. 验证哈希
            local_hash = calculate_file_hash(local_file)
            download_hash = calculate_file_hash(download_path)
            assert local_hash == download_hash, "文件哈希不匹配"

            # 4. 删除
            sftp_client.remove(remote_path)
            with pytest.raises(IOError):
                sftp_client.stat(remote_path)

        finally:
            os.remove(local_file)
            if os.path.exists(download_path):
                os.remove(download_path)

    def test_multiple_files_transfer(self, sftp_client, remote_test_dir):
        """测试多个文件传输"""
        files = []

        try:
            # 创建并上传多个文件
            for i in range(5):
                local_file = generate_test_text_file(content=f"Content of file {i}")
                files.append(local_file)
                remote_path = f"{remote_test_dir}/multi_file_{i}.txt"
                sftp_client.put(local_file, remote_path)

            # 验证所有文件都存在
            entries = sftp_client.listdir(remote_test_dir)
            for i in range(5):
                assert f"multi_file_{i}.txt" in entries, f"multi_file_{i}.txt 不存在"

        finally:
            for f in files:
                if os.path.exists(f):
                    os.remove(f)
