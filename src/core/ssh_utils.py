"""
SSH 连接工具模块
提供统一的SSH连接、配置和工作线程实现
"""

import paramiko
from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
from typing import Optional, Dict, Any, Callable, Tuple, List


class SSHConfig:
    """SSH配置类，从配置管理器读取配置"""

    @staticmethod
    def from_config_manager(config_manager, prefix: str = "ssh") -> Dict[str, str]:
        """
        从配置管理器读取SSH配置

        Args:
            config_manager: 配置管理器实例
            prefix: 配置前缀，"ssh" 或 "ftp"

        Returns:
            包含 host, username, password 的字典
        """
        return {
            "host": config_manager.get(f"{prefix}_host", ""),
            "username": config_manager.get(f"{prefix}_username", ""),
            "password": config_manager.get(f"{prefix}_password", ""),
        }

    @staticmethod
    def validate(config: Dict[str, str]) -> Tuple[bool, str]:
        """
        验证SSH配置是否完整

        Args:
            config: 包含 host, username, password 的配置字典

        Returns:
            (是否有效, 错误信息)
        """
        if not config.get("host"):
            return False, "主机地址不能为空"
        if not config.get("username"):
            return False, "用户名不能为空"
        if not config.get("password"):
            return False, "密码不能为空"
        return True, ""


class SSHClientFactory:
    """SSH客户端工厂类，统一创建和配置SSHClient"""

    @staticmethod
    def create_client() -> paramiko.SSHClient:
        """创建并配置基础的SSHClient"""
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        return client

    @staticmethod
    def build_connect_kwargs(
        host: str,
        username: str,
        password: Optional[str] = None,
        timeout: int = 10,
        **extra_kwargs
    ) -> Dict[str, Any]:
        """
        构建连接参数字典

        Args:
            host: 主机地址
            username: 用户名
            password: 密码（可选）
            timeout: 连接超时时间
            **extra_kwargs: 额外的连接参数

        Returns:
            连接参数字典
        """
        kwargs = {
            "hostname": host,
            "username": username,
            "timeout": timeout,
        }
        if password:
            kwargs.update({
                "password": password,
                "look_for_keys": False,
                "allow_agent": False,
            })
        kwargs.update(extra_kwargs)
        return kwargs

    @classmethod
    def connect(
        cls,
        host: str,
        username: str,
        password: Optional[str] = None,
        timeout: int = 10,
        **extra_kwargs
    ) -> paramiko.SSHClient:
        """
        创建SSH连接

        Args:
            host: 主机地址
            username: 用户名
            password: 密码（可选）
            timeout: 连接超时时间
            **extra_kwargs: 额外的连接参数

        Returns:
            已连接的SSHClient实例
        """
        client = cls.create_client()
        kwargs = cls.build_connect_kwargs(host, username, password, timeout, **extra_kwargs)
        client.connect(**kwargs)
        return client


class SSHConnectionContext:
    """SSH连接上下文管理器，确保资源正确关闭"""

    def __init__(self, client: Optional[paramiko.SSHClient] = None):
        self.client = client
        self.sftp = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def open_sftp(self) -> paramiko.SFTPClient:
        """打开SFTP会话"""
        if self.client is None:
            raise RuntimeError("SSH client is not connected")
        self.sftp = self.client.open_sftp()
        return self.sftp

    def close(self):
        """关闭所有资源"""
        if self.sftp is not None:
            try:
                self.sftp.close()
            except Exception:
                pass
            self.sftp = None
        if self.client is not None:
            try:
                self.client.close()
            except Exception:
                pass
            self.client = None


