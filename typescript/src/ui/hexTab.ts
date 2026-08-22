import { state } from "../state";
import type { SaveData } from "../lib/saveData";
import type { FieldKind } from "../lib/fields";
import { el, clear } from "./helpers";
import { createDataTable, type Column } from "./dataTable";

const KIND_SIZE: Record<FieldKind, number> = { u8: 1, u16: 2, u32: 4, i32: 4, f32: 4, bit: 1 };
const HEX_ROW_WIDTH = 16;

interface HexRow {
  offset: string;
  hex: string;
  ascii: string;
  fields: string;
}

function buildHexRows(sd: SaveData): { rows: HexRow[]; summary: string } {
  const raw = sd.data;
  const fieldList = sd.fieldList();
  const values = sd.fields();

  const rowNotes = new Map<number, string[]>();
  const covered = new Set<number>();
  for (const f of fieldList) {
    const absOff = sd.headerLen + f.offset;
    const size = KIND_SIZE[f.kind];
    for (let i = 0; i < size; i++) covered.add(absOff + i);
    const rowIdx = Math.floor(absOff / HEX_ROW_WIDTH);
    const notes = rowNotes.get(rowIdx) ?? [];
    notes.push(`${f.name}=${values[f.name]}`);
    rowNotes.set(rowIdx, notes);
  }

  const rows: HexRow[] = [];
  for (let start = 0; start < raw.length; start += HEX_ROW_WIDTH) {
    const chunk = raw.subarray(start, start + HEX_ROW_WIDTH);
    let hex = "";
    let ascii = "";
    for (const b of chunk) {
      hex += b.toString(16).padStart(2, "0") + " ";
      ascii += b >= 32 && b < 127 ? String.fromCharCode(b) : ".";
    }
    rows.push({
      offset: `0x${start.toString(16).padStart(5, "0")}`,
      hex: hex.trim(),
      ascii,
      fields: (rowNotes.get(start / HEX_ROW_WIDTH) ?? []).join(", "),
    });
  }

  const coverage = raw.length ? `${((covered.size / raw.length) * 100).toFixed(1)}%` : "0%";
  const summary = `${raw.length.toLocaleString()} bytes total - ${fieldList.length} known fields covering ${coverage} of the file.`;
  return { rows, summary };
}

let tableHandle: ReturnType<typeof createDataTable<HexRow>> | null = null;
let searchText = "";
let allRows: HexRow[] = [];

function applyFilter(): HexRow[] {
  const s = searchText.trim().toLowerCase();
  if (!s) return allRows;
  return allRows.filter(
    (r) =>
      r.offset.toLowerCase().includes(s) ||
      r.hex.toLowerCase().includes(s) ||
      r.ascii.toLowerCase().includes(s) ||
      r.fields.toLowerCase().includes(s),
  );
}

export function renderHexTab(container: HTMLElement): void {
  clear(container);

  const card = el("div", { className: "card" }, [
    el("div", { className: "card-title", text: "Explore the raw file" }),
    el("div", {
      className: "card-subtitle",
      text:
        "Every 16 bytes of the file, in hex - the Fields column shows any known field(s) living in that row and " +
        "their current value. Search matches offset, hex bytes, ASCII text, or field names.",
    }),
  ]);
  container.append(card);

  const sd = state.saveData;
  if (!sd) {
    card.append(el("div", { className: "help-text", text: "Upload a save to explore its bytes." }));
    return;
  }

  const { rows, summary } = buildHexRows(sd);
  allRows = rows;
  card.append(el("div", { text: summary, attrs: { style: "margin-bottom:12px;font-size:12.5px;color:var(--text-muted)" } }));

  const searchInput = el("input", { attrs: { type: "text", placeholder: "Search offset, hex, text, or field name…" } }) as HTMLInputElement;
  searchInput.style.flex = "1";
  searchInput.style.minWidth = "260px";
  searchInput.value = searchText;
  searchInput.oninput = () => {
    searchText = searchInput.value;
    tableHandle?.setRows(applyFilter());
  };
  card.append(el("div", { className: "toolbar" }, [searchInput]));

  const tableContainer = el("div");
  card.append(tableContainer);

  const columns: Column<HexRow>[] = [
    { label: "Offset", render: (r) => r.offset },
    { label: "Hex", render: (r) => r.hex },
    { label: "ASCII", render: (r) => r.ascii },
    { label: "Fields", className: "fields-col", render: (r) => r.fields },
  ];
  tableHandle = createDataTable(tableContainer, columns, 25);
  tableHandle.setRows(applyFilter());
}
