# Run 35503159425 — stage 3 workflow, plugin 0.1.4 / cli 0.2.0 (commit 0b4d260), macos-latest, 2026-09-20

https://github.com/fanzhixiang777/ProportionalBold/actions/runs/35503159425 — job 77 s, all steps green.

| item | result |
|---|---|
| GUI: plugin loaded (launch log) | `principalClass time: 0.52 s ProportionalBold.glyphsPlugin`, no traceback |
| GUI: Filter menu | lists "Proportional Bold → New Master…" — PASS |
| GUI: Python | Plugin Manager module GlyphsPythonPlugin py311 (3.11.9, PyObjC 10.2), `GSPythonFrameworkPath` honoured |
| headless: done / fallback / skipped / failed | 413 / 1 (cid00015, median stem 65.0) / 1 / 0 |
| headless: median stem | 65.0 (expected 63.0 ± 2) |
| headless: corners not rounded, master added, layers have paths, save/reopen | PASS |
| headless: timing | 6.5 s for 414 glyphs → ~17 min for 65,535 (limit 30) |
| headless: 1.stem_after_offset | FAIL for 一十日國 at ratio 1.00 — measurement artifact: Glyphs' intersection cache still held the pre-offset paths in memory; the saved file has 1.44–1.46 for the same glyphs (see 50-compare.txt). Check moved to the reopened file in the next commit. |
| propbold-compare on the saved output (sandbox) | IoU plugin vs CLI mean 0.9939, min 0.9802, none below 0.97 — PASS |
| vs designer Bold (Noto), 412 glyphs | IoU plugin 0.8313 / CLI 0.8318 / single global offset 0.8287; counters closed 18.4 % / 17.5 % / 22.1 % |
| vs designer Bold, 318 CJK | IoU 0.8547 / 0.8553 / 0.8532; counters closed 23.9 % / 22.6 % / 28.6 % |

`30-headless-cli.txt` and `glyphs3-launch.log` are stored with the Bugsnag lines removed. Screenshots and the 1.5 MB `.glyphs` output stay in the workflow artifact.
