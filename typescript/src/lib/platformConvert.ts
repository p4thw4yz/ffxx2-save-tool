// Convert a save's raw bytes between platforms, using this project's own
// bundled reference saves (public/reference/) for the target header/size -
// a straight port of the Python project's platform_convert.py, adapted to
// fetch its reference files instead of reading them off local disk.

import { Game } from "./checksum";
import { HEADER_LEN, type Platform } from "./saveData";

// Real save files bundled under public/reference/ - see README.md for how
// these were validated. No confirmed real FFX2 Vita sample yet, so that
// one falls back to the PC reference (best available guess; PC and Vita
// are confirmed to share format for FFX, unconfirmed but assumed for FFX2).
const REFERENCE_URLS: Record<string, string> = {
  [refKey(Game.FFX, "switch")]: "/reference/switch/ffx_001",
  [refKey(Game.FFX, "pc")]: "/reference/pc/ffx_004",
  [refKey(Game.FFX, "vita")]: "/reference/vita/ffx_004",
  [refKey(Game.FFX2, "switch")]: "/reference/switch/ffx2_main_001",
  [refKey(Game.FFX2, "pc")]: "/reference/pc/ffx2_001",
  [refKey(Game.FFX2, "vita")]: "/reference/pc/ffx2_001",
};

function refKey(game: Game, platform: Platform): string {
  return `${game}:${platform}`;
}

const referenceCache = new Map<string, Uint8Array>();

async function loadReference(game: Game, platform: Platform): Promise<Uint8Array | null> {
  const key = refKey(game, platform);
  const cached = referenceCache.get(key);
  if (cached) return cached;
  const url = REFERENCE_URLS[key];
  if (!url) return null;
  const res = await fetch(url);
  if (!res.ok) return null;
  const bytes = new Uint8Array(await res.arrayBuffer());
  referenceCache.set(key, bytes);
  return bytes;
}

function fit(data: Uint8Array, target: number | null): Uint8Array {
  if (target === null || data.length === target) return data;
  if (data.length < target) {
    const out = new Uint8Array(target);
    out.set(data);
    return out;
  }
  const excess = data.subarray(target);
  if (excess.some((b) => b !== 0)) {
    throw new Error(
      `${data.length} bytes vs target ${target}; the ${excess.length} excess bytes are not all zero, refusing to cut real data`,
    );
  }
  return data.subarray(0, target);
}

/** Returns `data` (currently formatted for `srcPlatform`) reformatted for
 * `dstPlatform` - header added/stripped and size matched to a real
 * reference save for the target. */
export async function convertPlatform(
  data: Uint8Array,
  game: Game,
  srcPlatform: Platform,
  dstPlatform: Platform,
): Promise<Uint8Array> {
  if (srcPlatform === dstPlatform) return new Uint8Array(data);

  const body = data.subarray(HEADER_LEN[srcPlatform]);
  const dstHeaderLen = HEADER_LEN[dstPlatform];

  const ref = await loadReference(game, dstPlatform);
  let header: Uint8Array = new Uint8Array(0);
  let targetSize: number | null = null;
  if (ref) {
    targetSize = ref.length;
    header = ref.subarray(0, dstHeaderLen);
  }

  const combined = new Uint8Array(header.length + body.length);
  combined.set(header, 0);
  combined.set(body, header.length);

  return fit(combined, targetSize);
}
