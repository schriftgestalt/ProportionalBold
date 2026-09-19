# Definition of done — a propbold TTF is "done" only when all of these hold

1. `pytest` green in `propbold-cli/` (parity with the plugin, 65,535-glyph assembly, Windows conventions).
2. `python -m ots <output>.ttf` → "File sanitized successfully!" (OTS is necessary, not sufficient).
3. **Installs on Windows 10/11**: double-click → *Install* succeeds, the family shows up in Word / Notepad
   font lists, Chinese text renders. Checked by hand on a real Windows machine for every release.
   Lesson learned 2026-09-19: a font with no name ID 4 passed OTS and fontTools but Windows said
   "not a valid font file".
4. Installs on macOS (Font Book validation passes) — checked by hand.
5. Vertical text (`vert`) and kerning still work in the output: `vhea/vmtx/GSUB/GPOS/GDEF/BASE` copied.
6. The plugin's Glyphs 3 run on a Mac, and the Glyphs 4 run, both produce a master (not yet done).

Diagnostic switches (environment variables, not CLI flags — never needed in normal use):
- `PROPBOLD_MAX_GLYPHS=65534` writes only the first N glyphs (layout tables are then dropped).
- `PROPBOLD_NO_LAYOUT=1` skips copying vhea/vmtx/GSUB/GPOS/GDEF/BASE.
