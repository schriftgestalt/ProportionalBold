# -*- coding: utf-8 -*-
"""
diag_stem.py — why did the plugin's stem measurement return None headless?

Run under glyphs-cli (no GUI):
  glyphs run --app "/Applications/Glyphs 3.app" --python <…/Python.framework/Versions/3.11/Python> \
             --plugins ./ProportionalBold.glyphsPlugin mac/diag_stem.py

For 一 十 日 國 it prints, from testdata/NotoSansCJKtc-Regular-sub415.glyphs:
  font/master metrics; layer bounds, path/component/node counts;
  the RAW result of layer.intersectionsBetweenPoints() for one horizontal and one vertical scan line
  on (A) the attached master layer, (B) layer.copy() detached, (C) layer.copyDecomposedLayer() detached
  [= what plugin.py measures on], (D) C after removeOverlap() [= exactly plugin.py's state],
  (E) C attached to the glyph as an extra layer;
  then plugin.stemWidth() on A, D and E, and — if the propbold package is importable in this Python —
  the CLI's own numbers for the same lines from the same .glyphs file via glyphsLib + skia-pathops.
Output is plain text; the workflow tees it to mac/log/40-diag-stem.txt.
"""
import os
import sys
import traceback

from GlyphsApp import Glyphs
import objc

CHARS = "一十日國"


def find_repo():
    env = os.environ.get("PROPBOLD_REPO")
    if env:
        return os.path.expanduser(env)
    try:
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    except NameError:
        return os.path.expanduser("~/ProportionalBold")


REPO = find_repo()
GLYPHS_FILE = os.path.join(REPO, "testdata", "NotoSansCJKtc-Regular-sub415.glyphs")


def p(*a):
    print(*a)
    sys.stdout.flush()


def pts_repr(pts):
    """Show what intersectionsBetweenPoints really returns: count, type, and coordinates via .x/.y,
    falling back to pointValue() if the objects are plain NSValues."""
    if pts is None:
        return "None"
    try:
        n = len(pts)
    except Exception as e:
        return "not a sequence: %r (%r)" % (pts, e)
    if n == 0:
        return "[] (0 points)"
    t = type(pts[0]).__name__
    coords = []
    for q in pts:
        try:
            coords.append((round(q.x, 1), round(q.y, 1)))
        except Exception:
            try:
                v = q.pointValue()
                coords.append(("pv", round(v.x, 1), round(v.y, 1)))
            except Exception as e:
                coords.append(("?", repr(e)[:40]))
    return "%d points, type %s: %s" % (n, t, coords)


def bounds_str(layer):
    try:
        b = layer.bounds
        return "x %.1f..%.1f  y %.1f..%.1f  (w %.1f h %.1f)" % (b.origin.x, b.origin.x + b.size.width, b.origin.y, b.origin.y + b.size.height, b.size.width, b.size.height)
    except Exception as e:
        return "bounds raised %r" % e


def counts(layer):
    try:
        nodes = sum(len(pa.nodes) for pa in layer.paths)
        return "paths %d components %d nodes %d parent %s" % (len(layer.paths), len(layer.components), nodes, "None" if layer.parent is None else type(layer.parent).__name__)
    except Exception as e:
        return "counts raised %r" % e


def lines_for(layer):
    b = layer.bounds
    x0, y0, W, H = b.origin.x, b.origin.y, b.size.width, b.size.height
    hy = y0 + 0.5 * H
    vx = x0 + 0.5 * W
    return ((x0 - 10.0, hy), (x0 + W + 10.0, hy)), ((vx, y0 - 10.0), (vx, y0 + H + 10.0))


def raw_intersections(layer, tag):
    try:
        (h1, h2), (v1, v2) = lines_for(layer)
    except Exception as e:
        p("   %s: cannot place lines: %r" % (tag, e))
        return None, None
    hp = vp = None
    for name, a, b in (("H", h1, h2), ("V", v1, v2)):
        try:
            pts = layer.intersectionsBetweenPoints(a, b, components=True)
            p("   %s %s-line %s -> %s: %s" % (tag, name, tuple(round(v, 1) for v in a), tuple(round(v, 1) for v in b), pts_repr(pts)))
            if name == "H":
                hp = pts
            else:
                vp = pts
        except Exception:
            p("   %s %s-line raised:\n%s" % (tag, name, traceback.format_exc()))
    return hp, vp


def plugin_instance():
    try:
        cls = objc.lookUpClass("ProportionalBold")
    except objc.nosuchclass_error:
        p("plugin class NOT loaded (run with --plugins ./ProportionalBold.glyphsPlugin)")
        return None
    try:
        cls.start = lambda self: None
    except Exception:
        pass
    try:
        return cls.alloc().init()
    except Exception:
        p("alloc().init() failed, using alloc():\n" + traceback.format_exc())
        return cls.alloc()


def glyph_by_unicode(font, u):
    hexcode = "%04X" % u
    g = font.glyphs["uni" + hexcode]
    if g is not None:
        return g
    for g in font.glyphs:
        if g.unicode and g.unicode.upper() == hexcode:
            return g
    return None


