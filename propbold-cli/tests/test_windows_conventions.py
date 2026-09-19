"""What Windows GDI needs that fontTools round-trips and OTS do not check.

The first Windows install of a propbold TTF failed with "not a valid font file" although
ots-sanitize passed. Cause: the name table had no Full name (ID 4). These assertions pin every
convention assemble_ttf now guarantees. They are necessary, not sufficient: the definition of done
still includes a real install on Windows (see ../DOD.md).
"""
import subprocess
import sys
import pytest
from fontTools.ttLib import TTFont
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from propbold.io_binary import assemble_ttf, embolden_glyphs, weight_class


def _square(x0, y0, x1, y1):
    pen = TTGlyphPen(None)
    pen.moveTo((x0, y0)); pen.lineTo((x1, y0)); pen.lineTo((x1, y1)); pen.lineTo((x0, y1)); pen.closePath()
    return pen.glyph()


@pytest.fixture(scope="module")
def out_font(tmp_path_factory):
    """Small CID-style source with vhea/vmtx, run through the real pipeline."""
    order = [".notdef", "space"] + ["cid%05d" % i for i in range(2, 60)]
    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap({0x20: "space", **{0x4E00 + i: order[i] for i in range(2, 60)}})
    glyphs = {n: _square(60, 0, 140, 800) for n in order}
    glyphs[".notdef"] = _square(0, 0, 500, 700)
    glyphs["space"] = TTGlyphPen(None).glyph()
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics({n: (1000, 60) for n in order})
    fb.setupHorizontalHeader(ascent=880, descent=-120)
    fb.setupNameTable({"familyName": "Src", "styleName": "Regular", "copyright": "(c) test",
                       "licenseDescription": "OFL"})
    fb.setupOS2(sTypoAscender=880, sTypoDescender=-120, usWinAscent=1000, usWinDescent=200,
                ulCodePageRange1=0x00100000, sxHeight=500, sCapHeight=700)
    fb.setupPost(keepGlyphNames=False)
    fb.setupVerticalMetrics({n: (1000, 120) for n in order})
    fb.setupVerticalHeader(ascent=500, descent=-500)
    src_path = tmp_path_factory.mktemp("src") / "src.ttf"
    fb.save(str(src_path))
    src = TTFont(str(src_path))
    glyphs, metrics, _ = embolden_glyphs(src, 1.45, log=lambda *a: None)
    dst = tmp_path_factory.mktemp("dst") / "src-propbold145.ttf"
    assemble_ttf(src, glyphs, metrics, 1.45, str(dst))
    return str(dst), src


def test_name_ids_windows_and_mac(out_font):
    dst, _ = out_font
    n = TTFont(dst)["name"]
    for plat, enc, lang in ((3, 1, 0x409), (1, 0, 0)):
        for nid in (1, 2, 3, 4, 5, 6):
            assert n.getName(nid, plat, enc, lang) is not None, f"nameID {nid} missing for ({plat},{enc},{lang:#x})"
    ps = n.getName(6, 3, 1, 0x409).toUnicode()
    assert len(ps) <= 63 and ps.isascii() and " " not in ps
    assert n.getName(4, 3, 1, 0x409).toUnicode() == n.getName(1, 3, 1, 0x409).toUnicode()   # Regular: full == family
    assert n.getName(0, 3, 1, 0x409).toUnicode() == "(c) test"                              # legal strings carried
    assert "ltag" not in TTFont(dst)


def test_os2_head_post_consistency(out_font):
    dst, src = out_font
    f = TTFont(dst)
    os2, head, post = f["OS/2"], f["head"], f["post"]
    assert os2.version >= 3
    assert os2.fsSelection & 0x40 and not (os2.fsSelection & 0x21)      # REGULAR set, BOLD/ITALIC clear
    assert head.macStyle == 0
    assert 100 <= os2.usWeightClass <= 900 and os2.usWeightClass == 700
    assert os2.fsType == 0
    assert os2.ulCodePageRange1 == src["OS/2"].ulCodePageRange1          # ranges copied from source
    assert os2.sxHeight == 500 and os2.sCapHeight == 700
    assert head.flags & 0x000B == 0x000B
    assert post.formatType == 3.0
    assert f.getGlyphOrder()[0] == ".notdef"
    assert "gasp" in f and f["gasp"].gaspRange == {0xFFFF: 0x000F}
    assert {(t.platformID, t.platEncID, t.format) for t in f["cmap"].tables} >= {(3, 1, 4)}


def test_lsb_equals_xmin(out_font):
    dst, _ = out_font
    f = TTFont(dst)
    g, h = f["glyf"], f["hmtx"]
    for name in f.getGlyphOrder():
        gl = g[name]
        if gl.numberOfContours:
            gl.recalcBounds(g)
            assert h[name][1] == gl.xMin, name
        else:
            assert h[name][1] == 0, name


def test_vertical_and_layout_tables_copied(out_font):
    dst, src = out_font
    f = TTFont(dst)
    for tag in ("vhea", "vmtx"):
        assert tag in f
    assert f["vmtx"].metrics[".notdef"] == src["vmtx"].metrics[".notdef"]


def test_weight_class_mapping():
    assert weight_class(1.0) == 400
    assert weight_class(1.45) == 700
    assert weight_class(1.75) == 900
    assert weight_class(2.5) == 900


def test_ots_sanitize(out_font):
    pytest.importorskip("ots")
    dst, _ = out_font
    r = subprocess.run([sys.executable, "-m", "ots", dst], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
