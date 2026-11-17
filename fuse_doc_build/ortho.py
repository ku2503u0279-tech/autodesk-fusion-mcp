"""Orthographic (first-angle) projections from the same geometry as the 3D views.

A z-buffer rasteriser gives correct occlusion, which a painter's algorithm
cannot once plates interpenetrate.  Returns a PIL image plus a Mapper so the
PDF can draw dimension lines in millimetre space on top.
"""
import math

import numpy as np
from PIL import Image, ImageDraw

from render3d import _normal, shade

SS = 2
EDGE = (52, 62, 76)


class Mapper:
    """World (mm) -> image px for one orthographic view."""

    def __init__(self, axis, u0, v_top, scale, w, h):
        self.axis, self.u0, self.v_top, self.scale = axis, u0, v_top, scale
        self.w, self.h = w, h

    def uv(self, p):
        if self.axis == "front":       # looking along +Z -> u = X, v = Y
            return p[0], p[1]
        if self.axis == "top":         # looking down -Y, back wall at the top
            return p[0], -p[2]
        return p[2], p[1]              # side: u = Z, v = Y

    def to_px(self, u, v):
        return ((u - self.u0) * self.scale, (self.v_top - v) * self.scale)


def _bounds(scene, axis):
    m = Mapper(axis, 0, 0, 1, 1, 1)
    us, vs = [], []
    for f in scene.faces:
        for p in f["pts"]:
            u, v = m.uv(p)
            us.append(u)
            vs.append(v)
    return min(us), max(us), min(vs), max(vs)


def render_ortho(scene, axis="front", px_per_mm=2.2, pad_mm=8.0, bg=(255, 255, 255), light=0.42):
    u0, u1, v0, v1 = _bounds(scene, axis)
    u0 -= pad_mm
    u1 += pad_mm
    v0 -= pad_mm
    v1 += pad_mm
    S = px_per_mm * SS
    W, H = int(round((u1 - u0) * S)), int(round((v1 - v0) * S))
    mapper = Mapper(axis, u0, v1, S, W, H)

    zbuf = np.full((H, W), np.inf, dtype=np.float32)
    cbuf = np.zeros((H, W, 3), dtype=np.uint8)
    cbuf[:, :] = bg

    KEY = np.array([-0.42, 0.70, 0.58])
    KEY /= np.linalg.norm(KEY)

    tris = []
    for f in scene.faces:
        pts = f["pts"]
        n = _normal(pts)
        if axis == "front":
            facing = -abs(n[2])
        elif axis == "top":
            facing = abs(n[1])
        else:
            facing = abs(n[0])
        lam = abs(float(n @ KEY))
        col = shade(f["color"], max(0.55, min(1.22, 1.0 - light + light * (0.45 * facing + 0.75 * lam))))
        depthv = [(-p[2] if axis == "front" else (-p[1] if axis == "top" else -p[0])) for p in pts]
        scr = [mapper.to_px(*mapper.uv(p)) for p in pts]
        for i in range(1, len(pts) - 1):
            tris.append(((scr[0], scr[i], scr[i + 1]), (depthv[0], depthv[i], depthv[i + 1]), col))

    for tri, dv, col in tris:
        xs = [q[0] for q in tri]
        ys = [q[1] for q in tri]
        x0, x1 = max(0, int(math.floor(min(xs)))), min(W, int(math.ceil(max(xs))) + 1)
        y0, y1 = max(0, int(math.floor(min(ys)))), min(H, int(math.ceil(max(ys))) + 1)
        if x1 <= x0 or y1 <= y0:
            continue
        (ax, ay), (bx, by), (cx, cy) = tri
        det = (bx - ax) * (cy - ay) - (cx - ax) * (by - ay)
        if abs(det) < 1e-9:
            continue
        yy, xx = np.mgrid[y0:y1, x0:x1]
        px, py = xx + 0.5, yy + 0.5
        w1 = ((px - ax) * (cy - ay) - (cx - ax) * (py - ay)) / det
        w0 = ((bx - ax) * (py - ay) - (px - ax) * (by - ay)) / det
        w2 = 1.0 - w0 - w1
        inside = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        if not inside.any():
            continue
        d = w2 * dv[0] + w1 * dv[1] + w0 * dv[2]
        zsub = zbuf[y0:y1, x0:x1]
        hit = inside & (d < zsub)
        if not hit.any():
            continue
        zsub[hit] = d[hit]
        cbuf[y0:y1, x0:x1][hit] = col

    img = Image.fromarray(cbuf, "RGB")

    # ---- silhouette + internal feature edges from a face-id buffer ----
    ids = np.full((H, W), -1, dtype=np.int32)
    z2 = np.full((H, W), np.inf, dtype=np.float32)
    for k, f in enumerate(scene.faces):
        depthv = [(-p[2] if axis == "front" else (-p[1] if axis == "top" else -p[0])) for p in f["pts"]]
        scr = [mapper.to_px(*mapper.uv(p)) for p in f["pts"]]
        im = Image.new("I", (W, H), 0)
        ImageDraw.Draw(im).polygon([(q[0], q[1]) for q in scr], fill=1 << 20)
        xs = [q[0] for q in scr]
        ys = [q[1] for q in scr]
        x0, x1 = max(0, int(math.floor(min(xs)))), min(W, int(math.ceil(max(xs))) + 1)
        y0, y1 = max(0, int(math.floor(min(ys)))), min(H, int(math.ceil(max(ys))) + 1)
        if x1 <= x0 or y1 <= y0:
            continue
        mask = np.array(im.crop((x0, y0, x1, y1)), dtype=bool)
        if not mask.any():
            continue
        dmean = float(np.mean(depthv))
        zsub = z2[y0:y1, x0:x1]
        hit = mask & (dmean < zsub + 0.35)
        zsub[hit] = dmean
        ids[y0:y1, x0:x1][hit] = k

    e = np.zeros((H, W), dtype=bool)
    e[:-1, :] |= ids[:-1, :] != ids[1:, :]
    e[1:, :] |= ids[1:, :] != ids[:-1, :]
    e[:, :-1] |= ids[:, :-1] != ids[:, 1:]
    e[:, 1:] |= ids[:, 1:] != ids[:, :-1]
    e &= ids >= 0

    arr = np.array(img)
    arr[e] = EDGE
    img = Image.fromarray(arr, "RGB")
    img = img.resize((W // SS, H // SS), Image.LANCZOS)

    # crop to the drawing so the page gets the largest possible view
    a = np.array(img)
    ink = (a < 246).any(axis=2)
    rows = np.where(ink.any(axis=1))[0]
    cols = np.where(ink.any(axis=0))[0]
    if len(rows) and len(cols):
        pad = 4
        top = max(0, rows[0] - pad)
        bot = min(a.shape[0], rows[-1] + pad + 1)
        left = max(0, cols[0] - pad)
        right = min(a.shape[1], cols[-1] + pad + 1)
        mapper.u0 += left / px_per_mm
        mapper.v_top -= top / px_per_mm
        img = img.crop((left, top, right, bot))

    mapper.scale = px_per_mm
    mapper.w, mapper.h = img.size
    return img, mapper
