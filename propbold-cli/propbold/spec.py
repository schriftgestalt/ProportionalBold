"""
The rule, in one place. These constants MUST stay identical to the ones at the top of
ProportionalBold.glyphsPlugin/Contents/Resources/plugin.py (tests/test_parity.py checks that).

    stem  w_g  = PCT-th percentile of ink-run lengths on N_LINES horizontal + N_LINES vertical
                 scan lines across the glyph bbox, ignoring runs longer than MAX_RUN_FRAC x bbox
    offset d_g = (ratio - 1) / 2 * w_g, capped at D_CAP * w_g
    BOX_GROWTH = 1.0 means plain offset (no skeleton shrink); <1 shrinks so the bbox grows only BOX_GROWTH x 2d
"""
DEFAULT_RATIO = 1.45     # suggested setting for Bold; suggested settings and measured designer ratios: README.md
PCT = 30
N_LINES = 24
MAX_RUN_FRAC = 0.35
D_CAP = 0.6
BOX_GROWTH = 1.0
MITER_LIMIT = 1.5        # CLI only (pathops stroke join). Keeps 90-degree corners square (a right angle needs a
                         # miter limit of at least sqrt(2)). How the CLI's tips compare with the plugin's: README.md.
# Unmeasurable glyphs (tiny dots, marks: fewer than 6 ink runs) get the font's median stem as a
# FALLBACK stem, counted separately as "fallback" — never as done with d = 0, never silently.
