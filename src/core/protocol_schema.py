import csv
import os
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


CSV_COLUMNS = [
    "index",
    "length",
    "type",
    "name_cn",
    "name_en",
    "lsb",
    "default",
    "is_valid",
]

TYPE_OPTIONS = [
    "CONST",
    "ANY",
    "U8",
    "S8",
    "U16",
    "S16",
    "U32",
    "S32",
    "U8F",
    "S8F",
    "U16F",
    "S16F",
    "U32F",
    "S32F",
    "F32",
    "F64",
    "BIT",
]

TYPE_SPECS: Dict[str, Dict[str, Optional[str]]] = {
    "CONST": {"bytes": 1, "cpp_type": "uint8_t", "log_type": "UInt8"},
    "ANY": {"bytes": 1, "cpp_type": "uint8_t", "log_type": "UInt8"},
    "U8": {"bytes": 1, "cpp_type": "uint8_t", "log_type": "UInt8"},
    "S8": {"bytes": 1, "cpp_type": "int8_t", "log_type": "Int8"},
    "U16": {"bytes": 2, "cpp_type": "uint16_t", "log_type": "UInt16"},
    "S16": {"bytes": 2, "cpp_type": "int16_t", "log_type": "Int16"},
    "U32": {"bytes": 4, "cpp_type": "uint32_t", "log_type": "UInt32"},
    "S32": {"bytes": 4, "cpp_type": "int32_t", "log_type": "Int32"},
    "U8F": {"bytes": 1, "cpp_type": "double", "log_type": "Float64"},
    "S8F": {"bytes": 1, "cpp_type": "double", "log_type": "Float64"},
    "U16F": {"bytes": 2, "cpp_type": "double", "log_type": "Float64"},
    "S16F": {"bytes": 2, "cpp_type": "double", "log_type": "Float64"},
    "U32F": {"bytes": 4, "cpp_type": "double", "log_type": "Float64"},
    "S32F": {"bytes": 4, "cpp_type": "double", "log_type": "Float64"},
    "F32": {"bytes": 4, "cpp_type": "float", "log_type": "Float32"},
    "F64": {"bytes": 8, "cpp_type": "double", "log_type": "Float64"},
    "BIT": {"bytes": None, "cpp_type": None, "log_type": None},
}


@dataclass
class FieldSpec:
    index: int
    length: int
    field_type: str
    name_cn: str
    name_en: str
    lsb: Optional[float]
    default: Optional[str]
    is_valid: bool


@dataclass
class ArrayRef:
    base: str
    index: int
    field: Optional[str]


def parse_array_ref(name_en: str) -> Optional[ArrayRef]:
    pattern = re.compile(r"^(?P<base>[A-Za-z_]\w*)\[(?P<index>\d+)\](?:\.(?P<field>[A-Za-z_]\w*))?$")
    match = pattern.match(name_en.strip())
    if not match:
        return None
    return ArrayRef(
        base=match.group("base"),
        index=int(match.group("index")),
        field=match.group("field"),
    )


def split_group_name(name_en: str) -> Tuple[Optional[str], str]:
    if "." not in name_en:
        return None, name_en
    parts = name_en.split(".")
    return parts[0], parts[-1]


def normalize_identifier(name: str) -> str:
    name = name.strip()
    if not name:
        return "_"
    name = re.sub(r"[^\w]", "_", name)
    if name[0].isdigit():
        name = f"_{name}"
    return name


def to_struct_name(name: str) -> str:
    name = normalize_identifier(name)
    return name[:1].upper() + name[1:]


def parse_bool(value: str) -> bool:
    text = (value or "").strip().lower()
    if text in ("1", "true", "yes", "y", "是"):
        return True
    if text in ("0", "false", "no", "n", "否"):
        return False
    return False


def parse_float(value: str) -> Optional[float]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_int(value: str) -> Optional[int]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(text, 0)
    except ValueError:
        return None


def load_csv(path: str) -> List[FieldSpec]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)
    if not rows:
        return []
    header = [h.strip() for h in rows[0]]
    col_index = {name: idx for idx, name in enumerate(header)}
    fields = []
    auto_index = 1
    for row in rows[1:]:
        if not any(str(item).strip() for item in row):
            continue
        def get_col(key):
            idx = col_index.get(key)
            if idx is None or idx >= len(row):
                return ""
            return row[idx]
        raw_index = get_col("index")
        index_val = parse_int(raw_index)
        if index_val is None:
            index_val = auto_index
        auto_index = index_val + 1
        length_val = parse_int(get_col("length")) or 0
        field_type = (get_col("type") or "").strip().upper()
        name_cn = (get_col("name_cn") or "").strip()
        name_en = (get_col("name_en") or "").strip()
        lsb_val = parse_float(get_col("lsb"))
        default_val = (get_col("default") or "").strip()
        is_valid = parse_bool(get_col("is_valid"))
        if field_type == "BIT":
            is_valid = True
        fields.append(FieldSpec(
            index=index_val,
            length=length_val,
            field_type=field_type,
            name_cn=name_cn,
            name_en=name_en,
            lsb=lsb_val,
            default=default_val if default_val != "" else None,
            is_valid=is_valid,
        ))
    return fields


