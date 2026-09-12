import { el } from "./helpers";
import type { SaveData } from "../lib/saveData";
import { Game } from "../lib/checksum";

const FFX_PARTY = ["tidus", "yuna", "auron", "kimahri", "wakka", "lulu", "rikku"];
const FFX2_PARTY = ["yuna", "rikku", "paine"];
const STATS = ["strength", "defense", "magic", "magic_defense", "agility", "accuracy", "evasion", "luck"];

function expForLevel(level: number): number {
  if (level <= 1) return 0;
  return level * 7000;
}

function getCharStats(sd: SaveData, char: string): Record<string, number> {
  const stats: Record<string, number> = {};
  try {
    if (sd.game === Game.FFX2) {
      stats.level = sd.get(`${char}_level`) as number;
      stats.hp = sd.get(`${char}_hp`) as number;
      stats.max_hp = sd.get(`${char}_max_hp`) as number;
      stats.mp = sd.get(`${char}_mp`) as number;
      stats.max_mp = sd.get(`${char}_max_mp`) as number;
      for (const stat of STATS) {
        stats[stat] = sd.get(`${char}_${stat}`) as number;
      }
      stats.experience = sd.get(`${char}_experience`) as number;
    } else {
      stats.level = sd.get(`${char}_level`) as number;
      stats.hp = sd.get(`${char}_current_hp`) as number;
      for (const stat of STATS) {
        try {
          stats[stat] = sd.get(`${char}_${stat}`) as number;
        } catch {
          // Field may not exist for FFX
        }
      }
    }
  } catch (e) {
    console.error(`Error reading stats for ${char}:`, e);
  }
  return stats;
}

