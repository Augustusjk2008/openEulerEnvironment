# 集成测试报告

## 概述

本文档描述了针对RT-OpenEuler环境的SSH/SFTP集成测试架构、测试用例和运行方式。

## VM环境信息

### 测试虚拟机配置

| 项目 | 值 |
|------|-----|
| IP地址 | 192.168.56.132 |
| 操作系统 | Ubuntu 20.04 LTS (推荐) |
| SSH端口 | 22 |
| 测试用户 | testuser |
| 测试目录 | /home/testuser/sftp_test |

### 环境要求

- SSH服务已安装并运行
- 测试用户已创建并有sudo权限
- 测试目录已创建并有适当权限
- 网络可达（主机与VM之间）

## 测试文件清单

### 1. VM环境准备文档

**文件**: `docs/vm_setup_guide.md`

包含内容：
- VM基本信息
- SSH服务安装步骤
- 测试用户创建指南
- 测试目录设置
- 连接验证方法
- 故障排除指南

### 2. 集成测试配置

**文件**: `tests/integration/conftest.py`

包含内容：
- `vm_config` fixture: 提供VM连接配置
- `vm_available` fixture: 检查VM是否可达
- `ubuntu_vm` 标记: 控制VM相关测试的执行

### 3. SSH集成测试

**文件**: `tests/integration/test_ssh_workflow.py`

测试类清单：

| 测试类 | 描述 | 测试方法数 |
|--------|------|-----------|
| `TestSSHConnection` | SSH连接测试 | 4 |
| `TestSSHCommandExecution` | 命令执行测试 | 7 |
| `TestSSHAuthenticationFailure` | 认证失败处理 | 2 |
| `TestSSHConnectionRetry` | 连接重试机制 | 1 |

详细测试用例：

#### TestSSHConnection
- `test_ssh_basic_connection_success`: 测试基础SSH连接成功
- `test_ssh_connection_failure_wrong_password`: 测试错误密码连接失败
- `test_ssh_connection_failure_wrong_host`: 测试错误主机连接失败
- `test_ssh_connection_timeout`: 测试连接超时处理

#### TestSSHCommandExecution
- `test_execute_simple_echo`: 测试执行简单echo命令
- `test_execute_pwd`: 测试执行pwd命令
- `test_execute_ls`: 测试执行ls命令
- `test_execute_complex_pipeline`: 测试执行复杂命令（管道）
- `test_execute_with_redirection`: 测试执行带重定向的命令
- `test_execute_command_with_args`: 测试执行带参数的命令
- `test_execute_invalid_command`: 测试执行无效命令
- `test_execute_multiple_commands`: 测试连续执行多个命令

#### TestSSHAuthenticationFailure
- `test_auth_failure_wrong_username`: 测试错误用户名认证失败
- `test_auth_failure_empty_password`: 测试空密码认证失败

#### TestSSHConnectionRetry
- `test_connection_retry_on_failure`: 测试连接失败时的重试行为

### 4. SFTP集成测试

**文件**: `tests/integration/test_sftp_workflow.py`

测试类清单：

| 测试类 | 描述 | 测试方法数 |
|--------|------|-----------|
| `TestSFTPUpload` | 文件上传测试 | 5 |
| `TestSFTPDownload` | 文件下载测试 | 3 |
| `TestSFTPDelete` | 文件删除测试 | 2 |
| `TestSFTPDirectory` | 目录操作测试 | 4 |
| `TestSFTPFilePermissions` | 文件权限测试 | 2 |
| `TestSFTPWorkflow` | 完整工作流测试 | 2 |

详细测试用例：

#### TestSFTPUpload
- `test_upload_small_file`: 测试上传小文件
- `test_upload_binary_file`: 测试上传二进制文件
- `test_upload_large_file`: 测试上传大文件（1MB）
- `test_upload_file_integrity`: 测试上传文件完整性（哈希验证）
- `test_upload_to_nonexistent_directory`: 测试上传到不存在的目录

#### TestSFTPDownload
- `test_download_small_file`: 测试下载小文件
- `test_download_binary_file`: 测试下载二进制文件
- `test_download_nonexistent_file`: 测试下载不存在的文件

#### TestSFTPDelete
- `test_delete_file`: 测试删除文件
- `test_delete_nonexistent_file`: 测试删除不存在的文件

#### TestSFTPDirectory
- `test_list_directory`: 测试列出目录内容
- `test_list_empty_directory`: 测试列出空目录
- `test_create_and_remove_directory`: 测试创建和删除目录

