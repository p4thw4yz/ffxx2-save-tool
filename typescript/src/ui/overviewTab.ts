import { state } from "../state";
import type { SaveData } from "../lib/saveData";
import { FFX_CHECKPOINTS } from "../lib/generated/checkpoints";
import { el, formatInt, formatHms } from "./helpers";
import { FFX_PARTY_ORDER, FFX2_PARTY_ORDER, ACTIVATION_LABELS } from "./categories";

function nearestCheckpoint(progress: number): string | null {
  let best: { label: string; progress: number } | null = null;
  for (const c of FFX_CHECKPOINTS) {
    if (c.progress !== null && c.progress <= progress && (!best || c.progress > best.progress)) {
      best = { label: c.label, progress: c.progress };
    }
  }
  return best ? best.label : null;
}

function statTile(label: string, value: string, sub?: string): HTMLElement {
  const children = [el("div", { className: "stat-tile-label", text: label }), el("div", { className: "stat-tile-value", text: value })];
  if (sub) children.push(el("div", { className: "stat-tile-sub", text: sub }));
  return el("div", { className: "stat-tile" }, children);
}

function statRow(label: string, value: string | number): HTMLElement {
  return el("div", { className: "party-card-stat-row" }, [
    el("span", { className: "party-card-stat-label", text: label }),
    el("span", { className: "party-card-stat-value", text: String(value) }),
  ]);
}

function partyCard(name: string, subtitle: string, rows: [string, string | number][], extraLines: string[]): HTMLElement {
  const children: HTMLElement[] = [
    el("div", { className: "party-card-name", text: name[0].toUpperCase() + name.slice(1) }),
    el("div", { className: "party-card-sub", text: subtitle }),
  ];
  for (const [l, v] of rows) children.push(statRow(l, v));
  if (extraLines.length) {
    children.push(el("div", { className: "party-card-extra" }, extraLines.map((line) => el("div", { text: line }))));
  }
  return el("div", { className: "party-card" }, children);
}

function renderFfxOverview(container: HTMLElement, sd: SaveData): void {
  const gil = sd.get("gil") as number;
  const playtime = sd.get("game_time_seconds") as number;
  const battles = sd.get("battles_fought") as number;
  const room = sd.get("room_number") as number;
  const progress = sd.get("storyline_progress") as number;
  const checkpoint = nearestCheckpoint(progress);

  const tiles = el("div", { className: "stat-tile-row" }, [
    statTile("Gil", formatInt(gil)),
    statTile("Play Time", formatHms(playtime)),
    statTile("Battles Fought", formatInt(battles)),
    statTile("Story Progress", formatInt(progress), checkpoint ? `near: ${checkpoint}` : `room ${room}`),
  ]);

  const cards = FFX_PARTY_ORDER.map((name) => {
    const hp = sd.get(`${name}_current_hp`) as number;
    const mp = sd.get(`${name}_current_mp`) as number;
    const baseHp = sd.get(`${name}_base_hp`) as number;
    const baseMp = sd.get(`${name}_base_mp`) as number;
    const activation = sd.get(`${name}_activation_type`) as number;
    const status = ACTIVATION_LABELS[activation] ?? `Unknown (${activation})`;
    const gauge = sd.get(`${name}_overdrive_gauge`) as number;
    const gaugeMax = sd.get(`${name}_overdrive_gauge_max`) as number;
    const abilityFields = sd.fieldList().filter((f) => f.name.startsWith(`${name}_ability_`));
    const known = abilityFields.filter((f) => sd.get(f.name)).length;
    return partyCard(
      name,
      status,
      [
        ["HP", formatInt(hp)],
        ["MP", formatInt(mp)],
      ],
      [
        `Abilities unlocked: ${known} / ${abilityFields.length}`,
        `Overdrive gauge: ${gauge} / ${gaugeMax}`,
        `Base HP/MP bonus: ${baseHp} / ${baseMp}`,
      ],
    );
  });

  container.append(tiles, el("div", { className: "party-grid" }, cards));
}

function renderFfx2Overview(container: HTMLElement, sd: SaveData): void {
  const gil = sd.get("gil") as number;
  const playtime = sd.get("gametime_seconds") as number;
  const chapter = sd.get("chapter") as number;
  const encounters = sd.get("encounters") as number;
  const primers = sd.get("al_bhed_primer_count") as number;

  const tiles = el("div", { className: "stat-tile-row" }, [
    statTile("Gil", formatInt(gil)),
    statTile("Play Time", formatHms(playtime)),
    statTile("Chapter", formatInt(chapter)),
    statTile("Encounters", formatInt(encounters)),
    statTile("Al Bhed Primers", formatInt(primers)),
  ]);

  const cards = FFX2_PARTY_ORDER.map((name) => {
    const level = sd.get(`${name}_level`) as number;
    const hp = sd.get(`${name}_hp`) as number;
    const maxHp = sd.get(`${name}_max_hp`) as number;
    const mp = sd.get(`${name}_mp`) as number;
    const maxMp = sd.get(`${name}_max_mp`) as number;
    const exp = sd.get(`${name}_experience`) as number;
    const nextExp = sd.get(`${name}_next_level_exp`) as number;
    const dressphere = sd.get(`${name}_dressphere`) as number;
    return partyCard(
      name,
      `Level ${level}`,
      [
        ["HP", `${formatInt(hp)} / ${formatInt(maxHp)}`],
        ["MP", `${formatInt(mp)} / ${formatInt(maxMp)}`],
      ],
      [`Experience: ${formatInt(exp)} / ${formatInt(nextExp)}`, `Dressphere: #${dressphere}`],
    );
  });

  container.append(tiles, el("div", { className: "party-grid" }, cards));
}

export function renderOverview(container: HTMLElement): void {
  container.replaceChildren();
  const card = el("div", { className: "card" }, [
    el("div", { className: "card-title", text: "Save summary" }),
    el("div", {
      className: "card-subtitle",
      text: "Gil, play time, story progress, and a quick look at each party member - upload a save to see it filled in.",
    }),
  ]);
  container.append(card);

  const sd = state.saveData;
  if (!sd || !state.game) {
    card.append(el("div", { className: "help-text", text: "Upload a save to see its overview." }));
    return;
  }

  if (state.game === "ffx") renderFfxOverview(card, sd);
  else renderFfx2Overview(card, sd);
}
