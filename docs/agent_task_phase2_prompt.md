# Agent Team 任务：Phase 2 测试完善与核心模块覆盖

## 任务概述

本任务需要建立一支Agent测试专家团队，**先修复Phase 1遗留问题，然后完成核心模块单元测试**，确保测试框架可正常运行并达到目标覆盖率。

**重要原则**：
- 设备初始化向导只在真实目标板(192.168.1.29)测试，不在Ubuntu虚拟机测试
- **绝对不允许修改原有源代码**，所有测试代码新建于tests目录
- 团队协作，互相审查，迭代至所有专家满意

---

## Phase 1 遗留问题修复（必须先完成）

### 问题1：pytest配置修复

**文件**: `tests/pytest.ini`

**问题描述**:
- `qt_api` 和 `env` 配置选项需要特定插件支持
- `rootdir` 和 `pythonpath` 配置可能导致导入错误

**修复方案**:
```ini
[pytest]
minversion = 6.0
# 移除或注释掉不兼容的配置
# qt_api = pyqt5  # 需要pytest-qt插件时才启用
# env = ...       # 需要pytest-env插件时才启用

# 正确的路径配置
pythonpath = src
testpaths = tests/unit, tests/integration, tests/e2e

python_files = test_*.py
python_classes = Test*
python_functions = test_*

addopts =
    -v
    --tb=short
    --durations=10

markers =
    ubuntu_vm: marks tests that require an Ubuntu VM
    real_device: marks tests that require a real target device
    slow: marks tests as slow
    gui: marks tests that require GUI

# Qt配置（如果安装了pytest-qt）
# qt_api = pyqt5

log_cli = true
log_cli_level = INFO
log_cli_format = %(asctime)s [%(levelname)8s] %(message)s (%(filename)s:%(lineno)s)
log_cli_date_format = %Y-%m-%d %H:%M:%S

filterwarnings =
    ignore::DeprecationWarning:PyQt5.*:
    ignore::PendingDeprecationWarning:PyQt5.*:
```

**验证方式**:
```bash
conda activate pyqt5_env
cd H:\WorkSpace\PythonWorkspace\openEulerEnvironment
pytest tests/unit/core/test_config_manager.py -v
# 应该能正确发现并运行测试，无导入错误
```

---

### 问题2：补充交叉审查记录

**文件**: `docs/review/{审查者}_review_{被审查者}.md`

**问题描述**: Phase 1缺少具体的交叉审查记录，只有README.md。

**修复方案**:
根据Phase 1实际完成情况，补充以下审查记录（如实际未执行交叉审查，则记录自检结果）：

```markdown
# 审查记录：{审查者} 审查 {被审查者}

**审查日期**: 2026-02-16
**审查者**: {角色名}
**被审查者**: {角色名}

## 审查内容

### 交付物检查
- [ ] 文件是否完整
- [ ] 代码是否符合规范
- [ ] 文档是否清晰

### 发现的问题
1. ...

### 改进建议
1. ...

### 审查结论
- [ ] 通过
- [ ] 需返工

## 返工记录（如需要）
- 问题1修复：...
- 问题2修复：...
```

**需要补充的记录**（根据Phase 1实际执行情况进行自检并记录）：
- `core_tester_review_architect.md` - 核心模块测试专家审查测试架构师
- `integration_tester_review_core_tester.md` - 集成测试专家审查核心模块测试专家
- `ui_tester_review_integration_tester.md` - UI测试专家审查集成测试专家
- `architect_review_ui_tester.md` - 测试架构师审查UI测试专家
- `inspector_final_review.md` - 质量审查员最终审查汇总

---

### 问题3：依赖安装确认

**确保以下依赖已安装**:

```bash
conda activate pyqt5_env
pip install pytest pytest-cov pytest-qt pytest-timeout pyyaml
```

**验证方式**:
```bash
pytest --version
pytest-cov --version  # 应显示已安装
python -c "import pytest_qt; print('pytest-qt OK')"
```

---

## Phase 2 任务：核心模块测试完善

### 目标

1. **修复Phase 1问题**（上述3个问题）
2. **确保测试可运行** - `pytest tests/unit/ -v` 正常执行
3. **达到目标覆盖率** - 核心模块覆盖率达到要求
4. **产出测试报告** - 覆盖率报告、问题清单、修改建议

### 覆盖率目标

| 模块 | 目标覆盖率 | 当前状态 | 优先级 |
|------|-----------|----------|--------|
| config_manager | 90% | 待评估 | P0 |
| ssh_utils | 85% | 待评估 | P0 |
| slog_parser | 80% | 待评估 | P1 |
| auth_manager | 75% | 未开始 | P1 |
| ui/style_helper | 60% | 待评估 | P2 |

---

