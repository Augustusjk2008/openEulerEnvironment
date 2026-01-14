# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# 语言设置
请始终使用简体中文与我对话和输出代码注释。

## 开发工作流

### 常用命令

```bash
# 创建并激活 Conda 环境
conda create -n pyqt5_env python=3.8 -y
conda activate pyqt5_env

# 安装依赖
pip install -r requirements.txt

# 开发模式运行（建议传入资源目录）
python src/main.py -d .

# 跳过登录（开发调试用）
python src/main.py --skip-login -d .

# 打包为可执行文件
pip install pyinstaller
pyinstaller --noconsole --onefile src/main.py

# 运行测试
python -m unittest tests.test_slog_parser
```

### 单元测试

使用 Python 内置的 unittest 框架。测试文件位于 `tests/` 目录：
- 当前主要测试 `slog_parser` 模块
- 测试命名遵循 `test_*` 格式

---

## 项目概述

RTopenEuler 系统管理工具是一个基于 PyQt5 和 PyQt-Fluent-Widgets 的桌面应用程序，用于管理和配置 openEuler 嵌入式开发环境。

### 核心功能

1. **开发环境配置** - 一键部署编译器、依赖库、工具链（CMake、ARM工具链、MinGW64、VSCode等）
2. **系统初始化** - 通过 SSH 远程执行 CCU 设备出厂初始化操作（文件上传、命令执行）
3. **远程终端** - 内置 SSH 终端，支持与远程设备进行交互式命令行操作
4. **FTP 客户端** - 基于 SFTP 的文件上传、下载与移动
5. **数据可视化** - 读取 SLOG 文件并绘制数据曲线，支持本地或远程文件
6. **教程文档** - 配置指南、代码示例与版本说明

---

## 开发环境设置

### Conda 环境管理

```bash
# 创建环境
conda create -n pyqt5_env python=3.8 -y

# 安装依赖
conda run -n pyqt5_env pip install -r requirements.txt
```

### 依赖包

核心依赖在 `requirements.txt`:
- `PyQt5==5.15.9` - GUI 框架
- `qfluentwidgets` - Fluent 风格组件库
- `paramiko==3.3.1` - SSH/SFTP 客户端库
- `matplotlib` - 数据可视化绘图
- `pyte` - 终端模拟器解析库（可选）

### 运行应用

```bash
# 开发模式运行
python src/main.py -d .

# 打包为可执行文件
pyinstaller --noconsole --onefile src/main.py
```

---

## 架构概览

### 目录结构

```
openEulerEnvironment/
├── src/                                  # 源代码
│   ├── core/                             # 核心管理模块
│   │   ├── auth_manager.py               # 用户认证管理
│   │   ├── config_manager.py             # 配置管理 (JSON)
│   │   ├── font_manager.py               # 全局字体与 DPI 适配
│   │   └── slog_parser.py                # SLOG 解析器
│   ├── ui/                               # UI 相关组件
│   │   ├── interfaces/                   # 功能子界面
│   │   │   ├── home_interface.py         # 首页界面
│   │   │   ├── tutorial_interface.py     # 教程与文档界面
│   │   │   ├── settings_interface.py     # 设置界面
│   │   │   ├── initializer_interface.py  # 系统初始化界面
│   │   │   ├── environment_install_interface.py # 环境配置界面
│   │   │   ├── code_generation_interface.py     # 代码生成界面
│   │   │   ├── terminal_interface.py     # 内嵌 SSH 终端界面
│   │   │   ├── ftp_interface.py          # FTP 客户端界面
│   │   │   ├── data_visualization_interface.py  # 数据可视化界面
│   │   │   └── login_interface.py        # 登录界面
│   │   ├── loading_dialog.py             # 主窗口加载提示
│   │   ├── main_window.py                # 主窗口 (FluentWindow)
│   │   └── style_helper.py               # 动态样式助手
│   ├── __init__.py
│   └── main.py                           # 程序统一入口
├── docs/                                 # 文档与资源
│   ├── versions/                         # 版本说明 (txt)
│   ├── images/                           # UI 截图与图示
│   └── 00.本程序怎么使用.md               # 用户手册
├── requirements.txt                      # 依赖列表
└── CLAUDE.md                             # 本文件
```

### 启动与登录流程 (`src/main.py`)

