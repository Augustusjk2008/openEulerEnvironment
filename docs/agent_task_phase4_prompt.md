# Agent Team 任务：Phase 4 核心业务模块测试补充

## 任务概述

本任务需要建立一支Agent测试专家团队，**完成剩余核心业务模块的单元测试**，重点补充协议模式、代码生成、文档生成等核心功能的测试覆盖。

**当前测试状态**：
| 分类 | 代码行数 | 覆盖率 | 状态 |
|------|---------|--------|------|
| 已测试核心模块 | 429行 | ~95% | ✅ 完成 |
| 未测试核心模块 | 2,261行 | 0% | ❌ 待补充 |
| UI界面模块 | 7,057行 | 0% | ⏸️ 可选 |

**Phase 4目标**：将核心模块覆盖率从4.4%提升到**30%+**

---

## 未测试模块分析（按优先级排序）

### 🔴 P0 - 最高优先级（必须完成）

| 模块 | 文件路径 | 行数 | 功能说明 | 预估测试数 |
|------|----------|------|----------|-----------|
| **protocol_schema** | src/core/protocol_schema.py | 1,051 | 协议字段定义、模式解析、验证 | 80+ |
| **autopilot_codegen_cpp** | src/core/autopilot_codegen_cpp.py | 516 | C++代码生成、模板渲染 | 40+ |
| **autopilot_document** | src/core/autopilot_document.py | 636 | Word文档生成、图表插入 | 50+ |
| **initializer_interface** | src/ui/interfaces/initializer_interface.py | 140 | 设备初始化向导逻辑 | 20+ |

### 🟡 P1 - 高优先级（建议完成）

| 模块 | 文件路径 | 行数 | 功能说明 | 预估测试数 |
|------|----------|------|----------|-----------|
| **ftp_interface** | src/ui/interfaces/ftp_interface.py | 677 | FTP文件传输界面逻辑 | 30+ |
| **terminal_interface** | src/ui/interfaces/terminal_interface.py | 691 | SSH终端界面逻辑 | 30+ |
| **protocol_editor_interface** | src/ui/interfaces/protocol_editor_interface.py | 673 | 协议编辑器界面 | 30+ |

---

## 团队角色配置（5人专家组）

### 角色1：协议测试专家 (Protocol Testing Specialist)

**职责**：
- 负责protocol_schema模块的全面测试
- 测试协议字段类型、模式定义、验证逻辑
- 测试协议导入导出功能

**被测文件**：`src/core/protocol_schema.py` (1,051行)

**目标输出**：
- `tests/unit/core/test_protocol_schema.py` (80+测试)
- `docs/protocol_test_guide.md` - 协议测试说明

**测试要点**：
```python
# ProtocolSchema核心测试点：

# 1. 字段类型定义
# - LogFieldType枚举
# - 基础类型（Int8, Int16, Int32, Float32等）
# - 数组类型
# - 嵌套类型

# 2. 协议字段定义
# - 字段创建
# - 字段属性（name, type, count, scale等）
# - 字段验证

# 3. 协议模式定义
# - 协议创建
# - 添加字段
# - 字段顺序
# - 协议验证

# 4. 协议解析
# - 从JSON/XML解析
# - 从二进制解析
# - 错误处理

# 5. 协议导出
# - 导出为JSON
# - 导出为XML
# - 导出为Word文档

# 6. 协议验证
# - 字段类型验证
# - 必填字段验证
# - 循环依赖检测
```

---

### 角色2：代码生成测试专家 (Code Generation Testing Specialist)

**职责**：
- 负责autopilot_codegen_cpp模块的测试
- 测试C++代码生成逻辑
- 测试模板渲染、变量替换

**被测文件**：`src/core/autopilot_codegen_cpp.py` (516行)

**目标输出**：
- `tests/unit/core/test_autopilot_codegen.py` (40+测试)
- `tests/fixtures/codegen_templates/` - 测试用模板
- `docs/codegen_test_guide.md` - 代码生成测试说明