class BaseSSHWorker(QObject):
    """SSH工作线程基类"""

    finished = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, host: str, username: str, password: str, timeout: int = 10):
        super().__init__()
        self.host = host
        self.username = username
        self.password = password
        self.timeout = timeout
        self._client: Optional[paramiko.SSHClient] = None

    def get_client(self) -> paramiko.SSHClient:
        """获取或创建SSH客户端"""
        if self._client is None:
            self._client = SSHClientFactory.connect(
                self.host, self.username, self.password, self.timeout
            )
        return self._client

    def close_client(self):
        """关闭SSH客户端"""
        if self._client is not None:
            try:
                self._client.close()
            except Exception:
                pass
            self._client = None

    def safe_close(self, client: Optional[paramiko.SSHClient] = None):
        """安全关闭客户端（不抛出异常）"""
        target = client if client is not None else self._client
        if target is not None:
            try:
                target.close()
            except Exception:
                pass
        if client is None:
            self._client = None

    def translate_exception(self, exc: Exception) -> str:
        """将异常转换为用户友好的错误信息"""
        if isinstance(exc, paramiko.BadHostKeyException):
            return f"主机密钥验证失败: {exc}"
        elif isinstance(exc, paramiko.AuthenticationException):
            return f"认证失败: 用户名或密码错误"
        elif isinstance(exc, paramiko.SSHException):
            return f"SSH连接错误: {exc}"
        elif isinstance(exc, TimeoutError):
            return f"连接超时，请检查网络或主机地址"
        else:
            return f"连接失败: {exc}"


class SSHConnectWorker(BaseSSHWorker):
    """通用SSH连接工作线程"""

    connected = pyqtSignal(object)  # 发射 SSHClient
    auth_failed = pyqtSignal(str)
    host_key_error = pyqtSignal(str)

    def __init__(self, host: str, username: str, password: str, timeout: int = 10):
        super().__init__(host, username, password, timeout)
        self._client_for_emit: Optional[paramiko.SSHClient] = None

    @pyqtSlot()
    def run(self):
        client = None
        try:
            client = SSHClientFactory.connect(
                self.host, self.username, self.password, self.timeout
            )
            self._client_for_emit = client
            self.connected.emit(client)
            # 发射后将所有权转移给接收者
            client = None
            self._client_for_emit = None
        except paramiko.BadHostKeyException as exc:
            self.safe_close(client)
            self.host_key_error.emit(str(exc))
            self.auth_failed.emit(f"主机密钥异常: {exc}")
        except paramiko.AuthenticationException as exc:
            self.safe_close(client)
            self.auth_failed.emit(str(exc))
            self.error_occurred.emit(f"认证失败: {exc}")
        except Exception as exc:
            self.safe_close(client)
            error_msg = self.translate_exception(exc)
            self.error_occurred.emit(error_msg)
        finally:
            self.finished.emit()


