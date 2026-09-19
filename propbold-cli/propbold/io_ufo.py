"""UFO in -> new UFO out (components decomposed, outlines offset)."""
from __future__ import annotations
import ufoLib2
from .core import path_from_glyphset, proportional_bold


def process_ufo(src_path, dst_path, ratio, log=print):
    font = ufoLib2.Font.open(src_path)
    stems = []
    for i, glyph in enumerate(font):
        try:
            p = path_from_glyphset(font, glyph.name)
        except Exception as e:
            log(f"  ! {glyph.name}: {e!r} — left unchanged")
            continue
        if p.bounds is None:
            continue
        out, info = proportional_bold(p, ratio)
        glyph.clearContours()
        glyph.clearComponents()
        out.draw(glyph.getPen())
        glyph.lib["com.propbold.info"] = {k: v for k, v in (("ratio", ratio), ("stem", info["stem"]), ("offset", info["offset"])) if v is not None}
        if info["stem"]:
            stems.append(info["stem"])
        if i and i % 2000 == 0:
            log(f"  {i} glyphs…")
    font.info.styleName = f"{font.info.styleName or 'Regular'} PropBold {ratio:.2f}"
    font.save(dst_path, overwrite=False)
    stems.sort()
    med = stems[len(stems) // 2] if stems else 0
    return {"glyphs": len(font), "median_stem": med, "median_stem_out": med * ratio}
