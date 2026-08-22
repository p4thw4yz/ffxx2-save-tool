// Load a save's bytes, read/edit named fields, export it back out - with
// the platform header and checksum handled automatically. A straight port
// of the Python project's save_data.py.

import { Game, updateChecksum } from "./checksum";
import { readField, writeField, type FieldDef } from "./fields";
import { FFX_FIELDS } from "./generated/fieldsFfx";
import { FFX2_FIELDS } from "./generated/fieldsFfx2";

export type Platform = "pc" | "vita" | "switch";

// Confirmed against real hardware for both games: Switch prepends an
// 8-byte header; PC and Vita saves have none.
export const HEADER_LEN: Record<Platform, number> = { pc: 0, vita: 0, switch: 8 };

// Both games' checksum algorithms are validated (see checksum.ts).
const CHECKSUM_SUPPORTED: Record<Game, boolean> = { [Game.FFX]: true, [Game.FFX2]: true };

function buildIndex(fields: FieldDef[]): Map<string, FieldDef> {
  const m = new Map<string, FieldDef>();
  for (const f of fields) m.set(f.name, f);
  return m;
}

const FIELDS_BY_GAME: Record<Game, FieldDef[]> = {
  [Game.FFX]: FFX_FIELDS,
  [Game.FFX2]: FFX2_FIELDS,
};

const FIELDS_INDEX: Record<Game, Map<string, FieldDef>> = {
  [Game.FFX]: buildIndex(FFX_FIELDS),
  [Game.FFX2]: buildIndex(FFX2_FIELDS),
};

export class UnknownFieldError extends Error {}

export class SaveData {
  readonly game: Game;
  readonly platform: Platform;
  data: Uint8Array;
  readonly headerLen: number;
  private readonly fieldsIndex: Map<string, FieldDef>;

  constructor(game: Game, platform: Platform, raw: Uint8Array) {
    this.game = game;
    this.platform = platform;
    this.data = new Uint8Array(raw); // own copy - never aliases the caller's buffer
    this.headerLen = HEADER_LEN[platform];
    this.fieldsIndex = FIELDS_INDEX[game];
  }

  fieldList(): FieldDef[] {
    return FIELDS_BY_GAME[this.game];
  }

  private field(name: string): FieldDef {
    const f = this.fieldsIndex.get(name);
    if (!f) {
      throw new UnknownFieldError(`no field ${JSON.stringify(name)} for ${this.game} (known fields: ${this.fieldsIndex.size})`);
    }
    return f;
  }

  get(name: string): number | boolean {
    return readField(this.data, this.field(name), this.headerLen);
  }

  set(name: string, value: number | boolean): void {
    writeField(this.data, this.field(name), value, this.headerLen);
  }

  /** Returns {name: current_value} for every known field. */
  fields(): Record<string, number | boolean> {
    const out: Record<string, number | boolean> = {};
    for (const name of this.fieldsIndex.keys()) out[name] = this.get(name);
    return out;
  }

  exportBytes(recomputeChecksum = true): Uint8Array {
    if (recomputeChecksum && CHECKSUM_SUPPORTED[this.game]) {
      return updateChecksum(this.data, this.game, this.headerLen);
    }
    return new Uint8Array(this.data);
  }

  checksumSupported(): boolean {
    return CHECKSUM_SUPPORTED[this.game];
  }
}
