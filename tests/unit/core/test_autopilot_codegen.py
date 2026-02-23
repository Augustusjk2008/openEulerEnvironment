"""
Unit tests for autopilot_codegen_cpp module.

Tests C++ code generation logic including:
- Template rendering and variable replacement
- Code generation for headers and sources
- Expression conversion to C++
- Type handling and sanitization
"""

import math
import pytest
from unittest.mock import patch, MagicMock

# Import the module under test
from core.autopilot_codegen_cpp import (
    generate_cpp_header,
    _class_name_from_doc,
    _class_name_from_path,
    _sanitize_cpp_class_name,
    _cpp_enum_name,
    _cpp_type,
    _emit_member_decl,
    _cpp_param_decl,
    _cpp_assign_input,
    _cpp_literal,
    _cpp_init_list,
    _cpp_float_literal,
    _clamp_bound_to_cpp,
    _split_functions,
    _func_method_name,
    _assigned_vars,
    _used_vars,
    _infer_outputs,
    _only_self_read_for_clamp,
    _iter_private_members,
    _emit_nodes,
    _expr_to_cpp,
    _FuncSeg,
)


class TestClassNameFromDoc:
    """Tests for _class_name_from_doc function."""

    def test_default_class_name(self):
        """Test default class name when name is not provided."""
        doc = {}
        result = _class_name_from_doc(doc)
        assert result == "Controller"

    def test_class_name_from_name_field(self):
        """Test class name extracted from document name field."""
        doc = {"name": "MyController"}
        result = _class_name_from_doc(doc)
        assert result == "MyController"

    def test_class_name_sanitization(self):
        """Test class name sanitization."""
        doc = {"name": "My-Controller!"}
        result = _class_name_from_doc(doc)
        assert result == "My_Controller_"

    def test_empty_name_defaults_to_controller(self):
        """Test empty name defaults to Controller."""
        doc = {"name": ""}
        result = _class_name_from_doc(doc)
        assert result == "Controller"

    def test_whitespace_name_defaults_to_controller(self):
        """Test whitespace-only name defaults to Controller."""
        doc = {"name": "   "}
        result = _class_name_from_doc(doc)
        assert result == "Controller"


class TestClassNameFromPath:
    """Tests for _class_name_from_path function."""

    def test_none_path(self):
        """Test None path returns empty string."""
        result = _class_name_from_path(None)
        assert result == ""

    def test_empty_path(self):
        """Test empty path returns empty string."""
        result = _class_name_from_path("")
        assert result == ""

    def test_json_extension_removed(self):
        """Test .json extension is removed."""
        result = _class_name_from_path("/path/to/MyController.json")
        assert result == "MyController"

    def test_json_extension_case_insensitive(self):
        """Test .JSON extension is removed (case insensitive)."""
        result = _class_name_from_path("/path/to/MyController.JSON")
        assert result == "MyController"

    def test_path_with_directories(self):
        """Test path with directories extracts basename."""
        result = _class_name_from_path("/a/b/c/TestController")
        assert result == "TestController"

    def test_filename_only(self):
        """Test filename only extracts correctly."""
        result = _class_name_from_path("TestController.json")
        assert result == "TestController"


class TestSanitizeCppClassName:
    """Tests for _sanitize_cpp_class_name function."""

    def test_valid_name_unchanged(self):
        """Test valid C++ class name remains unchanged."""
        result = _sanitize_cpp_class_name("MyController")
        assert result == "MyController"

    def test_invalid_chars_replaced(self):
        """Test invalid characters are replaced with underscore."""
        result = _sanitize_cpp_class_name("My-Controller!@#")
        assert result == "My_Controller___"

    def test_leading_digit_prefixed(self):
        """Test leading digit gets underscore prefix."""
        result = _sanitize_cpp_class_name("123Controller")
        assert result == "_123Controller"

    def test_empty_name_defaults_to_controller(self):
        """Test empty name defaults to Controller."""
        result = _sanitize_cpp_class_name("")
        assert result == "Controller"

    def test_whitespace_trimmed(self):
        """Test whitespace is trimmed."""
        result = _sanitize_cpp_class_name("  MyController  ")
        assert result == "MyController"

    def test_only_invalid_chars(self):
        """Test name with only invalid chars becomes underscores with prefix."""
        result = _sanitize_cpp_class_name("!@#$%")
        # The function replaces invalid chars with _, and if result starts with _, it's kept
        assert result == "_____"


