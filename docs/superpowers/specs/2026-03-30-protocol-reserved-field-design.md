# 协议建模工作台 RESERVED 字段设计

**日期：** 2026-03-30

**背景**

协议建模工作台当前缺少“连续预留字段”的一等建模能力。用户需要在协议中表达一段连续保留字节，并允许该字段在原始帧布局中占位，但不参与 `unpack` 解析结果和日志 `schema` 输出。

**目标**

- 新增 `RESERVED` 字段类型，长度支持任意正整数字节数。
- `RESERVED` 始终参与原始协议帧字节布局计算。
- `RESERVED` 在 `有效=勾选` 时进入解析帧 `frame` 结构体并占据 `FRAME_SIZE`。
- `RESERVED` 在 `有效=未勾选` 时不进入解析帧 `frame` 结构体。
- `RESERVED` 永远不参与 `unpack` 赋值，不参与 `schema` 构建。
- `packFrame()` 对 `RESERVED` 对应字节保持 `0`。

**字段语义**

- 类型：`RESERVED`
- 长度：任意正整数字节数
- `LSB`：无意义，忽略
- `默认值`：无意义，忽略
- `有效`：
  - 勾选：进入 `frame` 结构体，占解析帧位置，但不参与 `unpack` 和 `schema`
  - 未勾选：仅占原始协议帧位置，不进入 `frame` 结构体

**代码生成规则**

- 有效 `RESERVED` 生成成员：`std::array<uint8_t, N> <field_name>{};`
- `packFrame()` 不对该成员写入 `buffer`
- `unpackFrame()` 跳过该字段对应字节
- `buildSchema()` 忽略该字段

**UI 规则**

- 类型下拉新增“预留字节”
- 默认长度为 `1`
- `有效` 复选框保持可编辑
- `LSB`、`默认值` 对 `RESERVED` 不生效；编辑器在交互上清空并禁用
- `RESERVED` 行采用独立浅色高亮

**影响范围**

- `src/core/protocol_schema.py`
- `src/ui/interfaces/protocol_editor_interface.py`
- `tests/unit/core/test_protocol_schema.py`

**验证策略**

- 先补单测覆盖 `RESERVED` 校验、CSV 读写、字节布局、解析帧布局、C++ 生成行为
- 再实现核心逻辑与 UI 适配
- 最后运行目标单测进行回归验证
