# Agent Team 任务：Phase 3 UI自动化与真实设备测试准备

## 任务概述

本任务需要建立一支Agent测试专家团队，**先修复Phase 2遗留问题，然后完成UI自动化测试和真实设备测试准备**，确保测试覆盖界面交互和设备初始化场景。

**重要原则**：
- 设备初始化向导只在真实目标板(192.168.1.29)测试，不在Ubuntu虚拟机测试
- **绝对不允许修改原有源代码**，所有测试代码新建于tests目录
- 团队协作，互相审查，迭代至所有专家满意

---

## Phase 2 遗留问题修复（必须先完成）

### 问题1：缺少Phase 2最终审查报告

**缺失文件**: `docs/phase2_review_report.md`

**问题描述**: 质量审查员未产出Phase 2最终审查报告，缺少正式的验收结论。

**修复方案**: 质量审查员基于以下已有文档编制最终报告：
- `docs/review/phase2/inspector_final_review.md` - 审查记录
- `docs/core_module_test_report.md` - 核心模块测试报告
- `docs/integration_test_report.md` - 集成测试报告
- `docs/phase1_fix_report.md` - Phase 1修复报告

**报告内容要求**:
```markdown
# Phase 2 最终审查报告

## 1. 执行摘要
- Phase 2目标回顾：核心模块单元测试达标、集成测试框架建立
- 总体完成状态：已完成/部分完成/未完成

## 2. Phase 1修复验证
- pytest配置修复确认：已修复，测试可运行
- 交叉审查记录补充：已补充6份审查记录

## 3. Phase 2完成评估

### 3.1 核心模块测试专家
- 交付物清单：4个核心模块测试文件
- 覆盖率达成情况：全部达标（93.51%, 97.32%, 89.04%, 98.11%）
- 测试通过率：171个测试全部通过
- 评估结论：达标

### 3.2 集成测试专家
- 交付物清单：VM指南、SSH/SFTP集成测试
- VM环境准备文档：已完成
- 集成测试用例：32个（15 SSH + 17 SFTP）
- 评估结论：达标

### 3.3 质量审查员
- 交付物清单：审查记录、覆盖率分析
- 评估结论：达标

## 4. 验收结论
- [x] pytest可运行
- [x] 核心模块达到目标覆盖率
- [x] 集成测试框架完成
- [x] 文档完整
- 总体评估：Phase 2通过验收

## 5. 遗留问题
- 无 / 如有请列出

## 6. 下一步建议
- Phase 3重点：UI自动化测试、真实设备测试准备
```

**验收标准**:
- [ ] 报告文件存在
- [ ] 包含所有关键评估项
- [ ] 有明确的验收结论

---

### 问题2：源代码修改建议未更新

**文件**: `docs/test_code_suggestions.md`

**问题描述**: 文档仍为Phase 1创建的模板状态，未填充Phase 2测试过程中发现的问题。

**修复方案**:

如果在Phase 2测试过程中**发现了源代码问题**，应记录：
```markdown
## 🔴 高优先级 (High)

| # | 文件 | 行号 | 问题描述 | 建议修改 | 发现者 | 发现时间 |
|---|------|------|----------|----------|--------|----------|
| 1 | core/config_manager.py | 28 | get_program_dir()中frozen情况难以测试 | 建议将frozen判断逻辑提取为可注入的依赖 | Core Tester | 2026-02-16 |
| 2 | core/ssh_utils.py | 187 | 异常处理分支难以触发 | 考虑重构异常处理逻辑，或提供更清晰的错误码 | Core Tester | 2026-02-16 |

## 🟡 中优先级 (Medium)

| # | 文件 | 行号 | 问题描述 | 建议修改 | 发现者 | 发现时间 |
|---|------|------|----------|----------|--------|----------|
| ... | ... | ... | ... | ... | ... | ... |
```