class TestCppEnumName:
    """Tests for _cpp_enum_name function."""

    def test_valid_enum_name(self):
        """Test valid enum name remains unchanged."""
        result = _cpp_enum_name("ActiveState")
        assert result == "ActiveState"

    def test_invalid_chars_replaced(self):
        """Test invalid characters are replaced with underscore."""
        result = _cpp_enum_name("Active-State!")
        assert result == "Active_State_"

    def test_leading_digit_prefixed(self):
        """Test leading digit gets underscore prefix."""
        result = _cpp_enum_name("1stState")
        assert result == "_1stState"

    def test_empty_name_defaults_to_unknown(self):
        """Test empty name defaults to Unknown."""
        result = _cpp_enum_name("")
        assert result == "Unknown"

    def test_none_handled(self):
        """Test None input handled gracefully."""
        result = _cpp_enum_name(None)
        assert result == "Unknown"

    def test_whitespace_trimmed(self):
        """Test whitespace is trimmed."""
        result = _cpp_enum_name("  ActiveState  ")
        assert result == "ActiveState"


class TestCppType:
    """Tests for _cpp_type function."""

    def test_f32_type(self):
        """Test f32 maps to float."""
        result = _cpp_type({"type": "f32"})
        assert result == "float"

    def test_f64_type(self):
        """Test f64 maps to double."""
        result = _cpp_type({"type": "f64"})
        assert result == "double"

    def test_int_type(self):
        """Test int maps to int32_t."""
        result = _cpp_type({"type": "int"})
        assert result == "int32_t"

    def test_uint_type(self):
        """Test uint maps to uint32_t."""
        result = _cpp_type({"type": "uint"})
        assert result == "uint32_t"

    def test_default_type(self):
        """Test default type is double."""
        result = _cpp_type({})
        assert result == "double"

    def test_invalid_type_defaults_to_double(self):
        """Test invalid type defaults to double."""
        result = _cpp_type({"type": "invalid"})
        assert result == "double"

    def test_none_meta_defaults_to_double(self):
        """Test None meta defaults to double."""
        result = _cpp_type(None)
        assert result == "double"


class TestEmitMemberDecl:
    """Tests for _emit_member_decl function."""

    def test_scalar_member(self):
        """Test scalar member declaration."""
        meta = {"kind": "scalar", "type": "f64"}
        result = _emit_member_decl("value", meta, indent="    ")
        assert any("double value = 0.0;" in line for line in result)

    def test_scalar_with_init(self):
        """Test scalar member with initialization."""
        meta = {"kind": "scalar", "type": "f64", "init": 3.14}
        result = _emit_member_decl("value", meta, indent="    ")
        assert any("double value = 3.14;" in line for line in result)

    def test_constant_member(self):
        """Test constant member declaration."""
        meta = {"kind": "constant", "type": "f64", "init": 2.0}
        result = _emit_member_decl("PI", meta, indent="    ")
        assert any("const double PI = 2.0;" in line for line in result)

    def test_sequence_member(self):
        """Test sequence member declaration."""
        meta = {"kind": "sequence", "type": "f64"}
        result = _emit_member_decl("history", meta, indent="    ")
        assert any("DynamicSequence<double> history;" in line for line in result)

    def test_vector_member(self):
        """Test vector (dim > 1) member declaration."""
        meta = {"kind": "scalar", "type": "f64", "dim": 3}
        result = _emit_member_decl("position", meta, indent="    ")
        assert any("std::vector<double> position" in line for line in result)

    def test_member_with_description(self):
        """Test member with description comment."""
        meta = {"kind": "scalar", "type": "f64", "desc": "The position value"}
        result = _emit_member_decl("pos", meta, indent="    ")
        assert any("// The position value" in line for line in result)

    def test_invalid_meta_handled(self):
        """Test invalid meta is handled gracefully."""
        result = _emit_member_decl("value", None, indent="    ")
        assert any("double value = 0.0;" in line for line in result)

    def test_different_types(self):
        """Test different C++ types."""
        for type_name, cpp_type in [("f32", "float"), ("int", "int32_t"), ("uint", "uint32_t")]:
            meta = {"kind": "scalar", "type": type_name}
            result = _emit_member_decl("val", meta, indent="    ")
            assert any(f"{cpp_type} val" in line for line in result)


class TestCppParamDecl:
    """Tests for _cpp_param_decl function."""

    def test_scalar_param(self):
        """Test scalar parameter declaration."""
        meta = {"kind": "scalar", "type": "f64"}
        result = _cpp_param_decl("input", meta)
        assert result == "double input_in"

    def test_sequence_param(self):
        """Test sequence parameter declaration."""
        meta = {"kind": "sequence", "type": "f64"}
        result = _cpp_param_decl("history", meta)
        assert result == "double history_in"

    def test_vector_param(self):
        """Test vector (dim > 1) parameter declaration."""
        meta = {"kind": "scalar", "type": "f64", "dim": 3}
        result = _cpp_param_decl("position", meta)
        assert result == "const std::vector<double>& position_in"

    def test_invalid_dim_handled(self):
        """Test invalid dimension is handled gracefully."""
        meta = {"kind": "scalar", "type": "f64", "dim": "invalid"}
        result = _cpp_param_decl("input", meta)
        assert result == "double input_in"

    def test_invalid_meta_defaults(self):
        """Test invalid meta uses defaults."""
        result = _cpp_param_decl("input", None)
        assert result == "double input_in"


