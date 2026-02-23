import os
import math
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from core.autopilot_document import normalize_controller_document


_CPP_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_ARRAY_REF_RE = re.compile(r"(?P<base>[A-Za-z_][A-Za-z0-9_]*)\[(?P<index>\d+)\]")


@dataclass
class _FuncSeg:
    name: str
    comment: str
    nodes: List[Dict[str, Any]]


def generate_cpp_header(doc: Dict[str, Any], source_path: Optional[str] = None) -> str:
    normalized = normalize_controller_document(doc)
    class_name = _class_name_from_path(source_path) or _class_name_from_doc(normalized)
    state = normalized.get("state", {}) if isinstance(normalized.get("state"), dict) else {}
    program = normalized.get("program", []) if isinstance(normalized.get("program"), list) else []
    data = normalized.get("data", {}) if isinstance(normalized.get("data"), dict) else {}

    funcs = _split_functions(program)
    states = state.get("states", []) if isinstance(state.get("states"), list) else []
    current_state = state.get("STATE") if isinstance(state.get("STATE"), str) else ""

    assigned = _assigned_vars(program)
    used = _used_vars(program)
    consts = {k for k, v in data.items() if isinstance(v, dict) and str(v.get("kind") or "") == "constant"}

    inputs = sorted([k for k, v in data.items() if isinstance(v, dict) and str(v.get("io") or "internal") == "input"])
    outputs = sorted([k for k, v in data.items() if isinstance(v, dict) and str(v.get("io") or "internal") == "output"])
    internal = sorted([k for k, v in data.items() if isinstance(v, dict) and str(v.get("io") or "internal") == "internal"])

    h: List[str] = []
    h.append("#pragma once")
    h.append("")
    h.append("#include <algorithm>")
    h.append("#include <cmath>")
    h.append("#include <cstddef>")
    h.append("#include <cstdint>")
    h.append("#include <vector>")
    h.append("")
    h.append(f"class {class_name} {{")
    h.append("public:")
    h.append(f"    {class_name}() = default;")
    h.append(f"    ~{class_name}() = default;")
    h.append("")

    for name in outputs:
        meta = data.get(name, {})
        h.extend(_emit_member_decl(name, meta, indent="    "))
    if outputs:
        h.append("")

    params = []
    for name in inputs:
        meta = data.get(name, {})
        params.append(_cpp_param_decl(name, meta))
    h.append(f"    void update({', '.join(params)}) {{")
    if inputs:
        h.append("        _assignInputs(" + ", ".join([f"{n}_in" for n in inputs]) + ");")
    else:
        h.append("        _assignInputs();")
    for seg in funcs:
        fn = _func_method_name(seg.name)
        h.append(f"        {fn}();")
    h.append("        _iterateSequences();")
    h.append("    }")
    h.append("")

    h.append("// private:")
    h.append("    template <typename T>")
    h.append("    struct DynamicSequence {")
    h.append("        std::vector<T> data_;")
    h.append("        DynamicSequence() : data_(1, T{}) {}")
    h.append("")
    h.append("        T& operator[](size_t n) {")
    h.append("            if (n >= data_.size()) {")
    h.append("                data_.resize(n + 1, T{});")
    h.append("            }")
    h.append("            return data_[n];")
    h.append("        }")
    h.append("")
    h.append("        void shift() {")
    h.append("            for (size_t i = data_.size() - 1; i > 0; --i) {")
    h.append("                data_[i] = data_[i - 1];")
    h.append("            }")
    h.append("        }")
    h.append("")
    h.append("        void zero() noexcept {")
    h.append("            std::fill(data_.begin(), data_.end(), T{});")
    h.append("        }")
    h.append("    };")
    h.append("")
    h.append("    enum class FlightState {")
    for i, s in enumerate([x for x in states if isinstance(x, str) and x]):
        h.append(f"        {_cpp_enum_name(s)}{',' if i < len(states) - 1 else ''}")
    h.append("    };")
    h.append(f"    FlightState STATE = FlightState::{_cpp_enum_name(current_state or (states[0] if states else 'Step1'))};")
    h.append("")

    private_names = []
    private_names.extend([k for k in internal if k not in outputs])
    private_names.extend([k for k in inputs if k not in outputs])
    private_names = sorted(set(private_names))
    for name in private_names:
        meta = data.get(name, {})
        h.extend(_emit_member_decl(name, meta, indent="    "))
    h.append("")

    in_params = []
    for name in inputs:
        meta = data.get(name, {})
        in_params.append(_cpp_param_decl(name, meta))
    h.append(f"    void _assignInputs({', '.join(in_params)}) {{")
    for name in inputs:
        meta = data.get(name, {})
        comment = str(meta.get('desc') or '')
        if comment:
            h.append(f"        // {comment}")
        h.append(_cpp_assign_input(name, meta, indent="        "))
    h.append("    }")
    h.append("")

    for seg in funcs:
        fn = _func_method_name(seg.name)
        if seg.comment:
            h.append(f"    // {seg.comment}")
        h.append(f"    void {fn}() {{")
        h.extend(_emit_nodes(seg.nodes, indent="        ", data=data, states=[x for x in states if isinstance(x, str) and x]))
        h.append("    }")
        h.append("")

    h.append("    void _iterateSequences() {")
    for name, meta in data.items():
        if not isinstance(meta, dict):
            continue
        if str(meta.get("kind") or "") != "sequence":
            continue
        if not bool(meta.get("iterate")):
            continue
        desc = str(meta.get("desc") or "")
        if desc:
            h.append(f"        // {desc}")
        h.append(f"        {name}.shift();")
    h.append("    }")
    h.append("};")
    h.append("")
    return "\n".join(h)


