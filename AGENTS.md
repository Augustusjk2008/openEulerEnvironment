# AGENTS.md - openEulerEnvironment 仓库协作指南

## 项目定位

`openEulerEnvironment` 是一个面向 RTopenEuler / openEuler 嵌入式开发环境的桌面管理工具，技术栈以 `PyQt5 + qfluentwidgets + paramiko + matplotlib` 为主。主要能力包括：

- 开发环境安装与资源部署
- 设备初始化与 SSH/SFTP 操作
- 代码生成
- 协议编辑与导出
- 飞控算法编辑
- SLOG 数据可视化
- 教程文档展示

这个文件面向协作代理与维护者，重点说明“仓库现在是什么样”“应该怎样改”，而不是只做静态产品介绍。

---

## 全局约束

### 终端命令

遵循 `C:\Users\JiangKai\.codex\RTK.md`：

- 优先使用 `rtk <external-command>`
- `rtk` 无法直接代理 PowerShell cmdlet 时，优先使用 `rtk python -c "..."` 读取信息
- 只有在确实需要原始命令时再考虑 `rtk proxy ...`

示例：

```powershell
rtk git status --short
rtk rg --files
rtk pytest tests/unit/core -q
rtk python -c "from pathlib import Path; print(Path('src/main.py').read_text(encoding='utf-8'))"
```

### 代码修改原则

- 保持 `PyQt5 + qfluentwidgets` 现有交互风格，不要随意引入新的 UI 框架
- 耗时任务不要阻塞主线程；已有界面普遍假设重操作应异步执行
- 配置统一走 `ConfigManager`，不要在界面或业务逻辑里散落硬编码配置
- SSH / FTP 密码默认不应硬编码到源码；当前默认值为空，靠 `settings.json` 或界面输入
- 字体大小统一通过 `FontManager` 管理
- 修改导航页时，优先复用 `MainWindow` 里的懒加载模式，不要把所有重页面改回启动时一次性构建

---

## 仓库结构

当前仓库的关键目录与文件如下：

```text
openEulerEnvironment/
├── src/
│   ├── main.py
│   ├── core/
│   │   ├── auth_manager.py
│   │   ├── autopilot_codegen_cpp.py
│   │   ├── autopilot_document.py
│   │   ├── config_manager.py
│   │   ├── font_manager.py
│   │   ├── protocol_schema.py
│   │   ├── slog_parser.py
│   │   └── ssh_utils.py
│   └── ui/
│       ├── main_window.py
│       ├── loading_dialog.py
│       ├── style_helper.py
│       └── interfaces/
│           ├── autopilot_editor_interface.py
│           ├── code_generation_interface.py
│           ├── data_visualization_interface.py
│           ├── environment_install_interface.py
│           ├── ftp_interface.py
│           ├── home_interface.py
│           ├── initializer_interface.py
│           ├── login_interface.py
│           ├── protocol_editor_interface.py
│           ├── settings_interface.py
│           ├── terminal_interface.py
│           └── tutorial_interface.py
├── build_helpers/
│   ├── pyinstaller_pywin32.py
│   └── pyi_rth_pywin32_compat.py
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   ├── fixtures/
│   ├── config/
│   ├── reports/
│   └── pytest.ini
├── docs/
│   ├── 00.本程序怎么使用.md
│   ├── 01.示例工程怎么编译、调试、运行.md
│   ├── 02.MB数据分发框架（MB_DDF）介绍.md
│   ├── 03.RTopenEuler实时操作系统介绍.md
│   ├── 04.RTopenEuler启动脚本详解.md
│   ├── vm_setup_guide.md
│   ├── vm_auto_config.md
│   ├── versions/
│   ├── review/
│   └── superpowers/
├── run.bat
├── run_tests.bat
├── run_tests.ps1
├── openEulerManage.spec
├── requirements.txt
└── pyimod04_pywin32.py
```

---

## 运行与调试

### 应用入口

主入口是 `src/main.py`，支持两个关键参数：

- `-d / --dir`：指定程序资源目录
- `--skip-login`：跳过登录直接进入主页

常用命令：

```powershell
rtk python src/main.py -d H:\Resources\RTLinux\Environment
rtk python src/main.py -d H:\Resources\RTLinux\Environment --skip-login
```

### 批处理入口

`run.bat` 是项目约定的主要入口，当前支持：

- `simple`
- `dev`
- `build`
- `install`
- `pack`
- `all`

示例：

```powershell
run.bat dev
run.bat build
run.bat all
```

### 打包约束

- `PyInstaller` 打包要求当前解释器是 Python 3.8，否则 `run.bat build` / `all` 会直接失败
- Win7 兼容相关补丁在 `pyimod04_pywin32.py` 与 `build_helpers/` 中，修改打包链路时不要遗漏

---

## 测试约定

### pytest 入口

`tests/pytest.ini` 当前配置：

- `testpaths = tests/unit, tests/integration, tests/e2e`
- marker:
  - `ubuntu_vm`
  - `real_device`
  - `slow`
  - `gui`

常用命令：

```powershell
rtk pytest tests/unit/core -v --tb=short
rtk pytest tests/unit/ui -v --tb=short -m "not gui"
rtk pytest tests/integration -v --tb=short
```