class TestCppAssignInput:
    """Tests for _cpp_assign_input function."""

    def test_scalar_assignment(self):
        """Test scalar input assignment."""
        meta = {"kind": "scalar"}
        result = _cpp_assign_input("value", meta, indent="        ")
        assert result == "        value = value_in;"

    def test_sequence_assignment(self):
        """Test sequence input assignment."""
        meta = {"kind": "sequence"}
        result = _cpp_assign_input("history", meta, indent="        ")
        assert result == "        history[0] = history_in;"

    def test_vector_assignment(self):
        """Test vector (dim > 1) input assignment."""
        meta = {"kind": "scalar", "dim": 3}
        result = _cpp_assign_input("position", meta, indent="        ")
        assert result == "        position = position_in;"

    def test_invalid_dim_handled(self):
        """Test invalid dimension is handled gracefully."""
        meta = {"kind": "scalar", "dim": "invalid"}
        result = _cpp_assign_input("value", meta, indent="        ")
        assert result == "        value = value_in;"

    def test_invalid_meta_defaults(self):
        """Test invalid meta uses defaults."""
        result = _cpp_assign_input("value", None, indent="        ")
        assert result == "        value = value_in;"


class TestCppLiteral:
    """Tests for _cpp_literal function."""

    def test_float_literal(self):
        """Test float literal conversion."""
        result = _cpp_literal(3.14, "float")
        assert result == "3.14"

    def test_double_literal(self):
        """Test double literal conversion."""
        result = _cpp_literal(3.14, "double")
        assert result == "3.14"

    def test_int_literal(self):
        """Test int literal conversion."""
        result = _cpp_literal(42, "int32_t")
        assert result == "42"

    def test_invalid_float_defaults_to_zero(self):
        """Test invalid float defaults to 0.0."""
        result = _cpp_literal("invalid", "float")
        assert result == "0.0"

    def test_invalid_int_defaults_to_zero(self):
        """Test invalid int defaults to 0."""
        result = _cpp_literal("invalid", "int32_t")
        assert result == "0"

    def test_none_float_defaults_to_zero(self):
        """Test None float defaults to 0.0."""
        result = _cpp_literal(None, "double")
        assert result == "0.0"


class TestCppInitList:
    """Tests for _cpp_init_list function."""

    def test_list_values(self):
        """Test list of values."""
        result = _cpp_init_list([1.0, 2.0, 3.0], 3, "double")
        assert result == "{1.0, 2.0, 3.0}"

    def test_single_value_repeated(self):
        """Test single value repeated to match dimension."""
        result = _cpp_init_list([5.0], 3, "double")
        assert result == "{5.0, 5.0, 5.0}"

    def test_values_extended(self):
        """Test values extended with last value."""
        result = _cpp_init_list([1.0, 2.0], 4, "double")
        assert result == "{1.0, 2.0, 2.0, 2.0}"

    def test_values_truncated(self):
        """Test values truncated to match dimension."""
        result = _cpp_init_list([1.0, 2.0, 3.0, 4.0], 2, "double")
        assert result == "{1.0, 2.0}"

    def test_empty_list_defaults(self):
        """Test empty list defaults to single zero."""
        result = _cpp_init_list([], 3, "double")
        assert result == "{0.0, 0.0, 0.0}"

    def test_none_value_defaults(self):
        """Test None value defaults to single zero."""
        result = _cpp_init_list(None, 2, "double")
        assert result == "{0.0, 0.0}"


class TestCppFloatLiteral:
    """Tests for _cpp_float_literal function."""

    def test_integer_value(self):
        """Test integer value gets .0 suffix."""
        result = _cpp_float_literal(42)
        assert result == "42.0"

    def test_float_value(self):
        """Test float value formatting."""
        result = _cpp_float_literal(3.14159)
        assert result == "3.14159"

    def test_zero(self):
        """Test zero formatting."""
        result = _cpp_float_literal(0)
        assert result == "0.0"

    def test_negative_value(self):
        """Test negative value."""
        result = _cpp_float_literal(-3.14)
        assert result == "-3.14"

    def test_infinity_positive(self):
        """Test positive infinity."""
        result = _cpp_float_literal(float('inf'))
        assert result == "INFINITY"

    def test_infinity_negative(self):
        """Test negative infinity."""
        result = _cpp_float_literal(float('-inf'))
        assert result == "-INFINITY"

    def test_nan(self):
        """Test NaN handling - NaN is not finite so returns -INFINITY."""
        result = _cpp_float_literal(float('nan'))
        # NaN is not finite, so it returns -INFINITY based on implementation
        assert "INFINITY" in result

    def test_invalid_string(self):
        """Test invalid string defaults to 0.0."""
        result = _cpp_float_literal("invalid")
        assert result == "0.0"

    def test_large_integer_scientific(self):
        """Test large integer uses scientific notation."""
        result = _cpp_float_literal(1e20)
        assert "e" in result.lower() or "E" in result


