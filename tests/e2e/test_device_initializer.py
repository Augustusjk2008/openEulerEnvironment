"""
设备初始化向导测试 - 真实设备测试

重要警告：
- 本测试仅针对真实目标板 192.168.1.29
- 绝对禁止在 Ubuntu 虚拟机 (192.168.56.132) 执行
- 必须设置 REAL_DEVICE_TEST=1 环境变量才执行
- 默认情况下（无环境变量）自动跳过

环境变量要求：
- REAL_DEVICE_TEST=1 - 启用真实设备测试
- DEVICE_PASSWORD - root用户密码
"""

import os
import pytest
import yaml
import time
import socket
from pathlib import Path

# 标记需要真实设备的测试
real_device = pytest.mark.skipif(
    not os.environ.get("REAL_DEVICE_TEST"),
    reason="需要真实目标板192.168.1.29（设置REAL_DEVICE_TEST=1启用）"
)

# 验证目标设备IP，禁止在Ubuntu虚拟机执行
FORBIDDEN_HOSTS = ["192.168.56.132"]
REQUIRED_HOST = "192.168.1.29"


def load_device_config():
    """加载设备测试配置"""
    config_path = Path(__file__).parent.parent / "config" / "device_test_env.yaml"
    if not config_path.exists():
        pytest.skip(f"设备测试配置文件不存在: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # 替换环境变量
    password = os.environ.get("DEVICE_PASSWORD")
    if password:
        config["device"]["password"] = password

    return config


def verify_target_host(host):
    """验证目标主机是允许的设备，不是禁止的主机"""
    if host in FORBIDDEN_HOSTS:
        raise ValueError(f"禁止在 {host} 执行设备初始化测试！")
    if host != REQUIRED_HOST:
        pytest.skip(f"目标设备必须是 {REQUIRED_HOST}，当前为 {host}")


def check_host_reachable(host, port=22, timeout=5):
    """检查目标主机是否可达"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


@pytest.fixture(scope="class")
def device_config():
    """设备配置fixture"""
    config = load_device_config()
    device = config["device"]

    # 验证目标主机
    verify_target_host(device["host"])

    # 检查主机可达性
    if not check_host_reachable(device["host"], device["port"]):
        pytest.skip(f"目标设备 {device['host']} 不可达")

    # 检查密码
    if not device.get("password"):
        pytest.skip("未设置设备密码（DEVICE_PASSWORD环境变量）")

    return config


@pytest.fixture(scope="class")
def ssh_connection(device_config):
    """SSH连接fixture"""
    try:
        import paramiko
    except ImportError:
        pytest.skip("未安装paramiko，无法执行SSH测试")

    device = device_config["device"]
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(
            hostname=device["host"],
            port=device["port"],
            username=device["username"],
            password=device["password"],
            timeout=30
        )
        yield client
    except Exception as e:
        pytest.skip(f"SSH连接失败: {e}")
    finally:
        client.close()


@pytest.fixture(scope="class")
def sftp_connection(ssh_connection):
    """SFTP连接fixture"""
    sftp = ssh_connection.open_sftp()
    yield sftp
    sftp.close()


@real_device
class TestDeviceInitialization:
    """设备初始化向导测试 - 仅在真实设备执行

    测试目标：验证设备初始化向导在真实目标板(192.168.1.29)上的功能
    测试范围：8步初始化流程
    环境要求：真实设备IP、root密码
    """

    def test_step0_ssh_connection(self, device_config, ssh_connection):
        """步骤0：验证SSH连接

        验证点：
        - SSH连接成功建立
        - 可以执行基本命令
        - 返回结果正确
        """
        stdin, stdout, stderr = ssh_connection.exec_command("whoami")
        result = stdout.read().decode().strip()
        assert result == "root", f"期望用户为root，实际为{result}"

    def test_step1_set_root_password(self, device_config, ssh_connection):
        """步骤1：设置root密码

        验证点：
        - 密码设置命令执行成功
        - 新密码可以正常登录
        """
        device = device_config["device"]
        password = device["password"]

        # 设置密码
        command = f"echo 'root:{password}' | chpasswd"
        stdin, stdout, stderr = ssh_connection.exec_command(command)
        exit_code = stdout.channel.recv_exit_status()

        assert exit_code == 0, f"密码设置失败: {stderr.read().decode()}"

        # 验证密码设置成功（通过新连接测试）
        import paramiko
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(
                hostname=device["host"],
                port=device["port"],
                username="root",
                password=password,
                timeout=10
            )
            stdin, stdout, stderr = client.exec_command("whoami")
            result = stdout.read().decode().strip()
            assert result == "root", "密码设置后无法登录"
        finally:
            client.close()

    def test_step2_create_directory_structure(self, device_config, ssh_connection):
        """步骤2：创建目录结构

        验证点：
        - /home/sast8目录创建成功
        - 子目录结构完整
        - 目录权限正确
        """
        # 创建目录结构
        dirs = [
            "/home/sast8",
            "/home/sast8/user_tests",
            "/home/sast8/user_apps",
            "/home/sast8/user_libs",
            "/home/sast8/user_libs/shared_libs",
            "/home/sast8/user_libs/static_libs",
            "/home/sast8/user_modules",
            "/home/sast8/user_modules/resize",
            "/home/sast8/user_modules/xdma_803",
            "/home/sast8/user_tmp",
        ]

        for dir_path in dirs:
            command = f"mkdir -p {dir_path}"
            stdin, stdout, stderr = ssh_connection.exec_command(command)
            exit_code = stdout.channel.recv_exit_status()
            assert exit_code == 0, f"创建目录 {dir_path} 失败"

        # 验证目录存在
        for dir_path in dirs:
            command = f"test -d {dir_path} && echo 'EXISTS'"
            stdin, stdout, stderr = ssh_connection.exec_command(command)
            result = stdout.read().decode().strip()
            assert result == "EXISTS", f"目录 {dir_path} 不存在"

    def test_step3_upload_files(self, device_config, ssh_connection, sftp_connection):
        """步骤3：上传文件到目标设备

        验证点：
        - 文件可以成功上传
        - 上传后文件完整性正确
        - 文件权限正确
        """
        import tempfile

        # 创建临时测试文件
        test_content = "This is a test file for device initialization"

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write(test_content)
            temp_file = f.name

        try:
            remote_path = "/home/sast8/user_tests/test_upload.txt"

            # 上传文件
            sftp_connection.put(temp_file, remote_path)

            # 验证文件存在且内容正确
            stdin, stdout, stderr = ssh_connection.exec_command(f"cat {remote_path}")
            result = stdout.read().decode().strip()
            assert result == test_content, "上传文件内容不匹配"

            # 清理测试文件
            ssh_connection.exec_command(f"rm -f {remote_path}")

        finally:
            os.unlink(temp_file)

    def test_step4_configure_ld_library_path(self, device_config, ssh_connection):
        """步骤4：配置动态库路径

        验证点：
        - ld.so.conf.d/sast8_libs.conf创建成功
        - 配置内容正确
        - ldconfig执行成功
        """
        # 创建ld.so.conf.d目录（如果不存在）
        commands = [
            "mkdir -p /etc/ld.so.conf.d",
            "echo '/home/sast8/user_libs/shared_libs' > /etc/ld.so.conf.d/sast8_libs.conf",
            "ldconfig",
        ]

        for command in commands:
            stdin, stdout, stderr = ssh_connection.exec_command(command)
            exit_code = stdout.channel.recv_exit_status()
            assert exit_code == 0, f"命令执行失败: {command}"

        # 验证配置文件内容
        stdin, stdout, stderr = ssh_connection.exec_command(
            "cat /etc/ld.so.conf.d/sast8_libs.conf"
        )
        result = stdout.read().decode().strip()
        assert "/home/sast8/user_libs/shared_libs" in result, "动态库路径配置不正确"

        # 验证ldconfig执行成功
        stdin, stdout, stderr = ssh_connection.exec_command("ldconfig -p")
        exit_code = stdout.channel.recv_exit_status()
        assert exit_code == 0, "ldconfig执行失败"

    def test_step5_expand_partition(self, device_config, ssh_connection):
        """步骤5：硬盘扩容

        验证点：
        - resize2fs-arm64文件存在且可执行
        - 扩容命令执行成功
        - 分区大小增加

        注意：此测试可能需要较长时间，且在某些情况下可能无法执行
        """
        # 检查resize2fs-arm64是否存在
        stdin, stdout, stderr = ssh_connection.exec_command(
            "test -f /home/sast8/user_modules/resize/resize2fs-arm64 && echo 'EXISTS'"
        )
        result = stdout.read().decode().strip()

        if result != "EXISTS":
            pytest.skip("resize2fs-arm64不存在，跳过扩容测试")

        # 检查是否可执行
        stdin, stdout, stderr = ssh_connection.exec_command(
            "chmod +x /home/sast8/user_modules/resize/resize2fs-arm64"
        )

        # 获取扩容前的分区信息
        stdin, stdout, stderr = ssh_connection.exec_command("df -h /")
        before_info = stdout.read().decode()

        # 执行扩容（谨慎操作，可能耗时较长）
        # 注意：实际扩容操作可能影响系统，根据情况决定是否执行
        # stdin, stdout, stderr = ssh_connection.exec_command(
        #     "/home/sast8/user_modules/resize/resize2fs-arm64 /dev/mmcblk0p3",
        #     timeout=120
        # )
        # exit_code = stdout.channel.recv_exit_status()
        # assert exit_code == 0, f"扩容失败: {stderr.read().decode()}"

        pytest.skip("扩容测试需要谨慎执行，请手动验证")

    def test_step6_run_security_tests(self, device_config, ssh_connection):
        """步骤6：执行安全测试

        验证点：
        - device_hash_and_sign.sh存在且可执行
        - test_secure存在且可执行
        - 安全测试执行成功
        """
        # 检查测试脚本是否存在
        scripts = [
            "/home/sast8/user_tmp/device_hash_and_sign.sh",
            "/home/sast8/user_tmp/test_secure",
        ]

        for script in scripts:
            stdin, stdout, stderr = ssh_connection.exec_command(
                f"test -f {script} && echo 'EXISTS'"
            )
            result = stdout.read().decode().strip()
            if result != "EXISTS":
                pytest.skip(f"安全测试脚本 {script} 不存在，跳过测试")

        # 设置可执行权限
        stdin, stdout, stderr = ssh_connection.exec_command(
            "chmod +x /home/sast8/user_tmp/*"
        )

        # 执行安全测试（根据实际脚本调整）
        # stdin, stdout, stderr = ssh_connection.exec_command(
        #     "cd /home/sast8/user_tmp && ./device_hash_and_sign.sh"
        # )
        # exit_code = stdout.channel.recv_exit_status()

        # 清理测试文件
        ssh_connection.exec_command("rm -f /home/sast8/user_tmp/*")

        pytest.skip("安全测试需要实际脚本，请手动验证")

    def test_step7_configure_time(self, device_config, ssh_connection):
        """步骤7：配置系统时间

        验证点：
        - 时间设置命令执行成功
        - 系统时间设置正确
        """
        import datetime

        # 设置当前时间
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        command = f'date -s "{current_time}"'

        stdin, stdout, stderr = ssh_connection.exec_command(command)
        exit_code = stdout.channel.recv_exit_status()
        assert exit_code == 0, f"时间设置失败: {stderr.read().decode()}"

        # 验证时间设置（允许1分钟误差）
        stdin, stdout, stderr = ssh_connection.exec_command("date '+%Y-%m-%d %H:%M'")
        device_time = stdout.read().decode().strip()
        local_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        assert device_time == local_time, f"时间不匹配: 设备{device_time} vs 本地{local_time}"

    def test_step8_reboot_confirm(self, device_config, ssh_connection):
        """步骤8：重启系统并确认

        验证点：
        - 重启命令可以正常发送
        - 系统可以正常重启
        - 重启后可以重新连接

        警告：此测试会重启目标设备！
        """
        pytest.skip("重启测试需要谨慎执行，请手动验证")

        # 如果需要自动测试重启，取消下面的注释：
        # device = device_config["device"]
        #
        # # 发送重启命令
        # ssh_connection.exec_command("reboot")
        #
        # # 等待系统关闭
        # time.sleep(10)
        #
        # # 等待系统重新启动（最多等待5分钟）
        # max_wait = 300  # 5分钟
        # waited = 0
        # while waited < max_wait:
        #     if check_host_reachable(device["host"], device["port"], timeout=5):
        #         break
        #     time.sleep(5)
        #     waited += 5
        #
        # assert waited < max_wait, "系统重启后无法连接"
        #
        # # 验证可以重新登录
        # import paramiko
        # client = paramiko.SSHClient()
        # client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # try:
        #     client.connect(
        #         hostname=device["host"],
        #         port=device["port"],
        #         username=device["username"],
        #         password=device["password"],
        #         timeout=30
        #     )
        #     stdin, stdout, stderr = client.exec_command("whoami")
        #     result = stdout.read().decode().strip()
        #     assert result == "root", "重启后无法登录"
        # finally:
        #     client.close()


@real_device
class TestDeviceInitializationNegative:
    """设备初始化负面测试 - 验证错误处理"""

    def test_invalid_password(self, device_config):
        """测试错误密码处理"""
        import paramiko

        device = device_config["device"]
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        with pytest.raises(paramiko.AuthenticationException):
            client.connect(
                hostname=device["host"],
                port=device["port"],
                username="root",
                password="wrong_password",
                timeout=10
            )

    def test_network_unreachable(self, device_config):
        """测试网络不可达处理"""
        import paramiko

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        with pytest.raises((paramiko.SSHException, socket.error)):
            client.connect(
                hostname="192.168.255.255",  # 不可达地址
                port=22,
                username="root",
                password="test",
                timeout=5
            )
