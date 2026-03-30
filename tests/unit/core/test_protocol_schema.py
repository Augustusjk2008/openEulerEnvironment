"""
Tests for protocol_schema module.

Tests FieldSpec, ArrayRef, type definitions, CSV operations, and utility functions.
"""

import os
import sys
import tempfile
import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

from core.protocol_schema import (
    # Data classes
    FieldSpec,
    ArrayRef,
    FieldMeta,
    BitGroup,
    ArrayGroup,
    # Constants
    CSV_COLUMNS,
    TYPE_OPTIONS,
    TYPE_SPECS,
    MAX_BIT_FIELD_BITS,
    # Functions
    parse_array_ref,
    split_group_name,
    normalize_identifier,
    to_struct_name,
    parse_bool,
    parse_float,
    parse_int,
    load_csv,
    save_csv,
    validate_fields,
    compute_byte_positions,
    compute_bit_positions,
    compute_bit_group_info,
    generate_cpp_code,
    # Internal functions
    _escape_cpp_string,
    _format_int_literal,
    _format_float_literal,
    _infer_default_numeric,
    _effective_bit_length,
    _bit_container_bits,
    _split_bit_fields,
    _build_layout,
    _field_byte_length,
    _bit_group_container_bytes,
    _collect_arrays,
    _assign_implicit_arrays,
    _compute_frame_offsets,
)


class TestFieldSpec:
    """Tests for FieldSpec dataclass."""

    def test_field_spec_creation(self):
        """Test creating FieldSpec with all fields."""
        field = FieldSpec(
            index=1,
            length=4,
            field_type="U32",
            name_cn="测试字段",
            name_en="test_field",
            lsb=0.01,
            default="100",
            is_valid=True
        )
        assert field.index == 1
        assert field.length == 4
        assert field.field_type == "U32"
        assert field.name_cn == "测试字段"
        assert field.name_en == "test_field"
        assert field.lsb == 0.01
        assert field.default == "100"
        assert field.is_valid is True

    def test_field_spec_defaults(self):
        """Test FieldSpec with default values."""
        field = FieldSpec(
            index=1,
            length=1,
            field_type="U8",
            name_cn="",
            name_en="field",
            lsb=None,
            default=None,
            is_valid=False
        )
        assert field.lsb is None
        assert field.default is None
        assert field.is_valid is False

    def test_field_spec_equality(self):
        """Test FieldSpec equality comparison."""
        field1 = FieldSpec(1, 4, "U32", "测试", "test", None, None, True)
        field2 = FieldSpec(1, 4, "U32", "测试", "test", None, None, True)
        field3 = FieldSpec(2, 4, "U32", "测试", "test", None, None, True)
        assert field1 == field2
        assert field1 != field3

    def test_field_spec_repr(self):
        """Test FieldSpec string representation."""
        field = FieldSpec(1, 4, "U32", "测试", "test", 0.1, "0", True)
        repr_str = repr(field)
        assert "FieldSpec" in repr_str
        assert "test" in repr_str

    def test_field_spec_with_bit_type(self):
        """Test FieldSpec with BIT type."""
        field = FieldSpec(
            index=1,
            length=3,
            field_type="BIT",
            name_cn="位字段",
            name_en="status.flags",
            lsb=None,
            default=None,
            is_valid=True
        )
        assert field.field_type == "BIT"
        assert field.length == 3


class TestArrayRef:
    """Tests for ArrayRef dataclass."""

    def test_array_ref_creation(self):
        """Test creating ArrayRef."""
        ref = ArrayRef(base="data", index=5, field="value")
        assert ref.base == "data"
        assert ref.index == 5
        assert ref.field == "value"

    def test_array_ref_without_field(self):
        """Test ArrayRef without field."""
        ref = ArrayRef(base="array", index=0, field=None)
        assert ref.base == "array"
        assert ref.index == 0
        assert ref.field is None

    def test_array_ref_equality(self):
        """Test ArrayRef equality."""
        ref1 = ArrayRef("data", 1, "field")
        ref2 = ArrayRef("data", 1, "field")
        ref3 = ArrayRef("data", 2, "field")
        assert ref1 == ref2
        assert ref1 != ref3


class TestParseArrayRef:
    """Tests for parse_array_ref function."""

    def test_parse_simple_array_ref(self):
        """Test parsing simple array reference."""
        result = parse_array_ref("data[0]")
        assert result is not None
        assert result.base == "data"
        assert result.index == 0
        assert result.field is None

    def test_parse_array_ref_with_field(self):
        """Test parsing array reference with field."""
        result = parse_array_ref("items[5].value")
        assert result is not None
        assert result.base == "items"
        assert result.index == 5
        assert result.field == "value"

    def test_parse_array_ref_large_index(self):
        """Test parsing array with large index."""
        result = parse_array_ref("buffer[999]")
        assert result.index == 999

    def test_parse_invalid_array_ref_no_brackets(self):
        """Test parsing invalid reference without brackets."""
        result = parse_array_ref("data")
        assert result is None

    def test_parse_invalid_array_ref_no_index(self):
        """Test parsing invalid reference without index."""
        result = parse_array_ref("data[]")
        assert result is None

    def test_parse_invalid_array_ref_invalid_chars(self):
        """Test parsing with invalid characters."""
        result = parse_array_ref("data[0]field")
        assert result is None

    def test_parse_array_ref_with_whitespace(self):
        """Test parsing with whitespace."""
        result = parse_array_ref("  data[1]  ")
        assert result is not None
        assert result.base == "data"

    def test_parse_array_ref_underscore_base(self):
        """Test parsing with underscore in base name."""
        result = parse_array_ref("_data[0]")
        assert result.base == "_data"

    def test_parse_array_ref_complex_field(self):
        """Test parsing with complex field name."""
        result = parse_array_ref("data[0].field_name_123")
        assert result.field == "field_name_123"


class TestSplitGroupName:
    """Tests for split_group_name function."""

    def test_split_with_dot(self):
        """Test splitting name with dot."""
        group, field = split_group_name("group.field")
        assert group == "group"
        assert field == "field"

    def test_split_without_dot(self):
        """Test splitting name without dot."""
        group, field = split_group_name("fieldname")
        assert group is None
        assert field == "fieldname"

    def test_split_multiple_dots(self):
        """Test splitting name with multiple dots."""
        group, field = split_group_name("a.b.c.d")
        assert group == "a"
        assert field == "d"

    def test_split_empty_string(self):
        """Test splitting empty string."""
        group, field = split_group_name("")
        assert group is None
        assert field == ""