class TestClampBoundToCpp:
    """Tests for _clamp_bound_to_cpp function."""

    def test_numeric_float(self):
        """Test numeric float value."""
        result = _clamp_bound_to_cpp(3.14, [], "double")
        assert result == "3.14"

    def test_numeric_int(self):
        """Test numeric int value."""
        result = _clamp_bound_to_cpp(42, [], "double")
        assert result == "42.0"

    def test_infinity_string_positive(self):
        """Test positive infinity string."""
        result = _clamp_bound_to_cpp("inf", [], "double")
        assert "INFINITY" in result

    def test_infinity_string_negative(self):
        """Test negative infinity string."""
        result = _clamp_bound_to_cpp("-inf", [], "double")
        # For double type, negative infinity gets -(double)INFINITY format
        assert "INFINITY" in result

    def test_empty_string_defaults_to_zero(self):
        """Test empty string defaults to zero."""
        result = _clamp_bound_to_cpp("", [], "double")
        assert result == "0.0"

    def test_expression_conversion(self):
        """Test expression is converted to C++."""
        result = _clamp_bound_to_cpp("x + y", [], "double")
        assert "x" in result and "y" in result

    def test_float_type_suffix(self):
        """Test float type adds f suffix."""
        result = _clamp_bound_to_cpp(3.14, [], "float")
        assert result == "3.14f"

    def test_double_infinity_cast(self):
        """Test double type with infinity gets cast."""
        result = _clamp_bound_to_cpp("inf", [], "double")
        assert "(double)INFINITY" in result


class TestSplitFunctions:
    """Tests for _split_functions function."""

    def test_empty_program(self):
        """Test empty program returns default function."""
        result = _split_functions([])
        assert len(result) == 1
        assert result[0].name == "Default"

    def test_single_function(self):
        """Test single function definition."""
        program = [
            {"op": "function", "name": "Init", "comment": "Initialize"},
            {"op": "assign", "lhs": "x", "rhs": "0"}
        ]
        result = _split_functions(program)
        assert len(result) == 1
        assert result[0].name == "Init"
        assert result[0].comment == "Initialize"
        assert len(result[0].nodes) == 1

    def test_multiple_functions(self):
        """Test multiple function definitions."""
        program = [
            {"op": "function", "name": "Init"},
            {"op": "assign", "lhs": "x", "rhs": "0"},
            {"op": "function", "name": "Update"},
            {"op": "assign", "lhs": "y", "rhs": "1"}
        ]
        result = _split_functions(program)
        assert len(result) == 2
        assert result[0].name == "Init"
        assert result[1].name == "Update"

    def test_function_without_name(self):
        """Test function without name gets default."""
        program = [
            {"op": "function"},
            {"op": "assign", "lhs": "x", "rhs": "0"}
        ]
        result = _split_functions(program)
        assert result[0].name == "Function"

    def test_no_function_returns_default(self):
        """Test program without function returns default."""
        program = [
            {"op": "assign", "lhs": "x", "rhs": "0"}
        ]
        result = _split_functions(program)
        assert len(result) == 1
        assert result[0].name == "Default"

    def test_non_dict_nodes_ignored(self):
        """Test non-dict nodes are ignored."""
        program = [
            "not a dict",
            {"op": "function", "name": "Test"},
            123,
            {"op": "assign", "lhs": "x", "rhs": "0"}
        ]
        result = _split_functions(program)
        assert result[0].name == "Test"
        assert len(result[0].nodes) == 1


class TestFuncMethodName:
    """Tests for _func_method_name function."""

    def test_valid_name(self):
        """Test valid function name."""
        result = _func_method_name("Init")
        assert result == "_fn_Init"

    def test_invalid_chars_replaced(self):
        """Test invalid characters replaced."""
        result = _func_method_name("Init-Phase")
        assert result == "_fn_Init_Phase"

    def test_leading_digit_prefixed(self):
        """Test leading digit gets underscore prefix."""
        result = _func_method_name("1stPhase")
        assert result == "_fn__1stPhase"

    def test_empty_name_defaults(self):
        """Test empty name defaults to Function."""
        result = _func_method_name("")
        assert result == "_fn_Function"

    def test_whitespace_trimmed(self):
        """Test whitespace is trimmed."""
        result = _func_method_name("  Init  ")
        assert result == "_fn_Init"