def save_csv(path: str, fields: List[FieldSpec]) -> None:
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_COLUMNS)
        positions = compute_byte_positions(fields)
        for idx, field in enumerate(fields, start=1):
            writer.writerow([
                positions[idx - 1] if idx - 1 < len(positions) else "",
                field.length,
                field.field_type,
                field.name_cn,
                field.name_en,
                "" if field.lsb is None else field.lsb,
                "" if field.default is None else field.default,
                "1" if field.is_valid else "0",
            ])


def validate_fields(fields: List[FieldSpec]) -> List[str]:
    warnings = []
    for field in fields:
        if field.field_type not in TYPE_OPTIONS:
            warnings.append(f"未知类型: {field.field_type} (序号 {field.index})")
            continue
        if field.field_type == "BIT":
            if field.length <= 0:
                warnings.append(f"BIT 长度必须大于0 (序号 {field.index})")
            continue
        expected = TYPE_SPECS[field.field_type]["bytes"]
        if expected is not None and field.length not in (0, expected):
            warnings.append(
                f"类型 {field.field_type} 长度应为 {expected} 字节 (序号 {field.index})"
            )
    return warnings


@dataclass
class FieldMeta:
    spec: FieldSpec
    byte_offset: int = 0
    bit_offset: int = 0
    bit_group: Optional["BitGroup"] = None
    array_ref: Optional[ArrayRef] = None
    frame_offset: Optional[int] = None


@dataclass
class BitGroup:
    name: str
    struct_name: str
    member_name: str
    start_offset: int
    total_bits: int
    container_bits: int
    fields: List[FieldMeta]
    frame_offset: Optional[int] = None


@dataclass
class ArrayGroup:
    base: str
    count: int
    is_struct: bool
    struct_name: Optional[str]
    element_type: Optional[str]
    fields: Dict[str, str]


