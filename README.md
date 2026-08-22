# FFX / FFX2 HD Remaster Save Tool

Convert FINAL FANTASY X / X-2 HD Remaster saves between PC, Vita and Switch,
and read/edit thousands of fields inside them (stats, abilities, story
position, and more). Two independent, self-contained implementations of the
same tool live here - pick whichever fits how you want to run it:

- **[`python/`](python/README.md)** - a local Dash GUI (plus a scripted
  batch-convert tool and a CLI). Needs Python + `pip install -r
  requirements.txt`.
- **[`typescript/`](typescript/README.md)** - a client-side web port with the
  same tabs and capabilities. No backend, runs entirely in the browser,
  static-hostable anywhere. Needs Node + `npm install`.

Both read/write the same save formats and are verified byte-identical against
each other (see `typescript/README.md`'s "Correctness" section) - the
TypeScript version is a direct port of the Python one, not a separate
reimplementation, and the two are developed in parallel from here on.

**Always keep your original save until you've loaded a converted/edited one
in-game and confirmed it works as expected.**

## What's here

| Capability | Status |
|---|---|
| PC ↔ Switch conversion | **Confirmed working** on real hardware, both games |
| Vita ↔ PC/Switch conversion | Container format matches (same size, no extra header); untested with a real matching save |
| Field editing | FFX: 3,116 fields (full per-character stats/abilities/perks + ~290 world-state flags). FFX2: 632 fields (full party stats + 554 story/dialogue flags) |
| Story position / chapter rewind | FFX: 15 curated checkpoints. FFX2: use its official in-game Chapter Select instead |
| Checksum | Both games validated - edits get a real, automatically-recomputed checksum |

See either subproject's README for full details, quick start, and the
reverse-engineering notes behind all of the above.

## Acknowledgments

Built on the reverse-engineering work of [`gabacode/FFXED`](https://github.com/gabacode/FFXED),
[`Meth962/FFX2SaveEditor`](https://github.com/Meth962/FFX2SaveEditor), and
[JKSV](https://github.com/J-D-K/JKSV) - see `python/README.md`'s
Acknowledgments section for specifics on what each contributed.

## License

[MIT](LICENSE)
