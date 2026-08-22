# FFX / FFX2 HD Remaster Save Tool

Convert FINAL FANTASY X / X-2 HD Remaster saves between PC, Vita and
Switch, read and edit hundreds of fields inside them (stats, abilities,
story position, and more), and browse the raw file - all from one local
tool. No command line required day-to-day; the GUI covers everything
below except the very first `pip install`.

## Quick start

```
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python app.py
```

Open the printed local URL (default `http://127.0.0.1:8050`). Tabs:

- **Overview** - a plain-language summary of the loaded save: Gil, play
  time, battles fought, story progress (with a "near: `<checkpoint>`"
  guess for FFX), and a card per party member with their HP/MP,
  unlocked-ability count, and overdrive gauge (FFX) or Level/EXP/
  dressphere (FFX2).
- **Fields** - every known field in a searchable, filterable table.
  Filter by category or type part of a field name, edit any Value cell,
  then **Apply edits** to rewrite the in-memory save and recompute a
  valid checksum.
- **Story Position** *(FFX only)* - pick a known story checkpoint from
  the dropdown and click **Jump to checkpoint** to set
  `room_number`/`spawn_point`/`storyline_progress` in one click. FFX2
  doesn't need this - see "Story position / chapter rewinding" below.
- **Export** - **Download edited save** as-is, or pick a target platform
  and **Convert & download**.
- **Raw / Hex** - a hex dump of the whole file, 16 bytes per row, with
  any known field(s) in that row shown inline. One search box matches
  offset, hex bytes, ASCII text, or field names.
- **Info** - this README, rendered in-app.

**Always keep your original save until you've loaded an edited one
in-game and confirmed it works as expected.**

## What's here

| Capability | Status |
|---|---|
| PC ↔ Switch conversion | **Confirmed working** on real hardware, both games |
| Vita ↔ PC/Switch conversion | Container format matches (same size, no extra header); untested with a real matching save - see Open items |
| Field editing | FFX: 3,116 fields (full per-character stats/abilities/perks + ~290 world-state flags). FFX2: 632 fields (full party stats + 554 story/dialogue flags) |
| Story position / chapter rewind | FFX: 15 curated checkpoints. FFX2: use its official in-game Chapter Select instead (see below) |
| Checksum | Both games validated - edits get a real, automatically-recomputed checksum, no in-game save-and-reload workaround needed |

## How platform conversion works

A Switch save is the PC save body with an **8-byte header prepended**.
Confirmed against real Switch saves: this header is **not** a fixed
magic value - its first 4 bytes are a little-endian Unix timestamp,
followed by 4 zero bytes. The game rewrites this header (and checksum)
itself on your next in-game save, so the exact value doesn't need to be
"correct," just present and 8 bytes long - which is why conversion
always uses a real reference save from the target platform for the
header and output size, rather than a placeholder constant.

One real difference between the games: **FFX2's file grows by exactly
+8 bytes** on conversion (91808 → 91816, a plain prepend), while **FFX's
file size stays the same** (26880 → 26880) because the PC body ends in
8 bytes of zero padding that get trimmed to make room for the header.
Both are handled automatically (`platform_convert.py`'s `fit()` logic
only trims when the bytes it would cut are actually all zero).

Real Switch save naming also differs by game - confirmed against files
pulled off an SD card: FFX2 saves are `ffx2_main_000`, `ffx2_main_001`,
...; FFX saves are `ffx_000`, `ffx_001`, ... (**no** `_main_`). Don't
assume one game's naming for the other.

Vita and PC FFX saves are the same size (26880 bytes) with no extra
header on either side, so they appear to share the same raw format -
but the two files compared were unrelated saves at different points in
the game, so this only confirms the container format, not a
field-level byte match. A real matching Vita save would settle this
properly (see Open items).

## Field editing reference

