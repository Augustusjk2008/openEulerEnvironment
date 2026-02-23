# Ubuntu VM测试环境准备指南

## VM信息

- **IP地址**: 192.168.56.132
- **用途**: SSH/SFTP集成测试
- **操作系统**: Ubuntu 20.04 LTS 或更高版本
- **网络**: 与主机在同一局域网内可访问

## 环境准备步骤

### 1. 安装SSH服务

```bash
# 更新软件包列表
sudo apt-get update

# 安装OpenSSH服务器
sudo apt-get install -y openssh-server

# 启用SSH服务开机自启
sudo systemctl enable ssh

# 启动SSH服务
sudo systemctl start ssh

# 验证SSH服务状态
sudo systemctl status ssh
```

### 2. 创建测试用户

```bash
# 创建测试用户
sudo useradd -m testuser

# 设置密码（按提示输入密码）
sudo passwd testuser

# 将用户添加到sudo组（可选，用于需要sudo权限的测试）
sudo usermod -aG sudo testuser
```

### 3. 创建测试目录

```bash
# 创建SFTP测试目录
sudo mkdir -p /home/testuser/sftp_test

# 设置目录所有权
sudo chown testuser:testuser /home/testuser/sftp_test

# 设置目录权限
sudo chmod 755 /home/testuser/sftp_test

# 创建子目录用于不同类型的测试
sudo -u testuser mkdir -p /home/testuser/sftp_test/upload
sudo -u testuser mkdir -p /home/testuser/sftp_test/download
sudo -u testuser mkdir -p /home/testuser/sftp_test/temp
```

### 4. 配置SSH（可选）

编辑SSH配置文件以允许密码认证：

```bash
# 备份原始配置
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup

# 编辑配置
sudo nano /etc/ssh/sshd_config
```

确保以下配置项：
```
PasswordAuthentication yes
PermitRootLogin no
MaxAuthTries 3
```

重启SSH服务：
```bash
sudo systemctl restart ssh
```

### 5. 验证连接

从主机测试SSH连接：

```bash
# 测试SSH连接
ssh testuser@192.168.56.132

# 测试SFTP连接
sftp testuser@192.168.56.132
```

## 测试数据

| 项目 | 值 |
|------|-----|
| 用户名 | testuser |
| 密码 | （实际设置的密码） |
| 测试目录 | /home/testuser/sftp_test |
| SSH端口 | 22 |

## 环境变量配置

在运行集成测试前，设置以下环境变量：

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

## 故障排除

### 无法连接到VM

1. 检查VM网络配置：
   ```bash
   ip addr show
   ```

2. 检查SSH服务是否运行：
   ```bash
   sudo systemctl status ssh
   ```

3. 检查防火墙设置：
   ```bash
   sudo ufw status
   sudo ufw allow 22/tcp
   ```

### 认证失败

1. 确认用户名和密码正确
2. 检查SSH配置允许密码认证
3. 查看认证日志：
   ```bash
   sudo tail -f /var/log/auth.log
   ```

### 权限问题

1. 确认测试目录所有权：
   ```bash
   ls -la /home/testuser/
   ```

2. 确认用户主目录权限：
   ```bash
   sudo chmod 755 /home/testuser
   ```

## 安全注意事项

1. **仅用于测试环境**：此配置仅适用于隔离的测试环境
2. **强密码策略**：为testuser设置强密码
3. **网络隔离**：确保VM在安全的网络环境中
4. **测试后清理**：测试完成后可考虑删除测试用户和数据

## 参考

- [OpenSSH官方文档](https://www.openssh.com/manual.html)
- [Ubuntu SSH指南](https://ubuntu.com/server/docs/service-openssh)
