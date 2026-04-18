# openEulerEnvironment

Windows-focused desktop management tool for RTopenEuler / openEuler embedded development workflows.

> Chinese-first repository. The root README provides the public overview; detailed product and usage docs remain under `docs/`.

## What It Does

- Install and deploy embedded development environment resources
- Connect to target devices over SSH / SFTP
- Generate project code templates
- Edit and export protocol definitions
- Edit autopilot algorithm documents
- Visualize `.slog` data files
- Browse bundled tutorials and version notes

## Tech Stack

- Python
- PyQt5
- PyQt-Fluent-Widgets
- paramiko
- matplotlib

## Current Scope

- Primary development target: Windows
- Packaging scripts currently focus on Windows desktop distribution
- Some test tiers require an Ubuntu VM or a real device and are not part of the public CI baseline

## Quick Start

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python src/main.py --skip-login
```

Optional:

```powershell
python src/main.py -d C:\path\to\resources
```

## Testing

Public unit baseline:

```powershell
pytest tests/unit -q -m "not gui and not ubuntu_vm and not real_device"
```

Other test tiers:

- `tests/integration`: requires environment variables for an Ubuntu VM
- `tests/e2e`: requires extra GUI or device-specific setup
- GUI tests: require PyQt-capable local setup and are intentionally excluded from CI

## Documentation

- [User Manual](docs/00.本程序怎么使用.md)
- [Example Project Guide](docs/01.示例工程怎么编译、调试、运行.md)
- [Version Notes](docs/versions/)
- [VM Setup Guide](docs/vm_setup_guide.md)

## Packaging Notes

- `run.bat` contains convenience commands for local Windows workflows
- `setup_cxfreeze.py` and `openEulerManage.spec` are retained for Windows packaging maintenance
- Windows 7 compatibility constraints still apply to the legacy packaging flow

## Repository Status

This repository is being prepared for a minimal public release. The current cleanup focuses on repository hygiene, public documentation, and a stable open-source baseline rather than on large architectural changes.
