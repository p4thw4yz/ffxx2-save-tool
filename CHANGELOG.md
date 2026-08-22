# Changelog

## Unreleased

**Restructured for the public GitHub release.** `v3/` is renamed
`typescript/` and the Python app moves into `python/`, as siblings at
the repo root - each with its own README. Real save files bundled as
conversion header/size templates (`reference/`) move to
`python/reference/` and stay in the repo (conversion needs them to work
out of the box); everything else that's personal save data (`input/`,
`output/`, `JKSV/`, `og from switch/`) is git-ignored, not deleted -
those directories still exist locally for day-to-day use, just outside
version control. Old ad-hoc zip snapshots (`ffxx2HD-tool-v*.zip`) are
dropped in favor of git history / GitHub Releases. Earlier entries below
predate this move and refer to the old flat layout (`v3/`,
`fields_ffx.py` instead of `python/fields_ffx.py`, etc).

**Added `v3/` - a client-side (TypeScript) port of the entire Dash app.**
No Python backend: runs entirely in the browser, static-hostable
(Cloudflare Pages or anywhere). Not a rewrite from scratch - a direct
port of this project's own logic:

- `checksum.ts`, `fields.ts`, `saveData.ts`, `platformConvert.ts` port
  `checksum.py`/`fields.py`/`save_data.py`/`platform_convert.py`
  line-for-line where the languages allow it (platformConvert.ts fetches
  its reference saves from `public/reference/` instead of reading local
  disk paths, since there's no filesystem in a browser).
- `v3/gen_fields.py` generates `src/lib/generated/fieldsFfx.ts` (3,116
  fields), `fieldsFfx2.ts` (632 fields), and `checkpoints.ts` (15 story
  checkpoints) directly from `fields_ffx.py`/`fields_ffx2.py` - the
  Python field maps stay the single source of truth, so the TS port can
  never silently drift out of sync with them. Re-run it after any future
  change to the Python field maps.
- UI: vanilla TypeScript + DOM (no framework), six tabs matching
  `app.py` exactly (Overview, Fields, Story Position, Export, Raw/Hex,
  Info), same blue/teal/pink visual theme ported to plain CSS.
- **Correctness, not just parity in spirit**: `v3/scripts/verify_parity.ts`
  loads the same real save files as the Python project and diffs every
  one of the 3,116 FFX + 632 FFX2 field values, plus a round-trip
  edit+checksum test, against JSON/binary dumps produced by the actual
  Python code. `verify_convert.ts` does the same for platform
  conversion (PC→Switch, both games). All checks passed byte-identical
  before any of this was trusted enough to build a UI on top of.
- Bug found and fixed *during* the port, not carried over from Python:
  TypeScript 6's `erasableSyntaxOnly` flag rejected the initial `enum
  Game {...}` and constructor parameter-property shorthand as
  non-erasable syntax - converted to a plain `as const` object type and
  explicit field assignments respectively. Also hit a "union type too
  complex" TS checker limit trying to structurally verify a 3,116-element
  typed array literal against `FieldDef` - worked around by having the
  generator emit a JSON string parsed at runtime instead of a literal
  array (the data was already Python-verified, so runtime parsing loses
  nothing).

**Cleaned up README.md** - it had grown into a chronological devlog
(separate "Findings/gotchas," duplicated JKSV warnings in two places,
a stray H3 for "PC vs. Vita," GUI walkthrough steps numbered from 0).
Reorganized around how people actually use the project now (GUI-first
quick start, a status table, then reference sections), consolidated the
duplicated JKSV-mix-up warning into one place, and moved the CLI/
`main.py` config path to a clearly-labeled "Advanced" section since the
GUI is the primary path. Nothing substantive was deleted - specific
details that didn't earn a place in the now-user-facing README (it's
rendered in-app via the Info tab, so it's read by end users, not just
contributors) moved to `notes.md` instead: the exact bad-zip names to
avoid in JKSV, the playtime-counter diagnostic that confirmed
`ffx2_000`/`ffx2_001` weren't a conversion bug, and the specific test
inputs behind the "confirmed working" FFX2 claim.

**Added an "Info" tab to the GUI** - renders `README.md` in-app via
`dcc.Markdown`, styled to match the theme (headers, tables, code blocks).
Loaded once from disk at startup (`load_readme()`); no callback needed
since it's static content. Point of this: the project overview is
always one click away instead of requiring the user to go find the
file themselves.

**Added an "Overview" tab to the GUI**, now the default landing tab. A
plain-language save summary instead of a raw field table: stat tiles
for Gil/play time/battles fought/story progress (with a "near:
<checkpoint>" guess computed from `FFX_CHECKPOINTS` by nearest reached
`storyline_progress`), plus a card per party member. Along the way,
found that FFX's `current_hp`/`base_hp` aren't a current/max pair the
way FFX2's `hp`/`max_hp` are - aeons have `base_hp=0` with a large,
real `current_hp`, so `base_hp` is shown as a separate bonus counter
rather than a misleading progress-bar denominator; FFX2's HP/MP bars
use real current/max pairs since that field map is independently
trustworthy (clean, non-obfuscated source).

**FFX field map expanded from 143 to 3,116 fields** - the long-standing
"per-character core stats not found" gap is closed. Went back to
`gabacode/FFXED`'s readable source and found `FFXSaveEditor.java` shares
ONE stat-panel field layout across all 18 party-member/aeon slots
(Tidus/Yuna/Auron/Kimahri/Wakka/Lulu/Rikku/Seymour + 10 aeons) via a
fixed 148-byte-per-slot offset delta, read straight from
`characterPanels` in the source - not inferred or guessed. Confirmed
against a real save: `tidus_current_hp`/`yuna_current_hp`/etc. all read
different, plausible values (thousands of HP, matching a save this deep
into the game), and `yuna_ability_cure` reads `True` while
`tidus_ability_cure` reads `False` - exactly right thematically (Yuna's
the healer). This also revealed the ability-unlock bank (22090) and
"sensor perk" bank (22164-22166) were ALSO per-character all along -
the old field map exposed only one unlabeled global copy of each
(silently just whichever character sits at delta 0), which was a real
correctness gap, not just a coverage one. Fixed two wrong field sizes
found in the process: `activation_type`/`overdrive_mode` were typed
`u16`, should be `u8` (a ComboBox's size is its first option's byte
length, which is 1 for both).

Also regex-extracted (not hand-transcribed, same approach as the FFX2
story flags) ~290 more GLOBAL (non-character) fields from the same
source: optional-boss-defeated flags, sidequest/treasure-chest state,
chocobo training times, key-item pickup flags (Al Bhed Primers,
celestial weapon parts), and a few raw enum bytes not yet decoded to
friendly option labels - now in `fields_ffx_extra.py` +
`fields_ffx.py`'s `flag_*`/`num_*`/`raw_*`/`cond_*` fields. Round-trip
tested (read/edit/write/reload/checksum) against the real reference
save - all correct, checksum self-consistent, output size unchanged.

Coverage of the raw file (per the new Raw/Hex tab, see below) jumped
from ~0.2% to ~7.1% for FFX as a result. Still not decoded: item/
equipment inventory (needs `ItemDisplayLabel`'s item-ID table) and
character name strings (custom charmap, out of scope for this project's
numeric/bit field engine).

`app.py`'s field categories were reworked to match: one category per
FFX party member (Tidus/Yuna/Auron/Kimahri/Wakka/Lulu/Rikku), one
shared "Aeons" category, "Flags" and "Misc" for the new global
extras - replacing the old "Ability"/"Perk" categories, which no
field name matches anymore now that every ability/perk is
character-prefixed.

**Added a "Raw / Hex" tab to the GUI.** A 16-bytes-per-row hex dump of
the whole file (`build_hex_rows` in `app.py`), cross-referenced against
`FFX_FIELDS`/`FFX2_FIELDS` so any row containing a known field shows its
name and current value inline, plus a coverage stat (bytes with at
least one known field / total bytes - honest and low: ~0.2% for FFX,
~0.8% for FFX2, since most of both files is still unidentified). One
search box filters offset/hex/ASCII/field-name at once via the
DataTable's `filter_query`. Point of this: turns "what's actually in
this file" from a hex-editor-and-guesswork exercise into something
searchable in the same tool used for editing.

Snapshotted the project as `ffxx2HD-tool-v2.0.0.zip` (whole directory
minus `.venv`/`__pycache__`/the old v1 zip) - supersedes
`ffxx2HD-tool-v1.0.0.zip`, which predates the entire field-editing
layer, GUI, and story-position work.

**`FFX_CHECKPOINTS` expanded from 7 to 15 entries**, spanning the whole
story instead of just the Macalania/Bevelle region: opening (Laughing
Scene), the boat to Besaid, two Besaid spots, Kilika, Luca, Operation
Mi'ihen (+ aftermath), Djose Temple, plus the originals (Guadosalam,
Macalania Antechamber, Bevelle, the ending). Cross-checked the new
storyline_progress values against each other before trusting them: they
climb in correct story order (0, 111, 294, 402, 815, 922, 971, 1096,
2130, 3400) across totally separate search results, which is good
evidence they're real rather than noise. One contradictory result (a
second "Ending" at progress 630, which would have to fall between Luca
and Operation Mi'ihen going by the others) was dropped for failing that
same check. Also gave the Dash GUI's dark-then-light theme rework its
own visual identity (blue/teal for FFX, pink/violet for FFX2, applied
throughout cards/buttons/table/tabs), a stacked centered header with the
user's own `logo.png` (real HD Remaster artwork, not something scraped -
copied into `assets/` so Dash serves it), and a category+search filter
above the fields table now that FFX2 alone has 632 fields.

**Story position / chapter-rewind editing added.** Found `gabacode/FFXED`,
a *readable* (non-obfuscated) decompile of FFXED - unlike the original
FFXED source, its `FFXSaveEditor.java` has named fields, including a
"Game Coordinates" panel: `room_number` (u16 @250), `spawn_point`
(u8 @248), `storyline_progress` (u16 @3116). Cross-checked against our
own real save (`ffx_004` read `room=194, spawn=2, progress=2915` -
plausible, non-garbage values, confirming these are real). Added to
`fields_ffx.py`, plus an `FFX_CHECKPOINTS` list of known (room, spawn,
progress) triples for real story beats, sourced from search-engine
snippets of the PCSX2 forums "FFX Game Coordinates" thread (the thread
itself blocks direct fetches - Steam/GameFAQs/PCSX2-forums all 403
WebFetch, so this was pieced together from search result snippets, not
one clean source table). Used this to build a save at the "Macalania
Antechamber, just before Shiva/the wedding" checkpoint for a real
rewind request this session - see `output/switch/
ffx_004_macalania_antechamber` and `JKSV/.../converted_story_rewind.zip`.

Also found that `Meth962/FFX2SaveEditor`'s `Models/GameInfo.cs` ships a
fully named list of 555 individual story/dialogue flags (`(address,
bitmask, description, chapter, location)`), addressed relative to a
16KB story-flag region at body offset `0x222C` (`Saves/Ffx2Save.cs`:
`storyOffset=0x222c`). Parsed via a regex script (not hand-transcribed)
into `fields_ffx2_story.py` (554 usable entries - one upstream entry had
a non-power-of-two bitmask, a likely source typo, and was dropped) and
wired into `fields_ffx2.py` as `story_*`/`requisite_*` bit fields.
Confirmed FFX2 has an **official in-game Chapter Select** (unlocked
after any ending) for whole-chapter rewinds on an existing save with no
editing needed at all - these 554 flags are only useful for rewinding
to a specific scene *inside* a chapter, past what Chapter Select offers.

`app.py` got a new "Story position (FFX only)" panel: a dropdown of
`FFX_CHECKPOINTS` plus a "Jump to checkpoint" button that sets all three
story fields in one click (new `jump_to_checkpoint` callback, tested
the same in-process way as the other multi-output callbacks). Also
added a "Story" category so `room_number`/`spawn_point`/
`storyline_progress` (FFX) and `story_*`/`requisite_*` (FFX2) group
together in the field table instead of falling into the generic "Core"
bucket.

**Dash GUI added (`app.py`, `platform_convert.py`, `requirements.txt`).**
Upload a save, browse/edit every known field in a searchable table, apply
edits (checksum recomputed for both games), download the result, or
convert it to another platform - all from one local web app instead of
editing `main.py`'s CONFIG block or using the CLI. `platform_convert.py`
generalizes main.py's header/size logic into a pure function driven by
this project's own bundled reference saves. Tested end-to-end (in-process,
calling the actual callback functions directly - the manual HTTP harness
used to probe it hit Dash's internal duplicate-output request signing,
not a bug in the app): upload+auto-detect, field edit, checksum
self-consistency after edit, download, and platform conversion (PC→Switch
size came out exactly right, matching the already-validated math).

**FFX2 checksum cracked.** Found MarkH221/FFX-HD-Checksum-Utility (a
dedicated HD Remaster tool covering both games) - its FFX end-offset
(`0x64f8`) matched what we'd already validated, and its FFX2 end-offset
(`0x1626C`) turned out to be 4 bytes different from the older
PS2-International-Edition forum number (`0x16270`) the first attempt
used. With the corrected offset, recomputing the checksum against both
real FFX2 reference saves (PC and Switch) now matches exactly.
`checksum.py` and `save_data.py` updated - both games now get a
real, automatically-recomputed checksum on edit, no in-game
save-and-reload workaround needed for either.

Searched further for FFX's core party stats (HP/MP/Strength/Level - the
FFX equivalent of FFX2's clean Character block) - no luck. Every guide
and tool found points users to the FFXED GUI rather than documenting raw
offsets, and FFXED's own decompiled source doesn't expose them either.
Still an open item; would need an empirical diff session (e.g. compare
saves before/after a known stat change) rather than a source-mining one.
(**Resolved later in this same session** - see the "FFX field map
expanded from 143 to 3,116 fields" entry above; the source that finally
exposed this was `gabacode/FFXED`, a *different, readable* decompile
found afterward, not the original obfuscated FFXED source referenced
here.)

Added field-level reading and editing, on top of platform conversion.

- Researched and cloned five open-source FFX/FFX2 community save editors
  (FFXED, FFX2SaveEditor, mrhappyasthma's cross-platform Python converter,
  FFXProjectEditor, Farplane) to mine their reverse-engineered save format
  knowledge — no license files present in any of them, but shared publicly
  for the community, so treated as fair to build on.
- **`checksum.py`** — ported the CRC-16 checksum algorithm (source:
  mrhappyasthma's converter). FFX validated: recomputing the checksum for
  our real reference saves (both PC and Switch) reproduces the exact
  bytes already stored in those files. FFX2 not cracked — two different
  community-sourced offset sets both failed against our real FFX2 saves
  (though both of FFX2's stored checksum copies do agree with each
  other, confirming the pattern is real, just at an unconfirmed offset).
- **`fields.py` / `fields_ffx.py` / `fields_ffx2.py`** — byte-offset field
  maps transcribed from FFXED (FFX, decompiled Java, ability/perk bits —
  137 fields) and FFX2SaveEditor (FFX2, clean C# source, full party stats
  — confirmed `gametime_seconds` field reproduced a previously
  hand-derived value exactly: 1475, matching the manual playtime-counter
  analysis from the v1.0.0 investigation).
- **`save_data.py`** — `SaveData` class: load a save, get/set fields by
  name, save back out with platform header and (FFX only) checksum
  handled automatically.
- **`edit.py`** — CLI for listing/getting/setting fields. Round-trip
  tested: edited FFX fields persist and the recomputed checksum is
  self-consistent, so an edited FFX save no longer needs the "load and
  save once in-game" workaround. FFX2 edits persist but still need that
  workaround until its checksum is cracked.

## v1.0.0 — 2026-08-20

First working release. Converts FINAL FANTASY X / X-2 HD Remaster save
files between PC and Switch by adding/stripping an 8-byte platform header
and matching the target platform's file size.

### Confirmed working (tested on real Switch hardware)

- **FFX2 PC → Switch** — real Steam progress saves and a 100%-completed
  save all convert and load correctly.
- **FFX PC → Switch** — converted PC save loads and plays correctly.

### Key findings

- Both games use an 8-byte Switch header (first 4 bytes little-endian Unix
  timestamp, last 4 zero) prepended to the PC save body. The game rewrites
  this header itself on next in-game save, so the exact bytes don't matter
  as long as a real reference save is used to seed a plausible one.
- **FFX2**: header is a straight prepend — total size grows by exactly 8
  bytes (91808 → 91816).
- **FFX**: total size stays the same (26880 → 26880) — the PC body ends in
  8 bytes of zero padding that get trimmed to make room for the header.
  `main.py`'s size-fitting logic already handled this correctly once a real
  reference save was available; no special-casing was needed.
- Real Switch save naming differs by game: FFX2 saves are `ffx2_main_000`,
  `ffx2_main_001`, ...; FFX saves are `ffx_000`, `ffx_001`, ... (no
  `_main_`). Confirmed against real files pulled off the SD card.
- `GameSettings` is a single shared file per game title (not per save) —
  one copy in a JKSV restore zip covers both FFX and FFX2 saves.

### Known gotchas

- JKSV restore mix-ups: restoring an old pre-existing backup zip instead of
  the freshly converted one silently loads old/first-sphere progress —
  always restore the correctly-named, freshly-built zip.
- An early FFX attempt used a placeholder (non-real) header with no
  reference save, produced a save 8 bytes too large, and failed to load.
  Kept around (`og from switch/ffx_main_000`,
  `output/switch_ffx_UNVERIFIED/`, `converted_ffx_UNVERIFIED.zip`) for
  reference only — not used by the current config.

### Not yet done

- Vita ↔ PC/Switch conversion is untested with a genuine matching save
  state — only an unrelated-file container-format comparison (same size,
  no extra header) has been done so far. Still need a real FFX Vita save
  (~25%-progress playthrough) as a proper test input.
- Switch → PC direction uses the same header strip/fit logic symmetrically
  but hasn't been field-tested (only PC → Switch has been loaded on real
  hardware so far).

### Planned

- Once Vita is validated, wrap this into a proper Python app or web UI
  instead of the current config-block script.