如果在Phase 2测试过程中**未发现明显问题**，应说明：
```markdown
## 审查结论

经Phase 2全面测试，未发现源代码存在明显缺陷或高风险问题。

各模块代码质量良好：
- config_manager: 结构清晰，可测试性良好
- ssh_utils: 接口设计合理，异常处理完整
- slog_parser: 解析逻辑稳健，边界处理到位
- auth_manager: 认证流程完整，安全性考虑充分

未发现需要高优先级修改的代码问题。
```

**验收标准**:
- [ ] 文档不再是空模板状态
- [ ] 有问题记录问题，无问题说明结论

---

## Phase 3 任务：UI自动化与真实设备测试

### 目标

1. **修复Phase 2问题**（补充最终报告、更新修改建议）
2. **完成UI自动化测试** - 主窗口、关键界面交互测试
3. **准备真实设备测试** - 设备初始化向导测试框架
4. **性能与稳定性测试** - 内存、并发、大文件处理

### 测试范围

| 模块 | 测试类型 | 说明 |
|------|----------|------|
| 主窗口导航 | UI自动化 | 页面切换、菜单操作、状态保持 |
| 登录界面 | UI自动化 | 输入验证、登录流程、错误提示 |
| 设置界面 | UI自动化 | 配置修改、保存、重置 |
| 设备初始化向导 | **真实设备** | 仅在192.168.1.29测试 |
| 协议/算法编辑器 | UI自动化 | 编辑、保存、验证 |
| 内存稳定性 | 性能测试 | 长期运行内存监控 |
| 并发SSH | 稳定性测试 | 多连接稳定性 |

---

## 团队角色配置（4人专家组）

### 角色1：报告完善专家 (Report Specialist)

**职责**：
- 修复Phase 2遗留问题
- 编制Phase 2最终审查报告
- 更新源代码修改建议文档
- 整理Phase 1-2文档归档

**目标输出**：
- `docs/phase2_review_report.md` - Phase 2最终审查报告
- `docs/test_code_suggestions.md` (更新版) - 源代码修改建议
- `docs/archive/phase1_2_summary.md` - Phase 1-2阶段总结

**验收标准**：
- [ ] Phase 2最终报告存在且内容完整
- [ ] 修改建议文档已填充（有问题记录/无问题说明）
- [ ] 所有文档通过质量审查员审查

---

### 角色2：UI自动化测试专家 (UI Automation Tester)

**职责**：
- 使用pytest-qt完成UI自动化测试
- 覆盖主窗口、登录、设置等关键界面
- 设计界面交互测试用例
- 处理Qt测试的特殊情况（对话框、异步操作）

**目标输出**：
- `tests/unit/ui/test_login_interface.py` - 登录界面测试
- `tests/unit/ui/test_settings_interface.py` - 设置界面测试
- `tests/e2e/test_main_workflow.py` - 主工作流E2E测试
- `docs/ui_test_implementation.md` - UI测试实现文档

**UI测试覆盖要求**：
```python
# 登录界面测试
# - 用户名/密码输入框正常显示
# - 输入验证（空值、长度限制）
# - 登录按钮状态（启用/禁用）
# - 登录成功/失败提示
# - 记住密码功能

# 设置界面测试
# - 各设置项正确加载
# - 修改设置后保存
# - 重置为默认值
# - 设置变更实时生效

# 主窗口测试
# - 页面切换正常
# - 状态栏更新
# - 菜单操作
# - 快捷键响应
```

**技术要点**：
- 使用`qtbot`进行UI交互
- Mock QMessageBox避免阻塞
- Mock QFileDialog避免文件选择弹窗
- 处理QThread异步操作

**验收标准**：
- [ ] UI测试可运行（`pytest tests/unit/ui/ -v`）
- [ ] 登录界面测试覆盖主要场景
- [ ] 设置界面测试覆盖主要场景
- [ ] 主工作流E2E测试完成

---

### 角色3：设备测试专家 (Device Testing Specialist)

**职责**：
- 准备真实设备(192.168.1.29)测试环境
- 设计设备初始化向导测试方案
- 编写设备初始化测试用例（标记@real_device）
- 设计初始化异常处理测试

**目标输出**：
- `docs/device_test_plan.md` - 设备测试计划
- `tests/e2e/test_device_initializer.py` - 设备初始化测试
- `tests/config/device_test_env.yaml` - 设备环境配置
- `docs/device_test_checklist.md` - 设备测试检查清单