class TestAssignedVars:
    """Tests for _assigned_vars function."""

    def test_simple_assignment(self):
        """Test simple variable assignment."""
        program = [
            {"op": "assign", "lhs": "x", "rhs": "0"}
        ]
        result = _assigned_vars(program)
        assert "x" in result

    def test_array_assignment(self):
        """Test array element assignment."""
        program = [
            {"op": "assign", "lhs": "arr[0]", "rhs": "0"}
        ]
        result = _assigned_vars(program)
        assert "arr" in result

    def test_multiple_assignments(self):
        """Test multiple variable assignments."""
        program = [
            {"op": "assign", "lhs": "x", "rhs": "0"},
            {"op": "assign", "lhs": "y", "rhs": "1"}
        ]
        result = _assigned_vars(program)
        assert "x" in result
        assert "y" in result

    def test_if_statement_walked(self):
        """Test if statement branches are walked."""
        program = [
            {"op": "if", "cond": "true", "then": [
                {"op": "assign", "lhs": "x", "rhs": "0"}
            ], "else": [
                {"op": "assign", "lhs": "y", "rhs": "1"}
            ]}
        ]
        result = _assigned_vars(program)
        assert "x" in result
        assert "y" in result

    def test_function_op_ignored(self):
        """Test function op doesn't add variables."""
        program = [
            {"op": "function", "name": "Test"}
        ]
        result = _assigned_vars(program)
        assert len(result) == 0

    def test_non_dict_nodes_ignored(self):
        """Test non-dict nodes are ignored."""
        program = [
            "not a dict",
            123,
            {"op": "assign", "lhs": "x", "rhs": "0"}
        ]
        result = _assigned_vars(program)
        assert "x" in result


class TestUsedVars:
    """Tests for _used_vars function."""

    def test_simple_variable(self):
        """Test simple variable in expression."""
        program = [
            {"op": "assign", "lhs": "x", "rhs": "y + 1"}
        ]
        result = _used_vars(program)
        assert "y" in result

    def test_multiple_variables(self):
        """Test multiple variables in expression."""
        program = [
            {"op": "assign", "lhs": "z", "rhs": "x + y"}
        ]
        result = _used_vars(program)
        assert "x" in result
        assert "y" in result

    def test_reserved_words_excluded(self):
        """Test reserved words are excluded."""
        program = [
            {"op": "assign", "lhs": "x", "rhs": "abs(y) + min(a, b)"}
        ]
        result = _used_vars(program)
        assert "abs" not in result
        assert "min" not in result
        assert "y" in result
        assert "a" in result
        assert "b" in result

    def test_if_condition_scanned(self):
        """Test if condition is scanned."""
        program = [
            {"op": "if", "cond": "x > 0", "then": [], "else": []}
        ]
        result = _used_vars(program)
        assert "x" in result

    def test_if_branches_walked(self):
        """Test if branches are walked."""
        program = [
            {"op": "if", "cond": "true", "then": [
                {"op": "assign", "lhs": "x", "rhs": "y"}
            ], "else": [
                {"op": "assign", "lhs": "z", "rhs": "w"}
            ]}
        ]
        result = _used_vars(program)
        assert "y" in result
        assert "w" in result

    def test_string_literals_excluded(self):
        """Test string literals are excluded."""
        program = [
            {"op": "assign", "lhs": "x", "rhs": "'some_string' + y"}
        ]
        result = _used_vars(program)
        assert "some_string" not in result
        assert "y" in result

    def test_scientific_notation_excluded(self):
        """Test scientific notation numbers are excluded."""
        program = [
            {"op": "assign", "lhs": "x", "rhs": "1.5e10 + y"}
        ]
        result = _used_vars(program)
        assert "e" not in result
        assert "y" in result


class TestInferOutputs:
    """Tests for _infer_outputs function."""

    def test_assigned_not_used_is_output(self):
        """Test variable assigned but not used is output."""
        program = [
            {"op": "assign", "lhs": "output", "rhs": "1"}
        ]
        data = {"output": {"kind": "scalar"}}
        result = _infer_outputs(program, data, [])
        assert "output" in result

    def test_input_excluded(self):
        """Test inputs are excluded from outputs."""
        program = [
            {"op": "assign", "lhs": "input_var", "rhs": "1"}
        ]
        data = {"input_var": {"kind": "scalar"}}
        result = _infer_outputs(program, data, ["input_var"])
        assert "input_var" not in result

    def test_non_scalar_excluded(self):
        """Test non-scalar variables are excluded."""
        program = [
            {"op": "assign", "lhs": "seq", "rhs": "1"}
        ]
        data = {"seq": {"kind": "sequence"}}
        result = _infer_outputs(program, data, [])
        assert "seq" not in result

    def test_not_assigned_excluded(self):
        """Test variables not assigned are excluded."""
        program = []
        data = {"var": {"kind": "scalar"}}
        result = _infer_outputs(program, data, [])
        assert "var" not in result


class TestOnlySelfReadForClamp:
    """Tests for _only_self_read_for_clamp function."""

    def test_no_self_read(self):
        """Test when target is not read."""
        program = [
            {"op": "assign", "lhs": "x", "rhs": "y"}
        ]
        result = _only_self_read_for_clamp(program, "x")
        assert result is True

    def test_self_read_in_clamp(self):
        """Test self read in clamp operation."""
        program = [
            {"op": "clamp", "lhs": "x", "rhs": "x", "min": "0", "max": "10"}
        ]
        result = _only_self_read_for_clamp(program, "x")
        assert result is True

    def test_other_read_in_assign(self):
        """Test other variable read in assignment."""
        program = [
            {"op": "assign", "lhs": "x", "rhs": "y"}
        ]
        result = _only_self_read_for_clamp(program, "y")
        assert result is False


