"""
SLOG解析器单元测试
测试SLOG文件解析功能，包括头部解析、模式解析和记录解析
"""

import sys
import struct
import tempfile
from pathlib import Path
from io import BytesIO

import pytest

# 确保src在路径中（用于直接运行测试文件）
_src_path = str(Path(__file__).resolve().parent.parent.parent.parent / "src")
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

from core.slog_parser import (
    LogFieldType,
    LogField,
    LogSchema,
    SlogHeader,
    SlogFile,
    parse_slog_file,
    parse_slog_bytes,
    _parse_header,
    _parse_schema,
    _parse_record,
    _read_struct,
    MAGIC,
    VERSION,
    ENDIAN_LITTLE,
    HEADER_SIZE,
)


class TestLogFieldType:
    """测试日志字段类型枚举"""

    def test_field_type_values(self):
        """测试字段类型值"""
        assert LogFieldType.UInt8.value == 0
        assert LogFieldType.UInt16.value == 1
        assert LogFieldType.UInt32.value == 2
        assert LogFieldType.UInt64.value == 3
        assert LogFieldType.Int8.value == 4
        assert LogFieldType.Int16.value == 5
        assert LogFieldType.Int32.value == 6
        assert LogFieldType.Int64.value == 7
        assert LogFieldType.Float32.value == 8
        assert LogFieldType.Float64.value == 9


class TestLogField:
    """测试日志字段类"""

    def test_field_creation(self):
        """测试字段创建"""
        field = LogField(
            name="test_field",
            field_type=LogFieldType.Float32,
            count=1,
            scale=1.0,
            offset=0.0,
        )

        assert field.name == "test_field"
        assert field.field_type == LogFieldType.Float32
        assert field.count == 1
        assert field.scale == 1.0
        assert field.offset == 0.0

    def test_field_immutable(self):
        """测试字段不可变性"""
        field = LogField(
            name="test",
            field_type=LogFieldType.Int32,
            count=1,
            scale=1.0,
            offset=0.0,
        )

        # 不可变dataclass，尝试修改应该创建新对象或失败
        with pytest.raises((AttributeError, TypeError)):
            field.name = "modified"


class TestLogSchema:
    """测试日志模式类"""

    def test_empty_schema(self):
        """测试空模式"""
        schema = LogSchema(fields=[])
        assert schema.record_size == 0

    def test_single_field_schema(self):
        """测试单字段模式"""
        field = LogField(
            name="value",
            field_type=LogFieldType.Float32,
            count=1,
            scale=1.0,
            offset=0.0,
        )
        schema = LogSchema(fields=[field])
        assert schema.record_size == 4  # Float32 is 4 bytes

    def test_multiple_fields_schema(self):
        """测试多字段模式"""
        fields = [
            LogField("timestamp", LogFieldType.UInt64, 1, 1.0, 0.0),  # 8 bytes
            LogField("value1", LogFieldType.Float32, 1, 1.0, 0.0),     # 4 bytes
            LogField("value2", LogFieldType.Float32, 1, 1.0, 0.0),     # 4 bytes
        ]
        schema = LogSchema(fields=fields)
        assert schema.record_size == 16  # 8 + 4 + 4

    def test_array_field_schema(self):
        """测试数组字段模式"""
        field = LogField(
            name="values",
            field_type=LogFieldType.Float32,
            count=10,  # 10个Float32
            scale=1.0,
            offset=0.0,
        )
        schema = LogSchema(fields=[field])
        assert schema.record_size == 40  # 10 * 4

    def test_mixed_types_schema(self):
        """测试混合类型模式"""
        fields = [
            LogField("id", LogFieldType.UInt32, 1, 1.0, 0.0),        # 4 bytes
            LogField("timestamp", LogFieldType.UInt64, 1, 1.0, 0.0),  # 8 bytes
            LogField("x", LogFieldType.Float64, 1, 1.0, 0.0),        # 8 bytes
            LogField("y", LogFieldType.Float64, 1, 1.0, 0.0),        # 8 bytes
        ]
        schema = LogSchema(fields=fields)
        assert schema.record_size == 28  # 4 + 8 + 8 + 8


