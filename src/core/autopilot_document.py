import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
from uuid import uuid4


@dataclass
class ValidationIssue:
    level: str
    message: str
    path: str


_ALLOWED_EXPR_RE = re.compile(r"^[A-Za-z0-9_\s\.\[\]\(\)\+\-\*/%<>=!&\|,']*$")
_IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_\.]*")
_SEQ_REF_RE = re.compile(r"^(?P<base>[A-Za-z_][A-Za-z0-9_]*)\[(?P<index>\d+)\]$")
_LHS_NS_REF_RE = re.compile(r"^(?:(?:in|out)\.)?(?P<name>[A-Za-z_][A-Za-z0-9_]*)(?:\[(?P<index>\d+)\])?$")
_STRING_LITERAL_RE = re.compile(r"^\s*(['\"])(?P<value>.*)\1\s*$")


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def dump_json_text(doc: Dict[str, Any]) -> str:
    return json.dumps(canonicalize_document(doc), ensure_ascii=False, indent=2)


def canonicalize_document(doc: Any) -> Any:
    if isinstance(doc, list):
        return [canonicalize_document(x) for x in doc]
    if not isinstance(doc, dict):
        return doc

    def sort_dict(d: Dict[str, Any]) -> Dict[str, Any]:
        return {k: canonicalize_document(d[k]) for k in sorted(d.keys())}

    schema_version = doc.get("schema_version")
    if isinstance(schema_version, str) and schema_version.startswith("autopilot.controller."):
        normalized = normalize_controller_document(doc)
        ordered: Dict[str, Any] = {}
        for key in ["schema_version", "name", "dt", "state", "data", "program", "ui"]:
            if key in normalized:
                ordered[key] = canonicalize_document(normalized[key])
        for k in normalized.keys():
            if k not in ordered:
                ordered[k] = canonicalize_document(normalized[k])
        return ordered

    if "inputs" in doc or "outputs" in doc:
        ordered: Dict[str, Any] = {}
        if "inputs" in doc:
            ordered["inputs"] = canonicalize_document(doc.get("inputs"))
        if "outputs" in doc:
            ordered["outputs"] = canonicalize_document(doc.get("outputs"))
        for k in doc.keys():
            if k not in ordered:
                ordered[k] = canonicalize_document(doc[k])
        return ordered

    if "id" in doc and "type" in doc:
        ordered: Dict[str, Any] = {}
        for k in ["id", "type", "desc", "unit"]:
            if k in doc:
                ordered[k] = canonicalize_document(doc[k])
        for k in doc.keys():
            if k not in ordered:
                ordered[k] = canonicalize_document(doc[k])
        return ordered

    if "scalars" in doc or "sequences" in doc:
        ordered: Dict[str, Any] = {}
        for k in ["states", "STATE", "scalars", "sequences"]:
            if k in doc:
                v = doc.get(k)
                if k in {"scalars", "sequences"} and isinstance(v, dict):
                    ordered[k] = sort_dict(v)
                else:
                    ordered[k] = canonicalize_document(v)
        for k in doc.keys():
            if k not in ordered:
                ordered[k] = canonicalize_document(doc[k])
        return ordered

    if "shift_sequences" in doc:
        ordered: Dict[str, Any] = {}
        if "shift_sequences" in doc:
            v = doc.get("shift_sequences")
            if isinstance(v, list):
                ordered["shift_sequences"] = sorted([x for x in v if isinstance(x, str)])
            else:
                ordered["shift_sequences"] = canonicalize_document(v)
        for k in doc.keys():
            if k not in ordered:
                ordered[k] = canonicalize_document(doc[k])
        return ordered

    if "op" in doc:
        ordered: Dict[str, Any] = {}
        for k in ["op", "_id", "comment", "name", "lhs", "rhs", "cond", "min", "max", "cases", "else", "true", "false", "then"]:
            if k in doc and k not in ordered:
                ordered[k] = canonicalize_document(doc[k])
        for k in doc.keys():
            if k not in ordered:
                ordered[k] = canonicalize_document(doc[k])
        return ordered

    return {k: canonicalize_document(doc[k]) for k in doc.keys()}


