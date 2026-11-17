"""Desk-system geometry for the portfolio renders.

Every part is placed from the bounding boxes that `verify_fusion_scripts.py`
reports for the real Fusion models, so the illustrations cannot drift away
from the CAD that ships.  Sculpted detail (rounded profiles, slots, wells)
is drawn on top of those envelopes.
"""
import json
import math
import os

from render3d import Scene, mix, hx, shade

HERE = os.path.dirname(os.path.abspath(__file__))
PARTS = {p["name"]: p for p in json.load(open(os.path.join(HERE, "parts.json")))}

WALNUT = hx("#8A5626")
WALNUT_L = hx("#A9723C")
BIRCH = hx("#BB8850")
PRINT = hx("#39434F")
PRINT_L = hx("#4A5764")
RED = hx("#C2212F")
METAL = hx("#AFBAC7")
GLASS = hx("#7FB6D9")
MAT = hx("#161B22")
KEY_CAP = hx("#41506B")
BOTTLE = hx("#8FA8BE")
PHONE = hx("#20272F")


def bb(name):
    p = PARTS[name]
    return p["x"], p["y"], p["z"]


def rpoly(pts, r, segs=4):
    """Round every corner of a closed 2D polygon with tangent arcs (G1)."""
    n = len(pts)
    out = []
    for i in range(n):
        p0, p1, p2 = pts[i - 1], pts[i], pts[(i + 1) % n]
        v1 = (p0[0] - p1[0], p0[1] - p1[1])
        v2 = (p2[0] - p1[0], p2[1] - p1[1])
        l1 = math.hypot(*v1) or 1e-9
        l2 = math.hypot(*v2) or 1e-9
        u1 = (v1[0] / l1, v1[1] / l1)
        u2 = (v2[0] / l2, v2[1] / l2)
        rr = min(r, l1 * 0.49, l2 * 0.49)
        a = (p1[0] + u1[0] * rr, p1[1] + u1[1] * rr)
        b = (p1[0] + u2[0] * rr, p1[1] + u2[1] * rr)
        cx, cy = p1[0] + (u1[0] + u2[0]) * rr, p1[1] + (u1[1] + u2[1]) * rr
        a0 = math.atan2(a[1] - cy, a[0] - cx)
        a1 = math.atan2(b[1] - cy, b[0] - cx)
        da = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
        for k in range(segs + 1):
            t = a0 + da * k / segs
            out.append((cx + rr * math.cos(t), cy + rr * math.sin(t)))
    return out


def stadium_2d(u0, v0, w, h, segs=8):
    """Stadium / pill outline filling a w x h box."""
    r = min(w, h) / 2.0
    if w >= h:
        a, b = (u0 + r, v0 + h / 2), (u0 + w - r, v0 + h / 2)
        pts = []
        for k in range(segs + 1):
            t = -math.pi / 2 + math.pi * k / segs
            pts.append((b[0] + r * math.cos(t), b[1] + r * math.sin(t)))
        for k in range(segs + 1):
            t = math.pi / 2 + math.pi * k / segs
            pts.append((a[0] + r * math.cos(t), a[1] + r * math.sin(t)))
        return pts
    a, b = (u0 + w / 2, v0 + r), (u0 + w / 2, v0 + h - r)
    pts = []
    for k in range(segs + 1):
        t = math.pi + math.pi * k / segs
        pts.append((a[0] + r * math.cos(t), a[1] + r * math.sin(t)))
    for k in range(segs + 1):
        t = math.pi * k / segs
        pts.append((b[0] + r * math.cos(t), b[1] + r * math.sin(t)))
    return pts


