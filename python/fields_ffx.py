"""
FFX field map.

Source: reverse-engineered offsets transcribed/extracted from
gabacode/FFXED - a *readable* (non-obfuscated) decompile of FFXED, unlike
the original fuzzymillipede FFXED.jar (fully obfuscated). Two mechanical
rules, both confirmed straight from the source, not guessed:

    bit fields:     byte_offset = base_offset + bit_index // 8
                     bit         = bit_index % 8            (BitFieldAccessor.java)
    numeric fields:  plain little-endian N-byte read at an absolute offset
                                                              (NumericInputField.java)

PER-CHARACTER STATS - the long-standing gap ("HP/MP/Strength/Level, the
FFX equivalent of FFX2's clean Character block") is now found. FFXSaveEditor
.java's character-select combo (`this.characterPanels`) shares ONE set of
stat-panel fields across 18 party-member/aeon slots by shifting every
field's offset by a fixed per-slot delta (148 bytes/slot) - see
CHARACTER_DELTAS below, taken verbatim from the source, not inferred. This
also means the ability-unlock bank (offset 22090) and the "sensor
perk"/personality-counter bank (22164-22166, labels Stoic/Warrior/Comrade/
...) - previously exposed as ONE unlabeled global instance - are actually
per-character too; every character/aeon now gets its own
`{name}_ability_*` / `{name}_perk_*` fields instead of one ambiguous
shared copy (this was a real correctness gap in the old field map, not
just a coverage gap: editing e.g. `ability_cure` silently only ever
affected whichever character happened to be at delta 0/Tidus).

`fields_ffx_extra.py` holds ~290 additional GLOBAL (non-character) fields
regex-extracted the same way: optional-boss-defeated flags, sidequest/
chest state, chocobo training times, key-item pickup flags, and a few raw
enum bytes not yet decoded to friendly option labels.

room_number/spawn_point/storyline_progress (the "Game Coordinates" panel,
source lines ~2431-2435) are the fields the game itself uses to know
where to place the party and which story checkpoint has been reached -
see FFX_CHECKPOINTS below for known real-location example triples
(community-sourced via search, not independently verified - see its own
comment).

Two fields were fixed from earlier (wrong) guesses: `activation_type` and
`overdrive_mode` were previously typed `u16`; the real size is `u8`
(ComboBoxPanel's size = its first option's byte-array length, which is 1
for both of these) - confirmed from source this session, now correct AND
per-character.

Still not found: full item/equipment/inventory decoding (the 178-slot,
22-bytes-per-slot item list starting near offset 0/484 needs
ItemDisplayLabel's item-ID table, not yet pulled in) and character name
strings (TextWithFontField, a custom charmap - out of scope for the
numeric/bit Field engine this project uses).

All offsets are relative to the start of the core save body (no platform
header). Confirmed real body size: 26880 bytes (PC/Switch).
"""

import re

from fields import Field, bit_field
from fields_ffx_extra import CHECKBOXES, COMBOS_RAW_U8, CONDITIONAL_BITS, NUMERIC

# 18 party-member/aeon slots share one stat-panel layout, each shifted by
# this per-slot byte delta (from characterPanels in FFXSaveEditor.java -
# verbatim from source, not inferred).
CHARACTER_DELTAS = [
    ("tidus", 0), ("yuna", 148), ("auron", 296), ("kimahri", 444),
    ("wakka", 592), ("lulu", 740), ("rikku", 888), ("seymour", 1036),
    ("valefor", 1184), ("ifrit", 1332), ("ixion", 1480), ("shiva", 1628),
    ("bahamut", 1776), ("anima", 1924), ("yojimbo", 2072),
    ("cindy", 2220), ("sandy", 2368), ("mindy", 2516),
]
PLAYABLE_CHARACTERS = {"tidus", "yuna", "auron", "kimahri", "wakka", "lulu", "rikku"}

