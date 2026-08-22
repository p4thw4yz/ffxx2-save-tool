# FFX / FFX2 Save Tool (client-side)

A client-side port of the [Dash version](../python/README.md) of this project -
same capabilities (convert saves between PC/Vita/Switch, edit thousands
of fields, jump to story checkpoints, browse the raw file), but runs
entirely in your browser. No backend, no upload - drop a save file in
and everything happens locally in JavaScript. Static-hostable anywhere
(Cloudflare Pages, GitHub Pages, or just open `dist/index.html`).

## Quick start

```
npm install
npm run dev
```

Open the printed local URL. `npm run build` produces a static `dist/`
folder ready to deploy anywhere.

## Tabs

Same six as the Dash app, same behavior:

- **Overview** - Gil, play time, story progress, and a card per party
  member.
- **Fields** - every known field, filterable by category or search,
  editable inline, applied with **Apply edits** (recomputes the
  checksum).
- **Story Position** *(FFX only)* - jump to one of 15 known story
  checkpoints in one click.
- **Export** - download the edited save as-is, or convert it to
  another platform.
- **Raw / Hex** - a searchable, annotated hex dump of the whole file.
- **Info** - this README, rendered in-app.

## How it's built

This is a straight TypeScript port of the Python project's logic
layer - not a rewrite from scratch:

```
src/lib/
  checksum.ts          CRC-16 - ported from checksum.py
  fields.ts             shared Field read/write engine - ported from fields.py
  saveData.ts             SaveData class - ported from save_data.py
  platformConvert.ts        platform conversion - ported from platform_convert.py,
                             fetches reference saves from public/reference/ instead
                             of reading local disk paths
  generated/
    fieldsFfx.ts             FFX's 3,116 fields - generated from ../python/fields_ffx.py
    fieldsFfx2.ts             FFX2's 632 fields - generated from ../python/fields_ffx2.py
    checkpoints.ts             FFX's 15 story checkpoints - generated from FFX_CHECKPOINTS
```

The Python project's field maps are the single source of truth - the
`generated/` files are produced by `gen_fields.py`, not hand-written, so
they can never drift out of sync with the Python source. Re-run it after
changing anything in `../python/fields_ffx.py` or `../python/fields_ffx2.py`:

```
python3 gen_fields.py
```

**Correctness**: `scripts/verify_parity.ts` and `scripts/verify_convert.ts`
check every field this port reads/writes, and every byte of platform
conversion output, against the Python implementation - loading the same
real save files and diffing the results. Both pass byte-identical
before anything here is trusted. Fixture files (`scripts/ref_*.json`,
`scripts/ref_*.bin`) are dev-only diagnostic dumps produced from the
Python implementation and diffed against - git-ignored rather than
committed, since they're derived from real save data. Run these scripts
(from `typescript/`) with:

```
npx tsx scripts/verify_parity.ts
npx tsx scripts/verify_convert.ts   # needs a static server on public/ - see the script's header comment
```

## Deploying (Cloudflare Pages)

```
npm run build
```

Point Cloudflare Pages (or any static host) at the resulting `dist/`
folder - build command `npm run build`, output directory `dist`. No
environment variables, no backend, no server-side anything.

## Reference saves

`public/reference/` holds the same real save files as
[`../python/reference/`](../python/README.md#directory-layout), used as
header/size sources for platform conversion (see the Python README for
how those were validated). They're fetched at runtime, not embedded in
the JS bundle, to keep the bundle itself small.

## Known differences from the Dash version

- Pagination is fixed (15 rows/page for Fields, 25 for Raw/Hex) rather
  than Dash's native table controls, but filtering/search work the
  same way.
- No server means no filesystem CLI equivalent to `edit.py` - editing
  only happens through the browser UI.
- Everything else - field coverage, checksum handling, story
  checkpoints, conversion logic - is the same, verified byte-for-byte
  against the Python source (see "Correctness" above).
