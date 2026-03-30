# Protocol Reserved Field Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `RESERVED` protocol field type that occupies raw frame bytes, optionally occupies parsed frame layout, and never participates in unpacked values or schema generation.

**Architecture:** Extend the shared protocol schema model first, because field type registration, layout computation, CSV behavior, and C++ code generation are centralized in one module. Then update the protocol editor UI so the new type can be created and exported consistently with the new semantics.

**Tech Stack:** Python 3, PyQt5, qfluentwidgets, pytest

---

### Task 1: Add failing protocol schema tests

**Files:**
- Modify: `tests/unit/core/test_protocol_schema.py`
- Modify: `src/core/protocol_schema.py`

- [ ] **Step 1: Write the failing test**

```python
def test_validate_reserved_length_positive_only():
    fields = [FieldSpec(1, 0, "RESERVED", "", "reserved", None, None, True)]
    warnings = validate_fields(fields)
    assert len(warnings) == 1


def test_generate_cpp_reserved_field_skips_schema_and_unpack():
    fields = [
        FieldSpec(1, 4, "U32", "头", "header", None, None, True),
        FieldSpec(2, 3, "RESERVED", "预留", "reserved_block", None, None, True),
        FieldSpec(3, 2, "U16", "尾", "tail", None, None, True),
    ]
    code = generate_cpp_code("ReservedFrame", fields)
    assert "std::array<uint8_t, 3> reserved_block{};" in code
    assert 'schema.addFieldAt("预留"' not in code
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/core/test_protocol_schema.py -k reserved -v`
Expected: FAIL because `RESERVED` is not a known type and generated code does not yet treat it specially.

- [ ] **Step 3: Write minimal implementation**

```python
TYPE_OPTIONS.append("RESERVED")
TYPE_SPECS["RESERVED"] = {"bytes": None, "cpp_type": None, "log_type": None}
```

- [ ] **Step 4: Run test to verify it still fails for missing behavior**

Run: `pytest tests/unit/core/test_protocol_schema.py -k reserved -v`
Expected: FAIL on layout / generation assertions until remaining logic is implemented.

- [ ] **Step 5: Commit**

```bash
git add tests/unit/core/test_protocol_schema.py src/core/protocol_schema.py
git commit -m "test: add reserved protocol field coverage"
```

### Task 2: Implement RESERVED core behavior

**Files:**
- Modify: `src/core/protocol_schema.py`
- Test: `tests/unit/core/test_protocol_schema.py`

- [ ] **Step 1: Implement validation and layout rules**

```python
if field.field_type == "RESERVED":
    if field.length <= 0:
        warnings.append(f"RESERVED 长度必须大于0 (序号 {field.index})")
    continue
```

- [ ] **Step 2: Implement parsed frame sizing and struct generation**

```python
if spec.field_type == "RESERVED":
    if not spec.is_valid:
        continue
    meta.frame_offset = frame_offset
    frame_offset += _field_byte_length(spec)
```

- [ ] **Step 3: Implement pack / unpack / schema special handling**

```python
if spec.field_type == "RESERVED":
    continue
```

- [ ] **Step 4: Run focused tests**

Run: `pytest tests/unit/core/test_protocol_schema.py -k reserved -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/unit/core/test_protocol_schema.py src/core/protocol_schema.py
git commit -m "feat: add reserved protocol field core behavior"
```

### Task 3: Update protocol editor UI

**Files:**
- Modify: `src/ui/interfaces/protocol_editor_interface.py`
- Modify: `src/core/protocol_schema.py`

- [ ] **Step 1: Register the new type in the editor**

```python
("预留字节", "RESERVED")
```

- [ ] **Step 2: Apply RESERVED defaults and field state handling**

```python
if field_type == "RESERVED":
    length_item.setText("1")
```

- [ ] **Step 3: Disable meaningless columns and adjust styling**

```python
if field_type == "RESERVED":
    lsb_item.setText("")
    default_item.setText("")
```

- [ ] **Step 4: Keep export output readable**

```python
type_text = type_map.get(field.field_type, field.field_type)
```

- [ ] **Step 5: Commit**

```bash
git add src/ui/interfaces/protocol_editor_interface.py src/core/protocol_schema.py
git commit -m "feat: expose reserved protocol field in editor"
```

### Task 4: Verify feature behavior

**Files:**
- Modify: `tests/unit/core/test_protocol_schema.py`

- [ ] **Step 1: Run targeted protocol schema tests**

Run: `pytest tests/unit/core/test_protocol_schema.py -v`
Expected: PASS

- [ ] **Step 2: Run UI-adjacent regression coverage only if needed**

Run: `pytest tests/unit/core/test_protocol_schema.py -k "csv or generate_cpp" -v`
Expected: PASS

- [ ] **Step 3: Review resulting diff**

Run: `git diff -- src/core/protocol_schema.py src/ui/interfaces/protocol_editor_interface.py tests/unit/core/test_protocol_schema.py docs/superpowers/specs/2026-03-30-protocol-reserved-field-design.md docs/superpowers/plans/2026-03-30-protocol-reserved-field.md`
Expected: Diff contains only reserved-field feature and docs changes.
