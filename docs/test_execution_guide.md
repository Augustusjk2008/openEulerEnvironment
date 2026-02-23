# 全阶段测试执行指南

## 概述

本指南描述如何执行Phase 1-3建立的全部测试，包括环境准备、执行步骤、结果验证和问题处理流程。

**测试范围统计**：
| 阶段 | 测试类型 | 数量 | 环境要求 |
|------|----------|------|----------|
| Phase 2 | 核心模块单元测试 | 171个 | 本地(Windows) |
| Phase 2 | SSH/SFTP集成测试 | 32个 | Ubuntu虚拟机(192.168.56.132) |
| Phase 3 | UI自动化测试 | 111个 | 本地(Windows+显示器) |
| Phase 3 | E2E工作流测试 | 46个 | 本地(Windows) |
| Phase 3 | 设备初始化测试 | 11个 | **真实设备(192.168.1.29)** |
| **总计** | | **371个** | |

---

## 第一部分：环境准备

### 1.1 Windows本地环境准备

#### 必需软件

| 软件 | 版本 | 用途 | 检查命令 |
|------|------|------|----------|
| Python | 3.8 | 运行环境 | `python --version` |
| Conda | 任意 | 虚拟环境管理 | `conda --version` |
| Git Bash | 最新 | 执行Shell命令 | - |

#### Conda虚拟环境

```bash
# 1. 激活虚拟环境
conda activate pyqt5_env

# 2. 验证Python版本
python --version
# 应显示 Python 3.8.x

# 3. 验证PyQt5安装
python -c "from PyQt5 import QtWidgets; print('PyQt5 OK')"

# 4. 安装/更新测试依赖
pip install pytest pytest-cov pytest-qt pytest-timeout pyyaml

# 5. 验证pytest安装
pytest --version
```

#### 项目路径检查

```bash
# 确认当前目录
pwd
# 应为: H:/WorkSpace/PythonWorkspace/openEulerEnvironment

# 确认目录结构
ls tests/
# 应显示: conftest.py  config  e2e  fixtures  integration  pytest.ini  unit  utils  verify_setup.py
```

### 1.2 Ubuntu虚拟机环境准备（用于集成测试）

#### 虚拟机配置清单

| 配置项 | 要求 | 说明 |
|--------|------|------|
| IP地址 | 192.168.56.132 | 固定IP |
| 系统 | Ubuntu 20.04/22.04 | 桌面版或服务器版 |
| SSH服务 | 已启用 | 端口22 |
| 测试用户 | testuser | 普通用户，非root |
| 测试目录 | /home/testuser/sftp_test | 用于文件传输测试 |

#### 虚拟机设置步骤

在Ubuntu虚拟机(192.168.56.132)上执行：

```bash
# 1. 安装SSH服务
sudo apt-get update
sudo apt-get install -y openssh-server
sudo systemctl enable ssh
sudo systemctl start ssh

# 2. 创建测试用户
sudo useradd -m testuser
sudo passwd testuser  # 设置密码，记住这个密码

# 3. 创建测试目录
sudo mkdir -p /home/testuser/sftp_test
sudo chown testuser:testuser /home/testuser/sftp_test

# 4. 验证SSH连接
# 在Windows上执行:
# ssh testuser@192.168.56.132
```

#### 测试配置更新

编辑 `tests/config/test_env.yaml`：

```yaml
ubuntu_vm:
  host: "192.168.56.132"
  port: 22
  username: "testuser"          # 填入实际用户名
  password: "your_password"     # 填入实际密码
  # 或使用密钥:
  # private_key: "~/.ssh/id_rsa"
```

### 1.3 真实目标设备准备（仅设备初始化测试）

**⚠️ 警告：设备初始化测试会修改系统配置，仅在192.168.1.29执行**

| 配置项 | 要求 | 说明 |
|--------|------|------|
| IP地址 | 192.168.1.29 | RTopenEuler嵌入式设备 |
| 用户名 | root | 需要root权限 |
| 密码 | 已知 | 设备root密码 |
| 状态 | 出厂状态 | 建议初始化前状态 |

**设备测试环境变量**：
```bash
set REAL_DEVICE_TEST=1
set DEVICE_PASSWORD=your_root_password
```

---

## 第二部分：测试执行步骤

### 2.1 快速验证（推荐首次执行）

```bash
# 1. 激活环境
conda activate pyqt5_env

# 2. 进入项目目录
cd H:/WorkSpace/PythonWorkspace/openEulerEnvironment

# 3. 运行验证脚本
python tests/verify_setup.py

# 期望输出:
# ✓ pytest可用
# ✓ 模块导入
# ✓ 示例测试
```

### 2.2 单元测试执行（Phase 2核心模块）

#### 全部单元测试