class TestIterPrivateMembers:
    """Tests for _iter_private_members function."""

    def test_excludes_outputs(self):
        """Test outputs are excluded."""
        data = {
            "output1": {"kind": "scalar"},
            "internal1": {"kind": "scalar"}
        }
        result = _iter_private_members(data, ["output1"])
        assert len(result) == 1
        assert result[0][0] == "internal1"

    def test_sorted_order(self):
        """Test results are sorted."""
        data = {
            "z": {"kind": "scalar"},
            "a": {"kind": "scalar"},
            "m": {"kind": "scalar"}
        }
        result = _iter_private_members(data, [])
        names = [r[0] for r in result]
        assert names == ["a", "m", "z"]

    def test_non_dict_values_excluded(self):
        """Test non-dict values are excluded."""
        data = {
            "valid": {"kind": "scalar"},
            "invalid": "not a dict"
        }
        result = _iter_private_members(data, [])
        assert len(result) == 1
        assert result[0][0] == "valid"


class TestExprToCpp:
    """Tests for _expr_to_cpp function."""

    def test_and_operator(self):
        """Test 'and' operator converted to &&."""
        result = _expr_to_cpp("a and b", [])
        assert "&&" in result

    def test_or_operator(self):
        """Test 'or' operator converted to ||."""
        result = _expr_to_cpp("a or b", [])
        assert "||" in result

    def test_not_operator(self):
        """Test 'not' operator converted to !."""
        result = _expr_to_cpp("not a", [])
        assert result.startswith("!")

    def test_true_false(self):
        """Test True/False converted to true/false."""
        result = _expr_to_cpp("True and False", [])
        assert "true" in result
        assert "false" in result

    def test_state_string_conversion(self):
        """Test state string converted to enum."""
        result = _expr_to_cpp("'Active'", ["Active"])
        assert "FlightState::Active" in result

    def test_state_not_in_list_quoted(self):
        """Test state not in list gets quoted."""
        result = _expr_to_cpp("'Unknown'", ["Active"])
        assert '"Unknown"' in result

    def test_abs_function(self):
        """Test abs function converted to std::abs."""
        result = _expr_to_cpp("abs(x)", [])
        assert "std::abs" in result

    def test_min_function(self):
        """Test min function converted to std::min."""
        result = _expr_to_cpp("min(a, b)", [])
        assert "std::min" in result

    def test_max_function(self):
        """Test max function converted to std::max."""
        result = _expr_to_cpp("max(a, b)", [])
        assert "std::max" in result

    def test_infinity_conversion(self):
        """Test infinity converted to INFINITY."""
        result = _expr_to_cpp("inf", [])
        assert "INFINITY" in result

    def test_empty_expr_returns_zero(self):
        """Test empty expression returns 0."""
        result = _expr_to_cpp("", [])
        assert result == "0"


class TestEmitNodes:
    """Tests for _emit_nodes function."""

    def test_assign_op(self):
        """Test assign operation emission."""
        nodes = [{"op": "assign", "lhs": "x", "rhs": "y + 1"}]
        result = _emit_nodes(nodes, indent="    ", data={}, states=[])
        assert any("x = y + 1;" in line for line in result)

    def test_clamp_op(self):
        """Test clamp operation emission."""
        nodes = [{"op": "clamp", "lhs": "x", "rhs": "y", "min": "0", "max": "10"}]
        result = _emit_nodes(nodes, indent="    ", data={"x": {"type": "f64"}}, states=[])
        assert any("std::clamp" in line for line in result)

    def test_select_op(self):
        """Test select operation emission."""
        nodes = [{"op": "select", "lhs": "x", "cond": "a > 0", "true": "1", "false": "0"}]
        result = _emit_nodes(nodes, indent="    ", data={}, states=[])
        assert any("x = (a > 0 ? 1 : 0);" in line for line in result)

    def test_if_op(self):
        """Test if operation emission."""
        nodes = [{"op": "if", "cond": "x > 0", "then": [], "else": []}]
        result = _emit_nodes(nodes, indent="    ", data={}, states=[])
        assert any("if (x > 0)" in line for line in result)
        assert any("else" in line for line in result)

    def test_comment_emission(self):
        """Test comment is emitted."""
        nodes = [{"op": "assign", "lhs": "x", "rhs": "0", "comment": "Initialize x"}]
        result = _emit_nodes(nodes, indent="    ", data={}, states=[])
        assert any("// Initialize x" in line for line in result)

    def test_piecewise_op(self):
        """Test piecewise operation emission."""
        nodes = [{
            "op": "piecewise",
            "lhs": "x",
            "cases": [{"when": "a > 0", "value": "1"}],
            "else": "0"
        }]
        result = _emit_nodes(nodes, indent="    ", data={}, states=[])
        assert any("if (a > 0)" in line for line in result)
        assert any("else" in line for line in result)

    def test_function_op_skipped(self):
        """Test function op is skipped."""
        nodes = [{"op": "function", "name": "Test"}]
        result = _emit_nodes(nodes, indent="    ", data={}, states=[])
        assert len(result) == 0

    def test_non_dict_nodes_skipped(self):
        """Test non-dict nodes are skipped."""
        nodes = ["not a dict", 123]
        result = _emit_nodes(nodes, indent="    ", data={}, states=[])
        assert len(result) == 0