def _class_name_from_doc(doc: Dict[str, Any]) -> str:
    raw = str(doc.get("name") or "Controller").strip() or "Controller"
    return _sanitize_cpp_class_name(raw)


def _class_name_from_path(path: Optional[str]) -> str:
    if not path:
        return ""
    base = os.path.basename(path)
    if base.lower().endswith(".json"):
        base = base[:-5]
    return _sanitize_cpp_class_name(base)


def _sanitize_cpp_class_name(name: str) -> str:
    n = re.sub(r"[^A-Za-z0-9_]", "_", name.strip())
    if not n:
        n = "Controller"
    if n[0].isdigit():
        n = "_" + n
    return n


def _cpp_enum_name(s: str) -> str:
    n = re.sub(r"[^A-Za-z0-9_]", "_", (s or "").strip())
    if not n:
        n = "Unknown"
    if n[0].isdigit():
        n = "_" + n
    return n


def _cpp_type(meta: Any) -> str:
    t = str(meta.get("type") or "f64") if isinstance(meta, dict) else "f64"
    if t == "f32":
        return "float"
    if t == "f64":
        return "double"
    if t == "int":
        return "int32_t"
    if t == "uint":
        return "uint32_t"
    return "double"


def _emit_member_decl(name: str, meta: Any, *, indent: str) -> List[str]:
    out: List[str] = []
    if not isinstance(meta, dict):
        meta = {}
    kind = str(meta.get("kind") or "scalar")
    desc = str(meta.get("desc") or "")
    dim = int(meta.get("dim") or 1) if isinstance(meta.get("dim"), (int, float, str)) else 1
    dim = max(1, dim)
    ctype = _cpp_type(meta)

    if desc:
        out.append(f"{indent}// {desc}")

    if kind == "sequence":
        out.append(f"{indent}DynamicSequence<{ctype}> {name};")
        return out

    init = meta.get("init")
    if dim == 1:
        prefix = "const " if kind == "constant" else ""
        out.append(f"{indent}{prefix}{ctype} {name} = {_cpp_literal(init, ctype)};")
        return out

    init_list = _cpp_init_list(init, dim, ctype)
    prefix = "const " if kind == "constant" else ""
    out.append(f"{indent}{prefix}std::vector<{ctype}> {name} = {init_list};")
    return out


def _cpp_param_decl(name: str, meta: Any) -> str:
    if not isinstance(meta, dict):
        meta = {}
    kind = str(meta.get("kind") or "scalar")
    ctype = _cpp_type(meta)
    dim = meta.get("dim", 1)
    try:
        dim_i = int(dim)
    except Exception:
        dim_i = 1
    dim_i = max(1, dim_i)
    if kind == "sequence":
        return f"{ctype} {name}_in"
    if dim_i > 1:
        return f"const std::vector<{ctype}>& {name}_in"
    return f"{ctype} {name}_in"


