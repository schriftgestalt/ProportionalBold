# -*- coding: utf-8 -*-
"""
headless_check.py — runs INSIDE Glyphs (Macro panel, or pushed in by mac/glyphs_remote.py).
Exercises the ProportionalBold plugin without touching any menu or dialog and prints one
PASS/FAIL line per check plus a JSON summary. Works in Glyphs 3 (Python 3.11) and Glyphs 4 (3.14).

Set REPO below if the repository is not at ~/ProportionalBold.
"""
import json
import os
import sys
import time
import traceback

REPO = os.path.expanduser(os.environ.get("PROPBOLD_REPO", "~/ProportionalBold"))
RATIO = 1.45
TESTFONT = os.path.join(REPO, "testdata", "NotoSansCJKtc-Regular-sub415.otf")
EXPECTED = os.path.join(REPO, "testdata", "expected_sub415.json")

from GlyphsApp import Glyphs, FILTER_MENU
import objc

results = {"glyphs_version": Glyphs.versionString, "build": Glyphs.buildNumber,
           "python": sys.version.split()[0], "checks": {}}


def check(name, ok, detail=""):
    results["checks"][name] = {"ok": bool(ok), "detail": detail}
    print("%s  %s  %s" % ("PASS" if ok else "FAIL", name, detail))


def plugin_class():
    """The class Glyphs loaded from the bundle; fallback: load plugin.py under another name."""
    for cname in ("ProportionalBold", "ProportionalBoldHeadless"):
        try:
            return objc.lookUpClass(cname), cname == "ProportionalBold"
        except objc.nosuchclass_error:
            pass
    src = os.path.join(REPO, "ProportionalBold.glyphsPlugin", "Contents", "Resources", "plugin.py")
    code = open(src, encoding="utf-8").read().replace("class ProportionalBold(", "class ProportionalBoldHeadless(")
    ns = {"__file__": src, "__name__": "propbold_headless"}
    exec(compile(code, src, "exec"), ns)
    return ns["ProportionalBoldHeadless"], False


def glyph_by_unicode(font, hexcode):
    g = font.glyphs[hexcode]                       # Glyphs names imported glyphs uniXXXX
    if g is not None:
        return g
    for g in font.glyphs:
        if g.unicode and g.unicode.upper() == hexcode[3:].upper():
            return g
    return None


def oncurve_count(layer):
    return sum(1 for p in layer.paths for n in p.nodes if n.type != "offcurve")


def main():
    # CHECK 0 — plugin loaded by Glyphs, menu item present
    cls, loaded_by_glyphs = plugin_class()
    titles = [item.title() for item in Glyphs.menu[FILTER_MENU].submenu().itemArray()] if hasattr(Glyphs.menu[FILTER_MENU], "submenu") else []
    menu_ok = any("Proportional Bold" in t or "比例加粗" in t for t in titles)
    check("0.plugin_loaded", loaded_by_glyphs, "class %s; menu item %s" % ("found" if loaded_by_glyphs else "NOT loaded (fallback exec)", "present" if menu_ok else "absent"))
    plugin = cls.alloc().init()

    # open the test font without a window
    font = Glyphs.open(TESTFONT, showInterface=False)
    check("0.testfont_open", font is not None and len(font.glyphs) > 400, "%s glyphs" % (len(font.glyphs) if font else 0))
    exp = json.load(open(EXPECTED, encoding="utf-8"))
    src = font.masters[0]
    n_masters_before = len(font.masters)
    reg_nodes = {u: oncurve_count(glyph_by_unicode(font, u).layers[src.id]) for u in exp["glyphs"] if glyph_by_unicode(font, u)}

    # CHECK 1 — Offset Curve (the 12-argument GlyphsFilterOffsetCurve call) and the measurement
    t0 = time.time()
    r = plugin.emboldenFont(font, RATIO, master=src, log=print)
    secs = time.time() - t0
    check("1.no_failures", r["failed"] == 0, "done %d skipped %d failed %d %s" % (r["done"], r["skipped"], r["failed"], r["failures"][:5]))
    check("1.median_stem", abs(r["medianStem"] - exp["median_stem_regular"]) <= 2, "%.1f vs expected %.1f" % (r["medianStem"], exp["median_stem_regular"]))
    newId = r["masterId"]
    tol = exp["tolerance_units"]
    bad = []
    for u, e in exp["glyphs"].items():
        g = glyph_by_unicode(font, u)
        if g is None:
            bad.append((u, "missing")); continue
        b = g.layers[newId].bounds
        got = [b.origin.x, b.origin.y, b.origin.x + b.size.width, b.origin.y + b.size.height]
        if max(abs(a - c) for a, c in zip(got, e["expected_bold_bounds"])) > tol:
            bad.append((e["char"], [round(v, 1) for v in got], e["expected_bold_bounds"]))
    check("1.bounds_match_cli", not bad, "tolerance %d units; mismatches: %s" % (tol, bad[:4]))
    rounded = []
    for u in reg_nodes:
        g = glyph_by_unicode(font, u)
        n_new = oncurve_count(g.layers[newId])
        if n_new > reg_nodes[u] * 1.3 + 2:
            rounded.append((exp["glyphs"][u]["char"], reg_nodes[u], n_new))
    check("1.corners_not_rounded", not rounded, "on-curve nodes regular -> bold: %s" % (rounded[:4] or "unchanged within 30%"))

    # CHECK 2 — master.copy() + new id, layer assignment, save/reopen survives
    check("2.master_added", len(font.masters) == n_masters_before + 1 and font.masters[-1].id == newId and newId != src.id,
          "masters %d -> %d, ids distinct %s" % (n_masters_before, len(font.masters), newId != src.id))
    empty = [g.name for g in font.glyphs if g.layers[src.id] and len(g.layers[src.id].paths) and g.layers[newId] is not None and len(g.layers[newId].paths) == 0]
    check("2.layers_have_paths", not empty, "new-master layers without paths: %d %s" % (len(empty), empty[:5]))
    ax = "n/a"
    try:
        ax = "%s -> %s" % (src.axes[0], font.masters[-1].axes[0])
    except Exception:
        pass
    out = os.path.join(os.path.expanduser("~/Desktop"), "propbold-check-%s.glyphs" % Glyphs.versionString.split()[0])
    font.save(out)
    font.close()
    re = Glyphs.open(out, showInterface=False)
    ok = re is not None and len(re.masters) == n_masters_before + 1 and all(g.layers[re.masters[-1].id] is not None for g in re.glyphs)
    check("2.save_reopen", ok, "saved %s; masters %d; axes %s" % (out, len(re.masters) if re else -1, ax))
    if re:
        re.close()

    # CHECK 3 — timing: extrapolate the 415-glyph run to 65,535 glyphs
    per = secs / max(r["done"] + r["skipped"], 1)
    est = per * 65535 / 60.0
    check("3.timing", est <= 30, "%.1fs for %d glyphs -> %.1f ms/glyph -> ~%.0f min for 65,535 (limit 30)" % (secs, r["done"] + r["skipped"], per * 1000, est))

    results["summary"] = r
    results["seconds"] = secs
    print("JSON " + json.dumps(results, ensure_ascii=False))
    resfile = os.path.join(REPO, "mac", "results-%s.json" % results["build"])
    with open(resfile, "w", encoding="utf-8") as fh:
        json.dump(results, fh, ensure_ascii=False, indent=1)
    print("wrote", resfile)


try:
    main()
except Exception:
    print("FAIL  uncaught\n" + traceback.format_exc())
