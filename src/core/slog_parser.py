from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
import struct
from typing import Dict, List, Sequence, Tuple, Union


MAGIC = b"SLOG"
VERSION = 1
ENDIAN_LITTLE = 1
HEADER_SIZE = 16


class LogFieldType(IntEnum):
    UInt8 = 0
    UInt16 = 1
    UInt32 = 2
    UInt64 = 3
    Int8 = 4
    Int16 = 5
    Int32 = 6
    Int64 = 7
    Float32 = 8
    Float64 = 9


_TYPE_INFO: Dict[LogFieldType, Tuple[str, int]] = {
    LogFieldType.UInt8: ("<B", 1),
    LogFieldType.UInt16: ("<H", 2),
    LogFieldType.UInt32: ("<I", 4),
    LogFieldType.UInt64: ("<Q", 8),
    LogFieldType.Int8: ("<b", 1),
    LogFieldType.Int16: ("<h", 2),
    LogFieldType.Int32: ("<i", 4),
    LogFieldType.Int64: ("<q", 8),
    LogFieldType.Float32: ("<f", 4),
    LogFieldType.Float64: ("<d", 8),
}


@dataclass(frozen=True)
class LogField:
    name: str
    field_type: LogFieldType
    count: int
    scale: float
    offset: float


@dataclass(frozen=True)
class LogSchema:
    fields: Sequence[LogField]

    @property
    def record_size(self) -> int:
        total = 0
        for field in self.fields:
            _, size = _TYPE_INFO[field.field_type]
            total += size * field.count
        return total


@dataclass(frozen=True)
class SlogHeader:
    magic: bytes
    version: int
    endian: int
    schema_size: int
    record_size: int


RecordValue = Union[int, float, List[Union[int, float]]]


@dataclass(frozen=True)
class SlogFile:
    header: SlogHeader
    schema: LogSchema
    records: List[Dict[str, RecordValue]]


def parse_slog_file(path: Union[str, Path], *, strict: bool = True, apply_scale: bool = True) -> SlogFile:
    data = Path(path).read_bytes()
    return parse_slog_bytes(data, strict=strict, apply_scale=apply_scale)


def parse_slog_bytes(data: bytes, *, strict: bool = True, apply_scale: bool = True) -> SlogFile:
    if len(data) < HEADER_SIZE:
        raise ValueError("SLOG file too small for header.")

    header = _parse_header(data)
    if header.magic != MAGIC:
        raise ValueError(f"Invalid magic: {header.magic!r}")
    if header.version != VERSION:
        raise ValueError(f"Unsupported version: {header.version}")
    if header.endian != ENDIAN_LITTLE:
        raise ValueError(f"Unsupported endian: {header.endian}")

    schema_end = HEADER_SIZE + header.schema_size
    if schema_end > len(data):
        raise ValueError("Schema size exceeds file length.")

    schema = _parse_schema(data[HEADER_SIZE:schema_end])
    if strict and schema.record_size != header.record_size:
        raise ValueError(
            f"Record size mismatch: header {header.record_size}, schema {schema.record_size}"
        )

    record_bytes = data[schema_end:]
    records: List[Dict[str, RecordValue]] = []
    if header.record_size > 0:
        if strict and (len(record_bytes) % header.record_size) != 0:
            raise ValueError("Record data size is not a multiple of record size.")
        record_count = len(record_bytes) // header.record_size
        for i in range(record_count):
            start = i * header.record_size
            end = start + header.record_size
            records.append(_parse_record(record_bytes[start:end], schema, apply_scale))

    return SlogFile(header=header, schema=schema, records=records)


def _parse_header(data: bytes) -> SlogHeader:
    magic = data[:4]
    version, = struct.unpack_from("<H", data, 4)
    endian = data[6]
    schema_size, = struct.unpack_from("<I", data, 8)
    record_size, = struct.unpack_from("<I", data, 12)
    return SlogHeader(
        magic=magic,
        version=version,
        endian=endian,
        schema_size=schema_size,
        record_size=record_size,
    )


def _parse_schema(schema_bytes: bytes) -> LogSchema:
    offset = 0
    field_count, offset = _read_struct("<I", schema_bytes, offset)
    fields: List[LogField] = []
    for _ in range(field_count):
        name_len, offset = _read_struct("<H", schema_bytes, offset)
        if offset + name_len > len(schema_bytes):
            raise ValueError("Schema name exceeds schema size.")
        name_bytes = schema_bytes[offset:offset + name_len]
        offset += name_len
        try:
            name = name_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("Failed to decode field name.") from exc

        if offset + 2 > len(schema_bytes):
            raise ValueError("Schema entry truncated before type.")
        field_type_raw = schema_bytes[offset]
        offset += 2  # skip type + reserved byte
        try:
            field_type = LogFieldType(field_type_raw)
        except ValueError as exc:
            raise ValueError(f"Unknown field type: {field_type_raw}") from exc

        count, offset = _read_struct("<I", schema_bytes, offset)
        scale, offset = _read_struct("<d", schema_bytes, offset)
        offset_value, offset = _read_struct("<d", schema_bytes, offset)
        fields.append(LogField(name=name,
                               field_type=field_type,
                               count=count,
                               scale=scale,
                               offset=offset_value))

    if offset != len(schema_bytes):
        raise ValueError("Schema size mismatch.")

    return LogSchema(fields=fields)


def _parse_record(record_bytes: bytes, schema: LogSchema, apply_scale: bool) -> Dict[str, RecordValue]:
    offset = 0
    record: Dict[str, RecordValue] = {}
    for field in schema.fields:
        fmt, size = _TYPE_INFO[field.field_type]
        values = []
        for _ in range(field.count):
            if offset + size > len(record_bytes):
                raise ValueError("Record truncated while reading fields.")
            value, = struct.unpack_from(fmt, record_bytes, offset)
            offset += size
            if apply_scale:
                value = value * field.scale + field.offset
            values.append(value)
        record[field.name] = values[0] if field.count == 1 else values

    if offset != len(record_bytes):
        raise ValueError("Record size does not match schema definition.")
    return record


def _read_struct(fmt: str, data: bytes, offset: int) -> Tuple[Union[int, float], int]:
    size = struct.calcsize(fmt)
    if offset + size > len(data):
        raise ValueError("Unexpected end of data while parsing.")
    value = struct.unpack_from(fmt, data, offset)[0]
    return value, offset + size


__all__ = [
    "LogFieldType",
    "LogField",
    "LogSchema",
    "SlogHeader",
    "SlogFile",
    "parse_slog_bytes",
    "parse_slog_file",
]
