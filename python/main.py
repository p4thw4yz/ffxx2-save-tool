#!/usr/bin/env python3
"""
ffx_saveconv.py - batch save converter for FINAL FANTASY X / X-2 HD Remaster

Edit the CONFIG block below, then run:  python3 ffx_saveconv.py

A Switch save is the PC save body prefixed with an 8-byte header and padded with
zeros to a fixed length. This script adds or strips that header across a whole
directory and handles the size matching.

Keep an untouched backup of your original saves before restoring anything.
"""

# ==========================================================================
#  CONFIG - edit this block only
# ==========================================================================

GAME = "ffx"                     # "ffx" or "ffx2"

INPUT_PLATFORM = "pc"            # "pc" or "switch"
OUTPUT_PLATFORM = "switch"       # "pc" or "switch"

INPUT_DIR = "./input/pc"         # folder holding the saves to convert
OUTPUT_DIR = "./output/switch"   # folder to write converted saves into

# A real save file from the OUTPUT platform. Strongly recommended: its length
# sets the output size, and (if USE_REF_HEADER is on) its first 8 bytes are used
# as the header instead of the built-in constant. Leave "" to skip.
# Reference saves are organized by platform under ./reference/<platform>/
REFERENCE_SAVE = "./reference/switch/ffx_001"

USE_REF_HEADER = True            # take the header from REFERENCE_SAVE when available

FILE_GLOB = "ffx_*"               # e.g. "ffx2_*" to limit which files are picked up
NAME_TEMPLATE = "ffx_{index:03d}"  # output filename; {name} {stem} {index} {game}
INDEX_START = 0                  # first value of {index}

TRIM_TRAILING_ZEROS = False      # switch -> pc, when no REFERENCE_SAVE is set
OVERWRITE = False                # allow writing over existing files in OUTPUT_DIR
DRY_RUN = False                  # report what would happen, write nothing

# ==========================================================================
#  End of config
# ==========================================================================

import glob
import os
import sys

# Fallback, used when REFERENCE_SAVE is not set. This value is NOT a real
# header for either game - a real Switch reference save showed the actual
# header's first 4 bytes are a little-endian Unix timestamp, followed by 4
# zero bytes. Always prefer REFERENCE_SAVE + USE_REF_HEADER when you have a
# real save to check against - a prior attempt at ffx using this placeholder,
# with no REFERENCE_SAVE set (so no size matching happened either), produced
# a save that did not load on real hardware.
HEADERS = {
    "ffx":  bytes([0x08, 0x00, 0x00, 0x00, 0x01, 0x00, 0x01, 0x02]),
    "ffx2": bytes([0x08, 0x00, 0x00, 0x00, 0x01, 0x00, 0x01, 0x02]),
}
HEADER_LEN = 8


def fail(msg):
    sys.exit(f"error: {msg}")


def hexstr(data, n=16):
    return " ".join(f"{b:02X}" for b in data[:n])


def validate():
    if GAME not in HEADERS:
        fail(f"GAME must be one of {sorted(HEADERS)}, got {GAME!r}")
    for label, val in (("INPUT_PLATFORM", INPUT_PLATFORM), ("OUTPUT_PLATFORM", OUTPUT_PLATFORM)):
        if val not in ("pc", "switch"):
            fail(f"{label} must be 'pc' or 'switch', got {val!r}")
    if INPUT_PLATFORM == OUTPUT_PLATFORM:
        fail("INPUT_PLATFORM and OUTPUT_PLATFORM are the same, nothing to do")
    if not os.path.isdir(INPUT_DIR):
        fail(f"INPUT_DIR does not exist: {INPUT_DIR}")
    if REFERENCE_SAVE and not os.path.isfile(REFERENCE_SAVE):
        fail(f"REFERENCE_SAVE does not exist: {REFERENCE_SAVE}")


