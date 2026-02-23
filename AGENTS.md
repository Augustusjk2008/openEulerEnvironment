# AGENTS.md - RTopenEuler 系统管理工具项目指南

## 项目概述

**RTopenEuler 系统管理工具**是一个面向 openEuler 嵌入式开发环境的集成管理平台，由上海航天八院（803所）开发。该工具采用 PyQt5 + PyQt-Fluent-Widgets 构建，提供现代化的 Fluent 设计语言界面。

### 核心功能

| 功能模块 | 说明 |
|---------|------|
| 开发环境配置 | 一键部署编译器、依赖库、工具链，自动配置环境变量 |
| 自动代码生成 | 根据产品型号和工程类型生成标准代码模板 |
| 设备初始化向导 | 通过 SSH 远程完成 CCU 设备的出厂初始化配置 |
| 远程终端 | SSH 交互式终端 |
| FTP 客户端 | 本地与远端文件上传、下载、移动 |
| 数据可视化 | 读取 SLOG 文件并绘制曲线 |
| 协议编辑器 | 协议配置与管理 |
| 算法编辑器 | 自动驾驶相关算法配置 |
| 教程与文档 | 配置指南、代码示例、版本说明 |

---

## 项目结构

```
openEulerEnvironment/
├── src/                          # 源代码目录
│   ├── main.py                   # 程序入口
│   ├── core/                     # 核心功能模块
│   │   ├── auth_manager.py       # 认证管理（登录/注册）
│   │   ├── autopilot_codegen_cpp.py  # 自动驾驶代码生成
│   │   ├── autopilot_document.py     # 自动驾驶文档处理
│   │   ├── config_manager.py     # 配置管理器
│   │   ├── font_manager.py       # 字体管理
│   │   ├── protocol_schema.py    # 协议模式定义
│   │   └── slog_parser.py        # SLOG 日志解析
│   └── ui/                       # 用户界面模块
│       ├── main_window.py        # 主窗口
│       ├── loading_dialog.py     # 加载对话框
│       ├── style_helper.py       # 样式辅助
│       └── interfaces/           # 各功能界面
│           ├── autopilot_editor_interface.py   # 算法编辑界面
│           ├── code_generation_interface.py    # 代码生成界面
│           ├── data_visualization_interface.py # 数据可视化界面
│           ├── environment_install_interface.py # 环境安装界面
│           ├── ftp_interface.py                # FTP 客户端界面
│           ├── home_interface.py               # 首页
│           ├── initializer_interface.py        # 设备初始化界面
│           ├── login_interface.py              # 登录界面
│           ├── protocol_editor_interface.py    # 协议编辑界面
│           ├── settings_interface.py           # 设置界面
│           ├── terminal_interface.py           # 远程终端界面
│           └── tutorial_interface.py           # 教程界面
├── docs/                         # 文档目录
│   ├── images/                   # 文档图片
│   ├── versions/                 # 版本历史
│   ├── 00.本程序怎么使用.md       # 用户使用手册
│   ├── 01.示例工程怎么编译、调试、运行.md
│   ├── 02.MB数据分发框架（MB_DDF）介绍.md
│   ├── 03.RTopenEuler实时操作系统介绍.md
│   ├── 04.RTopenEuler启动脚本详解.md
│   └── environment_guide.md      # Python 环境操作指南
├── requirements.txt              # Python 依赖
├── run.bat                       # 运行/构建脚本
├── pyimod04_pywin32.py          # PyInstaller Win7 兼容补丁
└── .gitignore                    # Git 忽略配置
```

---

## 技术栈

### 核心依赖

| 依赖 | 版本 | 用途 |
|-----|------|------|
| PyQt5 | 5.15.9 | GUI 框架 |
| qfluentwidgets | latest | Fluent Design 组件库 |
| paramiko | 3.3.1 | SSH/FTP 连接 |
| matplotlib | latest | 数据可视化 |
| pyte | optional | 终端仿真 |

### 开发/构建工具

- **PyInstaller**: 打包为独立可执行文件
- **conda**: Python 环境管理

---

## 运行与构建

### 开发模式运行

```bash
# 简单启动（带资源目录）
run.bat simple

# 开发模式（跳过登录）
run.bat dev

# 或直接 Python 运行
python src/main.py -d H:\Resources\RTLinux\Environment --skip-login
```

### 构建可执行文件

```bash
# 构建
run.bat build

# 安装到指定目录
run.bat install

# 一键构建+安装
run.bat all
```

### 命令行参数

| 参数 | 说明 |
|-----|------|
| `-d, --dir` | 指定程序资源目录 |
| `--skip-login` | 跳过登录界面直接进入主页 |

---

## 核心模块详解

### 1. 配置管理 (config_manager.py)

**ConfigManager** 负责应用程序配置的读取、保存和管理。

