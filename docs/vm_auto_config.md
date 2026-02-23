# VM自动配置文档

**配置日期**: 2026-02-16
**配置状态**: 已完成

---

## 配置概述

已配置SSH免密登录，实现自动化测试执行，无需手动输入密码。

---

## 配置步骤

### 1. 生成SSH密钥对

```bash
ssh-keygen -t rsa -b 4096 -C "test@openEuler" -f ~/.ssh/id_rsa -N ""
```

生成的文件：
- `~/.ssh/id_rsa` - 私钥（本地保留）
- `~/.ssh/id_rsa.pub` - 公钥（复制到VM）

### 2. 配置VM免密登录

```bash
cat ~/.ssh/id_rsa.pub | ssh jiangkai@192.168.56.132 "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys"
```

### 3. 验证免密登录

```bash
ssh -o PasswordAuthentication=no jiangkai@192.168.56.132 "echo 'SSH免密登录成功'"
```

**结果**: 无需输入密码即可连接

---

## 测试配置变更

### tests/integration/conftest.py

**变更1**: 自动检测VM可用性

```python
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
```

**变更2**: 自动设置环境变量

```python
_VM_AVAILABLE = _is_vm_available()
if _VM_AVAILABLE:
    os.environ["UBUNTU_VM_AVAILABLE"] = "1"
```

**变更3**: 使用SSH密钥而非密码

```python
return {
    "host": "192.168.56.132",
    "port": 22,
    "username": "jiangkai",
    "password": None,  # 使用SSH密钥
    "key_filename": os.path.expanduser("~/.ssh/id_rsa"),
    "test_dir": "/home/jiangkai/sftp_test",
}
```

### tests/config/test_env.yaml

```yaml
ubuntu_vm:
  host: "192.168.56.132"
  port: 22
  username: "jiangkai"
  private_key: "~/.ssh/id_rsa"  # 使用密钥认证
```

---

## 自动化脚本

### run_tests.bat (CMD)

功能：
1. 自动激活conda环境
2. 自动检测VM连接
3. 自动设置UBUNTU_VM_AVAILABLE环境变量
4. 依次执行各类测试

使用方法：
```cmd
run_tests.bat
```

### run_tests.ps1 (PowerShell)

功能：
1. 更完善的彩色输出
2. 自动检测VM并执行集成测试
3. 生成覆盖率报告
4. 详细的测试结果汇总

使用方法：
```powershell
.\run_tests.ps1
```

---

## 测试执行

### 手动执行（自动检测VM）

```bash
# 进入项目目录
cd H:\WorkSpace\PythonWorkspace\openEulerEnvironment

# 激活conda环境
conda activate pyqt5_env

# 运行测试（自动检测VM）
pytest tests/integration/ -v
```

### 使用自动化脚本

```bash
# CMD
run_tests.bat

# PowerShell
.\run_tests.ps1
```

---

## 验证配置

### 1. 验证SSH免密登录

```bash
ssh jiangkai@192.168.56.132 "echo '连接成功'"
```

**预期**: 无需输入密码直接显示"连接成功"

### 2. 验证集成测试执行

```bash
pytest tests/integration/test_ssh_workflow.py::TestSSHConnection::test_ssh_basic_connection_success -v
```

**预期**: 测试通过，不再是"skipped"

### 3. 验证SFTP目录

```bash
ssh jiangkai@192.168.56.132 "ls -la /home/jiangkai/sftp_test"
```

**预期**: 目录存在且权限正确

---

## 故障排除

### 问题: SSH免密登录失败

**检查**:
1. 私钥文件存在：`ls -la ~/.ssh/id_rsa`
2. 公钥在VM上：`ssh jiangkai@192.168.56.132 "cat ~/.ssh/authorized_keys"`
3. 权限正确：`chmod 600 ~/.ssh/authorized_keys`

**修复**:
```bash
# 重新复制公钥
ssh-copy-id jiangkai@192.168.56.132
```

### 问题: 集成测试仍被跳过

**检查**:
1. VM是否运行：`ping 192.168.56.132`
2. SSH服务是否运行：`ssh jiangkai@192.168.56.132 "sudo systemctl status ssh"`
3. 测试配置是否正确：`cat tests/config/test_env.yaml`

**手动设置环境变量**:
```bash
set UBUNTU_VM_AVAILABLE=1
pytest tests/integration/ -v
```

---

## 预期结果

修复后执行测试：

```bash
pytest tests/integration/ -v
```

**预期输出**:
```
tests/integration/test_ssh_workflow.py::TestSSHConnection::test_ssh_basic_connection_success PASSED
tests/integration/test_ssh_workflow.py::TestSSHConnection::test_ssh_connection_failure_wrong_password PASSED
...
tests/integration/test_sftp_workflow.py::TestSFTPUpload::test_upload_small_file PASSED
...
```

所有32个集成测试应该通过。
