# 设备测试计划

## 1. 测试目标

验证**设备初始化向导**在真实目标板（IP: 192.168.1.29）上的功能完整性和可靠性。

### 关键目标
- 确保8步初始化流程在真实硬件上正确执行
- 验证SSH连接稳定性和文件传输功能
- 确认系统配置命令在目标板上生效
- 确保初始化后的系统状态符合预期

## 2. 测试范围

### 2.1 包含的测试项

| 步骤 | 测试项 | 描述 |
|------|--------|------|
| 步骤1 | 设置root密码 | 验证root用户密码设置功能 |
| 步骤2 | 创建目录结构 | 验证/home/sast8目录结构创建 |
| 步骤3 | 上传文件 | 验证文件上传到目标设备功能 |
| 步骤4 | 配置动态库路径 | 验证ld.so.conf.d配置和ldconfig执行 |
| 步骤5 | 硬盘扩容 | 验证resize2fs-arm64执行和分区扩展 |
| 步骤6 | 执行安全测试 | 验证device_hash_and_sign.sh和test_secure执行 |
| 步骤7 | 配置系统时间 | 验证系统时间设置功能 |
| 步骤8 | 重启确认 | 验证系统重启功能及重启后状态检查 |

### 2.2 不包含的测试项

- Ubuntu虚拟机（192.168.56.132）上的任何测试
- 其他IP地址的设备测试
- 非root用户的初始化测试

## 3. 环境要求

### 3.1 硬件要求

| 项目 | 要求 |
|------|------|
| 目标设备 | 真实目标板（ARM64架构） |
| IP地址 | 192.168.1.29 |
| 网络 | 测试主机与目标设备网络可达 |
| SSH端口 | 22（默认） |

### 3.2 软件要求

| 项目 | 要求 |
|------|------|
| Python | 3.8+ |
| pytest | 7.0+ |
| paramiko | 用于SSH连接 |
| 环境变量 | REAL_DEVICE_TEST=1 |
| 密码环境变量 | DEVICE_PASSWORD（root密码） |

### 3.3 前置条件

1. 目标设备已上电并启动
2. 目标设备网络配置正确（192.168.1.29）
3. SSH服务已启用
4. root用户可登录
5. 已知root密码

## 4. 测试策略

### 4.1 标记策略

所有设备初始化测试必须使用 `@real_device` 标记：

```python
import pytest
import os

real_device = pytest.mark.skipif(
    not os.environ.get("REAL_DEVICE_TEST"),
    reason="需要真实目标板192.168.1.29（设置REAL_DEVICE_TEST=1启用）"
)

@real_device
class TestDeviceInitialization:
    """设备初始化向导测试 - 仅在真实设备执行"""
    pass
```

### 4.2 执行策略

| 场景 | 行为 |
|------|------|
| 无REAL_DEVICE_TEST环境变量 | 自动跳过所有@real_device测试 |
| REAL_DEVICE_TEST=1 | 执行设备初始化测试 |
| REAL_DEVICE_TEST=0 | 自动跳过所有@real_device测试 |

### 4.3 安全策略

**重要警告**：
- 绝对禁止在Ubuntu虚拟机（192.168.56.132）执行设备初始化测试
- 设备初始化测试仅针对192.168.1.29执行
- 测试前确认目标设备IP地址正确
- 测试过程中可能重启目标设备，确保不影响其他测试

## 5. 测试执行

### 5.1 执行命令

```bash
# 设置环境变量并执行测试
export REAL_DEVICE_TEST=1
export DEVICE_PASSWORD="your_root_password"
pytest tests/e2e/test_device_initializer.py -v

# 仅执行设备测试
pytest tests/e2e/test_device_initializer.py -v -m real_device

# 排除设备测试（默认行为）
pytest tests/ -v --ignore=tests/e2e/test_device_initializer.py
```

### 5.2 预期结果

| 测试项 | 预期结果 |
|--------|----------|
| SSH连接 | 成功建立SSH连接 |
| 密码设置 | root密码设置成功 |
| 目录创建 | /home/sast8目录结构完整 |
| 文件上传 | 文件成功上传到目标路径 |
| 库路径配置 | ld.so.conf.d/sast8_libs.conf创建，ldconfig执行成功 |
| 硬盘扩容 | resize2fs-arm64执行成功，分区扩展完成 |
| 安全测试 | device_hash_and_sign.sh和test_secure执行完成 |
| 时间配置 | 系统时间设置正确 |
| 重启 | 系统成功重启并可重新连接 |

## 6. 风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 目标设备不可达 | 测试失败 | 测试前验证网络连通性 |
| 密码错误 | 认证失败 | 确认密码环境变量设置正确 |
| 硬盘扩容失败 | 存储空间不足 | 检查分区状态和resize2fs日志 |
| 安全测试失败 | 安全状态异常 | 检查测试脚本和依赖文件 |
| 系统无法重启 | 设备无法恢复 | 准备物理访问或远程管理手段 |

## 7. 测试报告

测试完成后生成报告，包含：
- 测试执行摘要
- 通过的测试项
- 失败的测试项及错误信息
- 目标设备状态信息
- 建议和改进措施

## 8. 相关文档

- [设备测试检查清单](device_test_checklist.md) - 手动验证步骤
- [测试环境配置](../tests/config/device_test_env.yaml) - 设备连接配置
- [初始化界面源码](../src/ui/interfaces/initializer_interface.py) - 8步初始化流程参考