def save_json(path: str, doc: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(dump_json_text(doc) + "\n")


def ensure_program_ids(doc: Dict[str, Any]) -> bool:
    program = doc.get("program")
    if not isinstance(program, list):
        return False

    changed = False

    def walk(nodes: List[Dict[str, Any]]) -> None:
        nonlocal changed
        for node in nodes:
            if not isinstance(node, dict):
                continue
            if "_id" not in node or not isinstance(node.get("_id"), str) or not node.get("_id"):
                node["_id"] = str(uuid4())
                changed = True
            op = node.get("op")
            if op == "if":
                then_nodes = node.get("then", [])
                else_nodes = node.get("else", [])
                if isinstance(then_nodes, list):
                    walk(then_nodes)
                if isinstance(else_nodes, list):
                    walk(else_nodes)

    walk(program)
    return changed


def iter_program_nodes(doc: Dict[str, Any]) -> Iterable[Tuple[Dict[str, Any], str]]:
    program = doc.get("program")
    if not isinstance(program, list):
        return

    def walk(nodes: List[Any], prefix: str) -> Iterable[Tuple[Dict[str, Any], str]]:
        for i, node in enumerate(nodes):
            node_path = f"{prefix}{i}"
            if isinstance(node, dict):
                yield node, node_path
                if node.get("op") == "if":
                    then_nodes = node.get("then", [])
                    else_nodes = node.get("else", [])
                    if isinstance(then_nodes, list):
                        yield from walk(then_nodes, f"{node_path}.then.")
                    if isinstance(else_nodes, list):
                        yield from walk(else_nodes, f"{node_path}.else.")

    yield from walk(program, "")


def find_program_node_by_id(doc: Dict[str, Any], node_id: str) -> Optional[Tuple[Dict[str, Any], str]]:
    for node, path in iter_program_nodes(doc):
        if node.get("_id") == node_id:
            return node, path
    return None


def parse_lhs_target(lhs: str) -> Tuple[str, Optional[int]]:
    lhs = (lhs or "").strip()
    if not lhs:
        return "", None
    m = _LHS_NS_REF_RE.match(lhs)
    if m:
        name = m.group("name")
        index = m.group("index")
        return name, int(index) if index is not None else None
    match = _SEQ_REF_RE.match(lhs)
    if match:
        return match.group("base"), int(match.group("index"))
    return lhs, None


def normalize_controller_document(
    doc: Dict[str, Any],
    *,
    declare_missing_data: bool = False,
    expand_scalar_dims: bool = False,
    expand_sequence_dims: bool = True,
) -> Dict[str, Any]:
    out: Dict[str, Any] = dict(doc) if isinstance(doc, dict) else {}
    legacy_state_raw = out.get("state") if isinstance(out.get("state"), dict) else {}

    state = legacy_state_raw
    states = state.get("states")
    if not isinstance(states, list):
        states = [state.get("STATE", "Step1")] if isinstance(state.get("STATE"), str) and state.get("STATE") else ["Step1"]
    states = [x for x in states if isinstance(x, str) and x]
    if not states:
        states = ["Step1"]
    cur_state = state.get("STATE")
    if not isinstance(cur_state, str) or not cur_state:
        cur_state = states[0]
    if cur_state not in states:
        states.append(cur_state)
    out["state"] = {"states": states, "STATE": cur_state}

    data = out.get("data")
    if isinstance(data, dict):
        out["data"] = data

        program = out.get("program")
        if isinstance(program, list):
            max_index_by_base: Dict[str, int] = {}

            def visit_expr(text: Any) -> None:
                if not isinstance(text, str):
                    return
                expr_no_str = re.sub(r"'[^']*'|\"[^\"]*\"", "''", text)
                expr_no_str = re.sub(r"\b\d+(?:\.\d+)?[eE][+-]?\d+\b", "0", expr_no_str)
                for m in re.finditer(r"(?P<base>[A-Za-z_][A-Za-z0-9_]*)\[(?P<index>\d+)\]", expr_no_str):
                    base = m.group("base")
                    idx = int(m.group("index"))
                    prev = max_index_by_base.get(base, -1)
                    if idx > prev:
                        max_index_by_base[base] = idx

            def walk_nodes(nodes: List[Any]) -> None:
                for n in nodes:
                    if not isinstance(n, dict):
                        continue
                    op = n.get("op")
                    if op == "if":
                        visit_expr(n.get("cond"))
                        then_nodes = n.get("then", [])
                        else_nodes = n.get("else", [])
                        if isinstance(then_nodes, list):
                            walk_nodes(then_nodes)
                        if isinstance(else_nodes, list):
                            walk_nodes(else_nodes)
                        continue
                    visit_expr(n.get("lhs"))
                    visit_expr(n.get("rhs"))
                    visit_expr(n.get("cond"))
                    visit_expr(n.get("min"))
                    visit_expr(n.get("max"))
                    visit_expr(n.get("true"))
                    visit_expr(n.get("false"))
                    cases = n.get("cases")
                    if isinstance(cases, list):
                        for c in cases:
                            if isinstance(c, dict):
                                visit_expr(c.get("when"))
                                visit_expr(c.get("value"))
                    visit_expr(n.get("else"))

            walk_nodes(program)

            for base, max_idx in max_index_by_base.items():
                need_dim = max_idx + 1
                if need_dim <= 1:
                    continue
                e = data.get(base)
                if not isinstance(e, dict):
                    if not declare_missing_data:
                        continue
                    e = {"kind": "scalar", "type": "f64", "dim": need_dim, "init": [0.0] * need_dim}
                    data[base] = e
                kind = str(e.get("kind") or "scalar")
                allow_expand = (kind == "sequence" and expand_sequence_dims) or (kind != "sequence" and expand_scalar_dims)
                if not allow_expand:
                    continue
                try:
                    cur_dim = int(e.get("dim", 1))
                except Exception:
                    cur_dim = 1
                cur_dim = max(1, cur_dim)
                if need_dim > cur_dim:
                    e["dim"] = need_dim
                init = e.get("init")
                if isinstance(init, list):
                    if len(init) < int(e.get("dim") or 1):
                        fill = init[-1] if init else 0.0
                        e["init"] = list(init) + [fill] * (int(e.get("dim") or 1) - len(init))
                    elif len(init) > int(e.get("dim") or 1):
                        e["init"] = list(init)[: int(e.get("dim") or 1)]
                else:
                    if int(e.get("dim") or 1) > 1:
                        e["init"] = [init if init is not None else 0.0] * int(e.get("dim") or 1)

        for legacy_key in ("ports", "constants", "commit", "types", "descriptions"):
            out.pop(legacy_key, None)
        if isinstance(out.get("state"), dict):
            out["state"].pop("scalars", None)
            out["state"].pop("sequences", None)
        return out

    legacy_ports = out.get("ports") if isinstance(out.get("ports"), dict) else {}
    legacy_inputs = legacy_ports.get("inputs", []) if isinstance(legacy_ports.get("inputs"), list) else []
    legacy_outputs = legacy_ports.get("outputs", []) if isinstance(legacy_ports.get("outputs"), list) else []
    legacy_constants = out.get("constants", {}) if isinstance(out.get("constants"), dict) else {}
    legacy_scalars = legacy_state_raw.get("scalars", {}) if isinstance(legacy_state_raw.get("scalars"), dict) else {}
    legacy_sequences = legacy_state_raw.get("sequences", {}) if isinstance(legacy_state_raw.get("sequences"), dict) else {}
    legacy_commit = out.get("commit", {}) if isinstance(out.get("commit"), dict) else {}
    legacy_shift = legacy_commit.get("shift_sequences", []) if isinstance(legacy_commit.get("shift_sequences"), list) else []
    legacy_types = out.get("types", {}) if isinstance(out.get("types"), dict) else {}
    legacy_desc = out.get("descriptions", {}) if isinstance(out.get("descriptions"), dict) else {}

    def parse_port_type(t: str) -> Tuple[str, int]:
        s = (t or "").strip()
        if not s:
            return "", 1
        if "[" in s and s.endswith("]"):
            base, _, tail = s.partition("[")
            try:
                dim = int(tail[:-1])
            except Exception:
                dim = 1
            return base.strip(), max(1, dim)
        return s, 1

    data2: Dict[str, Any] = {}

    def ensure_entry(name: str) -> Dict[str, Any]:
        if name not in data2 or not isinstance(data2.get(name), dict):
            data2[name] = {}
        return data2[name]

    for k, v in legacy_constants.items():
        if not isinstance(k, str) or not k:
            continue
        e = ensure_entry(k)
        e["kind"] = "constant"
        e["type"] = str(legacy_types.get(k) or "f64")
        if isinstance(v, list):
            e["dim"] = max(1, len(v))
            e["init"] = v
        else:
            e["dim"] = 1
            e["init"] = v
        d = legacy_desc.get(k)
        if isinstance(d, str) and d:
            e["desc"] = d

    for k, v in legacy_scalars.items():
        if not isinstance(k, str) or not k:
            continue
        e = ensure_entry(k)
        e["kind"] = "scalar"
        e["type"] = str(legacy_types.get(k) or "f64")
        if isinstance(v, list):
            e["dim"] = max(1, len(v))
            e["init"] = v
        else:
            e["dim"] = 1
            e["init"] = v
        d = legacy_desc.get(k)
        if isinstance(d, str) and d:
            e["desc"] = d

    for k, v in legacy_sequences.items():
        if not isinstance(k, str) or not k:
            continue
        e = ensure_entry(k)
        e["kind"] = "sequence"
        e["type"] = str(legacy_types.get(k) or "f64")
        init = v.get("init") if isinstance(v, dict) else None
        if isinstance(init, list) and init:
            e["dim"] = max(1, len(init))
            e["init"] = init
        else:
            e["dim"] = 1
            e["init"] = [0.0]
        if k in legacy_shift:
            e["iterate"] = True
        d = legacy_desc.get(k)
        if isinstance(d, str) and d:
            e["desc"] = d

    for p in list(legacy_inputs) + list(legacy_outputs):
        if not isinstance(p, dict):
            continue
        name = p.get("id")
        if not isinstance(name, str) or not name:
            continue
        e = ensure_entry(name)
        if "kind" not in e:
            e["kind"] = "scalar"
        t = p.get("type")
        if isinstance(t, str) and t:
            dt, dim = parse_port_type(t)
            if dt:
                e["type"] = dt
            if "dim" not in e:
                e["dim"] = dim
        if "dim" not in e:
            e["dim"] = 1
        if "init" not in e:
            e["init"] = 0.0 if int(e.get("dim") or 1) == 1 else [0.0] * int(e.get("dim") or 1)
        d = p.get("desc") or p.get("unit")
        if isinstance(d, str) and d and "desc" not in e:
            e["desc"] = d

    program = out.get("program")
    if isinstance(program, list):
        max_index_by_base: Dict[str, int] = {}

        def visit_expr(text: Any) -> None:
            if not isinstance(text, str):
                return
            expr_no_str = re.sub(r"'[^']*'|\"[^\"]*\"", "''", text)
            for m in re.finditer(r"(?P<base>[A-Za-z_][A-Za-z0-9_]*)\[(?P<index>\d+)\]", expr_no_str):
                base = m.group("base")
                idx = int(m.group("index"))
                prev = max_index_by_base.get(base, -1)
                if idx > prev:
                    max_index_by_base[base] = idx

        def walk_nodes(nodes: List[Any]) -> None:
            for n in nodes:
                if not isinstance(n, dict):
                    continue
                op = n.get("op")
                if op == "if":
                    visit_expr(n.get("cond"))
                    then_nodes = n.get("then", [])
                    else_nodes = n.get("else", [])
                    if isinstance(then_nodes, list):
                        walk_nodes(then_nodes)
                    if isinstance(else_nodes, list):
                        walk_nodes(else_nodes)
                    continue
                visit_expr(n.get("lhs"))
                visit_expr(n.get("rhs"))
                visit_expr(n.get("cond"))
                visit_expr(n.get("min"))
                visit_expr(n.get("max"))
                visit_expr(n.get("true"))
                visit_expr(n.get("false"))
                cases = n.get("cases")
                if isinstance(cases, list):
                    for c in cases:
                        if isinstance(c, dict):
                            visit_expr(c.get("when"))
                            visit_expr(c.get("value"))
                visit_expr(n.get("else"))

        walk_nodes(program)

        for base, max_idx in max_index_by_base.items():
            need_dim = max_idx + 1
            if need_dim <= 1:
                continue
            e = ensure_entry(base)
            try:
                cur_dim = int(e.get("dim", 1))
            except Exception:
                cur_dim = 1
            cur_dim = max(1, cur_dim)
            if need_dim > cur_dim:
                e["dim"] = need_dim
            init = e.get("init")
            if isinstance(init, list):
                if len(init) < int(e.get("dim") or 1):
                    fill = init[-1] if init else 0.0
                    init2 = list(init) + [fill] * (int(e.get("dim") or 1) - len(init))
                    e["init"] = init2
                elif len(init) > int(e.get("dim") or 1):
                    e["init"] = list(init)[: int(e.get("dim") or 1)]
            else:
                if int(e.get("dim") or 1) > 1:
                    e["init"] = [init if init is not None else 0.0] * int(e.get("dim") or 1)

    out["data"] = data2
    for legacy_key in ("ports", "constants", "commit", "types", "descriptions"):
        out.pop(legacy_key, None)
    if isinstance(out.get("state"), dict):
        out["state"].pop("scalars", None)
        out["state"].pop("sequences", None)
    return out


def validate_document(doc: Dict[str, Any]) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []

    if not isinstance(doc, dict):
        return [ValidationIssue("error", "根对象必须是 JSON object", "$")]

    schema_version = doc.get("schema_version")
    if not isinstance(schema_version, str) or not schema_version:
        issues.append(ValidationIssue("error", "缺少 schema_version", "$.schema_version"))

    if not isinstance(doc.get("name"), str) or not doc.get("name"):
        issues.append(ValidationIssue("error", "缺少 name", "$.name"))

    dt = doc.get("dt")
    if not isinstance(dt, (int, float)):
        issues.append(ValidationIssue("error", "dt 必须为数字", "$.dt"))
    normalized = normalize_controller_document(
        doc,
        declare_missing_data=False,
        expand_scalar_dims=False,
        expand_sequence_dims=True,
    )

    data = normalized.get("data")
    if not isinstance(data, dict):
        issues.append(ValidationIssue("error", "data 必须为 object", "$.data"))
        data = {}

    dims_scalar: Dict[str, int] = {}
    for name, meta in data.items():
        if not isinstance(name, str) or not name:
            issues.append(ValidationIssue("error", "data 中存在空变量名", "$.data"))
            continue
        if not isinstance(meta, dict):
            issues.append(ValidationIssue("error", "data 项必须为 object", f"$.data.{name}"))
            continue
        kind = str(meta.get("kind") or "")
        if kind != "scalar":
            continue
        dim = meta.get("dim", 1)
        try:
            dim_i = int(dim)
        except Exception:
            dim_i = 1
        dim_i = max(1, dim_i)
        dims_scalar[name] = dim_i

    data_names = {str(k) for k in data.keys() if isinstance(k, str) and k}

    state = normalized.get("state")
    if not isinstance(state, dict):
        issues.append(ValidationIssue("error", "state 必须为 object", "$.state"))
        state = {}

    if not isinstance(state.get("STATE"), str) or not state.get("STATE"):
        issues.append(ValidationIssue("warning", "state.STATE 需要为字符串", "$.state.STATE"))

    states = state.get("states")
    state_values: List[str] = []
    if states is None:
        issues.append(ValidationIssue("warning", "建议补充 state.states 声明所有状态枚举", "$.state.states"))
    elif not isinstance(states, list):
        issues.append(ValidationIssue("error", "state.states 必须为字符串数组", "$.state.states"))
    else:
        for i, v in enumerate(states):
            if not isinstance(v, str) or not v:
                issues.append(ValidationIssue("error", "state.states 中存在空状态值", f"$.state.states[{i}]"))
                continue
            state_values.append(v)
        duplicates = {x for x in state_values if state_values.count(x) > 1}
        for dup in sorted(duplicates):
            issues.append(ValidationIssue("error", f"state.states 状态值重复: {dup}", "$.state.states"))
        current_state = state.get("STATE")
        if isinstance(current_state, str) and current_state and state_values and current_state not in state_values:
            issues.append(ValidationIssue("error", f"state.STATE 不在 state.states 中: {current_state}", "$.state.STATE"))

    program = normalized.get("program")
    if not isinstance(program, list):
        issues.append(ValidationIssue("error", "program 必须为数组", "$.program"))
        return issues

    allowed_funcs = {"abs", "min", "max"}
    allowed_keywords = {"and", "or", "not", "True", "False"}

    def check_expr(expr: Any, expr_path: str) -> None:
        if isinstance(expr, (int, float)):
            return
        if not isinstance(expr, str):
            issues.append(ValidationIssue("error", "表达式必须为字符串或数字", expr_path))
            return
        if not _ALLOWED_EXPR_RE.match(expr):
            issues.append(ValidationIssue("warning", "表达式包含潜在非法字符", expr_path))
        if expr.count("(") != expr.count(")"):
            issues.append(ValidationIssue("warning", "表达式括号不匹配", expr_path))

        if re.search(r"[A-Za-z_][A-Za-z0-9_]*\.", expr):
            issues.append(ValidationIssue("error", "不支持 in./out. 命名空间", expr_path))
            return

        expr_no_str = re.sub(r"'[^']*'|\"[^\"]*\"", "''", expr)
        expr_no_str = re.sub(r"\b\d+(?:\.\d+)?[eE][+-]?\d+\b", "0", expr_no_str)

        for m in re.finditer(r"(?P<base>[A-Za-z_][A-Za-z0-9_]*)\[(?P<index>\d+)\]", expr_no_str):
            base = m.group("base")
            idx = int(m.group("index"))
            if base in dims_scalar and idx >= int(dims_scalar[base]):
                issues.append(ValidationIssue("error", f"数组下标越界: {base}[{idx}]", expr_path))

        for ident in _IDENT_RE.findall(expr_no_str):
            if ident in allowed_funcs or ident in allowed_keywords:
                continue
            if ident == "STATE":
                continue
            if ident in data_names:
                continue
            issues.append(ValidationIssue("error", f"表达式引用未知变量: {ident}", expr_path))

    def check_node(node: Any, node_path: str) -> None:
        if not isinstance(node, dict):
            issues.append(ValidationIssue("error", "program 节点必须为 object", node_path))
            return
        op = node.get("op")
        if op not in {"assign", "if", "clamp", "piecewise", "select", "function"}:
            issues.append(ValidationIssue("error", f"未知 op: {op}", f"{node_path}.op"))
            return

        if op == "function":
            name = node.get("name")
            if not isinstance(name, str) or not name.strip():
                issues.append(ValidationIssue("error", "function.name 必须为非空字符串", f"{node_path}.name"))
            return

        if op == "if":
            check_expr(node.get("cond"), f"{node_path}.cond")
            then_nodes = node.get("then", [])
            else_nodes = node.get("else", [])
            if not isinstance(then_nodes, list):
                issues.append(ValidationIssue("error", "if.then 必须为数组", f"{node_path}.then"))
                then_nodes = []
            if not isinstance(else_nodes, list):
                issues.append(ValidationIssue("error", "if.else 必须为数组", f"{node_path}.else"))
                else_nodes = []
            for i, child in enumerate(then_nodes):
                check_node(child, f"{node_path}.then[{i}]")
            for i, child in enumerate(else_nodes):
                check_node(child, f"{node_path}.else[{i}]")
            return

        lhs = node.get("lhs")
        if not isinstance(lhs, str) or not lhs.strip():
            issues.append(ValidationIssue("error", "缺少 lhs", f"{node_path}.lhs"))
        else:
            base, _ = parse_lhs_target(lhs)
            if base not in data_names and base != "STATE":
                issues.append(ValidationIssue("error", f"lhs 引用了不存在的变量: {base}", f"{node_path}.lhs"))

        if op == "assign":
            check_expr(node.get("rhs"), f"{node_path}.rhs")
            if isinstance(lhs, str) and parse_lhs_target(lhs)[0] == "STATE" and state_values:
                rhs = node.get("rhs")
                if isinstance(rhs, str):
                    m = _STRING_LITERAL_RE.match(rhs)
                    if m:
                        v = m.group("value")
                        if v and v not in state_values:
                            issues.append(ValidationIssue("error", f"STATE 赋值不在 state.states 中: {v}", f"{node_path}.rhs"))
        elif op == "clamp":
            check_expr(node.get("rhs"), f"{node_path}.rhs")
            check_expr(node.get("min"), f"{node_path}.min")
            check_expr(node.get("max"), f"{node_path}.max")
        elif op == "select":
            check_expr(node.get("cond"), f"{node_path}.cond")
            check_expr(node.get("true"), f"{node_path}.true")
            check_expr(node.get("false"), f"{node_path}.false")
        elif op == "piecewise":
            cases = node.get("cases", [])
            if not isinstance(cases, list):
                issues.append(ValidationIssue("error", "piecewise.cases 必须为数组", f"{node_path}.cases"))
                cases = []
            for i, c in enumerate(cases):
                if not isinstance(c, dict):
                    issues.append(ValidationIssue("error", "piecewise.cases 项必须为 object", f"{node_path}.cases[{i}]"))
                    continue
                check_expr(c.get("when"), f"{node_path}.cases[{i}].when")
                check_expr(c.get("value"), f"{node_path}.cases[{i}].value")
            check_expr(node.get("else"), f"{node_path}.else")

    for node, path in iter_program_nodes(normalized):
        check_node(node, f"$.program.{path}" if path else "$.program")

    return issues


def create_default_document() -> Dict[str, Any]:
    return {
        "schema_version": "autopilot.controller.v1",
        "name": "NewController",
        "dt": 0.001,
        "state": {"states": ["Step1"], "STATE": "Step1"},
        "data": {},
        "program": [],
    }


def set_sequence_init(sequences: Dict[str, Any], name: str, values: List[float]) -> None:
    if name not in sequences or not isinstance(sequences.get(name), dict):
        sequences[name] = {"init": [0.0]}
    seq = sequences[name]
    init = seq.get("init")
    if not isinstance(init, list) or not init:
        seq["init"] = [0.0]
        init = seq["init"]
    seq["init"] = list(values) if values else [0.0]


def normalize_path(path: str) -> str:
    return str(Path(path))
