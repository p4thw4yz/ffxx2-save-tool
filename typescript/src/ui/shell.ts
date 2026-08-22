import { el } from "./helpers";

export interface TabDef {
  id: string;
  label: string;
}

export interface Shell {
  root: HTMLElement;
  uploadZone: HTMLElement;
  fileInput: HTMLInputElement;
  uploadStatus: HTMLElement;
  gameSelect: HTMLSelectElement;
  platformSelect: HTMLSelectElement;
  tabButtons: Record<string, HTMLButtonElement>;
  tabPanels: Record<string, HTMLElement>;
  selectTab(id: string): void;
}

const TABS: TabDef[] = [
  { id: "overview", label: "Overview" },
  { id: "fields", label: "Fields" },
  { id: "story", label: "Story Position" },
  { id: "export", label: "Export" },
  { id: "hex", label: "Raw / Hex" },
  { id: "info", label: "Info" },
];

export function buildShell(root: HTMLElement): Shell {
  const header = el("div", { className: "app-header" }, [
    el("img", { className: "app-logo", attrs: { src: "/logo.png", alt: "Final Fantasy X / X-2 HD Remaster" } }),
    el("h1", { text: "Save / Edit Tool" }),
    el("p", {
      text:
        "Upload a save to inspect and edit its fields, jump to a known story checkpoint, or convert it between " +
        "PC, Vita and Switch. Runs entirely in your browser - no file is ever uploaded anywhere.",
    }),
  ]);

  const fileInput = el("input", { attrs: { type: "file", id: "file-input" } }) as HTMLInputElement;
  fileInput.style.display = "none";

  const uploadZone = el("div", { className: "upload-zone" }, [
    "Drag and drop a save file, or ",
    el("a", { text: "browse" }),
  ]);

  const uploadStatus = el("div", { attrs: { id: "upload-status" } });
  uploadStatus.style.marginTop = "12px";

  const gameSelect = el("select", { attrs: { id: "game-select" } }, [
    el("option", { text: "—", attrs: { value: "" } }),
    el("option", { text: "FFX", attrs: { value: "ffx" } }),
    el("option", { text: "FFX2", attrs: { value: "ffx2" } }),
  ]) as HTMLSelectElement;

  const platformSelect = el("select", { attrs: { id: "platform-select" } }, [
    el("option", { text: "—", attrs: { value: "" } }),
    el("option", { text: "Pc", attrs: { value: "pc" } }),
    el("option", { text: "Vita", attrs: { value: "vita" } }),
    el("option", { text: "Switch", attrs: { value: "switch" } }),
  ]) as HTMLSelectElement;

  const uploadCard = el("div", { className: "card" }, [
    uploadZone,
    fileInput,
    uploadStatus,
    el("div", { className: "field-row", attrs: { style: "margin-top:16px" } }, [
      el("div", { className: "field-group" }, [el("label", { text: "Game" }), gameSelect]),
      el("div", { className: "field-group" }, [el("label", { text: "Current platform" }), platformSelect]),
    ]),
  ]);

  const tabBar = el("div", { className: "main-tabs" });
  const tabButtons: Record<string, HTMLButtonElement> = {};
  const tabPanels: Record<string, HTMLElement> = {};
  const panelsWrap = el("div", { attrs: { id: "tab-panels" } });

  function selectTab(id: string): void {
    for (const [tid, btn] of Object.entries(tabButtons)) btn.classList.toggle("selected", tid === id);
    for (const [tid, panel] of Object.entries(tabPanels)) panel.style.display = tid === id ? "" : "none";
  }

  for (const tab of TABS) {
    const btn = el("button", { className: "main-tab", text: tab.label, attrs: { type: "button" } }) as HTMLButtonElement;
    btn.onclick = () => selectTab(tab.id);
    tabButtons[tab.id] = btn;
    tabBar.append(btn);

    const panel = el("div");
    tabPanels[tab.id] = panel;
    panelsWrap.append(panel);
  }

  root.append(header, uploadCard, tabBar, panelsWrap);
  selectTab("overview");

  return { root, uploadZone, fileInput, uploadStatus, gameSelect, platformSelect, tabButtons, tabPanels, selectTab };
}