# ---------------------------------------------------------------- desk
def desk(s, mat=True, slab=True, wall=False):
    if slab:
        s.prism(rpoly([(0, 0), (630, 0), (630, 280), (0, 280)], 5), "y", -18.0, 0.0, WALNUT, spec=0.12)
        s.face([(0, 0, 280), (630, 0, 280), (630, -1.2, 279.6), (0, -1.2, 279.6)], WALNUT_L, spec=0.3)
        s.face([(0, -18, 280), (630, -18, 280), (630, -16.8, 279.6), (0, -16.8, 279.6)],
               mix(WALNUT, (0, 0, 0), 0.3), spec=0.1)
    if mat:
        s.prism(rpoly([(0, 0), (630, 0), (630, 280), (0, 280)], 5), "y", 0.0, 3.0, MAT, spec=0.08)
    if wall:
        s.face([(-30, -30, 0), (660, -30, 0), (660, 210, 0), (-30, 210, 0)], hx("#DCE3EB"),
               outline=False, spec=0.02, back=True)


def desk_patch(s, x0, x1, z0, z1, mat=True):
    """A cropped piece of the desk, so an isolated product still has real ground under it."""
    s.prism([(x0, z0), (x1, z0), (x1, z1), (x0, z1)], "y", -18.0, 0.0, WALNUT, spec=0.12)
    if mat:
        s.prism([(x0, z0), (x1, z0), (x1, z1), (x0, z1)], "y", 0.0, 3.0, MAT, spec=0.08)
    s.face([(x0, -18, z1), (x1, -18, z1), (x1, 0, z1), (x0, 0, z1)], shade(WALNUT, 0.82),
           outline=True, spec=0.1)
    s.face([(x0, -18, z0), (x0, -18, z1), (x0, 0, z1), (x0, 0, z0)], shade(WALNUT, 0.9),
           outline=True, spec=0.1)


# ---------------------------------------------------------------- product 1
def aero_bridge(s, deck=True, laptop=True, lid=True):
    xa = bb("W1A_Left_Wood_Arch")
    xb = bb("W1B_Right_Wood_Arch")
    z0, z1 = xa[2]
    yb, yt = xa[1]
    prof = [
        (yb, z0), (yb, 160), (yb + 13, 160), (yb + 16, z0 + 46),
        (65, z0 + 98), (65, z1), (78, z1), (yt, z0),
    ]
    prof = rpoly(prof, 9, 5)
    for x0, x1 in ((xa[0][0], xa[0][1]), (xb[0][0], xb[0][1])):
        s.prism(prof, "x", x0, x1, BIRCH, spec=0.18)
        for xx in (x0 - 0.5, x1 + 0.1):
            s.prism(stadium_2d(61.0, z0 + 26.0, 20.0, 56.0), "x", xx, xx + 0.4,
                    mix(BIRCH, (0, 0, 0), 0.42), outline=False, spec=0.05)

    if deck:
        t = math.radians(18.0)
        uz, uy = -math.cos(t), math.sin(t)
        nz, ny = math.sin(t), math.cos(t)
        zf, yf, L, W = 258.0, 78.0, 250.0, 6.0
        p0 = (yf, zf)
        p1 = (yf + L * uy, zf + L * uz)
        p2 = (p1[0] + W * ny, p1[1] + W * nz)
        p3 = (yf + W * ny, zf + W * nz)
        s.prism([p0, p1, p2, p3], "x", xa[0][0], xb[0][1], WALNUT_L, spec=0.2)  # profile is (y, z)
        for k in range(6):
            sx = xa[0][0] + 25.0 + k * 52.8
            quad = []
            for du, dv in ((-59, -15), (59, -15), (59, 15), (-59, 15)):
                yy = yf + (125 + du) * uy + (W + 1.3) * ny
                zz = zf + (125 + du) * uz + (W + 1.3) * nz
                quad.append((sx + dv, yy, zz))
            s.face(quad, hx("#101821"), outline=False, spec=0.02)
        s.face([(xa[0][0], yf + W * ny - 0.5, zf + W * nz - 0.5),
                (xb[0][1], yf + W * ny - 0.5, zf + W * nz - 0.5),
                (xb[0][1], yf + W * ny - 0.5, zf + W * nz - 2.5),
                (xa[0][0], yf + W * ny - 0.5, zf + W * nz - 2.5)], WALNUT, outline=False, spec=0.1)

    for n in ("M1A_Rear_TieRod", "M1B_Front_TieRod"):
        x, y, z = bb(n)
        s.tube_x(x[0], x[1], (y[0] + y[1]) / 2, (z[0] + z[1]) / 2, 4.0, METAL, seg=22)

    for n in ("P1E_Collar_Left", "P1E_Collar_Right"):
        x, y, z = bb(n)
        s.prism(rpoly([(y[0], z[0]), (y[1], z[0]), (y[1], z[1]), (y[0], z[1])], 10), "x",
                x[0], x[1], RED, spec=0.3)

    for n in ("P1D_Stopper_Left", "P1D_Stopper_Right"):
        x, y, z = bb(n)
        s.prism(rpoly([(y[0], z[0]), (y[1], z[0]), (y[1], z[1]), (y[0], z[1])], 8), "x",
                x[0], x[1], PRINT_L, spec=0.25)

    x, y, z = bb("P1F_MagPivot_Arm")
    s.panel(x[0], x[1], y[0], y[1], z[0], z[1], PRINT, r=10, spec=0.28)
    x, y, z = bb("P1G_MagSafe_Disc")
    s.tube_z(z[0], z[1], (x[0] + x[1]) / 2, (y[0] + y[1]) / 2, 35.0, PRINT, seg=40)
    s.tube_z(z[1], z[1] + 0.8, (x[0] + x[1]) / 2, (y[0] + y[1]) / 2, 27.0, RED, seg=40)
    s.disc_y((x[0] + x[1]) / 2, (z[0] + z[1]) / 2, 8.0, y[0] + 34, y[0] + 36,
             mix(PRINT, (0, 0, 0), 0.5))

    if laptop:
        lap(s, lid=lid)


