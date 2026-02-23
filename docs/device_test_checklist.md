# 设备测试检查清单

## 概述

本文档提供设备初始化向导在真实目标板（192.168.1.29）上的手动测试检查清单，用于验证自动化测试无法覆盖的场景或作为自动化测试的补充。

**重要警告**：
- 绝对禁止在 Ubuntu 虚拟机 (192.168.56.132) 执行设备初始化测试
- 设备初始化测试仅针对 192.168.1.29 执行
- 测试前确认目标设备IP地址正确

---

## 一、环境准备检查项

### 1.1 网络环境检查

| 检查项 | 检查方法 | 预期结果 | 状态 |
|--------|----------|----------|------|
| 目标设备IP可达 | `ping 192.168.1.29` | 正常响应，无丢包 | [ ] |
| SSH端口开放 | `telnet 192.168.1.29 22` 或 `nc -zv 192.168.1.29 22` | 连接成功 | [ ] |
| 网络延迟正常 | `ping -c 10 192.168.1.29` | 平均延迟 < 100ms | [ ] |

### 1.2 目标设备状态检查

| 检查项 | 检查方法 | 预期结果 | 状态 |
|--------|----------|----------|------|
| 设备已上电 | 物理检查 | 电源指示灯亮 | [ ] |
| 系统已启动 | SSH登录后执行 `uptime` | 显示运行时间 | [ ] |
| SSH服务运行 | `systemctl status sshd` | 状态为 active (running) | [ ] |
| root用户可用 | `whoami` | 返回 root | [ ] |

### 1.3 测试环境检查

| 检查项 | 检查方法 | 预期结果 | 状态 |
|--------|----------|----------|------|
| Python环境 | `python --version` | Python 3.8+ | [ ] |
| pytest已安装 | `pytest --version` | 显示版本信息 | [ ] |
| paramiko已安装 | `python -c "import paramiko; print(paramiko.__version__)"` | 显示版本信息 | [ ] |
| 环境变量设置 | `echo $REAL_DEVICE_TEST` | 值为 1 | [ ] |
| 密码环境变量 | `echo $DEVICE_PASSWORD` | 显示密码（已设置） | [ ] |

### 1.4 测试文件准备

| 检查项 | 检查方法 | 预期结果 | 状态 |
|--------|----------|----------|------|
| 测试配置文件 | `ls tests/config/device_test_env.yaml` | 文件存在 | [ ] |
| 测试脚本 | `ls tests/e2e/test_device_initializer.py` | 文件存在 | [ ] |
| 上传文件目录 | `ls files_to_upload/` | 目录存在且有内容 | [ ] |

---

## 二、初始化步骤验证清单

### 步骤0：SSH连接验证

| 验证点 | 验证方法 | 预期结果 | 状态 |
|--------|----------|----------|------|
| SSH连接成功 | `ssh root@192.168.1.29` | 登录成功，无错误 | [ ] |
| 认证成功 | 输入密码后 | 进入shell提示符 | [ ] |
| 基本命令执行 | `whoami` | 返回 root | [ ] |
| 系统信息获取 | `uname -a` | 显示ARM64系统信息 | [ ] |

### 步骤1：设置root密码

| 验证点 | 验证方法 | 预期结果 | 状态 |
|--------|----------|----------|------|
| 密码设置命令 | `echo 'root:newpass' \| chpasswd` | 执行成功，无错误 | [ ] |
| 新密码生效 | 退出后使用新密码登录 | 登录成功 | [ ] |
| 密码复杂度 | `passwd --status root` | 显示密码状态 | [ ] |

### 步骤2：创建目录结构

| 验证点 | 验证方法 | 预期结果 | 状态 |
|--------|----------|----------|------|
| /home/sast8存在 | `ls -la /home/sast8` | 目录存在 | [ ] |
| user_tests子目录 | `ls -la /home/sast8/user_tests` | 目录存在 | [ ] |
| user_apps子目录 | `ls -la /home/sast8/user_apps` | 目录存在 | [ ] |
| user_libs子目录 | `ls -la /home/sast8/user_libs` | 目录存在 | [ ] |
| shared_libs子目录 | `ls -la /home/sast8/user_libs/shared_libs` | 目录存在 | [ ] |
| static_libs子目录 | `ls -la /home/sast8/user_libs/static_libs` | 目录存在 | [ ] |
| user_modules子目录 | `ls -la /home/sast8/user_modules` | 目录存在 | [ ] |
| resize子目录 | `ls -la /home/sast8/user_modules/resize` | 目录存在 | [ ] |
| xdma_803子目录 | `ls -la /home/sast8/user_modules/xdma_803` | 目录存在 | [ ] |
| user_tmp子目录 | `ls -la /home/sast8/user_tmp` | 目录存在 | [ ] |
| 目录权限正确 | `stat -c '%a %n' /home/sast8` | 权限为755 | [ ] |

