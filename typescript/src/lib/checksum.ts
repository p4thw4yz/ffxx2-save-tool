// CRC-16 checksum for FINAL FANTASY X / X-2 HD Remaster saves - a straight
// port of the Python project's checksum.py. Both games validated there
// against real reference saves; this port is checked against the same
// files for byte-identical output (see verify_parity.ts).

export const Game = { FFX: "ffx", FFX2: "ffx2" } as const;
export type Game = (typeof Game)[keyof typeof Game];

const CRC_START_OFFSET = 0x40;
const CRC_SEED = 0xffff;

// End of the checksummed core region (== PS2-era save size for each game).
const CRC_END: Record<Game, number> = {
  [Game.FFX]: 0x64f8,
  [Game.FFX2]: 0x1626c,
};

// Where the checksum bytes themselves are written (little-endian uint16).
const CHECKSUM_LOCATION_A = 0x1a; // shared by FFX and FFX2
const CHECKSUM_LOCATION_B: Record<Game, number> = {
  [Game.FFX]: 0x64f4,
  [Game.FFX2]: 0x16268,
};

function buildCrc16Table(): Uint16Array {
  // CRC-16-CCITT with a known off-by-one bug: the last table entry is
  // forced to 0 rather than the mathematically correct value, so the
  // table must be generated this way to match the game.
  const generator = 0x1021;
  const table = new Uint16Array(256);
  for (let dividend = 0; dividend < 256; dividend++) {
    let cur = (dividend << 8) & 0xffff;
    for (let i = 0; i < 8; i++) {
      cur = cur & 0x8000 ? ((cur << 1) ^ generator) & 0xffff : (cur << 1) & 0xffff;
    }
    table[dividend] = cur;
  }
  table[255] = 0;
  return table;
}

const CRC16_TABLE = buildCrc16Table();

function computeChecksum(data: Uint8Array, headerLen: number, game: Game): [number, number] {
  const end = headerLen + CRC_END[game];
  const checksumLoc = headerLen + CHECKSUM_LOCATION_B[game];
  let checksum = CRC_SEED;
  for (let i = headerLen + CRC_START_OFFSET; i < end; i++) {
    // The checksum bytes read as 0 while computing (whatever value is
    // already there, stale or not, must be ignored).
    const byte = i === checksumLoc || i === checksumLoc + 1 ? 0 : data[i];
    const tableIndex = ((checksum >> 8) ^ byte) & 0xff;
    checksum = ((checksum << 8) ^ CRC16_TABLE[tableIndex]) & 0xffff;
  }
  checksum ^= CRC_SEED;
  return [checksum & 0xff, (checksum >> 8) & 0xff];
}

/** Returns a copy of `data` with both checksum locations rewritten to the
 * correct value for its current contents. `headerLen` is 8 for a
 * Switch-formatted save (8-byte header prepended), 0 otherwise. */
export function updateChecksum(data: Uint8Array, game: Game, headerLen = 0): Uint8Array {
  const out = new Uint8Array(data);
  const [lo, hi] = computeChecksum(out, headerLen, game);
  out[headerLen + CHECKSUM_LOCATION_A] = lo;
  out[headerLen + CHECKSUM_LOCATION_A + 1] = hi;
  const bLoc = headerLen + CHECKSUM_LOCATION_B[game];
  out[bLoc] = lo;
  out[bLoc + 1] = hi;
  return out;
}

/** Returns the (A, B) checksum values currently stored in `data`, each a
 * little-endian uint16, for comparison against a freshly computed value. */
export function readChecksum(data: Uint8Array, game: Game, headerLen = 0): [number, number] {
  const aLoc = headerLen + CHECKSUM_LOCATION_A;
  const bLoc = headerLen + CHECKSUM_LOCATION_B[game];
  const a = data[aLoc] | (data[aLoc + 1] << 8);
  const b = data[bLoc] | (data[bLoc + 1] << 8);
  return [a, b];
}