# "Command/ability" bank - 96 bits starting at this offset (Tidus/delta=0).
_ABILITY_BANK_REL = 22090
_ABILITY_BITS = [
    ("attack", 0), ("item", 1), ("switch", 2), ("escape", 3), ("weapon", 4),
    ("armor", 5), ("delay_attack", 6), ("delay_buster", 7),
    ("sleep_attack", 8), ("silence_attack", 9), ("dark_attack", 10),
    ("zombie_attack", 11), ("sleep_buster", 12), ("silence_buster", 13),
    ("dark_buster", 14), ("triple_foul", 15),
    ("power_break", 16), ("magic_break", 17), ("armor_break", 18),
    ("mental_break", 19), ("mug", 20), ("quick_hit", 21), ("steal", 22),
    ("use", 23), ("flee", 24), ("pray", 25), ("cheer", 26), ("aim", 27),
    ("focus", 28), ("reflex", 29), ("luck", 30), ("jinx", 31),
    ("lancet", 32), ("defend", 33), ("guard", 34), ("sentinel", 35),
    ("spare_change", 36), ("threaten", 37), ("provoke", 38), ("entrust", 39),
    ("copycat", 40), ("doublecast", 41), ("bribe", 42), ("cure", 43),
    ("cura", 44), ("curaga", 45), ("nulfrost", 46), ("nulblaze", 47),
    ("nulshock", 48), ("nultide", 49), ("scan", 50), ("esuna", 51),
    ("life", 52), ("full_life", 53), ("haste", 54), ("hastega", 55),
    ("slow", 56), ("slowga", 57), ("shell", 58), ("protect", 59),
    ("reflect", 60), ("dispel", 61), ("regen", 62), ("holy", 63),
    ("auto_life", 64), ("blizzard", 65), ("fire", 66), ("thunder", 67),
    ("water", 68), ("fira", 69), ("blizzara", 70), ("thundara", 71),
    ("watera", 72), ("firaga", 73), ("blizzaga", 74), ("thundaga", 75),
    ("waterga", 76), ("bio", 77), ("demi", 78), ("death", 79),
    ("drain", 80), ("osmose", 81), ("flare", 82), ("ultima", 83),
    ("shield", 84), ("boost", 85), ("dismiss", 86),
    ("pilfer_gil", 88), ("full_break", 89), ("extract_power", 90),
    ("extract_mana", 91), ("extract_speed", 92), ("extract_ability", 93),
    ("nab_gil", 94), ("quick_pockets", 95),
]
ABILITY_NAMES = [name for name, _ in _ABILITY_BITS]

# "Sensor perk" / personality-counter bank - a learned-flag bit (byte
# 22164-22166, Tidus/delta=0) and a paired 2-byte count (22124-22162).
# Semantics of the individual names (Stoic/Warrior/Comrade/...) aren't
# confirmed beyond what FFXED itself labels them; the container panel
# they're read from is oddly titled "Overdrive Modes" in this decompile
# (likely a decompiler variable-reuse artifact), but the labels match the
# community term "sensor perks"/personality counters, kept here.
_PERK_BANK_REL = 22164
_PERKS = [
    ("warrior", 0, 22124), ("comrade", 1, 22126), ("stoic", 2, 22128),
    ("healer", 3, 22130), ("tactician", 4, 22132), ("victim", 5, 22134),
    ("dancer", 6, 22136), ("avenger", 7, 22138),
]
_PERK_BANK_2_REL = 22165
_PERKS_2 = [
    ("slayer", 0, 22140), ("hero", 1, 22142), ("rook", 2, 22144),
    ("victor", 3, 22146), ("coward", 4, 22148), ("ally", 5, 22150),
    ("sufferer", 6, 22152), ("daredevil", 7, 22154),
]
_PERK_BANK_3_REL = 22166
_PERKS_3 = [
    ("loner", 0, 22156), ("unknown_perk_1", 1, 22158),
    ("unknown_perk_2", 2, 22160), ("aeons_only", 3, 22162),
]

