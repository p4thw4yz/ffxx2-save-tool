// Verifies convertPlatform() against Python's platform_convert output.
// Needs a static server serving public/ at BASE_URL (fetch() needs a real
// origin to resolve relative reference URLs against) - see the command
// used to launch one in the parent README/CHANGELOG notes for this file.
// Run with:  npx tsx scripts/verify_convert.ts

import { readFileSync } from "node:fs";
import { join } from "node:path";

import { Game } from "../src/lib/checksum";
import { convertPlatform } from "../src/lib/platformConvert";

const ROOT = join(import.meta.dirname, "..", "..");
const BASE_URL = process.env.VERIFY_BASE_URL ?? "http://127.0.0.1:8124";

// platformConvert.ts fetches "/reference/..." (browser-relative); patch
// global fetch so those resolve against our throwaway static server.
const realFetch = fetch;
// @ts-expect-error - test-only global patch
globalThis.fetch = (url: string, init?: RequestInit) => realFetch(new URL(url, BASE_URL), init);

let failures = 0;
function check(label: string, cond: boolean) {
  if (!cond) {
    failures++;
    console.error(`FAIL: ${label}`);
  } else {
    console.log(`ok: ${label}`);
  }
}

async function verify(label: string, game: Game, srcPath: string, refPath: string) {
  const raw = new Uint8Array(readFileSync(join(ROOT, srcPath)));
  const out = await convertPlatform(raw, game, "pc", "switch");
  const expected = new Uint8Array(readFileSync(join(ROOT, refPath)));
  check(`${label}: size (${out.length} vs ${expected.length})`, out.length === expected.length);
  let diffAt = -1;
  for (let i = 0; i < Math.min(out.length, expected.length); i++) {
    if (out[i] !== expected[i]) {
      diffAt = i;
      break;
    }
  }
  check(`${label}: byte-identical to Python's convert_platform output`, diffAt === -1);
}

await verify("FFX pc->switch", Game.FFX, "python/reference/pc/ffx_004", "typescript/scripts/ref_ffx_switch.bin");
await verify("FFX2 pc->switch", Game.FFX2, "python/reference/pc/ffx2_001", "typescript/scripts/ref_ffx2_switch.bin");

if (failures > 0) {
  console.error(`\n${failures} check(s) failed.`);
  process.exit(1);
}
console.log("\nAll conversion parity checks passed.");
