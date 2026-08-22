"""
FFX2 field map.

Source: reverse-engineered offsets transcribed from Meth962/FFX2SaveEditor
(Saves/Ffx2Save.cs, ReadFile method) - a clean, actively-maintained C#
save editor with named properties, not obfuscated. Not independently
byte-verified against our own saves the way checksum.py's FFX path was,
but the offsets read directly off working editor source, not a guess.

All offsets are relative to the start of the core save body (no platform
header). Confirmed real body size: 91808 bytes (PC).

Also includes 554 individual story/dialogue flags (fields_ffx2_story.py,
named "story_*"/"requisite_*") - one bit each, per real named event, not a
coarse position like FFX's room/spawn/storyline_progress. FFX2 doesn't
need save-editing for a whole-chapter rewind though: the game has an
official in-game Chapter Select menu (unlocked once you've seen an
ending) that jumps to any earlier chapter on the same save file, no risk
to completion stats. These story flags are only useful for rewinding to
a specific scene *inside* a chapter, past what Chapter Select offers.
"""

import re

from fields import Field, bit_field
from fields_ffx2_story import STORY_FLAG_BASE, STORY_FLAGS

CHARACTER_NAMES = ["yuna", "rikku", "paine"]
_CHAR_BASE = 0x8204
_CHAR_STRIDE = 0x80


def _character_fields(index, key):
    off = _CHAR_BASE + index * _CHAR_STRIDE
    p = f"{key}_"
    return [
        Field(p + "experience", off + 0x00, "u32"),
        Field(p + "next_level_exp", off + 0x04, "u32"),
        Field(p + "hp", off + 0x08, "u32"),
        Field(p + "mp", off + 0x0C, "u32"),
        Field(p + "max_hp", off + 0x10, "u32"),
        Field(p + "max_mp", off + 0x14, "u32"),
        Field(p + "strength", off + 0x19, "u8"),
        Field(p + "defense", off + 0x1A, "u8"),
        Field(p + "magic", off + 0x1B, "u8"),
        Field(p + "magic_defense", off + 0x1C, "u8"),
        Field(p + "agility", off + 0x1D, "u8"),
        Field(p + "accuracy", off + 0x1E, "u8"),
        Field(p + "evasion", off + 0x1F, "u8"),
        Field(p + "luck", off + 0x20, "u8"),
        Field(p + "level", off + 0x21, "u8"),
        Field(p + "dressphere", off + 0x22, "u8"),
    ]


FFX2_FIELDS = [
    Field("gametime_seconds", 0x10, "u32"),
    Field("gil", 0x7818, "i32"),
    Field("encounters", 0x7824, "u32"),
    Field("open_air_credits", 0x2EC, "u32"),
    Field("argent_credits", 0x2F0, "u32"),
    Field("successful_digs", 0x340, "u32"),
    Field("failed_digs", 0x344, "u32"),
    Field("gunner_points", 0x3B0, "u32"),
    Field("sl_credits_ch5", 0x4B4, "u32"),
    Field("hover_rides", 0x4C1, "u32"),
    Field("chocobo_success_0", 0x4C7, "u8"),
    Field("chocobo_success_1", 0x4C8, "u8"),
    Field("chocobo_success_2", 0x4C9, "u8"),
    Field("chocobo_success_3", 0x4CA, "u8"),
    Field("chocobo_success_4", 0x4CB, "u8"),
    Field("faction", 0xC55, "u8", note="Youth League / New Yevon standing"),
    Field("pahsana_greens", 0xD0C, "u32"),
    Field("mimett_greens", 0xD10, "u32"),
    Field("sylkis_greens", 0xD14, "u32"),
    Field("gysahl_greens", 0xD18, "u32"),
    Field("kimahri_self_esteem_ch2", 0xDB8, "u32"),
    Field("kimahri_self_esteem", 0xDBC, "u32"),
    Field("open_air_points", 0xDE4, "u32"),
    Field("argent_points", 0xDE8, "u32"),
    Field("marriage_points", 0xDEC, "u32"),
    Field("sl_credits", 0xDF0, "u32"),
    Field("chapter", 0x118C, "u8"),
    Field("oaka_debt", 0x1194, "f32"),
    Field("al_bhed_primer_count", 0x11A6, "u8"),
    Field("al_bhed_master", 0x11A7, "u8"),
]

for _i, _key in enumerate(CHARACTER_NAMES):
    FFX2_FIELDS.extend(_character_fields(_i, _key))


def _slugify(description, seen):
    slug = re.sub(r"[^a-z0-9]+", "_", description.lower()).strip("_")[:40].strip("_") or "flag"
    name, n = slug, 2
    while name in seen:
        name = f"{slug}_{n}"
        n += 1
    seen.add(name)
    return name


_seen_story_names = set()
for _addr, _bit, _desc, _chapter, _location, _is_req in STORY_FLAGS:
    _slug_name = _slugify(_desc, _seen_story_names)
    _kind = "requisite" if _is_req else "story"
    FFX2_FIELDS.append(
        bit_field(
            f"{_kind}_{_slug_name}",
            STORY_FLAG_BASE + _addr,
            _bit,
            note=f"ch{_chapter} {_location}: {_desc}",
        )
    )

FFX2_FIELDS_BY_NAME = {f.name: f for f in FFX2_FIELDS}