```
checksum.py           CRC-16 checksum - validated for both games against real saves
fields.py              shared Field/bit-field engine
fields_ffx.py            FFX field map - 3,116 fields: full per-character stats/abilities/
                          perks for all 18 party members & aeons, story position, ~290 global
                          flags (optional bosses, sidequests, key items, chocobo times, ...)
fields_ffx_extra.py       FFX's ~290 global (non-character) fields as raw data - generated,
                          not hand-written
fields_ffx2.py            FFX2 field map (Gil, playtime, chapter, full character stat blocks,
                           554 individual story/dialogue flags) - 632 fields
fields_ffx2_story.py        FFX2's 554 story/dialogue flags as raw data (address, bit,
                             description, chapter, location) - generated, not hand-written
save_data.py               SaveData class: load, get/set fields, save (handles platform header + checksum)
edit.py                      CLI: list / get / set fields on a save file
```

CLI, if you'd rather script it than use the GUI:

```
python3 edit.py list <path> <ffx|ffx2> <pc|vita|switch>
python3 edit.py get  <path> <ffx|ffx2> <pc|vita|switch> <field>
python3 edit.py set  <path> <ffx|ffx2> <pc|vita|switch> <field> <value> [--out <path>]
```

FFX's per-character core stats (HP/MP/Strength/etc) were a long-standing
gap, solved by finding that `FFXSaveEditor.java` (`gabacode/FFXED`, a
readable decompile) shares one stat-panel layout across all 18
party-member/aeon slots via a fixed 148-byte-per-slot offset delta
(taken straight from source, not guessed). That also revealed the
ability-unlock and "sensor perk" banks are per-character too, not the
single unlabeled global copy the field map exposed before - every
character/aeon now gets their own `{name}_ability_*`/`{name}_perk_*`
fields (e.g. `yuna_ability_cure`, `auron_current_hp`, `shiva_base_hp`).
FFX2's field map is still the more *trusted* one (clean, non-obfuscated
C# source vs. FFX's decompiled one), but FFX's is no longer
meaningfully narrower in scope.

## Story position / chapter rewinding

**FFX** stores story position as three plain fields: `room_number`,
`spawn_point`, and `storyline_progress` (source: `gabacode/FFXED`'s
"Game Coordinates" panel). `fields_ffx.py`'s `FFX_CHECKPOINTS` list has
15 known (room, spawn, progress) triples spanning the whole story -
opening, Besaid, Kilika, Luca, Operation Mi'ihen (+ aftermath), Djose
Temple, Guadosalam, Macalania Antechamber (just before Shiva/the
wedding), Bevelle, and the ending - sourced from search-engine snippets
of the PCSX2 forums' "FFX Game Coordinates" thread (the thread itself
blocks direct fetches, so treat these as good-confidence, not certain -
the `storyline_progress` values do climb in correct story order across
all of them, which is a decent cross-check that they're real). A few
entries don't have a known `storyline_progress` (flagged in the
checkpoint's status message after jumping) - the GUI leaves it
untouched in that case, which risks a room/progress mismatch. Always
keep the original save until you've confirmed the result in-game.

**FFX2** doesn't need any of this for a whole-chapter rewind: the game
has its own **official in-game Chapter Select** (unlocked from the
save/load screen once you've seen any ending) that jumps to any earlier
chapter on your existing save file - no editing, no risk to completion
stats. For rewinding to a *specific scene inside* a chapter, FFX2's
field map includes all 554 named story/dialogue flags from
`Meth962/FFX2SaveEditor`'s `GameInfo.cs` (`story_*`/`requisite_*`
fields in the Fields tab) - there's just no curated one-click list for
these the way FFX has, since 554 individual flags don't reduce to a
short list the same way a 3-field position does.

## Restoring to the Switch (JKSV)

1. Convert your save (via the GUI's Export tab, or `main.py` for
   batch/scripted conversion - see below).
2. Zip the converted file(s) up flat (no subfolder) alongside a
   `GameSettings` file - that's the layout JKSV expects. `GameSettings`
   is shared by both games and only needs to be included once per zip.
