#!/usr/bin/env python3
"""
measure_stem_ratios.py — how much thicker are the designer-drawn Bold and Black of Noto Sans CJK TC than its Regular?

Per glyph, the stem is measured with propbold's own estimator (propbold.core.stem_width: 30th percentile of ink runs on
24 horizontal + 24 vertical scan lines — the same rule the plugin and the CLI use). The ratio designer-weight / Regular is
taken per glyph, over every CJK Unified Ideograph (U+4E00–U+9FFF) that all three fonts map and that has a measurable stem.

    python measure_stem_ratios.py NotoSansCJKtc-Regular.otf NotoSansCJKtc-Bold.otf NotoSansCJKtc-Black.otf > output.txt

Fonts: https://github.com/notofonts/noto-cjk/tree/main/Sans/OTF/TraditionalChinese
"""
import hashlib
import subprocess
import sys
import time
import numpy as np
from fontTools.ttLib import TTFont
from propbold.core import path_from_glyphset, stem_width


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main(reg, bold, black):
    t0 = time.time()
    fonts = {name: TTFont(path) for name, path in (("Regular", reg), ("Bold", bold), ("Black", black))}
    cmaps = {n: f.getBestCmap() for n, f in fonts.items()}
    sets = {n: f.getGlyphSet() for n, f in fonts.items()}
    codes = [c for c in range(0x4E00, 0xA000) if all(c in cm for cm in cmaps.values())]
    stems = {n: {} for n in fonts}
    for c in codes:
        for n in fonts:
            try:
                stems[n][c] = stem_width(path_from_glyphset(sets[n], cmaps[n][c]))
            except Exception:
                stems[n][c] = None
    try:
        commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    except Exception:
        commit = "?"
    print("Designer stem ratios of Noto Sans CJK TC, measured with propbold.core.stem_width (repo commit %s)" % commit)
    for n, path in (("Regular", reg), ("Bold", bold), ("Black", black)):
        print("  %-7s %s  sha256 %s" % (n, path.split("/")[-1], sha256(path)))
    print("population: CJK Unified Ideographs U+4E00–U+9FFF mapped in all three fonts: %d code points" % len(codes))
    for n in ("Bold", "Black"):
        r = np.array([stems[n][c] / stems["Regular"][c] for c in codes if stems[n][c] and stems["Regular"][c]])
        print("%s / Regular: n=%d  median %.4f  p25 %.4f  p75 %.4f  mean %.4f  min %.4f  max %.4f"
              % (n, len(r), np.median(r), np.percentile(r, 25), np.percentile(r, 75), r.mean(), r.min(), r.max()))
    print("runtime %.0f s" % (time.time() - t0))


if __name__ == "__main__":
    main(*sys.argv[1:4])
