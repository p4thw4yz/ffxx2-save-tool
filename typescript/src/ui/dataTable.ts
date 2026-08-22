import { el, clear } from "./helpers";

export interface Column<T> {
  label: string;
  className?: string;
  render: (row: T) => Node | string;
}

export interface DataTableHandle<T> {
  setRows(rows: T[]): void;
  refresh(): void;
}

export function createDataTable<T>(
  container: HTMLElement,
  columns: Column<T>[],
  pageSize: number,
): DataTableHandle<T> {
  let rows: T[] = [];
  let page = 0;

  function renderPage(): void {
    clear(container);

    const totalPages = Math.max(1, Math.ceil(rows.length / pageSize));
    page = Math.min(page, totalPages - 1);
    const start = page * pageSize;
    const pageRows = rows.slice(start, start + pageSize);

    const table = el("table", { className: "data-table" });
    const thead = el("thead");
    const headRow = el("tr");
    for (const col of columns) headRow.append(el("th", { text: col.label }));
    thead.append(headRow);
    table.append(thead);

    const tbody = el("tbody");
    for (const row of pageRows) {
      const tr = el("tr");
      for (const col of columns) {
        const td = el("td", { className: col.className ?? "" });
        const content = col.render(row);
        if (typeof content === "string") td.textContent = content;
        else td.append(content);
        tr.append(td);
      }
      tbody.append(tr);
    }
    table.append(tbody);

    const wrap = el("div", { className: "data-table-wrap" }, [table]);
    container.append(wrap);

    const pager = el("div", { className: "table-pager" });
    const prevBtn = el("button", { text: "‹ Prev" });
    const nextBtn = el("button", { text: "Next ›" });
    prevBtn.disabled = page === 0;
    nextBtn.disabled = page >= totalPages - 1;
    prevBtn.onclick = () => {
      page--;
      renderPage();
    };
    nextBtn.onclick = () => {
      page++;
      renderPage();
    };
    pager.append(
      prevBtn,
      el("span", { text: `Page ${page + 1} of ${totalPages} (${rows.length.toLocaleString()} rows)` }),
      nextBtn,
    );
    container.append(pager);
  }

  return {
    setRows(newRows: T[]) {
      rows = newRows;
      page = 0;
      renderPage();
    },
    refresh: renderPage,
  };
}