class SFTPTransferWorker(QThread):
    """通用SFTP文件传输工作线程"""

    progress_updated = pyqtSignal(int, int)  # 当前, 总数
    status_updated = pyqtSignal(str)
    transfer_finished = pyqtSignal(bool, str)

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        action: str,  # "upload" or "download"
        local_path: str,
        remote_path: str,
        delete_source: bool = False,
        timeout: int = 30
    ):
        super().__init__()
        self.host = host
        self.username = username
        self.password = password
        self.timeout = timeout
        self.action = action
        self.local_path = local_path
        self.remote_path = remote_path
        self.delete_source = delete_source

    @pyqtSlot()
    def run(self):
        ssh = None
        sftp = None
        try:
            self.status_updated.emit("正在连接服务器...")
            ssh = SSHClientFactory.connect(
                self.host, self.username, self.password, self.timeout
            )
            sftp = ssh.open_sftp()

            if self.action == "upload":
                self._upload(sftp, self.local_path, self.remote_path)
            elif self.action == "download":
                self._download(sftp, self.remote_path, self.local_path)
            else:
                raise ValueError(f"未知的传输类型: {self.action}")

            # 删除源文件（如果是移动操作）
            if self.delete_source:
                if self.action == "upload":
                    self._delete_local(self.local_path)
                else:
                    self._delete_remote(sftp, self.remote_path)

            self.transfer_finished.emit(True, "传输完成")
        except paramiko.BadHostKeyException as exc:
            error_msg = f"传输失败: 主机密钥验证失败: {exc}"
            self.transfer_finished.emit(False, error_msg)
        except paramiko.AuthenticationException as exc:
            error_msg = f"传输失败: 认证失败，请检查用户名或密码"
            self.transfer_finished.emit(False, error_msg)
        except paramiko.SSHException as exc:
            error_msg = f"传输失败: SSH错误: {exc}"
            self.transfer_finished.emit(False, error_msg)
        except (IOError, OSError) as exc:
            error_msg = f"传输失败: I/O错误: {exc}"
            self.transfer_finished.emit(False, error_msg)
        except Exception as exc:
            error_msg = f"传输失败: {exc}"
            self.transfer_finished.emit(False, error_msg)
        finally:
            if sftp is not None:
                try:
                    sftp.close()
                except Exception:
                    pass
            if ssh is not None:
                try:
                    ssh.close()
                except Exception:
                    pass
            self.finished.emit()

    def _ensure_remote_dir(self, sftp: paramiko.SFTPClient, remote_path: str):
        """确保远程目录存在"""
        import posixpath
        if remote_path in ("", "/"):
            return
        parts = remote_path.strip("/").split("/")
        current = ""
        for part in parts:
            current = f"{current}/{part}" if current else f"/{part}"
            try:
                sftp.stat(current)
            except Exception:
                sftp.mkdir(current)

    def _upload(self, sftp: paramiko.SFTPClient, local_path: str, remote_path: str):
        """上传文件或目录"""
        import os
        import posixpath
        import stat as stat_module

        if os.path.isdir(local_path):
            self._ensure_remote_dir(sftp, remote_path)
            total_files = self._count_local_files(local_path)
            current = 0
            for root, _, files in os.walk(local_path):
                rel = os.path.relpath(root, local_path)
                rel = "" if rel == "." else rel.replace("\\", "/")
                target_dir = remote_path if not rel else posixpath.join(remote_path, rel)
                self._ensure_remote_dir(sftp, target_dir)
                for filename in files:
                    current += 1
                    self.progress_updated.emit(current, total_files)
                    self.status_updated.emit(f"上传 {filename} ({current}/{total_files})")
                    local_file = os.path.join(root, filename)
                    remote_file = posixpath.join(target_dir, filename)
                    sftp.put(local_file, remote_file)
        else:
            remote_dir = posixpath.dirname(remote_path)
            self._ensure_remote_dir(sftp, remote_dir)
            self.status_updated.emit(f"上传 {os.path.basename(local_path)}")
            sftp.put(local_path, remote_path)
            self.progress_updated.emit(1, 1)

    def _download(self, sftp: paramiko.SFTPClient, remote_path: str, local_path: str):
        """下载文件或目录"""
        import os
        import posixpath
        import stat as stat_module

        info = sftp.stat(remote_path)
        if stat_module.S_ISDIR(info.st_mode):
            os.makedirs(local_path, exist_ok=True)
            entries = sftp.listdir_attr(remote_path)
            total = len(entries)
            for i, entry in enumerate(entries):
                remote_child = posixpath.join(remote_path, entry.filename)
                local_child = os.path.join(local_path, entry.filename)
                self.progress_updated.emit(i + 1, total)
                self.status_updated.emit(f"下载 {entry.filename} ({i+1}/{total})")
                if stat_module.S_ISDIR(entry.st_mode):
                    self._download(sftp, remote_child, local_child)
                else:
                    os.makedirs(os.path.dirname(local_child), exist_ok=True)
                    sftp.get(remote_child, local_child)
        else:
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            self.status_updated.emit(f"下载 {os.path.basename(remote_path)}")
            sftp.get(remote_path, local_path)
            self.progress_updated.emit(1, 1)

    def _delete_local(self, local_path: str):
        """删除本地文件或目录"""
        import os
        import shutil
        if os.path.isdir(local_path):
            shutil.rmtree(local_path)
        else:
            os.remove(local_path)

    def _delete_remote(self, sftp: paramiko.SFTPClient, remote_path: str):
        """删除远程文件或目录"""
        import posixpath
        import stat as stat_module

        try:
            info = sftp.stat(remote_path)
        except Exception:
            return
        if stat_module.S_ISDIR(info.st_mode):
            for entry in sftp.listdir_attr(remote_path):
                child = posixpath.join(remote_path, entry.filename)
                if stat_module.S_ISDIR(entry.st_mode):
                    self._delete_remote(sftp, child)
                else:
                    sftp.remove(child)
            sftp.rmdir(remote_path)
        else:
            sftp.remove(remote_path)

    def _count_local_files(self, local_path: str) -> int:
        """统计本地文件数量"""
        import os
        if os.path.isfile(local_path):
            return 1
        count = 0
        for _, _, files in os.walk(local_path):
            count += len(files)
        return count