## 团队角色配置（4人专家组）

### 角色1：测试修复专家 (Fix Specialist)

**职责**：
- 修复Phase 1遗留的pytest配置问题
- 修复测试导入路径问题
- 确保 `pytest tests/unit/ -v` 能正常运行
- 补充交叉审查记录

**目标输出**：
- 修复后的 `tests/pytest.ini`
- 修复后的 `tests/conftest.py`（如需要）
- `docs/review/*.md` - 补充的审查记录
- `docs/phase1_fix_report.md` - 修复报告

**验收标准**：
- [ ] `pytest tests/unit/core/test_config_manager.py -v` 正常运行
- [ ] `pytest tests/unit/core/test_ssh_utils.py -v` 正常运行
- [ ] `pytest tests/unit/core/test_slog_parser.py -v` 正常运行
- [ ] 交叉审查记录完整

---

### 角色2：核心模块测试专家 (Core Module Tester)

**职责**：
- 完善config_manager、ssh_utils、slog_parser的单元测试
- 确保达到目标覆盖率
- 添加边界条件、异常处理测试
- 编写auth_manager单元测试

**目标输出**：
- 完善的 `tests/unit/core/test_config_manager.py`（目标：90%覆盖）
- 完善的 `tests/unit/core/test_ssh_utils.py`（目标：85%覆盖）
- 完善的 `tests/unit/core/test_slog_parser.py`（目标：80%覆盖）
- 新建的 `tests/unit/core/test_auth_manager.py`（目标：75%覆盖）
- `docs/core_module_test_report.md` - 测试报告

**测试覆盖要求**：
```python
# ConfigManager测试应覆盖：
# - 正常读写配置
# - 默认值处理
# - 配置持久化
# - 配置重置
# - 异常处理（文件不存在、JSON格式错误等）
# - 边界值（空字符串、特殊字符、长字符串）

# SSHUtils测试应覆盖：
# - SSH连接建立/关闭
# - 命令执行（正常返回、错误返回、超时）
# - SFTP文件操作（上传、下载、删除、列表）
# - 连接异常处理（网络不通、认证失败、超时）
# - 多线程并发（如适用）

# SlogParser测试应覆盖：
# - 正常文件解析
# - 各种数据类型（Float32, Float64, Int32, etc.）
# - 空文件处理
# - 损坏文件处理
# - 大文件性能
```

**验收标准**：
- [ ] config_manager测试覆盖率达到90%
- [ ] ssh_utils测试覆盖率达到85%
- [ ] slog_parser测试覆盖率达到80%
- [ ] auth_manager测试覆盖率达到75%
- [ ] 所有测试用例通过

---

### 角色3：集成测试专家 (Integration Tester)

**职责**：
- 准备Ubuntu虚拟机(192.168.56.132)测试环境
- 编写SSH集成测试（标记@ubuntu_vm）
- 编写SFTP集成测试
- 验证真实SSH连接

**目标输出**：
- `docs/vm_setup_guide.md` - 虚拟机环境准备指南
- 完善的 `tests/integration/test_ssh_workflow.py`
- 新建的 `tests/integration/test_sftp_workflow.py`
- `tests/integration/conftest.py` - 集成测试专用fixture
- `docs/integration_test_report.md` - 集成测试报告

**VM环境准备清单**：
```bash
# 在192.168.56.132上执行：
sudo apt-get update
sudo apt-get install -y openssh-server
sudo systemctl enable ssh
sudo systemctl start ssh

# 创建测试用户
sudo useradd -m testuser
sudo passwd testuser  # 设置密码
sudo usermod -aG sudo testuser

# 创建测试目录
sudo mkdir -p /home/testuser/sftp_test
sudo chown testuser:testuser /home/testuser/sftp_test

# 记录信息：
# IP: 192.168.56.132
# 用户名: testuser
# 密码: （设置的实际密码）
# 测试目录: /home/testuser/sftp_test
```

**测试用例要求**：
```python
# SSH工作流测试（标记@ubuntu_vm）
# - 连接成功/失败
# - 执行简单命令（ls, pwd, echo）
# - 执行复杂命令（管道、重定向）
# - 连接超时处理
# - 认证失败处理

# SFTP工作流测试（标记@ubuntu_vm）
# - 上传文件（小文件、大文件）
# - 下载文件
# - 删除文件
# - 列出目录
# - 文件权限验证
```

**验收标准**：
- [ ] VM环境准备文档完整
- [ ] SSH集成测试可运行（设置UBUNTU_VM_AVAILABLE=1时）
- [ ] SFTP集成测试可运行
- [ ] 测试在无VM时自动跳过（不失败）

---

### 角色4：质量审查员 (Quality Inspector)