def lap(s, lid=True):
    """ASUS ROG Strix G16 on the W1C deck at 18 degrees."""
    t = math.radians(18.0)
    uz, uy = -math.cos(t), math.sin(t)
    nz, ny = math.sin(t), math.cos(t)
    zf, yf = 257.0, 79.0
    base = [
        (yf, zf),
        (yf + 264 * uy, zf + 264 * uz),
        (yf + 264 * uy + 24 * ny, zf + 264 * uz + 24 * nz),
        (yf + 24 * ny, zf + 24 * nz),
    ]
    s.prism(base, "x", 91.0, 445.0, hx("#232B35"), spec=0.35)
    s.prism([(yf + 60 * uy + 22 * ny, zf + 60 * uz + 22 * nz),
             (yf + 240 * uy + 22 * ny, zf + 240 * uz + 22 * nz),
             (yf + 240 * uy + 24 * ny, zf + 240 * uz + 24 * nz),
             (yf + 60 * uy + 24 * ny, zf + 60 * uz + 24 * nz)], "x", 108.0, 428.0, KEY_CAP, spec=0.1)
    if not lid:
        return
    sa = math.radians(110.0 - 18.0)
    sz, sy = -math.cos(sa), math.sin(sa)
    zr, yr = zf + 264 * uz, yf + 264 * uy
    s.prism([(yr, zr),
             (yr + 245 * sy, zr + 245 * sz),
             (yr + 245 * sy + 7 * sz, zr + 245 * sz - 7 * sy),
             (yr + 7 * sy, zr + 7 * sz)], "x", 94.0, 442.0, hx("#2A333F"), spec=0.4)
    s.prism([(yr + 16 * sy + 6 * ny, zr + 16 * sz + 6 * nz),
             (yr + 232 * sy + 6 * ny, zr + 232 * sz + 6 * nz),
             (yr + 232 * sy + 8 * ny, zr + 232 * sz + 8 * nz),
             (yr + 16 * sy + 8 * ny, zr + 16 * sz + 8 * nz)], "x", 106.0, 430.0,
            hx("#18202B"), spec=0.5)
    s.prism([(yr + 24 * sy + 8.4 * ny, zr + 24 * sz + 8.4 * nz),
             (yr + 224 * sy + 8.4 * ny, zr + 224 * sz + 8.4 * nz),
             (yr + 224 * sy + 9.2 * ny, zr + 224 * sz + 9.2 * nz),
             (yr + 24 * sy + 9.2 * ny, zr + 24 * sz + 9.2 * nz)], "x", 112.0, 424.0,
            hx("#1D4E63"), spec=0.6)
    s.face([(240.0, yr + 60 * sy + 7.6 * ny, zr + 60 * sz + 7.6 * nz),
            (240.0, yr + 120 * sy + 7.6 * ny, zr + 120 * sz + 7.6 * nz),
            (240.0, yr + 120 * sy + 9.9 * ny, zr + 120 * sz + 9.9 * nz),
            (240.0, yr + 60 * sy + 9.9 * ny, zr + 60 * sz + 9.9 * nz)], RED, outline=False, spec=0.3)