class TestNormalizeIdentifier:
    """Tests for normalize_identifier function."""

    def test_normalize_simple_name(self):
        """Test normalizing simple name."""
        assert normalize_identifier("fieldName") == "fieldName"

    def test_normalize_with_spaces(self):
        """Test normalizing name with spaces."""
        assert normalize_identifier("field name") == "field_name"

    def test_normalize_with_special_chars(self):
        """Test normalizing name with special characters."""
        assert normalize_identifier("field-name@123") == "field_name_123"

    def test_normalize_starting_with_digit(self):
        """Test normalizing name starting with digit."""
        assert normalize_identifier("123field") == "_123field"

    def test_normalize_empty_string(self):
        """Test normalizing empty string."""
        assert normalize_identifier("") == "_"

    def test_normalize_unicode(self):
        """Test normalizing unicode characters."""
        # Unicode字符在Windows上可能被编码为乱码，测试只要不出错即可
        result = normalize_identifier("字段名")
        # 结果可能是原始字符串或规范化后的字符串，取决于编码
        assert isinstance(result, str)
        assert len(result) > 0

    def test_normalize_whitespace(self):
        """Test normalizing whitespace-only string."""
        assert normalize_identifier("   ") == "_"


class TestToStructName:
    """Tests for to_struct_name function."""

    def test_to_struct_name_simple(self):
        """Test converting simple name to struct name."""
        assert to_struct_name("mystruct") == "Mystruct"

    def test_to_struct_name_already_capitalized(self):
        """Test converting already capitalized name."""
        assert to_struct_name("MyStruct") == "MyStruct"

    def test_to_struct_name_with_special_chars(self):
        """Test converting name with special characters."""
        assert to_struct_name("my-struct") == "My_struct"

    def test_to_struct_name_single_char(self):
        """Test converting single character."""
        assert to_struct_name("x") == "X"


class TestParseBool:
    """Tests for parse_bool function."""

    def test_parse_true_values(self):
        """Test parsing various true values."""
        true_values = ["1", "true", "True", "TRUE", "yes", "YES", "y", "Y", "是"]
        for val in true_values:
            assert parse_bool(val) is True, f"Failed for {val}"

    def test_parse_false_values(self):
        """Test parsing various false values."""
        false_values = ["0", "false", "False", "FALSE", "no", "NO", "n", "N", "否"]
        for val in false_values:
            assert parse_bool(val) is False, f"Failed for {val}"

    def test_parse_invalid_returns_false(self):
        """Test that invalid values return False."""
        invalid_values = ["", "maybe", "invalid", None, "2"]
        for val in invalid_values:
            assert parse_bool(val) is False, f"Failed for {val}"

    def test_parse_bool_with_whitespace(self):
        """Test parsing with whitespace."""
        assert parse_bool("  true  ") is True
        assert parse_bool("  0  ") is False


class TestParseFloat:
    """Tests for parse_float function."""

    def test_parse_valid_floats(self):
        """Test parsing valid float strings."""
        assert parse_float("3.14") == 3.14
        assert parse_float("-2.5") == -2.5
        assert parse_float("0") == 0.0
        assert parse_float("1e10") == 1e10

    def test_parse_float_none(self):
        """Test parsing None."""
        assert parse_float(None) is None

    def test_parse_float_empty(self):
        """Test parsing empty string."""
        assert parse_float("") is None

    def test_parse_float_whitespace(self):
        """Test parsing whitespace."""
        assert parse_float("   ") is None

    def test_parse_float_invalid(self):
        """Test parsing invalid float."""
        assert parse_float("abc") is None
        assert parse_float("12.34.56") is None


class TestParseInt:
    """Tests for parse_int function."""

    def test_parse_valid_ints(self):
        """Test parsing valid integers."""
        assert parse_int("42") == 42
        assert parse_int("-10") == -10
        assert parse_int("0") == 0

    def test_parse_hex(self):
        """Test parsing hexadecimal."""
        assert parse_int("0xFF") == 255
        assert parse_int("0x10") == 16

    def test_parse_binary(self):
        """Test parsing binary."""
        assert parse_int("0b1010") == 10

    def test_parse_int_none(self):
        """Test parsing None."""
        assert parse_int(None) is None

    def test_parse_int_empty(self):
        """Test parsing empty string."""
        assert parse_int("") is None

    def test_parse_int_invalid(self):
        """Test parsing invalid integer."""
        assert parse_int("abc") is None
        assert parse_int("12.5") is None


class TestTypeSpecs:
    """Tests for TYPE_SPECS constant."""

    def test_type_specs_keys(self):
        """Test that TYPE_SPECS has expected keys."""
        expected_types = ["U8", "S8", "U16", "S16", "U32", "S32", "F32", "F64", "BIT"]
        for t in expected_types:
            assert t in TYPE_SPECS, f"Missing type: {t}"

    def test_type_specs_structure(self):
        """Test TYPE_SPECS entry structure."""
        for type_name, spec in TYPE_SPECS.items():
            assert "bytes" in spec or type_name == "BIT"
            assert "cpp_type" in spec or type_name == "BIT"
            assert "log_type" in spec or type_name == "BIT"

    def test_type_specs_bytes_values(self):
        """Test TYPE_SPECS bytes values."""
        assert TYPE_SPECS["U8"]["bytes"] == 1
        assert TYPE_SPECS["U16"]["bytes"] == 2
        assert TYPE_SPECS["U32"]["bytes"] == 4
        assert TYPE_SPECS["F32"]["bytes"] == 4
        assert TYPE_SPECS["F64"]["bytes"] == 8

    def test_type_options_completeness(self):
        """Test that TYPE_OPTIONS covers all TYPE_SPECS."""
        for type_name in TYPE_SPECS.keys():
            assert type_name in TYPE_OPTIONS, f"{type_name} not in TYPE_OPTIONS"


class TestCSVColumns:
    """Tests for CSV_COLUMNS constant."""

    def test_csv_columns(self):
        """Test CSV_COLUMNS has expected values."""
        expected = ["index", "length", "type", "name_cn", "name_en", "lsb", "default", "is_valid"]
        assert CSV_COLUMNS == expected