def _cpp_assign_input(name: str, meta: Any, *, indent: str) -> str:
    if not isinstance(meta, dict):
        meta = {}
    kind = str(meta.get("kind") or "scalar")
    dim = meta.get("dim", 1)
    try:
        dim_i = int(dim)
    except Exception:
        dim_i = 1
    dim_i = max(1, dim_i)
    if kind == "sequence":
        return f"{indent}{name}[0] = {name}_in;"
    if dim_i > 1:
        return f"{indent}{name} = {name}_in;"
    return f"{indent}{name} = {name}_in;"


def _cpp_literal(v: Any, ctype: str) -> str:
    if ctype in {"float", "double"}:
        try:
            return str(float(v))
        except Exception:
            return "0.0"
    try:
        return str(int(v))
    except Exception:
        return "0"


def _cpp_init_list(v: Any, dim: int, ctype: str) -> str:
    values: List[str] = []
    if isinstance(v, list):
        values = [_cpp_literal(x, ctype) for x in v]
    if not values:
        values = [_cpp_literal(0, ctype)]
    if len(values) == 1:
        values = values * dim
    if len(values) < dim:
        values = values + [values[-1]] * (dim - len(values))
    if len(values) > dim:
        values = values[:dim]
    return "{" + ", ".join(values) + "}"


def _cpp_float_literal(v: Any) -> str:
    try:
        fv = float(v)
    except Exception:
        return "0.0"
    if not math.isfinite(fv):
        return "INFINITY" if fv > 0 else "-INFINITY"
    if fv.is_integer():
        if abs(fv) < 1e15:
            return f"{int(fv)}.0"
        return f"{fv:.0e}"
    return f"{fv:g}"


def _clamp_bound_to_cpp(v: Any, states: List[str], target_ctype: str) -> str:
    def typed_infinity(sign: int) -> str:
        if target_ctype == "double":
            base = "(double)INFINITY"
            return base if sign >= 0 else "-" + base
        return "INFINITY" if sign >= 0 else "-INFINITY"

    def typed_zero() -> str:
        return "0.0f" if target_ctype == "float" else "0.0"

    def typed_numeric_literal(text: str) -> str:
        s2 = text.strip()
        if re.fullmatch(r"[+-]?\d+", s2):
            s2 = s2 + ".0"
        if target_ctype == "float":
            return s2 if s2.lower().endswith("f") else s2 + "f"
        if target_ctype == "double" and s2.lower().endswith("f"):
            return s2[:-1]
        return s2

    if isinstance(v, (int, float)) and not isinstance(v, bool):
        try:
            fv = float(v)
        except Exception:
            return typed_zero()
        if not math.isfinite(fv):
            return typed_infinity(1 if fv > 0 else -1)
        return typed_numeric_literal(_cpp_float_literal(fv))

    s = str(v or "").strip()
    if not s:
        return typed_zero()
    sl = s.lower()
    if sl in {"inf", "+inf", "infinity", "+infinity"}:
        return typed_infinity(1)
    if sl in {"-inf", "-infinity"}:
        return typed_infinity(-1)
    if s in {"INFINITY", "-INFINITY"}:
        return typed_infinity(1 if s == "INFINITY" else -1)

    if re.fullmatch(r"[+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?", s):
        return typed_numeric_literal(s)

    expr = _expr_to_cpp(s, states)
    if target_ctype == "double":
        expr = re.sub(r"\bINFINITY\b", "(double)INFINITY", expr)
    return expr


def _split_functions(program: Sequence[Any]) -> List[_FuncSeg]:
    funcs: List[_FuncSeg] = []
    cur = _FuncSeg(name="Default", comment="", nodes=[])
    for n in program:
        if not isinstance(n, dict):
            continue
        if n.get("op") == "function":
            if cur.nodes or cur.comment or cur.name != "Default":
                funcs.append(cur)
            cur = _FuncSeg(
                name=str(n.get("name") or "").strip() or "Function",
                comment=str(n.get("comment") or "").strip(),
                nodes=[],
            )
            continue
        cur.nodes.append(n)
    if cur.nodes or not funcs:
        funcs.append(cur)
    return funcs


def _func_method_name(name: str) -> str:
    raw = re.sub(r"[^A-Za-z0-9_]", "_", (name or "").strip())
    if not raw:
        raw = "Function"
    if raw[0].isdigit():
        raw = "_" + raw
    return "_fn_" + raw