### 自动化脚本

- `run_tests.bat`：CMD 测试入口
- `run_tests.ps1`：PowerShell 测试入口
- 两者都会尝试探测 Ubuntu VM `192.168.56.132`
- 集成测试依赖环境变量 `UBUNTU_VM_AVAILABLE=1`
- 真机测试依赖环境变量 `REAL_DEVICE_TEST=1`

### 测试实现注意事项

- 根目录 `conftest.py` 会在大量非 GUI 测试中 mock `PyQt5`、`qfluentwidgets`、`matplotlib` 等依赖
- 修改 UI 导入路径、初始化时机或第三方依赖时，要确认不会破坏现有 mock 策略
- 如果新增配置项、界面信号或导航页，至少补对应单元测试

---

## 关键实现事实

### 配置系统

`src/core/config_manager.py` 的当前行为：

- 所有配置统一写入 `settings.json`
- 配置文件位置取决于 `get_program_dir()`
- 若命令行传入 `-d`，配置文件落在该目录
- 若为打包运行，配置文件落在可执行文件所在目录
- 若直接源码运行且未传 `-d`，配置文件落在 `src/core/` 目录

当前默认配置重点如下：

- `font_size`: `small`
- `remember_window_pos`: `False`
- `window_pos`: `None`
- `default_output_dir`: `C:\Projects`
- `default_install_dir`: `C:\openEulerTools`
- `ssh_*` / `ftp_*`: 默认空字符串
- `protocol_csv_dir`: `""`
- `autopilot_json_dir`: `""`

修改配置项时：

1. 先更新 `ConfigManager.DEFAULT_CONFIG`
2. 如果用户可编辑，再同步更新 `SettingsInterface`
3. 如果会影响启动流程或资源目录，再检查 `main.py` 与相关界面

### 主窗口与导航

`src/ui/main_window.py` 当前不是简单的“全部页面一次性创建”模式，而是：

- `HomeInterface` 与 `SettingsInterface` 立即创建
- 其余较重页面通过 `_LazyInterfaceHost` 懒加载
- 页面首次切换时才真正构建控件

当前导航注册顺序是：

1. 首页
2. 环境配置
3. 代码生成
4. 远程终端
5. FTP 客户端
6. 数据可视化
7. 协议编辑
8. 算法编辑
9. 系统初始化
10. 教程文档
11. 设置（底部）

其他已知事实：

- 窗口初始化会先 `resize(1700, 1050)`，随后 `showMaximized()`
- 数据可视化页会根据 FTP 连接状态同步可用性
- 关闭窗口前会清理导航动画状态，避免已销毁对象被延迟回调访问

### 字体与设置页

- 字体大小分为 `small / medium / large`
- 设置页保存字体大小后，当前逻辑仍要求重启应用才能完全生效
- 新界面应继续使用 `FontManager` 提供的字号，而不是各自定义魔法数字

### 协议与编辑器相关

基于 `docs/versions/0.0.8.txt` 和现有源码，当前代码线已包含：

- 协议 `RESERVED` 字段类型支持
- 协议导出 Word 文档能力
- 飞控算法编辑器与相关文档处理/代码生成模块
- C++ 代码生成增强

如果继续扩展协议字段模型，请同步检查：

- `src/core/protocol_schema.py`
- `src/core/autopilot_codegen_cpp.py`
- `src/ui/interfaces/protocol_editor_interface.py`
- 对应 `tests/unit/core/` 与 `tests/unit/ui/`

---

## 常见修改建议

### 新增设置项

- 加入 `ConfigManager.DEFAULT_CONFIG`
- 在 `SettingsInterface` 增加加载、编辑、保存逻辑
- 如果该设置影响启动阶段，检查 `main.py` / `MainWindow`

### 新增导航页

- 在 `src/ui/interfaces/` 新增界面
- 优先在 `MainWindow` 中按懒加载方式注册
- 从首页跳转时同步补连接信号
- 增加至少一份导航或界面初始化测试

### 修改打包流程

- 同时检查 `run.bat`
- 同时检查 `openEulerManage.spec`
- 同时检查 `build_helpers/`
- 同时检查 `pyimod04_pywin32.py`
- 不要破坏 Win7 兼容目标与 Python 3.8 约束

---

## 参考文档

- 用户手册：`docs/00.本程序怎么使用.md`
- 示例工程说明：`docs/01.示例工程怎么编译、调试、运行.md`
- MB_DDF 文档：`docs/02.MB数据分发框架（MB_DDF）介绍.md`
- RTopenEuler 背景：`docs/03.RTopenEuler实时操作系统介绍.md`
- 启动脚本说明：`docs/04.RTopenEuler启动脚本详解.md`
- VM 搭建/自动化：`docs/vm_setup_guide.md`、`docs/vm_auto_config.md`
- 最新版本记录：`docs/versions/0.0.8.txt`

---

## 维护要求

出现以下变化时，必须同步更新本文件：

- 目录结构发生调整
- 运行命令、测试命令或打包链路变化
- 新增或删除主导航页
- 配置项默认值或配置文件落点变化
- 测试基础设施、VM 地址、设备接入方式变化
