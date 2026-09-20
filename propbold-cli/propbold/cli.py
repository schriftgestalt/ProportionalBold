"""propbold <font> [--ratio 1.45]  — never overwrites the input; output goes next to it."""
from __future__ import annotations
import argparse
import os
import sys
import time
from .spec import DEFAULT_RATIO


def _dst(src, ratio):
    root, ext = os.path.splitext(src.rstrip("/\\"))
    tag = f"-propbold{int(round(ratio * 100)):03d}"
    ext = ext.lower()
    if ext in (".otf", ".ttf"):
        return root + tag + ".ttf"
    return root + tag + ext


def main(argv=None):
    ap = argparse.ArgumentParser(prog="propbold",
        description="Per-glyph proportional emboldening: offset = (ratio-1)/2 x each glyph's own stem. "
                    "Same rule as the ProportionalBold Glyphs plugin.")
    ap.add_argument("font", help=".glyphs (new master appended, source = first master), .ufo (new UFO) or .otf/.ttf (new .ttf)")
    ap.add_argument("--ratio", type=float, default=DEFAULT_RATIO, help="target stem ratio (Bold ~1.45, Black ~1.75); default %(default)s")
    a = ap.parse_args(argv)
    if not (1.0 < a.ratio < 3.0):
        ap.error("--ratio must be between 1.0 and 3.0")
    src = a.font
    if not os.path.exists(src):
        ap.error(f"not found: {src}")
    dst = _dst(src, a.ratio)
    if os.path.exists(dst):
        ap.error(f"output already exists, remove it first: {dst}")
    ext = os.path.splitext(src.rstrip("/\\"))[1].lower()
    t0 = time.time()
    print(f"propbold: {src} -> {dst}  (ratio {a.ratio:.2f})")
    if ext == ".glyphs":
        from .io_glyphs import process_glyphs as run
    elif ext == ".ufo":
        from .io_ufo import process_ufo as run
    elif ext in (".otf", ".ttf"):
        from .io_binary import process_binary as run
    else:
        ap.error("input must be .glyphs, .ufo, .otf or .ttf")
    info = run(src, dst, a.ratio, log=print)
    print(f"done in {time.time() - t0:.0f}s: {info['glyphs']} glyphs ({info.get('done', 0)} measured, {info.get('fallback', 0)} with fallback stem, "
          f"{info.get('failed', 0)} failed), median stem {info['median_stem']:.0f} -> {info['median_stem_out']:.0f} units")
    print(f"wrote {dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