### 步骤3：上传文件验证

| 验证点 | 验证方法 | 预期结果 | 状态 |
|--------|----------|----------|------|
| 文件上传成功 | `scp -r files_to_upload/* root@192.168.1.29:/` | 传输完成 | [ ] |
| 文件完整性 | `find /files_to_upload -type f -exec md5sum {} \;` | 与本地MD5匹配 | [ ] |
| 文件权限保留 | `ls -la /files_to_upload/` | 权限正确 | [ ] |
| 符号链接处理 | `ls -la /files_to_upload/ | grep "->"` | 链接正确 | [ ] |

### 步骤4：配置动态库路径

| 验证点 | 验证方法 | 预期结果 | 状态 |
|--------|----------|----------|------|
| ld.so.conf.d目录 | `ls -la /etc/ld.so.conf.d/` | 目录存在 | [ ] |
| sast8_libs.conf创建 | `cat /etc/ld.so.conf.d/sast8_libs.conf` | 文件存在，内容正确 | [ ] |
| 配置内容正确 | `cat /etc/ld.so.conf.d/sast8_libs.conf` | 包含/home/sast8/user_libs/shared_libs | [ ] |
| ldconfig执行 | `ldconfig` | 执行成功，无错误 | [ ] |
| 库缓存更新 | `ldconfig -p | grep sast8` | 显示缓存的库路径 | [ ] |

### 步骤5：硬盘扩容

| 验证点 | 验证方法 | 预期结果 | 状态 |
|--------|----------|----------|------|
| resize2fs-arm64存在 | `ls -la /home/sast8/user_modules/resize/resize2fs-arm64` | 文件存在 | [ ] |
| 文件可执行 | `file /home/sast8/user_modules/resize/resize2fs-arm64` | 显示可执行文件 | [ ] |
| 分区信息查看 | `df -h /` | 显示当前分区大小 | [ ] |
| 扩容前备份 | - | 已确认数据备份 | [ ] |
| 扩容执行 | `./resize2fs-arm64 /dev/mmcblk0p3` | 执行成功 | [ ] |
| 扩容后验证 | `df -h /` | 分区大小增加 | [ ] |

**警告**：此步骤会修改分区，请确保已备份重要数据！

### 步骤6：执行安全测试

| 验证点 | 验证方法 | 预期结果 | 状态 |
|--------|----------|----------|------|
| device_hash_and_sign.sh存在 | `ls -la /home/sast8/user_tmp/device_hash_and_sign.sh` | 文件存在 | [ ] |
| test_secure存在 | `ls -la /home/sast8/user_tmp/test_secure` | 文件存在 | [ ] |
| 脚本可执行 | `chmod +x /home/sast8/user_tmp/*` | 权限设置成功 | [ ] |
| 哈希签名测试 | `./device_hash_and_sign.sh` | 执行成功 | [ ] |
| 安全测试执行 | `./test_secure` | 执行成功，通过测试 | [ ] |
| 测试日志检查 | `cat /home/sast8/user_tmp/test_*.log` | 日志显示测试通过 | [ ] |
| 清理测试文件 | `rm -f /home/sast8/user_tmp/*` | 文件已清理 | [ ] |

### 步骤7：配置系统时间

| 验证点 | 验证方法 | 预期结果 | 状态 |
|--------|----------|----------|------|
| 时间设置命令 | `date -s "2024-01-01 12:00:00"` | 执行成功 | [ ] |
| 时间验证 | `date` | 显示设置的时间 | [ ] |
| 时区检查 | `date +%Z` | 显示正确时区 | [ ] |
| 硬件时钟同步 | `hwclock --systohc` | 执行成功 | [ ] |
| 时间同步服务 | `systemctl status systemd-timesyncd` | 服务状态正常 | [ ] |

### 步骤8：重启确认

| 验证点 | 验证方法 | 预期结果 | 状态 |
|--------|----------|----------|------|
| 重启前保存工作 | - | 已确认保存 | [ ] |
| 重启命令执行 | `reboot` | 系统开始重启 | [ ] |
| 网络断开确认 | `ping 192.168.1.29` | 无响应 | [ ] |
| 等待系统启动 | 等待2-5分钟 | - | [ ] |
| 网络恢复确认 | `ping 192.168.1.29` | 正常响应 | [ ] |
| SSH重新连接 | `ssh root@192.168.1.29` | 登录成功 | [ ] |
| 系统状态检查 | `uptime` | 显示刚启动 | [ ] |
| 初始化状态保留 | `ls -la /home/sast8` | 目录结构完整 | [ ] |

