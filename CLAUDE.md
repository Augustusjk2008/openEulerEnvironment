# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# 语言设置
请始终使用简体中文与我对话和输出代码注释。

---

## 项目概述

RTopenEuler 系统管理工具是一个基于 PyQt5 和 PyQt-Fluent-Widgets 的桌面应用程序，用于管理和配置 openEuler 嵌入式开发环境。

### 核心功能

1. **开发环境配置** - 一键部署编译器、依赖库、工具链（CMake、ARM工具链、MinGW64、VSCode等）
2. **系统初始化** - 通过SSH远程执行CCU设备出厂初始化操作（文件上传、命令执行）
3. **代码生成** - 根据产品型号生成初始化模板、驱动代码（规划中）
4. **教程文档** - 配置指南、代码示例与版本说明

---

## 开发环境设置

### Conda 环境管理

```bash
# 创建环境
conda create -n pyqt5_env python=3.8 -y

# 安装依赖
conda run -n pyqt5_env pip install PyQt5 PyQt-Fluent-Widgets paramiko

# 激活环境
conda activate pyqt5_env

# 退出环境
conda deactivate
```

### 依赖包

核心依赖在 `references/openEulerReset/requirements.txt`:
- `PyQt5==5.15.9` - GUI框架
- `paramiko==3.3.1` - SSH客户端库
- `PyQt-Fluent-Widgets` - Material Design风格组件库

### 运行应用

```bash
# 开发模式运行
python src/main_window.py

# 打包为可执行文件
pyinstaller --noconsole --onefile src/main_window.py
```

---

## 架构概览

### 目录结构

```
openEulerEnvironment/
├── src/                                  # 源代码
│   ├── main_window.py                   # 主窗口 (FluentWindow)
│   ├── home_interface.py                # 首页界面
│   ├── tutorial_interface.py            # 教程与文档界面
│   ├── settings_interface.py            # 设置界面
│   ├── initializer_interface.py         # 系统初始化界面
│   ├── environment_install_interface.py # 环境配置界面
│   └── code_generation_interface.py     # 代码生成界面
├── versions/                             # 版本说明(txt，文件名为版本号)
├── references/
├── docs/
│   └── environment_guide.md             # 环境操作指南
└── CLAUDE.md                             # 本文件
```

### 主窗口架构 (`main_window.py`)

- 基于 `FluentWindow` 实现导航结构
- 窗口固定大小：1000x750
- 三个主要功能页面 + 设置页面（底部导航）
- 使用信号槽机制处理页面跳转

**关键代码模式：**
```python
# 页面跳转通过信号实现
self.homeInterface.switch_to_initializer.connect(self._switch_to_initializer_page)

def _switch_to_initializer_page(self):
    self.switchTo(self.initializerInterface)
```

### 界面模块

1. **HomeInterface** (`home_interface.py`)
   - 主页展示，采用卡片式布局
   - 功能卡片：环境配置、代码生成、设备初始化、教程文档
   - 定义跳转信号：`switch_to_initializer`, `switch_to_environment`

2. **EnvironmentInstallInterface** (`environment_install_interface.py`)
   - 环境安装配置界面
   - 使用 `InstallThread` (QThread) 执行后台安装任务
   - 支持组件：CMake、工具链、库文件、MinGW64、VSCode、VSCode插件
   - 自动修改 Windows PATH 环境变量

3. **InitializerInterface** (`initializer_interface.py`)
   - CCU系统出厂初始化
   - 使用两个工作线程：
     - `FileUploadWorker` - SFTP文件上传
     - `SSHWorker` - SSH命令执行
   - 自动定位 `references/openEulerReset/files_to_upload` 目录

4. **CodeGenerationInterface** (`code_generation_interface.py`)
   - 根据产品型号和工程类型生成代码模板
   - 使用 `CodeGenerateThread` 后台线程执行生成任务
   - 支持的工程类型：Hello_World, MB_DDF, Helm_Control, Auto_Pilot, Upgrade_And_Test
   - 模板文件位于程序目录下的 `programs/` 子目录
   - 支持中文文件名乱码修复（多种编码尝试）
5. **TutorialInterface** (`tutorial_interface.py`)
   - 教程与文档页面，展示 PDF、Word 文档与版本说明
   - 版本信息读取程序目录下 `versions/` 中的 `.txt` 文件（文件名为版本号）

### 多线程架构

所有耗时操作都使用 QThread 在后台执行，避免阻塞UI：

```python
class WorkerThread(QThread):
    log_signal = pyqtSignal(str)      # 日志输出
    status_signal = pyqtSignal(str)   # 状态更新
    finished_signal = pyqtSignal(bool, str)  # 完成

# 连接信号
worker.log_signal.connect(self.log_message)
worker.finished_signal.connect(self.on_finished)
```

**线程类列表：**
- `InstallThread` - 环境安装（environment_install_interface.py）
- `FileUploadWorker` - SFTP文件上传（initializer_interface.py）
- `SSHWorker` - SSH命令执行（initializer_interface.py）
- `CodeGenerateThread` - 代码生成（code_generation_interface.py）

---

## SSH 远程操作

### 连接配置

连接参数通过 `config.py` 配置（优先）或使用硬编码默认值：
```python
SSH_HOST = "192.168.137.100"
SSH_USERNAME = "root"
SSH_PASSWORD = "Shanghaith8"
```

### 初始化步骤顺序

系统初始化按以下步骤执行（见 `initializer_interface.py:273-327`）：

