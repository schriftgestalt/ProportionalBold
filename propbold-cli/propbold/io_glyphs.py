""".glyphs in -> .glyphs out with a new master appended (source = first master)."""
from __future__ import annotations
import copy
import uuid
from glyphsLib import GSFont, GSLayer
from .core import path_from_glyphset, proportional_bold, stem_width


class _MasterGlyphSet:
    """Maps glyph name -> object with .draw(pen) for one master, so components can be decomposed."""

    def __init__(self, font, master_id):
        self.font = font
        self.master_id = master_id

    def __getitem__(self, name):
        glyph = self.font.glyphs[name]
        if glyph is None:
            raise KeyError(name)
        layer = glyph.layers[self.master_id]
        if layer is None:
            raise KeyError(name)
        return layer

    def __contains__(self, name):
        return self.font.glyphs[name] is not None


def process_glyphs(src_path, dst_path, ratio, log=print):
    font = GSFont(src_path)
    src = font.masters[0]
    new = copy.deepcopy(src)
    new.id = str(uuid.uuid4()).upper()
    new.name = f"{src.name} PropBold {ratio:.2f}"
    try:  # weight axis value = stem-based -> scale with the ratio
        if new.axes and new.axes[0] and new.axes[0] > 0:
            new.axes[0] = round(new.axes[0] * ratio)
    except Exception:
        pass
    font.masters.append(new)
    gset = _MasterGlyphSet(font, src.id)
    # pass 1: stems, median = fallback for unmeasurable glyphs
    measured = []
    for glyph in font.glyphs:
        try:
            p = path_from_glyphset(gset, glyph.name)
            w = stem_width(p) if p.bounds is not None else None
            if w:
                measured.append(w)
        except Exception:
            pass
    measured.sort()
    fallback = measured[len(measured) // 2] if measured else None
    stems, n = [], 0
    counts = {"done": 0, "fallback": 0, "failed": 0, "fallback_glyphs": []}
    for i, glyph in enumerate(font.glyphs):
        srcLayer = glyph.layers[src.id]
        newLayer = GSLayer()
        newLayer.layerId = new.id
        newLayer.associatedMasterId = new.id
        newLayer.name = new.name
        if srcLayer is not None:
            newLayer.width = srcLayer.width
            try:
                p = path_from_glyphset(gset, glyph.name)
            except Exception as e:
                log(f"  ! {glyph.name}: {e!r} — empty layer written")
                p = None
            if p is not None and p.bounds is not None:
                out, info = proportional_bold(p, ratio, fallback_stem=fallback)
                if info["stem"] is None:
                    log(f"  ! {glyph.name}: no stem and no fallback — copied unchanged"); counts["failed"] += 1
                    p.draw(newLayer.getPen())
                else:
                    out.draw(newLayer.getPen())
                    newLayer.userData["proportionalBold"] = {k: v for k, v in (("ratio", ratio), ("stem", info["stem"]), ("offset", info["offset"]), ("fallback", info["fallback"] or None)) if v is not None}
                    if info["fallback"]:
                        counts["fallback"] += 1; counts["fallback_glyphs"].append(glyph.name)
                    else:
                        counts["done"] += 1; stems.append(info["stem"])
                n += 1
        glyph.layers.append(newLayer)
        if i and i % 2000 == 0:
            log(f"  {i} glyphs…")
    if counts["fallback"]:
        log(f"  fallback stem {fallback:.1f} used for {counts['fallback']} unmeasurable glyphs: {counts['fallback_glyphs'][:20]}")
    font.save(dst_path)
    stems.sort()
    med = stems[len(stems) // 2] if stems else 0
    return {"glyphs": n, "median_stem": med, "median_stem_out": med * ratio, "master": new.name,
            "done": counts["done"], "fallback": counts["fallback"], "failed": counts["failed"]}