# ---------------------------------------------------------------- product 2
def stealth_vault(s, hanger=True):
    for n in ("P2A_Rear_Clamp_Arch", "P2B_Front_Clamp_Arch"):
        x, y, z = bb(n)
        s.prism(rpoly([(x[0], z[0]), (x[1], z[0]), (x[1], z[1]), (x[0], z[1])], 6), "y",
                y[0], y[1], PRINT, spec=0.22)
    for n, col in (("W2A_Bottom_Wood_Tray", WALNUT), ("W2B_Walnut_Shield", WALNUT_L)):
        x, y, z = bb(n)
        s.prism(rpoly([(x[0], z[0]), (x[1], z[0]), (x[1], z[1]), (x[0], z[1])], 4), "y",
                y[0], y[1], col, spec=0.16)
    x, y, z = bb("P2C_Cable_Spine")
    s.prism(rpoly([(y[0], z[0]), (y[1], z[0]), (y[1], z[1]), (y[0], z[1])], 6), "x",
            x[0], x[1], PRINT_L, spec=0.2)
    xw, yw, zw = bb("W2B_Walnut_Shield")
    for k in range(9):
        zc = zw[0] + 22 + k * 18
        if zc + 9 > zw[1] - 10:
            break
        s.face([(xw[0] - 0.6, yw[0] + 18, zc), (xw[0] - 0.6, yw[0] + 66, zc),
                (xw[0] - 0.6, yw[0] + 66, zc + 9), (xw[0] - 0.6, yw[0] + 18, zc + 9)],
               mix(WALNUT, (0, 0, 0), 0.45), outline=False, spec=0.05)
    s.box(-10.0, 16.0, -112.0, -30.0, 22.0, 202.0, hx("#232A33"), r=3)

    x, y, z = bb("P2D_ULT_Bearing_Hub")
    s.prism(rpoly([(y[0], z[0]), (y[1], z[0]), (y[1], z[1]), (y[0], z[1])], 12), "x",
            x[0], x[1], PRINT, spec=0.25)
    s.tube_x(x[0] - 1, x[1] + 1, (y[0] + y[1]) / 2, (z[0] + z[1]) / 2, 11.0, METAL, seg=24)
    x, y, z = bb("P2E_ULT_Axle_Collar")
    s.tube_x(x[0], x[1], (y[0] + y[1]) / 2, (z[0] + z[1]) / 2, 12.0, RED, seg=24)
    x, y, z = bb("W2C_Walnut_ULT_Saddle")
    s.box(x[0], x[1], y[0], y[1], (z[0] + z[1]) / 2 - 19.0, (z[0] + z[1]) / 2 + 19.0, WALNUT,
          r=14, spec=0.2)
    if hanger:
        cx = (x[0] + x[1]) / 2 + 6
        cz = (z[0] + z[1]) / 2
        s.face([(cx - 40, y[1], cz - 16), (cx + 40, y[1], cz - 16), (cx + 34, y[1] + 26, cz - 12),
                (cx - 34, y[1] + 26, cz - 12)], hx("#2A323C"), spec=0.2, outline=False)
        s.tube_x(cx - 62, cx - 44, y[1] + 20, cz - 4, 21.0, hx("#333C47"), seg=20)
        s.tube_x(cx + 44, cx + 62, y[1] + 20, cz - 4, 21.0, hx("#333C47"), seg=20)