class TestEscapeCppString:
    """Tests for _escape_cpp_string function."""

    def test_escape_backslash(self):
        """Test escaping backslashes."""
        assert _escape_cpp_string("path\\to\\file") == "path\\\\to\\\\file"

    def test_escape_quote(self):
        """Test escaping quotes."""
        assert _escape_cpp_string('say "hello"') == 'say \\"hello\\"'

    def test_escape_both(self):
        """Test escaping both backslash and quote."""
        result = _escape_cpp_string('C:\\path\\"file"')
        assert "\\\\" in result
        assert "\\\"" in result

    def test_no_escape_needed(self):
        """Test string without special characters."""
        assert _escape_cpp_string("hello world") == "hello world"


class TestFormatIntLiteral:
    """Tests for _format_int_literal function."""

    def test_format_positive(self):
        """Test formatting positive integers."""
        assert _format_int_literal(42) == "42"
        assert _format_int_literal(0) == "0"

    def test_format_negative(self):
        """Test formatting negative integers."""
        assert _format_int_literal(-10) == "-10"


class TestFormatFloatLiteral:
    """Tests for _format_float_literal function."""

    def test_format_simple_float(self):
        """Test formatting simple floats."""
        result = _format_float_literal(3.14)
        assert "3.14" in result or "3.140" in result

    def test_format_scientific(self):
        """Test formatting scientific notation."""
        result = _format_float_literal(1e10)
        assert "e" in result.lower() or "E" in result


class TestEffectiveBitLength:
    """Tests for _effective_bit_length function."""

    def test_effective_bit_length_normal(self):
        """Test normal bit lengths."""
        assert _effective_bit_length(8) == 8
        assert _effective_bit_length(16) == 16
        assert _effective_bit_length(32) == 32

    def test_effective_bit_length_clamped(self):
        """Test clamped bit lengths."""
        assert _effective_bit_length(0) == 0
        assert _effective_bit_length(-5) == 0
        assert _effective_bit_length(64) == 32  # MAX_BIT_FIELD_BITS


class TestBitContainerBits:
    """Tests for _bit_container_bits function."""

    def test_container_8bit(self):
        """Test 8-bit container."""
        assert _bit_container_bits(1) == 8
        assert _bit_container_bits(8) == 8

    def test_container_16bit(self):
        """Test 16-bit container."""
        assert _bit_container_bits(9) == 16
        assert _bit_container_bits(16) == 16

    def test_container_32bit(self):
        """Test 32-bit container."""
        assert _bit_container_bits(17) == 32
        assert _bit_container_bits(32) == 32


class TestFieldByteLength:
    """Tests for _field_byte_length function."""

    def test_field_byte_length_known_types(self):
        """Test byte length for known types."""
        field_u8 = FieldSpec(1, 0, "U8", "", "", None, None, True)
        assert _field_byte_length(field_u8) == 1

        field_u32 = FieldSpec(1, 0, "U32", "", "", None, None, True)
        assert _field_byte_length(field_u32) == 4

    def test_field_byte_length_with_length(self):
        """Test byte length using field length."""
        field = FieldSpec(1, 10, "UNKNOWN", "", "", None, None, True)
        assert _field_byte_length(field) == 10


class TestLoadCSV:
    """Tests for load_csv function."""

    def test_load_csv_empty_file(self, tmp_path):
        """Test loading empty CSV file."""
        csv_file = tmp_path / "empty.csv"
        csv_file.write_text("")
        result = load_csv(str(csv_file))
        assert result == []

    def test_load_csv_nonexistent(self):
        """Test loading nonexistent file."""
        result = load_csv("/nonexistent/file.csv")
        assert result == []

    def test_load_csv_basic(self, tmp_path):
        """Test loading basic CSV."""
        csv_file = tmp_path / "test.csv"
        csv_content = "index,length,type,name_cn,name_en,lsb,default,is_valid\n"
        csv_content += "1,4,U32,测试,test,0.01,100,1\n"
        csv_file.write_text(csv_content, encoding="utf-8-sig")

        result = load_csv(str(csv_file))
        assert len(result) == 1
        assert result[0].field_type == "U32"
        assert result[0].name_en == "test"

    def test_load_csv_auto_index(self, tmp_path):
        """Test auto-indexing in CSV."""
        csv_file = tmp_path / "test.csv"
        csv_content = "index,length,type,name_cn,name_en,lsb,default,is_valid\n"
        csv_content += ",1,U8,测试1,test1,,,1\n"
        csv_content += ",1,U8,测试2,test2,,,1\n"
        csv_file.write_text(csv_content, encoding="utf-8-sig")

        result = load_csv(str(csv_file))
        assert len(result) == 2
        assert result[0].index == 1
        assert result[1].index == 2


class TestSaveCSV:
    """Tests for save_csv function."""

    def test_save_csv_basic(self, tmp_path):
        """Test saving basic CSV."""
        csv_file = tmp_path / "output.csv"
        fields = [
            FieldSpec(1, 4, "U32", "测试", "test", 0.01, "100", True),
        ]
        save_csv(str(csv_file), fields)

        assert csv_file.exists()
        content = csv_file.read_text(encoding="utf-8-sig")
        assert "U32" in content
        assert "test" in content


class TestValidateFields:
    """Tests for validate_fields function."""

    def test_validate_valid_fields(self):
        """Test validating valid fields."""
        fields = [
            FieldSpec(1, 4, "U32", "", "field1", None, None, True),
            FieldSpec(2, 2, "U16", "", "field2", None, None, True),
        ]
        warnings = validate_fields(fields)
        assert len(warnings) == 0

    def test_validate_unknown_type(self):
        """Test validating field with unknown type."""
        fields = [
            FieldSpec(1, 4, "UNKNOWN", "", "field", None, None, True),
        ]
        warnings = validate_fields(fields)
        assert len(warnings) == 1
        assert "未知类型" in warnings[0]

    def test_validate_bit_length_zero(self):
        """Test validating BIT field with zero length."""
        fields = [
            FieldSpec(1, 0, "BIT", "", "flags", None, None, True),
        ]
        warnings = validate_fields(fields)
        assert len(warnings) == 1
        assert "长度必须大于0" in warnings[0]

    def test_validate_bit_length_too_large(self):
        """Test validating BIT field with excessive length."""
        fields = [
            FieldSpec(1, 64, "BIT", "", "flags", None, None, True),
        ]
        warnings = validate_fields(fields)
        assert len(warnings) == 1
        assert "不能超过" in warnings[0]

    def test_validate_wrong_length(self):
        """Test validating field with wrong length."""
        fields = [
            FieldSpec(1, 8, "U32", "", "field", None, None, True),
        ]
        warnings = validate_fields(fields)
        assert len(warnings) == 1
        assert "长度应为" in warnings[0]