**测试要点**：
```python
# AutopilotCodegenCpp核心测试点：

# 1. 模板管理
# - 加载模板
# - 模板缓存
# - 模板不存在处理

# 2. 变量替换
# - 简单变量替换
# - 嵌套变量替换
# - 条件渲染（if/else）
# - 循环渲染（for）
# - 特殊字符转义

# 3. 代码生成
# - 头文件生成
# - 源文件生成
# - 多文件生成
# - 文件命名规则

# 4. 代码格式化
# - 缩进处理
# - 空行处理
# - 注释保留

# 5. 错误处理
# - 模板语法错误
# - 变量缺失
# - 循环嵌套过深
```

---

### 角色3：文档生成测试专家 (Document Generation Testing Specialist)

**职责**：
- 负责autopilot_document模块的测试
- 测试Word文档生成
- 测试图表插入、表格生成

**被测文件**：`src/core/autopilot_document.py` (636行)

**目标输出**：
- `tests/unit/core/test_autopilot_document.py` (50+测试)
- `tests/fixtures/document_templates/` - 测试用模板
- `docs/document_test_guide.md` - 文档测试说明

**测试要点**：
```python
# AutopilotDocument核心测试点：

# 1. 文档创建
# - 创建新文档
# - 加载模板
# - 页面设置

# 2. 段落操作
# - 添加标题
# - 添加正文
# - 添加列表
# - 样式设置

# 3. 表格操作
# - 创建表格
# - 添加行/列
# - 合并单元格
# - 表格样式

# 4. 图表操作
# - 插入图片
# - 插入图表
# - 图表数据绑定

# 5. 文档导出
# - 保存为docx
# - 导出为PDF
# - 文件覆盖处理

# 6. 复杂文档
# - 目录生成
# - 页眉页脚
# - 水印
```

---

### 角色4：设备初始化测试专家 (Device Initializer Testing Specialist)

**职责**：
- 负责initializer_interface模块的测试
- 测试设备初始化向导逻辑
- Mock SSH操作，验证命令组装

**被测文件**：`src/ui/interfaces/initializer_interface.py` (140行)

**目标输出**：
- `tests/unit/ui/test_initializer_interface.py` (20+测试)
- `tests/e2e/test_device_init_logic.py` - 初始化流程逻辑测试
- `docs/initializer_test_guide.md` - 初始化测试说明

**测试要点**：
```python
# InitializerInterface核心测试点：

# 1. 初始化步骤管理
# - 步骤定义
# - 步骤顺序
# - 步骤跳过逻辑
# - 步骤依赖

# 2. 命令组装（Mock SSH）
# - 设置root密码命令
# - 创建目录命令
# - 上传文件命令
# - 配置动态库路径命令
# - 扩容分区命令
# - 运行安全测试命令
# - 配置时间命令
# - 重启命令

# 3. 状态管理
# - 当前步骤状态
# - 总体进度
# - 成功/失败标记
# - 日志记录

# 4. 错误处理
# - 命令执行失败
# - 网络中断
# - 用户取消
# - 超时处理

# 5. 回滚逻辑
# - 部分失败回滚
# - 数据恢复
```

**安全约束**：
```python
# 所有测试必须使用Mock SSH，禁止真实连接
# 验证命令组装正确，但不执行

@pytest.fixture
def mock_ssh():
    """Mock SSH连接，记录命令但不执行"""
    ssh = MagicMock()
    ssh.exec_command = MagicMock(return_value=(None, MagicMock(), None))
    return ssh

def test_init_step_command(mock_ssh):
    # 验证命令组装正确
    expected_cmd = "echo 'root:newpass' | chpasswd"
    # 不实际执行
```

---

### 角色5：质量审查员 (Quality Inspector)

**职责**：
- **不直接产出代码**，只负责审查
- 审查各模块测试质量
- 运行覆盖率分析
- 出具Phase 4最终报告

**目标输出**：
- `docs/review/phase4/*.md` - Phase 4交叉审查记录
- `docs/phase4_review_report.md` - Phase 4最终审查报告
- `tests/reports/coverage_phase4.md` - Phase 4覆盖率报告
- `docs/test_code_suggestions_v2.md` - 更新的源代码修改建议

