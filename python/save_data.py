"""
Load a save file, read/edit named fields, write it back out - with the
platform header and (where supported) checksum handled automatically.

    >>> sd = SaveData.load("reference/pc/ffx2_001", Game.FFX2, "pc")
    >>> sd.get("gil")
    1234
    >>> sd.set("gil", 999999)
    >>> sd.save("output/edited/ffx2_001")
"""

from checksum import Game, update_checksum
from fields import read_field, write_field
from fields_ffx import FFX_FIELDS_BY_NAME
from fields_ffx2 import FFX2_FIELDS_BY_NAME

# Confirmed against real hardware for both games (see README/CHANGELOG):
# Switch prepends an 8-byte header; PC and Vita saves have none.
HEADER_LEN = {"pc": 0, "vita": 0, "switch": 8}

_FIELDS_BY_GAME = {Game.FFX: FFX_FIELDS_BY_NAME, Game.FFX2: FFX2_FIELDS_BY_NAME}

# Both games' checksum algorithms are validated (see checksum.py).
_CHECKSUM_SUPPORTED = {Game.FFX: True, Game.FFX2: True}


class UnknownFieldError(KeyError):
    pass


def coerce_value(raw, current):
    """Parses a user-supplied string `raw` into the same type as `current`
    (as returned by SaveData.get) - bool/float/int."""
    if isinstance(raw, (bool, int, float)):
        raw = str(raw)
    if isinstance(current, bool):
        return raw.strip().lower() in ("1", "true", "yes", "on")
    if isinstance(current, float):
        return float(raw)
    return int(raw)


class SaveData:
    def __init__(self, raw: bytes, game: Game, platform: str):
        if platform not in HEADER_LEN:
            raise ValueError(f"platform must be one of {sorted(HEADER_LEN)}, got {platform!r}")
        self.game = game
        self.platform = platform
        self.header_len = HEADER_LEN[platform]
        self.data = bytearray(raw)
        self._fields = _FIELDS_BY_GAME[game]

    @classmethod
    def load(cls, path, game: Game, platform: str):
        with open(path, "rb") as f:
            return cls(f.read(), game, platform)

    def _field(self, name):
        try:
            return self._fields[name]
        except KeyError:
            raise UnknownFieldError(
                f"no field {name!r} for {self.game.name} "
                f"(known fields: {len(self._fields)})"
            ) from None

    def get(self, name):
        return read_field(self.data, self._field(name), self.header_len)

    def set(self, name, value):
        write_field(self.data, self._field(name), value, self.header_len)

    def fields(self):
        """Returns {name: current_value} for every known field."""
        return {name: self.get(name) for name in self._fields}

    def export_bytes(self, recompute_checksum=True):
        data = bytes(self.data)
        if recompute_checksum and _CHECKSUM_SUPPORTED[self.game]:
            data = update_checksum(data, self.game, self.header_len)
        return data

    def save(self, path, recompute_checksum=True):
        with open(path, "wb") as f:
            f.write(self.export_bytes(recompute_checksum))

    def checksum_supported(self):
        return _CHECKSUM_SUPPORTED[self.game]
