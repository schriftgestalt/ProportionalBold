"""Parity between the CLI core and the Glyphs plugin: constants and the stem estimator."""
import os, re, sys, types
import numpy as np
import pytest
import pathops
from propbold import spec, core

HERE = os.path.dirname(__file__)
PLUGIN = os.path.join(HERE, "..", "..", "ProportionalBold.glyphsPlugin", "Contents", "Resources", "plugin.py")


def _plugin_source():
    if not os.path.exists(PLUGIN):
        pytest.skip("plugin.py not found next to the CLI package")
    return open(PLUGIN, encoding="utf-8").read()


def test_constants_identical():
    src = _plugin_source()
    for name in ("DEFAULT_RATIO", "PCT", "N_LINES", "MAX_RUN_FRAC", "D_CAP", "BOX_GROWTH"):
        m = re.search(r"^%s\s*=\s*([0-9.]+)" % name, src, re.M)
        assert m, name
        assert float(m.group(1)) == float(getattr(spec, name)), name


def _load_plugin_class():
    src = _plugin_source()
    class Stub(types.ModuleType):
        def __getattr__(self, n):
            return lambda *a, **k: None
    for m in ("objc", "GlyphsApp", "GlyphsApp.plugins", "AppKit"):
        sys.modules[m] = Stub(m)
    sys.modules["objc"].python_method = lambda f: f
    class GeneralPlugin: pass
    sys.modules["GlyphsApp.plugins"].GeneralPlugin = GeneralPlugin
    sys.modules["GlyphsApp"].FILTER_MENU = 0
    sys.modules["GlyphsApp"].Glyphs = None
    ns = {}
    exec(compile(src, "plugin.py", "exec"), ns)
    return ns["ProportionalBold"]()


class _P:
    def __init__(self, x, y): self.x, self.y = x, y


class _FakeLayer:
    """GSLayer stand-in: bounds + intersectionsBetweenPoints (endpoints included, like Glyphs)."""
    def __init__(self, path):
        self.contours = core._flatten(path)
        x0, y0, x1, y1 = path.bounds
        self.bounds = types.SimpleNamespace(origin=types.SimpleNamespace(x=x0, y=y0),
                                            size=types.SimpleNamespace(width=x1 - x0, height=y1 - y0))

    def intersectionsBetweenPoints(self, p1, p2, components=False):
        pts = [_P(*p1)]
        horizontal = abs(p1[1] - p2[1]) < 1e-9
        axis = 1 if horizontal else 0
        coord = p1[1] if horizontal else p1[0]
        vals = []
        for c in self.contours:
            a, b = c[:-1], c[1:]
            ya, yb = a[:, axis], b[:, axis]
            cr = ((ya <= coord) & (yb > coord)) | ((yb <= coord) & (ya > coord))
            t = (coord - ya[cr]) / (yb[cr] - ya[cr])
            o = 1 - axis
            vals += list(a[cr, o] + t * (b[cr, o] - a[cr, o]))
        for v in sorted(vals):
            pts.append(_P(v, coord) if horizontal else _P(coord, v))
        pts.append(_P(*p2))
        return pts


def _rect(x0, y0, x1, y1):
    p = pathops.Path(); pen = p.getPen()
    pen.moveTo((x0, y0)); pen.lineTo((x1, y0)); pen.lineTo((x1, y1)); pen.lineTo((x0, y1)); pen.closePath()
    return p


def _plus():
    p = pathops.op(_rect(0, 400, 800, 480), _rect(360, 0, 440, 900), pathops.PathOp.UNION); p.simplify(); return p


@pytest.mark.parametrize("path,expected", [(_rect(0, 0, 80, 700), 80.0), (_plus(), 80.0)])
def test_stem_estimator_matches_plugin(path, expected):
    plugin = _load_plugin_class()
    w_cli = core.stem_width(path)
    w_plugin = plugin.stemWidth(_FakeLayer(path))
    assert abs(w_cli - w_plugin) <= 1.0
    assert abs(w_cli - expected) <= 2.0


def test_offset_amount():
    out, info = core.proportional_bold(_rect(0, 0, 80, 700), 1.45)
    assert abs(info["offset"] - 18.0) < 0.01
    x0, y0, x1, y1 = out.bounds
    assert abs((x1 - x0) - 116.0) < 0.5          # 80 + 2 * 18


def test_fallback_policy():
    """A glyph with too few ink runs has no stem: unchanged without a fallback, offset by the fallback with one."""
    dot = _rect(100, 100, 140, 140)
    out, info = core.proportional_bold(dot, 1.45)
    assert info["stem"] is None and info["offset"] == 0.0 and out.bounds == dot.bounds
    out, info = core.proportional_bold(dot, 1.45, fallback_stem=60.0)
    assert info["fallback"] is True and abs(info["offset"] - 13.5) < 0.01
    x0, y0, x1, y1 = out.bounds
    assert abs((x1 - x0) - (40 + 27)) < 0.5


def test_miter_limit_keeps_right_angles_square():
    out, info = core.proportional_bold(_rect(0, 0, 80, 700), 1.45)
    x0, y0, x1, y1 = out.bounds
    assert abs((x1 - x0) - 116.0) < 0.5 and abs((y1 - y0) - 736.0) < 0.5   # corners still reach the full miter
