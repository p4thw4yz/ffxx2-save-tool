"""
Convert a save's raw bytes between platforms, using the project's own
bundled reference saves for the target header/size - the same approach
validated in main.py, wrapped as a pure function for reuse by the GUI.
"""

import os

from checksum import Game
from save_data import HEADER_LEN

_BASE = os.path.dirname(os.path.abspath(__file__))

# Real save files already in this repo, used as the header/size source for
# each (game, target platform) pair - see README/CHANGELOG for how these
# were validated. No confirmed real FFX2 Vita sample yet, so that one
# falls back to the PC reference (best available guess; PC and Vita are
# confirmed to share format for FFX, unconfirmed but assumed for FFX2).
REFERENCE_FILES = {
    (Game.FFX, "switch"): os.path.join(_BASE, "reference", "switch", "ffx_001"),
    (Game.FFX, "pc"): os.path.join(_BASE, "reference", "pc", "ffx_004"),
    (Game.FFX, "vita"): os.path.join(_BASE, "reference", "vita", "ffx_004"),
    (Game.FFX2, "switch"): os.path.join(_BASE, "reference", "switch", "ffx2_main_001"),
    (Game.FFX2, "pc"): os.path.join(_BASE, "reference", "pc", "ffx2_001"),
    (Game.FFX2, "vita"): os.path.join(_BASE, "reference", "pc", "ffx2_001"),
}


def _fit(data: bytes, target):
    if target is None or len(data) == target:
        return data
    if len(data) < target:
        return data + b"\x00" * (target - len(data))
    excess = data[target:]
    if any(excess):
        raise ValueError(
            f"{len(data)} bytes vs target {target}; the {len(excess)} excess "
            f"bytes are not all zero, refusing to cut real data"
        )
    return data[:target]


def convert_platform(data: bytes, game: Game, src_platform: str, dst_platform: str) -> bytes:
    """Returns `data` (currently formatted for `src_platform`) reformatted
    for `dst_platform` - header added/stripped and size matched to a real
    reference save for the target."""
    if src_platform == dst_platform:
        return bytes(data)

    body = bytes(data[HEADER_LEN[src_platform] :])
    dst_header_len = HEADER_LEN[dst_platform]

    ref_path = REFERENCE_FILES.get((game, dst_platform))
    header = b""
    target_size = None
    if ref_path and os.path.isfile(ref_path):
        with open(ref_path, "rb") as f:
            ref = f.read()
        target_size = len(ref)
        header = ref[:dst_header_len]

    return _fit(header + body, target_size)
