# -*- coding: utf-8 -*-
"""
headless_check.py — runs INSIDE Glyphs, two ways:

  headless (no GUI, CI):
    glyphs run --app "/Applications/Glyphs 3.app" --python <…/Python.framework/Versions/3.11/Python> \
               --plugins ./ProportionalBold.glyphsPlugin mac/headless_check.py
  in the app: paste into Window > Macro Panel and run.

Exercises the ProportionalBold plugin without touching any menu or dialog. One PASS/FAIL/SKIP line
per check, a JSON summary and a copy of this log are written to <repo>/mac/log/.
Checks are the ones MAC_RUNBOOK.md section F defines (U1 corners/bounds, U2 master.copy(), U3 timing).
CHECK 0's menu-item test is GUI-only: it is SKIPped, not failed, when Glyphs.menu is unavailable.
"""
import json
import os
import sys
import time
import traceback

RATIO = 1.45
LOG = []


def out(line):
    LOG.append(line)
    print(line)


# ---------------------------------------------------------------- where is the repo
def find_repo():
    env = os.environ.get("PROPBOLD_REPO")
    if env:
        return os.path.expanduser(env)
    try:
        here = os.path.dirname(os.path.abspath(__file__))       # glyphs-cli sets __file__
        cand = os.path.dirname(here)
        if os.path.isdir(os.path.join(cand, "testdata")):
            return cand
    except NameError:
        pass                                                      # Macro panel: no __file__
    return os.path.expanduser("~/ProportionalBold")


REPO = find_repo()
LOGDIR = os.path.join(REPO, "mac", "log")
os.makedirs(LOGDIR, exist_ok=True)
TESTFONT_OTF = os.path.join(REPO, "testdata", "NotoSansCJKtc-Regular-sub415.otf")
TESTFONT_GLYPHS = os.path.join(REPO, "testdata", "NotoSansCJKtc-Regular-sub415.glyphs")
EXPECTED = os.path.join(REPO, "testdata", "expected_sub415.json")

from GlyphsApp import Glyphs, FILTER_MENU  # noqa: E402
import objc  # noqa: E402

results = {"mode": None, "glyphs_version": None, "build": None, "python": sys.version.split()[0], "checks": {}}
for attr, key in (("versionString", "glyphs_version"), ("buildNumber", "build")):
    try:
        results[key] = getattr(Glyphs, attr)
    except Exception:
        pass
BUILD = str(results["build"] or "unknown").replace(".0", "")


def check(name, ok, detail=""):
    results["checks"][name] = {"ok": bool(ok), "detail": detail}
    out("%s  %s  %s" % ("PASS" if ok else "FAIL", name, detail))


def skip(name, reason):
    results["checks"][name] = {"ok": None, "skipped": reason}
    out("SKIP  %s  %s" % (name, reason))


# ---------------------------------------------------------------- GUI or headless?
def menu_available():
    try:
        Glyphs.menu[FILTER_MENU]
        return True
    except Exception:
        return False


MODE = "app" if menu_available() else "cli"
results["mode"] = MODE
out("MODE %s  Glyphs %s (%s)  Python %s  repo %s" % (MODE, results["glyphs_version"], results["build"], results["python"], REPO))


# ---------------------------------------------------------------- plugin class
def plugin_class():
    """The class Glyphs loaded from the bundle (app: Plugins folder; cli: --plugins);
    fallback: load plugin.py from the repo under another class name."""
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


def make_instance(cls):
    """alloc().init() runs loadPlugin -> settings() -> start(); start() appends a menu item and
    cannot work headless, so it is replaced by a no-op there. Fallback: an alloc()-only object,
    which is enough for the pure-Python methods we call."""
    if MODE == "cli":
        try:
            cls.start = lambda self: None
        except Exception:
            pass
    try:
        return cls.alloc().init()
    except Exception:
        out("note: alloc().init() failed, using alloc() only\n" + traceback.format_exc())
        return cls.alloc()