```bash
# 运行所有单元测试（不含UI）
pytest tests/unit/core/ -v

# 生成覆盖率报告
pytest tests/unit/core/ --cov=src --cov-report=html --cov-report=term

# 查看HTML报告
start tests/reports/coverage_html/index.html
```

#### 单独模块测试

```bash
# 仅测试配置管理器
pytest tests/unit/core/test_config_manager.py -v

# 仅测试SSH工具
pytest tests/unit/core/test_ssh_utils.py -v

# 仅测试SLOG解析器
pytest tests/unit/core/test_slog_parser.py -v

# 仅测试认证管理器
pytest tests/unit/core/test_auth_manager.py -v
```

**期望结果**：
- 171个测试全部通过
- config_manager覆盖率 ≥ 90%
- ssh_utils覆盖率 ≥ 85%
- slog_parser覆盖率 ≥ 80%
- auth_manager覆盖率 ≥ 75%

### 2.3 集成测试执行（Phase 2 SSH/SFTP）

#### 无VM环境（跳过集成测试）

```bash
# 不设置环境变量，集成测试自动跳过
pytest tests/unit/ -v
```

#### 有VM环境（执行集成测试）

```bash
# 1. 设置环境变量
set UBUNTU_VM_AVAILABLE=1

# 2. 运行包含集成测试的全部测试
pytest tests/unit/ tests/integration/ -v

# 3. 仅运行集成测试
pytest tests/integration/ -v
```

**期望结果**：
- SSH连接测试通过
- SFTP上传下载测试通过
- 32个集成测试通过

### 2.4 UI自动化测试执行（Phase 3）

**⚠️ 注意：UI测试需要图形界面，建议在本地Windows执行，不建议在SSH远程会话执行**

```bash
# 运行所有UI测试
pytest tests/unit/ui/ -v

# 运行特定UI测试
pytest tests/unit/ui/test_login_interface.py -v
pytest tests/unit/ui/test_settings_interface.py -v

# 运行E2E测试
pytest tests/e2e/test_main_workflow.py -v
```

**UI测试特殊选项**：

```bash
# 无头模式（不显示窗口，但Qt测试可能需要显示器）
pytest tests/unit/ui/ -v --headless

# 超时设置（UI测试可能较慢）
pytest tests/unit/ui/ -v --timeout=60
```

**期望结果**：
- 111个UI测试通过
- 46个E2E测试通过
- 无窗口卡住或崩溃

### 2.5 设备初始化测试执行（Phase 3 - 危险操作）

**⚠️ 再次确认：此测试仅在192.168.1.29执行，会修改设备配置**

```bash
# 1. 确认目标设备正确
ping 192.168.1.29

# 2. 设置环境变量
set REAL_DEVICE_TEST=1
set DEVICE_PASSWORD=your_root_password_here

# 3. 仅运行设备测试
pytest tests/e2e/test_device_initializer.py -v

# 4. 运行全部测试（包括设备测试）
pytest tests/ -v -m "real_device"
```

**安全验证**：

测试代码会自动验证：
- 禁止在192.168.56.132执行
- 必须设置REAL_DEVICE_TEST=1
- 必须提供DEVICE_PASSWORD

**期望结果**：
- 11个设备测试通过
- 设备完成初始化流程
- 设备重启后状态正常

### 2.6 全量测试执行（所有阶段）

```bash
# 1. 基础环境检查
conda activate pyqt5_env

# 2. 单元测试 + UI测试（本地可执行的全部）
pytest tests/unit/ -v --cov=src --cov-report=html

# 3. 包含集成测试（需要VM）
set UBUNTU_VM_AVAILABLE=1
pytest tests/unit/ tests/integration/ -v

# 4. 包含设备测试（需要真实设备）
set REAL_DEVICE_TEST=1
set DEVICE_PASSWORD=xxx
pytest tests/ -v
```

---

## 第三部分：结果验证

### 3.1 测试通过标准

| 测试类型 | 通过标准 | 失败处理 |
|----------|----------|----------|
| 单元测试 | 171个全部通过 | 见第4章 |
| 集成测试 | 32个全部通过 | 检查VM连接 |
| UI测试 | 111个全部通过 | 见第4章 |
| E2E测试 | 46个全部通过 | 见第4章 |
| 设备测试 | 11个全部通过 | 检查设备状态 |

### 3.2 覆盖率验证

```bash
# 生成完整覆盖率报告
pytest tests/unit/ --cov=src --cov-report=html --cov-report=term

# 验证阈值
# - config_manager: 90%+
# - ssh_utils: 85%+
# - slog_parser: 80%+
# - auth_manager: 75%+
```

### 3.3 测试报告查看

