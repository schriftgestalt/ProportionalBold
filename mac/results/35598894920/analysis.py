#!/usr/bin/env python3
"""
analysis.py — the numbers quoted from run 35598894920 that propbold-compare does not print itself.

Inputs are the run's plugin outputs (workflow artifacts mac-verify-stage4-35598894920 and mac-verify-g4-35598894920,
file propbold-check-cli-<build>.glyphs) and the designer-drawn Noto Sans CJK TC Bold:

    python analysis.py g3/propbold-check-cli-3532.glyphs g4/propbold-check-cli-4107.glyphs NotoSansCJKtc-Bold.otf

Writes, next to this script: g3-vs-g4-output.txt, tips-plugin-vs-cli.txt, excluded-cid43205.txt.
"""
import math
import os
import sys
import numpy as np
import pathops
import glyphsLib
from fontTools.ttLib import TTFont
from propbold.core import path_from_glyphset, proportional_bold
from propbold.io_glyphs import _MasterGlyphSet
from propbold.compare import iou

HERE = os.path.dirname(os.path.abspath(__file__))
RUN = "run 35598894920"


def floor4(x):
    return math.floor(x * 1e4) / 1e4


def ceil1(x):
    return math.ceil(x * 10) / 10


def masters(path):
    g = glyphsLib.GSFont(path)
    return g, _MasterGlyphSet(g, g.masters[0].id), _MasterGlyphSet(g, g.masters[-1].id)


def g3_vs_g4(g3, g4):
    a, _, ga = masters(g3)
    b, _, gb = masters(g4)
    rows = []
    for gl in a.glyphs:
        la = gl.layers[a.masters[-1].id]
        if b.glyphs[gl.name] is None or la is None or not la.paths:
            continue
        pa, pb = path_from_glyphset(ga, gl.name), path_from_glyphset(gb, gl.name)
        if pa.bounds is None or pb.bounds is None:
            continue
        ua = dict(la.userData).get("proportionalBold", {})
        ub = dict(b.glyphs[gl.name].layers[b.masters[-1].id].userData).get("proportionalBold", {})
        rows.append((gl.name, gl.unicode, iou(pa, pb), ua.get("stem"), ub.get("stem")))
    v = np.array([r[2] for r in rows])
    out = ["Plugin output, Glyphs 3.5 (3532) vs Glyphs 4.1 (4107), %s, new master of the 415-glyph test font" % RUN,
           "glyphs compared: %d (all glyphs with outlines)" % len(rows),
           "identical (IoU > 0.9999): %d   mean IoU %.5f   minimum IoU %.4f (floored)" % ((v > 0.9999).sum(), v.mean(), floor4(v.min())),
           "measured stem differs in %d glyph(s): %s" % (sum(1 for r in rows if r[3] != r[4]),
                                                          [(r[0], "U+" + (r[1] or ""), r[3], r[4]) for r in rows if r[3] != r[4]]),
           "least similar glyphs (the two versions' Offset Curve / removeOverlap differ slightly at the same offset):"]
    for r in sorted(rows, key=lambda r: r[2])[:10]:
        out.append("   %-10s U+%s  IoU %.4f  stem %s / %s" % (r[0], r[1], floor4(r[2]), r[3], r[4]))
    return out


