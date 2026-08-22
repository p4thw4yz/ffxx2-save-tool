import { state, rebuildSaveData, notifyStateChange } from "../state";
import { FFX_CHECKPOINTS } from "../lib/generated/checkpoints";
import { el, alertBox, clear } from "./helpers";

export function renderStoryTab(container: HTMLElement): void {
  clear(container);

  const card = el("div", { className: "card" }, [
    el("div", { className: "card-title", text: "Jump to a known story checkpoint (FFX only)" }),
    el("div", { className: "help-text" }, [
      "Sets room_number / spawn_point / storyline_progress in one click - a shortcut for the same fields " +
        "editable in the Fields tab. Room/progress values are community-sourced, not independently verified; " +
        "spawn_point is occasionally an unconfirmed guess (noted after you jump). Keep your original save until " +
        "you've loaded the result in-game and confirmed it lands where expected.",
      el("br"),
      el("br"),
      "For FFX2, don't use this - the game has its own official Chapter Select (unlocked after any ending) for " +
        "whole-chapter jumps on your existing save with zero risk to completion stats. FFX2's story_*/requisite_* " +
        "fields (Fields tab, Story category) are only for rewinding to a specific scene inside a chapter.",
    ]),
  ]);
  container.append(card);

  const select = el(
    "select",
    {},
    [
      el("option", { text: "Choose a checkpoint…", attrs: { value: "" } }),
      ...FFX_CHECKPOINTS.map((c) => el("option", { text: c.label, attrs: { value: c.label } })),
    ],
  ) as HTMLSelectElement;
  select.style.flex = "1";
  select.style.minWidth = "320px";

  const jumpBtn = el("button", { className: "btn btn-primary", text: "Jump to checkpoint" });
  const statusEl = el("div");

  jumpBtn.onclick = () => {
    clear(statusEl);
    const sd = state.saveData;
    if (!sd || !state.game) {
      statusEl.append(alertBox("Load a save first.", "error"));
      return;
    }
    if (state.game !== "ffx") {
      statusEl.append(alertBox("These checkpoints are FFX-only - use FFX2's in-game Chapter Select instead.", "error"));
      return;
    }
    const label = select.value;
    if (!label) {
      statusEl.append(alertBox("Pick a checkpoint first.", "error"));
      return;
    }
    const cp = FFX_CHECKPOINTS.find((c) => c.label === label)!;
    sd.set("room_number", cp.room);
    sd.set("spawn_point", cp.spawn);
    if (cp.progress !== null) sd.set("storyline_progress", cp.progress);

    state.rawBytes = sd.exportBytes(true);
    rebuildSaveData();

    statusEl.append(
      alertBox(`Jumped to '${cp.label}' (room=${cp.room}, spawn=${cp.spawn}, progress=${cp.progress}). ${cp.note}.`, "success"),
    );
    notifyStateChange();
  };

  card.append(el("div", { className: "toolbar" }, [select, jumpBtn]), statusEl);
}
