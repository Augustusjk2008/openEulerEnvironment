# Agent Team 任务：Phase 1 测试基础设施搭建

## 任务概述

**本任务需要建立一支Agent测试专家团队**，通过多角色协作完成RTopenEuler系统管理工具的测试基础设施搭建。

**重要原则**：
- 设备初始化向导只在真实目标板(192.168.1.29)测试，不在Ubuntu虚拟机测试
- **绝对不允许修改原有源代码**，所有测试代码新建于tests目录
- 团队协作，互相审查，迭代至所有专家满意

## 第一步：清理历史（所有角色执行前必须先完成）

```bash
# 删除tests目录下所有原有内容，从头开始
# 保留tests目录本身，但清空其内容
```

**原有tests内容**：`list_icons.py`、`test_slog_parser.py` → **全部删除**

## 团队角色配置（5人专家组）

### 角色1：测试架构师 (Test Architect)

**职责**：
- 设计整体测试框架结构
- 制定技术选型决策（pytest配置、目录结构、Mock策略）
- 审查其他角色的方案，确保架构一致性
- 最终验收所有交付物

**目标输出**：
- `tests/pytest.ini` - 主配置文件
- `tests/conftest.py` - 全局fixture和标记定义
- `.coveragerc` - 覆盖率配置
- `docs/test_architecture.md` - 架构设计文档（说明设计决策）

**审查重点**：
- 是否支持pytest-qt
- 是否正确标记@ubuntu_vm和@real_device
- 覆盖率配置是否合理
- 是否Windows/Conda环境兼容

---

### 角色2：核心模块测试专家 (Core Module Tester)

**职责**：
- 负责src/core/下模块的单元测试
- 设计ConfigManager、SSHUtils、SlogParser等的测试策略
- 提供Mock方案（不依赖外部设备）

**目标输出**：
- `tests/unit/core/test_config_manager.py`
- `tests/unit/core/test_ssh_utils.py`
- `tests/unit/core/test_slog_parser.py`
- `tests/fixtures/mocks/mock_config.py`
- `tests/fixtures/mocks/mock_ssh_server.py`

**审查重点**：
- 是否使用临时目录隔离测试（不污染真实配置）
- Mock是否彻底（不依赖外部网络）
- 是否覆盖主要业务场景和边界情况

---

### 角色3：集成测试专家 (Integration Tester)

**职责**：
- 设计集成测试策略
- 配置Ubuntu虚拟机(192.168.56.132)连接参数
- 设计真实SSH/SFTP测试用例（可选执行）

**目标输出**：
- `tests/config/test_env.yaml` - 环境配置
- `tests/integration/__init__.py`
- `tests/integration/test_ssh_workflow.py` （标记@ubuntu_vm）
- `tests/utils/test_helpers.py` - 测试工具函数

**审查重点**：
- 是否正确区分本地测试和需要VM的测试
- 环境配置是否清晰（含占位符说明）
- 是否有环境跳过机制

---

### 角色4：UI测试专家 (UI Tester)

**职责**：
- 设计UI自动化测试策略
- 配置pytest-qt环境
- 为主窗口和关键界面设计测试方案

**目标输出**：
- `tests/unit/ui/test_style_helper.py`
- `tests/unit/ui/test_main_window_navigation.py`
- `tests/e2e/__init__.py`
- `docs/ui_test_strategy.md` - UI测试策略说明

**审查重点**：
- QApplication单例处理是否正确
- 是否避免界面卡顿（多线程相关）
- 是否有图形界面依赖的跳过机制

---

### 角色5：质量审查员 (Quality Inspector)

**职责**：
- **不直接产出代码**，只负责审查
- 编写测试报告模板
- 检查代码修改建议
- 最终出具阶段性报告

**目标输出**：
- `docs/phase1_review_report.md` - Phase 1审查报告
- `docs/test_code_suggestions.md` - 源代码修改建议
- `tests/verify_setup.py` - 框架验证脚本

**审查清单**：
- [ ] 所有角色输出是否完整
- [ ] 是否真的没有修改原代码
- [ ] tests目录结构是否规范
- [ ] 是否可以通过 `pytest tests/ -v` 运行
- [ ] 覆盖率报告是否生成
- [ ] 约束条件是否全部满足

---

## 团队协作流程（迭代制）

### 第一轮：各自独立完成（每个角色）

每个专家根据职责独立完成自己的任务，创建所需文件。

### 第二轮：交叉审查（必须执行）

每个角色必须被至少2个其他角色审查：

| 被审查角色 | 审查者 |
|-----------|--------|
| 测试架构师 | 核心模块测试专家 + 质量审查员 |
| 核心模块测试专家 | 测试架构师 + 集成测试专家 |
| 集成测试专家 | UI测试专家 + 质量审查员 |
| UI测试专家 | 测试架构师 + 核心模块测试专家 |
| 质量审查员 | 测试架构师（最终审查） |

**审查方式**：
- 在 `docs/review/` 目录下创建审查意见文件
- 命名格式：`{审查者}_review_{被审查者}.md`
- 必须包含：问题清单、改进建议、是否通过

### 第三轮：返工修改（如需要）

被审查不通过的角色必须返工，直到审查者满意。

**返工记录**：在审查文件中追加修改记录。

