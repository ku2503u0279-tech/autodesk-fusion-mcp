"""AeroBridge Studio, product 1 — the scroll.

The object is a stack of ply laminations. Each one is a closed cross-section
extruded across a slice of the width; no two are the same shape, so the stack
makes one continuous surface that ripples across the desk. That is the design.

The section is an arch: a tilted seat on top for the laptop, and a garage
underneath the seat that a keyboard slides into. Feet at both ends stand on the
desk, so the laptop's weight lands straight over the feet instead of trying to
peel the arch open.

How the shape stays valid
    The outer path is a polyline with a tangent arc at every corner, so it is
    G1 continuous. The inner path is that same dense path pushed inward by one
    constant wall. Offsetting a G1 path is only safe where the wall is smaller
    than the local radius of curvature, so every convex radius here is at least
    40 mm against an 18 mm wall. The toe corners are left sharp and the legs
    meet the desk vertically: that is what makes the inner path land exactly on
    the floor, so the section closes with two straight floor segments and there
    is no corner to fold over.

Every lamination is then an AFFINE MAP of that section: scale in Y, scale in Z,
translate. An affine map cannot turn a simple polygon into a crossing one, so
the other ten sections are safe by construction rather than by luck.

Coordinates
    z  0 at the back edge of the desk, positive toward the user
    y  0 on the desk mat, positive up
    x  0 at the left edge, positive right
"""
import math

import numpy as np

# ------------------------------------------------------------------ the section
# Outer skeleton, back toe -> over the seat -> front toe, as (z, y, r).
# r is the fillet radius at that corner. Zero means leave it sharp.
OUTER = [
    (30.0, 0.0, 0.0),      # back toe, on the desk
    (30.0, 150.0, 60.0),   # long shoulder off the back face onto the deck
    (54.0, 246.0, 0.0),    # back edge of the deck: crisp, and that matters
    (300.0, 140.0, 0.0),   # front edge of the deck: crisp too
    (312.0, 80.0, 70.0),   # long roll off the front face onto the deck
    (312.0, 0.0, 0.0),     # front toe, on the desk
]

WALL = 18.0          # section wall.
# A convex fillet smaller than the wall cannot be offset inward — the inner
# path collapses to a cusp and folds, so every rounded corner here is either
# sharp or at least twice the wall. The sharp ones are the seat edges, which
# want to read as machined edges rather than soft folds anyway.
TOE_LEN = 0.0


def _unit(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy)
    if L < 1e-12:
        return (0.0, 0.0)
    return (dx / L, dy / L)


def fillet(v0, v1, v2, r, steps=18):
    """Points of the arc rounding the corner at v1. Exact tangent construction.

    Returns (points, tangent_length). The points run from the tangent point on
    v0->v1 to the tangent point on v1->v2, so they can be spliced straight into
    the path.
    """
    if r <= 1e-9:
        return [], 0.0
    u1, u2 = _unit(v0, v1), _unit(v1, v2)
    if u1 == (0.0, 0.0) or u2 == (0.0, 0.0):
        return [], 0.0
    d = math.atan2(u1[0] * u2[1] - u1[1] * u2[0], u1[0] * u2[0] + u1[1] * u2[1])
    if abs(d) < 1e-9:
        return [], 0.0
    t = r * math.tan(abs(d) / 2.0)
    sgn = 1.0 if d > 0 else -1.0
    n1 = (-u1[1] * sgn, u1[0] * sgn)
    T1 = (v1[0] - u1[0] * t, v1[1] - u1[1] * t)
    C = (T1[0] + n1[0] * r, T1[1] + n1[1] * r)
    T2 = (v1[0] + u2[0] * t, v1[1] + u2[1] * t)
    a0 = math.atan2(T1[1] - C[1], T1[0] - C[0])
    a1 = math.atan2(T2[1] - C[1], T2[0] - C[0])
    dd = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
    pts = [(C[0] + r * math.cos(a0 + dd * k / steps),
            C[1] + r * math.sin(a0 + dd * k / steps)) for k in range(steps + 1)]
    return pts, t