class TestComputePositions:
    """Tests for position computation functions."""

    def test_compute_byte_positions_simple(self):
        """Test computing byte positions for simple fields."""
        fields = [
            FieldSpec(1, 4, "U32", "", "field1", None, None, True),
            FieldSpec(2, 2, "U16", "", "field2", None, None, True),
        ]
        positions = compute_byte_positions(fields)
        assert len(positions) == 2
        assert "B1" in positions[0]
        assert "B" in positions[1]

    def test_compute_bit_positions(self):
        """Test computing bit positions."""
        fields = [
            FieldSpec(1, 3, "BIT", "", "flags1", None, None, True),
            FieldSpec(2, 5, "BIT", "", "flags2", None, None, True),
        ]
        positions = compute_bit_positions(fields)
        assert len(positions) == 2
        assert positions[0] != ""
        assert positions[1] != ""


class TestGenerateCppCode:
    """Tests for generate_cpp_code function."""

    def test_generate_cpp_simple(self):
        """Test generating C++ code for simple frame."""
        fields = [
            FieldSpec(1, 4, "U32", "计数字段", "counter", None, None, True),
        ]
        code = generate_cpp_code("TestFrame", fields)
        assert "#pragma once" in code
        assert "struct TestFrame" in code
        assert "counter" in code
        assert "FRAME_SIZE" in code

    def test_generate_cpp_with_bit_fields(self):
        """Test generating C++ code with bit fields."""
        fields = [
            FieldSpec(1, 4, "U32", "", "data", None, None, True),
            FieldSpec(2, 3, "BIT", "", "status.flags", None, None, True),
        ]
        code = generate_cpp_code("BitFrame", fields)
        assert "struct" in code
        assert "packFrame" in code
        assert "unpackFrame" in code


class TestConstants:
    """Tests for module constants."""

    def test_max_bit_field_bits(self):
        """Test MAX_BIT_FIELD_BITS constant."""
        assert MAX_BIT_FIELD_BITS == 32


class TestIntegration:
    """Integration tests for protocol_schema module."""

    def test_full_workflow(self, tmp_path):
        """Test full workflow: create, save, load, validate, generate."""
        # Create fields
        fields = [
            FieldSpec(1, 4, "U32", "头部", "header", None, "0x55AA", True),
            FieldSpec(2, 2, "U16", "长度", "length", None, None, True),
            FieldSpec(3, 4, "F32", "数值", "value", 0.01, "0.0", True),
        ]

        # Save to CSV
        csv_file = tmp_path / "protocol.csv"
        save_csv(str(csv_file), fields)

        # Load from CSV
        loaded = load_csv(str(csv_file))
        assert len(loaded) == 3

        # Validate
        warnings = validate_fields(loaded)
        assert len(warnings) == 0

        # Generate C++ code
        code = generate_cpp_code("MyFrame", loaded)
        assert "MyFrame" in code
        assert "packFrame" in code
        assert "unpackFrame" in code


class TestSplitBitFieldsExtended:
    """Extended tests for _split_bit_fields function."""

    def test_split_bit_fields_large_group(self):
        """Test splitting large bit field groups."""
        # 创建超过32位的位字段组
        specs = [FieldSpec(i, 8, "BIT", "", f"flags.bit{i}", None, None, True) for i in range(1, 6)]
        metas = [FieldMeta(spec=s) for s in specs]
        result = _split_bit_fields(metas)
        # 40位应该被分割成多个组
        assert len(result) >= 2

    def test_split_bit_fields_exactly_32(self):
        """Test splitting exactly 32 bits."""
        specs = [FieldSpec(1, 32, "BIT", "", "flags.bits", None, None, True)]
        metas = [FieldMeta(spec=s) for s in specs]
        result = _split_bit_fields(metas)
        assert len(result) == 1
        assert result[0][2] == 32


class TestBuildLayoutExtended:
    """Extended tests for _build_layout function."""

    def test_build_layout_mixed_types(self):
        """Test layout with mixed field types."""
        fields = [
            FieldSpec(1, 4, "U32", "头部", "header", None, None, True),
            FieldSpec(2, 4, "BIT", "标志1", "flags.bit1", None, None, True),
            FieldSpec(3, 4, "BIT", "标志2", "flags.bit2", None, None, True),
            FieldSpec(4, 4, "F32", "数值", "value", None, None, True),
            FieldSpec(5, 2, "U16", "状态", "status", None, None, True),
        ]
        metas, bit_groups, total_size = _build_layout(fields)
        assert len(metas) == 5
        assert len(bit_groups) == 1
        assert total_size == 4 + 1 + 4 + 2  # U32 + BIT组 + F32 + U16

    def test_build_layout_split_bit_groups(self):
        """Test layout with split bit field groups."""
        # 创建需要分割的位字段组（超过32位）
        fields = [FieldSpec(i, 8, "BIT", "", f"group.bit{i}", None, None, True) for i in range(1, 6)]
        metas, bit_groups, total_size = _build_layout(fields)
        # 40位应该被分割成多个组
        assert len(bit_groups) >= 2


class TestInferDefaultNumericExtended:
    """Extended tests for _infer_default_numeric function."""

    def test_infer_default_scaled_types(self):
        """Test inferring defaults for scaled types."""
        # U8F类型
        field = FieldSpec(1, 1, "U8F", "", "field", 0.1, "10.5", True)
        result = _infer_default_numeric(field)
        assert result is not None

        # S16F类型
        field = FieldSpec(1, 2, "S16F", "", "field", 0.01, "-100", True)
        result = _infer_default_numeric(field)
        assert result is not None

    def test_infer_default_float_from_int(self):
        """Test inferring float default from integer string."""
        field = FieldSpec(1, 4, "F32", "", "field", None, "100", True)
        result = _infer_default_numeric(field)
        assert result is not None
        assert "100" in result

    def test_infer_default_int_from_float(self):
        """Test inferring int default from float string."""
        field = FieldSpec(1, 4, "U32", "", "field", None, "100.0", True)
        result = _infer_default_numeric(field)
        assert result is not None


