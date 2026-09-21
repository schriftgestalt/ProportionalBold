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
| propbold-compare: IoU plugin vs CLI | mean 0.9939, min 0.9802 — PASS | mean 0.9939, min 0.9802 — PASS |
| vs designer Bold, 318 CJK: IoU / counters closed | 0.8547 / 23.9 % (single offset 0.8532 / 28.6 %) | 0.8548 / 23.9 % |

Glyphs 3 vs Glyphs 4 output (`g3-vs-g4-output.txt`): not identical. 292 of 414 glyphs are identical, mean IoU 0.9998,
min 0.9949; one glyph's measured stem differs (U+599A: 71.9 vs 73), the rest is the two versions' Offset Curve /
removeOverlap producing slightly different outlines at the same offset. The same difference was already present in run
35503951963, whose README called the outputs identical — that was wrong in the last digits.

Screenshots (`21-edit-menu.png`, `21-filter-menu.png`) and the `.glyphs` outputs stay in the workflow artifacts; Bugsnag lines removed from the logs.