#### TestSFTPFilePermissions
- `test_file_permissions_after_upload`: 测试上传后的文件权限
- `test_change_file_permissions`: 测试修改文件权限

#### TestSFTPWorkflow
- `test_upload_download_delete_workflow`: 测试完整的上传-下载-删除工作流
- `test_multiple_files_transfer`: 测试多个文件传输

## 运行方式说明

### 前置条件

1. 确保VM已启动并可访问
2. 确保测试用户已创建
3. 确保SSH服务正在运行

### 环境变量设置

在运行测试前，需要设置以下环境变量：

```bash
# Linux/macOS
export UBUNTU_VM_AVAILABLE=1
export VM_PASSWORD="your_testuser_password"

# Windows CMD
set UBUNTU_VM_AVAILABLE=1
set VM_PASSWORD=your_testuser_password

# Windows PowerShell
$env:UBUNTU_VM_AVAILABLE=1
$env:VM_PASSWORD="your_testuser_password"
```

### 运行所有集成测试

```bash
# 进入测试目录
cd tests

# 运行所有集成测试
pytest integration/ -v

# 运行并生成HTML报告
pytest integration/ -v --html=reports/integration_report.html
```

### 运行特定测试文件

```bash
# 仅运行SSH测试
pytest integration/test_ssh_workflow.py -v

# 仅运行SFTP测试
pytest integration/test_sftp_workflow.py -v
```

### 运行特定测试类

```bash
# 运行SSH连接测试
pytest integration/test_ssh_workflow.py::TestSSHConnection -v

# 运行SFTP上传测试
pytest integration/test_sftp_workflow.py::TestSFTPUpload -v
```

### 无VM环境下的测试行为

当 `UBUNTU_VM_AVAILABLE` 环境变量未设置时：
- 所有带有 `@ubuntu_vm` 标记的测试会自动跳过
- 测试不会失败，而是显示为 "skipped"
- 控制台会显示跳过原因："需要Ubuntu虚拟机192.168.56.132"

示例输出：
```
tests/integration/test_ssh_workflow.py::TestSSHConnection::test_ssh_basic_connection_success SKIPPED
tests/integration/test_sftp_workflow.py::TestSFTPUpload::test_upload_small_file SKIPPED
```

### 验证VM连接

在运行测试前，可以先验证VM是否可达：

```bash
# 测试SSH连接
ssh testuser@192.168.56.132

# 或使用Python脚本检查
python -c "
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(2)
result = sock.connect_ex(('192.168.56.132', 22))
print('VM is', 'reachable' if result == 0 else 'not reachable')
sock.close()
"
```

## 测试覆盖率

### SSH功能覆盖

- [x] 基础连接建立
- [x] 连接失败处理（错误密码、错误主机）
- [x] 连接超时处理
- [x] 简单命令执行（echo, pwd, ls）
- [x] 复杂命令执行（管道、重定向）
- [x] 认证失败处理
- [x] 连接重试机制

### SFTP功能覆盖

- [x] 小文件上传
- [x] 二进制文件上传
- [x] 大文件上传（1MB）
- [x] 文件完整性验证
- [x] 小文件下载
- [x] 二进制文件下载
- [x] 文件删除
- [x] 目录列表
- [x] 目录创建/删除
- [x] 文件权限验证
- [x] 完整工作流测试

## 故障排除

### 测试被跳过

如果测试被跳过，请检查：
1. `UBUNTU_VM_AVAILABLE` 环境变量是否设置为 `1`
2. VM是否正在运行
3. 网络连接是否正常

### 连接失败

如果连接失败，请检查：
1. VM的IP地址是否正确
2. SSH服务是否正在运行
3. 防火墙设置是否允许SSH连接
4. 用户名和密码是否正确

### 权限问题

如果遇到权限问题，请检查：
1. 测试目录是否存在并有正确的所有权
2. 测试用户是否有写入权限

## 维护说明

### 添加新测试

1. 在相应的测试类中添加新方法
2. 使用 `@ubuntu_vm` 标记需要VM的测试
3. 使用 `sftp_client` 或 `connected_client` fixture获取已连接的客户端
4. 使用 `remote_test_dir` fixture获取临时测试目录

### 修改VM配置

如果需要修改VM配置（如IP地址、用户名等），请更新：
1. `tests/integration/conftest.py` 中的 `vm_config` fixture
2. `docs/vm_setup_guide.md` 中的VM信息
3. 本报告中的VM环境信息
