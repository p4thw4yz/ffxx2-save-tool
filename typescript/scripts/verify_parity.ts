// One-off correctness check: runs the TS port against the same real save
// files the Python project uses, and diffs the results against JSON/binary
// dumps produced by the Python source of truth (see gen_fields.py's sibling
// commands in the parent README for how those were made). Run with:
//   npx tsx scripts/verify_parity.ts
// Not part of the app build - a development-time check only.

import { readFileSync } from "node:fs";
import { join } from "node:path";

import { Game } from "../src/lib/checksum";
import { SaveData } from "../src/lib/saveData";

const ROOT = join(import.meta.dirname, "..", ".."); // scripts/ -> typescript/ -> repo root

let failures = 0;

function check(label: string, cond: boolean) {
  if (!cond) {
    failures++;
    console.error(`FAIL: ${label}`);
  }
}

function loadBytes(path: string): Uint8Array {
  return new Uint8Array(readFileSync(path));
}

function verifyFields(label: string, game: Game, savePath: string, refJsonPath: string) {
  const raw = loadBytes(join(ROOT, savePath));
  const sd = new SaveData(game, "pc", raw);
  const tsFields = sd.fields();

  const refFields: Record<string, number | boolean> = JSON.parse(readFileSync(join(ROOT, refJsonPath), "utf-8"));

  const tsNames = Object.keys(tsFields);
  const refNames = Object.keys(refFields);
  check(`${label}: field count matches (${tsNames.length} vs ${refNames.length})`, tsNames.length === refNames.length);

  let mismatches = 0;
  for (const name of refNames) {
    if (!(name in tsFields)) {
      mismatches++;
      if (mismatches <= 5) console.error(`  ${label}: missing field ${name}`);
      continue;
    }
    if (tsFields[name] !== refFields[name]) {
      mismatches++;
      if (mismatches <= 5) console.error(`  ${label}: ${name} = ${tsFields[name]} (TS) vs ${refFields[name]} (Python)`);
    }
  }
  check(`${label}: all ${refNames.length} field values match`, mismatches === 0);
  console.log(`${label}: checked ${refNames.length} fields, ${mismatches} mismatches`);
}

function verifyRoundTrip(
  label: string,
  game: Game,
  savePath: string,
  edits: Array<[string, number | boolean]>,
  refBinPath: string,
) {
  const raw = loadBytes(join(ROOT, savePath));
  const sd = new SaveData(game, "pc", raw);
  for (const [name, value] of edits) sd.set(name, value);
  const out = sd.exportBytes(true);

  const expected = loadBytes(join(ROOT, refBinPath));
  check(`${label}: output size matches (${out.length} vs ${expected.length})`, out.length === expected.length);

  let diffAt = -1;
  for (let i = 0; i < Math.min(out.length, expected.length); i++) {
    if (out[i] !== expected[i]) {
      diffAt = i;
      break;
    }
  }
  check(`${label}: output bytes are identical to Python's`, diffAt === -1);
  if (diffAt !== -1) {
    console.error(`  ${label}: first diff at byte ${diffAt}: TS=${out[diffAt]} Python=${expected[diffAt]}`);
  } else {
    console.log(`${label}: byte-identical to Python output (${out.length} bytes)`);
  }
}

verifyFields("FFX", Game.FFX, "python/reference/pc/ffx_004", "typescript/scripts/ref_ffx.json");
verifyFields("FFX2", Game.FFX2, "python/reference/pc/ffx2_001", "typescript/scripts/ref_ffx2.json");

verifyRoundTrip(
  "FFX round-trip",
  Game.FFX,
  "python/reference/pc/ffx_004",
  [
    ["room_number", 80],
    ["spawn_point", 3],
    ["storyline_progress", 12345],
    ["tidus_current_hp", 9999],
    ["yuna_ability_cure", false],
  ],
  "typescript/scripts/ref_ffx_edited.bin",
);

verifyRoundTrip(
  "FFX2 round-trip",
  Game.FFX2,
  "python/reference/pc/ffx2_001",
  [
    ["gil", 999999],
    ["chapter", 3],
    ["yuna_level", 50],
    ["story_rikku_hey_give_it_back_already", true],
  ],
  "typescript/scripts/ref_ffx2_edited.bin",
);

if (failures > 0) {
  console.error(`\n${failures} check(s) failed.`);
  process.exit(1);
} else {
  console.log("\nAll parity checks passed.");
}