def _dedup(pts, eps=0.02):
    out = [pts[0]]
    for q in pts[1:]:
        if math.hypot(q[0] - out[-1][0], q[1] - out[-1][1]) > eps:
            out.append(q)
    return out


def outer_path():
    """The arch, one G1 polyline, from the back toe to the front toe."""
    out = []
    n = len(OUTER)
    for i in range(n - 1):
        p = (OUTER[i][0], OUTER[i][1])
        q = (OUTER[i + 1][0], OUTER[i + 1][1])
        if i == 0:
            out.append(p)
        if i + 1 < n - 1:                       # fillet the far end of this leg
            pts, t = fillet((OUTER[i][0], OUTER[i][1]), q,
                            (OUTER[i + 2][0], OUTER[i + 2][1]),
                            OUTER[i + 1][2])
        else:
            pts, t = [], 0.0
        if t > 1e-9:
            out.extend(pts)
        else:
            out.append(q)
    out.append((OUTER[-1][0], OUTER[-1][1]))
    return _dedup(out)


def inner_path(o=None, wall=WALL):
    """The outer path pushed inward by `wall`, landing on the floor at both toes.

    Each vertex moves along the bisector of its two adjacent inward normals, at
    the MITER length wall / cos(half-angle). Using the plain wall length along
    the bisector — which is what this did at first — slides every corner too
    little, the wall pinches on the inside of a curve, and on a tight corner the
    path doubles back and crosses itself.

    Where two segments meet at an angle, the bisector is steeper than either
    normal, so it has to travel further to stand `wall` clear of both. The half
    angle is recovered from the bisector's own length: for unit normals n1, n2,
    |n1 + n2| = 2 cos(theta/2), so miter = 2 / |n1 + n2|.
    """
    o = o or outer_path()
    P = np.asarray(o, dtype=float)
    seg = np.diff(P, axis=0)
    L = np.linalg.norm(seg, axis=1, keepdims=True)
    seg = seg / np.maximum(L, 1e-12)
    nrm = np.stack([seg[:, 1], -seg[:, 0]], axis=1)     # right normal = inward

    vn = np.zeros_like(P)
    vn[0] = nrm[0]
    vn[-1] = nrm[-1]
    vn[1:-1] = nrm[:-1] + nrm[1:]
    ln = np.linalg.norm(vn, axis=1, keepdims=True)
    # guard the miter: at a hairpin the bisector vanishes and the miter runs away
    ln = np.clip(ln, 1e-6, None)
    miter = np.minimum(2.0 / ln, 4.0)
    Q = P + (vn / ln) * wall * miter
    Q[:, 1] = np.maximum(Q[:, 1], 0.0)
    Q[0, 1] = 0.0
    Q[-1, 1] = 0.0
    return [tuple(q) for q in Q]


def section():
    """The closed section: out along the outer path, back along the inner.

    The seat is snapped onto its own plane here, once, for every consumer. The
    fillet arcs either side of it are sampled finely enough that a point can sit
    a few hundredths of a millimetre off the flat; left alone, eleven of those
    add up to a surface a laptop rocks on.
    """
    o = outer_path()
    i = inner_path(o)
    st = seat_line()
    out = []
    for (z, y) in o:
        if st["z0"] - 0.01 <= z <= st["z1"] + 0.01:
            y = _seat_y(z)
        out.append((z, max(y, 0.0)))
    return out + list(reversed(i))


def self_crossings(loop):
    """Count proper segment crossings. Zero means the section is simple."""
    n = len(loop)
    hits = 0

    def crs(o, p, q):
        return (p[0] - o[0]) * (q[1] - o[1]) - (p[1] - o[1]) * (q[0] - o[0])

    def cross(a, b, c, d):
        d1, d2 = crs(c, d, a), crs(c, d, b)
        d3, d4 = crs(a, b, c), crs(a, b, d)
        return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0))

    for a in range(n):
        for b in range(a + 2, n):
            if a == 0 and b == n - 1:
                continue
            if cross(loop[a], loop[(a + 1) % n], loop[b], loop[(b + 1) % n]):
                hits += 1
    return hits


