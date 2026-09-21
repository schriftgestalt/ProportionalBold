# Run 35623398619 — plugin 1.0.2 (bundle 8, text only), commit 5742c32, 2026-09-21

https://github.com/fanzhixiang777/ProportionalBold/actions/runs/35623398619 — both jobs green, gate steps included.

| item | Glyphs 3.5 (3532) | Glyphs 4.1 (4107) |
|---|---|---|
| plugin loaded (launch log) | `principalClass 0.67 s`, no traceback | `principalClass 1.55 s`, no traceback |
| Edit menu lists the item / Filter menu read, item absent | PASS / PASS | PASS / PASS |
| headless: pass / fail / skip | 11 / 0 / 1 | 11 / 0 / 1 |
| done / fallback / skipped / failed | 413 / 1 / 1 / 0 | 413 / 1 / 1 / 0 |
| timing, extrapolated to 65,535 glyphs | 10.2 s / 414 → ~27 min | 5.5 s / 414 → ~15 min |
| propbold-compare (runner, fixed tool) | IoU plugin vs CLI mean 0.9939, min 0.9802 over 413 glyphs, 険 excluded — PASS | mean 0.9939, min 0.9801 — PASS |

The release changes text only (dialog string, comments). Its output is geometrically identical to plugin 1.0.1's
(run 35598894920, outputs committed there): all 414 glyphs identical per glyph (minimum IoU 1.000000) in both
versions, recorded stems identical. The dialog itself is not opened by CI; its string is in plugin.py at 5742c32.

Timing varies between runs on the same runner type: this run's Glyphs 3 job extrapolates to ~27 min, run 35598894920's
to ~18 min. Bugsnag lines removed from the logs; screenshots and `.glyphs` outputs stay in the workflow artifacts.