```bash
# HTML覆盖率报告
start htmlcov/index.html

# 单元测试详细报告
cat tests/reports/coverage_report.md

# 集成测试报告
cat docs/integration_test_report.md

# UI测试实现文档
cat docs/ui_test_implementation.md
```

---

## 第四部分：错误处理流程

### 4.1 错误分类与处理决策树

```
测试失败
    │
    ├── 1. 导入错误 (ImportError/ModuleNotFoundError)
    │   ├── pytest配置问题 → 修复 tests/pytest.ini
    │   └── 路径问题 → 修复 tests/conftest.py
    │
    ├── 2. 测试代码错误 (AssertionError in test)
    │   ├── 测试逻辑错误 → 修复测试代码
    │   └── Mock设置错误 → 修复Mock/fixture
    │
    ├── 3. 被测代码暴露的问题 (原程序Bug)
    │   └── 记录到 docs/test_code_suggestions.md
    │       ├── 高优先级: 功能错误
    │       ├── 中优先级: 边界处理不当
    │       └── 低优先级: 优化建议
    │
    └── 4. 环境问题
        ├── VM连接失败 → 检查网络/SSH配置
        ├── UI测试卡住 → 检查显示器/ Qt环境
        └── 设备测试失败 → 检查设备状态/网络
```

### 4.2 具体处理流程

#### 场景1：测试代码错误（修复测试）

**判断标准**：
- 测试断言逻辑错误
- Mock返回值设置错误
- fixture准备数据错误
- 测试与实现不匹配

**处理步骤**：

```bash
# 1. 定位失败的测试
pytest tests/unit/core/test_xxx.py::TestClass::test_method -v

# 2. 查看详细错误
pytest tests/unit/core/test_xxx.py::TestClass::test_method -v --tb=long

# 3. 修复测试代码（示例）
# 编辑 tests/unit/core/test_xxx.py

# 4. 重新运行验证
pytest tests/unit/core/test_xxx.py::TestClass::test_method -v
```

**示例修复**（Mock返回值错误）：
```python
# 原测试（错误）
def test_feature(self, mock_ssh):
    mock_ssh.exec_command.return_value = (None, "output", None)  # 格式错误
    result = ssh_utils.execute("ls")
    assert result == "output"  # 失败

# 修复后
def test_feature(self, mock_ssh):
    # 正确设置Mock返回值
    mock_stdout = MagicMock()
    mock_stdout.read.return_value = b"output"
    mock_ssh.exec_command.return_value = (None, mock_stdout, None)
    result = ssh_utils.execute("ls")
    assert result == "output"
```

#### 场景2：原程序Bug（记录问题）

**判断标准**：
- 测试逻辑正确，但原程序返回错误结果
- 边界条件处理不当（如空值、特殊字符）
- 异常处理缺失
- 与文档/预期行为不符

**处理步骤**：

1. **不要修改原代码**（遵守约束）
2. **记录到问题文档**

编辑 `docs/test_code_suggestions.md`：

```markdown
## 🔴 高优先级 (High)

| # | 文件 | 行号 | 问题描述 | 建议修改 | 发现者 | 发现时间 |
|---|------|------|----------|----------|--------|----------|
| 1 | core/config_manager.py | 45 | `get()`方法对None值处理不当，返回None而非默认值 | 建议添加: if value is None: return default | Tester | 2026-02-16 |

## 测试用例（复现问题）

```python
def test_get_none_value_should_return_default():
    cm = ConfigManager()
    cm._config["key"] = None
    # 期望返回默认值"default"，实际返回None
    assert cm.get("key", "default") == "default"  # 失败
```
```

3. **标记测试为跳过或预期失败**（可选）

```python
@pytest.mark.skip(reason="已知Bug: 等待修复 https://github.com/xxx/issues/1")
def test_feature_with_known_bug():
    ...

# 或
@pytest.mark.xfail(reason="边界条件处理待改进")
def test_edge_case():
    ...
```

#### 场景3：环境问题

**VM连接失败**：
```bash
# 检查网络
ping 192.168.56.132

# 检查SSH服务
ssh testuser@192.168.56.132

# 检查配置
cat tests/config/test_env.yaml
```

**UI测试失败**：
```bash
# 检查Qt环境
python -c "from PyQt5.QtWidgets import QApplication; print('Qt OK')"

# 检查显示器（Windows）
echo %DISPLAY%

# 运行单测试调试
pytest tests/unit/ui/test_login_interface.py::TestLogin::test_field -v -s
```

**设备测试失败**：
```bash
# 检查设备可达性
ping 192.168.1.29
ssh root@192.168.1.29

# 检查环境变量
echo %REAL_DEVICE_TEST%
echo %DEVICE_PASSWORD%

# 查看详细日志
pytest tests/e2e/test_device_initializer.py -v --tb=long
```