# ---------------------------------------------------------------- product 3
def hydro_sling(s, bottle=True):
    cx, cz = 40.0, 334.0
    r_out, r_in = 49.5, 44.0
    y_rim, cage_h = -92.0, 84.0
    s.disc_y(cx, cz, r_out, y_rim - cage_h, y_rim, PRINT, seg=44)
    s.tube_y(y_rim - cage_h + 6, y_rim, cx, cz, (r_out + r_in) / 2, PRINT_L, seg=44)
    for a in (-38, 38, 142, 218):
        x = cx + (r_out + 1.0) * math.cos(math.radians(a))
        z = cz + (r_out + 1.0) * math.sin(math.radians(a))
        s.face([(x, y_rim - 62, z), (x, y_rim - 12, z), (x, y_rim - 12, z + 6),
                (x, y_rim - 62, z + 6)], mix(PRINT, (0, 0, 0), 0.55), outline=False, spec=0.04)
    s.prism(rpoly([(-9.5, 262.0), (26.5, 262.0), (26.5, 292.0), (-9.5, 292.0)], 4), "y",
            -26.0, 5.5, PRINT, spec=0.24)
    x, y, z = bb("W3A_Walnut_Coaster")
    s.disc_y((x[0] + x[1]) / 2, (z[0] + z[1]) / 2, 42.0, y[0], y[1], WALNUT, seg=40)
    if bottle:
        s.tube_y(-168.0, -12.0, cx, cz, 38.0, BOTTLE, seg=40)
        s.tube_y(-172.0, -168.0, cx, cz, 36.0, mix(BOTTLE, (0, 0, 0), 0.35), seg=36)
        s.tube_y(-34.0, -12.0, cx, cz, 33.0, mix(BOTTLE, (0, 0, 0), 0.22), seg=36)
        s.disc_y(cx, cz, 30.0, -40.0, -34.0, RED, seg=34)
    for n in ("P3B_Left_Runner", "P3B_Right_Runner"):
        x, y, z = bb(n)
        s.panel(x[0], x[1], -48.0, 8.0, z[0], z[1], PRINT, r=6, spec=0.22)
    x, y, z = bb("W3B_Walnut_Notebook_Tray")
    mx = (x[0] + x[1]) / 2
    s.prism(rpoly([(x[0], z[0]), (x[1], z[0]), (x[1], z[1]), (mx + 34, z[1]),
                   (mx + 22, z[1] - 18), (mx - 22, z[1] - 18), (mx - 34, z[1])], 8), "y",
            y[0], y[1], BIRCH, spec=0.16)
    for n in ("P3C_Left_Cleat", "P3C_Right_Cleat"):
        x, y, z = bb(n)
        s.prism(rpoly([(y[0], z[0]), (y[1], z[0]), (y[1], z[1]), (y[0], z[1])], 2), "x",
                x[0], x[1], RED, spec=0.18)
    s.box(28.0, 176.0, -30.5, -24.5, 122.0, 266.0, hx("#C9D3DE"), r=3, spec=0.25)
    s.face([(28.0, -24.2, 122.0), (176.0, -24.2, 122.0), (176.0, -24.2, 128.0), (28.0, -24.2, 128.0)],
           hx("#8A3844"), outline=False, spec=0.1)


