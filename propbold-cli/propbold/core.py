"""Vector core: scan-line stem measurement + offset via skia-pathops (stroke ∪ fill = dilation)."""
from __future__ import annotations
import numpy as np
import pathops
from fontTools.pens.recordingPen import DecomposingRecordingPen
from .spec import PCT, N_LINES, MAX_RUN_FRAC, D_CAP, BOX_GROWTH


# ------------------------------------------------------------------ input
def path_from_glyphset(glyphset, name) -> pathops.Path:
    """Draw glyph `name` (components decomposed) into a simplified pathops Path."""
    rec = DecomposingRecordingPen(glyphset)
    glyphset[name].draw(rec)
    p = pathops.Path()
    rec.replay(p.getPen())
    p.simplify()          # nonzero -> even-odd normalised, overlaps removed
    return p


# ------------------------------------------------------------------ measurement
def _flatten(path, steps=8):
    contours, cur, start = [], [], None
    for verb, pts in path:
        if verb == pathops.PathVerb.MOVE:
            if len(cur) > 1:
                contours.append(np.array(cur))
            cur = [pts[0]]
            start = pts[0]
        elif verb == pathops.PathVerb.LINE:
            cur.append(pts[0])
        elif verb == pathops.PathVerb.QUAD:
            p0 = np.array(cur[-1]); p1, p2 = np.array(pts[0]), np.array(pts[1])
            for t in np.linspace(0, 1, steps + 1)[1:]:
                cur.append(tuple((1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t * t * p2))
        elif verb == pathops.PathVerb.CUBIC:
            p0 = np.array(cur[-1]); p1, p2, p3 = (np.array(p) for p in pts)
            for t in np.linspace(0, 1, steps + 1)[1:]:
                cur.append(tuple((1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t * t * p2 + t ** 3 * p3))
        elif verb == pathops.PathVerb.CLOSE:
            if start is not None:
                cur.append(start)
            if len(cur) > 1:
                contours.append(np.array(cur))
            cur = []
    if len(cur) > 1:
        contours.append(np.array(cur))
    return contours


def scanline_runs(contours, coord, axis):
    """Ink-run lengths on one scan line (axis=1: horizontal line y=coord; axis=0: vertical x=coord)."""
    xs = []
    for c in contours:
        a, b = c[:-1], c[1:]
        ya, yb = a[:, axis], b[:, axis]
        cross = ((ya <= coord) & (yb > coord)) | ((yb <= coord) & (ya > coord))
        if not cross.any():
            continue
        t = (coord - ya[cross]) / (yb[cross] - ya[cross])
        o = 1 - axis
        xs.extend(a[cross, o] + t * (b[cross, o] - a[cross, o]))
    xs = np.sort(np.array(xs))
    if len(xs) < 2:
        return []
    n = len(xs) - (len(xs) % 2)
    return list(xs[1:n:2] - xs[0:n:2])


def stem_width(path):
    """Per-glyph stem width in font units, or None. Same estimator as the Glyphs plugin."""
    b = path.bounds
    if b is None:
        return None
    x0, y0, x1, y1 = b
    W, H = x1 - x0, y1 - y0
    if W < 1 or H < 1:
        return None
    contours = _flatten(path)
    runs = []
    for i in range(N_LINES):
        f = 0.06 + 0.88 * i / (N_LINES - 1)
        runs += scanline_runs(contours, y0 + f * H, 1)
        runs += scanline_runs(contours, x0 + f * W, 0)
    limit = MAX_RUN_FRAC * max(W, H)
    runs = sorted(r for r in runs if 0 < r < limit)
    if len(runs) < 6:
        return None
    return float(runs[min(len(runs) - 1, int(len(runs) * PCT / 100.0))])


# ------------------------------------------------------------------ offset
def dilate(path, d):
    """Offset outward by d: fill ∪ stroke(width 2d, miter joins). Result is overlap-free."""
    if d <= 0:
        return pathops.Path(path)
    s = pathops.Path(path)
    s.stroke(2 * d, pathops.LineCap.BUTT_CAP, pathops.LineJoin.MITER_JOIN, 4.0)
    s.convertConicsToQuads()
    u = pathops.op(path, s, pathops.PathOp.UNION)
    u.simplify()
    return u


def proportional_bold(path, ratio):
    """Return (new_path, info) with d = (ratio-1)/2 * stem, capped at D_CAP * stem."""
    p = pathops.Path(path)
    p.simplify()
    w = stem_width(p)
    if w is None:
        return p, {"stem": None, "offset": 0.0}
    d = max(0.0, min((ratio - 1.0) / 2.0 * w, D_CAP * w))
    if BOX_GROWTH < 1.0:
        x0, y0, x1, y1 = p.bounds
        W, H = x1 - x0, y1 - y0
        dW = BOX_GROWTH * 2.0 * d
        sx = float(np.clip((W + dW - 2 * d) / W, 0.85, 1.1)) if W > 0 else 1.0
        sy = float(np.clip((H + dW - 2 * d) / H, 0.85, 1.1)) if H > 0 else 1.0
        cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
        p = p.transform(sx, 0, 0, sy, cx * (1 - sx), cy * (1 - sy))
    out = dilate(p, d)
    out.convertConicsToQuads()
    return out, {"stem": w, "offset": d}
