"""propbold-compare — measure a plugin-made master against the CLI's own output on the same file.

    propbold-compare <font-with-two-masters.glyphs> [--ratio 1.45] [--gt DesignerBold.otf] [--json out.json] [--report report.txt]

--report writes the reference-free hand-work list (no designer weight needed): every glyph whose
counter count dropped from the source master to the output master, and every glyph that used the
fallback stem. This is the report delivered with the service.

Master 0 is the source, the last master is the plugin's output. For every glyph with paths:
  IoU(plugin, CLI)          — the two engines on identical outlines; tips are a negligible area, so this
                              is the agreement metric (bounds are dominated by sharp diagonal tips)
  stem/offset recorded by the plugin vs the CLI's
  counters closed vs GT     — if --gt is given: n_counters(output) < n_counters(designer glyph)
                              for plugin, CLI and a single global offset (naive, d fitted to GT median)
Exit code 1 if any glyph has IoU(plugin, CLI) < 0.97 or the mean is < 0.99.
"""
from __future__ import annotations
import argparse
import json
import sys
import numpy as np
import pathops
from .core import path_from_glyphset, proportional_bold, dilate, stem_width
from .spec import DEFAULT_RATIO


def iou(a, b):
    for _ in range(2):
        try:
            inter = pathops.op(a, b, pathops.PathOp.INTERSECTION); inter.simplify()
            union = pathops.op(a, b, pathops.PathOp.UNION); union.simplify()
            return abs(inter.area) / abs(union.area) if abs(union.area) else 1.0
        except pathops.PathOpsError:
            a = pathops.Path(a); a.simplify(); b = pathops.Path(b); b.simplify()
    return None