### 4.3 问题记录模板

当发现原程序问题时，使用此模板记录：

```markdown
### 问题编号: BUG-XXX

**发现日期**: 2026-02-16
**发现者**: [你的名字]
**测试文件**: tests/unit/core/test_xxx.py::TestClass::test_method
**原程序文件**: src/core/xxx.py

**问题描述**:
在[什么情况下]，原程序[什么表现]，期望[什么表现]。

**复现步骤**:
1. 调用xxx函数，参数为xxx
2. 观察返回值为xxx
3. 期望返回xxx

**影响评估**:
- [ ] 高: 导致程序崩溃或数据丢失
- [x] 中: 功能异常但可 workaround
- [ ] 低: 边界情况或优化建议

**建议修复**:
```python
# 当前代码
def problematic_func():
    return None  # 问题

# 建议修复
def problematic_func():
    if condition:
        return default_value  # 添加边界处理
    return result
```

**相关测试**:
```python
def test_expose_bug():
    result = problematic_func()
    assert result is not None  # 暴露问题
```
```

---

## 第五部分：常见问题排查

### 5.1 pytest导入错误

**错误**：`ModuleNotFoundError: No module named 'core'`

**解决**：
```bash
# 检查pytest.ini
[pytest]
pythonpath = src
testpaths = tests/unit, tests/integration, tests/e2e

# 或临时设置环境变量
set PYTHONPATH=src
pytest tests/ -v
```

### 5.2 Qt测试卡住

**错误**：UI测试执行后无响应

**解决**：
```bash
# 添加超时
pytest tests/unit/ui/ -v --timeout=30

# 或跳过UI测试
pytest tests/unit/core/ tests/integration/ -v
```

### 5.3 覆盖率报告为空

**错误**：`pytest --cov=src` 显示0%

**解决**：
```bash
# 安装pytest-cov
pip install pytest-cov

# 正确运行
pytest tests/unit/ --cov=src --cov-report=html
```

### 5.4 VM测试跳过

**现象**：集成测试被跳过

**解决**：
```bash
# 检查环境变量
echo %UBUNTU_VM_AVAILABLE%
# 应为: 1

# 检查配置
cat tests/config/test_env.yaml

# 测试连接
ssh testuser@192.168.56.132
```

---

## 第六部分：执行检查清单

执行测试前，逐项确认：

### 环境检查
- [ ] Conda环境 `pyqt5_env` 已激活
- [ ] 项目目录正确
- [ ] pytest已安装
- [ ] PyQt5可导入
- [ ] 测试文件结构完整

### 单元测试前
- [ ] 不需要特殊环境
- [ ] 直接运行: `pytest tests/unit/core/ -v`

### 集成测试前
- [ ] Ubuntu虚拟机(192.168.56.132)已启动
- [ ] SSH服务已启用
- [ ] 测试用户可登录
- [ ] 环境变量 `UBUNTU_VM_AVAILABLE=1` 已设置
- [ ] `tests/config/test_env.yaml` 配置正确

### UI测试前
- [ ] 在Windows桌面环境（非SSH远程）
- [ ] 显示器可用
- [ ] Qt环境正常

### 设备测试前（危险）
- [ ] 确认目标设备是192.168.1.29
- [ ] 确认不是192.168.56.132
- [ ] 设备处于可初始化状态
- [ ] 环境变量 `REAL_DEVICE_TEST=1` 已设置
- [ ] `DEVICE_PASSWORD` 已设置

---

## 第七部分：快速命令参考

```bash
# 激活环境
conda activate pyqt5_env

# 单元测试
pytest tests/unit/core/ -v

# 单元测试+覆盖率
pytest tests/unit/core/ --cov=src --cov-report=html

# UI测试
pytest tests/unit/ui/ -v

# 集成测试（需VM）
set UBUNTU_VM_AVAILABLE=1
pytest tests/integration/ -v

# 设备测试（危险，仅192.168.1.29）
set REAL_DEVICE_TEST=1
set DEVICE_PASSWORD=xxx
pytest tests/e2e/test_device_initializer.py -v

# 全量测试（本地部分）
pytest tests/unit/ -v

# 查看覆盖率报告
start htmlcov/index.html
```

---

## 附录：联系方式与资源

| 资源 | 位置 |
|------|------|
| 测试文档 | `docs/` 目录 |
| 测试代码 | `tests/` 目录 |
| 覆盖率报告 | `htmlcov/index.html` |
| 问题记录 | `docs/test_code_suggestions.md` |
| 环境配置 | `tests/config/test_env.yaml` |

**测试执行顺序建议**：
1. 单元测试（无需环境）
2. UI测试（需要显示器）
3. 集成测试（需要VM）
4. 设备测试（需要真实设备，危险）
