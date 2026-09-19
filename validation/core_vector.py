# -*- coding: utf-8 -*-
"""
core_vector.py — 「比例加粗＋輪廓守恆」的純向量實作（沙盒驗證用）。
與 Glyphs 外掛使用同一套演算法；外掛裡的三個原語對應如下：
  掃描線交點量測   : Glyphs  layer.intersectionsBetweenPoints()   ↔ 這裡  scanline_runs()
  外推 (offset)    : Glyphs  GSOffsetCurve.offsetLayer...          ↔ 這裡  pathops stroke ∪ fill
  縮放             : Glyphs  layer.applyTransform()                ↔ 這裡  Path.transform()
"""
import numpy as np
import pathops

# ---------------------------------------------------------------- 幾何工具
def flatten(path, steps=8):
    """把 pathops.Path 打成多段線（每個 contour 一個 (N,2) 陣列）。"""
    contours, cur, start = [], [], None
    for verb, pts in path:
        if verb == pathops.PathVerb.MOVE:
            if len(cur) > 1: contours.append(np.array(cur))
            cur = [pts[0]]; start = pts[0]
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
            if start is not None: cur.append(start)
            if len(cur) > 1: contours.append(np.array(cur))
            cur = []
    if len(cur) > 1: contours.append(np.array(cur))
    return contours

def scanline_runs(contours, coord, axis):
    """一條掃描線（axis=1: 水平線 y=coord；axis=0: 垂直線 x=coord）與輪廓的交點，
    回傳墨段長度 list（even-odd 配對，輪廓須已去重疊）。"""
    xs = []
    for c in contours:
        a = c[:-1]; b = c[1:]
        ya, yb = a[:, axis], b[:, axis]
        cross = ((ya <= coord) & (yb > coord)) | ((yb <= coord) & (ya > coord))
        if not cross.any(): continue
        t = (coord - ya[cross]) / (yb[cross] - ya[cross])
        o = 1 - axis
        xs.extend(a[cross, o] + t * (b[cross, o] - a[cross, o]))
    xs = np.sort(np.array(xs))
    if len(xs) < 2: return []
    n = len(xs) - (len(xs) % 2)
    return list(xs[1:n:2] - xs[0:n:2])

def stem_width(path, n_lines=24, pct=30, max_frac=0.35):
    """每字筆畫粗細估計：雙向掃描線墨段長度的第 pct 百分位（排除過長的墨段）。"""
    b = path.bounds
    if b is None: return None, None
    x0, y0, x1, y1 = b
    W, H = x1 - x0, y1 - y0
    if W < 1 or H < 1: return None, (x0, y0, x1, y1)
    contours = flatten(path)
    runs = []
    for f in np.linspace(0.06, 0.94, n_lines):
        runs += scanline_runs(contours, y0 + f * H, 1)
        runs += scanline_runs(contours, x0 + f * W, 0)
    runs = np.array([r for r in runs if 0 < r < max_frac * max(W, H)])
    if runs.size < 6: return None, (x0, y0, x1, y1)
    return float(np.percentile(runs, pct)), (x0, y0, x1, y1)

# ---------------------------------------------------------------- 加粗
def dilate(path, d):
    """外推 d：填色 ∪ 寬 2d 的描邊（miter 接合＝直角保持方正）。"""
    if d <= 0: return pathops.Path(path)
    s = pathops.Path(path)
    s.stroke(2 * d, pathops.LineCap.BUTT_CAP, pathops.LineJoin.MITER_JOIN, 4.0)
    s.convertConicsToQuads()
    u = pathops.op(path, s, pathops.PathOp.UNION)
    u.simplify()
    return u

def proportional_bold(path, ratio, upm=1000, box_growth=0.7, d_cap=0.6, silhouette=True, w_ref=None, gamma=2.0):
    """比例加粗：目標粗細增量 Δ_g = (ratio-1) * w_ref * (w_g / w_ref)**gamma，單邊外推 d = Δ_g/2。
    gamma=1 為純比例；實測 Noto Sans CJK 的設計師增量接近 w_g 的平方 (gamma≈2)。
    w_ref 為全字型的參考筆寬（各字 w_g 的中位數）；未給時以本字 w_g 代替（退化為純比例）。
    輪廓守恆：先把骨架縮到 (W+ΔW-2d)/W 再外推。回傳 (new_path, info)。"""
    p = pathops.Path(path); p.simplify()
    w, bb = stem_width(p)
    if w is None:
        return p, dict(w=None, d=0.0, sx=1.0, sy=1.0)
    wr = w_ref if w_ref else w
    delta = (ratio - 1.0) * wr * (w / wr) ** gamma
    d = max(delta / 2.0, 0.0)
    d = min(d, d_cap * w)
    x0, y0, x1, y1 = bb; W, H = x1 - x0, y1 - y0
    sx = sy = 1.0
    if silhouette:
        dW = box_growth * 2 * d      # 外框只長 2d 的 box_growth 倍
        sx = float(np.clip((W + dW - 2 * d) / W, 0.85, 1.1))
        sy = float(np.clip((H + dW - 2 * d) / H, 0.85, 1.1))
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        p = p.transform(sx, 0, 0, sy, cx * (1 - sx), cy * (1 - sy))
    out = dilate(p, d)
    return out, dict(w=w, d=d, sx=sx, sy=sy)

# ---------------------------------------------------------------- 評估
def iou(a, b):
    inter = pathops.op(a, b, pathops.PathOp.INTERSECTION); inter.simplify()
    union = pathops.op(a, b, pathops.PathOp.UNION); union.simplify()
    ua = abs(union.area)
    return abs(inter.area) / ua if ua else 1.0

def n_holes(path):
    """counter 數 = 逆向 contour 數（simplify 後外框/內框方向相反）。"""
    p = pathops.Path(path); p.simplify()
    cw = sum(1 for c in p.contours if c.clockwise)
    ccw = len(list(p.contours)) - cw
    return min(cw, ccw)

def glyph_path(glyphset, name):
    p = pathops.Path(); glyphset[name].draw(p.getPen()); p.simplify()
    return p