**警告**：此步骤会重启目标设备，请确保不影响其他测试！

---

## 三、异常处理验证点

### 3.1 网络异常

| 场景 | 验证方法 | 预期行为 | 状态 |
|------|----------|----------|------|
| 连接超时 | 断开网络后执行命令 | 显示超时错误 | [ ] |
| 连接中断 | 测试过程中断开网络 | 显示连接错误 | [ ] |
| 网络恢复 | 恢复网络后重新连接 | 可以重新连接 | [ ] |

### 3.2 认证异常

| 场景 | 验证方法 | 预期行为 | 状态 |
|------|----------|----------|------|
| 错误密码 | 使用错误密码登录 | 认证失败 | [ ] |
| 空密码 | 不输入密码直接回车 | 认证失败 | [ ] |
| 用户锁定 | 多次错误密码后 | 账户可能锁定 | [ ] |

### 3.3 命令执行异常

| 场景 | 验证方法 | 预期行为 | 状态 |
|------|----------|----------|------|
| 命令不存在 | 执行不存在的命令 | 返回错误码127 | [ ] |
| 权限不足 | 非root用户执行特权命令 | 返回权限错误 | [ ] |
| 资源不足 | 磁盘满时创建文件 | 返回空间不足错误 | [ ] |
| 超时处理 | 执行长时间运行的命令 | 正确处理超时 | [ ] |

### 3.4 文件操作异常

| 场景 | 验证方法 | 预期行为 | 状态 |
|------|----------|----------|------|
| 文件不存在 | 读取不存在的文件 | 返回错误 | [ ] |
| 目录不存在 | 写入不存在的目录 | 返回错误 | [ ] |
| 权限拒绝 | 写入只读目录 | 返回权限错误 | [ ] |
| 磁盘满 | 磁盘满时上传文件 | 返回空间不足错误 | [ ] |

---

## 四、手动测试步骤

### 4.1 完整初始化流程手动测试

```bash
# 1. 环境准备
export REAL_DEVICE_TEST=1
export DEVICE_PASSWORD="your_root_password"

# 2. 网络检查
ping -c 4 192.168.1.29

# 3. SSH连接测试
ssh root@192.168.1.29

# 4. 执行初始化步骤（在目标设备上）
# 步骤1: 设置密码
echo 'root:newpassword' | chpasswd

# 步骤2: 创建目录
mkdir -p /home/sast8/{user_tests,user_apps,user_libs/shared_libs,user_libs/static_libs,user_modules/resize,user_modules/xdma_803,user_tmp}

# 步骤3: 上传文件（在本地执行）
scp -r files_to_upload/* root@192.168.1.29:/

# 步骤4: 配置动态库路径
echo '/home/sast8/user_libs/shared_libs' > /etc/ld.so.conf.d/sast8_libs.conf
ldconfig

# 步骤5: 硬盘扩容（谨慎执行）
cd /home/sast8/user_modules/resize
chmod +x resize2fs-arm64
./resize2fs-arm64 /dev/mmcblk0p3

# 步骤6: 执行安全测试
cd /home/sast8/user_tmp
chmod +x *
./device_hash_and_sign.sh
./test_secure
rm -f *

# 步骤7: 配置时间
date -s "$(date '+%Y-%m-%d %H:%M:%S')"

# 步骤8: 重启
reboot
```

### 4.2 自动化测试执行

```bash
# 执行所有设备测试
pytest tests/e2e/test_device_initializer.py -v

# 执行特定步骤测试
pytest tests/e2e/test_device_initializer.py::TestDeviceInitialization::test_step2_create_directory_structure -v

# 生成测试报告
pytest tests/e2e/test_device_initializer.py -v --html=tests/reports/device_test_report.html
```

---

## 五、测试完成确认

### 5.1 测试通过标准

- [ ] 所有环境准备检查项通过
- [ ] 所有8个初始化步骤验证通过
- [ ] 异常处理验证点通过
- [ ] 手动测试步骤执行无错误
- [ ] 自动化测试全部通过

### 5.2 测试报告内容

测试完成后，报告应包含：
1. 测试环境信息（目标设备IP、系统版本等）
2. 测试执行摘要（通过/失败数量）
3. 失败的测试项及错误信息
4. 异常处理验证结果
5. 发现的问题及建议

### 5.3 后续行动

- [ ] 修复发现的缺陷
- [ ] 更新测试用例
- [ ] 更新文档
- [ ] 归档测试报告

---

## 六、参考文档

- [设备测试计划](device_test_plan.md)
- [测试环境配置](../tests/config/device_test_env.yaml)
- [初始化界面源码](../src/ui/interfaces/initializer_interface.py)
- [pytest文档](https://docs.pytest.org/)
- [paramiko文档](https://www.paramiko.org/)
