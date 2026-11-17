"""Painter's-algorithm 3D renderer for light-studio technical illustration.

World axes (mm):
    X = left -> right   (0 .. 630 desk width)
    Y = height (up)     (-18 = underside of wood slab, 0 = wood top, 3 = mat top)
    Z = depth           (0 = back wall, 280 = front edge)
"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def hx(s):
    s = s.lstrip("#")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def shade(c, f):
    return tuple(max(0, min(255, int(round(v * f)))) for v in c)


class Camera:
    def __init__(self, az=32.0, el=25.0, scale=1.6, w=1600, h=1000,
                 target=(315.0, 30.0, 140.0), pan=(0.0, 0.0)):
        self.az, self.el = math.radians(az), math.radians(el)
        self.s, self.w, self.h = scale, w, h
        self.target = np.array(target, float)
        ca, sa = math.cos(self.az), math.sin(self.az)
        ce, se = math.cos(self.el), math.sin(self.el)
        self.U = np.array([ca, 0.0, -sa])
        self.V = np.array([-sa * se, ce, -ca * se])
        self.W = np.array([sa * ce, se, ca * ce])
        self.cx = w / 2.0 + pan[0]
        self.cy = h / 2.0 + pan[1]

    def project(self, p):
        d = np.asarray(p, float) - self.target
        return (self.cx + self.s * float(d @ self.U),
                self.cy - self.s * float(d @ self.V),
                float(d @ self.W))


def _normal(pts):
    a, b, c = np.array(pts[0], float), np.array(pts[1], float), np.array(pts[2], float)
    n = np.cross(b - a, c - a)
    L = np.linalg.norm(n)
    return n / L if L > 1e-9 else np.array([0.0, 1.0, 0.0])


def _convex_hull(pts):
    pts = sorted(set((round(p[0], 3), round(p[1], 3)) for p in pts))
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


class Scene:
    """Collects solids as polygons, then renders them flat-shaded."""

    KEY = np.array([-0.52, 0.74, 0.42])
    FILL = np.array([0.62, 0.36, 0.70])
    RIM = np.array([0.10, 0.42, -0.90])
    for _a in (KEY, FILL, RIM):
        _a /= np.linalg.norm(_a)

    def __init__(self):
        self.faces = []
        self.backdrop = []
        self.solids = []

    # ---------------- primitives ----------------
    def face(self, pts, color, smooth=False, outline=True, spec=0.22, back=False):
        if len(pts) < 3:
            return
        rec = dict(pts=[tuple(map(float, p)) for p in pts], color=color,
                   smooth=smooth, outline=outline, spec=spec)
        (self.backdrop if back else self.faces).append(rec)

    def prism(self, poly, axis, a0, a1, color, outline=True, spec=0.22, cap=True):
        """Extrude a 2D profile along `axis`.

        axis='y' -> poly is (x, z) ; axis='z' -> (x, y) ; axis='x' -> (y, z)
        """
        n = len(poly)
        if n < 3:
            return
        if axis == "y":
            lo = [(u, a0, v) for u, v in poly]
            hi = [(u, a1, v) for u, v in poly]
        elif axis == "z":
            lo = [(u, v, a0) for u, v in poly]
            hi = [(u, v, a1) for u, v in poly]
        else:                                   # axis 'x': poly is (y, z)
            lo = [(a0, u, v) for u, v in poly]
            hi = [(a1, u, v) for u, v in poly]
        for i in range(n):
            j = (i + 1) % n
            self.face([lo[i], lo[j], hi[j], hi[i]], color, outline=outline, spec=spec)
        if cap:
            self.face(list(reversed(lo)), shade(color, 0.86), outline=outline, spec=spec * 0.45)
            self.face(hi, shade(color, 1.04), outline=outline, spec=spec * 0.45)
        self._bbox(lo + hi)

    def box(self, x0, x1, y0, y1, z0, z1, color, r=0.0, ncorner=5, outline=True, spec=0.22):
        poly = _rrect(x0, x1, z0, z1, r, ncorner) if r > 0 else \
            [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]
        self.prism(poly, "y", y0, y1, color, outline=outline, spec=spec)

    def panel(self, x0, x1, y0, y1, z0, z1, color, r=0.0, ncorner=5, outline=True, spec=0.22):
        """Vertical plate, thin along Z (profile in X/Y)."""
        poly = _rrect(x0, x1, y0, y1, r, ncorner) if r > 0 else \
            [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        self.prism(poly, "z", z0, z1, color, outline=outline, spec=spec)

    def tube_x(self, x0, x1, cy, cz, r, color, seg=24):
        _tube(self, "x", x0, x1, cy, cz, r, color, seg)

    def tube_y(self, y0, y1, cx, cz, r, color, seg=24):
        _tube(self, "y", y0, y1, cx, cz, r, color, seg)

    def tube_z(self, z0, z1, cx, cy, r, color, seg=24):
        _tube(self, "z", z0, z1, cx, cy, r, color, seg)

    def disc_y(self, cx, cz, r, y0, y1, color, seg=32):
        _tube(self, "y", y0, y1, cx, cz, r, color, seg)

    def _bbox(self, pts):
        a = np.array(pts, float)
        self.solids.append((a.min(0), a.max(0)))

    # ---------------- framing ----------------
    def fit(self, az, el, w, h, margin=0.90, target=(315.0, 20.0, 145.0)):
        """Camera that frames every face, keeping the given view angles."""
        cam = Camera(az, el, 1.0, w, h, target)
        pts = [p for f in self.faces + self.backdrop for p in f["pts"]]
        xs = [cam.project(p) for p in pts]
        x0 = min(p[0] for p in xs); x1 = max(p[0] for p in xs)
        y0 = min(p[1] for p in xs); y1 = max(p[1] for p in xs)
        s = min(w * margin / max(1e-6, x1 - x0), h * margin / max(1e-6, y1 - y0))
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        return Camera(az, el, s, w, h, target, (w / 2 - cx, h / 2 - cy))

    # ---------------- rendering ----------------
    def render(self, cam, bg_top="#eef1f5", bg_bot="#cfd6df", vignette=0.30,
               shadow=0.42, shadow_y=3.0, aa=2, silhouette=True, edge_color="#2c3542",
               vig_color="#aab3c0", shadow_color="#96a0ad"):
        W, H = cam.w * aa, cam.h * aa
        img = Image.new("RGB", (W, H), bg_bot)
        d = ImageDraw.Draw(img)
        top, bot = hx(bg_top), hx(bg_bot)
        for i in range(H):
            d.line([(0, i), (W, i)], fill=mix(top, bot, (i / max(1, H - 1)) ** 1.15))

        cam2 = Camera(cam.az * 180 / math.pi, cam.el * 180 / math.pi, cam.s * aa, W, H,
                      tuple(cam.target), ((cam.cx - cam.w / 2) * aa, (cam.cy - cam.h / 2) * aa))

        # ---- contact shadow ----
        if shadow > 0 and self.solids:
            sm = Image.new("L", (W, H), 0)
            sd = ImageDraw.Draw(sm)
            L = self.KEY
            for lo, hi in self.solids:
                if lo[1] > shadow_y + 4:
                    continue
                pts = []
                for x in (lo[0], hi[0]):
                    for z in (lo[2], hi[2]):
                        t = (shadow_y - lo[1]) / max(0.30, L[1])
                        pts.append((x + L[0] * t, shadow_y, z + L[2] * t))
                        pts.append((x, shadow_y, z))
                hull = _convex_hull([cam2.project(p)[:2] for p in pts])
                if len(hull) >= 3:
                    sd.polygon(hull, fill=140)
            sm = sm.filter(ImageFilter.GaussianBlur(5.0 * aa))
            dark = Image.new("RGB", (W, H), hx(shadow_color))
            img = Image.composite(dark, img, sm.point(lambda v: int(v * shadow)))
            d = ImageDraw.Draw(img)

        for f in self.backdrop:
            pr = [cam2.project(p) for p in f["pts"]]
            n = _normal(f["pts"])
            lam = max(0.0, float(abs(n @ self.KEY)))
            d.polygon([(q[0], q[1]) for q in pr], fill=shade(f["color"], 0.72 + 0.28 * lam))

        items = []
        for f in self.faces:
            pr = [cam2.project(p) for p in f["pts"]]
            items.append((sum(q[2] for q in pr) / len(pr), f, pr))
        items.sort(key=lambda t: t[0])

        L1, L2, L3 = self.KEY, self.FILL, self.RIM
        for depth, f, pr in items:
            n = _normal(f["pts"])
            lam1 = max(0.0, float(n @ L1))
            lam2 = max(0.0, float(n @ L2))
            lam3 = max(0.0, float(n @ L3))
            col = shade(f["color"], min(1.30, 0.56 + 0.34 * lam1 + 0.13 * lam2 + 0.11 * lam3))
            hv = (L1 + cam2.W)
            hv = hv / (np.linalg.norm(hv) + 1e-9)
            spec = f["spec"] * (max(0.0, float(n @ hv)) ** 30)
            if spec > 0.005:
                col = tuple(min(255, int(c + (255 - c) * min(0.85, spec))) for c in col)
            poly = [(q[0], q[1]) for q in pr]
            d.polygon(poly, fill=col)
            if f["outline"] and not f["smooth"]:
                d.line(poly + [poly[0]], fill=shade(col, 0.80), width=max(1, aa // 2))

        if silhouette:
            sil = Image.new("L", (W, H), 0)
            sd2 = ImageDraw.Draw(sil)
            for depth, f, pr in items:
                sd2.polygon([(q[0], q[1]) for q in pr], fill=255)
            edge = sil.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.MinFilter(3))
            edge = edge.point(lambda v: 255 if v > 60 else 0).filter(ImageFilter.GaussianBlur(0.6 * aa))
            img = Image.composite(Image.new("RGB", (W, H), hx(edge_color)), img,
                                  edge.point(lambda v: int(v * 0.55)))

        if vignette > 0:
            vmask = Image.new("L", (W, H), 0)
            vd = ImageDraw.Draw(vmask)
            vd.ellipse([-W * 0.22, -H * 0.26, W * 1.22, H * 1.26], fill=255)
            vmask = vmask.filter(ImageFilter.GaussianBlur(W // 8))
            img = Image.composite(img, Image.new("RGB", (W, H), hx(vig_color)), vmask)

        if aa > 1:
            img = img.resize((cam.w, cam.h), Image.LANCZOS)
        return img


def _rrect(x0, x1, z0, z1, r, ncorner):
    r = min(r, (x1 - x0) / 2 - 0.01, (z1 - z0) / 2 - 0.01)
    if r <= 0.05:
        return [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]
    pts = []
    corners = [((x1 - r, z0 + r), -90), ((x1 - r, z1 - r), 0),
               ((x0 + r, z1 - r), 90), ((x0 + r, z0 + r), 180)]
    for (cx, cz), a0 in corners:
        for i in range(ncorner + 1):
            a = math.radians(a0 + 90 * i / ncorner)
            pts.append((cx + r * math.cos(a), cz + r * math.sin(a)))
    return pts


def _tube(scene, axis, a0, a1, c1, c2, r, color, seg):
    ring_a, ring_b = [], []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        u, v = c1 + r * math.cos(a), c2 + r * math.sin(a)
        if axis == "x":
            ring_a.append((a0, u, v)); ring_b.append((a1, u, v))
        elif axis == "y":
            ring_a.append((u, a0, v)); ring_b.append((u, a1, v))
        else:
            ring_a.append((u, v, a0)); ring_b.append((u, v, a1))
    for i in range(seg):
        j = (i + 1) % seg
        scene.face([ring_a[i], ring_a[j], ring_b[j], ring_b[i]], color,
                   smooth=True, outline=False, spec=0.62)
    scene.face(list(reversed(ring_a)), shade(color, 0.90), outline=False, spec=0.2)
    scene.face(ring_b, shade(color, 1.05), outline=False, spec=0.2)
    scene._bbox(ring_a + ring_b)