3. Copy the zip onto the SD card's real `JKSV/FINAL FANTASY X X-2 HD
   Remaster/` folder.
4. In JKSV, restore **that specific zip by name**. Double-check which
   zip you're restoring - restoring an old pre-existing backup instead
   of the freshly converted one is what silently loads old/first-sphere
   progress, and it's happened more than once in this project's own
   testing.
5. Load the save in-game, then save again at a sphere so the game
   writes its own fresh header/checksum over the placeholder one.

## Advanced: scripted conversion (`main.py`)

For batch conversion without the GUI, `main.py` is a single-file,
config-at-top-of-file script:

```
python3 main.py
```

It reads every file in `INPUT_DIR` matching `FILE_GLOB`, converts each
one, and writes the result to `OUTPUT_DIR`. Set `DRY_RUN = True` to
preview without writing anything. Current config converts FFX PC →
Switch:

```
GAME             = "ffx"
INPUT_PLATFORM   = "pc"
OUTPUT_PLATFORM  = "switch"
INPUT_DIR        = "./input/pc"
OUTPUT_DIR       = "./output/switch"
REFERENCE_SAVE   = "./reference/switch/ffx_001"
USE_REF_HEADER   = True
FILE_GLOB        = "ffx_*"
NAME_TEMPLATE    = "ffx_{index:03d}"
```

To convert FFX2 instead, flip: `GAME = "ffx2"`, `REFERENCE_SAVE =
"./reference/switch/ffx2_main_001"`, `FILE_GLOB = "ffx2_*"`,
`NAME_TEMPLATE = "ffx2_main_{index:03d}"`.

## Directory layout

```
reference/pc/       real PC saves, header + size source for pc-targeted conversions
reference/switch/    real Switch saves, header + size source (ffx2_main_001, ffx_001)
reference/vita/      real Vita save, for future vita conversions
assets/                logo.png + style.css served by the Dash app (app.py)
main.py                  the platform-conversion script (CONFIG-block driven)
app.py                    the Dash GUI
checksum.py, fields*.py,   field-editing layer - see "Field editing reference" above
  save_data.py, edit.py, platform_convert.py
```

`reference/` ships in this repo (see below) so conversion works right
out of the box. `input/`, `output/`, and `JKSV/` are your own local
working directories (git-ignored) - `input/pc/` for saves you're
converting, `output/` for converted results, `JKSV/` for zips staged to
restore onto a Switch. Create them as needed; `main.py`'s CONFIG block
and the commands above assume they sit alongside `app.py`/`main.py`
here in `python/`.

See [`../typescript/`](../typescript/README.md) for a client-side
(TypeScript) port of this whole app - no Python backend, static-hostable.

## Acknowledgments

This project builds on the reverse-engineering work of others:

- [`gabacode/FFXED`](https://github.com/gabacode/FFXED) - a readable
  FFX save editor decompile that supplied the per-character stat-panel
  layout (the 148-byte-per-slot delta shared across all 18 party/aeon
  slots) and the story-position field names (`room_number`,
  `spawn_point`, `storyline_progress`).
- [`Meth962/FFX2SaveEditor`](https://github.com/Meth962/FFX2SaveEditor) -
  clean, non-obfuscated C# source (`GameInfo.cs`) that the FFX2 field
  map (including all 554 story/dialogue flags) is sourced from.
- [JKSV](https://github.com/J-D-K/JKSV) - the Switch save manager this
  project's Switch-restore workflow is built around.

Thanks to all of them for doing the hard part first and publishing it.

## Open items

- Need a real FFX Vita save (a genuine matching save state, not just an
  unrelated same-size file) to properly confirm Vita ↔ PC/Switch
  conversion.
- FFX item/equipment/inventory isn't decoded yet (needs
  `ItemDisplayLabel`'s item-ID table from `gabacode/FFXED` - the raw
  178-slot, 22-bytes-per-slot region is known, just not its contents'
  meaning).
- Character name strings (FFX's `TextWithFontField`, a custom charmap)
  aren't exposed - out of scope for this project's numeric/bit field
  engine as it stands.
- A handful of FFX fields (`raw_*` in `fields_ffx.py`) are exposed as
  plain enum bytes without their friendly option labels decoded yet.
- ~~Client-side web version~~ - **done**, see [`../typescript/`](../typescript/README.md).
  A TypeScript port of this Dash app's full logic layer (checksum,
  field maps, platform conversion), matching it feature-for-feature,
  hostable as a static site (Cloudflare Pages or anywhere else) with no
  backend at all. Verified byte-identical to this Python implementation
  across every field and every conversion path before being trusted.
