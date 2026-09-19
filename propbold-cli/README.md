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
`glyph.lib["com.propbold.info"]` (UFO). Noto Sans CJK TC (65,535 glyphs) takes ~10–15 minutes.

## Large fonts

TTF output always uses `post` format 3.0 (no glyph names). Format 2.0 indexes names with a uint16
(258 + i) and overflows on fonts with tens of thousands of custom-named glyphs — the 65,535-glyph
Noto Sans CJK crashed there on the first Windows run. Consequence: tools will show synthesised
names (`uni9F9C`, `glyph12345`) instead of `cid12345`; the cmap is intact, nothing else changes.

`tests/test_large_font.py` builds a 65,535-glyph CID-style font and runs the assemble/save path
every time (~3 s). `PROPBOLD_SLOW=1 pytest` also runs the full measure/offset pipeline over all
65,535 glyphs (~1 min on synthetic squares). Measured rate on real Noto Sans CJK TC, Windows:
65,535 glyphs in 311 s.

## Windows installability

`assemble_ttf` writes what Windows GDI needs and OTS does not check: name IDs 1–6 for (3,1,0x409)
and (1,0,0) including the Full name (ID 4), OS/2 copied from the source (Unicode/code-page ranges,
PANOSE, heights) with `fsSelection` REGULAR and `usWeightClass` from the ratio (1.45 → 700,
1.75 → 900), `head.flags` 0x000B with lsb == xMin, `post` 3.0, a `gasp` table, and the source's
`vhea/vmtx/GSUB/GPOS/GDEF/BASE` copied verbatim (glyph IDs are unchanged). `tests/test_windows_conventions.py`
pins all of it; the real install on Windows is still part of the definition of done (`../DOD.md`).