**审查清单**：
```markdown
## Phase 4 审查清单

### protocol_schema测试审查
- [ ] 字段类型全部覆盖
- [ ] 协议验证逻辑测试
- [ ] 导入导出功能测试
- [ ] 边界条件测试

### autopilot_codegen测试审查
- [ ] 模板渲染测试
- [ ] 变量替换测试
- [ ] 代码生成测试
- [ ] 错误处理测试

### autopilot_document测试审查
- [ ] 文档创建测试
- [ ] 段落操作测试
- [ ] 表格/图表测试
- [ ] 导出功能测试

### initializer_interface测试审查
- [ ] 步骤管理测试
- [ ] 命令组装测试（Mock）
- [ ] 状态管理测试
- [ ] 错误处理测试

### 覆盖率审查
- [ ] protocol_schema ≥ 70%
- [ ] autopilot_codegen ≥ 70%
- [ ] autopilot_document ≥ 70%
- [ ] initializer_interface ≥ 60%
```

---

## 详细测试设计指南

### ProtocolSchema测试设计

```python
# tests/unit/core/test_protocol_schema.py

class TestProtocolFieldType:
    """测试协议字段类型"""

    def test_field_type_values(self):
        """测试所有字段类型值正确"""
        assert LogFieldType.INT8.value == 0
        assert LogFieldType.INT16.value == 1
        # ... 所有类型

    def test_field_type_from_string(self):
        """测试从字符串解析字段类型"""
        assert LogFieldType.from_string("int8") == LogFieldType.INT8
        assert LogFieldType.from_string("float32") == LogFieldType.FLOAT32

class TestLogField:
    """测试日志字段"""

    def test_field_creation(self):
        """测试创建字段"""
        field = LogField(name="test", field_type=LogFieldType.INT32)
        assert field.name == "test"
        assert field.field_type == LogFieldType.INT32

    def test_field_with_scale(self):
        """测试带缩放的字段"""
        field = LogField(name="temp", field_type=LogFieldType.FLOAT32, scale=0.1)
        assert field.scale == 0.1

class TestProtocolSchema:
    """测试协议模式"""

    def test_add_field(self):
        """测试添加字段"""
        schema = ProtocolSchema()
        schema.add_field(LogField(name="id", field_type=LogFieldType.INT32))
        assert len(schema.fields) == 1

    def test_validate_duplicate_name(self):
        """测试重复字段名验证"""
        schema = ProtocolSchema()
        schema.add_field(LogField(name="id", field_type=LogFieldType.INT32))
        with pytest.raises(ValueError):
            schema.add_field(LogField(name="id", field_type=LogFieldType.INT16))

    def test_to_json(self):
        """测试导出为JSON"""
        schema = ProtocolSchema()
        schema.add_field(LogField(name="id", field_type=LogFieldType.INT32))
        json_str = schema.to_json()
        assert "id" in json_str

    def test_from_json(self):
        """测试从JSON导入"""
        json_data = '{"name": "test", "fields": [...]}'
        schema = ProtocolSchema.from_json(json_data)
        assert schema.name == "test"
```

### AutopilotCodegenCpp测试设计

```python
# tests/unit/core/test_autopilot_codegen.py

class TestTemplateRendering:
    """测试模板渲染"""

    def test_simple_variable_replacement(self):
        """测试简单变量替换"""
        template = "Hello {{name}}!"
        result = render_template(template, {"name": "World"})
        assert result == "Hello World!"

    def test_conditional_rendering(self):
        """测试条件渲染"""
        template = "{% if debug %}DEBUG{% else %}RELEASE{% endif %}"
        result = render_template(template, {"debug": True})
        assert result == "DEBUG"

    def test_loop_rendering(self):
        """测试循环渲染"""
        template = "{% for item in items %}{{item}}{% endfor %}"
        result = render_template(template, {"items": ["a", "b", "c"]})
        assert result == "abc"

class TestCodeGeneration:
    """测试代码生成"""

    def test_generate_header_file(self):
        """测试生成头文件"""
        config = {"class_name": "Controller", "methods": [...]}
        code = generate_header(config)
        assert "class Controller" in code
        assert "#ifndef" in code

    def test_generate_source_file(self):
        """测试生成源文件"""
        config = {"class_name": "Controller", "implementations": [...]}
        code = generate_source(config)
        assert "#include" in code
        assert "Controller::" in code
```

### AutopilotDocument测试设计