export function buildStatsTab(
  panel: HTMLElement,
  sd: SaveData | null,
  onApply?: () => void,
): void {
  panel.innerHTML = "";

  if (!sd) {
    panel.append(el("div", { className: "help-text", text: "Upload a save to edit stats." }));
    return;
  }

  const party = sd.game === Game.FFX ? FFX_PARTY : FFX2_PARTY;
  const slidersByChar: Record<string, Record<string, HTMLInputElement>> = {};

  // Preset buttons
  const btn1 = el("button", { className: "btn btn-secondary", text: "Level 50" });
  btn1.onclick = () => {
    applyPreset(sd, party, "lv50");
    onApply?.();
  };

  const btn2 = el("button", { className: "btn btn-secondary", text: "Level 70" });
  btn2.onclick = () => {
    applyPreset(sd, party, "lv70");
    onApply?.();
  };

  const btn3 = el("button", { className: "btn btn-secondary", text: "Max Stats" });
  btn3.onclick = () => {
    applyPreset(sd, party, "max");
    onApply?.();
  };

  const btn4 = el("button", { className: "btn btn-primary", text: "Full Powerup" });
  btn4.onclick = () => {
    applyPreset(sd, party, "powerup");
    onApply?.();
  };

  const presetBar = el("div", { className: "toolbar" }, [btn1, btn2, btn3, btn4]);

  const headerCard = el("div", { className: "card" }, [
    el("div", { className: "card-title", text: "Character Stats Editor" }),
    el("div", {
      className: "card-subtitle",
      text: "Boost levels, HP, MP, stats, and Gil. Use presets for quick adjustments, or adjust sliders and apply.",
    }),
    presetBar,
  ]);

  panel.append(headerCard);

  // Character cards
  for (const char of party) {
    const stats = getCharStats(sd, char);
    if (Object.keys(stats).length === 0) continue;

    slidersByChar[char] = {};
    const inputs: HTMLElement[] = [];

    // Level
    const levelSlider = el("input") as HTMLInputElement;
    levelSlider.type = "range";
    levelSlider.min = "1";
    levelSlider.max = "99";
    levelSlider.value = stats.level.toString();

    const levelDisplay = el("span", { text: stats.level.toString() });
    levelDisplay.style.minWidth = "30px";
    levelDisplay.style.fontSize = "12px";

    levelSlider.oninput = () => {
      levelDisplay.textContent = levelSlider.value;
    };
    slidersByChar[char].level = levelSlider;

    const levelDiv = el("div", {});
    levelDiv.style.marginBottom = "12px";
    const levelLabel = el("label", { text: "Level" });
    levelLabel.style.cssText = "font-size: 11px; font-weight: 600; color: #666";
    levelDiv.appendChild(levelLabel);
    const levelRow = el("div", {});
    levelRow.style.display = "flex";
    levelRow.style.gap = "8px";
    levelRow.style.alignItems = "center";
    levelRow.appendChild(levelSlider);
    levelRow.appendChild(levelDisplay);
    levelDiv.appendChild(levelRow);
    inputs.push(levelDiv);

    // FFX2: HP and MP
    if (sd.game === Game.FFX2) {
      const hpSlider = el("input") as HTMLInputElement;
      hpSlider.type = "range";
      hpSlider.min = "1";
      hpSlider.max = "9999";
      hpSlider.step = "100";
      hpSlider.value = stats.hp.toString();

      const hpDisplay = el("span", { text: stats.hp.toString() });
      hpDisplay.style.minWidth = "50px";
      hpDisplay.style.fontSize = "12px";

      hpSlider.oninput = () => {
        hpDisplay.textContent = hpSlider.value;
      };
      slidersByChar[char].hp = hpSlider;

      const hpDiv = el("div", {});
      hpDiv.style.marginBottom = "12px";
      const hpLabel = el("label", { text: "HP" });
      hpLabel.style.cssText = "font-size: 11px; font-weight: 600; color: #666";
      hpDiv.appendChild(hpLabel);
      const hpRow = el("div", {});
      hpRow.style.display = "flex";
      hpRow.style.gap = "8px";
      hpRow.style.alignItems = "center";
      hpRow.appendChild(hpSlider);
      hpRow.appendChild(hpDisplay);
      hpDiv.appendChild(hpRow);
      inputs.push(hpDiv);

      const mpSlider = el("input") as HTMLInputElement;
      mpSlider.type = "range";
      mpSlider.min = "0";
      mpSlider.max = "9999";
      mpSlider.step = "100";
      mpSlider.value = stats.mp.toString();

      const mpDisplay = el("span", { text: stats.mp.toString() });
      mpDisplay.style.minWidth = "50px";
      mpDisplay.style.fontSize = "12px";

      mpSlider.oninput = () => {
        mpDisplay.textContent = mpSlider.value;
      };
      slidersByChar[char].mp = mpSlider;

      const mpDiv = el("div", {});
      mpDiv.style.marginBottom = "12px";
      const mpLabel = el("label", { text: "MP" });
      mpLabel.style.cssText = "font-size: 11px; font-weight: 600; color: #666";
      mpDiv.appendChild(mpLabel);
      const mpRow = el("div", {});
      mpRow.style.display = "flex";
      mpRow.style.gap = "8px";
      mpRow.style.alignItems = "center";
      mpRow.appendChild(mpSlider);
      mpRow.appendChild(mpDisplay);
      mpDiv.appendChild(mpRow);
      inputs.push(mpDiv);
    }

    // Stats
    for (const stat of STATS) {
      if (stats[stat] === undefined) continue;
      const statSlider = el("input") as HTMLInputElement;
      statSlider.type = "range";
      statSlider.min = "1";
      statSlider.max = "99";
      statSlider.value = stats[stat].toString();

      const statDisplay = el("span", { text: stats[stat].toString() });
      statDisplay.style.minWidth = "30px";
      statDisplay.style.fontSize = "12px";

      statSlider.oninput = () => {
        statDisplay.textContent = statSlider.value;
      };
      slidersByChar[char][stat] = statSlider;

      const statDiv = el("div", {});
      statDiv.style.marginBottom = "12px";
      const statLabel = el("label", { text: stat.replace(/_/g, " ").toUpperCase() });
      statLabel.style.cssText = "font-size: 11px; font-weight: 600; color: #666";
      statDiv.appendChild(statLabel);
      const statRow = el("div", {});
      statRow.style.display = "flex";
      statRow.style.gap = "8px";
      statRow.style.alignItems = "center";
      statRow.appendChild(statSlider);
      statRow.appendChild(statDisplay);
      statDiv.appendChild(statRow);
      inputs.push(statDiv);
    }

    // Apply button for this character
    const applyBtn = el("button", { className: "btn btn-secondary", text: "Apply Changes" });
    applyBtn.style.width = "100%";
    applyBtn.onclick = () => applyCharacterChanges(sd, char, slidersByChar[char], onApply);

    const applyDiv = el("div", {});
    applyDiv.style.marginTop = "12px";
    applyDiv.style.paddingTop = "12px";
    applyDiv.style.borderTop = "1px solid #ddd";
    applyDiv.appendChild(applyBtn);
    inputs.push(applyDiv);

    const charCard = el("div", { className: "card" }, inputs);
    charCard.style.marginBottom = "16px";
    const charTitle = charCard.querySelector(".card-title") || el("div", { className: "card-title", text: char.toUpperCase() });
    if (!charCard.querySelector(".card-title")) {
      charCard.insertBefore(charTitle, charCard.firstChild);
    }
    charTitle.textContent = char.toUpperCase();
    charTitle.setAttribute("style", "font-size: 14px; margin-bottom: 12px");

    panel.append(charCard);
  }

  // Gil
  try {
    const gil = sd.get("gil") as number;
    const gilSlider = el("input") as HTMLInputElement;
    gilSlider.type = "range";
    gilSlider.min = "0";
    gilSlider.max = "999999";
    gilSlider.step = "10000";
    gilSlider.value = gil.toString();

    const gilDisplay = el("span", { text: gil.toLocaleString() });
    gilDisplay.style.minWidth = "70px";
    gilDisplay.style.fontSize = "12px";

    gilSlider.oninput = () => {
      gilDisplay.textContent = parseInt(gilSlider.value).toLocaleString();
    };

    const gilRow = el("div", {});
    gilRow.style.display = "flex";
    gilRow.style.gap = "8px";
    gilRow.style.alignItems = "center";
    gilRow.style.marginBottom = "12px";
    gilRow.appendChild(gilSlider);
    gilRow.appendChild(gilDisplay);

    const gilApplyBtn = el("button", { className: "btn btn-secondary", text: "Apply Gil Change" });
    gilApplyBtn.style.width = "100%";
    gilApplyBtn.onclick = () => {
      try {
        sd.set("gil", parseInt(gilSlider.value));
        onApply?.();
      } catch (e) {
        console.error("Error applying gil:", e);
      }
    };

    const gilCard = el("div", { className: "card" }, [
      el("div", { className: "card-title", text: "GIL" }),
      gilRow,
      gilApplyBtn,
    ]);
    (gilCard.firstChild as HTMLElement).style.cssText = "font-size: 14px; margin-bottom: 12px";

    panel.append(gilCard);
  } catch {
    // Gil field may not exist
  }
}

