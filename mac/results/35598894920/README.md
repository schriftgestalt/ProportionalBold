# Run 35598894920 — plugin 1.0.1 (bundle 7), menu item moved to Edit, commit c459d4f, 2026-09-21

https://github.com/fanzhixiang777/ProportionalBold/actions/runs/35598894920 — both jobs green, including the new gate step.

| item | Glyphs 3.5 (3532) | Glyphs 4.1 (4107) |
|---|---|---|
| Python module | GlyphsPythonPlugin `py311`: 3.11.9, PyObjC 10.2 | GlyphsPython `main`: 3.14.6, PyObjC 12.2.1 |
| plugin loaded (launch log) | `principalClass 0.88 s` | `principalClass 1.78 s` |
| Edit menu lists "Proportional Bold → New Master…" | PASS — after *Compare Family…* | PASS — after *Kerning Groups…* |
| Filter menu read and item absent | PASS — Offset Curve listed, no plugin item | PASS — Offset Curve listed, no plugin item |
| first-launch window (recorded before any click) | Welcome window: Purchase License / Continue Trial + license checkbox | same; trial until 2026-10-21 |
| headless: pass / fail / skip | 11 / 0 / 1 | 11 / 0 / 1 |
| done / fallback / skipped / failed | 413 / 1 / 1 / 0 | 413 / 1 / 1 / 0 |
| stem_after_offset on the reopened file | 1.405–1.496 | 1.405–1.496 |
| timing | 6.7 s / 414 glyphs → ~18 min per 65,535 | 5.1 s → ~13 min |
| propbold-compare: IoU plugin vs CLI (413 glyphs) | mean 0.9939, min 0.9802 — PASS | mean 0.9939, min 0.9801 — PASS (corrected 2026-09-21: floored, the runner printed 0.9802) |
| vs designer Bold, 318 CJK: mean IoU / counters closed | 0.8547 / 23.9 % (single offset 0.8532 / 28.6 %) | 0.8548 / 23.9 % |

Glyphs 3 vs Glyphs 4 output (`g3-vs-g4-output.txt`): not identical. 292 of 414 glyphs are identical, mean IoU 0.9998,
min 0.9949; one glyph's measured stem differs (U+599A: 71.9 vs 73), the rest is the two versions' Offset Curve /
removeOverlap producing slightly different outlines at the same offset. The same difference was already present in run
35503951963, whose README called the outputs identical — that was wrong in the last digits.

Excluded from the plugin-vs-CLI IoU in both jobs: cid43205 U+967A 険 — skia-pathops cannot intersect its two outlines (`excluded-cid43205.txt`). It is in the hand-work report (counters 2 → 1). `g3/50-compare-sandbox.txt` and `g4/50-compare-sandbox.txt` are the fixed propbold-compare re-run on this run's outputs (exclusion named, minima floored). `tips-plugin-vs-cli.txt`: tip extents plugin vs CLI.

Designer-Bold statistics with the fixed propbold-compare (commit 35a5f6b, `g3/50-compare-sandbox.txt`), which now includes 険: 413 glyphs / 319 CJK; mean IoU plugin 0.8313 / single offset 0.8287; counters closed 18.4 % vs 22.0 % (all), 23.8 % vs 28.5 % (CJK). The runner's `50-compare.txt` above was printed by the earlier tool (412 / 318). `analysis.py` regenerates `g3-vs-g4-output.txt`, `tips-plugin-vs-cli.txt` and `excluded-cid43205.txt` from the artifacts.

The two plugin outputs are committed here, copied byte-for-byte from the workflow artifacts so `analysis.py` stays reproducible after the artifacts expire: `g3/propbold-check-cli-3532.glyphs` (sha256 f2246f7b26c5942736a03f3245243977f79f922225a651cde64d3729547dc4c3), `g4/propbold-check-cli-4107.glyphs` (sha256 0500a5079b06d594865dfa8c6033c5d04a09af5272707a222bacfb8f6943bd88). Screenshots stay in the artifacts; Bugsnag lines removed from the logs.
