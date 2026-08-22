import { state } from "../state";
import { convertPlatform } from "../lib/platformConvert";
import type { Platform } from "../lib/saveData";
import { el, alertBox, downloadBytes, clear } from "./helpers";

export function renderExportTab(container: HTMLElement): void {
  clear(container);

  const grid = el("div", { className: "export-grid" });
  container.append(grid);

  const dlBtn = el("button", { className: "btn btn-secondary", text: "Download edited save" }) as HTMLButtonElement;
  const dlCard = el("div", { className: "card" }, [
    el("div", { className: "card-title", text: "Download edited save" }),
    el("div", { className: "card-subtitle", text: "Save the current in-memory file as-is, same platform format." }),
    dlBtn,
  ]);
  dlBtn.onclick = () => {
    const sd = state.saveData;
    if (!sd) return;
    downloadBytes(sd.exportBytes(true), state.filename ?? "save_edited");
  };

  const platformSelect = el(
    "select",
    {},
    [
      el("option", { text: "Pc", attrs: { value: "pc" } }),
      el("option", { text: "Vita", attrs: { value: "vita" } }),
      el("option", { text: "Switch", attrs: { value: "switch" } }),
    ],
  ) as HTMLSelectElement;
  platformSelect.value = "switch";
  platformSelect.style.width = "160px";

  const convBtn = el("button", { className: "btn btn-primary", text: "Convert & download" }) as HTMLButtonElement;
  const convStatus = el("div");
  const convCard = el("div", { className: "card" }, [
    el("div", { className: "card-title", text: "Convert & download" }),
    el("div", {
      className: "card-subtitle",
      text: "Uses this project's bundled real reference saves for the target header/size.",
    }),
    el("div", { className: "toolbar" }, [platformSelect, convBtn]),
    convStatus,
  ]);
  convBtn.onclick = async () => {
    const sd = state.saveData;
    if (!sd || !state.game || !state.platform) return;
    clear(convStatus);
    convBtn.disabled = true;
    try {
      const converted = await convertPlatform(sd.exportBytes(true), sd.game, state.platform, platformSelect.value as Platform);
      const baseName = (state.filename ?? `${state.game}_save`).replace(/\.[^./]*$/, "");
      downloadBytes(converted, `${baseName}_${platformSelect.value}`);
    } catch (e) {
      convStatus.append(alertBox(e instanceof Error ? e.message : String(e), "error"));
    } finally {
      convBtn.disabled = false;
    }
  };

  if (!state.saveData) {
    dlBtn.disabled = true;
    convBtn.disabled = true;
  }

  grid.append(dlCard, convCard);
}