function applyPreset(sd: SaveData, party: string[], preset: string): void {
  try {
    for (const char of party) {
      if (preset === "lv50") {
        sd.set(`${char}_level`, 50);
        sd.set(`${char}_experience`, expForLevel(50));
      } else if (preset === "lv70") {
        sd.set(`${char}_level`, 70);
        sd.set(`${char}_experience`, expForLevel(70));
      } else if (preset === "max") {
        for (const stat of STATS) {
          try {
            sd.set(`${char}_${stat}`, 99);
          } catch {
            // Stat may not exist
          }
        }
      } else if (preset === "powerup") {
        sd.set(`${char}_level`, 70);
        sd.set(`${char}_experience`, 500000);
        if (sd.game === Game.FFX2) {
          try {
            sd.set(`${char}_hp`, 9999);
            sd.set(`${char}_max_hp`, 9999);
            sd.set(`${char}_mp`, 9999);
            sd.set(`${char}_max_mp`, 9999);
          } catch {
            // May not exist
          }
        }
        for (const stat of STATS) {
          try {
            sd.set(`${char}_${stat}`, 99);
          } catch {
            // Stat may not exist
          }
        }
      }
    }

    if (preset === "powerup") {
      try {
        sd.set("gil", 999999);
      } catch {
        // Gil may not exist
      }
    }
  } catch (e) {
    console.error("Error applying preset:", e);
  }
}

function applyCharacterChanges(
  sd: SaveData,
  char: string,
  sliders: Record<string, HTMLInputElement>,
  onApply?: () => void,
): void {
  try {
    for (const [field, slider] of Object.entries(sliders)) {
      const val = parseInt(slider.value);
      if (field === "level") {
        sd.set(`${char}_level`, val);
        sd.set(`${char}_experience`, expForLevel(val));
      } else {
        sd.set(`${char}_${field}`, val);
      }
    }
    onApply?.();
  } catch (e) {
    console.error(`Error applying changes for ${char}:`, e);
  }
}