**设备初始化测试范围**（仅在192.168.1.29执行）：
```python
# 初始化向导完整流程
# - 步骤1：设置root密码
# - 步骤2：创建目录结构
# - 步骤3：上传必要文件
# - 步骤4：配置动态库路径
# - 步骤5：硬盘分区扩容
# - 步骤6：运行安全测试
# - 步骤7：配置系统时间
# - 步骤8：重启确认

# 异常处理测试
# - 网络中断恢复
# - 命令执行失败处理
# - 用户取消操作
```

**重要约束**：
```python
# 这些测试必须标记为@real_device
# 默认情况下（无环境变量）自动跳过

@pytest.mark.real_device
def test_device_init_step1_set_password():
    """步骤1：设置root密码 - 仅在真实设备执行"""
    pass

@pytest.mark.real_device
def test_device_init_full_flow():
    """完整初始化流程 - 仅在真实设备执行"""
    pass
```

**验收标准**：
- [ ] 设备测试计划文档完整
- [ ] 测试用例标记正确（@real_device）
- [ ] 环境配置文档完整
- [ ] 测试检查清单可用于手动验证

---

### 角色4：质量审查员 (Quality Inspector)

**职责**：
- **不直接产出代码**，只负责审查
- 审查Phase 2问题修复情况
- 审查Phase 3测试质量
- 运行最终验收测试
- 出具Phase 3最终报告

**目标输出**：
- `docs/review/phase3/*.md` - Phase 3交叉审查记录
- `docs/phase3_review_report.md` - Phase 3最终审查报告
- `docs/final_test_summary.md` - 全阶段测试总结

**审查清单**：
```markdown
## Phase 3 审查清单

### Phase 2修复验证
- [ ] Phase 2最终报告已补充
- [ ] 源代码修改建议已更新

### UI自动化测试审查
- [ ] UI测试可正常运行
- [ ] 测试覆盖关键界面
- [ ] Mock使用恰当（不弹出真实对话框）
- [ ] 异步操作处理正确

### 设备测试审查
- [ ] 设备测试计划完整
- [ ] 测试正确标记@real_device
- [ ] 环境配置文档清晰

### 整体验收
- [ ] 所有交付物完整
- [ ] 测试可运行
- [ ] 文档齐全
```

**最终报告要求**:
```markdown
# Phase 3 最终审查报告

## 1. 全阶段总结
- Phase 1：基础设施 ✅
- Phase 2：核心模块测试 ✅
- Phase 3：UI自动化与设备测试 ✅

## 2. 测试统计
- 单元测试：171个
- 集成测试：32个
- UI测试：XX个
- 设备测试：XX个（标记@real_device）
- 总覆盖率：XX%

## 3. 验收结论
- 是否通过全部验收标准
- 是否可以进入生产测试阶段

## 4. 遗留事项
- 需手动执行的设备测试
- 未来改进建议
```

**验收标准**：
- [ ] Phase 2修复验证完成
- [ ] Phase 3交叉审查记录完整
- [ ] Phase 3最终报告已产出
- [ ] 全阶段总结文档已产出

---

## 团队协作流程（迭代制）

### 第一轮：Phase 2问题修复（报告完善专家主导）

1. 报告完善专家编制Phase 2最终报告
2. 报告完善专家更新源代码修改建议
3. 质量审查员审查并确认修复完成

### 第二轮：Phase 3开发（各角色并行）

| 角色 | 任务 |
|------|------|
| 报告完善专家 | 整理归档Phase 1-2文档 |
| UI自动化测试专家 | 开发UI测试用例 |
| 设备测试专家 | 准备设备测试环境、编写测试方案 |
| 质量审查员 | 跟踪进度、准备审查 |

### 第三轮：交叉审查（必须执行）

| 被审查角色 | 审查者 |
|-----------|--------|
| 报告完善专家 | UI自动化测试专家 + 质量审查员 |
| UI自动化测试专家 | 设备测试专家 + 报告完善专家 |
| 设备测试专家 | UI自动化测试专家 + 质量审查员 |
| 质量审查员 | 报告完善专家（最终审查） |