**默认配置项：**
```python
{
    "font_size": "small",              # 字体大小: small/medium/large
    "remember_window_pos": False,      # 记住窗口位置
    "default_output_dir": r"C:\Projects",
    "default_install_dir": r"C:\openEulerTools",
    "ssh_host": "192.168.137.100",     # SSH 默认主机
    "ssh_username": "root",
    "ssh_password": "Shanghaith8",
    "ftp_host": "192.168.137.100",     # FTP 默认主机
    "ftp_username": "root",
    "ftp_password": "Shanghaith8",
    "auto_check_update": False,
    "show_log_timestamp": True,
    "confirm_before_init": True,
    "protocol_csv_dir": "",            # 协议 CSV 目录
    "autopilot_json_dir": "",          # AutoPilot JSON 目录
}
```

**配置文件位置：** `settings.json`（程序目录下）

### 2. 主窗口 (main_window.py)

**MainWindow** 继承自 `FluentWindow`，提供导航栏和多个子界面。

**界面加载顺序：**
1. 首页 (Home)
2. 环境配置 (Environment)
3. 系统初始化 (Initializer)
4. 代码生成 (CodeGen)
5. 教程文档 (Tutorial)
6. 远程终端 (Terminal)
7. FTP 客户端 (FTP)
8. 数据可视化 (Data Visualization)
9. 协议编辑 (Protocol Editor)
10. 算法编辑 (Autopilot Editor)
11. 设置 (Settings)

**窗口规格：**
- 默认大小: 1700×1050 像素
- 居中显示

### 3. 登录认证 (auth_manager.py + login_interface.py)

- 支持用户注册（需 16 位邀请码）
- 登录成功后进入主窗口
- 开发模式可跳过登录

### 4. 代码生成 (code_generation_interface.py)

支持的工程类型：
- Hello_World
- MB_DDF
- Helm_Control
- Auto_Pilot
- Upgrade_And_Test
- No8RtBus

### 5. 设备初始化 (initializer_interface.py)

通过 SSH 远程完成 CCU 设备出厂初始化：
- 设置 root 密码
- 创建目录结构
- 上传必要文件
- 配置动态库路径
- 硬盘扩容
- 运行安全测试
- 配置系统时间并重启

---

## 相关技术背景

### RTopenEuler 实时操作系统

- **基线**: openEuler 24.03 LTS + Linux 5.10 + preempt-rt 89补丁
- **目标平台**: 瑞芯微 RK3588（ARM64）
- **实时性能**:
  - 最大中断延迟 < 8微秒
  - 任务切换时间 < 5微秒
  - 调度器抖动 < 10微秒

### MB_DDF 数据分发框架

- 基于共享内存的发布-订阅模式
- 支持 C++ 与 Python 跨语言交互
- 零拷贝数据传输
- 时间确定性通信

---

## 开发规范

### 代码风格

- 遵循 PEP 8 Python 编码规范
- 使用类型注解提高代码可读性
- 关键功能添加文档字符串

### 界面开发

- 使用 PyQt-Fluent-Widgets 组件保持界面一致性
- 耗时操作使用多线程避免界面卡顿
- 统一使用 FontManager 管理字体大小

### 配置管理

- 所有用户可配置项通过 ConfigManager 管理
- 新增配置项需在 `DEFAULT_CONFIG` 中定义默认值

---

## 常见问题

### 1. 资源目录设置

程序运行需要指定资源目录（包含 assets、templates 等）：
```bash
python src/main.py -d H:\Resources\RTLinux\Environment
```

### 2. 字体管理

字体大小分三级：small(10px)、medium(13px)、large(16px)
修改后需重启应用生效。

### 3. SSH/FTP 连接

默认连接目标设备：
- IP: 192.168.1.29
- 用户名: root
- 密码: Shanghaith8

### 4. 打包问题

- 使用 PyInstaller 打包时包含 `--hidden-import pyimod04_pywin32` 以支持 Win7
- 打包前确保所有依赖已安装

---

## 版本历史

| 版本 | 日期 | 主要更新 |
|-----|------|---------|
| v0.0.7 | - | 最新版本 |
| v0.0.6 | - | - |
| v0.0.5 | 2026-01-13 | 抢先版发布 |

---

## 参考资料

- [PyQt-Fluent-Widgets 文档](https://qfluentwidgets.com/)
- [RTopenEuler 操作系统文档](docs/03.RTopenEuler实时操作系统介绍.md)
- [MB_DDF 框架文档](docs/02.MB数据分发框架（MB_DDF）介绍.md)
- [用户使用手册](docs/00.本程序怎么使用.md)

---

## 开发团队

- **开发单位**: 上海航天八院 803所
- **项目用途**: 面向 openEuler 嵌入式开发环境的集成管理平台