class TestSlogHeader:
    """测试SLOG头部类"""

    def test_header_creation(self):
        """测试头部创建"""
        header = SlogHeader(
            magic=b"SLOG",
            version=1,
            endian=1,
            schema_size=100,
            record_size=32,
        )

        assert header.magic == b"SLOG"
        assert header.version == 1
        assert header.endian == 1
        assert header.schema_size == 100
        assert header.record_size == 32


class TestReadStruct:
    """测试结构读取辅助函数"""

    def test_read_uint8(self):
        """测试读取UInt8"""
        data = b"\x42"
        value, offset = _read_struct("<B", data, 0)
        assert value == 0x42
        assert offset == 1

    def test_read_uint16(self):
        """测试读取UInt16"""
        data = struct.pack("<H", 0x1234)
        value, offset = _read_struct("<H", data, 0)
        assert value == 0x1234
        assert offset == 2

    def test_read_uint32(self):
        """测试读取UInt32"""
        data = struct.pack("<I", 0x12345678)
        value, offset = _read_struct("<I", data, 0)
        assert value == 0x12345678
        assert offset == 4

    def test_read_uint64(self):
        """测试读取UInt64"""
        data = struct.pack("<Q", 0x123456789ABCDEF0)
        value, offset = _read_struct("<Q", data, 0)
        assert value == 0x123456789ABCDEF0
        assert offset == 8

    def test_read_float32(self):
        """测试读取Float32"""
        data = struct.pack("<f", 3.14159)
        value, offset = _read_struct("<f", data, 0)
        assert abs(value - 3.14159) < 0.0001
        assert offset == 4

    def test_read_float64(self):
        """测试读取Float64"""
        data = struct.pack("<d", 3.141592653589793)
        value, offset = _read_struct("<d", data, 0)
        assert abs(value - 3.141592653589793) < 1e-15
        assert offset == 8

    def test_read_with_offset(self):
        """测试带偏移量的读取"""
        data = b"\x00\x00\x42\x00"
        value, offset = _read_struct("<B", data, 2)
        assert value == 0x42
        assert offset == 3

    def test_read_beyond_end(self):
        """测试读取超出数据末尾"""
        data = b"\x00"
        with pytest.raises(ValueError) as exc_info:
            _read_struct("<I", data, 0)  # 尝试读取4字节，但只有1字节
        assert "Unexpected end of data" in str(exc_info.value)


class TestParseHeader:
    """测试头部解析函数"""

    def test_parse_valid_header(self):
        """测试解析有效头部"""
        # 构建有效头部
        header_data = b"SLOG"  # magic
        header_data += struct.pack("<H", 1)  # version
        header_data += b"\x01"  # endian
        header_data += b"\x00"  # padding
        header_data += struct.pack("<I", 100)  # schema_size
        header_data += struct.pack("<I", 32)   # record_size

        header = _parse_header(header_data)

        assert header.magic == b"SLOG"
        assert header.version == 1
        assert header.endian == 1
        assert header.schema_size == 100
        assert header.record_size == 32

    def test_parse_header_exact_size(self):
        """测试解析恰好16字节的头部"""
        header_data = b"SLOG" + b"\x00" * 12  # 4 + 12 = 16 bytes

        header = _parse_header(header_data)

        assert header.magic == b"SLOG"
        assert header.version == 0
        assert header.schema_size == 0
        assert header.record_size == 0