**审查方式**：
- 在 `docs/review/phase3/` 目录下创建审查意见文件
- 命名格式：`{审查者}_review_{被审查者}_phase3.md`
- 必须包含：问题清单、改进建议、是否通过

### 第四轮：返工与最终验收（如需要）

- 不通过的产出需返工
- 质量审查员运行最终验收
- 出具Phase 3最终报告和全阶段总结

---

## 约束条件（红线，绝对不可违反）

### 1. 不修改原有代码

```
❌ 禁止修改 src/ 下任何文件
❌ 禁止修改 requirements.txt（除非新增测试依赖注释段）
❌ 禁止修改 run.bat
✅ 只允许在 tests/ 目录下新建文件
✅ 只允许修改 tests/ 目录下的文件
✅ 只允许修改 docs/ 目录下的文档
```

### 2. 设备测试安全

```
❌ 绝对禁止在Ubuntu虚拟机(192.168.56.132)执行设备初始化测试
✅ 设备初始化向导测试必须标记@real_device
✅ 必须设置REAL_DEVICE_TEST=1才执行
✅ 默认情况下（无环境变量）自动跳过
```

### 3. 文档完整性

```
✅ Phase 2最终报告必须补充
✅ 源代码修改建议必须更新（不能是空模板）
✅ Phase 3审查记录必须创建
✅ Phase 3最终报告必须产出
```

---

## 交付物清单

### Phase 2修复交付物

| 文件 | 负责角色 | 说明 |
|------|---------|------|
| `docs/phase2_review_report.md` | 报告完善专家 | Phase 2最终审查报告 |
| `docs/test_code_suggestions.md` (更新) | 报告完善专家 | 源代码修改建议 |
| `docs/archive/phase1_2_summary.md` | 报告完善专家 | Phase 1-2阶段总结 |

### Phase 3代码交付物

| 文件 | 负责角色 | 说明 |
|------|---------|------|
| `tests/unit/ui/test_login_interface.py` | UI自动化测试专家 | 登录界面测试 |
| `tests/unit/ui/test_settings_interface.py` | UI自动化测试专家 | 设置界面测试 |
| `tests/e2e/test_main_workflow.py` | UI自动化测试专家 | 主工作流E2E测试 |
| `tests/e2e/test_device_initializer.py` | 设备测试专家 | 设备初始化测试（@real_device） |
| `tests/config/device_test_env.yaml` | 设备测试专家 | 设备环境配置 |

### Phase 3文档交付物

| 文件 | 负责角色 | 说明 |
|------|---------|------|
| `docs/ui_test_implementation.md` | UI自动化测试专家 | UI测试实现文档 |
| `docs/device_test_plan.md` | 设备测试专家 | 设备测试计划 |
| `docs/device_test_checklist.md` | 设备测试专家 | 设备测试检查清单 |
| `docs/review/phase3/*.md` | 所有角色 | Phase 3交叉审查记录 |
| `docs/phase3_review_report.md` | 质量审查员 | Phase 3最终审查报告 |
| `docs/final_test_summary.md` | 质量审查员 | 全阶段测试总结 |

---

## 阶段性报告要求

### 中期检查点（Day 2-3）

每个角色需输出：`docs/progress/phase3/{角色名}_day2.md`

内容：
- Phase 2修复进展（如适用）
- Phase 3已完成工作
- 遇到的问题
- 需要其他角色配合的事项
- 预计完成时间

### 最终报告要求

**质量审查员必须输出**：

1. **Phase 3审查报告** (`docs/phase3_review_report.md`)
   - Phase 2修复验证
   - Phase 3各角色完成度评估
   - UI自动化测试评估
   - 设备测试准备评估
   - 是否通过验收

2. **全阶段测试总结** (`docs/final_test_summary.md`)
   - Phase 1-2-3总体回顾
   - 测试统计数据
   - 覆盖率汇总
   - 遗留工作（如设备测试需在真实环境执行）
   - 未来改进建议