class TestGenerateCppHeader:
    """Tests for generate_cpp_header function."""

    def test_empty_doc_generates_header(self):
        """Test empty document generates valid header."""
        doc = {}
        result = generate_cpp_header(doc)
        assert "#pragma once" in result
        assert "class Controller" in result

    def test_class_name_from_doc(self):
        """Test class name from document."""
        doc = {"name": "MyController"}
        result = generate_cpp_header(doc)
        assert "class MyController" in result

    def test_class_name_from_path(self):
        """Test class name from source path."""
        doc = {"name": "DocName"}
        result = generate_cpp_header(doc, source_path="/path/FileName.json")
        assert "class FileName" in result

    def test_includes_generated(self):
        """Test standard includes are generated."""
        doc = {}
        result = generate_cpp_header(doc)
        assert "#include <algorithm>" in result
        assert "#include <cmath>" in result
        assert "#include <vector>" in result

    def test_constructor_destructor_generated(self):
        """Test constructor and destructor are generated."""
        doc = {}
        result = generate_cpp_header(doc)
        assert "Controller() = default;" in result
        assert "~Controller() = default;" in result

    def test_input_output_members(self):
        """Test input and output members are generated."""
        doc = {
            "data": {
                "input1": {"io": "input", "kind": "scalar", "type": "f64"},
                "output1": {"io": "output", "kind": "scalar", "type": "f64"}
            }
        }
        result = generate_cpp_header(doc)
        assert "output1" in result

    def test_state_enum_generated(self):
        """Test state enum is generated."""
        doc = {
            "state": {
                "states": ["Idle", "Active", "Done"],
                "STATE": "Idle"
            }
        }
        result = generate_cpp_header(doc)
        assert "enum class FlightState" in result
        assert "Idle" in result
        assert "Active" in result
        assert "Done" in result

    def test_dynamic_sequence_template(self):
        """Test DynamicSequence template is generated."""
        doc = {}
        result = generate_cpp_header(doc)
        assert "template <typename T>" in result
        assert "struct DynamicSequence" in result

    def test_update_method_generated(self):
        """Test update method is generated."""
        doc = {}
        result = generate_cpp_header(doc)
        assert "void update(" in result

    def test_function_methods_generated(self):
        """Test function methods are generated."""
        doc = {
            "program": [
                {"op": "function", "name": "Init"},
                {"op": "assign", "lhs": "x", "rhs": "0"}
            ]
        }
        result = generate_cpp_header(doc)
        assert "_fn_Init" in result

    def test_sequence_iteration(self):
        """Test sequence iteration is generated."""
        doc = {
            "data": {
                "history": {"kind": "sequence", "type": "f64", "iterate": True}
            }
        }
        result = generate_cpp_header(doc)
        assert "history.shift()" in result

    def test_assign_inputs_method(self):
        """Test _assignInputs method is generated."""
        doc = {
            "data": {
                "input1": {"io": "input", "kind": "scalar", "type": "f64"}
            }
        }
        result = generate_cpp_header(doc)
        assert "_assignInputs(" in result


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_generate_cpp_header_with_none_state(self):
        """Test generate_cpp_header handles None state."""
        doc = {"state": None}
        result = generate_cpp_header(doc)
        assert "class Controller" in result

    def test_generate_cpp_header_with_none_program(self):
        """Test generate_cpp_header handles None program."""
        doc = {"program": None}
        result = generate_cpp_header(doc)
        assert "class Controller" in result

    def test_generate_cpp_header_with_none_data(self):
        """Test generate_cpp_header handles None data."""
        doc = {"data": None}
        result = generate_cpp_header(doc)
        assert "class Controller" in result

    def test_emit_nodes_with_nested_if(self):
        """Test emit_nodes handles nested if statements."""
        nodes = [{
            "op": "if",
            "cond": "x > 0",
            "then": [
                {"op": "if", "cond": "y > 0", "then": [], "else": []}
            ],
            "else": []
        }]
        result = _emit_nodes(nodes, indent="    ", data={}, states=[])
        # Count lines containing "if ("
        if_count = sum(1 for line in result if "if (" in line)
        assert if_count == 2

    def test_split_functions_with_empty_nodes(self):
        """Test _split_functions with empty nodes list."""
        program = [
            {"op": "function", "name": "Empty"}
        ]
        result = _split_functions(program)
        assert result[0].name == "Empty"
        assert len(result[0].nodes) == 0

    def test_clamp_bound_with_infinity_float(self):
        """Test _clamp_bound_to_cpp with float infinity."""
        result = _clamp_bound_to_cpp(float('inf'), [], "double")
        assert "INFINITY" in result

    def test_cpp_literal_with_bool_for_int(self):
        """Test _cpp_literal with boolean for int type."""
        result = _cpp_literal(True, "int32_t")
        assert result == "1"

    def test_cpp_init_list_with_mixed_types(self):
        """Test _cpp_init_list with mixed numeric types."""
        result = _cpp_init_list([1, 2.5, 3], 3, "double")
        assert "1.0" in result
        assert "2.5" in result
        assert "3.0" in result