class TestParseSchema:
    """测试模式解析函数"""

    def test_parse_empty_schema(self):
        """测试解析空模式"""
        # 0个字段
        schema_data = struct.pack("<I", 0)

        schema = _parse_schema(schema_data)

        assert len(schema.fields) == 0
        assert schema.record_size == 0

    def test_parse_single_field_schema(self):
        """测试解析单字段模式"""
        # 构建模式数据: 1个字段
        schema_data = struct.pack("<I", 1)  # field_count

        # 字段名: "value"
        name = "value".encode("utf-8")
        schema_data += struct.pack("<H", len(name)) + name

        # 字段类型 + 保留字节
        schema_data += struct.pack("<B", LogFieldType.Float32.value)
        schema_data += b"\x00"  # reserved

        # count, scale, offset
        schema_data += struct.pack("<I", 1)   # count
        schema_data += struct.pack("<d", 1.0)  # scale
        schema_data += struct.pack("<d", 0.0)  # offset

        schema = _parse_schema(schema_data)

        assert len(schema.fields) == 1
        assert schema.fields[0].name == "value"
        assert schema.fields[0].field_type == LogFieldType.Float32
        assert schema.fields[0].count == 1
        assert schema.fields[0].scale == 1.0
        assert schema.fields[0].offset == 0.0

    def test_parse_multiple_fields_schema(self):
        """测试解析多字段模式"""
        schema_data = struct.pack("<I", 2)  # 2个字段

        # 字段1: timestamp (UInt64)
        name1 = "timestamp".encode("utf-8")
        schema_data += struct.pack("<H", len(name1)) + name1
        schema_data += struct.pack("<B", LogFieldType.UInt64.value)
        schema_data += b"\x00"
        schema_data += struct.pack("<I", 1)
        schema_data += struct.pack("<d", 1.0)
        schema_data += struct.pack("<d", 0.0)

        # 字段2: temperature (Float32)
        name2 = "temperature".encode("utf-8")
        schema_data += struct.pack("<H", len(name2)) + name2
        schema_data += struct.pack("<B", LogFieldType.Float32.value)
        schema_data += b"\x00"
        schema_data += struct.pack("<I", 1)
        schema_data += struct.pack("<d", 0.1)  # scale
        schema_data += struct.pack("<d", -40.0)  # offset

        schema = _parse_schema(schema_data)

        assert len(schema.fields) == 2
        assert schema.fields[0].name == "timestamp"
        assert schema.fields[0].field_type == LogFieldType.UInt64
        assert schema.fields[1].name == "temperature"
        assert schema.fields[1].field_type == LogFieldType.Float32
        assert schema.fields[1].scale == 0.1
        assert schema.fields[1].offset == -40.0

    def test_parse_schema_with_array(self):
        """测试解析数组字段模式"""
        schema_data = struct.pack("<I", 1)

        name = "values".encode("utf-8")
        schema_data += struct.pack("<H", len(name)) + name
        schema_data += struct.pack("<B", LogFieldType.Float32.value)
        schema_data += b"\x00"
        schema_data += struct.pack("<I", 10)  # count = 10
        schema_data += struct.pack("<d", 1.0)
        schema_data += struct.pack("<d", 0.0)

        schema = _parse_schema(schema_data)

        assert schema.fields[0].count == 10