# ---------------------------------------------------------------- product 4
def hex_wing(s, spire=True):
    x, y, z = bb("P4A_Right_CClamp")
    s.prism(rpoly([(x[0], 5.0), (x[1], 5.0), (x[1], -42.0), (x[0], -42.0)], 6), "z",
            z[0], z[1], PRINT, spec=0.24)
    for n, col in (("W4A_Bottom_Walnut_Deck", WALNUT), ("W4B_Top_Walnut_Collar", WALNUT_L)):
        x, y, z = bb(n)
        s.prism(stadium_2d(x[0], z[0], x[1] - x[0], z[1] - z[0], 7), "y", y[0], y[1], col, spec=0.18)
    x, y, z = bb("P4B_Fluted_Core")
    s.prism(stadium_2d(x[0] + 2, z[0] + 2, x[1] - x[0] - 4, z[1] - z[0] - 4, 7), "y",
            y[0], y[1], PRINT, spec=0.2)
    for k in range(7):
        zz = z[0] + 8 + k * 16.5
        if zz > z[1] - 8:
            break
        s.face([(x[0] - 0.4, y[0] + 6, zz), (x[0] - 0.4, y[1] - 6, zz),
                (x[0] - 0.4, y[1] - 6, zz + 6), (x[0] - 0.4, y[0] + 6, zz + 6)],
               PRINT_L, outline=False, spec=0.16)
    for px in (x[0] + 19, x[0] + 49):
        for pz in (z[0] + 21, z[0] + 51, z[0] + 81):
            s.disc_y(px, pz, 11.5, y[1] - 1.0, y[1] + 0.6, hx("#0A0E14"), seg=22)
    x, y, z = bb("W4C_Walnut_Drawer_Face")
    s.panel(x[0], x[1], y[0], y[1], z[1] - 0.5, z[1] + 0.5, WALNUT, r=7, spec=0.2)
    s.face([(x[0] + 19, (y[0] + y[1]) / 2 - 1.4, z[1] + 0.7),
            (x[0] + 33, (y[0] + y[1]) / 2 - 1.4, z[1] + 0.7),
            (x[0] + 33, (y[0] + y[1]) / 2 + 1.4, z[1] + 0.7),
            (x[0] + 19, (y[0] + y[1]) / 2 + 1.4, z[1] + 0.7)],
           mix(WALNUT, (0, 0, 0), 0.55), outline=False, spec=0.05)
    if spire:
        wing = rpoly([(632.7, 50.0), (683.8, 50.0), (660.0, 96.0), (632.7, 144.1),
                      (629.0, 132.0), (648.0, 92.0)], 4)
        s.prism(wing, "z", 20.0, 34.0, PRINT, spec=0.28)
        s.tube_z(19.5, 34.5, 641.0, 137.0, 11.0, METAL, seg=22)
        s.tube_z(34.0, 36.0, 641.0, 137.0, 8.0, RED, seg=20)


# ---------------------------------------------------------------- product 5
def holo_buddy(s):
    x, y, z = bb("P5D_Wing_Arm")
    s.prism(rpoly([(y[0] + 4, z[0]), (y[1] - 26, z[0]), (y[1] - 26, z[1]), (y[0] + 4, z[1])], 8),
            "x", x[0] - 7.0, x[1], PRINT, spec=0.24)
    x, y, z = bb("P5B_Electronics_Base")
    s.prism(rpoly([(x[0], z[0]), (x[1], z[0]), (x[1], z[1]), (x[0], z[1])], 9), "y",
            y[0], y[1], PRINT_L, spec=0.24)
    x, y, z = bb("P5A_Optical_Core")
    s.prism(rpoly([(x[0], z[0]), (x[1], z[0]), (x[1], z[1]), (x[0], z[1])], 8), "y",
            y[0], y[1], PRINT, spec=0.26)
    for n in ("W5A_Left_Walnut_Cheek", "W5A_Right_Walnut_Cheek"):
        x, y, z = bb(n)
        s.panel(x[0], x[1], y[0], y[1], z[0], z[1], WALNUT, r=6, spec=0.2)
    s.box(490.0, 515.4, 121.7, 147.1, 70.0, 95.4, GLASS, r=1.0, outline=True, spec=0.75)
    s.face([(490, 121.7, 95.4), (515.4, 121.7, 95.4), (515.4, 121.7, 70.0), (490, 121.7, 70.0)],
           mix(GLASS, (255, 255, 255), 0.45), outline=False, spec=0.9)
    s.face([(490, 121.7, 95.4), (515.4, 121.7, 95.4), (515.4, 147.1, 95.4), (490, 147.1, 95.4)],
           mix(GLASS, (255, 255, 255), 0.2), outline=False, spec=0.9)
    s.face([(491, 115.4, 78.0), (514, 115.4, 78.0), (514, 115.4, 94.0), (491, 115.4, 94.0)],
           hx("#8FE3FF"), outline=False, spec=0.5)
    x, y, z = bb("P5C_Magnetic_Visor")
    s.prism(rpoly([(y[0], z[0]), (y[1], z[0]), (y[1], z[1]), (y[0], z[1])], 4), "x",
            x[0], x[1], RED, spec=0.35)


