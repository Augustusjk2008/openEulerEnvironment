# 测试架构设计文档

**版本**: 1.0
**日期**: 2026-02-16
**作者**: 测试架构师

---

## 1. 概述

本文档描述了openEuler环境配置器项目的测试架构设计，包括测试框架的组织结构、配置说明和使用指南。

### 1.1 设计目标

- **可维护性**: 清晰的目录结构和命名规范
- **可扩展性**: 支持新增测试类型和标记
- **环境隔离**: 支持不同测试环境（本地、VM、真实设备）
- **自动化**: 集成CI/CD流程，支持自动化测试

### 1.2 技术栈

| 组件 | 用途 | 版本 |
|------|------|------|
| pytest | 测试框架核心 | >=6.0 |
| pytest-qt | Qt/PyQt5测试支持 | latest |
| pytest-cov | 覆盖率测量 | latest |
| pytest-timeout | 测试超时控制 | latest |
| coverage | 覆盖率报告 | latest |

---

## 2. 目录结构

```
openEulerEnvironment/
├── src/                          # 源代码目录
│   ├── core/                     # 核心功能模块
│   ├── ui/                       # 用户界面模块
│   └── ...
│
├── tests/                        # 测试目录（本架构的核心）
│   ├── pytest.ini               # pytest主配置文件
│   ├── conftest.py              # 全局fixture和标记定义
│   │
│   ├── unit/                     # 单元测试
│   │   ├── core/                 # 核心模块单元测试
│   │   ├── ui/                   # UI模块单元测试
│   │   └── ...
│   │
│   ├── integration/              # 集成测试
│   │   ├── ssh/                  # SSH功能集成测试
│   │   ├── ftp/                  # FTP功能集成测试
│   │   └── vm/                   # VM相关集成测试
│   │
│   ├── e2e/                      # 端到端测试
│   │   └── device_init/          # 设备初始化向导测试
│   │
│   ├── fixtures/                 # 测试数据文件
│   │   ├── cpp_samples/          # C++代码样例
│   │   ├── protocol_samples/     # 协议定义样例
│   │   └── config_samples/       # 配置文件样例
│   │
│   ├── utils/                    # 测试工具函数
│   │   ├── helpers.py            # 通用辅助函数
│   │   └── mocks.py              # 模拟对象定义
│   │
│   └── reports/                  # 测试报告输出（.gitignore）
│       ├── coverage_html/        # HTML覆盖率报告
│       ├── coverage.xml          # XML覆盖率报告
│       └── junit.xml             # JUnit格式报告
│
├── .coveragerc                   # 覆盖率配置文件
├── docs/                         # 文档目录
│   └── test_architecture.md      # 本文件
│
└── ...
```

---

## 3. 配置文件说明

### 3.1 pytest.ini

**位置**: `tests/pytest.ini`

**功能**: pytest主配置文件，定义测试发现规则、插件配置和标记。

**关键配置项**:

| 配置项 | 说明 |
|--------|------|
| `testpaths` | 测试目录搜索顺序：unit → integration → e2e |
| `markers` | 自定义标记定义（ubuntu_vm, real_device等） |
| `addopts` | 默认命令行选项（覆盖率、报告等） |
| `qt_api` | Qt绑定类型（pyqt5） |
| `env` | 默认环境变量 |

**自定义标记**:

- `@pytest.mark.ubuntu_vm` - 需要Ubuntu虚拟机
- `@pytest.mark.real_device` - 需要真实目标板
- `@pytest.mark.slow` - 慢速测试
- `@pytest.mark.gui` - GUI相关测试

### 3.2 conftest.py

**位置**: `tests/conftest.py`

**功能**: 全局fixture和标记定义，提供测试基础设施。

**主要Fixture**:

| Fixture | 作用域 | 说明 |
|---------|--------|------|
| `project_root` | session | 项目根目录路径 |
| `src_path` | session | src目录路径 |
| `qt_bot` | function | QtBot实例（GUI测试） |
| `temp_config_dir` | function | 临时配置目录 |
| `temp_project_dir` | function | 临时项目目录 |
| `mock_qt_messagebox` | function | 模拟QMessageBox |
| `mock_qt_filedialog` | function | 模拟QFileDialog |
| `mock_ssh_client` | function | 模拟SSH客户端 |
| `mock_ftp_client` | function | 模拟FTP客户端 |
| `ubuntu_vm_config` | session | Ubuntu VM配置 |
| `real_device_config` | session | 真实设备配置 |

### 3.3 .coveragerc

**位置**: `.coveragerc`

**功能**: 覆盖率测量配置。

**关键配置**:

- `source`: 测量`src/`目录的覆盖率
- `branch`: 启用分支覆盖率
- `exclude_lines`: 排除特定模式的行（如导入、抽象方法等）
- `fail_under`: 可设置最低覆盖率阈值

---

## 4. 环境配置

### 4.1 环境变量

| 变量名 | 值 | 说明 |
|--------|-----|------|
| `UBUNTU_VM_AVAILABLE` | `1` | 启用Ubuntu VM测试 |
| `REAL_DEVICE_TEST` | `1` | 启用真实设备测试 |
| `UBUNTU_VM_USER` | 用户名 | VM登录用户名（默认：openeuler） |
| `UBUNTU_VM_PASS` | 密码 | VM登录密码（默认：openeuler） |
| `DEVICE_USER` | 用户名 | 设备登录用户名（默认：root） |
| `DEVICE_PASS` | 密码 | 设备登录密码（默认：空） |
| `QT_QPA_PLATFORM` | `offscreen` | Qt无头模式 |

### 4.2 网络环境

- **Ubuntu VM**: `192.168.56.132` (VirtualBox Host-Only)
- **真实设备**: `192.168.1.29` (局域网)

---

## 5. 使用指南

### 5.1 运行所有测试

```bash
# 使用conda环境
conda activate pyqt5_env

# 运行所有测试（跳过VM和设备测试）
pytest tests/

# 或进入tests目录
pytest
```

### 5.2 运行特定类型测试

```bash
# 仅运行单元测试
pytest tests/unit/

# 仅运行集成测试
pytest tests/integration/

# 仅运行端到端测试
pytest tests/e2e/
```

### 5.3 使用标记过滤

```bash
# 排除慢速测试
pytest -m "not slow"

# 排除GUI测试
pytest -m "not gui"

# 仅运行VM测试（需要环境变量）
UBUNTU_VM_AVAILABLE=1 pytest -m "ubuntu_vm"

# 仅运行设备测试（需要环境变量）
REAL_DEVICE_TEST=1 pytest -m "real_device"

# 组合过滤
pytest -m "not ubuntu_vm and not real_device and not slow"
```

### 5.4 覆盖率报告

```bash
# 生成HTML覆盖率报告
pytest --cov=src --cov-report=html

# 查看控制台覆盖率报告
pytest --cov=src --cov-report=term-missing

# 生成XML报告（用于CI）
pytest --cov=src --cov-report=xml
```

### 5.5 调试测试

```bash
# 失败时立即停止
pytest -x

# 失败时进入PDB调试
pytest --pdb

# 显示详细的测试输出
pytest -v -s

# 仅运行上次失败的测试
pytest --lf

# 运行特定测试函数
pytest tests/unit/core/test_config.py::test_load_config
```

---

## 6. 编写测试

### 6.1 单元测试示例

```python
# tests/unit/core/test_config_manager.py
import pytest
from core.config_manager import ConfigManager

def test_config_manager_init(temp_config_dir):
    """测试配置管理器初始化"""
    config = ConfigManager(config_dir=temp_config_dir)
    assert config.config_dir == temp_config_dir

def test_config_save_and_load(temp_config_dir):
    """测试配置保存和加载"""
    config = ConfigManager(config_dir=temp_config_dir)
    config.set("key", "value")
    config.save()

    config2 = ConfigManager(config_dir=temp_config_dir)
    assert config2.get("key") == "value"
```

### 6.2 GUI测试示例

