# Windows 11 verification of propbold-cli 0.2.0 — 2026-09-20 (Ez, by hand)

Environment: Windows 11, Python 3.13 venv, skia-pathops 0.9.2 wheel, `pip install git+…#subdirectory=propbold-cli`.

| step | result |
|---|---|
| `propbold NotoSansCJKtc-Regular.otf --ratio 1.45` | `done in 541s: 65535 glyphs (65471 measured, 64 with fallback stem, 0 failed), median stem 64 -> 93 units` |
| fallback list | space, period and punctuation/marks: cid00001, cid00015, cid00117, cid00249, cid00255, cid00467, cid00468, cid00530, cid00733, cid01206–cid01218 |
| `python -m ots NotoSansCJKtc-Regular-propbold145.ttf` | `File sanitized successfully!` |
| Windows Font Viewer | opens as "Noto Sans CJK TC PropBold145 (TrueType)", Install works |
| Word | family listed; 臺灣鬱鑿籲龜體 renders bold |

Earlier: 0.1.2 output (A-65535-full.ttf) installed on Windows 11 on 2026-09-19; the first attempt had failed for a missing name ID 4.
