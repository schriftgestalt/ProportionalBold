"""OTF/TTF in -> TTF out (glyf). CFF input is converted to quadratic outlines with cu2qu.

Windows-installability rules baked in here (fontTools round-trip and OTS do NOT check these):
  * name table carries IDs 1, 2, 3, 4, 5, 6 for both (3,1,0x409) and (1,0,0). GDI refuses a font
    without a Full name (ID 4) with "not a valid font file" — the first Windows run hit exactly this.
  * OS/2 is copied from the source font (Unicode/code-page ranges, PANOSE, x/cap height, first/last
    char, typo/win metrics) and patched: fsSelection REGULAR bit set, macStyle consistent,
    usWeightClass from the ratio, fsType 0 (installable), xAvgCharWidth recalculated.
  * post is format 3.0 (no glyph names): format 2.0 indexes names with a uint16 (258 + i) and
    overflows on 65,535-glyph CID fonts. cmap carries the mapping; names are not needed.
  * head.flags 0x000B (baseline y=0, lsb = xMin, integer ppem), lsb == xMin for every glyph.
  * gasp table added (unhinted TTF: smoothing at all sizes).
  * vhea/vmtx and GSUB/GPOS/GDEF/BASE are copied verbatim from the source — glyph order and count
    are unchanged, so glyph IDs stay valid; DSIG/VORG/CFF are dropped.
"""
from __future__ import annotations
import os
import time
import copy
from fontTools.ttLib import TTFont, newTable
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.cu2quPen import Cu2QuPen
from .core import path_from_glyphset, proportional_bold

MAX_GLYPHS = 65535   # maxp.numGlyphs is uint16
COPY_TABLES = ("vhea", "vmtx", "GSUB", "GPOS", "GDEF", "BASE")


def _tt_glyph(path):
    pen = TTGlyphPen(None)
    path.draw(Cu2QuPen(pen, max_err=1.0, reverse_direction=False))
    return pen.glyph()


def _glyph_order(src, max_glyphs=None):
    """Glyph order to write. PROPBOLD_MAX_GLYPHS=N (or max_glyphs) truncates for diagnostics."""
    order = list(src.getGlyphOrder())
    n = max_glyphs or int(os.environ.get("PROPBOLD_MAX_GLYPHS", "0") or 0)
    if n and len(order) > n:
        order = order[:n]
    return order


def embolden_glyphs(src, ratio, log=print, max_glyphs=None):
    """Run the rule over every glyph of an open TTFont.
    Returns (glyphs: name -> TTGlyph, metrics: name -> (advance, lsb), stems: list)."""
    gs = src.getGlyphSet()
    order = _glyph_order(src, max_glyphs)
    hmtx = src["hmtx"]
    glyphs, metrics, stems = {}, {}, []
    t0 = time.time()
    for i, name in enumerate(order):
        adv, lsb = hmtx[name]
        out = None
        try:
            p = path_from_glyphset(gs, name)
            if p.bounds is None:
                glyphs[name] = TTGlyphPen(None).glyph()
            else:
                out, info = proportional_bold(p, ratio)
                glyphs[name] = _tt_glyph(out)
                if info["stem"]:
                    stems.append(info["stem"])
        except Exception as e:  # keep the source glyph on failure
            log(f"  ! {name}: {e!r} — copied unchanged")
            p = path_from_glyphset(gs, name)
            out = p if p.bounds else None
            glyphs[name] = _tt_glyph(p) if p.bounds else TTGlyphPen(None).glyph()
        # TrueType: lsb must equal the glyph's integer xMin, otherwise renderers shift the outline
        g = glyphs[name]
        if g.numberOfContours:
            g.recalcBounds(None)
            lsb = g.xMin
        else:
            lsb = 0
        metrics[name] = (adv, lsb)
        if i and i % 2000 == 0:
            el = time.time() - t0
            log(f"  {i}/{len(order)} glyphs, {el:.0f}s elapsed, ~{el / i * (len(order) - i):.0f}s left")
    return glyphs, metrics, stems


def weight_class(ratio):
    """Regular = 400; Noto's Bold (ratio ~1.5) = 700, Black (~1.8) = 900."""
    w = 400 + 625 * (ratio - 1.0)
    return int(min(900, max(100, round(w / 100.0) * 100)))