def min_wall(loop, n_out):
    """Closest approach between the two paths, in mm."""
    best = 1e9
    for p in loop[n_out:]:
        for q in loop[:n_out]:
            best = min(best, math.hypot(p[0] - q[0], p[1] - q[1]))
    return best


# ------------------------------------------------------------- the lamination
# The stack, left to right.
SHELL = dict(
    n=11,                 # laminations
    span=372.0,           # overall width, X. A laptop is ~340 wide,
                          # so the stand is a little wider than the machine and
                          # nothing more. At 520 this read as a riser shelf.
    gap=0.55,             # the saw cut between laminations. Real, and it is
                          # what draws the lines across the surface. Any wider
                          # and the slot becomes a tunnel you can see into, which
                          # renders as black teeth along the crown.
    shoulder=0.030,       # how far the back shoulder waves, as a fraction of
                          # its height. This is the whole ripple.
    shoulder_z=0.0,       # ... and how far it waves in Z, in mm.
)
SPLIT_Z = 54.0            # = the back edge of the deck


def _seat_ends():
    """Where the flat of the seat really starts and stops.

    Not the skeleton vertices: the fillet behind it eats into the seat, so the
    flat runs from the tangency point to the front vertex. Measured off the
    same fillet call that builds the path, so it cannot drift.
    """
    u = _unit((OUTER[2][0], OUTER[2][1]), (OUTER[3][0], OUTER[3][1]))
    _p, t = fillet((OUTER[1][0], OUTER[1][1]), (OUTER[2][0], OUTER[2][1]),
                   (OUTER[3][0], OUTER[3][1]), OUTER[2][2])
    a = (OUTER[2][0] + u[0] * t, OUTER[2][1] + u[1] * t)
    b = (OUTER[3][0], OUTER[3][1])
    return dict(z0=a[0], y0=a[1], z1=b[0], y1=b[1])


_seat_cache = {}


def seat_line():
    """The seat as a plane: back edge and front edge, in the base section."""
    if "v" not in _seat_cache:
        _seat_cache["v"] = _seat_ends()
    return _seat_cache["v"]


def _seat_y(z):
    s = seat_line()
    t = min(max((z - s["z0"]) / (s["z1"] - s["z0"]), 0.0), 1.0)
    return s["y0"] + (s["y1"] - s["y0"]) * t


def _anchor_z():
    """The plane every lamination finishes on, in front."""
    return max(p[0] for p in outer_path())


def lamination_profiles(P=None):
    """Every lamination's cross-section, plus the slice of X it occupies.

    The outer path is deformed, then the inner path is re-derived as an offset
    of the DEFORMED path. That is the important part: offsetting after the
    deformation means the wall is exactly WALL everywhere, instead of being
    right in the base section and wrong everywhere else. The wall is what
    carries the laptop, so it is not allowed to vary across the stack.

    The deformation is one vertical scale, ramped smoothly to zero at the seat
    and at the floor. Everything the laptop touches is therefore identical in
    all eleven laminations, and the ripple lives entirely in the crown.
    """
    p = P or {}
    n = SHELL["n"]
    sw = SHELL["span"] / n
    o = outer_path()
    out = []
    for k in range(n):
        u = (k - (n - 1) / 2.0) / ((n - 1) / 2.0)
        w = (1.0 - u * u) ** 1.6           # 1 at the middle, 0 at the ends
        amp = SHELL["shoulder"] * (1.0 - w)
        op = []
        for (z, y) in o:
            # The wave peaks in the MIDDLE of the back shoulder and is pinned at
            # both of its ends: at the seat above, and at the back toe below.
            # Keying it to height instead would have left the crown untouched
            # (the crown is the seat edge) and keying it linearly would have put
            # a crease along the back. A sine has zero slope at both ends, so the
            # back face stays flat, the seat stays flat, and the feet stay put.
            t = min(max((SPLIT_Z - z) / (SPLIT_Z - 40.0), 0.0), 1.0)
            r = math.sin(math.pi * t)
            op.append((z + SHELL["shoulder_z"] * amp * r,
                       y * (1.0 - amp * r)))
        ip = inner_path(op)
        poly = [(z, max(0.0, y)) for (z, y) in op] + list(reversed(ip))
        x0 = (p.get("desk_x", 630.0) - SHELL["span"]) / 2.0 + k * sw
        out.append(dict(i=k, u=u, x0=x0, x1=x0 + sw - SHELL["gap"], poly=poly,
                        w=w, amp=amp))
    return out


