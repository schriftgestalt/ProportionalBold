# Run 35503661259 — stage 4 workflow (step 50 on the runner), plugin 0.1.4 / cli 0.2.0, commit 11e0ce4, 2026-09-20

https://github.com/fanzhixiang777/ProportionalBold/actions/runs/35503661259 — all steps green, `RESULT pass=11 fail=0 skip=1`.

| item | result |
|---|---|
| GUI: plugin loaded, Filter menu | `principalClass 0.52 s`; menu lists "Proportional Bold → New Master…" — PASS |
| headless: done / fallback / skipped / failed | 413 / 1 (cid00015 → median stem 65.0) / 1 / 0 |
| headless: 1.stem_after_offset on the reopened file | PASS — 一 1.439, 十 1.442, 日 1.453, 國 1.458, 永 1.405, 人 1.496, 語 1.438, 臺 1.440, 灣 1.450, 龜 1.449, 體 1.463 |
| headless: same measurement in memory (INFO only) | 1.00 for 8 glyphs, 0.95–1.00 for the rest — Glyphs' intersection cache is stale right after the batch; not a plugin defect |
| headless: corners, master added, layers, save/reopen | PASS |
| headless: timing | 5.3 s / 414 glyphs → ~14 min for 65,535 |
| step 50 propbold-compare (on the runner) | IoU plugin vs CLI mean 0.9939, min 0.9802, none below 0.97 — PASS |
| vs designer Bold, 412 glyphs | IoU plugin 0.8313 / CLI 0.8318 / single global offset 0.8287; counters closed 18.4 % / 17.5 % / 22.1 % |
| vs designer Bold, 318 CJK | IoU 0.8547 / 0.8553 / 0.8532; counters closed 23.9 % / 22.6 % / 28.6 % |

Glyphs 3.5 (3532) headless verification of the plugin is complete with these numbers. Bugsnag noise removed from the two logs; screenshots and the `.glyphs` output stay in the artifact.