def _names(src, ratio):
    fam = f"{_family(src)} PropBold{int(round(ratio * 100)):03d}"
    ps = "".join(ch for ch in fam if ch.isalnum()) + "-Regular"
    names = {
        "familyName": fam,
        "styleName": "Regular",
        "uniqueFontIdentifier": f"{fam};propbold",
        "fullName": fam,                      # nameID 4 — mandatory for Windows GDI
        "version": "Version 0.100",
        "psName": ps[:63],
        "typographicFamily": fam,
        "typographicSubfamily": "Regular",
    }
    # carry the source's legal strings (copyright, trademark, license) so the derivative stays honest
    try:
        n = src["name"]
        for key, nid in (("copyright", 0), ("trademark", 7), ("licenseDescription", 13), ("licenseInfoURL", 14)):
            rec = n.getName(nid, 3, 1, 0x409)
            if rec:
                names[key] = rec.toUnicode()
    except Exception:
        pass
    return names


def assemble_ttf(src, glyphs, metrics, ratio, dst_path, max_glyphs=None):
    """Build and save a TrueType font from processed glyphs, copying order/cmap/metrics from `src`."""
    order = _glyph_order(src, max_glyphs)
    if len(order) > MAX_GLYPHS:
        raise ValueError(f"{len(order)} glyphs exceed the TrueType limit of {MAX_GLYPHS}")
    keep = set(order)
    glyphs = {g: glyphs[g] for g in order}
    metrics = {g: metrics[g] for g in order}
    cmap = {u: g for u, g in (src.getBestCmap() or {}).items() if g in keep}

    upm = src["head"].unitsPerEm
    fb = FontBuilder(upm, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(cmap)
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics(metrics)
    hhea = src["hhea"]
    fb.setupHorizontalHeader(ascent=hhea.ascent, descent=hhea.descent, lineGap=hhea.lineGap,
                             caretSlopeRise=hhea.caretSlopeRise, caretSlopeRun=hhea.caretSlopeRun,
                             caretOffset=hhea.caretOffset)
    fb.setupNameTable(_names(src, ratio))
    fb.setupOS2()                                 # placeholder; replaced below
    fb.setupPost(keepGlyphNames=False)            # format 3.0
    font = fb.font

    # --- OS/2: start from the source (ranges, PANOSE, heights, metrics), then patch
    if "OS/2" in src:
        os2 = copy.deepcopy(src["OS/2"])
    else:
        os2 = font["OS/2"]
    os2.version = max(os2.version, 3)
    os2.usWeightClass = weight_class(ratio)
    os2.fsSelection = (os2.fsSelection & ~0x0021) | 0x0040      # clear ITALIC/BOLD, set REGULAR
    os2.fsType = 0
    os2.achVendID = "NONE"
    font["OS/2"] = os2
    font["OS/2"].recalcAvgCharWidth(font)
    # --- head / post
    head = font["head"]
    head.flags = 0x000B
    head.macStyle = 0
    head.fontRevision = 0.1
    post = font["post"]
    if "post" in src:
        sp = src["post"]
        post.italicAngle = sp.italicAngle
        post.underlinePosition = sp.underlinePosition
        post.underlineThickness = sp.underlineThickness
        post.isFixedPitch = sp.isFixedPitch

    # --- gasp: unhinted TrueType, smooth at every size
    gasp = newTable("gasp")
    gasp.version = 1
    gasp.gaspRange = {0xFFFF: 0x000F}
    font["gasp"] = gasp

    # --- vertical metrics and OpenType layout: glyph ids are unchanged, copy verbatim
    # (PROPBOLD_NO_LAYOUT=1 skips this — diagnostic switch for Windows install bisecting)
    if len(order) == len(src.getGlyphOrder()) and not os.environ.get("PROPBOLD_NO_LAYOUT"):
        for tag in COPY_TABLES:
            if tag in src:
                font[tag] = src[tag]
    fb.save(dst_path)


def process_binary(src_path, dst_path, ratio, log=print):
    src = TTFont(src_path)
    glyphs, metrics, stems = embolden_glyphs(src, ratio, log=log)
    assemble_ttf(src, glyphs, metrics, ratio, dst_path)
    stems.sort()
    med = stems[len(stems) // 2] if stems else 0
    return {"glyphs": len(glyphs), "median_stem": med, "median_stem_out": med * ratio}


def _family(font):
    try:
        n = font["name"].getBestFamilyName()
        if n:
            return n
    except Exception:
        pass
    return "Font"
