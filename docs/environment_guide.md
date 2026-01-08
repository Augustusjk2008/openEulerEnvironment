# Python PyQt5 环境操作指南

本文档介绍了如何管理 Conda 环境以及如何打包 PyQt5 程序。

## 1. 环境创建回顾
使用以下命令创建一个 Python 3.8 的虚拟环境，并安装 PyQt5：

```bash
# 创建环境
conda create -n pyqt5_env python=3.8 -y

# 安装 PyQt5
conda run -n pyqt5_env pip install PyQt5
```

## 2. 查看 Conda 环境
要查看系统中已经创建的所有 Conda 环境，可以使用以下命令：

```bash
conda env list
# 或者
conda info --envs
```
在列表中，带有星号 `*` 的环境表示当前正处于激活状态的环境。

## 3. 激活与退出环境

### 激活环境
在 Windows 终端中，使用以下命令激活环境：
```bash
conda activate pyqt5_env
```

### 退出环境
要退出当前激活的环境并返回到 base 环境，请使用：
```bash
conda deactivate
```

## 4. 打包 Python 程序
打包程序可以将 Python 脚本转换为独立的可执行文件（.exe），这样即使没有安装 Python 的电脑也能运行。

### 安装打包工具
我们通常使用 `PyInstaller` 进行打包：
```bash
pip install pyinstaller
```

### 执行打包
在激活的环境下，运行以下命令打包程序：
```bash
pyinstaller --noconsole --onefile hello_world.py
```
**参数说明：**
- `--noconsole`: 运行时不显示黑色命令行窗口（适用于 GUI 程序）。
- `--onefile`: 将所有依赖打包成一个单独的 .exe 文件。

打包完成后，生成的可执行文件位于 `dist/` 目录下。

## 5. 安装 PyQt-Fluent-Widgets
PyQt-Fluent-Widgets 是一个基于 PyQt5 的 Material Design 风格的组件库。要安装它，请使用以下命令：
```bash
pip install PyQt-Fluent-Widgets
```