class TestParseRecord:
    """测试记录解析函数"""

    def test_parse_single_value_record(self):
        """测试解析单值记录"""
        schema = LogSchema([
            LogField("value", LogFieldType.Float32, 1, 1.0, 0.0),
        ])

        record_data = struct.pack("<f", 3.14159)
        record = _parse_record(record_data, schema, apply_scale=True)

        assert abs(record["value"] - 3.14159) < 0.0001

    def test_parse_record_with_scale(self):
        """测试解析带缩放的记录"""
        schema = LogSchema([
            LogField("temp", LogFieldType.UInt16, 1, 0.1, -40.0),
        ])

        record_data = struct.pack("<H", 500)  # raw value
        record = _parse_record(record_data, schema, apply_scale=True)

        expected = 500 * 0.1 + (-40.0)  # 10.0
        assert abs(record["temp"] - expected) < 0.01

    def test_parse_record_without_scale(self):
        """测试解析不带缩放的记录"""
        schema = LogSchema([
            LogField("count", LogFieldType.UInt32, 1, 100.0, 0.0),
        ])

        record_data = struct.pack("<I", 42)
        record = _parse_record(record_data, schema, apply_scale=False)

        assert record["count"] == 42  # 不应用缩放

    def test_parse_array_record(self):
        """测试解析数组字段记录"""
        schema = LogSchema([
            LogField("values", LogFieldType.Float32, 3, 1.0, 0.0),
        ])

        record_data = struct.pack("<fff", 1.0, 2.0, 3.0)
        record = _parse_record(record_data, schema, apply_scale=True)

        assert record["values"] == [1.0, 2.0, 3.0]

    def test_parse_multiple_fields_record(self):
        """测试解析多字段记录"""
        schema = LogSchema([
            LogField("id", LogFieldType.UInt32, 1, 1.0, 0.0),
            LogField("x", LogFieldType.Float32, 1, 1.0, 0.0),
            LogField("y", LogFieldType.Float32, 1, 1.0, 0.0),
        ])

        record_data = struct.pack("<I", 123)
        record_data += struct.pack("<f", 1.5)
        record_data += struct.pack("<f", 2.5)

        record = _parse_record(record_data, schema, apply_scale=True)

        assert record["id"] == 123
        assert abs(record["x"] - 1.5) < 0.0001
        assert abs(record["y"] - 2.5) < 0.0001

    def test_parse_truncated_record(self):
        """测试解析截断记录"""
        schema = LogSchema([
            LogField("value", LogFieldType.Float32, 1, 1.0, 0.0),
        ])

        record_data = b"\x00"  # 只有1字节，但需要4字节

        with pytest.raises(ValueError) as exc_info:
            _parse_record(record_data, schema, apply_scale=True)
        assert "truncated" in str(exc_info.value).lower()


