# Agent Team 测试任务规划

## 项目背景

**RTopenEuler系统管理工具** - 基于PyQt5的桌面应用，面向openEuler嵌入式开发环境，功能包括：
- 开发环境配置安装
- 自动代码生成
- SSH远程终端
- FTP文件传输
- 设备初始化向导（**仅在真实目标板测试**）
- 数据可视化（SLOG文件解析）
- 协议编辑器
- 算法编辑器

## 技术环境

| 项目 | 说明 |
|------|------|
| 操作系统 | Windows 7/10/11 |
| Python版本 | 3.8 (conda虚拟环境 pyqt5_env) |
| GUI框架 | PyQt5 5.15.9 + qfluentwidgets |
| 网络库 | paramiko 3.3.1 (SSH/SFTP) |
| 绘图库 | matplotlib |
| 构建工具 | PyInstaller (打包为exe) |
| 运行方式 | `run.bat dev` 或 `run.bat simple` |

## 测试环境说明

### 目标生产环境
- **远端设备**: 192.168.1.29 嵌入式Linux CCU设备
- **系统**: RTopenEuler / openEuler 嵌入式
- **架构**: ARM64 (瑞芯微 RK3588)
- **用途**: SSH终端、FTP文件操作

### 实际测试环境
- **可用设备**: 192.168.56.132 Ubuntu虚拟机
- **系统**: Ubuntu (x86_64)
- **用途**: SSH/SFTP基础功能测试

### 测试范围划分

| 功能模块 | 测试环境 | 说明 |
|----------|----------|------|
| SSH基础连接 | Ubuntu虚拟机 | 验证连接、认证逻辑 |
| SFTP文件传输 | Ubuntu虚拟机 | 上传/下载/删除等基础操作 |
| 远程终端 | Ubuntu虚拟机 | 命令执行、输出获取 |
| 代码生成 | 本地（Windows） | 模板渲染、文件生成 |
| **设备初始化向导** | **192.168.1.29真实设备** | **不在虚拟机测试（环境差异大）** |
| SLOG解析 | 本地（Windows） | 文件解析、数据处理 |
| 协议/算法编辑器 | 本地（Windows） | UI交互、数据验证 |

### 设备初始化向导测试策略

**为什么不在Ubuntu虚拟机测试？**

设备初始化向导执行以下操作：
- 设置root密码
- 创建目录结构
- 上传必要文件
- 配置动态库路径
- 硬盘分区扩容
- 运行安全测试
- 配置系统时间并重启

这些操作高度依赖目标设备的特定环境：
| 差异项 | 目标设备 (192.168.1.29) | Ubuntu虚拟机 (192.168.56.132) |
|--------|------------------------|------------------------------|
| 架构 | ARM64 (瑞芯微RK3588) | x86_64 |
| 系统 | RTopenEuler | Ubuntu |
| 分区布局 | 嵌入式特定分区 | 标准分区 |
| 启动方式 | U-Boot | GRUB |
| 系统服务 | 嵌入式定制服务 | 标准systemd |
| 危险操作 | 可接受（出厂初始化） | 会损坏系统 |

**测试策略：**
1. **单元测试**: 仅测试初始化向导的UI逻辑、命令组装逻辑（Mock SSH执行）
2. **集成测试**: 跳过 - 不在虚拟机执行
3. **验收测试**: 在192.168.1.29真实设备上手动/自动化测试

## 任务优先级规划

### Phase 1: 测试基础设施搭建（最高优先级）
**目标**: 建立可运行的测试框架，能执行并能生成报告

| 任务ID | 任务名称 | 说明 | 预计输出 |
|--------|----------|------|----------|
| P1-T1 | pytest框架搭建 | 配置pytest.ini、conftest.py，支持Qt测试 | tests/conftest.py, pytest.ini |
| P1-T2 | 测试目录结构创建 | 按unit/integration/e2e组织测试代码 | tests/目录结构 |
| P1-T3 | 基础fixtures开发 | 提供QApplication、MockConfig、测试环境配置等fixture | tests/fixtures/ |
| P1-T4 | CI报告集成 | 配置覆盖率、Allure报告生成 | .github/workflows/ |
| P1-T5 | 测试环境配置 | 配置192.168.56.132连接参数 | tests/config/test_env.yaml |

### Phase 2: 核心模块单元测试（高优先级）
**目标**: 覆盖src/core/下所有核心逻辑模块

| 任务ID | 任务名称 | 测试目标 | 优先级 |
|--------|----------|----------|--------|
| P2-T1 | config_manager测试 | 配置读写、默认值、异常处理 | P0 |
| P2-T2 | ssh_utils测试 | SSHConfig、SSHClientFactory、Mock连接 | P0 |
| P2-T3 | slog_parser测试 | SLOG文件解析、各种数据类型 | P1 |
| P2-T4 | auth_manager测试 | 登录验证、邀请码校验 | P1 |
| P2-T5 | protocol_schema测试 | 协议模式解析、验证 | P2 |
| P2-T6 | autopilot_codegen测试 | 代码生成逻辑 | P2 |
| P2-T7 | 初始化向导UI逻辑测试 | 界面状态、命令组装（Mock SSH） | P1 |

### Phase 3: 集成测试（中优先级）
**目标**: 测试模块间交互和完整流程

