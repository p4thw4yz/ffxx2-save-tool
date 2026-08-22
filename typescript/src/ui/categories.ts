export const FFX_PARTY_ORDER = ["tidus", "yuna", "auron", "kimahri", "wakka", "lulu", "rikku"];
export const FFX2_PARTY_ORDER = ["yuna", "rikku", "paine"];
const FFX_AEONS = ["seymour", "valefor", "ifrit", "ixion", "shiva", "bahamut", "anima", "yojimbo", "cindy", "sandy", "mindy"];
export const ACTIVATION_LABELS: Record<number, string> = { 17: "Active", 16: "Reserve", 0: "Inactive" };

export const CATEGORIES = ["All", "Core", "Story", "Flags", "Misc", "Tidus", "Yuna", "Auron", "Kimahri", "Wakka", "Lulu", "Rikku", "Paine", "Aeons"];

export function categoryOf(name: string): string {
  if (name === "room_number" || name === "spawn_point" || name === "storyline_progress") return "Story";
  const prefixes: [string, string][] = [
    ["paine_", "Paine"],
    ["story_", "Story"],
    ["requisite_", "Story"],
    ["flag_", "Flags"],
    ["cond_", "Flags"],
    ["num_", "Misc"],
    ["raw_", "Misc"],
  ];
  for (const [prefix, label] of prefixes) {
    if (name.startsWith(prefix)) return label;
  }
  for (const char of FFX_PARTY_ORDER) {
    if (name.startsWith(`${char}_`)) return char[0].toUpperCase() + char.slice(1);
  }
  for (const aeon of FFX_AEONS) {
    if (name.startsWith(`${aeon}_`)) return "Aeons";
  }
  return "Core";
}
