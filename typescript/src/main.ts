import "./style.css";
import { buildShell } from "./ui/shell";
import { state, rebuildSaveData, onStateChange, notifyStateChange, type GameKey } from "./state";
import type { Platform } from "./lib/saveData";
import { alertBox, clear } from "./ui/helpers";
import { renderOverview } from "./ui/overviewTab";
import { renderFieldsTab } from "./ui/fieldsTab";
import { renderStoryTab } from "./ui/storyTab";
import { renderExportTab } from "./ui/exportTab";
import { renderHexTab } from "./ui/hexTab";
import { buildStatsTab } from "./ui/statsTab";
import { renderInfoTab } from "./ui/infoTab";

const appRoot = document.getElementById("app")!;
console.log("FFX/FFX2 Save Tool loaded");
const shell = buildShell(appRoot);

function guessGame(size: number): GameKey {
  return size > 50000 ? "ffx2" : "ffx";
}

function guessPlatform(raw: Uint8Array): Platform {
  // Heuristic: a Switch header's first 4 bytes are a little-endian Unix
  // timestamp (roughly year 2000-2040) followed by 4 zero bytes.
  if (raw.length >= 8) {
    const view = new DataView(raw.buffer, raw.byteOffset, raw.byteLength);
    const stamp = view.getUint32(0, true);
    const tailZero = raw[4] === 0 && raw[5] === 0 && raw[6] === 0 && raw[7] === 0;
    if (tailZero && stamp >= 946684800 && stamp <= 2208988800) return "switch";
  }
  return "pc";
}

function renderDataTabs(): void {
  renderOverview(shell.tabPanels.overview);
  renderFieldsTab(shell.tabPanels.fields);
  renderStoryTab(shell.tabPanels.story);
  renderExportTab(shell.tabPanels.export);
  renderHexTab(shell.tabPanels.hex);
  buildStatsTab(shell.tabPanels.stats, state.saveData, () => notifyStateChange());
}

onStateChange(renderDataTabs);
renderInfoTab(shell.tabPanels.info); // static content, no need to re-render on state change
renderDataTabs(); // initial "upload a save" placeholders

function loadFile(file: File): void {
  const reader = new FileReader();
  reader.onload = () => {
    const raw = new Uint8Array(reader.result as ArrayBuffer);
    const game = guessGame(raw.length);
    const platform = guessPlatform(raw);

    state.rawBytes = raw;
    state.filename = file.name;
    state.game = game;
    state.platform = platform;
    shell.gameSelect.value = game;
    shell.platformSelect.value = platform;
    rebuildSaveData();

    clear(shell.uploadStatus);
    shell.uploadStatus.append(
      alertBox(
        `Loaded ${file.name} (${raw.length.toLocaleString()} bytes) — guessed ${game.toUpperCase()} / ${platform}. ` +
          "Correct the dropdowns above if that's wrong.",
        "success",
      ),
    );
    notifyStateChange();
  };
  reader.readAsArrayBuffer(file);
}

shell.uploadZone.onclick = () => shell.fileInput.click();
shell.uploadZone.ondragover = (e) => {
  e.preventDefault();
  shell.uploadZone.classList.add("dragover");
};
shell.uploadZone.ondragleave = () => shell.uploadZone.classList.remove("dragover");
shell.uploadZone.ondrop = (e) => {
  e.preventDefault();
  shell.uploadZone.classList.remove("dragover");
  const file = e.dataTransfer?.files?.[0];
  if (file) loadFile(file);
};
shell.fileInput.onchange = () => {
  const file = shell.fileInput.files?.[0];
  if (file) loadFile(file);
};

shell.gameSelect.onchange = () => {
  state.game = (shell.gameSelect.value || null) as GameKey | null;
  rebuildSaveData();
  notifyStateChange();
};
shell.platformSelect.onchange = () => {
  state.platform = (shell.platformSelect.value || null) as Platform | null;
  rebuildSaveData();
  notifyStateChange();
};