def n_counters(path):
    p = pathops.Path(path); p.simplify()
    cw = sum(1 for c in p.contours if c.clockwise)
    n = len(list(p.contours))
    return min(cw, n - cw)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="propbold-compare", description=__doc__.split("\n")[0])
    ap.add_argument("font", help=".glyphs file: master 0 = source, last master = plugin output")
    ap.add_argument("--ratio", type=float, default=DEFAULT_RATIO)
    ap.add_argument("--gt", help="designer-drawn target weight (OTF/TTF) for the counter statistics")
    ap.add_argument("--json", help="write per-glyph rows here")
    ap.add_argument("--report", help="write the reference-free hand-work list (counters lost, fallback stems) as text")
    a = ap.parse_args(argv)

    import glyphsLib
    from .io_glyphs import _MasterGlyphSet
    g = glyphsLib.GSFont(a.font)
    if len(g.masters) < 2:
        print("need a file with at least two masters"); return 2
    src, out = g.masters[0], g.masters[-1]
    gs_src, gs_out = _MasterGlyphSet(g, src.id), _MasterGlyphSet(g, out.id)
    gt_gs = gt_cmap = None
    if a.gt:
        from fontTools.ttLib import TTFont
        gt = TTFont(a.gt); gt_gs, gt_cmap = gt.getGlyphSet(), gt.getBestCmap()

    # pass 1: fallback stem, and (with GT) the best single global offset for the naive reference
    measured = []
    for gl in g.glyphs:
        lr = gl.layers[src.id]
        if lr is None or not lr.paths:
            continue
        try:
            w = stem_width(path_from_glyphset(gs_src, gl.name))
            if w:
                measured.append(w)
        except Exception:
            pass
    measured.sort()
    fallback = measured[len(measured) // 2] if measured else None
    naive_d = (a.ratio - 1.0) / 2.0 * fallback if fallback else 0.0

    rows = []
    for gl in g.glyphs:
        lr, lo = gl.layers[src.id], gl.layers[out.id]
        if lr is None or lo is None or not lr.paths:
            continue
        try:
            p_src = path_from_glyphset(gs_src, gl.name); p_plug = path_from_glyphset(gs_out, gl.name)
        except Exception as e:
            rows.append({"name": gl.name, "error": repr(e)}); continue
        if p_src.bounds is None or p_plug.bounds is None:
            continue
        p_cli, info = proportional_bold(p_src, a.ratio, fallback_stem=fallback)
        ud = dict(lo.userData).get("proportionalBold", {}) or {}
        u = int(gl.unicode, 16) if gl.unicode else None
        r = {"name": gl.name, "unicode": u, "iou_plugin_cli": iou(p_plug, p_cli),
             "stem_plugin": ud.get("stem"), "offset_plugin": ud.get("offset"), "fallback_plugin": bool(ud.get("fallback")),
             "stem_cli": info["stem"], "offset_cli": info["offset"], "fallback_cli": info["fallback"],
             "counters_src": n_counters(p_src), "counters_plugin": n_counters(p_plug), "counters_cli": n_counters(p_cli),
             "cjk": bool(u and 0x4E00 <= u <= 0x9FFF)}
        if gt_gs is not None and u in (gt_cmap or {}):
            p_gt = path_from_glyphset(gt_gs, gt_cmap[u]); p_naive = dilate(p_src, naive_d)
            r.update({"iou_plugin_gt": iou(p_plug, p_gt), "iou_cli_gt": iou(p_cli, p_gt), "iou_naive_gt": iou(p_naive, p_gt),
                      "counters_gt": n_counters(p_gt), "counters_naive": n_counters(p_naive)})
        rows.append(r)

    ok = [r for r in rows if r.get("iou_plugin_cli") is not None]
    v = np.array([r["iou_plugin_cli"] for r in ok])
    low = [(r["name"], round(r["iou_plugin_cli"], 3)) for r in ok if r["iou_plugin_cli"] < 0.97]
    print(f"glyphs compared: {len(ok)}  (errors: {sum(1 for r in rows if 'error' in r)})")
    print(f"IoU plugin vs CLI: mean {v.mean():.4f}  median {np.median(v):.4f}  min {v.min():.4f}  below 0.97: {len(low)} {low[:10]}")
    sd = [abs((r['stem_plugin'] or 0) - (r['stem_cli'] or 0)) for r in ok]
    print(f"stem plugin==CLI within 1 unit: {sum(1 for x in sd if x <= 1)} of {len(ok)}; fallback glyphs plugin {sum(r['fallback_plugin'] for r in ok)}, CLI {sum(r['fallback_cli'] for r in ok)}")
    if gt_gs is not None:
        A = [r for r in ok if r.get("iou_plugin_gt") is not None]
        for label, rs in (("all", A), ("CJK", [r for r in A if r["cjk"]])):
            if not rs:
                continue
            print(f"vs designer weight, {label} (n={len(rs)}): IoU plugin {np.mean([r['iou_plugin_gt'] for r in rs]):.4f}  "
                  f"CLI {np.mean([r['iou_cli_gt'] for r in rs]):.4f}  single-offset d={naive_d:.1f} {np.mean([r['iou_naive_gt'] for r in rs]):.4f} | "
                  f"counters closed vs designer: plugin {100*np.mean([r['counters_plugin'] < r['counters_gt'] for r in rs]):.1f}%  "
                  f"CLI {100*np.mean([r['counters_cli'] < r['counters_gt'] for r in rs]):.1f}%  single-offset {100*np.mean([r['counters_naive'] < r['counters_gt'] for r in rs]):.1f}%")
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(rows, fh, ensure_ascii=False, indent=1, default=float)
    if a.report:
        write_report(a.report, a.font, src, out, a.ratio, ok, fallback)
    bad = len(low) > 0 or v.mean() < 0.99
    print("RESULT", "FAIL" if bad else "PASS", "agreement plugin vs CLI")
    return 1 if bad else 0


def _char(u):
    try:
        return chr(u) if u else ""
    except (ValueError, OverflowError):
        return ""


def write_report(path, font_path, src, out, ratio, rows, fallback):
    """Plain-text hand-work list: where to start by hand, in the output master."""
    lost = [r for r in rows if r["counters_plugin"] < r["counters_src"]]
    fb = [r for r in rows if r["fallback_plugin"]]
    lines = []
    lines.append("Proportional Bold — hand-work report")
    lines.append("file: %s" % font_path)
    lines.append("source master: %s    output master: %s    ratio %.2f" % (src.name, out.name, ratio))
    lines.append("glyphs with outlines: %d" % len(rows))
    lines.append("")
    lines.append("1. Counters lost — %d glyphs have fewer enclosed counters in the output than in the source. Start here." % len(lost))
    for r in sorted(lost, key=lambda r: (r["counters_src"] - r["counters_plugin"], r["name"]), reverse=True):
        lines.append("   %-12s U+%04X %s  counters %d -> %d  stem %s  offset %s" % (
            r["name"], r["unicode"] or 0, _char(r["unicode"]), r["counters_src"], r["counters_plugin"],
            "%.1f" % r["stem_plugin"] if r["stem_plugin"] else "-", "%.1f" % r["offset_plugin"] if r["offset_plugin"] else "-"))
    lines.append("")
    lines.append("2. Fallback stem — %d glyphs had no measurable stem and were offset with the font's median stem (%s). Check their weight." % (
        len(fb), "%.1f" % fallback if fallback else "n/a"))
    for r in sorted(fb, key=lambda r: r["name"]):
        lines.append("   %-12s U+%04X %s  offset %s" % (r["name"], r["unicode"] or 0, _char(r["unicode"]), "%.1f" % r["offset_plugin"] if r["offset_plugin"] else "-"))
    lines.append("")
    lines.append("Everything else was emboldened by (%.2f - 1) / 2 x its own measured stem. Junctions and stroke spacing are not treated: review dense glyphs anyway." % ratio)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("report: %d counters-lost glyphs, %d fallback glyphs -> %s" % (len(lost), len(fb), path))


if __name__ == "__main__":
    sys.exit(main())