def arch_stub(s, x0):
    """Just the right DT-30 collar of the AeroBridge, so an isolated HoloBuddy
    still shows the joint it actually hangs on."""
    x, y, z = bb("P1E_Collar_Right")
    s.prism(rpoly([(y[0], z[0]), (y[1], z[0]), (y[1], z[1]), (y[0], z[1])], 10), "x",
            x0 - 12.0, x0, RED, spec=0.3)
    s.prism(rpoly([(y[0] + 9, z[0] + 9), (y[1] - 9, z[0] + 9), (y[1] - 9, z[1] - 9),
                   (y[0] + 9, z[1] - 9)], 6), "x", x0 - 11.8, x0 - 0.1, mix(PRINT, RED, 0.35),
            outline=False, spec=0.1)


def pedestal(s):
    x, y, z = bb("W5B_Walnut_Coaster")
    s.disc_y((x[0] + x[1]) / 2, (z[0] + z[1]) / 2, 35.0, y[0], y[1], WALNUT, seg=36)
    x, y, z = bb("P5E_Pedestal_Hub")
    s.disc_y((x[0] + x[1]) / 2, (z[0] + z[1]) / 2, 18.0, y[0], y[1], PRINT, seg=30)
    s.disc_y((x[0] + x[1]) / 2, (z[0] + z[1]) / 2, 11.0, y[1] - 7.0, y[1] - 6.0, METAL, seg=26)


# ---------------------------------------------------------------- devices
def keyboard(s):
    s.box(106.5, 429.5, 3.0, 46.1, 132.0, 275.2, hx("#2B3442"), r=5, spec=0.2)
    s.face([(106.5, 46.2, 132.0), (429.5, 46.2, 132.0), (429.5, 46.2, 275.2), (106.5, 46.2, 275.2)],
           KEY_CAP, outline=False, spec=0.15)
    s.face([(114.0, 46.4, 142.0), (422.0, 46.4, 142.0), (422.0, 46.4, 266.0), (114.0, 46.4, 266.0)],
           hx("#39465C"), outline=False, spec=0.1)
    s.face([(190.0, 46.6, 234.0), (346.0, 46.6, 234.0), (346.0, 46.6, 262.0), (190.0, 46.6, 262.0)],
           hx("#4A5B76"), outline=False, spec=0.1)
    s.face([(418.0, 46.6, 138.0), (426.0, 46.6, 138.0), (426.0, 46.6, 146.0), (418.0, 46.6, 146.0)],
           RED, outline=False, spec=0.3)


def mouse(s):
    x0, x1, z0, z1 = 506.0, 570.0, 125.0, 250.0
    s.box(x0, x1, 3.0, 20.0, z0, z1, hx("#1F7A45"), r=26, spec=0.3)
    s.prism(rpoly([(x0 + 2, z0 + 6), (x1 - 2, z0 + 6), (x1 - 2, z1 - 6), (x0 + 2, z1 - 6)], 26),
            "y", 20.0, 40.0, hx("#27A05A"), spec=0.35)
    s.face([(x0 + 12, 33.0, z0 + 30), (x1 - 12, 33.0, z0 + 30), (x1 - 12, 33.0, z0 + 34),
            (x0 + 12, 33.0, z0 + 34)], hx("#0E2A1A"), outline=False, spec=0.1)


