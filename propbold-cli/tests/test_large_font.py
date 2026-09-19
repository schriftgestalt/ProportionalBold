"""Guard against 16-bit limits with a 65,535-glyph CID-style font (the Noto Sans CJK case).

test_assemble_65535 runs every time (a few seconds): it exercises the exact table-building and
save path that crashed on Windows (post 2.0 uint16 overflow).
test_full_pipeline_65535 also runs the measurement/offset over all glyphs; it is slow, so it only
runs when PROPBOLD_SLOW=1 is set.
"""
import os
import pytest
from fontTools.ttLib import TTFont
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from propbold.io_binary import assemble_ttf, embolden_glyphs, process_binary, MAX_GLYPHS

N = MAX_GLYPHS   # 65535


def _square(x0, y0, x1, y1):
    pen = TTGlyphPen(None)
    pen.moveTo((x0, y0)); pen.lineTo((x1, y0)); pen.lineTo((x1, y1)); pen.lineTo((x0, y1)); pen.closePath()
    return pen.glyph()


@pytest.fixture(scope="module")
def big_font(tmp_path_factory):
    """A TTF with 65,535 glyphs: .notdef + cid00001…cid65534, like a CID-keyed CJK font."""
    order = [".notdef"] + ["cid%05d" % i for i in range(1, N)]
    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder(order)
    # map the CJK block (and a bit beyond) onto the first glyphs; the rest stay unmapped like real CID fonts
    fb.setupCharacterMap({0x4E00 + i: order[1 + i] for i in range(min(N - 1, 0x9FFF - 0x4E00 + 1))})
    stem = _square(60, 0, 140, 800)
    glyphs = {name: stem for name in order}
    glyphs[".notdef"] = _square(0, 0, 500, 700)
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics({name: (1000, 60) for name in order})
    fb.setupHorizontalHeader(ascent=880, descent=-120)
    fb.setupNameTable({"familyName": "Big", "styleName": "Regular"})
    fb.setupOS2()
    fb.setupPost(keepGlyphNames=False)
    path = tmp_path_factory.mktemp("big") / "big.ttf"
    fb.save(str(path))
    return str(path)


def test_assemble_65535(big_font, tmp_path):
    src = TTFont(big_font)
    assert len(src.getGlyphOrder()) == N
    # skip the (slow) measurement: reuse the source outlines as if they had been processed
    glyf = src["glyf"]
    glyphs = {name: glyf[name] for name in src.getGlyphOrder()}
    metrics = {name: src["hmtx"][name] for name in src.getGlyphOrder()}
    dst = tmp_path / "big-propbold145.ttf"
    assemble_ttf(src, glyphs, metrics, 1.45, str(dst))      # crashed on Windows with post 2.0
    out = TTFont(str(dst))
    assert out["maxp"].numGlyphs == N
    assert out["post"].formatType == 3.0
    assert len(out.getGlyphOrder()) == N
    # post 3.0 stores no names: fontTools synthesises uniXXXX/glyphNNNNN on reload, so check by glyph index
    assert out.getGlyphID(out.getBestCmap()[0x9F9C]) == 1 + 0x9F9C - 0x4E00


def test_glyph_limit_error(big_font, tmp_path):
    src = TTFont(big_font)
    src.setGlyphOrder(src.getGlyphOrder() + ["one.too.many"])
    with pytest.raises(ValueError):
        assemble_ttf(src, {}, {}, 1.45, str(tmp_path / "x.ttf"))


@pytest.mark.skipif(os.environ.get("PROPBOLD_SLOW") != "1", reason="set PROPBOLD_SLOW=1 to run the full 65,535-glyph pipeline")
def test_full_pipeline_65535(big_font, tmp_path):
    dst = tmp_path / "big-propbold145.ttf"
    info = process_binary(big_font, str(dst), 1.45, log=lambda *a: None)
    assert info["glyphs"] == N
    out = TTFont(str(dst))
    assert out["post"].formatType == 3.0
    name = out.getGlyphOrder()[10]                             # names are synthesised (post 3.0); go by index
    g = out["glyf"][name]
    g.recalcBounds(out["glyf"])
    assert abs((g.xMax - g.xMin) - (80 + 2 * 18)) <= 1        # 80-unit stem -> 116 at ratio 1.45
    assert out["hmtx"][name][1] == g.xMin                      # lsb == xMin