- 应用启动后先创建登录界面
- 登录成功后显示初始化 LoadingDialog 并创建主窗口
- `MainWindow` 支持进度回调，用于显示初始化进度条
- 支持 `--skip-login` 直接进入主窗口（开发调试用）

### 主窗口架构 (`ui/main_window.py`)

- 基于 `FluentWindow` 实现导航结构
- 窗口固定大小：1700x1050
- 使用信号槽机制处理页面跳转与状态同步
- 通过 `ftpInterface.connection_changed` 同步数据可视化的远程选择按钮状态

---

## 界面与辅助模块

1. **LoginWindow** (`login_interface.py`)
   - 登录/注册界面，注册需 16 位邀请码（`core/auth_manager.py`）
   - 用户信息加密存储在 `users.dat`（位于 `get_program_dir()` 下）
2. **LoadingDialog** (`loading_dialog.py`)
   - 主窗口初始化时的图片+进度条提示
   - 使用 `assets/loading.png`
3. **HomeInterface** (`home_interface.py`)
   - 主页卡片入口，支持环境配置/代码生成/初始化/教程/终端/FTP/可视化
4. **TerminalInterface** (`terminal_interface.py`)
   - 基于 `paramiko` + `pyte` 的终端模拟器
5. **FtpInterface** (`ftp_interface.py`)
   - 基于 SFTP 的远端文件管理
   - 连接状态通过 `connection_changed` 信号对外通知
6. **DataVisualizationInterface** (`data_visualization_interface.py`)
   - 读取本地 `.slog` 文件绘图
   - 远程选择 `.slog` 时先下载到临时目录后读取展示

---

## 多线程架构

所有耗时操作使用 QThread 在后台执行，避免阻塞 UI：

```python
class WorkerThread(QThread):
    log_signal = pyqtSignal(str)      # 日志输出
    status_signal = pyqtSignal(str)   # 状态更新
    finished_signal = pyqtSignal(bool, str)  # 完成
```

**线程类列表：**
- `InstallThread` - 环境安装
- `FileUploadWorker` - SFTP 文件上传
- `SSHWorker` - SSH 命令执行
- `CodeGenerateThread` - 代码生成
- `SftpConnectWorker` - FTP 连接
- `TransferWorker` - FTP 上传/下载
- `RemoteDownloadWorker` - 数据可视化远程文件下载

---

## SSH/FTP 远程操作

### 连接配置

- 初始化/终端默认连接参数在代码中提供兜底值
- 也可在 `references/openEulerReset/config.py` 中配置 SSH 参数
- FTP 连接参数由用户在 FTP 界面填写并可保存为默认值

---

## 环境配置模块

### 支持的组件

- CMake (MSI 安装包静默安装)
- OpenSSH (可选)
- ARM GNU Toolchain (zip 解压)
- 库文件 (zip 解压)
- MinGW64 (zip 解压)
- VSCode (zip 解压)
- VSCode 插件 (zip 解压到 `%USERPROFILE%\.vscode`)
- 添加到 PATH 环境变量（使用 winreg 修改注册表）

---

## 打包部署

### 使用 PyInstaller

```bash
# 安装打包工具
pip install pyinstaller

# 打包命令
pyinstaller --noconsole --onefile src/main.py
```

---

## 重要常量和配置

### 窗口尺寸
- 主窗口初始大小：1700x1050 像素
- 登录窗口大小：1120x680 像素

### 默认输出目录
- 代码生成默认输出：`C:\Projects`

### 命令行参数
- `-d/--dir`: 指定程序资源目录（建议指向项目根目录）
- `--skip-login`: 跳过登录界面直接进入主页

---

## 资源文件定位机制

程序通过 `get_program_dir()` 统一定位资源与配置：

- 开发模式建议使用 `python src/main.py -d <项目根目录>`
- 资源目录下包含 `assets/`、`programs/`、`versions/`、`settings.json`、`users.dat`

---

## 测试架构说明

- 使用 Python 的 `unittest` 框架
- 测试文件位于 `tests/` 目录，目前仅包含 `slog_parser` 测试
- 测试命令：`python -m unittest tests.test_slog_parser`

---

## 重要注意事项

### 线程清理
- QThread 完成后需断开信号并调用 `deleteLater()`
- 长耗时任务需提供停止或取消机制（若支持）

### Windows PATH 修改
- 环境配置界面使用 `winreg` 修改注册表
- 修改后需要重启应用程序或系统才能生效
