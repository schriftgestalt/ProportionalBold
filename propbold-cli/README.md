# propbold (command line)

Per-glyph proportional emboldening — the command-line twin of the **ProportionalBold** Glyphs plugin.
Same rule, same constants (`propbold/spec.py` ↔ `plugin.py`, checked by `tests/test_parity.py`):

    stem  w_g  = 30th percentile of ink runs on 24+24 scan lines
    offset d_g = (ratio − 1) / 2 × w_g

Install (Windows, macOS, Linux; Python ≥ 3.9):

    pip install git+https://github.com/fanzhixiang777/ProportionalBold.git#subdirectory=propbold-cli

Use:

    propbold NotoSansCJKtc-Regular.otf --ratio 1.45

| input | output (written next to the input, never overwrites) |
|---|---|
| `Font.glyphs` | `Font-propbold145.glyphs` — same file plus one appended master, source = first master, components decomposed in the new master |
| `Font.ufo` | `Font-propbold145.ufo` — new UFO, outlines replaced |
| `Font.otf` / `Font.ttf` | `Font-propbold145.ttf` — compiled TrueType (CFF input is converted to quadratics) |

Per-glyph measurements are stored in `layer.userData["proportionalBold"]` (.glyphs) or
`glyph.lib["com.propbold.info"]` (UFO). Noto Sans CJK TC (65,535 glyphs) took 541 s on Windows 11 with 0.2.0 ([mac/results/windows-0.2.0.md](../mac/results/windows-0.2.0.md)).

## Unmeasurable glyphs (fallback policy)

A glyph whose scan lines find fewer than 6 ink runs (a dot, a tiny mark) has no stem of its own. It gets the
font's **median measured stem** as a fallback and is counted separately as `fallback` in the summary — never
as done, never as an offset of 0. The plugin does the same (`NoStem` → second phase with the median).

## Measured on real plugin output (run 35598894920: Glyphs 3.5 build 3532, headless, 2026-09-21)

`propbold-compare <plugin-output.glyphs> --gt NotoSansCJKtc-Bold.otf`:

| metric | plugin (Glyphs Offset Curve) | CLI (pathops, miter 1.5) | single global offset |
|---|---|---|---|
| IoU plugin vs CLI, same outlines | mean 0.994, min 0.980 (413 glyphs compared, run 35598894920; cid43205 U+967A excluded: skia-pathops cannot intersect its plugin and CLI outlines, whose edges largely coincide — [details](../mac/results/35598894920/excluded-cid43205.txt)) | — | — |
| mean IoU vs designer Bold, all 413 | 0.8313 | 0.8318 | 0.8287 |
| mean IoU vs designer Bold, 319 CJK | 0.8548 | 0.8553 | 0.8532 |
| counters closed vs designer, all 413 | 18.4 % | 17.4 % | 22.0 % |
| counters closed vs designer, 319 CJK | 23.8 % | 22.6 % | 28.5 % |

The designer rows include 険 (U+967A); only its IoU against the CLI is not computable. Output: [50-compare-sandbox.txt](../mac/results/35598894920/g3/50-compare-sandbox.txt).

Bounds are not a cross-engine metric: at sharp diagonal tips Glyphs' Offset Curve and pathops (miter 1.5) differ in both
directions — Glyphs' tip reaches up to 35.2 units further (人's left tip), pathops' up to 11.4 — while the area agrees at
mean IoU 0.994, minimum 0.980 over 413 glyphs, 険 excluded. Where the two tips differ by more than 3 units (163 sides),
Glyphs' extent is closer to the designer's Bold on 97 and pathops' on 66 (run 35598894920,
[tips-plugin-vs-cli.txt](../mac/results/35598894920/tips-plugin-vs-cli.txt)). `MITER_LIMIT = 1.5` keeps right angles
square (a right angle needs at least 1.414).

## Large fonts

TTF output always uses `post` format 3.0 (no glyph names). Format 2.0 indexes names with a uint16
(258 + i) and overflows on fonts with tens of thousands of custom-named glyphs — the 65,535-glyph
Noto Sans CJK crashed there on the first Windows run. Consequence: tools will show synthesised
names (`uni9F9C`, `glyph12345`) instead of `cid12345`; the cmap is intact, nothing else changes.

`tests/test_large_font.py` builds a 65,535-glyph CID-style font and runs the assemble/save path
every time. `PROPBOLD_SLOW=1 pytest` also runs the full measure/offset pipeline over all
65,535 glyphs. Real Noto Sans CJK TC on Windows 11: 65,535 glyphs in 541 s with 0.2.0
([mac/results/windows-0.2.0.md](../mac/results/windows-0.2.0.md)).

## Windows installability

`assemble_ttf` writes what Windows GDI needs and OTS does not check: name IDs 1–6 for (3,1,0x409)
and (1,0,0) including the Full name (ID 4), OS/2 copied from the source (Unicode/code-page ranges,
PANOSE, heights) with `fsSelection` REGULAR and `usWeightClass` from the ratio (1.45 → 700,
1.75 → 900), `head.flags` 0x000B with lsb == xMin, `post` 3.0, a `gasp` table, and the source's
`vhea/vmtx/GSUB/GPOS/GDEF/BASE` copied verbatim (glyph IDs are unchanged). `tests/test_windows_conventions.py`
pins all of it; the real install on Windows is still part of the definition of done (`../DOD.md`).