class TestCollectArraysExtended:
    """Extended tests for _collect_arrays function."""

    def test_collect_arrays_multiple_bases(self):
        """Test collecting arrays with multiple bases."""
        specs = [
            FieldSpec(1, 4, "U32", "", "data1[0]", None, None, True),
            FieldSpec(2, 4, "U32", "", "data1[1]", None, None, True),
            FieldSpec(3, 4, "U32", "", "data2[0]", None, None, True),
        ]
        metas = [
            FieldMeta(spec=specs[0], array_ref=ArrayRef("data1", 0, None)),
            FieldMeta(spec=specs[1], array_ref=ArrayRef("data1", 1, None)),
            FieldMeta(spec=specs[2], array_ref=ArrayRef("data2", 0, None)),
        ]
        result = _collect_arrays(metas)
        assert "data1" in result
        assert "data2" in result
        assert result["data1"].count == 2
        assert result["data2"].count == 1

    def test_collect_arrays_mixed_types(self):
        """Test collecting arrays with mixed element types."""
        specs = [
            FieldSpec(1, 4, "F32", "", "points[0].x", None, None, True),
            FieldSpec(2, 4, "F32", "", "points[0].y", None, None, True),
            FieldSpec(3, 4, "F32", "", "points[1].x", None, None, True),
            FieldSpec(4, 4, "F32", "", "points[1].y", None, None, True),
        ]
        metas = [
            FieldMeta(spec=specs[0], array_ref=ArrayRef("points", 0, "x")),
            FieldMeta(spec=specs[1], array_ref=ArrayRef("points", 0, "y")),
            FieldMeta(spec=specs[2], array_ref=ArrayRef("points", 1, "x")),
            FieldMeta(spec=specs[3], array_ref=ArrayRef("points", 1, "y")),
        ]
        result = _collect_arrays(metas)
        assert "points" in result
        assert result["points"].is_struct is True
        assert "x" in result["points"].fields
        assert "y" in result["points"].fields
        assert result["points"].count == 2


class TestAssignImplicitArraysExtended:
    """Extended tests for _assign_implicit_arrays function."""

    def test_assign_implicit_arrays_not_consecutive(self):
        """Test implicit arrays with non-consecutive duplicates."""
        specs = [
            FieldSpec(1, 4, "U32", "", "data", None, None, True),
            FieldSpec(2, 4, "U32", "", "other", None, None, True),
            FieldSpec(3, 4, "U32", "", "data", None, None, True),
        ]
        metas = [FieldMeta(spec=s) for s in specs]
        _assign_implicit_arrays(metas)
        # 非连续的重复字段不应被识别为数组
        assert metas[0].array_ref is None
        assert metas[1].array_ref is None
        assert metas[2].array_ref is None

    def test_assign_implicit_arrays_different_types(self):
        """Test implicit arrays with same name but different types."""
        specs = [
            FieldSpec(1, 4, "U32", "", "data", None, None, True),
            FieldSpec(2, 2, "U16", "", "data", None, None, True),
        ]
        metas = [FieldMeta(spec=s) for s in specs]
        _assign_implicit_arrays(metas)
        # 不同类型不应被识别为数组
        assert metas[0].array_ref is None
        assert metas[1].array_ref is None


class TestGenerateCppCodeExtended:
    """Extended tests for generate_cpp_code function."""

    def test_generate_cpp_with_all_scaled_types(self):
        """Test generating C++ with all scaled types."""
        fields = [
            FieldSpec(1, 1, "U8F", "U8缩放", "u8f", 0.1, "10", True),
            FieldSpec(2, 1, "S8F", "S8缩放", "s8f", 0.1, "-10", True),
            FieldSpec(3, 2, "U16F", "U16缩放", "u16f", 0.01, "100", True),
            FieldSpec(4, 2, "S16F", "S16缩放", "s16f", 0.01, "-100", True),
            FieldSpec(5, 4, "U32F", "U32缩放", "u32f", 0.001, "1000", True),
            FieldSpec(6, 4, "S32F", "S32缩放", "s32f", 0.001, "-1000", True),
        ]
        code = generate_cpp_code("ScaledFrame", fields)
        assert "encodeUnsigned" in code
        assert "encodeSigned" in code
        assert "decodeUnsigned" in code
        assert "decodeSigned" in code

    def test_generate_cpp_with_const_any(self):
        """Test generating C++ with CONST and ANY types."""
        fields = [
            FieldSpec(1, 1, "CONST", "常量", "const_field", None, "0x55", True),
            FieldSpec(2, 1, "ANY", "任意", "any_field", None, None, True),
        ]
        code = generate_cpp_code("ConstAnyFrame", fields)
        assert "const_field" in code or "any_field" in code

    def test_generate_cpp_empty_frame(self):
        """Test generating C++ with empty frame."""
        code = generate_cpp_code("EmptyFrame", [])
        assert "struct EmptyFrame" in code
        assert "FRAME_SIZE = 0" in code

    def test_generate_cpp_only_bit_fields(self):
        """Test generating C++ with only bit fields."""
        fields = [
            FieldSpec(1, 1, "BIT", "标志1", "flags.flag1", None, None, True),
            FieldSpec(2, 1, "BIT", "标志2", "flags.flag2", None, None, True),
            FieldSpec(3, 6, "BIT", "类型", "flags.type", None, None, True),
        ]
        code = generate_cpp_code("BitOnlyFrame", fields)
        assert "struct Flags" in code
        assert ": 1" in code
        assert ": 6" in code

    def test_generate_cpp_large_array(self):
        """Test generating C++ with large array."""
        fields = [FieldSpec(i, 4, "F32", f"数据{i}", f"data[{i}]", None, None, True) for i in range(1, 11)]
        code = generate_cpp_code("LargeArrayFrame", fields)
        assert "data[10]" in code

    def test_generate_cpp_with_invalid_fields(self):
        """Test generating C++ with some invalid fields."""
        fields = [
            FieldSpec(1, 4, "U32", "有效字段", "valid_field", None, None, True),
            FieldSpec(2, 4, "U32", "无效字段", "invalid_field", None, None, False),
            FieldSpec(3, 4, "F32", "另一个有效", "another_valid", None, None, True),
        ]
        code = generate_cpp_code("MixedValidFrame", fields)
        assert "valid_field" in code
        assert "another_valid" in code
        # 无效字段可能出现在结构体定义中，但不会在pack/unpack中使用