class SSHCommandWorker(QThread):
    """SSH命令执行工作线程"""

    command_started = pyqtSignal(str)  # 命令描述
    command_output = pyqtSignal(str)   # 命令输出
    command_error = pyqtSignal(str)    # 错误输出
    command_finished = pyqtSignal(str, int)  # 命令描述, 退出码
    all_finished = pyqtSignal(bool, str)  # 是否成功, 消息
    finished = pyqtSignal()

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        commands: list,  # [(step_name, command, needs_chmod), ...]
        timeout: int = 30
    ):
        super().__init__()
        self.host = host
        self.username = username
        self.password = password
        self.timeout = timeout
        self.commands = commands

    @pyqtSlot()
    def run(self):
        ssh = None
        try:
            self.command_output.emit("正在连接SSH服务器...")
            ssh = SSHClientFactory.connect(
                self.host, self.username, self.password, self.timeout
            )
            self.command_output.emit("SSH连接成功")

            for i, (step_name, command, needs_chmod) in enumerate(self.commands, 1):
                self.command_started.emit(step_name)
                self.command_output.emit(f"\n[{i}/{len(self.commands)}] {step_name}")

                if needs_chmod and command.startswith('./'):
                    chmod_cmd = f"chmod +x {command}"
                    ssh.exec_command(chmod_cmd)

                self.command_output.emit(f"执行: {command}")
                stdin, stdout, stderr = ssh.exec_command(command)
                output = stdout.read().decode('utf-8', errors='replace')
                error = stderr.read().decode('utf-8', errors='replace')
                exit_status = stdout.channel.recv_exit_status()

                if output:
                    self.command_output.emit(f"输出: {output}")
                if error:
                    self.command_error.emit(f"错误: {error}")

                if exit_status != 0:
                    raise Exception(f"命令执行失败，退出码: {exit_status}")

                self.command_output.emit(f"✓ {step_name} 完成")

            self.all_finished.emit(True, "所有命令执行完成")
        except paramiko.BadHostKeyException as exc:
            error_msg = f"主机密钥验证失败: {exc}"
            self.command_error.emit(error_msg)
            self.all_finished.emit(False, error_msg)
        except paramiko.AuthenticationException as exc:
            error_msg = f"认证失败: 用户名或密码错误"
            self.command_error.emit(error_msg)
            self.all_finished.emit(False, error_msg)
        except paramiko.SSHException as exc:
            error_msg = f"SSH连接错误: {exc}"
            self.command_error.emit(error_msg)
            self.all_finished.emit(False, error_msg)
        except Exception as exc:
            error_msg = f"命令执行失败: {exc}"
            self.command_error.emit(error_msg)
            self.all_finished.emit(False, error_msg)
        finally:
            if ssh is not None:
                try:
                    ssh.close()
                except Exception:
                    pass
            self.finished.emit()