def load_reference():
    """Returns (target_size, header) derived from REFERENCE_SAVE."""
    header = HEADERS[GAME]
    if not REFERENCE_SAVE:
        print("note: no REFERENCE_SAVE set - using the built-in header and no size matching")
        return None, header

    ref = open(REFERENCE_SAVE, "rb").read()
    size = len(ref)

    if OUTPUT_PLATFORM == "switch":
        if USE_REF_HEADER:
            header = ref[:HEADER_LEN]
            print(f"header from reference: {hexstr(header, HEADER_LEN)}")
        elif ref[:HEADER_LEN] != header:
            print(f"warning: reference header {hexstr(ref, HEADER_LEN)} differs from "
                  f"built-in {hexstr(header, HEADER_LEN)}")
    print(f"reference: {REFERENCE_SAVE} ({size} bytes)")
    return size, header


def fit(data, target, name):
    """Pad with zeros or drop trailing zeros so len(data) == target."""
    if target is None or len(data) == target:
        return data
    if len(data) < target:
        return data + b"\x00" * (target - len(data))
    excess = data[target:]
    if any(excess):
        raise ValueError(
            f"{len(data)} bytes vs target {target}; the {len(excess)} excess bytes "
            f"are not all zero, refusing to cut real data"
        )
    return data[:target]


def convert(data, target_size, header):
    if OUTPUT_PLATFORM == "switch":
        if data[:HEADER_LEN] == header:
            raise ValueError("already has the Switch header - is this a Switch save?")
        return fit(header + data, target_size, "output")

    # switch -> pc
    if data[:HEADER_LEN] != header:
        print(f"    warning: unexpected header {hexstr(data, HEADER_LEN)}, stripping anyway")
    body = data[HEADER_LEN:]
    if target_size is None and TRIM_TRAILING_ZEROS:
        body = body.rstrip(b"\x00")
    return fit(body, target_size, "output")


def main():
    validate()
    target_size, header = load_reference()

    files = sorted(
        f for f in glob.glob(os.path.join(INPUT_DIR, FILE_GLOB)) if os.path.isfile(f)
    )
    if REFERENCE_SAVE:
        files = [f for f in files if os.path.abspath(f) != os.path.abspath(REFERENCE_SAVE)]
    if not files:
        fail(f"no files matched {FILE_GLOB!r} in {INPUT_DIR}")

    print(f"\n{GAME.upper()}  {INPUT_PLATFORM} -> {OUTPUT_PLATFORM}   "
          f"{len(files)} file(s){'   [DRY RUN]' if DRY_RUN else ''}\n")

    if not DRY_RUN:
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    ok = skipped = 0
    for i, path in enumerate(files):
        name = os.path.basename(path)
        stem = os.path.splitext(name)[0]
        out_name = NAME_TEMPLATE.format(
            name=name, stem=stem, index=INDEX_START + i, game=GAME
        )
        out_path = os.path.join(OUTPUT_DIR, out_name)

        try:
            data = open(path, "rb").read()
            result = convert(data, target_size, header)
        except ValueError as e:
            print(f"  SKIP  {name}: {e}")
            skipped += 1
            continue

        if os.path.exists(out_path) and not OVERWRITE and not DRY_RUN:
            print(f"  SKIP  {name}: {out_name} exists (set OVERWRITE = True)")
            skipped += 1
            continue

        if not DRY_RUN:
            with open(out_path, "wb") as f:
                f.write(result)

        print(f"  OK    {name} -> {out_name}  ({len(data)} -> {len(result)} bytes)")
        skipped += 0
        ok += 1

    print(f"\ndone: {ok} converted, {skipped} skipped")
    if target_size is None and OUTPUT_PLATFORM == "switch":
        print("warning: no size matching was applied; the Switch build may reject a "
              "save whose size differs from its native one")
    if ok and OUTPUT_PLATFORM == "switch":
        print("\nNext: rename to the Switch save's exact filename, restore with "
              "JKSV/Checkpoint,\nload it, then save at an in-game save sphere so the "
              "game writes a valid checksum.")
    elif ok:
        print("\nNext: copy into the Steam save folder over an existing slot name, "
              "load it,\nthen save in-game.")


if __name__ == "__main__":
    main()