def _bore(rod):
    """A circle in the section's own (z, y) plane."""
    return [(rod["z"] + rod["r"] * math.cos(2 * math.pi * k / 40.0),
             rod["y"] + rod["r"] * math.sin(2 * math.pi * k / 40.0))
            for k in range(40)]


# Two brass stretcher rods pass right through the front legs, one above the
# other. They sit in the part of the section that is identical in every
# lamination, so a straight rod really does go through all eleven, and the
# collars land flat on the outer faces.
# The front leg's outer face is at z = 252 and its inner face at z = 234, so the
# rod has to sit between them with wood to spare on both sides: r = 4 at z = 243
# leaves 5 mm of wall outside it and 5 mm inside. At z = 250 with r = 5 the bore
# broke out through the front face — a hole into daylight, not a hole in wood.
RODS = [dict(tag="B1", name="Front Stretcher", y=55.0, z=303.0, r=4.0),
        dict(tag="B2", name="Back Stretcher", y=55.0, z=36.0, r=4.0)]
COLLAR = dict(len=15.0, r=11.5)


def stack(P=None):
    """All eleven laminations, each bored for both stretchers."""
    parts = []
    for lam in lamination_profiles(P):
        parts.append(dict(
            tag="L%02d" % (lam["i"] + 1),
            name="Lamination %02d" % (lam["i"] + 1),
            kind="ash", pt="lam", mat="ash",
            x0=lam["x0"], x1=lam["x1"], poly=lam["poly"],
            bores=[_bore(r) for r in RODS],
            chamfer=1.2, thickness=lam["x1"] - lam["x0"], u=lam["u"]))
    return parts


def rod_parts(P=None):
    p = P or {}
    x0 = (p.get("desk_x", 630.0) - SHELL["span"]) / 2.0
    x1 = x0 + SHELL["span"]
    out = []
    for r in RODS:
        out.append(dict(tag=r["tag"], name=r["name"], kind="brass", pt="rod",
                        x0=x0 - 9.0, x1=x1 + 9.0,
                        y=r["y"], z=r["z"], d=2.0 * (r["r"] + 0.2), mat="brass"))
        for side, xa in (("L", x0 - COLLAR["len"]), ("R", x1 - 1.0)):
            out.append(dict(tag=r["tag"] + side, name=r["name"] + " Collar",
                            kind="brass", pt="clamp", mat="brass",
                            x0=xa, x1=xa + COLLAR["len"], y=r["y"], z=r["z"],
                            d=2.0 * COLLAR["r"], length=COLLAR["len"]))
    return out


