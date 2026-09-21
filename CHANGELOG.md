# Changelog

## plugin 1.0.1 (bundle 7) — 2026-09-21
- Menu item moved from Filter to Edit at the maintainer's request (schriftgestalt/glyphs-packages PR #219). No other change.

## propbold-cli 0.2.0 — Windows 11 verified 2026-09-20 (65,535 glyphs in 541 s, ots clean, installs, Word renders); `propbold-compare --report` writes the reference-free hand-work list

## plugin 1.0.0 (bundle 6) — 2026-09-20
- First release considered verified: Glyphs 3.5 (3532) and Glyphs 4.1 (4107) on GitHub Actions macOS runners, GUI and headless
  (run 35503951963): plugin loads, menu item present, 413/415 test glyphs emboldened, 1 fallback, 0 failed; output of the two
  versions at mean IoU 0.9998, minimum 0.9949; vs the command-line tool mean 0.994, minimum 0.980 (corrected 2026-09-21).
- Same code as 0.1.4; version bump and README only. Measured effect vs the designer's Bold (Noto Sans CJK TC): IoU 0.831 vs 0.829
  for one Offset Curve value; closed counters 23.9 % vs 28.6 % on 318 CJK glyphs, 18.4 % vs 22.1 % on 412 glyphs.

## plugin 0.1.2 (bundle version 3) — unreleased, awaiting the Mac run
- `emboldenFont(font, ratio, master=None, glyphLimit=None)` is the headless entry point; the menu item only adds the dialog.
- Single 12-argument `GlyphsFilterOffsetCurve` call (declared identically in the Glyphs 3 and 4 SDK stubs); no try/except masking.
- `MAC_RUNBOOK.md`, `mac/headless_check.py`, `mac/glyphs_remote.py`, `testdata/` for the one-day Mac verification.

## propbold-cli 0.1.2 — release candidate (2026-09-19)
- TTF output installs on Windows 11 (verified by hand: installer, font viewer family name, CJK
  rendering at all sizes, app font lists). Root cause of the earlier rejection: no name ID 4.
- name IDs 1–6 for (3,1,0x409) and (1,0,0); OS/2 copied from source and patched; head.flags 0x000B
  with lsb == xMin; gasp; vhea/vmtx/GSUB/GPOS/GDEF/BASE copied verbatim.
- `tests/test_windows_conventions.py` pins the above; `tests/test_large_font.py` builds 65,535 glyphs.

## 0.1.1
- post format 3.0 for TTF output (format 2.0 overflowed its uint16 name index on 65,535 glyphs).
- Pipeline split into `embolden_glyphs` / `assemble_ttf`; 65,535-glyph tests.

## 0.1.0
- First CLI: .glyphs / .ufo / .otf|.ttf input, `--ratio`, parity tests with the Glyphs plugin.

## plugin 0.1.4 / propbold-cli 0.2.0 — stage 4 (2026-09-20)
- Unmeasurable glyphs (fewer than 6 ink runs) get the font's median stem as a fallback, counted as
  `fallback` — never as done, never as an offset of 0 (plugin: `NoStem` + second phase; CLI: two passes).
- CLI `MITER_LIMIT = 1.5`: closest pathops reproduction of Glyphs' short diagonal tips that keeps right angles square.
- In-Glyphs bounds check replaced by `1.stem_after_offset` (bold stem / regular stem in [1.38, 1.56]);
  cross-engine agreement is `propbold-compare` (IoU plugin vs CLI, counters vs the designer's weight), workflow step 50.
- Real plugin output (Glyphs 3.5 build 3532, 413 glyphs): IoU plugin vs CLI 0.993; vs designer Bold, CJK: IoU 0.855,
  counters closed 23.9 % (plugin) vs 28.6 % (single global offset).