def cli_reference(charname_map):
    """The CLI's own measurement of the same .glyphs file (same outlines, same lines)."""
    try:
        import glyphsLib
        from propbold.core import path_from_glyphset, stem_width, scanline_runs, _flatten, proportional_bold
        from propbold.io_glyphs import _MasterGlyphSet
    except Exception as e:
        p("CLI reference skipped: propbold/glyphsLib not importable in this Python (%r)" % e)
        return
    gf = glyphsLib.GSFont(GLYPHS_FILE)
    gs = _MasterGlyphSet(gf, gf.masters[0].id)
    for ch in CHARS:
        gl = None
        for cand in gf.glyphs:
            if cand.unicode and int(cand.unicode, 16) == ord(ch):
                gl = cand
                break
        if gl is None:
            p("   CLI: %s not found" % ch)
            continue
        path = path_from_glyphset(gs, gl.name)
        x0, y0, x1, y1 = path.bounds
        cont = _flatten(path)
        hy, vx = y0 + 0.5 * (y1 - y0), x0 + 0.5 * (x1 - x0)
        bold, info = proportional_bold(path, 1.45)
        p("   CLI %s (%s): bounds %s stem %.1f d %.2f | H-line y=%.1f runs %s | V-line x=%.1f runs %s | bold bounds %s"
          % (ch, gl.name, [round(v, 1) for v in path.bounds], info["stem"] or 0, info["offset"], hy,
             [round(float(r), 1) for r in scanline_runs(cont, hy, 1)], vx, [round(float(r), 1) for r in scanline_runs(cont, vx, 0)],
             [round(v, 1) for v in bold.bounds]))


def main():
    p("=== diag_stem  Glyphs %s (%s)  Python %s" % (getattr(Glyphs, "versionString", "?"), getattr(Glyphs, "buildNumber", "?"), sys.version.split()[0]))
    p("=== file: %s" % GLYPHS_FILE)
    font = None
    for kwargs in ({"showInterface": False}, {}):
        try:
            font = Glyphs.open(GLYPHS_FILE, **kwargs)
        except Exception as e:
            p("Glyphs.open(%s) raised %r" % (kwargs, e))
        if font is not None:
            break
    if font is None:
        p("FAIL could not open the .glyphs file")
        return
    m = font.masters[0]
    try:
        p("=== font: upm %s  formatVersion %s  masters %d  glyphs %d" % (font.upm, getattr(font, "formatVersion", "?"), len(font.masters), len(font.glyphs)))
        p("=== master: ascender %s descender %s capHeight %s xHeight %s" % (m.ascender, m.descender, m.capHeight, m.xHeight))
    except Exception as e:
        p("metrics raised %r" % e)
    plugin = plugin_instance()

    summary = {}
    for ch in CHARS:
        g = glyph_by_unicode(font, ord(ch))
        p("\n### %s  glyph %s" % (ch, g.name if g else "NOT FOUND"))
        if g is None:
            continue
        layer = g.layers[m.id]
        p("   A attached master layer: %s | %s" % (bounds_str(layer), counts(layer)))
        hA, _ = raw_intersections(layer, "A")

        try:
            cp = layer.copy()
            p("   B layer.copy(): %s | %s" % (bounds_str(cp), counts(cp)))
            hB, _ = raw_intersections(cp, "B")
        except Exception:
            p("   B raised:\n" + traceback.format_exc())
            hB = None

        try:
            work = layer.copyDecomposedLayer()
            p("   C copyDecomposedLayer(): %s | %s" % (bounds_str(work), counts(work)))
            hC, _ = raw_intersections(work, "C")
            work.removeOverlap()
            p("   D C after removeOverlap(): %s | %s" % (bounds_str(work), counts(work)))
            hD, _ = raw_intersections(work, "D")
        except Exception:
            p("   C/D raised:\n" + traceback.format_exc())
            work, hC, hD = None, None, None

        hE = None
        if work is not None:
            try:
                n_before = len(g.layers)
                g.layers.append(work)                       # attach as an extra (non-master) layer
                p("   E C attached to glyph (layers %d -> %d): %s | %s" % (n_before, len(g.layers), bounds_str(work), counts(work)))
                hE, _ = raw_intersections(work, "E")
            except Exception:
                p("   E raised:\n" + traceback.format_exc())

        if plugin is not None:
            for tag, lyr in (("A", layer), ("D/E work", work)):
                if lyr is None:
                    continue
                try:
                    w = plugin.stemWidth(lyr)
                    p("   plugin.stemWidth(%s) = %s" % (tag, w))
                except Exception:
                    p("   plugin.stemWidth(%s) raised:\n%s" % (tag, traceback.format_exc()))
            if hA:
                try:
                    (h1, h2), _ = lines_for(layer)
                    p("   plugin._cleanRuns(A H-line) = %s" % plugin._cleanRuns(hA, 0, h1, h2))
                except Exception:
                    p("   _cleanRuns raised:\n" + traceback.format_exc())
        if work is not None:
            try:
                idx = [i for i, l in enumerate(g.layers) if l.layerId == work.layerId]
                if idx:
                    del g.layers[idx[0]]
            except Exception:
                pass
        summary[ch] = tuple(("-" if x is None else len(x)) for x in (hA, hB, hC, hD, hE))

    p("\n=== SUMMARY  H-line intersection counts per variant  (A attached, B copy, C decomposed-detached, D after removeOverlap, E attached copy)")
    for ch, s in summary.items():
        p("   %s  A=%s B=%s C=%s D=%s E=%s" % ((ch,) + s))
    p("\n=== CLI reference on the same file")
    cli_reference(None)
    try:
        font.close()
    except Exception:
        pass


try:
    main()
except Exception:
    p("FAIL uncaught\n" + traceback.format_exc())