class TestParseSlogBytes:
    """测试解析字节数据函数"""

    def _create_slog_file(self, fields, records_data):
        """辅助函数：创建SLOG文件字节数据"""
        # 头部
        schema_data = struct.pack("<I", len(fields))

        for field in fields:
            name = field.name.encode("utf-8")
            schema_data += struct.pack("<H", len(name)) + name
            schema_data += struct.pack("<B", field.field_type.value)
            schema_data += b"\x00"
            schema_data += struct.pack("<I", field.count)
            schema_data += struct.pack("<d", field.scale)
            schema_data += struct.pack("<d", field.offset)

        # 计算记录大小
        record_size = sum(
            {LogFieldType.UInt8: 1, LogFieldType.UInt16: 2, LogFieldType.UInt32: 4,
             LogFieldType.UInt64: 8, LogFieldType.Int8: 1, LogFieldType.Int16: 2,
             LogFieldType.Int32: 4, LogFieldType.Int64: 8, LogFieldType.Float32: 4,
             LogFieldType.Float64: 8}[f.field_type] * f.count
            for f in fields
        )

        # 构建头部
        header_data = b"SLOG"
        header_data += struct.pack("<H", VERSION)
        header_data += struct.pack("<B", ENDIAN_LITTLE)
        header_data += b"\x00"
        header_data += struct.pack("<I", len(schema_data))
        header_data += struct.pack("<I", record_size)

        return header_data + schema_data + records_data

    def test_parse_empty_slog(self):
        """测试解析空SLOG文件"""
        fields = []
        data = self._create_slog_file(fields, b"")

        result = parse_slog_bytes(data)

        assert result.header.magic == MAGIC
        assert result.header.version == VERSION
        assert len(result.schema.fields) == 0
        assert len(result.records) == 0

    def test_parse_slog_with_records(self):
        """测试解析带记录的SLOG文件"""
        fields = [
            LogField("timestamp", LogFieldType.UInt64, 1, 1.0, 0.0),
            LogField("value", LogFieldType.Float32, 1, 1.0, 0.0),
        ]

        # 2条记录
        records_data = struct.pack("<Q", 1000) + struct.pack("<f", 1.5)
        records_data += struct.pack("<Q", 2000) + struct.pack("<f", 2.5)

        data = self._create_slog_file(fields, records_data)

        result = parse_slog_bytes(data)

        assert len(result.records) == 2
        assert result.records[0]["timestamp"] == 1000
        assert abs(result.records[0]["value"] - 1.5) < 0.0001
        assert result.records[1]["timestamp"] == 2000
        assert abs(result.records[1]["value"] - 2.5) < 0.0001

    def test_parse_slog_data_too_small(self):
        """测试解析过小的数据"""
        with pytest.raises(ValueError) as exc_info:
            parse_slog_bytes(b"SLOG")
        assert "too small" in str(exc_info.value).lower()

    def test_parse_slog_invalid_magic(self):
        """测试解析无效magic"""
        data = b"XXXX" + b"\x00" * 12  # 无效magic

        with pytest.raises(ValueError) as exc_info:
            parse_slog_bytes(data)
        assert "magic" in str(exc_info.value).lower()

    def test_parse_slog_unsupported_version(self):
        """测试解析不支持的版本"""
        data = b"SLOG"
        data += struct.pack("<H", 999)  # 不支持版本
        data += struct.pack("<B", ENDIAN_LITTLE)
        data += b"\x00"
        data += struct.pack("<I", 0)
        data += struct.pack("<I", 0)

        with pytest.raises(ValueError) as exc_info:
            parse_slog_bytes(data)
        assert "version" in str(exc_info.value).lower()

    def test_parse_slog_unsupported_endian(self):
        """测试解析不支持的endian"""
        data = b"SLOG"
        data += struct.pack("<H", VERSION)
        data += struct.pack("<B", 2)  # 不支持endian
        data += b"\x00"
        data += struct.pack("<I", 0)
        data += struct.pack("<I", 0)

        with pytest.raises(ValueError) as exc_info:
            parse_slog_bytes(data)
        assert "endian" in str(exc_info.value).lower()

    def test_parse_slog_strict_mode(self):
        """测试严格模式"""
        # 创建一个record_size与实际不符的文件
        fields = [LogField("value", LogFieldType.Float32, 1, 1.0, 0.0)]

        schema_data = struct.pack("<I", 1)
        name = "value".encode("utf-8")
        schema_data += struct.pack("<H", len(name)) + name
        schema_data += struct.pack("<B", LogFieldType.Float32.value)
        schema_data += b"\x00"
        schema_data += struct.pack("<I", 1)
        schema_data += struct.pack("<d", 1.0)
        schema_data += struct.pack("<d", 0.0)

        header_data = b"SLOG"
        header_data += struct.pack("<H", VERSION)
        header_data += struct.pack("<B", ENDIAN_LITTLE)
        header_data += b"\x00"
        header_data += struct.pack("<I", len(schema_data))
        header_data += struct.pack("<I", 100)  # 错误的record_size

        data = header_data + schema_data + struct.pack("<f", 1.0)

        # 严格模式应该失败
        with pytest.raises(ValueError) as exc_info:
            parse_slog_bytes(data, strict=True)
        assert "mismatch" in str(exc_info.value).lower()

        # 非严格模式应该成功（但记录数为0，因为record_size不匹配导致无法解析记录）
        result = parse_slog_bytes(data, strict=False)
        assert len(result.records) == 0  # record_size=100，但数据只有4字节，无法解析记录


class TestParseSlogFile:
    """测试解析文件函数"""

    def test_parse_nonexistent_file(self, tmp_path):
        """测试解析不存在的文件"""
        nonexistent = tmp_path / "nonexistent.slog"

        with pytest.raises(FileNotFoundError):
            parse_slog_file(nonexistent)

    def test_parse_valid_file(self, tmp_path):
        """测试解析有效文件"""
        # 创建简单的SLOG文件
        fields = [LogField("value", LogFieldType.Float32, 1, 1.0, 0.0)]

        schema_data = struct.pack("<I", 1)
        name = "value".encode("utf-8")
        schema_data += struct.pack("<H", len(name)) + name
        schema_data += struct.pack("<B", LogFieldType.Float32.value)
        schema_data += b"\x00"
        schema_data += struct.pack("<I", 1)
        schema_data += struct.pack("<d", 1.0)
        schema_data += struct.pack("<d", 0.0)

        header_data = b"SLOG"
        header_data += struct.pack("<H", VERSION)
        header_data += struct.pack("<B", ENDIAN_LITTLE)
        header_data += b"\x00"
        header_data += struct.pack("<I", len(schema_data))
        header_data += struct.pack("<I", 4)  # Float32 = 4 bytes

        data = header_data + schema_data + struct.pack("<f", 3.14159)

        slog_file = tmp_path / "test.slog"
        slog_file.write_bytes(data)

        result = parse_slog_file(slog_file)

        assert abs(result.records[0]["value"] - 3.14159) < 0.0001