def stop_parts(P=None):
    """The seat stop: a brass lip standing on the deck at its front edge.

    This is the part that makes it a laptop stand. The deck runs down toward
    the user at 23 degrees, so a laptop on it would slide into the keyboard;
    the bar catches the machine at the front before it can. It is 16 mm wide
    and stands 18 mm proud of the deck, and it is set flush with the deck's
    front edge so none of the deck's length is wasted behind it.

    Its underside follows the seat plane rather than being flat, so it beds
    down on the 23 degree deck instead of touching along one edge, and it is
    sunk 0.4 mm so the two faces cannot be coplanar and flicker.
    """
    p = P or {}
    x0 = (p.get("desk_x", 630.0) - SHELL["span"]) / 2.0 + 54.0
    x1 = x0 + (SHELL["span"] - 108.0)
    st = seat_line()
    zb = st["z1"]            # flush with the deck's front edge
    za = zb - 16.0
    h = 18.0
    return [dict(tag="S1", name="Seat Stop", kind="brass", pt="stop", mat="brass",
                 x0=x0, x1=x1,
                 poly=[(za, _seat_y(za) - 0.4),
                       (zb, _seat_y(zb) - 0.4),
                       (zb, _seat_y(zb) + h),
                       (za, _seat_y(za) + h)])]


def foot_spans():
    """Where the section actually meets the desk, read off the section itself.

    The pads used to be hardcoded at z 42..74 and 214..246, which was left over
    from a shallower stand: they hung in mid-air a clear 60 mm in front of the
    back foot. Derive them from the floor contact and they cannot drift again.
    """
    zs = sorted(z for (z, y) in section() if y <= 0.001)
    back = [z for z in zs if z < 150.0]
    front = [z for z in zs if z >= 150.0]
    return (min(back), max(back)), (min(front), max(front))


def pad_parts(P=None):
    """Felt under the feet, inset 2 mm from every edge so it never shows."""
    p = P or {}
    s = 30.0
    inset = 2.0
    x0 = (p.get("desk_x", 630.0) - SHELL["span"]) / 2.0
    out = []
    for side, xa in (("L", x0 + 226.0), ("R", x0 + 288.0 - s)):
        for end, (za, zb) in zip(("B", "F"), foot_spans()):
            out.append(dict(tag="F%s%s" % (side, end),
                            name="Felt Pad %s %s" % (side, end), kind="felt",
                            pt="pad", mat="felt", x0=xa, x1=xa + s,
                            z0=za + inset, z1=zb - inset, y=0.0,
                            thickness=2.0))
    return out


def assembly(P=None):
    a = dict(P or {})
    return stack(a) + rod_parts(a) + stop_parts(a) + pad_parts(a)


def by_tag(parts, *tags):
    return [p for p in parts if p["tag"] in tags]


# --------------------------------------------------------------- checks
def check(P=None):
    """Plain-English sanity checks. Empty means good."""
    out = []
    sec = section()
    c = self_crossings(sec)
    if c:
        out.append("the section crosses itself (%d)" % c)
    w = min_wall(sec, len(outer_path()))
    if w < 14.0:
        out.append("the section wall pinches to %.1f mm" % w)
    for lam in lamination_profiles(P):
        c = self_crossings(lam["poly"])
        if c:
            out.append("lamination %02d crosses itself (%d)"
                       % (lam["i"] + 1, c))
        ys = [q[1] for q in lam["poly"]]
        if min(ys) < -0.01:
            out.append("lamination %02d dips below the desk" % (lam["i"] + 1))
        if max(ys) > 260.0:
            out.append("lamination %02d is too tall" % (lam["i"] + 1))
        zs = [q[0] for q in lam["poly"]]
        if min(zs) < 2.0:
            out.append("lamination %02d runs off the back of the desk"
                       % (lam["i"] + 1))
        if max(zs) > 322.0:
            out.append("lamination %02d runs off the front of the desk (%0.f)"
                       % (lam["i"] + 1, max(zs)))
    st = seat_line()
    ang = math.degrees(math.atan((st["y0"] - st["y1"]) / (st["z1"] - st["z0"])))
    if not (18.0 < ang < 28.0):
        out.append("the seat sits at %.1f deg; it wants 20-26" % ang)
    if st["z1"] - st["z0"] < 120.0:
        out.append("the flat of the seat is only %.0f mm deep" % (st["z1"] - st["z0"]))
    for r in RODS:
        for lam in lamination_profiles(P):
            if not _inside((r["z"], r["y"]), lam["poly"], shrink=r["r"] + 2.0):
                out.append("rod %s misses solid wood in lamination %02d"
                           % (r["tag"], lam["i"] + 1))
    if max(q[1] for q in sec) < 200.0:
        out.append("the stand is too low to be useful")
    return out


