import { Game } from "./lib/checksum";
import { SaveData, type Platform } from "./lib/saveData";

export type GameKey = "ffx" | "ffx2";

export const GAME_LABELS: Record<GameKey, Game> = { ffx: Game.FFX, ffx2: Game.FFX2 };

export interface AppState {
  rawBytes: Uint8Array | null;
  filename: string | null;
  game: GameKey | null;
  platform: Platform | null;
  saveData: SaveData | null;
  /** field name -> raw text typed into a Value cell, not yet applied */
  pendingEdits: Map<string, string>;
}

export const state: AppState = {
  rawBytes: null,
  filename: null,
  game: null,
  platform: null,
  saveData: null,
  pendingEdits: new Map(),
};

/** Rebuilds state.saveData from rawBytes/game/platform, if all three are set. */
export function rebuildSaveData(): void {
  if (state.rawBytes && state.game && state.platform) {
    state.saveData = new SaveData(GAME_LABELS[state.game], state.platform, state.rawBytes);
  } else {
    state.saveData = null;
  }
  state.pendingEdits.clear();
}

type Listener = () => void;
const listeners: Listener[] = [];

export function onStateChange(fn: Listener): void {
  listeners.push(fn);
}

export function notifyStateChange(): void {
  for (const fn of listeners) fn();
}