def _escape_cpp_string(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


def _format_int_literal(value: int) -> str:
    return str(int(value))


def _format_float_literal(value: float) -> str:
    return f"{value:.10g}"


def _infer_default_numeric(field: FieldSpec) -> Optional[str]:
    if field.default is None:
        return None
    if field.field_type in ("F32", "F64") or field.field_type.endswith("F"):
        value = parse_float(field.default)
        if value is None:
            int_value = parse_int(field.default)
            if int_value is None:
                return None
            value = float(int_value)
        return _format_float_literal(value)
    value = parse_int(field.default)
    if value is None:
        value = parse_float(field.default)
        if value is None:
            return None
        return _format_float_literal(value)
    return _format_int_literal(value)


def _build_layout(fields: List[FieldSpec]) -> Tuple[List[FieldMeta], List[BitGroup], int]:
    metas: List[FieldMeta] = []
    bit_groups: List[BitGroup] = []
    offset = 0
    current_group: Optional[BitGroup] = None
    group_index = 1

    for spec in fields:
        meta = FieldMeta(spec=spec, array_ref=parse_array_ref(spec.name_en))
        if spec.field_type == "BIT":
            if current_group is None:
                group_name, _ = split_group_name(spec.name_en)
                if not group_name:
                    group_name = f"bitGroup{group_index}"
                    group_index += 1
                current_group = BitGroup(
                    name=group_name,
                    struct_name=to_struct_name(group_name),
                    member_name=normalize_identifier(group_name),
                    start_offset=offset,
                    total_bits=0,
                    container_bits=0,
                    fields=[],
                )
                bit_groups.append(current_group)
            meta.byte_offset = current_group.start_offset
            meta.bit_offset = current_group.total_bits
            current_group.fields.append(meta)
            current_group.total_bits += max(spec.length, 0)
        else:
            if current_group is not None:
                offset = current_group.start_offset + ((current_group.total_bits + 7) // 8)
                current_group = None
            meta.byte_offset = offset
            offset += max(spec.length, 0)
        metas.append(meta)

    if current_group is not None:
        offset = current_group.start_offset + ((current_group.total_bits + 7) // 8)

    for group in bit_groups:
        if group.total_bits <= 8:
            group.container_bits = 8
        elif group.total_bits <= 16:
            group.container_bits = 16
        elif group.total_bits <= 32:
            group.container_bits = 32
        else:
            group.container_bits = 32
    return metas, bit_groups, offset


def _field_byte_length(spec: FieldSpec) -> int:
    expected = TYPE_SPECS.get(spec.field_type, {}).get("bytes")
    if expected is not None:
        return int(expected)
    if spec.length > 0:
        return int(spec.length)
    return 0


def _bit_group_container_bytes(total_bits: int) -> int:
    if total_bits <= 8:
        return 1
    if total_bits <= 16:
        return 2
    return 4


def compute_byte_positions(fields: List[FieldSpec]) -> List[str]:
    positions = [""] * len(fields)
    offset = 0
    group_indices: List[int] = []
    group_bits = 0

    def flush_group():
        nonlocal offset, group_indices, group_bits
        if not group_indices:
            return
        bytes_len = _bit_group_container_bytes(group_bits)
        start = offset + 1
        end = offset + bytes_len
        label = f"B{start}" if bytes_len == 1 else f"B{start}-{end}"
        for idx in group_indices:
            positions[idx] = label
        offset += bytes_len
        group_indices = []
        group_bits = 0

    for idx, spec in enumerate(fields):
        if spec.field_type == "BIT":
            group_indices.append(idx)
            group_bits += max(spec.length, 0)
            continue
        flush_group()
        bytes_len = _field_byte_length(spec)
        if bytes_len <= 0:
            positions[idx] = ""
            continue
        start = offset + 1
        end = offset + bytes_len
        positions[idx] = f"B{start}" if bytes_len == 1 else f"B{start}-{end}"
        offset += bytes_len
    flush_group()
    return positions


def _compute_frame_offsets(metas: List[FieldMeta], bit_groups: List[BitGroup]) -> int:
    frame_offset = 0
    processed_groups = set()
    for meta in metas:
        spec = meta.spec
        if spec.field_type == "BIT":
            group = next((g for g in bit_groups if meta in g.fields), None)
            if group is None or group.member_name in processed_groups:
                continue
            processed_groups.add(group.member_name)
            if not any(item.spec.is_valid for item in group.fields):
                continue
            group.frame_offset = frame_offset
            frame_offset += group.container_bits // 8
            continue
        if not spec.is_valid:
            continue
        meta.frame_offset = frame_offset
        frame_offset += _field_byte_length(spec)
    return frame_offset


def _collect_arrays(metas: List[FieldMeta]) -> Dict[str, ArrayGroup]:
    arrays: Dict[str, ArrayGroup] = {}
    for meta in metas:
        if meta.array_ref is None:
            continue
        base = meta.array_ref.base
        field = meta.array_ref.field
        spec = meta.spec
        spec_info = TYPE_SPECS.get(spec.field_type, {})
        cpp_type = spec_info.get("cpp_type")

        group = arrays.get(base)
        if group is None:
            group = ArrayGroup(
                base=base,
                count=0,
                is_struct=field is not None,
                struct_name=to_struct_name(base),
                element_type=None,
                fields={},
            )
            arrays[base] = group
        group.count = max(group.count, meta.array_ref.index + 1)
        if field is None:
            group.is_struct = False
            group.element_type = cpp_type
        else:
            group.is_struct = True
            group.fields[field] = cpp_type or "double"
    return arrays


def generate_cpp_code(frame_name: str, fields: List[FieldSpec]) -> str:
    metas, bit_groups, frame_size = _build_layout(fields)
    frame_size = _compute_frame_offsets(metas, bit_groups)
    arrays = _collect_arrays(metas)
    array_field_specs: Dict[str, Dict[str, FieldSpec]] = {}
    array_base_specs: Dict[str, FieldSpec] = {}
    for meta in metas:
        if meta.array_ref is None:
            continue
        ref = meta.array_ref
        if ref.field:
            array_field_specs.setdefault(ref.base, {})
            if ref.field not in array_field_specs[ref.base]:
                array_field_specs[ref.base][ref.field] = meta.spec
        else:
            if ref.base not in array_base_specs:
                array_base_specs[ref.base] = meta.spec
    frame_struct_name = to_struct_name(frame_name)
    protocol_name = f"{frame_struct_name}Protocol"
    default_assignments: List[Tuple[str, str]] = []

    def build_comment(spec: Optional[FieldSpec], fallback: str = "", extra: Optional[str] = None) -> str:
        parts = []
        name_value = ""
        if spec:
            name_value = spec.name_cn or spec.name_en
        if not name_value:
            name_value = fallback
        if name_value:
            parts.append(name_value)
        if spec and not spec.is_valid:
            parts.append("非解析字段")
        if extra:
            parts.append(extra)
        if not parts:
            return ""
        return " // " + " / ".join(parts)

    def build_target(meta: FieldMeta) -> Optional[str]:
        spec = meta.spec
        if spec.field_type == "BIT":
            group = next((g for g in bit_groups if meta in g.fields), None)
            if group is None:
                return None
            _, field_name = split_group_name(spec.name_en)
            return f"{group.member_name}.{normalize_identifier(field_name)}"
        if meta.array_ref is not None:
            ref = meta.array_ref
            if ref.field:
                return f"{ref.base}[{ref.index}].{normalize_identifier(ref.field)}"
            return f"{ref.base}[{ref.index}]"
        return normalize_identifier(spec.name_en)

    for meta in metas:
        spec = meta.spec
        literal = _infer_default_numeric(spec)
        if literal is None:
            continue
        target = build_target(meta)
        if not target:
            continue
        default_assignments.append((target, literal))

    lines: List[str] = []
    lines.append("#pragma once")
    lines.append("// Auto-generated by the Protocol Modeling tool. Do not edit manually.")
    lines.append("#include <array>")
    lines.append("#include <cstddef>")
    lines.append("#include <cstdint>")
    lines.append("#include <cstring>")
    lines.append('#include "MB_DDF/Tools/SelfDescribingLog.h"')
    lines.append("")
    lines.append("namespace ProtocolModel {")
    lines.append("")
    lines.append(f"struct {frame_struct_name} {{")

    for group in arrays.values():
        if not group.is_struct:
            continue
        lines.append(f"    struct {group.struct_name} {{")
        for field_name, cpp_type in group.fields.items():
            spec = array_field_specs.get(group.base, {}).get(field_name)
            comment = build_comment(spec, field_name)
            lines.append(f"        {cpp_type} {normalize_identifier(field_name)};{comment}")
        lines.append("    };")

    for group in bit_groups:
        if not group.fields:
            continue
        base_type = "uint8_t" if group.container_bits == 8 else "uint16_t" if group.container_bits == 16 else "uint32_t"
        lines.append(f"    struct {group.struct_name} {{")
        for meta in group.fields:
            _, field_name = split_group_name(meta.spec.name_en)
            field_name = normalize_identifier(field_name)
            comment = build_comment(meta.spec, field_name)
            lines.append(f"        {base_type} {field_name} : {meta.spec.length};{comment}")
        lines.append("    };")

    declared = set()
    for meta in metas:
        spec = meta.spec
        if spec.field_type == "BIT":
            group = meta.bit_group or next((g for g in bit_groups if meta in g.fields), None)
            if group is None:
                continue
            if group.member_name in declared:
                continue
            lines.append(f"    {group.struct_name} {group.member_name};")
            declared.add(group.member_name)
            continue
        if meta.array_ref is not None:
            base = meta.array_ref.base
            if base in declared:
                continue
            group = arrays.get(base)
            if group is None:
                continue
            comment = ""
            array_items = [
                item for item in metas
                if item.array_ref and item.array_ref.base == base
            ]
            has_valid = any(item.spec.is_valid for item in array_items)
            has_invalid = any(not item.spec.is_valid for item in array_items)
            extra = None
            if not has_valid:
                extra = "非解析字段"
            elif has_invalid:
                extra = "含非解析字段"
            base_spec = array_base_specs.get(base)
            comment = build_comment(base_spec, base, extra)
            if group.is_struct:
                lines.append(f"    {group.struct_name} {base}[{group.count}];{comment}")
            else:
                cpp_type = group.element_type or "uint8_t"
                lines.append(f"    {cpp_type} {base}[{group.count}];{comment}")
            declared.add(base)
            continue
        cpp_type = TYPE_SPECS.get(spec.field_type, {}).get("cpp_type", "uint8_t")
        field_name = normalize_identifier(spec.name_en)
        if field_name in declared:
            continue
        comment = build_comment(spec, field_name)
        lines.append(f"    {cpp_type} {field_name};{comment}")
        declared.add(field_name)

    if default_assignments:
        lines.append("")
        lines.append("    // Initialize fields with default values.")
        lines.append(f"    {frame_struct_name}() {{")
        for target, literal in default_assignments:
            lines.append(f"        {target} = {literal};")
        lines.append("    }")

    lines.append("};")
    lines.append("")

    lines.append(f"class {protocol_name} {{")
    lines.append("public:")
    lines.append(f"    constexpr static size_t FRAME_SIZE = {frame_size};")
    lines.append("")
    lines.append("    // Return byte offset of a member within the frame struct.")
    lines.append("    template<typename T, typename Member>")
    lines.append("    constexpr static uint32_t offset_of_member(Member T::*member_ptr) {")
    lines.append("        return static_cast<uint32_t>(")
    lines.append("            reinterpret_cast<uintptr_t>(")
    lines.append("                &(static_cast<T*>(nullptr)->*member_ptr)")
    lines.append("            )")
    lines.append("        );")
    lines.append("    }")
    lines.append("")
    lines.append("    // Write 16-bit unsigned integer in little-endian.")
    lines.append("    static inline void writeLe16(char* dst, uint16_t value) {")
    lines.append("        dst[0] = static_cast<char>(value & 0xFF);")
    lines.append("        dst[1] = static_cast<char>((value >> 8) & 0xFF);")
    lines.append("    }")
    lines.append("")
    lines.append("    // Write 32-bit unsigned integer in little-endian.")
    lines.append("    static inline void writeLe32(char* dst, uint32_t value) {")
    lines.append("        dst[0] = static_cast<char>(value & 0xFF);")
    lines.append("        dst[1] = static_cast<char>((value >> 8) & 0xFF);")
    lines.append("        dst[2] = static_cast<char>((value >> 16) & 0xFF);")
    lines.append("        dst[3] = static_cast<char>((value >> 24) & 0xFF);")
    lines.append("    }")
    lines.append("")
    lines.append("    // Read 16-bit unsigned integer in little-endian.")
    lines.append("    static inline uint16_t readLe16(const char* src) {")
    lines.append("        return static_cast<uint8_t>(src[0]) | (static_cast<uint8_t>(src[1]) << 8);")
    lines.append("    }")
    lines.append("")
    lines.append("    // Read 32-bit unsigned integer in little-endian.")
    lines.append("    static inline uint32_t readLe32(const char* src) {")
    lines.append("        return static_cast<uint8_t>(src[0]) | (static_cast<uint8_t>(src[1]) << 8)")
    lines.append("            | (static_cast<uint8_t>(src[2]) << 16) | (static_cast<uint8_t>(src[3]) << 24);")
    lines.append("    }")
    lines.append("")
    lines.append("    // Encode unsigned value with LSB scaling.")
    lines.append("    static inline uint32_t encodeUnsigned(double actual, double lsb) {")
    lines.append("        return static_cast<uint32_t>(actual / lsb);")
    lines.append("    }")
    lines.append("")
    lines.append("    // Encode signed value with LSB scaling.")
    lines.append("    static inline int32_t encodeSigned(double actual, double lsb) {")
    lines.append("        return static_cast<int32_t>(actual / lsb);")
    lines.append("    }")
    lines.append("")
    lines.append("    // Decode unsigned value with LSB scaling.")
    lines.append("    static inline double decodeUnsigned(uint32_t encoded, double lsb) {")
    lines.append("        return static_cast<double>(encoded) * lsb;")
    lines.append("    }")
    lines.append("")
    lines.append("    // Decode signed value with LSB scaling.")
    lines.append("    static inline double decodeSigned(int32_t encoded, double lsb) {")
    lines.append("        return static_cast<double>(encoded) * lsb;")
    lines.append("    }")
    lines.append("")
    lines.append("    // Pack valid fields into a byte buffer.")
    lines.append(f"    static std::array<char, FRAME_SIZE> packFrame(const {frame_struct_name}& frame) {{")
    lines.append("        std::array<char, FRAME_SIZE> buffer{};")

    processed_groups = set()
    for meta in metas:
        spec = meta.spec
        if spec.field_type == "BIT":
            group = next((g for g in bit_groups if meta in g.fields), None)
            if group is None or group.member_name in processed_groups:
                continue
            processed_groups.add(group.member_name)
            if group.frame_offset is None:
                continue
            base_type = "uint8_t" if group.container_bits == 8 else "uint16_t" if group.container_bits == 16 else "uint32_t"
            lines.append(f"        {base_type} {group.member_name}Value = 0;")
            for bit_meta in group.fields:
                bit_spec = bit_meta.spec
                if not bit_spec.is_valid:
                    continue
                bit_len = max(bit_spec.length, 0)
                mask = "0xFFFFFFFFu" if bit_len == 32 else f"((1u << {bit_len}) - 1u)"
                _, field_name = split_group_name(bit_spec.name_en)
                field_name = normalize_identifier(field_name)
                value_expr = f"frame.{group.member_name}.{field_name}"
                lines.append(
                    f"        {group.member_name}Value |= (static_cast<{base_type}>({value_expr}) & {mask}) << {bit_meta.bit_offset};"
                )
            if group.container_bits == 8:
                lines.append(f"        buffer[{group.frame_offset}] = static_cast<char>({group.member_name}Value);")
            elif group.container_bits == 16:
                lines.append(f"        writeLe16(buffer.data() + {group.frame_offset}, {group.member_name}Value);")
            else:
                lines.append(f"        writeLe32(buffer.data() + {group.frame_offset}, {group.member_name}Value);")
            continue

        if not spec.is_valid:
            continue
        if meta.frame_offset is None:
            continue

        if meta.array_ref is not None:
            ref = meta.array_ref
            if ref.field:
                value_expr = f"frame.{ref.base}[{ref.index}].{normalize_identifier(ref.field)}"
            else:
                value_expr = f"frame.{ref.base}[{ref.index}]"
        else:
            value_expr = f"frame.{normalize_identifier(spec.name_en)}"

        if spec.field_type in ("CONST", "ANY", "U8", "S8"):
            lines.append(f"        buffer[{meta.frame_offset}] = static_cast<char>({value_expr});")
        elif spec.field_type in ("U16", "S16"):
            lines.append(f"        writeLe16(buffer.data() + {meta.frame_offset}, static_cast<uint16_t>({value_expr}));")
        elif spec.field_type in ("U32", "S32"):
            lines.append(f"        writeLe32(buffer.data() + {meta.frame_offset}, static_cast<uint32_t>({value_expr}));")
        elif spec.field_type in ("U8F", "U16F", "U32F"):
            lsb = spec.lsb if spec.lsb is not None else 1.0
            encoded = f"encodeUnsigned({value_expr}, {_format_float_literal(lsb)})"
            if spec.field_type == "U8F":
                lines.append(f"        buffer[{meta.frame_offset}] = static_cast<char>(static_cast<uint8_t>({encoded}));")
            elif spec.field_type == "U16F":
                lines.append(f"        writeLe16(buffer.data() + {meta.frame_offset}, static_cast<uint16_t>({encoded}));")
            else:
                lines.append(f"        writeLe32(buffer.data() + {meta.frame_offset}, static_cast<uint32_t>({encoded}));")
        elif spec.field_type in ("S8F", "S16F", "S32F"):
            lsb = spec.lsb if spec.lsb is not None else 1.0
            encoded = f"encodeSigned({value_expr}, {_format_float_literal(lsb)})"
            if spec.field_type == "S8F":
                lines.append(f"        buffer[{meta.frame_offset}] = static_cast<char>(static_cast<int8_t>({encoded}));")
            elif spec.field_type == "S16F":
                lines.append(f"        writeLe16(buffer.data() + {meta.frame_offset}, static_cast<uint16_t>({encoded}));")
            else:
                lines.append(f"        writeLe32(buffer.data() + {meta.frame_offset}, static_cast<uint32_t>({encoded}));")
        elif spec.field_type == "F32":
            lines.append("        {")
            lines.append(f"            float value = static_cast<float>({value_expr});")
            lines.append("            uint32_t raw = 0;")
            lines.append("            std::memcpy(&raw, &value, sizeof(raw));")
            lines.append(f"            writeLe32(buffer.data() + {meta.frame_offset}, raw);")
            lines.append("        }")
        elif spec.field_type == "F64":
            lines.append("        {")
            lines.append(f"            double value = static_cast<double>({value_expr});")
            lines.append("            uint64_t raw = 0;")
            lines.append("            std::memcpy(&raw, &value, sizeof(raw));")
            lines.append(f"            char* dst = buffer.data() + {meta.frame_offset};")
            lines.append("            dst[0] = static_cast<char>(raw & 0xFF);")
            lines.append("            dst[1] = static_cast<char>((raw >> 8) & 0xFF);")
            lines.append("            dst[2] = static_cast<char>((raw >> 16) & 0xFF);")
            lines.append("            dst[3] = static_cast<char>((raw >> 24) & 0xFF);")
            lines.append("            dst[4] = static_cast<char>((raw >> 32) & 0xFF);")
            lines.append("            dst[5] = static_cast<char>((raw >> 40) & 0xFF);")
            lines.append("            dst[6] = static_cast<char>((raw >> 48) & 0xFF);")
            lines.append("            dst[7] = static_cast<char>((raw >> 56) & 0xFF);")
            lines.append("        }")

    lines.append("        return buffer;")
    lines.append("    }")
    lines.append("")
    lines.append("    // Unpack valid fields from a byte buffer.")
    lines.append(f"    static bool unpackFrame(const char* rawData, size_t dataSize, {frame_struct_name}& frame) {{")
    lines.append("        if ((!rawData) || (dataSize < FRAME_SIZE)) {")
    lines.append("            return false;")
    lines.append("        }")

    processed_groups.clear()
    for meta in metas:
        spec = meta.spec
        if spec.field_type == "BIT":
            group = next((g for g in bit_groups if meta in g.fields), None)
            if group is None or group.member_name in processed_groups:
                continue
            processed_groups.add(group.member_name)
            if group.frame_offset is None:
                continue
            base_type = "uint8_t" if group.container_bits == 8 else "uint16_t" if group.container_bits == 16 else "uint32_t"
            if group.container_bits == 8:
                lines.append(f"        {base_type} {group.member_name}Value = static_cast<uint8_t>(rawData[{group.frame_offset}]);")
            elif group.container_bits == 16:
                lines.append(f"        {base_type} {group.member_name}Value = readLe16(rawData + {group.frame_offset});")
            else:
                lines.append(f"        {base_type} {group.member_name}Value = readLe32(rawData + {group.frame_offset});")
            for bit_meta in group.fields:
                bit_spec = bit_meta.spec
                if not bit_spec.is_valid:
                    continue
                bit_len = max(bit_spec.length, 0)
                mask = "0xFFFFFFFFu" if bit_len == 32 else f"((1u << {bit_len}) - 1u)"
                _, field_name = split_group_name(bit_spec.name_en)
                field_name = normalize_identifier(field_name)
                lines.append(
                    f"        frame.{group.member_name}.{field_name} = ({group.member_name}Value >> {bit_meta.bit_offset}) & {mask};"
                )
            continue

        if not spec.is_valid:
            continue
        if meta.frame_offset is None:
            continue
        if spec.field_type in ("CONST", "ANY", "U8"):
            value_expr = f"static_cast<uint8_t>(rawData[{meta.frame_offset}])"
        elif spec.field_type == "S8":
            value_expr = f"static_cast<int8_t>(rawData[{meta.frame_offset}])"
        elif spec.field_type == "U16":
            value_expr = f"readLe16(rawData + {meta.frame_offset})"
        elif spec.field_type == "S16":
            value_expr = f"static_cast<int16_t>(readLe16(rawData + {meta.frame_offset}))"
        elif spec.field_type == "U32":
            value_expr = f"readLe32(rawData + {meta.frame_offset})"
        elif spec.field_type == "S32":
            value_expr = f"static_cast<int32_t>(readLe32(rawData + {meta.frame_offset}))"
        elif spec.field_type in ("U8F", "U16F", "U32F"):
            lsb = spec.lsb if spec.lsb is not None else 1.0
            raw = "static_cast<uint8_t>(rawData[{0}])".format(meta.frame_offset) if spec.field_type == "U8F" else (
                f"readLe16(rawData + {meta.frame_offset})" if spec.field_type == "U16F" else f"readLe32(rawData + {meta.frame_offset})"
            )
            value_expr = f"decodeUnsigned({raw}, {_format_float_literal(lsb)})"
        elif spec.field_type in ("S8F", "S16F", "S32F"):
            lsb = spec.lsb if spec.lsb is not None else 1.0
            if spec.field_type == "S8F":
                raw = f"static_cast<int8_t>(rawData[{meta.frame_offset}])"
            elif spec.field_type == "S16F":
                raw = f"static_cast<int16_t>(readLe16(rawData + {meta.frame_offset}))"
            else:
                raw = f"static_cast<int32_t>(readLe32(rawData + {meta.frame_offset}))"
            value_expr = f"decodeSigned({raw}, {_format_float_literal(lsb)})"
        elif spec.field_type == "F32":
            lines.append("        {")
            lines.append(f"            uint32_t raw = readLe32(rawData + {meta.frame_offset});")
            lines.append("            float value = 0.0f;")
            lines.append("            std::memcpy(&value, &raw, sizeof(value));")
            value_expr = "value"
            assign_target = None
        elif spec.field_type == "F64":
            lines.append("        {")
            lines.append(f"            const char* src = rawData + {meta.frame_offset};")
            lines.append("            uint64_t raw = 0;")
            lines.append("            raw |= static_cast<uint64_t>(static_cast<uint8_t>(src[0]));")
            lines.append("            raw |= static_cast<uint64_t>(static_cast<uint8_t>(src[1])) << 8;")
            lines.append("            raw |= static_cast<uint64_t>(static_cast<uint8_t>(src[2])) << 16;")
            lines.append("            raw |= static_cast<uint64_t>(static_cast<uint8_t>(src[3])) << 24;")
            lines.append("            raw |= static_cast<uint64_t>(static_cast<uint8_t>(src[4])) << 32;")
            lines.append("            raw |= static_cast<uint64_t>(static_cast<uint8_t>(src[5])) << 40;")
            lines.append("            raw |= static_cast<uint64_t>(static_cast<uint8_t>(src[6])) << 48;")
            lines.append("            raw |= static_cast<uint64_t>(static_cast<uint8_t>(src[7])) << 56;")
            lines.append("            double value = 0.0;")
            lines.append("            std::memcpy(&value, &raw, sizeof(value));")
            value_expr = "value"
            assign_target = None
        else:
            value_expr = "0"

        if spec.field_type in ("F32", "F64"):
            if meta.array_ref is not None:
                ref = meta.array_ref
                if ref.field:
                    assign_target = f"frame.{ref.base}[{ref.index}].{normalize_identifier(ref.field)}"
                else:
                    assign_target = f"frame.{ref.base}[{ref.index}]"
            else:
                assign_target = f"frame.{normalize_identifier(spec.name_en)}"
            lines.append(f"            {assign_target} = {value_expr};")
            lines.append("        }")
            continue

        if meta.array_ref is not None:
            ref = meta.array_ref
            if ref.field:
                target = f"frame.{ref.base}[{ref.index}].{normalize_identifier(ref.field)}"
            else:
                target = f"frame.{ref.base}[{ref.index}]"
        else:
            target = f"frame.{normalize_identifier(spec.name_en)}"
        lines.append(f"        {target} = {value_expr};")

    lines.append("        return true;")
    lines.append("    }")
    lines.append("")
    lines.append("    // Build schema metadata for valid fields.")
    lines.append("    static MB_DDF::Tools::LogSchema buildSchema() {")
    lines.append("        MB_DDF::Tools::LogSchema schema;")
    lines.append("        using LFT = MB_DDF::Tools::LogFieldType;")

    array_offsets = {}
    for base, group in arrays.items():
        if group.is_struct:
            lines.append(f"        const uint32_t {base}_base = offset_of_member(&{frame_struct_name}::{base});")
            lines.append(f"        const uint32_t {base}_stride = static_cast<uint32_t>(sizeof({frame_struct_name}::{group.struct_name}));")
        else:
            lines.append(f"        const uint32_t {base}_base = offset_of_member(&{frame_struct_name}::{base});")
            lines.append(f"        const uint32_t {base}_stride = static_cast<uint32_t>(sizeof({group.element_type}));")
        array_offsets[base] = True

    bit_offsets = {}
    for group in bit_groups:
        if not any(meta.spec.is_valid for meta in group.fields):
            continue
        lines.append(f"        const uint32_t {group.member_name}_offset = offset_of_member(&{frame_struct_name}::{group.member_name});")
        bit_offsets[group.member_name] = True

    emitted_fields = set()
    emitted_array_fields = set()
    emitted_bit_fields = set()
    for meta in metas:
        spec = meta.spec
        if not spec.is_valid:
            continue
        if spec.field_type == "BIT":
            group = next((g for g in bit_groups if meta in g.fields), None)
            if group is None:
                continue
            key = f"{group.member_name}:{spec.name_en}"
            if key in emitted_bit_fields:
                continue
            emitted_bit_fields.add(key)
            storage_type = "UInt8" if group.container_bits == 8 else "UInt16" if group.container_bits == 16 else "UInt32"
            bit_len = max(spec.length, 0)
            output_type = "UInt8" if bit_len <= 8 else "UInt16" if bit_len <= 16 else "UInt32"
            name_cn = spec.name_cn or spec.name_en
            lines.append(
                f'        schema.addBitFieldAt("{_escape_cpp_string(name_cn)}", LFT::{storage_type}, {meta.bit_offset}, {bit_len}, {group.member_name}_offset, 0, LFT::{output_type});'
            )
            continue

        log_type = TYPE_SPECS.get(spec.field_type, {}).get("log_type", "UInt8")
        name_cn = spec.name_cn or spec.name_en
        if meta.array_ref is not None:
            ref = meta.array_ref
            base = ref.base
            if ref.field:
                key = f"{base}.{ref.field}"
                if key in emitted_array_fields:
                    continue
                emitted_array_fields.add(key)
                lines.append(
                    f'        schema.addFieldAt("{_escape_cpp_string(name_cn)}", LFT::{log_type}, {arrays[base].count}, {base}_base + offset_of_member(&{frame_struct_name}::{arrays[base].struct_name}::{normalize_identifier(ref.field)}), {base}_stride);'
                )
            else:
                if base in emitted_fields:
                    continue
                emitted_fields.add(base)
                lines.append(
                    f'        schema.addFieldAt("{_escape_cpp_string(name_cn)}", LFT::{log_type}, {arrays[base].count}, {base}_base, {base}_stride);'
                )
            continue

        field_name = normalize_identifier(spec.name_en)
        if field_name in emitted_fields:
            continue
        emitted_fields.add(field_name)
        lines.append(
            f'        schema.addFieldAt("{_escape_cpp_string(name_cn)}", LFT::{log_type}, 1, offset_of_member(&{frame_struct_name}::{field_name}));'
        )

    lines.append("        return schema;")
    lines.append("    }")
    lines.append("};")
    lines.append("")
    lines.append("} // namespace ProtocolModel")

    return "\n".join(lines)