def _area_sign(loop):
    s = 0.0
    n = len(loop)
    for i in range(n):
        s += loop[i][0] * loop[(i + 1) % n][1] - loop[(i + 1) % n][0] * loop[i][1]
    return s


def _loft(z, loop, step=1.0):
    """Highest solid point at depth z, as a cheap vertical ray cast."""
    best = 0.0
    y = 0.0
    inside = False
    while y < 320.0:
        now = _inside((z, y + step * 0.5), loop)
        if now != inside:
            inside = now
            if now:
                best = max(best, y)
        y += step
    return best


def _inside(pt, loop, shrink=0.0):
    """Point-in-polygon, with an optional inward shrink for clearance tests."""
    if shrink > 0.0:
        loop = _shrink(loop, shrink)
    x, y = pt[0], pt[1]
    c = False
    n = len(loop)
    for i in range(n):
        x1, y1 = loop[i]
        x2, y2 = loop[(i + 1) % n]
        if ((y1 > y) != (y2 > y)) and (x < (x2 - x1) * (y - y1) / (y2 - y1) + x1):
            c = not c
    return c


def _shrink(loop, d):
    """Pull a closed loop inward by d, for clearance tests.

    The normal direction depends on the winding, and the section is clockwise.
    Taking the left normal blindly made this EXPAND the loop, so a clearance
    test written with it passed a rod that was breaking out through the face.
    Sign is now chosen from the signed area.
    """
    P = np.asarray(loop, dtype=float)
    seg = np.diff(np.vstack([P, P[:1]]), axis=0)
    L = np.linalg.norm(seg, axis=1, keepdims=True)
    seg = seg / np.maximum(L, 1e-12)
    # left normal is inward for a counter-clockwise loop, outward for clockwise
    cw = _area_sign(loop) < 0
    sgn = -1.0 if cw else 1.0
    nrm = np.stack([-seg[:, 1] * sgn, seg[:, 0] * sgn], axis=1)
    n0 = np.vstack([nrm[-1:], nrm[:-1]])
    vn = n0 + nrm
    ln = np.linalg.norm(vn, axis=1, keepdims=True)
    vn = vn / np.maximum(ln, 1e-12)
    return [tuple(q) for q in (P + vn * d)]


if __name__ == "__main__":
    import studio3d as S3
    o, i = outer_path(), inner_path()
    sec = section()
    print("outer %d pts   inner %d pts   section %d pts" % (len(o), len(i), len(sec)))
    print("crossings %d   min wall %.1f mm   area %.0f mm2"
          % (self_crossings(sec), min_wall(sec, len(o)), S3.signed_area(sec)))
    st = seat_line()
    print("seat z %.1f..%.1f  y %.1f..%.1f  run %.0f mm  %.1f deg"
          % (st["z0"], st["z1"], st["y0"], st["y1"], st["z1"] - st["z0"],
             math.degrees(math.atan((st["y0"] - st["y1"]) / (st["z1"] - st["z0"])))))
    for lam in lamination_profiles():
        ys = [q[1] for q in lam["poly"]]
        print("L%02d u=%+.2f cross=%d  y %5.1f..%5.1f  x %5.1f..%5.1f"
              % (lam["i"] + 1, lam["u"], self_crossings(lam["poly"]),
                 min(ys), max(ys), lam["x0"], lam["x1"]))
    msgs = check()
    print("checks:", "all good" if not msgs else "")
    for m in msgs:
        print("  !", m)
    print("%d parts" % len(assembly()))