def _assigned_vars(program: Sequence[Any]) -> Set[str]:
    out: Set[str] = set()

    def walk(nodes: Sequence[Any]) -> None:
        for n in nodes:
            if not isinstance(n, dict):
                continue
            op = n.get("op")
            if op == "if":
                walk(n.get("then", []) if isinstance(n.get("then"), list) else [])
                walk(n.get("else", []) if isinstance(n.get("else"), list) else [])
                continue
            if op == "function":
                continue
            lhs = n.get("lhs")
            if isinstance(lhs, str) and lhs:
                base = lhs.split("[", 1)[0].strip()
                if base:
                    out.add(base)

    walk(program)
    return out


def _used_vars(program: Sequence[Any]) -> Set[str]:
    out: Set[str] = set()
    allowed = {"abs", "min", "max", "and", "or", "not", "True", "False"}

    def scan_expr(expr: Any):
        if not isinstance(expr, str):
            return
        expr2 = re.sub(r"'[^']*'|\"[^\"]*\"", "''", expr)
        expr2 = re.sub(r"\b\d+(?:\.\d+)?[eE][+-]?\d+\b", "0", expr2)
        for m in re.finditer(r"[A-Za-z_][A-Za-z0-9_]*", expr2):
            ident = m.group(0)
            if ident in allowed or ident == "STATE":
                continue
            out.add(ident)

    def walk(nodes: Sequence[Any]) -> None:
        for n in nodes:
            if not isinstance(n, dict):
                continue
            op = n.get("op")
            if op == "if":
                scan_expr(n.get("cond"))
                walk(n.get("then", []) if isinstance(n.get("then"), list) else [])
                walk(n.get("else", []) if isinstance(n.get("else"), list) else [])
                continue
            if op == "function":
                continue
            for k in ("rhs", "cond", "min", "max", "true", "false", "else"):
                scan_expr(n.get(k))
            cases = n.get("cases")
            if isinstance(cases, list):
                for c in cases:
                    if isinstance(c, dict):
                        scan_expr(c.get("when"))
                        scan_expr(c.get("value"))

    walk(program)
    return out


def _infer_outputs(program: Sequence[Any], data: Dict[str, Any], inputs: List[str]) -> List[str]:
    assigned = _assigned_vars(program)
    used = _used_vars(program)
    candidates = []
    for name, meta in data.items():
        if not isinstance(meta, dict):
            continue
        if str(meta.get("kind") or "") != "scalar":
            continue
        if name not in assigned:
            continue
        if name in inputs:
            continue
        candidates.append(name)

    out: List[str] = []
    for name in candidates:
        if name not in used:
            out.append(name)
            continue
        if _only_self_read_for_clamp(program, name):
            out.append(name)
    if not out and candidates:
        out = candidates
    return sorted(out)


def _only_self_read_for_clamp(program: Sequence[Any], target: str) -> bool:
    def scan_expr(expr: Any) -> bool:
        if not isinstance(expr, str):
            return False
        expr2 = re.sub(r"'[^']*'|\"[^\"]*\"", "''", expr)
        for m in re.finditer(r"[A-Za-z_][A-Za-z0-9_]*", expr2):
            if m.group(0) == target:
                return True
        return False

    def walk(nodes: Sequence[Any]) -> bool:
        for n in nodes:
            if not isinstance(n, dict):
                continue
            op = n.get("op")
            if op == "if":
                if walk(n.get("then", []) if isinstance(n.get("then"), list) else []):
                    return True
                if walk(n.get("else", []) if isinstance(n.get("else"), list) else []):
                    return True
                continue
            if op == "clamp":
                lhs = n.get("lhs")
                if isinstance(lhs, str) and lhs.split("[", 1)[0].strip() == target:
                    rhs = n.get("rhs")
                    if isinstance(rhs, str) and rhs.split("[", 1)[0].strip() == target:
                        continue
                    return True
            if op == "assign":
                rhs = n.get("rhs")
                if scan_expr(rhs) and (n.get("lhs") or "").split("[", 1)[0].strip() != target:
                    return True
        return False

    return not walk(program)


def _iter_private_members(data: Dict[str, Any], outputs: List[str]) -> List[Tuple[str, Dict[str, Any]]]:
    out: List[Tuple[str, Dict[str, Any]]] = []
    out_set = set(outputs)
    for name in sorted([k for k in data.keys() if isinstance(k, str) and k]):
        if name in out_set:
            continue
        meta = data.get(name)
        if isinstance(meta, dict):
            out.append((name, meta))
    return out


