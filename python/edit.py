#!/usr/bin/env python3
"""
Inspect and edit fields inside an FFX / FFX2 save file.

Usage:
  python3 edit.py list <path> <ffx|ffx2> <pc|vita|switch>
  python3 edit.py get  <path> <ffx|ffx2> <pc|vita|switch> <field>
  python3 edit.py set  <path> <ffx|ffx2> <pc|vita|switch> <field> <value> [--out <path>]

`set` writes back to <path> unless --out gives a different destination.
The checksum is recomputed automatically for both games (see checksum.py).
"""

import sys

from checksum import Game
from save_data import SaveData, UnknownFieldError, coerce_value

GAME_MAP = {"ffx": Game.FFX, "ffx2": Game.FFX2}


def main():
    args = sys.argv[1:]
    if len(args) < 4 or args[0] not in ("list", "get", "set"):
        print(__doc__)
        sys.exit(1)

    cmd, path, game_s, platform = args[0], args[1], args[2], args[3]
    if game_s not in GAME_MAP:
        sys.exit(f"error: game must be one of {sorted(GAME_MAP)}, got {game_s!r}")

    sd = SaveData.load(path, GAME_MAP[game_s], platform)

    try:
        if cmd == "list":
            for name, value in sorted(sd.fields().items()):
                print(f"{name} = {value}")

        elif cmd == "get":
            if len(args) < 5:
                sys.exit("error: get requires <field>")
            print(sd.get(args[4]))

        elif cmd == "set":
            if len(args) < 6:
                sys.exit("error: set requires <field> <value>")
            field, raw_value = args[4], args[5]
            out = path
            if "--out" in args:
                out = args[args.index("--out") + 1]

            current = sd.get(field)
            sd.set(field, coerce_value(raw_value, current))
            sd.save(out)

            note = ""
            if not sd.checksum_supported():
                note = "  (checksum NOT recomputed - load and save once in-game to fix it)"
            print(f"wrote {out}: {field} = {sd.get(field)}{note}")
    except UnknownFieldError as e:
        sys.exit(f"error: {e}")


if __name__ == "__main__":
    main()
