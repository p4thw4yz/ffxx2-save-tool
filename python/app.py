#!/usr/bin/env python3
"""
FFX / FFX2 HD Remaster save tool - Dash GUI.

Upload a save, inspect and edit its fields, download it back with a valid
checksum, or convert it to a different platform. Wraps checksum.py,
save_data.py and platform_convert.py - see README.md for how those were
validated.

Run with:  python3 app.py
"""

import base64
import os

from dash import Dash, Input, Output, State, dash_table, dcc, html, no_update

from checksum import Game
from fields_ffx import ABILITY_NAMES, FFX_CHECKPOINTS, FFX_FIELDS
from fields_ffx2 import FFX2_FIELDS
from platform_convert import convert_platform
from save_data import HEADER_LEN, SaveData, coerce_value

_README_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md")


def load_readme():
    try:
        with open(_README_PATH, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return "*README.md not found next to app.py.*"


README_CONTENT = load_readme()

FFX_PARTY_ORDER = ["tidus", "yuna", "auron", "kimahri", "wakka", "lulu", "rikku"]
FFX2_PARTY_ORDER = ["yuna", "rikku", "paine"]
_ACTIVATION_LABELS = {17: "Active", 16: "Reserve", 0: "Inactive"}

GAME_LABELS = {"ffx": Game.FFX, "ffx2": Game.FFX2}
GAME_NAMES = {Game.FFX: "ffx", Game.FFX2: "ffx2"}
PLATFORMS = ["pc", "vita", "switch"]
_FFX_CHARACTERS = ["tidus", "yuna", "auron", "kimahri", "wakka", "lulu", "rikku"]
_FFX_AEONS = ["seymour", "valefor", "ifrit", "ixion", "shiva", "bahamut", "anima", "yojimbo", "cindy", "sandy", "mindy"]
CATEGORIES = [
    "All", "Core", "Story", "Flags", "Misc",
    "Tidus", "Yuna", "Auron", "Kimahri", "Wakka", "Lulu", "Rikku", "Paine", "Aeons",
]
FIELD_LISTS = {"ffx": FFX_FIELDS, "ffx2": FFX2_FIELDS}
_KIND_SIZE = {"u8": 1, "u16": 2, "u32": 4, "i32": 4, "f32": 4, "bit": 1}
HEX_ROW_WIDTH = 16


def guess_game(size):
    return "ffx2" if size > 50000 else "ffx"


def guess_platform(raw):
    """Heuristic: a Switch header's first 4 bytes are a little-endian Unix
    timestamp (roughly year 2000-2040) followed by 4 zero bytes."""
    if len(raw) >= 8:
        stamp = int.from_bytes(raw[0:4], "little")
        tail_zero = raw[4:8] == b"\x00\x00\x00\x00"
        if tail_zero and 946684800 <= stamp <= 2208988800:
            return "switch"
    return "pc"


def category_of(name):
    if name in ("room_number", "spawn_point", "storyline_progress"):
        return "Story"
    for prefix, label in (
        ("paine_", "Paine"),
        ("story_", "Story"),
        ("requisite_", "Story"),
        ("flag_", "Flags"),
        ("cond_", "Flags"),
        ("num_", "Misc"),
        ("raw_", "Misc"),
    ):
        if name.startswith(prefix):
            return label
    for char in _FFX_CHARACTERS:
        if name.startswith(char + "_"):
            return char.capitalize()
    for aeon in _FFX_AEONS:
        if name.startswith(aeon + "_"):
            return "Aeons"
    return "Core"


def build_table_rows(sd: SaveData):
    rows = []
    for name, value in sorted(sd.fields().items()):
        rows.append({"category": category_of(name), "field": name, "value": value})
    return rows


def build_hex_rows(sd: SaveData, game_s):
    """One row per 16-byte chunk of the raw file, annotated with any known
    fields (from FIELD_LISTS) whose bytes fall in that chunk, name=value."""
    raw = bytes(sd.data)
    field_list = FIELD_LISTS[game_s]
    values = sd.fields()

    row_notes = {}
    covered = set()
    for f in field_list:
        abs_off = sd.header_len + f.offset
        size = _KIND_SIZE[f.kind]
        covered.update(range(abs_off, abs_off + size))
        row_notes.setdefault(abs_off // HEX_ROW_WIDTH, []).append(f"{f.name}={values[f.name]}")

    rows = []
    for start in range(0, len(raw), HEX_ROW_WIDTH):
        chunk = raw[start : start + HEX_ROW_WIDTH]
        rows.append(
            {
                "offset": f"0x{start:05x}",
                "hex": " ".join(f"{b:02x}" for b in chunk),
                "ascii": "".join(chr(b) if 32 <= b < 127 else "." for b in chunk),
                "fields": ", ".join(row_notes.get(start // HEX_ROW_WIDTH, [])),
            }
        )
    coverage = f"{len(covered) / len(raw) * 100:.1f}%" if raw else "0%"
    summary = f"{len(raw):,} bytes total - {len(field_list)} known fields covering {coverage} of the file."
    return rows, summary


def format_hms(total_seconds):
    total_seconds = int(total_seconds or 0)
    h, rem = divmod(total_seconds, 3600)
    m, _s = divmod(rem, 60)
    return f"{h}h {m}m"


def format_int(n):
    return f"{n:,}"


def stat_tile(label, value, sub=None):
    children = [html.Div(label, className="stat-tile-label"), html.Div(value, className="stat-tile-value")]
    if sub:
        children.append(html.Div(sub, className="stat-tile-sub"))
    return html.Div(className="stat-tile", children=children)


def mini_bar(current, maximum, color_class):
    pct = 0 if not maximum else max(0, min(100, current / maximum * 100))
    return html.Div(className="mini-bar", children=html.Div(className=f"mini-bar-fill {color_class}", style={"width": f"{pct:.0f}%"}))


def bar_row(label, current, maximum, color_class):
    """maximum=None means there's no confirmed max for this stat (e.g. FFX's
    current_hp isn't paired with a real max_hp field) - show the plain value
    instead of a current/max bar that could otherwise overflow or mislead."""
    if maximum is None:
        value = html.Span(format_int(current), className="party-card-bar-value")
    else:
        value = html.Span(f"{format_int(current)} / {format_int(maximum)}", className="party-card-bar-value")
    children = [html.Span(label, className="party-card-bar-label")]
    if maximum is not None:
        children.append(mini_bar(current, maximum, color_class))
    else:
        children.append(html.Div())  # keep the label/value grid columns aligned
    children.append(value)
    return html.Div(className="party-card-bar-row", children=children)


def party_card(name, subtitle, hp, max_hp, mp, max_mp, extra_lines=None):
    children = [
        html.Div(name.capitalize(), className="party-card-name"),
        html.Div(subtitle, className="party-card-sub"),
        bar_row("HP", hp, max_hp, "bar-hp"),
        bar_row("MP", mp, max_mp, "bar-mp"),
    ]
    if extra_lines:
        children.append(html.Div(className="party-card-extra", children=[html.Div(line) for line in extra_lines]))
    return html.Div(className="party-card", children=children)


def nearest_ffx_checkpoint(progress):
    if progress is None:
        return None
    best = None
    for label, _room, _spawn, p, _note in FFX_CHECKPOINTS:
        if p is not None and p <= progress and (best is None or p > best[1]):
            best = (label, p)
    return best[0] if best else None


def build_overview_ffx(sd: SaveData):
    gil = sd.get("gil")
    playtime = sd.get("game_time_seconds")
    battles = sd.get("battles_fought")
    room = sd.get("room_number")
    progress = sd.get("storyline_progress")
    checkpoint = nearest_ffx_checkpoint(progress)

    tiles = html.Div(
        className="stat-tile-row",
        children=[
            stat_tile("Gil", format_int(gil)),
            stat_tile("Play Time", format_hms(playtime)),
            stat_tile("Battles Fought", format_int(battles)),
            stat_tile(
                "Story Progress",
                format_int(progress),
                sub=f"near: {checkpoint}" if checkpoint else f"room {room}",
            ),
        ],
    )

    cards = []
    for name in FFX_PARTY_ORDER:
        # current_hp/mp are the real stats; base_hp/mp aren't a matching max
        # (aeons show base_hp=0 with a large current_hp) - more like a
        # separate sphere-grid bonus counter, so shown as a note, not a bar.
        hp, mp = sd.get(f"{name}_current_hp"), sd.get(f"{name}_current_mp")
        base_hp, base_mp = sd.get(f"{name}_base_hp"), sd.get(f"{name}_base_mp")
        activation = sd.get(f"{name}_activation_type")
        status = _ACTIVATION_LABELS.get(activation, f"Unknown ({activation})")
        known = sum(1 for ability in ABILITY_NAMES if sd.get(f"{name}_ability_{ability}"))
        gauge, gauge_max = sd.get(f"{name}_overdrive_gauge"), sd.get(f"{name}_overdrive_gauge_max")
        cards.append(
            party_card(
                name,
                status,
                hp,
                None,
                mp,
                None,
                extra_lines=[
                    f"Abilities unlocked: {known} / {len(ABILITY_NAMES)}",
                    f"Overdrive gauge: {gauge} / {gauge_max}",
                    f"Base HP/MP bonus: {base_hp} / {base_mp}",
                ],
            )
        )

    return html.Div([tiles, html.Div(className="party-grid", children=cards)])


def build_overview_ffx2(sd: SaveData):
    gil = sd.get("gil")
    playtime = sd.get("gametime_seconds")
    chapter = sd.get("chapter")
    encounters = sd.get("encounters")
    primers = sd.get("al_bhed_primer_count")

    tiles = html.Div(
        className="stat-tile-row",
        children=[
            stat_tile("Gil", format_int(gil)),
            stat_tile("Play Time", format_hms(playtime)),
            stat_tile("Chapter", format_int(chapter)),
            stat_tile("Encounters", format_int(encounters)),
            stat_tile("Al Bhed Primers", format_int(primers)),
        ],
    )

    cards = []
    for name in FFX2_PARTY_ORDER:
        level = sd.get(f"{name}_level")
        hp, max_hp = sd.get(f"{name}_hp"), sd.get(f"{name}_max_hp")
        mp, max_mp = sd.get(f"{name}_mp"), sd.get(f"{name}_max_mp")
        exp, next_exp = sd.get(f"{name}_experience"), sd.get(f"{name}_next_level_exp")
        dressphere = sd.get(f"{name}_dressphere")
        cards.append(
            party_card(
                name,
                f"Level {level}",
                hp,
                max_hp,
                mp,
                max_mp,
                extra_lines=[
                    f"Experience: {format_int(exp)} / {format_int(next_exp)}",
                    f"Dressphere: #{dressphere}",
                ],
            )
        )

    return html.Div([tiles, html.Div(className="party-grid", children=cards)])


def decode_upload(contents):
    _header, b64 = contents.split(",", 1)
    return base64.b64decode(b64)


def encode_download(data: bytes, filename: str):
    return dict(content=base64.b64encode(data).decode(), filename=filename, base64=True)


def alert(message, kind="info"):
    return html.Div(message, className=f"alert alert-{kind}")


def labeled(label, component):
    return html.Div(className="field-group", children=[html.Label(label), component])


TAB_STYLE = {
    "padding": "10px 4px",
    "marginRight": "24px",
    "border": "none",
    "borderBottom": "2px solid transparent",
    "fontSize": "13.5px",
    "fontWeight": "650",
    "letterSpacing": "0.03em",
    "textTransform": "uppercase",
    "color": "#64748b",
    "background": "transparent",
}
TAB_SELECTED_STYLE = {
    **TAB_STYLE,
    "borderBottom": "2px solid #2563eb",
    "color": "#2563eb",
}

app = Dash(__name__)
app.title = "FFX / FFX2 Save Tool"

app.layout = html.Div(
    className="app-shell",
    children=[
        html.Div(
            className="app-header",
            children=[
                html.Img(
                    src=app.get_asset_url("logo.png"),
                    className="app-logo",
                    alt="Final Fantasy X / X-2 HD Remaster",
                ),
                html.H1("Save / Edit Tool"),
                html.P(
                    "Upload a save to inspect and edit its fields, jump to a known story "
                    "checkpoint, or convert it between PC, Vita and Switch. See README.md "
                    "for what's validated on real hardware vs. still unconfirmed."
                ),
            ],
        ),
        html.Div(
            className="card",
            children=[
                dcc.Upload(
                    id="upload-save",
                    className="upload-zone",
                    children=html.Div(["Drag and drop a save file, or ", html.A("browse")]),
                ),
                html.Div(id="upload-status", style={"marginTop": "12px"}),
                html.Div(
                    className="field-row",
                    style={"marginTop": "16px"},
                    children=[
                        labeled(
                            "Game",
                            dcc.Dropdown(
                                id="game-dropdown",
                                options=[{"label": "FFX", "value": "ffx"}, {"label": "FFX2", "value": "ffx2"}],
                                clearable=False,
                            ),
                        ),
                        labeled(
                            "Current platform",
                            dcc.Dropdown(
                                id="platform-dropdown",
                                options=[{"label": p.capitalize(), "value": p} for p in PLATFORMS],
                                clearable=False,
                            ),
                        ),
                    ],
                ),
            ],
        ),
        dcc.Tabs(
            id="main-tabs",
            value="tab-overview",
            className="main-tabs",
            children=[
                dcc.Tab(
                    label="Overview",
                    value="tab-overview",
                    style=TAB_STYLE,
                    selected_style=TAB_SELECTED_STYLE,
                    children=[
                        html.Div(
                            className="card",
                            children=[
                                html.Div(className="card-title", children="Save summary"),
                                html.Div(
                                    className="card-subtitle",
                                    children="Gil, play time, story progress, and a quick look at each "
                                    "party member - upload a save to see it filled in.",
                                ),
                                dcc.Loading(
                                    type="dot",
                                    children=html.Div(
                                        id="overview-content",
                                        children=html.Div("Upload a save to see its overview.", className="help-text"),
                                    ),
                                ),
                            ],
                        )
                    ],
                ),
                dcc.Tab(
                    label="Fields",
                    value="tab-fields",
                    style=TAB_STYLE,
                    selected_style=TAB_SELECTED_STYLE,
                    children=[
                        html.Div(
                            className="card",
                            children=[
                                html.Div(className="card-title", children="Browse & edit fields"),
                                html.Div(
                                    className="card-subtitle",
                                    children="Filter by category or search a field name, edit any Value cell, then Apply.",
                                ),
                                html.Div(
                                    className="toolbar",
                                    children=[
                                        dcc.Dropdown(
                                            id="category-filter",
                                            options=[{"label": c, "value": c} for c in CATEGORIES],
                                            value="All",
                                            clearable=False,
                                            style={"width": "180px"},
                                        ),
                                        dcc.Input(
                                            id="search-filter",
                                            type="text",
                                            placeholder="Search field names…",
                                            debounce=True,
                                            style={
                                                "flex": "1",
                                                "minWidth": "200px",
                                                "padding": "8px 10px",
                                                "border": "1px solid var(--border)",
                                                "borderRadius": "8px",
                                            },
                                        ),
                                    ],
                                ),
                                dcc.Loading(
                                    type="dot",
                                    children=dash_table.DataTable(
                                        id="fields-table",
                                        columns=[
                                            {"name": "Category", "id": "category", "editable": False},
                                            {"name": "Field", "id": "field", "editable": False},
                                            {"name": "Value", "id": "value", "editable": True},
                                        ],
                                        data=[],
                                        editable=True,
                                        filter_action="native",
                                        sort_action="native",
                                        page_size=15,
                                        style_as_list_view=True,
                                        style_table={"overflowX": "auto"},
                                        style_header={
                                            "backgroundColor": "#eaf1ff",
                                            "fontWeight": "650",
                                            "textTransform": "uppercase",
                                            "fontSize": "11px",
                                            "letterSpacing": "0.05em",
                                            "color": "#2563eb",
                                            "borderBottom": "1px solid #c3d5ef",
                                        },
                                        style_cell={
                                            "textAlign": "left",
                                            "fontSize": "13px",
                                            "padding": "9px 12px",
                                            "fontFamily": "inherit",
                                            "backgroundColor": "#ffffff",
                                            "color": "#1b2434",
                                            "border": "1px solid #eef2f8",
                                        },
                                        style_cell_conditional=[
                                            {"if": {"column_id": "field"}, "fontFamily": "SFMono-Regular, Consolas, monospace"},
                                        ],
                                        style_data_conditional=[
                                            {"if": {"row_index": "odd"}, "backgroundColor": "#f7faff"},
                                            {
                                                "if": {"column_editable": True},
                                                "backgroundColor": "#fdf1f9",
                                                "border": "1px solid #f3c6e2",
                                            },
                                            {
                                                "if": {"state": "active"},
                                                "backgroundColor": "#eaf1ff",
                                                "border": "1px solid #2563eb",
                                            },
                                        ],
                                    ),
                                ),
                                html.Div(
                                    style={"marginTop": "16px", "display": "flex", "gap": "10px", "alignItems": "center"},
                                    children=[
                                        html.Button(
                                            "Apply edits (recomputes checksum)",
                                            id="apply-button",
                                            n_clicks=0,
                                            className="btn btn-primary",
                                        ),
                                        html.Div(id="apply-status"),
                                    ],
                                ),
                            ],
                        )
                    ],
                ),
                dcc.Tab(
                    label="Story Position",
                    value="tab-story",
                    style=TAB_STYLE,
                    selected_style=TAB_SELECTED_STYLE,
                    children=[
                        html.Div(
                            className="card",
                            children=[
                                html.Div(className="card-title", children="Jump to a known story checkpoint (FFX only)"),
                                html.Div(
                                    className="help-text",
                                    children=[
                                        "Sets room_number / spawn_point / storyline_progress in one click - a shortcut "
                                        "for the same fields editable in the Fields tab. Room/progress values are "
                                        "community-sourced, not independently verified; spawn_point is occasionally "
                                        "an unconfirmed guess (noted after you jump). Keep your original save until "
                                        "you've loaded the result in-game and confirmed it lands where expected.",
                                        html.Br(),
                                        html.Br(),
                                        "For FFX2, don't use this - the game has its own official Chapter Select "
                                        "(unlocked after any ending) for whole-chapter jumps on your existing save "
                                        "with zero risk to completion stats. FFX2's story_*/requisite_* fields "
                                        "(Fields tab, Story category) are only for rewinding to a specific scene "
                                        "inside a chapter, past what Chapter Select offers.",
                                    ],
                                ),
                                html.Div(
                                    className="toolbar",
                                    children=[
                                        dcc.Dropdown(
                                            id="checkpoint-dropdown",
                                            options=[{"label": c[0], "value": c[0]} for c in FFX_CHECKPOINTS],
                                            placeholder="Choose a checkpoint…",
                                            style={"flex": "1", "minWidth": "320px"},
                                        ),
                                        html.Button(
                                            "Jump to checkpoint",
                                            id="checkpoint-button",
                                            n_clicks=0,
                                            className="btn btn-primary",
                                        ),
                                    ],
                                ),
                                html.Div(id="checkpoint-status"),
                            ],
                        )
                    ],
                ),
                dcc.Tab(
                    label="Export",
                    value="tab-export",
                    style=TAB_STYLE,
                    selected_style=TAB_SELECTED_STYLE,
                    children=[
                        html.Div(
                            className="export-grid",
                            children=[
                                html.Div(
                                    className="card",
                                    children=[
                                        html.Div(className="card-title", children="Download edited save"),
                                        html.Div(
                                            className="card-subtitle",
                                            children="Save the current in-memory file as-is, same platform format.",
                                        ),
                                        html.Button(
                                            "Download edited save",
                                            id="download-button",
                                            n_clicks=0,
                                            className="btn btn-secondary",
                                        ),
                                    ],
                                ),
                                html.Div(
                                    className="card",
                                    children=[
                                        html.Div(className="card-title", children="Convert & download"),
                                        html.Div(
                                            className="card-subtitle",
                                            children="Uses this project's bundled real reference saves for the target header/size.",
                                        ),
                                        html.Div(
                                            className="toolbar",
                                            children=[
                                                dcc.Dropdown(
                                                    id="target-platform-dropdown",
                                                    options=[{"label": p.capitalize(), "value": p} for p in PLATFORMS],
                                                    value="switch",
                                                    clearable=False,
                                                    style={"width": "160px"},
                                                ),
                                                html.Button(
                                                    "Convert & download",
                                                    id="convert-button",
                                                    n_clicks=0,
                                                    className="btn btn-primary",
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
                            ],
                        )
                    ],
                ),
                dcc.Tab(
                    label="Raw / Hex",
                    value="tab-hex",
                    style=TAB_STYLE,
                    selected_style=TAB_SELECTED_STYLE,
                    children=[
                        html.Div(
                            className="card",
                            children=[
                                html.Div(className="card-title", children="Explore the raw file"),
                                html.Div(
                                    className="card-subtitle",
                                    children="Every 16 bytes of the file, in hex - the Fields column shows any "
                                    "known field(s) living in that row and their current value. Search matches "
                                    "offset, hex bytes, ASCII text, or field names.",
                                ),
                                html.Div(id="hex-summary", style={"marginBottom": "12px"}),
                                html.Div(
                                    className="toolbar",
                                    children=[
                                        dcc.Input(
                                            id="hex-search",
                                            type="text",
                                            placeholder="Search offset, hex, text, or field name…",
                                            debounce=True,
                                            style={
                                                "flex": "1",
                                                "minWidth": "260px",
                                                "padding": "8px 10px",
                                                "border": "1px solid var(--border)",
                                                "borderRadius": "8px",
                                            },
                                        ),
                                    ],
                                ),
                                dcc.Loading(
                                    type="dot",
                                    children=dash_table.DataTable(
                                        id="hex-table",
                                        columns=[
                                            {"name": "Offset", "id": "offset", "editable": False},
                                            {"name": "Hex", "id": "hex", "editable": False},
                                            {"name": "ASCII", "id": "ascii", "editable": False},
                                            {"name": "Fields", "id": "fields", "editable": False},
                                        ],
                                        data=[],
                                        editable=False,
                                        filter_action="native",
                                        sort_action="native",
                                        page_size=25,
                                        style_as_list_view=True,
                                        style_table={"overflowX": "auto"},
                                        style_header={
                                            "backgroundColor": "#eaf1ff",
                                            "fontWeight": "650",
                                            "textTransform": "uppercase",
                                            "fontSize": "11px",
                                            "letterSpacing": "0.05em",
                                            "color": "#2563eb",
                                            "borderBottom": "1px solid #c3d5ef",
                                        },
                                        style_cell={
                                            "textAlign": "left",
                                            "fontSize": "12.5px",
                                            "padding": "7px 10px",
                                            "fontFamily": "SFMono-Regular, Consolas, monospace",
                                            "backgroundColor": "#ffffff",
                                            "color": "#1b2434",
                                            "border": "1px solid #eef2f8",
                                            "whiteSpace": "nowrap",
                                        },
                                        style_cell_conditional=[
                                            {"if": {"column_id": "offset"}, "width": "90px", "color": "#64748b"},
                                            {"if": {"column_id": "hex"}, "width": "340px"},
                                            {"if": {"column_id": "ascii"}, "width": "150px"},
                                            {
                                                "if": {"column_id": "fields"},
                                                "whiteSpace": "normal",
                                                "fontFamily": "inherit",
                                                "color": "#db2b8e",
                                            },
                                        ],
                                        style_data_conditional=[
                                            {"if": {"row_index": "odd"}, "backgroundColor": "#f7faff"},
                                            {
                                                "if": {"filter_query": '{fields} != ""'},
                                                "backgroundColor": "#fdf1f9",
                                            },
                                        ],
                                    ),
                                ),
                            ],
                        )
                    ],
                ),
                dcc.Tab(
                    label="Info",
                    value="tab-info",
                    style=TAB_STYLE,
                    selected_style=TAB_SELECTED_STYLE,
                    children=[
                        html.Div(
                            className="card",
                            children=[
                                html.Div(className="card-title", children="About this tool"),
                                html.Div(
                                    className="card-subtitle",
                                    children="The project README, rendered here so it's always in reach.",
                                ),
                                dcc.Markdown(README_CONTENT, className="markdown-body", link_target="_blank"),
                            ],
                        )
                    ],
                ),
            ],
        ),
        dcc.Store(id="save-bytes"),
        dcc.Store(id="save-filename"),
        dcc.Download(id="download-out"),
    ],
)


@app.callback(
    Output("save-bytes", "data"),
    Output("save-filename", "data"),
    Output("game-dropdown", "value"),
    Output("platform-dropdown", "value"),
    Output("upload-status", "children"),
    Input("upload-save", "contents"),
    State("upload-save", "filename"),
    prevent_initial_call=True,
)
def on_upload(contents, filename):
    raw = decode_upload(contents)
    game = guess_game(len(raw))
    platform = guess_platform(raw)
    status = alert(
        f"Loaded {filename} ({len(raw):,} bytes) — guessed {game.upper()} / {platform}. "
        "Correct the dropdowns above if that's wrong.",
        "success",
    )
    return base64.b64encode(raw).decode(), filename, game, platform, status


@app.callback(
    Output("overview-content", "children"),
    Input("save-bytes", "data"),
    Input("game-dropdown", "value"),
    Input("platform-dropdown", "value"),
    prevent_initial_call=True,
)
def refresh_overview(b64_data, game_s, platform):
    if not b64_data or not game_s or not platform:
        return html.Div("Upload a save to see its overview.", className="help-text")
    raw = base64.b64decode(b64_data)
    sd = SaveData(raw, GAME_LABELS[game_s], platform)
    return build_overview_ffx(sd) if game_s == "ffx" else build_overview_ffx2(sd)


@app.callback(
    Output("fields-table", "data"),
    Input("save-bytes", "data"),
    Input("game-dropdown", "value"),
    Input("platform-dropdown", "value"),
    prevent_initial_call=True,
)
def refresh_table(b64_data, game_s, platform):
    if not b64_data or not game_s or not platform:
        return []
    raw = base64.b64decode(b64_data)
    sd = SaveData(raw, GAME_LABELS[game_s], platform)
    return build_table_rows(sd)


@app.callback(
    Output("fields-table", "filter_query"),
    Input("category-filter", "value"),
    Input("search-filter", "value"),
)
def filter_table(category, search):
    clauses = []
    if category and category != "All":
        clauses.append('{category} = "' + category + '"')
    if search:
        clauses.append('{field} contains "' + search.strip().replace('"', "") + '"')
    return " && ".join(clauses)


@app.callback(
    Output("hex-table", "data"),
    Output("hex-summary", "children"),
    Input("save-bytes", "data"),
    Input("game-dropdown", "value"),
    Input("platform-dropdown", "value"),
    prevent_initial_call=True,
)
def refresh_hex_table(b64_data, game_s, platform):
    if not b64_data or not game_s or not platform:
        return [], ""
    raw = base64.b64decode(b64_data)
    sd = SaveData(raw, GAME_LABELS[game_s], platform)
    rows, summary = build_hex_rows(sd, game_s)
    return rows, summary


@app.callback(
    Output("hex-table", "filter_query"),
    Input("hex-search", "value"),
)
def filter_hex_table(search):
    if not search:
        return ""
    text = search.strip().replace('"', "")
    if not text:
        return ""
    cols = ["offset", "hex", "ascii", "fields"]
    return " || ".join('{' + c + '} contains "' + text + '"' for c in cols)


@app.callback(
    Output("save-bytes", "data", allow_duplicate=True),
    Output("apply-status", "children"),
    Input("apply-button", "n_clicks"),
    State("fields-table", "data"),
    State("save-bytes", "data"),
    State("game-dropdown", "value"),
    State("platform-dropdown", "value"),
    prevent_initial_call=True,
)
def apply_edits(_n_clicks, table_data, b64_data, game_s, platform):
    if not b64_data or not game_s or not platform:
        return no_update, alert("Load a save first.", "error")

    raw = base64.b64decode(b64_data)
    sd = SaveData(raw, GAME_LABELS[game_s], platform)

    changed = 0
    errors = []
    for row in table_data:
        name, raw_value = row["field"], row["value"]
        try:
            current = sd.get(name)
            new_value = coerce_value(raw_value, current)
            if new_value != current:
                sd.set(name, new_value)
                changed += 1
        except Exception as e:  # noqa: BLE001 - surface any bad edit to the user, keep going
            errors.append(f"{name}: {e}")

    new_bytes = sd.export_bytes(recompute_checksum=True)

    if errors:
        msg = alert(f"Applied {changed} change(s), but hit errors: {'; '.join(errors)}", "error")
    else:
        msg = alert(f"Applied {changed} change(s), checksum recomputed.", "success")

    return base64.b64encode(new_bytes).decode(), msg


@app.callback(
    Output("save-bytes", "data", allow_duplicate=True),
    Output("apply-status", "children", allow_duplicate=True),
    Output("checkpoint-status", "children"),
    Input("checkpoint-button", "n_clicks"),
    State("checkpoint-dropdown", "value"),
    State("save-bytes", "data"),
    State("game-dropdown", "value"),
    State("platform-dropdown", "value"),
    prevent_initial_call=True,
)
def jump_to_checkpoint(_n_clicks, checkpoint_label, b64_data, game_s, platform):
    if not b64_data or not game_s or not platform:
        return no_update, no_update, alert("Load a save first.", "error")
    if game_s != "ffx":
        return no_update, no_update, alert(
            "These checkpoints are FFX-only - use FFX2's in-game Chapter Select instead.", "error"
        )
    if not checkpoint_label:
        return no_update, no_update, alert("Pick a checkpoint first.", "error")

    label, room, spawn, progress, note = next(c for c in FFX_CHECKPOINTS if c[0] == checkpoint_label)

    raw = base64.b64decode(b64_data)
    sd = SaveData(raw, GAME_LABELS[game_s], platform)
    sd.set("room_number", room)
    sd.set("spawn_point", spawn)
    if progress is not None:
        sd.set("storyline_progress", progress)

    new_bytes = sd.export_bytes(recompute_checksum=True)

    msg = alert(f"Jumped to '{label}' (room={room}, spawn={spawn}, progress={progress}). {note}.", "success")
    return base64.b64encode(new_bytes).decode(), "", msg


@app.callback(
    Output("download-out", "data"),
    Input("download-button", "n_clicks"),
    State("save-bytes", "data"),
    State("save-filename", "data"),
    prevent_initial_call=True,
)
def download_edited(_n_clicks, b64_data, filename):
    if not b64_data:
        return no_update
    raw = base64.b64decode(b64_data)
    return encode_download(raw, filename or "save_edited")


@app.callback(
    Output("download-out", "data", allow_duplicate=True),
    Input("convert-button", "n_clicks"),
    State("save-bytes", "data"),
    State("save-filename", "data"),
    State("game-dropdown", "value"),
    State("platform-dropdown", "value"),
    State("target-platform-dropdown", "value"),
    prevent_initial_call=True,
)
def convert_and_download(_n_clicks, b64_data, filename, game_s, src_platform, dst_platform):
    if not b64_data or not game_s or not src_platform:
        return no_update
    raw = base64.b64decode(b64_data)
    game = GAME_LABELS[game_s]
    converted = convert_platform(raw, game, src_platform, dst_platform)
    base_name = (filename or f"{game_s}_save").rsplit(".", 1)[0]
    out_name = f"{base_name}_{dst_platform}"
    return encode_download(converted, out_name)


if __name__ == "__main__":
    app.run(debug=True)