| 任务ID | 任务名称 | 测试场景 | 环境要求 |
|--------|----------|----------|----------|
| P3-T1 | SSH基础流程测试 | 连接→执行简单命令→断开 | Ubuntu虚拟机 |
| P3-T2 | SFTP文件传输测试 | 上传/下载/删除文件 | Ubuntu虚拟机 |
| P3-T3 | 代码生成流程测试 | 选择模板→生成文件→验证输出 | 本地 |

**注意**: 设备初始化向导不在此阶段测试

### Phase 4: UI自动化测试（中优先级）
**目标**: 使用pytest-qt测试界面交互

| 任务ID | 任务名称 | 测试范围 |
|--------|----------|----------|
| P4-T1 | 登录界面测试 | 输入验证、登录流程、错误提示 |
| P4-T2 | 设置界面测试 | 配置修改、保存、重置 |
| P4-T3 | 主窗口导航测试 | 页面切换、状态保持 |
| P4-T4 | 初始化向导界面测试 | 步骤切换、参数验证、日志显示（不连接真实设备） |

### Phase 5: 真实设备测试（验收阶段）
**目标**: 在192.168.1.29上验证设备初始化向导

| 任务ID | 任务名称 | 测试场景 | 环境要求 |
|--------|----------|----------|----------|
| P5-T1 | 设备初始化流程 | 完整初始化向导执行 | **192.168.1.29** |
| P5-T2 | 初始化异常处理 | 网络中断、命令失败恢复 | **192.168.1.29** |
| P5-T3 | 初始化后验证 | 检查配置是否正确应用 | **192.168.1.29** |

## 测试数据管理

```
tests/
├── fixtures/
│   ├── data/
│   │   ├── sample.slog          # 标准SLOG测试文件
│   │   ├── empty.slog           # 边界测试：空文件
│   │   └── corrupted.slog       # 异常测试：损坏文件
│   ├── mocks/
│   │   ├── mock_ssh_server.py   # SSH服务器Mock
│   │   └── mock_config.py       # 配置Mock
│   └── templates/
│       └── test_templates/      # 代码生成测试模板
```

## Mock策略

| 依赖项 | Mock方案 | 说明 |
|--------|----------|------|
| SSH连接 | paramiko.Transport Mock | 基础Mock用于单元测试 |
| Ubuntu设备 | 真实连接 | 集成测试使用192.168.56.132 |
| SFTP操作 | 临时目录模拟 | 使用pytest tmp_path |
| 配置文件 | 临时JSON文件 | pytest tmp_path fixture |
| Qt对话框 | QDialog.exec_ Mock | 模拟用户点击 |
| 初始化向导SSH | Mock exec_command | 仅验证命令组装，不执行 |

## 覆盖率目标

| 模块 | 目标覆盖率 | 说明 |
|------|-----------|------|
| config_manager | 90% | 核心业务逻辑 |
| ssh_utils | 85% | 网络连接核心 |
| slog_parser | 80% | 数据解析 |
| auth_manager | 75% | 认证相关 |
| ui/interfaces | 60% | 界面交互 |
| 初始化向导 | 50% | 仅UI逻辑和命令组装 |
| 整体 | 70% | 全项目平均 |

## 执行计划

### Week 1: 基础设施
- 完成Phase 1所有任务
- 配置Ubuntu虚拟机连接参数
- 确保`pytest`命令可正常运行
- 输出第一份覆盖率报告

### Week 2-3: 核心模块
- 完成Phase 2所有P0、P1任务
- config_manager和ssh_utils达到目标覆盖率
- 初始化向导UI逻辑测试（Mock方式）

### Week 4: 集成与UI
- 完成Phase 3关键流程测试（使用Ubuntu虚拟机）
- 完成Phase 4基础UI测试

### Week 5: 真实设备测试（需要192.168.1.29）
- 在目标设备上执行初始化向导测试
- 验证初始化后系统状态
- 输出完整测试报告

## 环境标记与跳过

```python
# conftest.py 中添加标记
import pytest

# 标记需要真实设备的测试
real_device = pytest.mark.skipif(
    not os.environ.get("REAL_DEVICE_TEST"),
    reason="需要真实目标设备192.168.1.29"
)

# 标记需要Ubuntu虚拟机的测试
ubuntu_vm = pytest.mark.skipif(
    not os.environ.get("UBUNTU_VM_AVAILABLE"),
    reason="需要Ubuntu虚拟机192.168.56.132"
)
```

使用示例：
```python
@real_device
def test_device_initializer_full_flow():
    """完整初始化流程 - 仅在真实设备上执行"""
    pass

@ubuntu_vm
def test_ssh_connection():
    """SSH连接测试 - 使用Ubuntu虚拟机"""
    pass
```

## 成功标准

1. ✅ `pytest` 命令能在conda环境中正常运行
2. ✅ 至少80%的核心模块（config, ssh, slog）有单元测试
3. ✅ 每次提交自动运行测试（如有CI）
4. ✅ 生成可读的HTML覆盖率报告
5. ✅ 清晰区分不同测试环境的要求
6. ✅ 测试运行时间 < 5分钟（全量，不含真实设备测试）

## 注意事项

1. **Windows环境**: 所有测试必须在Windows上可运行
2. **Conda环境**: 测试需要支持conda activate pyqt5_env
3. **Qt主循环**: 使用pytest-qt处理QApplication
4. **文件路径**: 使用pathlib处理Windows/Unix路径差异
5. **编码问题**: 注意中文路径和配置的编码处理
6. **设备初始化**: 绝对不要在Ubuntu虚拟机上执行完整初始化流程
7. **环境变量**: 使用环境变量控制是否执行需要外部设备的测试
