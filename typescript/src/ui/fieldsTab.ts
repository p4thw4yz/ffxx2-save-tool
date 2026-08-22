import { state, rebuildSaveData, notifyStateChange } from "../state";
import { coerceValue, type FieldKind } from "../lib/fields";
import { el, alertBox, fieldValueToString, clear } from "./helpers";
import { CATEGORIES, categoryOf } from "./categories";
import { createDataTable, type Column } from "./dataTable";

interface Row {
  category: string;
  field: string;
  value: number | boolean;
  kind: FieldKind;
}

let categoryFilter = "All";
let searchText = "";
let tableHandle: ReturnType<typeof createDataTable<Row>> | null = null;
let statusEl: HTMLElement | null = null;

function computeRows(): Row[] {
  const sd = state.saveData;
  if (!sd) return [];
  const kindByName = new Map(sd.fieldList().map((f) => [f.name, f.kind]));
  const rows: Row[] = [];
  for (const [name, value] of Object.entries(sd.fields())) {
    rows.push({ category: categoryOf(name), field: name, value, kind: kindByName.get(name)! });
  }
  rows.sort((a, b) => a.field.localeCompare(b.field));
  return rows;
}

function applyFilter(rows: Row[]): Row[] {
  const search = searchText.trim().toLowerCase();
  return rows.filter((r) => {
    if (categoryFilter !== "All" && r.category !== categoryFilter) return false;
    if (search && !r.field.toLowerCase().includes(search)) return false;
    return true;
  });
}

function applyEdits(): void {
  const sd = state.saveData;
  if (!sd || !statusEl) return;

  let changed = 0;
  const errors: string[] = [];
  for (const [name, rawText] of state.pendingEdits) {
    try {
      const field = sd.fieldList().find((f) => f.name === name);
      if (!field) continue;
      const current = sd.get(name);
      const next = coerceValue(rawText, field.kind);
      if (next !== current) {
        sd.set(name, next);
        changed++;
      }
    } catch (e) {
      errors.push(`${name}: ${e instanceof Error ? e.message : String(e)}`);
    }
  }

  state.rawBytes = sd.exportBytes(true);
  rebuildSaveData();

  clear(statusEl);
  if (errors.length) {
    statusEl.append(alertBox(`Applied ${changed} change(s), but hit errors: ${errors.join("; ")}`, "error"));
  } else {
    statusEl.append(alertBox(`Applied ${changed} change(s), checksum recomputed.`, "success"));
  }

  notifyStateChange();
}

export function renderFieldsTab(container: HTMLElement): void {
  clear(container);

  const card = el("div", { className: "card" }, [
    el("div", { className: "card-title", text: "Browse & edit fields" }),
    el("div", {
      className: "card-subtitle",
      text: "Filter by category or search a field name, edit any Value cell, then Apply.",
    }),
  ]);
  container.append(card);

  const sd = state.saveData;
  if (!sd) {
    card.append(el("div", { className: "help-text", text: "Upload a save to see its fields." }));
    return;
  }

  const categorySelect = el(
    "select",
    {},
    CATEGORIES.map((c) => el("option", { text: c, attrs: { value: c } })),
  ) as HTMLSelectElement;
  categorySelect.value = categoryFilter;
  categorySelect.onchange = () => {
    categoryFilter = categorySelect.value;
    tableHandle?.setRows(applyFilter(computeRows()));
  };

  const searchInput = el("input", { attrs: { type: "text", placeholder: "Search field names…" } }) as HTMLInputElement;
  searchInput.style.flex = "1";
  searchInput.style.minWidth = "200px";
  searchInput.value = searchText;
  searchInput.oninput = () => {
    searchText = searchInput.value;
    tableHandle?.setRows(applyFilter(computeRows()));
  };

  card.append(el("div", { className: "toolbar" }, [categorySelect, searchInput]));

  const tableContainer = el("div");
  card.append(tableContainer);

  const columns: Column<Row>[] = [
    { label: "Category", render: (r) => r.category },
    { label: "Field", className: "field-name", render: (r) => r.field },
    {
      label: "Value",
      className: "value-cell",
      render: (r) => {
        const input = el("input", { attrs: { type: "text" } }) as HTMLInputElement;
        input.value = state.pendingEdits.get(r.field) ?? fieldValueToString(r.value);
        input.oninput = () => state.pendingEdits.set(r.field, input.value);
        return input;
      },
    },
  ];

  tableHandle = createDataTable(tableContainer, columns, 15);
  tableHandle.setRows(applyFilter(computeRows()));

  const applyBtn = el("button", { className: "btn btn-primary", text: "Apply edits (recomputes checksum)" });
  applyBtn.onclick = applyEdits;
  statusEl = el("div");
  card.append(el("div", { attrs: { style: "margin-top:16px;display:flex;gap:10px;align-items:center" } }, [applyBtn, statusEl]));
}