def phone(s):
    x0, x1, y0, y1 = -14.0, 66.0, 68.0, 231.0
    s.panel(x0, x1, y0, y1, 99.5, 111.5, PHONE, r=9, spec=0.4)
    s.face([(x0 + 6, y0 + 6, 99.0), (x1 - 6, y0 + 6, 99.0), (x1 - 6, y1 - 6, 99.0),
            (x0 + 6, y1 - 6, 99.0)], hx("#123244"), outline=False, spec=0.5)


def coupon(s):
    """Product 0 six-in-one printer / hardware fit coupon (90 x 150 x 14 mm)."""
    s.prism(rpoly([(0, 0), (90, 0), (90, 150), (0, 150)], 8), "y", 0.0, 14.0, PRINT, spec=0.2)
    s.prism(rpoly([(8, 16), (34, 16), (30, 130), (12, 130)], 2), "y", 14.0, 20.0, PRINT_L, spec=0.22)
    for k in range(6):
        s.disc_y(50 + (k % 3) * 14, 26 + (k // 3) * 16, 1.5 + k * 0.05, 12.0, 20.0,
                 hx("#0A0E14"), seg=18)
    s.disc_y(62, 78, 11.0, 14.0, 20.5, PRINT_L, seg=26)
    s.disc_y(62, 78, 8.0, 14.0, 21.0, hx("#0A0E14"), seg=22)
    s.disc_y(44, 100, 3.1, 14.0, 17.4, hx("#0A0E14"), seg=16)
    s.disc_y(66, 100, 2.6, 14.0, 18.6, hx("#0A0E14"), seg=16)
    s.prism(stadium_2d(26, 132, 44, 10), "y", 14.0, 15.0, hx("#0A0E14"), spec=0.05)
    s.face([(90, 0, 0), (90, 14, 0), (90, 14, 150), (90, 0, 150)],
           mix(PRINT, RED, 0.45), outline=False, spec=0.2)


# ---------------------------------------------------------------- scenes
def scene_full(pedestal_on=True, hanger=True, bottle=True, lid=True, keyboard_on=True,
               deck=True, laptop=True, mat=True, desk_slab=True):
    s = Scene()
    desk(s, slab=desk_slab, mat=mat)
    s.solids.clear()
    aero_bridge(s, deck=deck, laptop=laptop, lid=lid)
    stealth_vault(s, hanger=hanger)
    hydro_sling(s, bottle=bottle)
    hex_wing(s)
    holo_buddy(s)
    if pedestal_on:
        pedestal(s)
    if keyboard_on:
        keyboard(s)
    mouse(s)
    phone(s)
    return s


def scene_product(which):
    s = Scene()
    if which == "p1":
        desk(s, mat=True)
        aero_bridge(s)
        phone(s)
    elif which == "p2":
        desk_patch(s, -58, 56, 2, 252)
        stealth_vault(s)
    elif which == "p3":
        hydro_sling(s)
    elif which == "p4":
        desk_patch(s, 585, 715, 0, 165)
        hex_wing(s)
    elif which == "p5":
        x, y, z = bb("W5B_Walnut_Coaster")
        cx, cz = (x[0] + x[1]) / 2, (z[0] + z[1]) / 2
        desk_patch(s, cx - 82, cx + 82, cz - 82, cz + 82)
        pedestal(s)
        holo_buddy(s)
    elif which == "p5d":
        x, y, z = bb("W5B_Walnut_Coaster")
        cx, cz = (x[0] + x[1]) / 2, (z[0] + z[1]) / 2
        desk_patch(s, cx - 78, cx + 78, cz - 78, cz + 78)
        pedestal(s)
    elif which == "p5m":
        desk_patch(s, 428, 542, 0, 175)
        arch_stub(s, 446.0)
        holo_buddy(s)
    elif which == "p0":
        desk_patch(s, -12, 102, -12, 162)
        coupon(s)
    return s
