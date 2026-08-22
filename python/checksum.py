"""
CRC-16 checksum for FINAL FANTASY X / X-2 HD Remaster saves.

Reimplemented from published community reverse-engineering (see README /
CHANGELOG for sources). Both FFX and FFX2 are validated: recomputing the
checksum for our real reference saves (PC and Switch, both games)
reproduces the exact bytes already stored in those files.

FFX2's end offset (0x1626C) came from MarkH221/FFX-HD-Checksum-Utility -
a dedicated HD Remaster tool that handles both games. It's 4 bytes short
of the older PS2-International-Edition forum number (0x16270) that a
first attempt used, which is why that attempt failed against our real
files.

The checksum covers a fixed-size "core" region starting at byte 0x40,
regardless of platform - PC/Switch saves are the same core structure with
extra bytes appended/padded after it. Two copies of the checksum are
stored: a shared location near the top of the file, and a second location
right after the core region ends.
"""

from enum import Enum


class Game(Enum):
    FFX = 1
    FFX2 = 2


CRC_START_OFFSET = 0x40
CRC_SEED = 0xFFFF

# End of the checksummed core region (== PS2-era save size for each game).
CRC_END_FFX = 0x64F8    # 25848
CRC_END_FFX2 = 0x1626C  # 91756

# Where the checksum bytes themselves are written (little-endian uint16).
CHECKSUM_LOCATION_A = 0x1A  # shared by FFX and FFX2
CHECKSUM_LOCATION_FFX_B = 0x64F4
CHECKSUM_LOCATION_FFX2_B = 0x16268


def _crc16_table():
    """FFX's CRC-16 table - CRC-16-CCITT with a known off-by-one bug: the
    last table entry is forced to 0 rather than the mathematically correct
    value, so the table must be generated this way to match the game."""
    generator = 0x1021
    table = [0] * 256
    for dividend in range(256):
        cur = (dividend << 8) & 0xFFFF
        for _ in range(8):
            if cur & 0x8000:
                cur = ((cur << 1) ^ generator) & 0xFFFF
            else:
                cur = (cur << 1) & 0xFFFF
        table[dividend] = cur
    table[255] = 0x0
    return table


_CRC16_TABLE = _crc16_table()


def _compute(data, header_len, game):
    """Compute the checksum bytes (lo, hi) for `data`, where `data` may
    have `header_len` extra bytes (0 or 8) prepended ahead of the core
    save structure (e.g. the Switch header)."""
    end = header_len + (CRC_END_FFX if game is Game.FFX else CRC_END_FFX2)
    checksum_loc = header_len + (
        CHECKSUM_LOCATION_FFX_B if game is Game.FFX else CHECKSUM_LOCATION_FFX2_B
    )
    checksum = CRC_SEED
    for i in range(header_len + CRC_START_OFFSET, end):
        # The checksum bytes read as 0 while computing (whatever value is
        # already there, stale or not, must be ignored).
        byte = 0 if i in (checksum_loc, checksum_loc + 1) else data[i]
        table_index = ((checksum >> 8) ^ byte) & 0xFF
        checksum = ((checksum << 8) ^ _CRC16_TABLE[table_index]) & 0xFFFF
    checksum ^= CRC_SEED
    return checksum & 0xFF, (checksum >> 8) & 0xFF


def update_checksum(data, game, header_len=0):
    """Returns a copy of `data` with both checksum locations rewritten to
    the correct value for its current contents. `header_len` is 8 for a
    Switch-formatted save (8-byte header prepended), 0 otherwise."""
    data = bytearray(data)
    lo, hi = _compute(data, header_len, game)
    data[header_len + CHECKSUM_LOCATION_A] = lo
    data[header_len + CHECKSUM_LOCATION_A + 1] = hi
    b_loc = header_len + (
        CHECKSUM_LOCATION_FFX_B if game is Game.FFX else CHECKSUM_LOCATION_FFX2_B
    )
    data[b_loc] = lo
    data[b_loc + 1] = hi
    return bytes(data)


def read_checksum(data, game, header_len=0):
    """Returns the (A, B) checksum values currently stored in `data`, each
    as a little-endian uint16, for comparison against a freshly computed
    value."""
    a_loc = header_len + CHECKSUM_LOCATION_A
    b_loc = header_len + (
        CHECKSUM_LOCATION_FFX_B if game is Game.FFX else CHECKSUM_LOCATION_FFX2_B
    )
    a = data[a_loc] | (data[a_loc + 1] << 8)
    b = data[b_loc] | (data[b_loc + 1] << 8)
    return a, b