class TestEdgeCases:
    """测试边界情况"""

    def test_all_field_types(self):
        """测试所有字段类型"""
        for field_type in LogFieldType:
            # 创建单字段模式
            schema_data = struct.pack("<I", 1)
            name = "field".encode("utf-8")
            schema_data += struct.pack("<H", len(name)) + name
            schema_data += struct.pack("<B", field_type.value)
            schema_data += b"\x00"
            schema_data += struct.pack("<I", 1)
            schema_data += struct.pack("<d", 1.0)
            schema_data += struct.pack("<d", 0.0)

            # 确定字段大小
            type_sizes = {
                LogFieldType.UInt8: 1, LogFieldType.UInt16: 2,
                LogFieldType.UInt32: 4, LogFieldType.UInt64: 8,
                LogFieldType.Int8: 1, LogFieldType.Int16: 2,
                LogFieldType.Int32: 4, LogFieldType.Int64: 8,
                LogFieldType.Float32: 4, LogFieldType.Float64: 8,
            }
            field_size = type_sizes[field_type]

            # 构建记录数据
            if field_type in (LogFieldType.Float32, LogFieldType.Float64):
                record_data = struct.pack("<f" if field_type == LogFieldType.Float32 else "<d", 1.0)
            else:
                record_data = b"\x01" * field_size

            header_data = b"SLOG"
            header_data += struct.pack("<H", VERSION)
            header_data += struct.pack("<B", ENDIAN_LITTLE)
            header_data += b"\x00"
            header_data += struct.pack("<I", len(schema_data))
            header_data += struct.pack("<I", field_size)

            data = header_data + schema_data + record_data

            result = parse_slog_bytes(data)
            assert len(result.records) == 1

    def test_unicode_field_names(self):
        """测试Unicode字段名"""
        schema_data = struct.pack("<I", 1)
        name = "温度值".encode("utf-8")
        schema_data += struct.pack("<H", len(name)) + name
        schema_data += struct.pack("<B", LogFieldType.Float32.value)
        schema_data += b"\x00"
        schema_data += struct.pack("<I", 1)
        schema_data += struct.pack("<d", 1.0)
        schema_data += struct.pack("<d", 0.0)

        header_data = b"SLOG"
        header_data += struct.pack("<H", VERSION)
        header_data += struct.pack("<B", ENDIAN_LITTLE)
        header_data += b"\x00"
        header_data += struct.pack("<I", len(schema_data))
        header_data += struct.pack("<I", 4)

        data = header_data + schema_data + struct.pack("<f", 25.0)

        result = parse_slog_bytes(data)
        assert result.schema.fields[0].name == "温度值"

    def test_zero_count_field(self):
        """测试零计数字段"""
        schema_data = struct.pack("<I", 1)
        name = "empty".encode("utf-8")
        schema_data += struct.pack("<H", len(name)) + name
        schema_data += struct.pack("<B", LogFieldType.Float32.value)
        schema_data += b"\x00"
        schema_data += struct.pack("<I", 0)  # count = 0
        schema_data += struct.pack("<d", 1.0)
        schema_data += struct.pack("<d", 0.0)

        header_data = b"SLOG"
        header_data += struct.pack("<H", VERSION)
        header_data += struct.pack("<B", ENDIAN_LITTLE)
        header_data += b"\x00"
        header_data += struct.pack("<I", len(schema_data))
        header_data += struct.pack("<I", 0)  # record_size = 0

        # 添加一个空记录（record_size=0，所以记录数据为空）
        data = header_data + schema_data + b""

        result = parse_slog_bytes(data)
        # 当record_size=0时，不会解析任何记录
        assert len(result.records) == 0