```python
# tests/unit/core/test_autopilot_document.py

class TestDocumentCreation:
    """测试文档创建"""

    def test_create_blank_document(self):
        """测试创建空白文档"""
        doc = Document()
        assert doc is not None

    def test_add_heading(self):
        """测试添加标题"""
        doc = Document()
        doc.add_heading("Test", level=1)
        assert len(doc.paragraphs) == 1

class TestTableOperations:
    """测试表格操作"""

    def test_create_table(self):
        """测试创建表格"""
        doc = Document()
        table = doc.add_table(rows=3, cols=3)
        assert len(table.rows) == 3
        assert len(table.columns) == 3

    def test_add_table_data(self):
        """测试添加表格数据"""
        doc = Document()
        table = doc.add_table(rows=2, cols=2)
        table.cell(0, 0).text = "Header1"
        table.cell(0, 1).text = "Header2"
        assert table.cell(0, 0).text == "Header1"

class TestDocumentExport:
    """测试文档导出"""

    def test_save_to_docx(self, tmp_path):
        """测试保存为docx"""
        doc = Document()
        doc.add_heading("Test", level=1)
        file_path = tmp_path / "test.docx"
        doc.save(str(file_path))
        assert file_path.exists()
```

### InitializerInterface测试设计

```python
# tests/unit/ui/test_initializer_interface.py

class TestInitSteps:
    """测试初始化步骤"""

    def test_step_definitions(self):
        """测试步骤定义"""
        steps = get_init_steps()
        assert len(steps) == 8
        assert steps[0]["name"] == "设置root密码"

    def test_step_order(self):
        """测试步骤顺序"""
        steps = get_init_steps()
        assert steps[0]["order"] < steps[1]["order"]

class TestCommandAssembly:
    """测试命令组装（Mock SSH）"""

    def test_set_password_command(self):
        """测试设置密码命令"""
        password = "newpass"
        cmd = build_set_password_cmd(password)
        assert "chpasswd" in cmd
        assert password in cmd

    def test_create_directory_command(self):
        """测试创建目录命令"""
        dirs = ["/opt/app", "/opt/data"]
        cmds = build_create_dir_cmds(dirs)
        assert len(cmds) == len(dirs)
        assert "mkdir -p" in cmds[0]

    def test_expand_partition_command(self):
        """测试扩容分区命令"""
        cmd = build_expand_partition_cmd("/dev/mmcblk0", "3")
        assert "resize2fs" in cmd or "parted" in cmd

class TestStateManagement:
    """测试状态管理"""

    def test_progress_calculation(self):
        """测试进度计算"""
        current = 4
        total = 8
        progress = calculate_progress(current, total)
        assert progress == 50

    def test_step_status_tracking(self):
        """测试步骤状态跟踪"""
        tracker = StepTracker()
        tracker.start_step(0)
        tracker.complete_step(0)
        assert tracker.get_step_status(0) == "completed"
```

---

## 团队协作流程（迭代制）

### 第一轮：独立开发（每个角色）

各专家根据职责独立完成测试代码编写。

### 第二轮：交叉审查（必须执行）

| 被审查角色 | 审查者 |
|-----------|--------|
| 协议测试专家 | 代码生成测试专家 + 质量审查员 |
| 代码生成测试专家 | 文档生成测试专家 + 协议测试专家 |
| 文档生成测试专家 | 设备初始化测试专家 + 质量审查员 |
| 设备初始化测试专家 | 协议测试专家 + 质量审查员 |
| 质量审查员 | 协议测试专家（最终审查） |

### 第三轮：返工修改（如需要）

被审查不通过的角色必须返工，直到审查者满意。

### 第四轮：质量审查员最终验收

- 运行覆盖率分析
- 出具Phase 4审查报告
- 更新全阶段总结

---

## 约束条件（红线，绝对不可违反）

### 1. 不修改原有代码

```
❌ 禁止修改 src/ 下任何文件
❌ 禁止修改 requirements.txt
❌ 禁止修改 run.bat
✅ 只允许在 tests/ 目录下新建文件
```

### 2. 测试安全

```
❌ initializer_interface测试禁止真实SSH连接
✅ 必须使用Mock验证命令组装
```

### 3. 覆盖率目标