1. 设置root密码 (`chpasswd`)
2. 创建文件夹结构 (`/home/sast8/user_*`)
3. 上传文件（可选，日志记录）
4. 配置动态库路径 (`ld.so.conf.d/sast8_libs.conf`)
5. 硬盘扩容 (`resize2fs-arm64 /dev/mmcblk0p3`)
6. 执行安全测试 (`device_hash_and_sign.sh` 和 `test_secure`)
7. 清理测试文件
8. 清理不需要的文件 (`/etc/volatile.cache`, `/etc/issue.net`)
9. 配置系统时间
10. 重启系统 (`reboot`)

---

## 环境配置模块

### 支持的组件

环境安装界面支持以下组件（见 `environment_install_interface.py:49-66`）：

- CMake (MSI安装包静默安装)
- OpenSSH (可选)
- ARM GNU Toolchain (zip解压)
- 库文件 (zip解压)
- MinGW64 (zip解压)
- VSCode (zip解压)
- VSCode插件 (zip解压到 `%USERPROFILE%\.vscode`)
- 添加到PATH环境变量（使用 winreg 修改注册表）

### 文件检测逻辑

界面启动时会自动检测源文件是否存在，不存在则禁用对应复选框：
```python
file_path = os.path.join(self.source_dir, filename)
if not os.path.exists(file_path):
    checkbox.setEnabled(False)
```

源文件目录根据运行模式自动确定：
- 打包模式：`os.path.dirname(sys.executable)`
- 开发模式：`os.path.dirname(os.path.abspath(__file__)`

这种模式在多个界面中使用（`environment_install_interface.py`, `code_generation_interface.py`），确保应用在开发和打包后都能正确找到资源文件。

---

## 打包部署

### 使用 PyInstaller

```bash
# 安装打包工具
pip install pyinstaller

# 打包命令
pyinstaller --noconsole --onefile src/main_window.py

# 输出位置：dist/main_window.exe
```

### 打包配置

- `--noconsole`: 不显示控制台窗口（GUI程序）
- `--onefile`: 单文件模式

---

## 常见任务

### 添加新的初始化步骤

在 `InitializerInterface.start_init_commands()` 的 `commands` 列表中添加：
```python
commands.append(("步骤名称", "命令", 是否需要chmod))
```

### 添加新的安装组件

1. 在 `EnvironmentInstallInterface._create_options_card()` 的 `options` 列表中添加
2. 在 `InstallThread` 中实现对应的 `_extract_xxx()` 方法
3. 在 `InstallThread.run()` 的步骤列表中注册

### 修改SSH连接配置

编辑 `references/openEulerReset/config.py` 文件。

### 添加新的工程模板

1. 将模板文件放入程序目录的 `programs/` 子目录
2. 在 `CodeGenerationInterface.PROJECT_TYPES` 字典中添加条目
3. 在 `_scan_templates()` 方法的模板列表中添加模板名

### 添加版本信息

1. 在程序目录下创建 `versions/` 文件夹（若不存在）
2. 新建 `.txt` 文件，文件名为版本号（例如 `1.2.0.txt`）
3. 在文件内容中写入该版本的说明，支持多行

---

## 代码生成模块

### 工程类型

代码生成界面支持以下工程类型（见 `code_generation_interface.py:178-184`）：

- `Hello_World` - Hello world
- `MB_DDF` - MB_DDF示例工程
- `Helm_Control` - 舵机控制工程
- `Auto_Pilot` - 自动驾驶仪工程
- `Upgrade_And_Test` - 监控和测试工程

### 模板文件位置

模板文件位于程序目录的 `programs/` 子目录下，每个工程类型对应一个文件/文件夹。

### 中文文件名处理

代码生成模块包含专门的中文文件名乱码修复功能（`_decode_zip_filename` 方法），会依次尝试以下编码：

1. CP437 -> GBK（Windows 中文系统最常见）
2. CP437 -> UTF-8
3. Latin-1 -> GBK
4. Latin-1 -> UTF-8
5. CP437 -> GB2312

---

## 重要常量和配置

### SSH 连接超时
- 连接超时：30秒
- 命令超时：300秒（见 `config.py:10-11`）

### 窗口尺寸
- 固定大小：1000x750 像素
- 禁止调整窗口大小（包括最大化）

### 默认输出目录
- 代码生成默认输出：`C:\Projects`（可由用户修改）

---

## 重要注意事项

### SSH 连接配置
- 默认连接配置硬编码在 `initializer_interface.py:249` 和 `271` 中
- 如果 `config.py` 导入失败，会使用这些默认值
- 修改 SSH 配置时，请同时检查这两个位置

### 文件上传目标目录
- 文件上传到目标设备的根目录 `/`（见 `initializer_interface.py:252`）
- 这是与原 `system_initializer.py` 保持一致的设计

### 信号槽连接模式
- 页面间跳转通过 PyQt 信号槽实现，而非直接调用方法
- 示例：`self.homeInterface.switch_to_initializer.connect(self._switch_to_initializer_page)`
- 这种模式确保了界面间的解耦

### 线程清理
- 所有 QThread 子类都需要正确实现 `stop()` 方法（如果支持取消）
- 线程完成后需断开信号连接并调用 `deleteLater()`（见 `code_generation_interface.py:767-781`）

### Windows PATH 修改
- 环境配置界面使用 `winreg` 模块直接修改注册表
- 修改后需要重启应用程序或系统才能生效

### 中文文件名乱码问题
- 代码生成模块特别处理了 ZIP 文件中的中文文件名
- 使用了多种编码尝试方法来修复乱码