# ---------------------------------------------------------------- helpers
def open_test_font():
    """OTF first (what the runbook says), .glyphs copy second (same outlines, made with glyphsLib)."""
    for path in (TESTFONT_OTF, TESTFONT_GLYPHS):
        if not os.path.exists(path):
            continue
        for kwargs in ({"showInterface": False}, {}):
            try:
                f = Glyphs.open(path, **kwargs)
            except Exception as e:
                out("note: Glyphs.open(%s, %s) raised %r" % (os.path.basename(path), kwargs, e))
                f = None
            if f is not None and len(f.glyphs) > 400:
                return f, path
    return None, None


def glyph_by_unicode(font, hexcode):
    g = font.glyphs[hexcode]                       # imported OTF: glyphs are named uniXXXX
    if g is not None:
        return g
    for g in font.glyphs:
        if g.unicode and g.unicode.upper() == hexcode[3:].upper():
            return g
    return None


def oncurve_count(layer):
    return sum(1 for p in layer.paths for n in p.nodes if n.type != "offcurve")


def bounds_list(layer):
    b = layer.bounds
    return [b.origin.x, b.origin.y, b.origin.x + b.size.width, b.origin.y + b.size.height]


# ---------------------------------------------------------------- checks
def main():
    # CHECK 0 — plugin class loaded; menu item (GUI only)
    cls, loaded_by_glyphs = plugin_class()
    check("0.plugin_class_loaded", loaded_by_glyphs,
          "class %s" % ("found (loaded by Glyphs)" if loaded_by_glyphs else "NOT loaded by Glyphs; exec fallback used"))
    if MODE == "app":
        try:
            titles = [item.title() for item in Glyphs.menu[FILTER_MENU].submenu().itemArray()]
            check("0.menu_item", any("Proportional Bold" in t or "比例加粗" in t for t in titles), "Filter menu: %s" % titles[-6:])
        except Exception as e:
            check("0.menu_item", False, "could not read Filter menu: %r" % e)
    else:
        skip("0.menu_item", "GUI-only (no Glyphs.menu under glyphs-cli); the workflow reads the Filter menu with System Events instead")
    plugin = make_instance(cls)

    font, used = open_test_font()
    check("0.testfont_open", font is not None, "%s: %s glyphs" % (os.path.basename(used) if used else "no test font opened", len(font.glyphs) if font else 0))
    if font is None:
        return
    exp = json.load(open(EXPECTED, encoding="utf-8"))
    src = font.masters[0]
    n_masters_before = len(font.masters)
    reg_nodes = {}
    for u in exp["glyphs"]:
        g = glyph_by_unicode(font, u)
        if g is not None:
            reg_nodes[u] = oncurve_count(g.layers[src.id])

    # CHECK 1 — U1: the 12-argument GlyphsFilterOffsetCurve call and the scan-line measurement
    t0 = time.time()
    r = plugin.emboldenFont(font, RATIO, master=src, log=out)
    secs = time.time() - t0
    check("1.no_failures", r["failed"] == 0, "done %d fallback %d skipped %d failed %d %s" % (r["done"], r.get("fallback", 0), r["skipped"], r["failed"], r["failures"][:5]))
    check("1.fallback_rare", r.get("fallback", 0) <= max(2, 0.02 * (r["done"] + r.get("fallback", 0))),
          "%d unmeasurable glyphs given the median stem: %s" % (r.get("fallback", 0), r.get("fallbackGlyphs", [])[:10]))
    check("1.median_stem", abs(r["medianStem"] - exp["median_stem_regular"]) <= 2, "%.1f vs expected %.1f" % (r["medianStem"], exp["median_stem_regular"]))
    newId = r["masterId"]
    # Offset amount, measured the same way on the emboldened layer: bold stem / regular stem must be ~ratio.
    # (Bounds were dropped as a metric: sharp diagonal tips differ between Glyphs' Offset Curve and any
    # pathops miter limit by up to 35 units while the area agrees to 1%; propbold-compare does IoU outside.)
    lo, hi = exp.get("bold_stem_ratio_range", [1.38, 1.56])
    off = []
    for u, e in exp["glyphs"].items():
        g = glyph_by_unicode(font, u)
        if g is None:
            off.append((u, "missing")); continue
        wb = plugin.stemWidth(g.layers[newId])
        wr = plugin.stemWidth(g.layers[src.id])
        if not wb or not wr:
            off.append((e["char"], "unmeasurable", wr, wb)); continue
        if not (lo <= wb / wr <= hi):
            off.append((e["char"], round(wr, 1), round(wb, 1), round(wb / wr, 3)))
    check("1.stem_after_offset", not off, "bold/regular stem within [%.2f, %.2f] for %d glyphs; off: %s" % (lo, hi, len(exp["glyphs"]), off[:4]))
    rounded = []
    for u in reg_nodes:
        g = glyph_by_unicode(font, u)
        n_new = oncurve_count(g.layers[newId])
        if n_new > reg_nodes[u] * 1.3 + 2:
            rounded.append((exp["glyphs"][u]["char"], reg_nodes[u], n_new))
    check("1.corners_not_rounded", not rounded, "on-curve nodes regular -> bold: %s" % (rounded[:4] or "unchanged within 30%"))

    # CHECK 2 — U2: master.copy() + new id, layer assignment, save/reopen survives
    check("2.master_added", len(font.masters) == n_masters_before + 1 and font.masters[-1].id == newId and newId != src.id,
          "masters %d -> %d, ids distinct %s" % (n_masters_before, len(font.masters), newId != src.id))
    empty = [g.name for g in font.glyphs
             if g.layers[src.id] and len(g.layers[src.id].paths) and g.layers[newId] is not None and len(g.layers[newId].paths) == 0]
    check("2.layers_have_paths", not empty, "new-master layers without paths: %d %s" % (len(empty), empty[:5]))
    ax = "n/a"
    try:
        ax = "%s -> %s" % (src.axes[0], font.masters[-1].axes[0])
    except Exception:
        pass
    saved = os.path.join(LOGDIR, "propbold-check-%s-%s.glyphs" % (MODE, BUILD))
    try:
        font.save(saved)
    except Exception as e:
        out("note: font.save raised %r" % e)
    try:
        font.close()
    except Exception:
        pass
    re = None
    try:
        re = Glyphs.open(saved, showInterface=False)
    except Exception:
        try:
            re = Glyphs.open(saved)
        except Exception as e:
            out("note: reopen raised %r" % e)
    ok = re is not None and len(re.masters) == n_masters_before + 1 and all(g.layers[re.masters[-1].id] is not None for g in re.glyphs)
    check("2.save_reopen", ok, "saved %s; masters %s; axes %s" % (saved, len(re.masters) if re else "n/a", ax))
    if re is not None:
        try:
            re.close()
        except Exception:
            pass

    # CHECK 3 — U3: timing, extrapolated from the 415-glyph run to 65,535 glyphs
    per = secs / max(r["done"] + r["skipped"], 1)
    est = per * 65535 / 60.0
    check("3.timing", est <= 30, "%.1fs for %d glyphs -> %.1f ms/glyph -> ~%.0f min for 65,535 (limit 30)" % (secs, r["done"] + r["skipped"], per * 1000, est))

    results["summary"] = r
    results["seconds"] = secs
    results["testfont"] = used


try:
    main()
except Exception:
    out("FAIL  uncaught\n" + traceback.format_exc())
    results["checks"]["uncaught"] = {"ok": False, "detail": traceback.format_exc()}

n_pass = sum(1 for c in results["checks"].values() if c.get("ok") is True)
n_fail = sum(1 for c in results["checks"].values() if c.get("ok") is False)
n_skip = sum(1 for c in results["checks"].values() if c.get("ok") is None)
out("RESULT  pass=%d fail=%d skip=%d" % (n_pass, n_fail, n_skip))
try:
    resfile = os.path.join(LOGDIR, "results-%s-%s.json" % (MODE, BUILD))
    with open(resfile, "w", encoding="utf-8") as fh:
        json.dump(results, fh, ensure_ascii=False, indent=1, default=str)
    with open(os.path.join(LOGDIR, "check-%s-%s.log" % (MODE, BUILD)), "w", encoding="utf-8") as fh:
        fh.write("\n".join(LOG) + "\n")
    print("wrote", resfile)
except Exception:
    print("could not write results:\n" + traceback.format_exc())