# (name, offset_rel, kind) - per-character numeric stats, offsets relative
# to Tidus/delta=0, from FFXSaveEditor.java's `this.aT` stat panel.
_CHAR_NUMERIC_REL = [
    ("base_hp", 22032, "u32"),
    ("base_mp", 22036, "u32"),
    ("base_strength", 22040, "u8"),
    ("base_defense", 22041, "u8"),
    ("base_magic", 22042, "u8"),
    ("base_magic_defense", 22043, "u8"),
    ("base_agility", 22044, "u8"),
    ("base_luck", 22045, "u8"),
    ("base_evasion", 22046, "u8"),
    ("base_accuracy", 22047, "u8"),
    ("ability_points", 22052, "u32"),
    ("current_hp", 22056, "u32"),
    ("current_mp", 22060, "u32"),
    ("activation_type", 22072, "u8"),  # ComboBox: 17=Enabled, 16=Disabled, 0=Inactivated
    ("poison_damage_percent", 22083, "u8"),
    ("overdrive_mode", 22084, "u8"),  # ComboBox, see gabacode-ffxed hArray4 for the name table
    ("overdrive_gauge", 22085, "u8"),
    ("overdrive_gauge_max", 22086, "u8"),  # labelled "/" next to overdrive_gauge in the source UI
    ("sphere_level", 22087, "u8"),
    ("sphere_level_max", 22088, "u8"),  # labelled "/" next to sphere_level in the source UI
    ("enemies_defeated", 22112, "u32"),
    ("affection_raw", 108, "u32", "hidden affection system; display scaling not confirmed"),
]


def _character_fields(name, delta):
    fields = []
    for entry in _CHAR_NUMERIC_REL:
        fname, off_rel, kind = entry[0], entry[1], entry[2]
        note = entry[3] if len(entry) > 3 else ""
        fields.append(Field(f"{name}_{fname}", off_rel + delta, kind, note=note))
    for _bit_name, _bit in _ABILITY_BITS:
        fields.append(bit_field(f"{name}_ability_{_bit_name}", _ABILITY_BANK_REL + delta, _bit))
    for _bank_rel, _perks in ((_PERK_BANK_REL, _PERKS), (_PERK_BANK_2_REL, _PERKS_2), (_PERK_BANK_3_REL, _PERKS_3)):
        for _perk_name, _bit, _count_off_rel in _perks:
            fields.append(bit_field(f"{name}_perk_{_perk_name}_learned", _bank_rel + delta, _bit))
            fields.append(Field(f"{name}_perk_{_perk_name}_count", _count_off_rel + delta, "u16"))
    return fields


FFX_FIELDS = [
    Field("spawn_point", 248, "u8", note="which entry point within room_number to appear at"),
    Field("room_number", 250, "u16", note="current map/room - see FFX_CHECKPOINTS for known example values"),
    Field("game_time_seconds", 252, "u32"),
    Field("gil_donated_oaka", 3168, "u32"),
    Field("storyline_progress", 3116, "u16", note="story checkpoint gate - see FFX_CHECKPOINTS for known example values"),
    Field("battles_fought", 15700, "u32"),
    Field("gil", 15752, "u32"),
    Field("yojimbo_compatibility", 15844, "u8"),
    Field("yojimbo_compatibility_mode", 15848, "u8", note="ComboBox raw byte: 0/1/2 = modes 1/2/3"),
    Field("tidus_overdrive_count", 15852, "u32"),
]
_HAND_COVERED_OFFSETS = {f.offset for f in FFX_FIELDS}

for _char_name, _delta in CHARACTER_DELTAS:
    FFX_FIELDS.extend(_character_fields(_char_name, _delta))


def _slugify(description, seen):
    slug = re.sub(r"[^a-z0-9]+", "_", description.lower()).strip("_")[:40].strip("_") or "flag"
    name, n = slug, 2
    while name in seen:
        name = f"{slug}_{n}"
        n += 1
    seen.add(name)
    return name


_seen_extra_names = set()

for _label, _offset, _bit, _invert in CHECKBOXES:
    if _offset in _HAND_COVERED_OFFSETS:
        continue
    _name = "flag_" + _slugify(_label, _seen_extra_names)
    FFX_FIELDS.append(bit_field(_name, _offset, _bit, note=_label if not _invert else f"{_label} (inverted: bit clear = true)"))