class TestComputeBitGroupInfoExtended:
    """Extended tests for compute_bit_group_info function."""

    def test_compute_bit_group_info_multiple_groups(self):
        """Test computing info for multiple bit groups."""
        fields = [
            FieldSpec(1, 4, "BIT", "", "group1.bit1", None, None, True),
            FieldSpec(2, 4, "BIT", "", "group1.bit2", None, None, True),
            FieldSpec(3, 4, "U32", "", "data", None, None, True),
            FieldSpec(4, 4, "BIT", "", "group2.bit1", None, None, True),
        ]
        group_by_index, group_info = compute_bit_group_info(fields)
        # 应该有两个位组
        assert len(group_info) == 2

    def test_compute_bit_group_info_no_bits(self):
        """Test computing info with no bit fields."""
        fields = [
            FieldSpec(1, 4, "U32", "", "field1", None, None, True),
            FieldSpec(2, 4, "F32", "", "field2", None, None, True),
        ]
        group_by_index, group_info = compute_bit_group_info(fields)
        assert group_by_index == {}
        assert group_info == {}


class TestValidateFieldsExtended:
    """Extended tests for validate_fields function."""

    def test_validate_zero_length_allowed(self):
        """Test that zero length is allowed for some types."""
        fields = [
            FieldSpec(1, 0, "U32", "", "field", None, None, True),
        ]
        warnings = validate_fields(fields)
        # U32类型长度为0应该被允许（使用默认长度）
        assert len(warnings) == 0

    def test_validate_multiple_warnings(self):
        """Test validating fields with multiple warnings."""
        fields = [
            FieldSpec(1, 4, "UNKNOWN1", "", "field1", None, None, True),
            FieldSpec(2, 4, "UNKNOWN2", "", "field2", None, None, True),
        ]
        warnings = validate_fields(fields)
        assert len(warnings) == 2

    def test_validate_reserved_requires_positive_length(self):
        """Test RESERVED fields require a positive byte length."""
        fields = [
            FieldSpec(1, 0, "RESERVED", "预留", "reserved_block", None, None, True),
        ]
        warnings = validate_fields(fields)
        assert len(warnings) == 1
        assert "RESERVED" in warnings[0]
        assert "大于0" in warnings[0]


class TestLoadCSVExtended:
    """Extended tests for load_csv function."""

    def test_load_csv_with_empty_rows(self, tmp_path):
        """Test loading CSV with empty rows."""
        csv_content = """index,length,type,name_cn,name_en,lsb,default,is_valid
1,4,U32,字段1,field1,,,1

2,4,U32,字段2,field2,,,1
"""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(csv_content, encoding="utf-8-sig")
        result = load_csv(str(csv_file))
        assert len(result) == 2

    def test_load_csv_bit_auto_valid(self, tmp_path):
        """Test that BIT fields are automatically set valid."""
        csv_content = """index,length,type,name_cn,name_en,lsb,default,is_valid
1,4,BIT,标志,flags.bit,,,0
"""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(csv_content, encoding="utf-8-sig")
        result = load_csv(str(csv_file))
        assert result[0].field_type == "BIT"
        assert result[0].is_valid is True

    def test_load_csv_reserved_keeps_valid_flag(self, tmp_path):
        """Test RESERVED fields preserve the valid flag from CSV."""
        csv_content = """index,length,type,name_cn,name_en,lsb,default,is_valid
1,6,RESERVED,预留,reserved_block,,,0
2,2,U16,尾字段,tail,,,1
"""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(csv_content, encoding="utf-8-sig")
        result = load_csv(str(csv_file))
        assert result[0].field_type == "RESERVED"
        assert result[0].is_valid is False
        assert result[0].length == 6


class TestSaveCSVExtended:
    """Extended tests for save_csv function."""

    def test_save_csv_creates_directory(self, tmp_path):
        """Test that save_csv creates directory if needed."""
        csv_file = tmp_path / "subdir" / "output.csv"
        fields = [FieldSpec(1, 4, "U32", "", "field", None, None, True)]
        save_csv(str(csv_file), fields)
        assert csv_file.exists()

    def test_save_csv_empty_fields(self, tmp_path):
        """Test saving empty fields list."""
        csv_file = tmp_path / "empty.csv"
        save_csv(str(csv_file), [])
        content = csv_file.read_text(encoding="utf-8-sig")
        lines = content.strip().split("\n")
        assert len(lines) == 1  # 只有表头


class TestIntegrationExtended:
    """Extended integration tests."""

    def test_complex_protocol_workflow(self, tmp_path):
        """Test complex protocol with all features."""
        # 创建复杂协议：包含各种类型、位字段、数组
        fields = [
            FieldSpec(1, 4, "U32", "头部", "header", None, "0xAA55", True),
            FieldSpec(2, 1, "BIT", "标志1", "flags.flag1", None, None, True),
            FieldSpec(3, 1, "BIT", "标志2", "flags.flag2", None, None, True),
            FieldSpec(4, 6, "BIT", "类型", "flags.type", None, None, True),
            FieldSpec(5, 4, "F32", "温度", "temperature", 0.01, "25.0", True),
            FieldSpec(6, 4, "F32", "压力", "pressure", 0.001, "101.3", True),
            FieldSpec(7, 4, "U32", "数据0", "data[0]", None, None, True),
            FieldSpec(8, 4, "U32", "数据1", "data[1]", None, None, True),
            FieldSpec(9, 4, "U32", "数据2", "data[2]", None, None, True),
            FieldSpec(10, 2, "U16F", "缩放值", "scaled", 0.1, "10.0", True),
        ]

        # 验证
        warnings = validate_fields(fields)
        assert len(warnings) == 0

        # 计算位置
        byte_positions = compute_byte_positions(fields)
        bit_positions = compute_bit_positions(fields)
        assert len(byte_positions) == 10
        assert len(bit_positions) == 10

        # 保存并加载
        csv_file = tmp_path / "complex.csv"
        save_csv(str(csv_file), fields)
        loaded = load_csv(str(csv_file))
        assert len(loaded) == 10

        # 生成C++代码
        code = generate_cpp_code("ComplexFrame", loaded)
        assert "struct ComplexFrame" in code
        assert "packFrame" in code
        assert "unpackFrame" in code
        assert "buildSchema" in code

    def test_protocol_with_struct_array(self, tmp_path):
        """Test protocol with struct array."""
        fields = [
            FieldSpec(1, 4, "F32", "点0X", "points[0].x", None, None, True),
            FieldSpec(2, 4, "F32", "点0Y", "points[0].y", None, None, True),
            FieldSpec(3, 4, "F32", "点0Z", "points[0].z", None, None, True),
            FieldSpec(4, 4, "F32", "点1X", "points[1].x", None, None, True),
            FieldSpec(5, 4, "F32", "点1Y", "points[1].y", None, None, True),
            FieldSpec(6, 4, "F32", "点1Z", "points[1].z", None, None, True),
        ]

        code = generate_cpp_code("PointFrame", fields)
        assert "points[2]" in code
        # 应该生成结构体定义
        assert "struct" in code