**职责**：
- **不直接产出代码**，只负责审查
- 审查Phase 1问题修复情况
- 审查Phase 2测试质量
- 运行覆盖率分析
- 出具最终报告

**目标输出**：
- `docs/phase2_review_report.md` - Phase 2审查报告
- `docs/test_code_suggestions.md` - 更新的源代码修改建议（填充发现的问题）
- `tests/reports/coverage_report.md` - 覆盖率分析报告
- `docs/review/*.md` - Phase 2交叉审查记录

**审查清单**：
```markdown
## Phase 2 审查清单

### Phase 1修复验证
- [ ] pytest配置修复完成
- [ ] 测试可正常运行
- [ ] 交叉审查记录补充完整

### 测试质量审查
- [ ] 单元测试覆盖所有主要功能路径
- [ ] 边界条件和异常处理有测试
- [ ] 测试命名清晰、有注释
- [ ] 没有重复测试
- [ ] Mock使用恰当

### 覆盖率审查
- [ ] config_manager >= 90%
- [ ] ssh_utils >= 85%
- [ ] slog_parser >= 80%
- [ ] auth_manager >= 75%

### 集成测试审查
- [ ] VM测试环境文档完整
- [ ] 集成测试标记正确
- [ ] 无VM时测试自动跳过

### 文档审查
- [ ] 所有报告文档完整
- [ ] 问题描述清晰
- [ ] 修改建议可行
```

**覆盖率报告要求**:
```bash
# 生成覆盖率报告
conda activate pyqt5_env
cd H:\WorkSpace\PythonWorkspace\openEulerEnvironment
pytest tests/unit/ --cov=src --cov-report=html --cov-report=term

# 报告应包含：
# - 整体覆盖率
# - 各模块覆盖率
# - 未覆盖代码行列表
# - 改进建议
```

**验收标准**：
- [ ] 所有审查清单项已检查
- [ ] 覆盖率报告已生成
- [ ] 源代码修改建议已更新（如发现问题）
- [ ] Phase 2最终报告已产出

---

## 团队协作流程（迭代制）

### 第一轮：问题修复（测试修复专家主导）

1. 测试修复专家修复pytest配置
2. 测试修复专家补充交叉审查记录
3. 其他角色自检并修复各自负责模块的问题

### 第二轮：测试完善（各角色并行）

| 角色 | 任务 |
|------|------|
| 测试修复专家 | 验证所有测试可运行，协助解决运行问题 |
| 核心模块测试专家 | 完善单元测试，提升覆盖率 |
| 集成测试专家 | 准备VM环境，编写集成测试 |
| 质量审查员 | 开始跟踪进度，准备审查 |

### 第三轮：交叉审查（必须执行）

每个角色产出物需被审查：

| 被审查角色 | 审查者 |
|-----------|--------|
| 测试修复专家 | 核心模块测试专家 + 质量审查员 |
| 核心模块测试专家 | 测试修复专家 + 集成测试专家 |
| 集成测试专家 | 核心模块测试专家 + 质量审查员 |
| 质量审查员 | 测试修复专家（最终审查） |

**审查方式**：
- 在 `docs/review/phase2/` 目录下创建审查意见文件
- 命名格式：`{审查者}_review_{被审查者}_phase2.md`
- 必须包含：问题清单、改进建议、是否通过

### 第四轮：返工与最终验收（如需要）

- 不通过的产出需返工
- 质量审查员运行最终覆盖率检查
- 出具Phase 2最终报告

---

## 约束条件（红线，绝对不可违反）

### 1. 不修改原有代码

```
❌ 禁止修改 src/ 下任何文件
❌ 禁止修改 requirements.txt（除非新增测试依赖注释段）
❌ 禁止修改 run.bat
✅ 只允许在 tests/ 目录下新建文件
✅ 只允许修改 tests/ 目录下的文件
```

### 2. 测试可运行性

```
✅ pytest tests/unit/ -v 必须正常执行
✅ pytest tests/unit/ --cov=src 必须生成覆盖率报告
✅ 无VM时 @ubuntu_vm 标记测试自动跳过（不失败）
```

### 3. 覆盖率要求

```
config_manager: >= 90%
ssh_utils: >= 85%
slog_parser: >= 80%
auth_manager: >= 75%
```

---

## 交付物清单

### 代码交付物

| 文件 | 负责角色 | 说明 |
|------|---------|------|
| `tests/pytest.ini` (修复后) | 测试修复专家 | pytest配置 |
| `tests/unit/core/test_*.py` (完善后) | 核心模块测试专家 | 单元测试 |
| `tests/integration/test_sftp_workflow.py` | 集成测试专家 | SFTP集成测试 |
| `tests/integration/conftest.py` | 集成测试专家 | 集成测试fixture |

### 文档交付物

