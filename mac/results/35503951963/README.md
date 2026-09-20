# Run 35503951963 — stage 5: Glyphs 3.5 (3532) and Glyphs 4.1 (4107), plugin 0.1.4 / cli 0.2.0, commit d182d3e, 2026-09-20

https://github.com/fanzhixiang777/ProportionalBold/actions/runs/35503951963 — both jobs green (glyphs3 103 s, glyphs4 116 s).

| item | Glyphs 3.5 (3532) | Glyphs 4.1 (4107) |
|---|---|---|
| Python module (what Plugin Manager installs) | GlyphsPythonPlugin `py311`: 3.11.9, PyObjC 10.2 | GlyphsPython `main`: 3.14.6, PyObjC 12.2.1 |
| GUI: plugin loaded, Filter menu | `principalClass 0.52 s`, item listed | `principalClass 1.97 s`, item listed |
| GUI: first-launch dialogs | Welcome window: license checkbox + Continue Trial | same window, same two clicks (report-only script had an AppleScript syntax error, fixed) |
| headless: done / fallback / skipped / failed | 413 / 1 / 1 / 0 | 413 / 1 / 1 / 0 |
| headless: stem_after_offset (reopened file) | 1.405–1.496, PASS | 1.405–1.496, PASS |
| headless: corners, master, layers, save/reopen | PASS | PASS |
| headless: timing | 5.3 s / 414 → ~14 min per 65,535 | 5.1 s / 414 → ~13 min |
| propbold-compare: IoU plugin vs CLI | mean 0.9939, min 0.9802, PASS | mean 0.9939, min 0.9802, PASS |
| vs designer Bold, 412 glyphs: IoU plugin / CLI / single offset | 0.8313 / 0.8318 / 0.8287 | 0.8313 / 0.8318 / 0.8287 |
| counters closed vs designer, 412 glyphs | 18.4 % / 17.5 % / 22.1 % | same |
| counters closed vs designer, 318 CJK | 23.9 % / 22.6 % / 28.6 % | same |
| diag: detached-layer bounds (copy/copyDecomposedLayer) | 0,0,0,0 (needs attach before measuring) | correct — Glyphs 4 fixed it; the plugin attaches anyway |
| headless OTF import | `Didn't find importer plugin for file type: public.opentype-font` → the .glyphs copy is used | same |

Plugin outputs are identical between the two versions to the last unit reported. Bugsnag noise removed from logs; screenshots and `.glyphs` outputs stay in the artifacts.
