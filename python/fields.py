"""
Shared field-definition engine for FFX / FFX2 save data.

A `Field` describes one named value inside the save body (numeric fields
are little-endian; `kind='bit'` fields pack a single flag into one byte).
All offsets are relative to the start of the *core save body* - i.e. after
any platform header has already been stripped (see save_data.py, which
adds `header_len` back on for you).
"""

from dataclasses import dataclass
from typing import Optional
import struct

_STRUCT = {
    "u8": ("<B", 1),
    "u16": ("<H", 2),
    "u32": ("<I", 4),
    "i32": ("<i", 4),
    "f32": ("<f", 4),
}


@dataclass(frozen=True)
class Field:
    name: str
    offset: int
    kind: str  # 'u8' | 'u16' | 'u32' | 'i32' | 'f32' | 'bit'
    bit: Optional[int] = None  # only for kind='bit': which bit of the byte at `offset`
    note: str = ""


def bit_field(name, base_offset, bit_index, note=""):
    """Mirrors FFXED's BitFieldAccessor: a "bit index" can run past 7 and
    spill into later bytes (byte = base + bit_index // 8, bit = bit_index % 8)."""
    return Field(name, base_offset + bit_index // 8, "bit", bit_index % 8, note)


def read_field(data, field: Field, header_len: int = 0):
    off = header_len + field.offset
    if field.kind == "bit":
        return bool(data[off] & (1 << field.bit))
    fmt, _size = _STRUCT[field.kind]
    return struct.unpack_from(fmt, data, off)[0]


def write_field(data: bytearray, field: Field, value, header_len: int = 0):
    off = header_len + field.offset
    if field.kind == "bit":
        if value:
            data[off] |= 1 << field.bit
        else:
            data[off] &= ~(1 << field.bit) & 0xFF
        return
    fmt, _size = _STRUCT[field.kind]
    struct.pack_into(fmt, data, off, value)