| 文件 | 负责角色 | 说明 |
|------|---------|------|
| `docs/phase1_fix_report.md` | 测试修复专家 | Phase 1修复报告 |
| `docs/review/phase2/*.md` | 所有角色 | Phase 2交叉审查记录 |
| `docs/vm_setup_guide.md` | 集成测试专家 | VM环境准备指南 |
| `docs/core_module_test_report.md` | 核心模块测试专家 | 核心模块测试报告 |
| `docs/integration_test_report.md` | 集成测试专家 | 集成测试报告 |
| `tests/reports/coverage_report.md` | 质量审查员 | 覆盖率分析报告 |
| `docs/test_code_suggestions.md` (更新) | 质量审查员 | 源代码修改建议（填充） |
| `docs/phase2_review_report.md` | 质量审查员 | Phase 2最终审查报告 |

---

## 阶段性报告要求

### 中期检查点（Day 2-3）

每个角色需输出：`docs/progress/phase2/{角色名}_day2.md`

内容：
- 已完成工作
- Phase 1修复进展
- 遇到的问题
- 需要其他角色配合的事项
- 预计完成时间

### 最终报告要求

**质量审查员必须输出**：

1. **Phase 2审查报告** (`docs/phase2_review_report.md`)
   - Phase 1修复情况验证
   - 各角色完成度评估
   - 覆盖率分析结果
   - 发现的问题清单
   - 是否通过验收
   - 下一步建议

2. **源代码修改建议** (`docs/test_code_suggestions.md`)
   - 基于测试过程中发现的源代码问题
   - 按优先级排序
   - 说明修改理由

---

## 验收标准（必须全部满足）

质量审查员负责验证：

- [ ] **Phase 1问题已修复**
  - [ ] pytest配置修复完成
  - [ ] 测试可正常运行
  - [ ] 交叉审查记录补充完整
- [ ] **没有修改src/** 目录下任何原有代码
- [ ] **pytest可运行** (`pytest tests/unit/ -v` 正常执行，无失败)
- [ ] **覆盖率达标**
  - [ ] config_manager >= 90%
  - [ ] ssh_utils >= 85%
  - [ ] slog_parser >= 80%
  - [ ] auth_manager >= 75%
- [ ] **集成测试框架完成** (VM环境文档、集成测试代码)
- [ ] **文档完整** (所有文档交付物已产出)
- [ ] **交叉审查完成** (docs/review/phase2/ 下有记录)

---

## 技术参考

### 测试环境信息

| 项目 | 说明 |
|------|------|
| Windows版本 | Windows 7/10/11 |
| Python版本 | 3.8 (conda虚拟环境 pyqt5_env) |
| GUI框架 | PyQt5 5.15.9 + qfluentwidgets |
| SSH库 | paramiko 3.3.1 |
| Ubuntu VM | 192.168.56.132 (用于SSH/SFTP测试) |
| 目标设备 | 192.168.1.29 (仅设备初始化向导测试) |

### 覆盖率运行命令

```bash
# 激活环境
conda activate pyqt5_env

# 运行单元测试
pytest tests/unit/ -v

# 运行并生成覆盖率报告
pytest tests/unit/ --cov=src --cov-report=html --cov-report=term

# 查看HTML报告
tests/reports/coverage_html/index.html

# 运行特定模块测试
pytest tests/unit/core/test_config_manager.py -v

# 运行无VM的测试（跳过@ubuntu_vm标记）
pytest tests/ -v -m "not ubuntu_vm"
```

### 被测源码位置

- `src/core/config_manager.py` - 配置管理器
- `src/core/ssh_utils.py` - SSH工具
- `src/core/slog_parser.py` - SLOG解析器
- `src/core/auth_manager.py` - 认证管理器
- `src/ui/style_helper.py` - UI样式帮助

---

## 启动指令

**团队负责人（Team Lead）启动任务**：

1. 检查Phase 1文件完整性
2. 分配角色给各agent
3. 建立`docs/review/phase2/`目录
4. 建立`docs/progress/phase2/`目录
5. 设定截止时间
6. 先执行修复任务，再执行测试完善任务
7. 组织交叉审查
8. 最终验收并输出报告

**各角色Agent启动后先阅读**：
- 本文档（明确职责和约束）
- `docs/agent_team_test_plan.md`（整体规划）
- `docs/agent_task_phase1_prompt.md`（Phase 1要求）
- `docs/phase1_review_report.md`（Phase 1审查报告）
- `src/core/`下相关源码（了解被测代码）

---

## 关键成功因素

1. **先修复，后完善** - 确保测试可运行是最高优先级
2. **覆盖率导向** - 每个测试用例都应提升覆盖率
3. **文档驱动** - 问题、方案、决策都要记录
4. **持续验证** - 经常运行pytest，确保不破坏已有测试