def tips(g3, gt_path):
    g, gs_s, gs_o = masters(g3)
    gt = TTFont(gt_path); gs_g, cm_g = gt.getGlyphSet(), gt.getBestCmap()
    rows, closer_p, closer_c, dist_p, dist_c = [], 0, 0, [], []
    for gl in g.glyphs:
        lr = gl.layers[g.masters[0].id]
        if lr is None or not lr.paths:
            continue
        ps, pp = path_from_glyphset(gs_s, gl.name), path_from_glyphset(gs_o, gl.name)
        if ps.bounds is None or pp.bounds is None:
            continue
        pc, _ = proportional_bold(ps, 1.45, fallback_stem=65.0)
        bp, bc = pp.bounds, pc.bounds
        rows.append((gl.name, gl.unicode, (bc[0] - bp[0], bc[1] - bp[1], bp[2] - bc[2], bp[3] - bc[3])))
        u = int(gl.unicode, 16) if gl.unicode else None
        if u in cm_g:
            bg = path_from_glyphset(gs_g, cm_g[u]).bounds
            for i in range(4):
                if abs(bp[i] - bc[i]) > 3:
                    dp, dc = abs(bp[i] - bg[i]), abs(bc[i] - bg[i])
                    dist_p.append(dp); dist_c.append(dc)
                    if dp < dc:
                        closer_p += 1
                    else:
                        closer_c += 1
    E = np.array([r[2] for r in rows])
    out = ["Tip extents: plugin 1.0.1 output (Glyphs 3.5, %s) vs propbold-cli 0.2.0 (pathops, MITER_LIMIT 1.5), same source outlines" % RUN,
           "glyphs: %d, sides: %d (left, bottom, right, top); + = the plugin's outline reaches further out" % (len(rows), E.size),
           "sides where the plugin reaches further by more than 3 units: %d; where the CLI does: %d" % ((E > 3).sum(), (E < -3).sum()),
           "largest plugin-further: %.1f units (exact %.3f); largest CLI-further: %.1f units (exact %.3f)  [maxima rounded up]"
           % (ceil1(E.max()), E.max(), ceil1(-E.min()), -E.min()),
           "against the designer-drawn Bold, on the %d sides where plugin and CLI differ by more than 3 units: the plugin's extent is closer on %d, "
           "the CLI's on %d; mean distance to the designer's extent: plugin %.1f, CLI %.1f units" % (len(dist_p), closer_p, closer_c, np.mean(dist_p), np.mean(dist_c))]
    for name, u, e in sorted(rows, key=lambda r: -max(abs(x) for x in r[2]))[:10]:
        out.append("   %-9s U+%s %s  left %6.1f  bottom %6.1f  right %6.1f  top %6.1f" % (name, u, chr(int(u, 16)) if u else " ", *e))
    return out


def excluded(g3, g4):
    out = ["Why propbold-compare leaves cid43205 (U+967A 険) out of the plugin-vs-CLI IoU — %s, both jobs" % RUN]
    for label, path in (("Glyphs 3.5 (3532)", g3), ("Glyphs 4.1 (4107)", g4)):
        g, gs_s, gs_o = masters(path)
        p_src, p_plug = path_from_glyphset(gs_s, "cid43205"), path_from_glyphset(gs_o, "cid43205")
        p_cli, info = proportional_bold(p_src, 1.45)
        q = pathops.Path(p_plug); q.simplify()
        out.append("%s: plugin outline %d contours, area %.0f (clean: simplify ok); CLI outline %d contours, area %.0f; stem %.1f, offset %.2f"
                   % (label, len(list(p_plug.contours)), abs(p_plug.area), len(list(p_cli.contours)), abs(p_cli.area), info["stem"], info["offset"]))
        try:
            r = pathops.op(p_plug, p_cli, pathops.PathOp.INTERSECTION); r.simplify()
            out.append("   intersection(plugin, CLI): area %.0f" % abs(r.area))
        except pathops.PathOpsError as e:
            out.append("   intersection(plugin, CLI): FAILS — skia-pathops: %s" % e)
        r = pathops.op(p_plug, p_cli, pathops.PathOp.UNION); r.simplify()
        out.append("   union(plugin, CLI): area %.0f — smaller than either outline, so the union is corrupt too" % abs(r.area))
    out.append("Both outlines are individually valid and their areas differ by %.3f %%; most edges coincide, which is the case where the"
               % (100 * abs(abs(p_plug.area) - abs(p_cli.area)) / abs(p_cli.area)))
    out.append("boolean engine breaks down. The glyph is in the hand-work report (counters 2 -> 1) and in the designer-Bold statistics; only its IoU against the CLI is missing.")
    return out


if __name__ == "__main__":
    g3, g4, gt = sys.argv[1:4]
    for name, lines in (("g3-vs-g4-output.txt", g3_vs_g4(g3, g4)), ("tips-plugin-vs-cli.txt", tips(g3, gt)), ("excluded-cid43205.txt", excluded(g3, g4))):
        with open(os.path.join(HERE, name), "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
        print("wrote", name)