class TestIntegration:
    """Integration tests for complete code generation scenarios."""

    def test_simple_controller_generation(self):
        """Test simple controller code generation."""
        doc = {
            "name": "SimpleController",
            "state": {
                "states": ["Idle", "Running"],
                "STATE": "Idle"
            },
            "data": {
                "input_val": {"io": "input", "kind": "scalar", "type": "f64", "desc": "Input value"},
                "output_val": {"io": "output", "kind": "scalar", "type": "f64", "desc": "Output value"},
                "gain": {"kind": "constant", "type": "f64", "init": 2.0}
            },
            "program": [
                {"op": "function", "name": "Compute", "comment": "Main computation"},
                {"op": "assign", "lhs": "output_val", "rhs": "input_val * gain"}
            ]
        }
        result = generate_cpp_header(doc)

        # Verify class structure
        assert "class SimpleController" in result
        assert "public:" in result

        # Verify members
        assert "output_val" in result
        assert "gain" in result

        # Verify methods
        assert "void update(" in result
        assert "_fn_Compute" in result

        # Verify comments
        assert "Input value" in result
        assert "Output value" in result
        assert "Main computation" in result

    def test_complex_controller_with_sequences(self):
        """Test complex controller with sequences."""
        doc = {
            "name": "FilterController",
            "data": {
                "input": {"io": "input", "kind": "scalar", "type": "f64"},
                "history": {"kind": "sequence", "type": "f64", "iterate": True, "desc": "History buffer"},
                "output": {"io": "output", "kind": "scalar", "type": "f64"}
            },
            "program": [
                {"op": "assign", "lhs": "output", "rhs": "(history[0] + history[1]) / 2.0"}
            ]
        }
        result = generate_cpp_header(doc)

        assert "DynamicSequence<double> history" in result
        assert "history.shift()" in result

    def test_controller_with_clamping(self):
        """Test controller with clamping operations."""
        doc = {
            "name": "ClampController",
            "data": {
                "input": {"io": "input", "kind": "scalar", "type": "f64"},
                "output": {"io": "output", "kind": "scalar", "type": "f64"},
                "min_val": {"kind": "constant", "type": "f64", "init": 0.0},
                "max_val": {"kind": "constant", "type": "f64", "init": 100.0}
            },
            "program": [
                {"op": "clamp", "lhs": "output", "rhs": "input", "min": "min_val", "max": "max_val"}
            ]
        }
        result = generate_cpp_header(doc)

        assert "std::clamp" in result

    def test_controller_with_conditional(self):
        """Test controller with conditional logic."""
        doc = {
            "name": "ConditionalController",
            "state": {
                "states": ["Off", "On"],
                "STATE": "Off"
            },
            "data": {
                "enabled": {"io": "input", "kind": "scalar", "type": "f64"},
                "output": {"io": "output", "kind": "scalar", "type": "f64"}
            },
            "program": [
                {"op": "if", "cond": "enabled > 0", "then": [
                    {"op": "assign", "lhs": "output", "rhs": "1"}
                ], "else": [
                    {"op": "assign", "lhs": "output", "rhs": "0"}
                ]}
            ]
        }
        result = generate_cpp_header(doc)

        assert "if (enabled > 0)" in result
        assert "else" in result
        assert "FlightState::Off" in result

    def test_controller_with_piecewise(self):
        """Test controller with piecewise operations."""
        doc = {
            "name": "PiecewiseController",
            "data": {
                "input": {"io": "input", "kind": "scalar", "type": "f64"},
                "output": {"io": "output", "kind": "scalar", "type": "f64"}
            },
            "program": [
                {"op": "piecewise", "lhs": "output", "cases": [
                    {"when": "input < 0", "value": "-1"},
                    {"when": "input > 0", "value": "1"}
                ], "else": "0"}
            ]
        }
        result = generate_cpp_header(doc)

        assert "if (input < 0)" in result
        assert "else if (input > 0)" in result
        assert "else" in result