for _label, _offset, _size in NUMERIC:
    if _offset in _HAND_COVERED_OFFSETS:
        continue
    _kind = {1: "u8", 2: "u16", 4: "u32"}.get(_size, "u8")
    _name = "num_" + _slugify(_label, _seen_extra_names)
    FFX_FIELDS.append(Field(_name, _offset, _kind, note=_label))

for _label, _offset, _var in COMBOS_RAW_U8:
    if _offset in _HAND_COVERED_OFFSETS:
        continue
    _name = "raw_" + _slugify(_label, _seen_extra_names)
    FFX_FIELDS.append(Field(_name, _offset, "u8", note=f"{_label} (raw enum byte, options table {_var} not decoded)"))

for _label, _offset, _bit, _invert, _has_extra in CONDITIONAL_BITS:
    if _offset in _HAND_COVERED_OFFSETS:
        continue
    _name = "cond_" + _slugify(_label, _seen_extra_names)
    _note = _label
    if _has_extra:
        _note += " (conditional in original editor - gated on a prerequisite bit not modeled here)"
    FFX_FIELDS.append(bit_field(_name, _offset, _bit, note=_note))

FFX_FIELDS_BY_NAME = {f.name: f for f in FFX_FIELDS}

# Known (room_number, spawn_point, storyline_progress) triples, sourced from
# search-engine snippets of the PCSX2 forums "FFX Game Coordinates" thread
# (the thread itself 403s on direct fetch, so this is what search snippets
# surfaced, not a verified full transcript). storyline_progress marked None
# means it wasn't found - jump_to_checkpoint (app.py) leaves the save's
# current storyline_progress untouched in that case, which risks a mismatch
# between "where you are" (room) and "how far the story thinks you are"
# (progress); treat those entries as less turnkey than the rest.
#
# The storyline_progress values below climb in real story order (0 -> 111 ->
# 294 -> 402 -> 815 -> 922 -> 971 -> 1096 -> 2130 -> 3400), which is a good
# cross-check that they're real and self-consistent, not noise - one
# search result claiming a second, contradictory "Ending" at progress 630
# was dropped for exactly this reason (630 would have to fall between Luca
# and Operation Mi'ihen, nowhere near an ending).
FFX_CHECKPOINTS = [
    # (label, room_number, spawn_point, storyline_progress, note)
    ("Debug Room", 1, 0, None, "community-sourced"),
    ("Auron Room (New Game+ start)", 2, 0, None, "community-sourced"),
    ("Laughing Scene (opening)", 132, 0, 0, "community-sourced"),
    ("Unknown Sea (boat to Besaid, prologue)", 70, 0, 111, "community-sourced"),
    ("Besaid - Crusaders' Lodge", 60, 1, None, "community-sourced, storyline_progress not found"),
    ("Besaid - Promontory", 67, 3, None, "community-sourced, storyline_progress not found"),
    ("Kilika", 43, 2, 294, "community-sourced"),
    ("Near Luca", 267, 0, 402, "community-sourced"),
    ("Operation Mi'ihen", 128, 2, 815, "community-sourced"),
    ("Operation Mi'ihen Aftermath", 131, 3, 922, "community-sourced"),
    ("Djose Temple", 82, 7, 971, "community-sourced"),
    ("Guadosalam (after Seymour's proposal, before Thunder Plains)", 243, 1, 1096, "community-sourced"),
    ("Macalania Antechamber (before Shiva/the wedding)", 80, 0, 1096, "room+progress community-sourced, spawn_point unconfirmed guess"),
    ("Bevelle - Passage of Cleansing", 305, 2, 2130, "community-sourced"),
    ("Ending (right before Auron's sending scene)", 325, 0, 3400, "community-sourced"),
]
FFX_CHECKPOINTS_BY_LABEL = {c[0]: c for c in FFX_CHECKPOINTS}