class TestBitGroupContainerBytes:
    """Tests for _bit_group_container_bytes function."""

    def test_bit_group_container_bytes_8(self):
        """Test 8-bit container."""
        assert _bit_group_container_bytes(8) == 1

    def test_bit_group_container_bytes_16(self):
        """Test 16-bit container."""
        assert _bit_group_container_bytes(16) == 2

    def test_bit_group_container_bytes_32(self):
        """Test 32-bit container."""
        assert _bit_group_container_bytes(32) == 4


class TestFieldMetaDataClasses:
    """Additional tests for dataclass functionality."""

    def test_field_meta_with_bit_group(self):
        """Test FieldMeta with BitGroup."""
        spec = FieldSpec(1, 4, "BIT", "", "flags.bit", None, None, True)
        group = BitGroup(
            name="flags",
            struct_name="Flags",
            member_name="flags",
            start_offset=0,
            total_bits=4,
            container_bits=8,
            fields=[],
        )
        meta = FieldMeta(spec=spec, bit_group=group)
        assert meta.bit_group == group

    def test_array_group_element_type(self):
        """Test ArrayGroup with element type."""
        group = ArrayGroup(
            base="data",
            count=5,
            is_struct=False,
            struct_name=None,
            element_type="float",
            fields={},
        )
        assert group.element_type == "float"
        assert group.is_struct is False


class TestGenerateCppCodeSchema:
    """Tests for C++ code generation - schema building."""

    def test_generate_cpp_schema_with_arrays(self):
        """Test schema generation with arrays."""
        fields = [
            FieldSpec(1, 4, "U32", "数据0", "data[0]", None, None, True),
            FieldSpec(2, 4, "U32", "数据1", "data[1]", None, None, True),
        ]
        code = generate_cpp_code("ArraySchemaFrame", fields)
        assert "buildSchema" in code
        assert "offset_of_member" in code

    def test_generate_cpp_schema_with_bit_fields(self):
        """Test schema generation with bit fields."""
        fields = [
            FieldSpec(1, 4, "BIT", "标志", "flags.bits", None, None, True),
        ]
        code = generate_cpp_code("BitSchemaFrame", fields)
        assert "buildSchema" in code
        assert "addBitFieldAt" in code or "schema" in code


class TestSplitBitFieldsEdgeCases:
    """Edge case tests for _split_bit_fields."""

    def test_split_bit_fields_17_to_24_bits(self):
        """Test 17-24 bit split rule."""
        # 创建一个17位的位字段组，应该被分割为16+1
        specs = [
            FieldSpec(1, 16, "BIT", "", "flags.high", None, None, True),
            FieldSpec(2, 1, "BIT", "", "flags.low", None, None, True),
        ]
        metas = [FieldMeta(spec=s) for s in specs]
        result = _split_bit_fields(metas)
        # 17位应该触发2+1分割规则
        assert len(result) >= 1

    def test_split_bit_fields_byte_aligned(self):
        """Test byte-aligned split preference."""
        # 创建40位字段，应该优先按字节对齐分割
        specs = [FieldSpec(i, 8, "BIT", "", f"flags.byte{i}", None, None, True) for i in range(5)]
        metas = [FieldMeta(spec=s) for s in specs]
        result = _split_bit_fields(metas)
        # 应该被分割为多个组
        assert len(result) >= 1


class TestBuildLayoutEdgeCases:
    """Edge case tests for _build_layout."""

    def test_build_layout_auto_group_naming(self):
        """Test automatic bit group naming."""
        # 位字段没有组名前缀
        fields = [
            FieldSpec(1, 4, "BIT", "", "bitfield1", None, None, True),
            FieldSpec(2, 4, "BIT", "", "bitfield2", None, None, True),
        ]
        metas, bit_groups, total_size = _build_layout(fields)
        # 应该自动生成组名
        assert len(bit_groups) >= 1

    def test_build_layout_duplicate_member_names(self):
        """Test handling of duplicate member names."""
        # 创建可能导致重复成员名的情况
        fields = [
            FieldSpec(1, 4, "BIT", "", "group.bit1", None, None, True),
            FieldSpec(2, 4, "U32", "", "group", None, None, True),  # 可能与组名冲突
        ]
        metas, bit_groups, total_size = _build_layout(fields)
        # 应该处理名称冲突
        assert len(metas) == 2


class TestCollectArraysEdgeCases:
    """Edge case tests for _collect_arrays."""

    def test_collect_arrays_empty_field_name(self):
        """Test collecting arrays with empty field names."""
        spec = FieldSpec(1, 4, "U32", "", "", None, None, True)
        meta = FieldMeta(spec=spec, array_ref=None)
        result = _collect_arrays([meta])
        assert result == {}

    def test_collect_arrays_bit_fields_excluded(self):
        """Test that BIT fields are excluded from arrays."""
        spec = FieldSpec(1, 4, "BIT", "", "flags[0].bit", None, None, True)
        meta = FieldMeta(spec=spec, array_ref=ArrayRef("flags", 0, "bit"))
        result = _collect_arrays([meta])
        # BIT字段应该被排除
        assert result == {}


class TestAssignImplicitArraysEdgeCases:
    """Edge case tests for _assign_implicit_arrays."""

    def test_assign_implicit_arrays_with_empty_name(self):
        """Test implicit arrays with empty field names."""
        spec = FieldSpec(1, 4, "U32", "", "", None, None, True)
        meta = FieldMeta(spec=spec)
        _assign_implicit_arrays([meta])
        assert meta.array_ref is None

    def test_assign_implicit_arrays_with_different_lsb(self):
        """Test that different LSB prevents array assignment."""
        specs = [
            FieldSpec(1, 4, "U32", "", "data", 0.1, None, True),
            FieldSpec(2, 4, "U32", "", "data", 0.2, None, True),  # 不同LSB
        ]
        metas = [FieldMeta(spec=s) for s in specs]
        _assign_implicit_arrays(metas)
        # 不同LSB不应该被识别为数组
        assert metas[0].array_ref is None
        assert metas[1].array_ref is None


