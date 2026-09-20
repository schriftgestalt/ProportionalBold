"""UFO in -> new UFO out (components decomposed, outlines offset)."""
from __future__ import annotations
import ufoLib2
from .core import path_from_glyphset, proportional_bold, stem_width


def process_ufo(src_path, dst_path, ratio, log=print):
    font = ufoLib2.Font.open(src_path)
    # pass 1: stems, median = fallback for unmeasurable glyphs
    measured = []
    for glyph in font:
        try:
            p = path_from_glyphset(font, glyph.name)
            w = stem_width(p) if p.bounds is not None else None
            if w:
                measured.append(w)
        except Exception:
            pass
    measured.sort()
    fallback = measured[len(measured) // 2] if measured else None
    stems, counts = [], {"done": 0, "fallback": 0, "failed": 0, "fallback_glyphs": []}
    for i, glyph in enumerate(font):
        try:
            p = path_from_glyphset(font, glyph.name)
        except Exception as e:
            log(f"  ! {glyph.name}: {e!r} — left unchanged"); counts["failed"] += 1
            continue
        if p.bounds is None:
            continue
        out, info = proportional_bold(p, ratio, fallback_stem=fallback)
        if info["stem"] is None:
            log(f"  ! {glyph.name}: no stem and no fallback — left unchanged"); counts["failed"] += 1
            continue
        glyph.clearContours()
        glyph.clearComponents()
        out.draw(glyph.getPen())
        glyph.lib["com.propbold.info"] = {k: v for k, v in (("ratio", ratio), ("stem", info["stem"]), ("offset", info["offset"]), ("fallback", info["fallback"] or None)) if v is not None}
        if info["fallback"]:
            counts["fallback"] += 1; counts["fallback_glyphs"].append(glyph.name)
        else:
            counts["done"] += 1; stems.append(info["stem"])
        if i and i % 2000 == 0:
            log(f"  {i} glyphs…")
    if counts["fallback"]:
        log(f"  fallback stem {fallback:.1f} used for {counts['fallback']} unmeasurable glyphs: {counts['fallback_glyphs'][:20]}")
    font.info.styleName = f"{font.info.styleName or 'Regular'} PropBold {ratio:.2f}"
    font.save(dst_path, overwrite=False)
    stems.sort()
    med = stems[len(stems) // 2] if stems else 0
    return {"glyphs": len(font), "median_stem": med, "median_stem_out": med * ratio,
            "done": counts["done"], "fallback": counts["fallback"], "failed": counts["failed"]}