def _emit_nodes(nodes: Sequence[Any], *, indent: str, data: Dict[str, Any], states: List[str]) -> List[str]:
    out: List[str] = []
    for n in nodes:
        if not isinstance(n, dict):
            continue
        op = n.get("op")
        if op == "function":
            continue
        comment = str(n.get("comment") or "").strip()
        if comment:
            out.append(f"{indent}// {comment}")
        if op == "assign":
            lhs = str(n.get("lhs") or "")
            rhs = _expr_to_cpp(str(n.get("rhs") or ""), states)
            out.append(f"{indent}{lhs} = {rhs};")
        elif op == "clamp":
            lhs = str(n.get("lhs") or "")
            rhs = _expr_to_cpp(str(n.get("rhs") or ""), states)
            base = lhs.split("[", 1)[0].strip()
            meta = data.get(base, {}) if isinstance(data, dict) else {}
            ctype = _cpp_type(meta) if isinstance(meta, dict) else "double"
            mn = _clamp_bound_to_cpp(n.get("min"), states, ctype)
            mx = _clamp_bound_to_cpp(n.get("max"), states, ctype)
            out.append(f"{indent}{lhs} = std::clamp({rhs}, {mn}, {mx});")
        elif op == "select":
            lhs = str(n.get("lhs") or "")
            cond = _expr_to_cpp(str(n.get("cond") or ""), states)
            t = _expr_to_cpp(str(n.get("true") or ""), states)
            f = _expr_to_cpp(str(n.get("false") or ""), states)
            out.append(f"{indent}{lhs} = ({cond} ? {t} : {f});")
        elif op == "piecewise":
            lhs = str(n.get("lhs") or "")
            cases = n.get("cases", [])
            emitted = False
            if isinstance(cases, list):
                for i, c in enumerate(cases):
                    if not isinstance(c, dict):
                        continue
                    when = _expr_to_cpp(str(c.get("when") or ""), states)
                    value = _expr_to_cpp(str(c.get("value") or ""), states)
                    if not emitted:
                        out.append(f"{indent}if ({when}) {{")
                        out.append(f"{indent}    {lhs} = {value};")
                        out.append(f"{indent}}}")
                        emitted = True
                    else:
                        out.append(f"{indent}else if ({when}) {{")
                        out.append(f"{indent}    {lhs} = {value};")
                        out.append(f"{indent}}}")
            else_value = _expr_to_cpp(str(n.get("else") or ""), states)
            if not emitted:
                out.append(f"{indent}{lhs} = {else_value};")
            else:
                out.append(f"{indent}else {{")
                out.append(f"{indent}    {lhs} = {else_value};")
                out.append(f"{indent}}}")
        elif op == "if":
            cond = _expr_to_cpp(str(n.get("cond") or ""), states)
            out.append(f"{indent}if ({cond}) {{")
            out.extend(_emit_nodes(n.get("then", []) if isinstance(n.get("then"), list) else [], indent=indent + "    ", data=data, states=states))
            out.append(f"{indent}}} else {{")
            out.extend(_emit_nodes(n.get("else", []) if isinstance(n.get("else"), list) else [], indent=indent + "    ", data=data, states=states))
            out.append(f"{indent}}}")
    return out


def _expr_to_cpp(expr: str, states: List[str]) -> str:
    s = (expr or "").strip()
    if not s:
        return "0"
    s = re.sub(r"\band\b", "&&", s)
    s = re.sub(r"\bor\b", "||", s)
    s = re.sub(r"\bnot\b", "!", s)
    s = s.replace("True", "true").replace("False", "false")
    s = re.sub(r"\b(?:inf|infinity)\b", "INFINITY", s, flags=re.IGNORECASE)

    def replace_state(m: re.Match) -> str:
        val = m.group(1)
        if val in states:
            return f"FlightState::{_cpp_enum_name(val)}"
        return f"\"{val}\""

    s = re.sub(r"'([^']+)'", replace_state, s)
    s = re.sub(r"\"([^\"]+)\"", replace_state, s)
    s = re.sub(r"\babs\s*\(", "std::abs(", s)
    s = re.sub(r"\bmin\s*\(", "std::min(", s)
    s = re.sub(r"\bmax\s*\(", "std::max(", s)
    return s