### 第四轮：质量审查员最终验收

质量审查员检查全部输出，出具Phase 1审查报告。

---

## 约束条件（红线，绝对不可违反）

### 1. 不修改原有代码

```
❌ 禁止修改 src/ 下任何文件
❌ 禁止修改 requirements.txt（除非新增测试依赖注释段）
❌ 禁止修改 run.bat
✅ 只允许在 tests/ 目录下新建文件
```

### 2. 目录结构规范

所有文件必须位于正确位置：

```
tests/
├── pytest.ini              # 测试架构师
├── conftest.py             # 测试架构师
├── __init__.py
├── unit/                   # 单元测试
│   ├── __init__.py
│   ├── core/              # 核心模块测试专家
│   │   ├── __init__.py
│   │   ├── test_config_manager.py
│   │   ├── test_ssh_utils.py
│   │   └── test_slog_parser.py
│   └── ui/                # UI测试专家
│       ├── __init__.py
│       └── test_*.py
├── integration/            # 集成测试专家
│   ├── __init__.py
│   └── test_ssh_workflow.py
├── e2e/                    # UI测试专家（框架）
│   └── __init__.py
├── fixtures/               # 各角色按需创建
│   ├── __init__.py
│   ├── data/
│   └── mocks/
├── utils/                  # 集成测试专家
│   ├── __init__.py
│   └── test_helpers.py
└── config/                 # 集成测试专家
    └── test_env.yaml
```

### 3. 测试环境适配

| 环境变量 | 用途 | 设置方式 |
|---------|------|---------|
| `UBUNTU_VM_AVAILABLE=1` | 启用Ubuntu虚拟机测试 | 手动设置 |
| `REAL_DEVICE_TEST=1` | 启用真实设备测试（危险） | 手动设置 |

---

## 交付物清单

### 代码交付物

| 文件 | 负责角色 | 说明 |
|------|---------|------|
| `tests/pytest.ini` | 测试架构师 | pytest主配置 |
| `tests/conftest.py` | 测试架构师 | fixture和标记 |
| `.coveragerc` | 测试架构师 | 覆盖率配置 |
| `tests/unit/core/test_*.py` | 核心模块测试专家 | 单元测试 |
| `tests/fixtures/mocks/*.py` | 核心模块测试专家 | Mock实现 |
| `tests/config/test_env.yaml` | 集成测试专家 | 环境配置 |
| `tests/integration/*.py` | 集成测试专家 | 集成测试 |
| `tests/utils/*.py` | 集成测试专家 | 工具函数 |
| `tests/unit/ui/*.py` | UI测试专家 | UI测试 |
| `tests/e2e/__init__.py` | UI测试专家 | E2E框架 |
| `tests/verify_setup.py` | 质量审查员 | 验证脚本 |

### 文档交付物

| 文件 | 负责角色 | 说明 |
|------|---------|------|
| `docs/test_architecture.md` | 测试架构师 | 架构设计说明 |
| `docs/ui_test_strategy.md` | UI测试专家 | UI测试策略 |
| `docs/review/*.md` | 所有角色 | 交叉审查记录 |
| `docs/phase1_review_report.md` | 质量审查员 | Phase 1最终报告 |
| `docs/test_code_suggestions.md` | 质量审查员 | 源代码修改建议 |

---

## 阶段性报告要求

### 中期检查点（Day 2-3）

每个角色需输出：`docs/progress/{角色名}_day2.md`

内容：
- 已完成工作
- 遇到的问题
- 需要其他角色配合的事项
- 预计完成时间

### 最终报告要求

**质量审查员必须输出**：

1. **Phase 1审查报告** (`docs/phase1_review_report.md`)
   - 各角色完成度评估
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

- [ ] **没有修改src/** 目录下任何原有代码
- [ ] **tests旧内容已清空** （原有list_icons.py等已删除）
- [ ] **pytest可运行** (`pytest tests/unit/ -v` 正常执行)
- [ ] **覆盖率报告生成** (`pytest --cov=src` 成功)
- [ ] **目录结构规范** (符合上述结构)
- [ ] **环境标记正确** (@ubuntu_vm, @real_device)
- [ ] **文档完整** (所有文档交付物已产出)
- [ ] **交叉审查完成** (review目录下有记录)

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

### 关键设计决策（供参考）

1. **设备初始化向导不Mock**：只在192.168.1.29真实设备测试
2. **Ubuntu VM用于SSH/SFTP**：测试基础连接、文件传输
3. **Mock仅用于单元测试**：不依赖外部网络
4. **QApplication单例**：使用session级fixture
5. **临时目录隔离**：所有配置、文件测试使用tmp_path

---

## 启动指令

**团队负责人（Team Lead）启动任务**：

1. 首先执行清理：`rm tests/*.py tests/**/*.py`（保留目录）
2. 分配角色给各agent
3. 建立`docs/review/`目录
4. 设定截止时间
5. 每日检查progress文档
6. 组织交叉审查
7. 最终验收并输出报告

**各角色Agent启动后先阅读**：
- 本文档（明确职责和约束）
- `docs/agent_team_test_plan.md`（整体规划）
- `AGENTS.md`（项目背景）
- `src/core/`下相关源码（了解被测代码）