```python
# tests/unit/ui/test_main_window.py
import pytest
from PyQt5.QtCore import Qt
from ui.main_window import MainWindow

def test_main_window_title(qt_bot):
    """测试主窗口标题"""
    window = MainWindow()
    qt_bot.addWidget(window)

    assert window.windowTitle() == "openEuler环境配置器"

def test_button_click(qt_bot, mock_qt_messagebox):
    """测试按钮点击"""
    window = MainWindow()
    qt_bot.addWidget(window)

    qt_bot.mouseClick(window.save_button, Qt.LeftButton)
    mock_qt_messagebox.information.assert_called_once()
```

### 6.3 VM集成测试示例

```python
# tests/integration/vm/test_ssh_connection.py
import pytest

@pytest.mark.ubuntu_vm
def test_ssh_connection(ubuntu_vm_config):
    """测试SSH连接（需要Ubuntu VM）"""
    from core.ssh_utils import SSHClient

    client = SSHClient()
    client.connect(
        host=ubuntu_vm_config["host"],
        port=ubuntu_vm_config["port"],
        username=ubuntu_vm_config["username"],
        password=ubuntu_vm_config["password"]
    )

    result = client.execute("uname -a")
    assert "Linux" in result
    client.close()
```

### 6.4 真实设备测试示例

```python
# tests/e2e/device_init/test_init_wizard.py
import pytest

@pytest.mark.real_device
def test_device_initialization(real_device_config):
    """测试设备初始化向导（需要真实设备）"""
    from ui.wizards.device_init_wizard import DeviceInitWizard

    wizard = DeviceInitWizard(device_config=real_device_config)
    result = wizard.run()

    assert result.success is True
```

---

## 7. 最佳实践

### 7.1 命名规范

- 测试文件: `test_<module_name>.py`
- 测试类: `Test<ClassName>`
- 测试函数: `test_<functionality>[_<condition>]`

### 7.2 测试组织

- 一个测试函数只测试一个概念
- 使用描述性的测试名称
- 使用fixture共享测试数据
- 避免测试之间的依赖

### 7.3 标记使用

- 使用`@pytest.mark.slow`标记耗时超过1秒的测试
- 使用`@pytest.mark.gui`标记需要GUI的测试
- 使用`@pytest.mark.ubuntu_vm`标记需要VM的测试
- 使用`@pytest.mark.real_device`标记需要真实设备的测试

### 7.4 Mock使用

- 使用内置的`monkeypatch` fixture
- 使用提供的`mock_qt_*` fixture避免弹窗
- 使用`mock_ssh_client`和`mock_ftp_client`模拟网络操作

---

## 8. CI/CD集成

### 8.1 GitHub Actions示例

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.8'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-qt pytest-cov

      - name: Run tests
        run: pytest -m "not ubuntu_vm and not real_device"

      - name: Upload coverage
        uses: codecov/codecov-action@v2
        with:
          files: ./tests/reports/coverage.xml
```

---

## 9. 故障排除

### 9.1 常见问题

**Q: Qt测试失败，提示没有显示器**
A: 确保设置了`QT_QPA_PLATFORM=offscreen`环境变量

**Q: 覆盖率报告为空**
A: 检查`.coveragerc`中的`source`路径是否正确

**Q: VM测试被跳过**
A: 检查是否设置了`UBUNTU_VM_AVAILABLE=1`环境变量

**Q: 导入模块失败**
A: 确保`conftest.py`中的`sys.path`设置正确

### 9.2 调试技巧

```bash
# 查看收集到的测试
pytest --collect-only

# 查看fixture信息
pytest --fixtures

# 详细输出
pytest -v --tb=long

# 覆盖率调试
pytest --cov=src --cov-debug=trace
```

---

## 10. 更新记录

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.0 | 2026-02-16 | 初始版本 |

---

## 11. 参考资源

- [pytest官方文档](https://docs.pytest.org/)
- [pytest-qt文档](https://pytest-qt.readthedocs.io/)
- [pytest-cov文档](https://pytest-cov.readthedocs.io/)
- [coverage.py文档](https://coverage.readthedocs.io/)