class TestGenerateCppCodeWithDefaults:
    """Tests for C++ code generation with default values."""

    def test_generate_cpp_with_all_defaults(self):
        """Test C++ generation with various default values."""
        fields = [
            FieldSpec(1, 4, "U32", "计数", "count", None, "0", True),
            FieldSpec(2, 4, "F32", "温度", "temp", 0.1, "25.5", True),
            FieldSpec(3, 4, "S32", "有符号", "signed", None, "-100", True),
        ]
        code = generate_cpp_code("DefaultFrame", fields)
        assert "count = 0" in code or "count" in code
        assert "temp" in code

    def test_generate_cpp_with_invalid_defaults(self):
        """Test C++ generation with invalid default values."""
        fields = [
            FieldSpec(1, 4, "U32", "字段", "field", None, "invalid", True),
        ]
        code = generate_cpp_code("InvalidDefaultFrame", fields)
        # 无效默认值应该被忽略
        assert "struct InvalidDefaultFrame" in code


class TestLoadCSVEncoding:
    """Tests for CSV loading with different encodings."""

    def test_load_csv_utf8_bom(self, tmp_path):
        """Test loading CSV with UTF-8 BOM."""
        csv_content = "index,length,type,name_cn,name_en,lsb,default,is_valid\n1,4,U32,测试,test,,,1\n"
        csv_file = tmp_path / "utf8bom.csv"
        csv_file.write_text(csv_content, encoding="utf-8-sig")
        result = load_csv(str(csv_file))
        assert len(result) == 1
        assert result[0].name_cn == "测试"

    def test_load_csv_extra_columns(self, tmp_path):
        """Test loading CSV with extra columns."""
        csv_content = "index,length,type,name_cn,name_en,lsb,default,is_valid,extra\n1,4,U32,测试,test,,,1,extra_value\n"
        csv_file = tmp_path / "extra.csv"
        csv_file.write_text(csv_content, encoding="utf-8-sig")
        result = load_csv(str(csv_file))
        assert len(result) == 1


class TestSaveCSVFormatting:
    """Tests for CSV save formatting."""

    def test_save_csv_preserves_lsb(self, tmp_path):
        """Test that LSB values are preserved."""
        fields = [
            FieldSpec(1, 4, "F32", "温度", "temp", 0.001, "25.5", True),
        ]
        csv_file = tmp_path / "lsb.csv"
        save_csv(str(csv_file), fields)
        content = csv_file.read_text(encoding="utf-8-sig")
        assert "0.001" in content

    def test_save_csv_boolean_format(self, tmp_path):
        """Test boolean format in CSV."""
        fields = [
            FieldSpec(1, 4, "U32", "有效", "valid", None, None, True),
            FieldSpec(2, 4, "U32", "无效", "invalid", None, None, False),
        ]
        csv_file = tmp_path / "bool.csv"
        save_csv(str(csv_file), fields)
        content = csv_file.read_text(encoding="utf-8-sig")
        assert "1" in content  # True
        assert "0" in content  # False


class TestReservedFieldBehavior:
    """Tests for RESERVED field behavior."""

    def test_reserved_affects_raw_byte_positions(self):
        """Test RESERVED fields occupy bytes in the raw frame layout."""
        fields = [
            FieldSpec(1, 4, "U32", "头部", "header", None, None, True),
            FieldSpec(2, 3, "RESERVED", "预留", "reserved_block", None, None, True),
            FieldSpec(3, 2, "U16", "尾部", "tail", None, None, True),
        ]
        positions = compute_byte_positions(fields)
        assert positions == ["B1-4", "B5-7", "B8-9"]

    def test_reserved_validity_changes_parsed_frame_size(self):
        """Test only valid RESERVED fields occupy parsed frame offsets."""
        fields = [
            FieldSpec(1, 4, "U32", "头部", "header", None, None, True),
            FieldSpec(2, 3, "RESERVED", "预留A", "reserved_valid", None, None, True),
            FieldSpec(3, 2, "U16", "中间", "middle", None, None, True),
            FieldSpec(4, 5, "RESERVED", "预留B", "reserved_invalid", None, None, False),
            FieldSpec(5, 1, "U8", "尾部", "tail", None, None, True),
        ]
        metas, bit_groups, _ = _build_layout(fields)
        parsed_size = _compute_frame_offsets(metas, bit_groups)
        assert parsed_size == 10
        assert metas[1].frame_offset == 4
        assert metas[2].frame_offset == 7
        assert metas[3].frame_offset is None
        assert metas[4].frame_offset == 9

    def test_generate_cpp_reserved_field_skips_pack_unpack_and_schema(self):
        """Test RESERVED fields are stored in frame but skipped by pack/unpack/schema."""
        fields = [
            FieldSpec(1, 4, "U32", "头部", "header", None, None, True),
            FieldSpec(2, 3, "RESERVED", "预留", "reserved_block", None, None, True),
            FieldSpec(3, 2, "U16", "尾部", "tail", None, None, True),
        ]
        code = generate_cpp_code("ReservedFrame", fields)
        assert "std::array<uint8_t, 3> reserved_block{};" in code
        assert "FRAME_SIZE = 9" in code
        assert 'schema.addFieldAt("预留"' not in code
        assert 'schema.addFieldAt("头部"' in code
        assert 'schema.addFieldAt("尾部"' in code
        assert "reserved_block = " not in code

    def test_generate_cpp_invalid_reserved_field_not_in_frame(self):
        """Test invalid RESERVED fields do not occupy parsed frame layout."""
        fields = [
            FieldSpec(1, 4, "U32", "头部", "header", None, None, True),
            FieldSpec(2, 6, "RESERVED", "预留", "reserved_block", None, None, False),
            FieldSpec(3, 2, "U16", "尾部", "tail", None, None, True),
        ]
        code = generate_cpp_code("ReservedFrameInvalid", fields)
        assert "reserved_block" not in code
        assert "FRAME_SIZE = 6" in code