```
protocol_schema: ≥ 70%
autopilot_codegen: ≥ 70%
autopilot_document: ≥ 70%
initializer_interface: ≥ 60%
```

---

## 交付物清单

### 代码交付物

| 文件 | 负责角色 | 说明 |
|------|---------|------|
| `tests/unit/core/test_protocol_schema.py` | 协议测试专家 | 协议模式测试 |
| `tests/unit/core/test_autopilot_codegen.py` | 代码生成测试专家 | 代码生成测试 |
| `tests/unit/core/test_autopilot_document.py` | 文档生成测试专家 | 文档生成测试 |
| `tests/unit/ui/test_initializer_interface.py` | 设备初始化测试专家 | 初始化界面测试 |
| `tests/e2e/test_device_init_logic.py` | 设备初始化测试专家 | 初始化流程逻辑测试 |
| `tests/fixtures/codegen_templates/` | 代码生成测试专家 | 测试模板 |
| `tests/fixtures/document_templates/` | 文档生成测试专家 | 测试模板 |

### 文档交付物

| 文件 | 负责角色 | 说明 |
|------|---------|------|
| `docs/protocol_test_guide.md` | 协议测试专家 | 协议测试指南 |
| `docs/codegen_test_guide.md` | 代码生成测试专家 | 代码生成测试指南 |
| `docs/document_test_guide.md` | 文档生成测试专家 | 文档测试指南 |
| `docs/initializer_test_guide.md` | 设备初始化测试专家 | 初始化测试指南 |
| `docs/review/phase4/*.md` | 所有角色 | 交叉审查记录 |
| `docs/phase4_review_report.md` | 质量审查员 | Phase 4审查报告 |
| `tests/reports/coverage_phase4.md` | 质量审查员 | Phase 4覆盖率报告 |
| `docs/test_code_suggestions_v2.md` | 质量审查员 | 源代码修改建议更新 |

---

## 验收标准（必须全部满足）

质量审查员负责验证：

### 覆盖率目标
- [ ] **protocol_schema ≥ 70%**
- [ ] **autopilot_codegen ≥ 70%**
- [ ] **autopilot_document ≥ 70%**
- [ ] **initializer_interface ≥ 60%**
- [ ] **整体核心模块覆盖率 ≥ 30%**（从4.4%提升）

### 测试质量
- [ ] 所有测试用例通过
- [ ] 边界条件覆盖
- [ ] 错误处理覆盖
- [ ] Mock使用恰当

### 文档完整性
- [ ] 所有文档交付物已产出
- [ ] 交叉审查记录完整
- [ ] Phase 4审查报告已产出

---

## 启动指令

**团队负责人（Team Lead）启动任务**：

1. 检查Phase 1-3完成情况
2. 分配角色给各agent
3. 建立`docs/review/phase4/`目录
4. 设定截止时间
5. 组织交叉审查
6. 最终验收并输出报告

**各角色Agent启动后先阅读**：
- 本文档（明确职责和约束）
- `docs/agent_team_test_plan.md`（整体规划）
- 被测源码文件（了解代码结构）

---

## 技术参考

### 被测源码快速浏览

```bash
# 查看protocol_schema结构
head -100 src/core/protocol_schema.py

# 查看autopilot_codegen_cpp结构
head -100 src/core/autopilot_codegen_cpp.py

# 查看autopilot_document结构
head -100 src/core/autopilot_document.py

# 查看initializer_interface结构
head -100 src/ui/interfaces/initializer_interface.py
```

### 覆盖率运行命令

```bash
# 运行新增测试并生成覆盖率报告
pytest tests/unit/core/test_protocol_schema.py tests/unit/core/test_autopilot_codegen.py tests/unit/core/test_autopilot_document.py --cov=src --cov-report=html --cov-report=term

# 查看完整覆盖率报告
start tests/reports/coverage_html/index.html
```

### 预期成果

Phase 4完成后，测试框架将覆盖：
- ✅ 基础核心模块（config, auth, ssh, slog）- 已测试
- ✅ 业务核心模块（protocol, codegen, document）- 新增
- ✅ 设备初始化逻辑 - 新增
- ⏸️ UI界面（可选，Phase 5）

**测试用例总数预计**：171（现有）+ 190（新增）= **361个测试**