---

## 验收标准（必须全部满足）

质量审查员负责验证：

### Phase 2修复验证
- [ ] **Phase 2最终报告已补充** (`docs/phase2_review_report.md`存在且完整)
- [ ] **源代码修改建议已更新** (不再是空模板)

### Phase 3成果验证
- [ ] **没有修改src/** 目录下任何原有代码
- [ ] **UI测试可运行** (`pytest tests/unit/ui/ -v` 正常执行)
- [ ] **E2E测试框架完成** (主工作流测试存在)
- [ ] **设备测试准备完成** (测试计划、检查清单、@real_device标记)
- [ ] **文档完整** (所有文档交付物已产出)
- [ ] **交叉审查完成** (docs/review/phase3/ 下有记录)

### 最终交付验证
- [ ] **Phase 3最终报告已产出**
- [ ] **全阶段测试总结已产出**

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

### UI测试运行命令

```bash
# 激活环境
conda activate pyqt5_env

# 运行UI测试
pytest tests/unit/ui/ -v

# 运行E2E测试（本地部分）
pytest tests/e2e/ -v -m "not real_device"

# 运行设备测试（需要真实设备）
set REAL_DEVICE_TEST=1
set DEVICE_PASSWORD=your_root_password
pytest tests/e2e/test_device_initializer.py -v

# 生成覆盖率报告（含UI测试）
pytest tests/unit/ui/ --cov=src.ui --cov-report=html
```

### UI测试示例

```python
# tests/unit/ui/test_login_interface.py
import pytest
from PyQt5.QtWidgets import QLineEdit, QPushButton
from PyQt5.QtCore import Qt

class TestLoginInterface:
    def test_username_input_exists(self, qtbot, qt_app):
        from ui.interfaces.login_interface import LoginWindow
        window = LoginWindow()
        qtbot.addWidget(window)

        # 检查用户名输入框存在
        assert window.username_input is not None
        assert isinstance(window.username_input, QLineEdit)

    def test_login_button_disabled_when_empty(self, qtbot, qt_app):
        from ui.interfaces.login_interface import LoginWindow
        window = LoginWindow()
        qtbot.addWidget(window)

        # 清空输入，按钮应禁用
        window.username_input.clear()
        window.password_input.clear()
        assert not window.login_button.isEnabled()
```

### 被测源码位置

- `src/ui/main_window.py` - 主窗口
- `src/ui/interfaces/login_interface.py` - 登录界面
- `src/ui/interfaces/settings_interface.py` - 设置界面
- `src/ui/interfaces/initializer_interface.py` - 设备初始化向导
- `src/ui/interfaces/protocol_editor_interface.py` - 协议编辑器
- `src/ui/interfaces/autopilot_editor_interface.py` - 算法编辑器

---

## 启动指令

**团队负责人（Team Lead）启动任务**：

1. 检查Phase 2文件完整性
2. 确认遗留问题清单
3. 分配角色给各agent
4. 建立`docs/review/phase3/`目录
5. 建立`docs/progress/phase3/`目录
6. 先执行Phase 2修复，再执行Phase 3开发
7. 组织交叉审查
8. 最终验收并输出报告

**各角色Agent启动后先阅读**：
- 本文档（明确职责和约束）
- `docs/agent_team_test_plan.md`（整体规划）
- `docs/agent_task_phase2_prompt.md`（Phase 2要求）
- `docs/phase1_fix_report.md`（Phase 1修复报告）
- `docs/core_module_test_report.md`（核心模块测试报告）
- `docs/integration_test_report.md`（集成测试报告）
- `src/ui/`下相关源码（了解被测UI代码）

---

## 关键成功因素

1. **先修复，后开发** - 确保Phase 2闭环是最高优先级
2. **文档完整** - Phase 2最终报告和修改建议必须完成
3. **UI测试稳定** - Qt测试容易因时序问题不稳定，需充分验证
4. **设备测试安全** - 确保@real_device标记正确，不会误执行
5. **全阶段总结** - Phase 3是全流程最后阶段，需完整总结
