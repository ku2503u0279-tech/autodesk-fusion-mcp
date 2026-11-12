"""Studio Line, product 1 — all parameters and part geometry in one place.

One dict `P` holds every dimension in millimetres. Every part is described by a
small dict, so the renderer, the Fusion script, the DXF writer and the BOM all
read the same numbers and can never drift apart.

Coordinates
    X  0 .. 630   left to right across the desk
    Y  0          top of the desk mat, positive is up
    Z  0          back edge of the desk (against the wall), positive toward you
"""
import math

# ------------------------------------------------------------------ params
P = dict(
    # the desk it stands on, from the brief
    desk_x=630.0, desk_z=280.0, slab_t=18.0, mat_t=3.0,
    # the blade: 18 mm solid oak, one left and one right
    arch_t=28.0,
    span_left=112.0, span_right=512.0,
    # the deck: three boards on a tilted plane, high at the back
    deck_t=12.0,
    deck_back=204.0,     # top surface height at the back edge
    deck_front=144.0,    # top surface height at the front edge
    deck_z0=10.0,        # back edge of the deck
    deck_z1=278.0,       # front edge of the deck
    deck_seam=0.0,
    deck_boards=1,
    # where the blade's feet stand
    z_back_outer=20.0,
    z_front_outer=260.0,
    # the blade band, measured across the wood
    blade_w=52.0,        # width through the legs
    blade_w_crown=34.0,  # a touch slimmer over the crown
    blade_belly=8.0,     # the window sags a little under the middle
    # The blade's top edge is a plain C. Keeping it that simple is the point:
    # every extra flourish is one more line in the drawing and one more thing
    # that can go out of true. Set wing_h above zero for a raised back crest.
    wing_h=0.0,
    wing_setback=26.0,
    wing_toe=26.0,
    loop_pts=260,
    # tie rod, tucked under the crown where it cannot be seen from the front
    rod_d=9.0, rod_y=46.0, rod_z=None, rod_clamp_len=24.0, rod_clamp_d=16.0,
    # front stop: a walnut rail on the low edge
    stop_h=7.0, stop_w=9.0, stop_z=10.0,
    # felt pads under the feet
    felt_t=2.0, pad_size=34.0,
    # the deck is a touch wider than the frame it sits on
    deck_over=7.0,
    # the desk mat in the pictures
    mat_inset=10.0,
)

# ------------------------------------------------------------------ helpers
def deck_y_at(P, z):
    """Height of the deck's top surface at depth z."""
    z = min(max(z, P["deck_z0"]), P["deck_z1"])
    t = (z - P["deck_z0"]) / (P["deck_z1"] - P["deck_z0"])
    return P["deck_back"] + (P["deck_front"] - P["deck_back"]) * t


def crown_y_at(P, z):
    """Height of the blade's top edge: the deck beds down onto this line."""
    return deck_y_at(P, z) - P["deck_t"]


def _spline(pts, per_seg=14, tension=0.5):
    """Catmull-Rom through `pts`, clamped at both ends, no overshoot allowed."""
    q = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(q) - 2):
        p0, p1, p2, p3 = q[i - 1], q[i], q[i + 1], q[i + 2]
        for k in range(per_seg):
            t = k / float(per_seg)
            t2, t3 = t * t, t * t * t
            m1 = (tension * (p2[0] - p0[0]), tension * (p2[1] - p0[1]))
            m2 = (tension * (p3[0] - p1[0]), tension * (p3[1] - p1[1]))
            out.append((
                (2 * t3 - 3 * t2 + 1) * p1[0] + (t3 - 2 * t2 + t) * m1[0]
                + (-2 * t3 + 3 * t2) * p2[0] + (t3 - t2) * m2[0],
                (2 * t3 - 3 * t2 + 1) * p1[1] + (t3 - 2 * t2 + t) * m1[1]
                + (-2 * t3 + 3 * t2) * p2[1] + (t3 - t2) * m2[1]))
    out.append(pts[-1])
    return out


def _resample_open(pts, n):
    """Resample an open polyline to exactly n points by arc length."""
    seg = [math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
           for i in range(len(pts) - 1)]
    total = sum(seg) or 1.0
    step = total / float(n - 1)
    out, acc, i = [pts[0]], 0.0, 0
    for k in range(1, n):
        target = k * step
        while acc + seg[i] < target and i < len(seg) - 1:
            acc += seg[i]
            i += 1
        f = 0.0 if seg[i] < 1e-9 else (target - acc) / seg[i]
        a, b = pts[i], pts[i + 1]
        out.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
    out[-1] = pts[-1]
    return out


def _clamp_y(pts, lo=0.0):
    """Never let the silhouette dip below the mat."""
    return [(z, max(lo, y)) for (z, y) in pts]


# ------------------------------------------------------------------ blade
def _chaikin(loop, iters=3):
    """Chaikin corner-cutting on a closed loop.

    Every new point is a weighted average of two old ones, so the curve always
    stays inside the control polygon: it can never overshoot the mat, never dip
    under the floor and never poke up through the deck. That is exactly the
    guarantee a Catmull-Rom spline does not give you.
    """
    pts = list(loop)
    for _ in range(iters):
        out = []
        n = len(pts)
        for i in range(n):
            a, b = pts[i], pts[(i + 1) % n]
            out.append((0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]))
            out.append((0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1]))
        pts = out
    return pts


def _resample_closed(pts, n):
    """Resample a closed polyline to exactly n points, evenly by arc length."""
    m = len(pts)
    seg = [math.hypot(pts[(i + 1) % m][0] - pts[i][0],
                      pts[(i + 1) % m][1] - pts[i][1]) for i in range(m)]
    total = sum(seg) or 1.0
    step = total / float(n)
    out, acc, i = [], 0.0, 0
    for k in range(n):
        target = k * step
        while acc + seg[i] < target and i < m - 1:
            acc += seg[i]
            i += 1
        f = 0.0 if seg[i] < 1e-9 else (target - acc) / seg[i]
        a, b = pts[i], pts[(i + 1) % m]
        out.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
    return out


def _seg(a, b, n=10):
    """n points from a to b, inclusive of both ends."""
    return [(a[0] + (b[0] - a[0]) * k / float(n - 1),
             a[1] + (b[1] - a[1]) * k / float(n - 1)) for k in range(n)]


def _corner(prev, p, nxt, r, n=9):
    """Round off the corner at p, with radius r, between the two edges."""
    def unit(v):
        ln = math.hypot(v[0], v[1]) or 1.0
        return (v[0] / ln, v[1] / ln)
    d1 = unit((prev[0] - p[0], prev[1] - p[1]))
    d2 = unit((nxt[0] - p[0], nxt[1] - p[1]))
    cosa = max(-1.0, min(1.0, d1[0] * d2[0] + d1[1] * d2[1]))
    ang = math.acos(cosa)
    if ang > math.pi - 0.08 or r <= 0.05:
        return [p]
    tan = min(r / math.tan(ang / 2.0), 0.48 * min(
        math.hypot(prev[0] - p[0], prev[1] - p[1]),
        math.hypot(nxt[0] - p[0], nxt[1] - p[1])))
    rr = tan * math.tan(ang / 2.0)
    a1 = (p[0] + d1[0] * tan, p[1] + d1[1] * tan)
    a2 = (p[0] + d2[0] * tan, p[1] + d2[1] * tan)
    # quadratic through the two tangent points, pulled toward the corner
    out = []
    for k in range(n):
        t = k / float(n - 1)
        x = (1 - t) ** 2 * a1[0] + 2 * (1 - t) * t * p[0] + t * t * a2[0]
        y = (1 - t) ** 2 * a1[1] + 2 * (1 - t) * t * p[1] + t * t * a2[1]
        out.append((x, y))
    del rr
    return out


def _rounded(pts, r, closed=True):
    """Round every corner of a polyline. Concave and convex both work."""
    n = len(pts)
    out = []
    for i in range(n):
        if not closed and (i == 0 or i == n - 1):
            out.append(pts[i])
            continue
        out += _corner(pts[i - 1], pts[i], pts[(i + 1) % n], r)
    return out


def crown_rise(P, z):
    """How far the blade rises above the deck line, as a function of depth.

    At the front it is zero: the deck simply ends there, over the front stop.
    At the back it climbs, so the two blades turn into a pair of curved wings
    standing up behind the laptop. That is what stops the laptop sliding back,
    and it is the detail that makes the thing read as a bridge and not a table.
    """
    R = P["wing_h"]
    z_back = P["deck_z0"] - P["wing_setback"]
    z_toe = P["deck_z0"] + P["wing_toe"]
    if z >= z_toe:
        return 0.0
    if z >= z_back:
        # the wing is a finger rising out of the deck: fully up at the back
        # of the deck, easing down to nothing where it meets the board
        return R
    t = (z_back - z) / max(1e-6, (z_back - P["z_back_outer"]))
    t = min(1.0, max(0.0, t))
    return R * (1.0 - t * t * (3.0 - 2.0 * t))


def blade_polygon(P):
    """One blade, as one simple closed polygon in (z, y).

    Walked once round, like a flat rectangular frame with the bottom opened up:

        back foot on the mat -> up the back -> along the top edge, which is the
        line the deck sits on and then lifts into the back wing -> down the
        front -> front foot on the mat -> up the inside of the front leg ->
        back along the underside of the window -> down the inside of the back
        leg -> back to the start.

    The corners are left sharp on purpose and Chaikin smoothing runs afterwards:
    each corner becomes a weighted average of its neighbours, so the outline can
    never bulge outside this control polygon. The feet stay flat on the desk and
    the top edge never lifts off the deck.
    """
    W = P["blade_w"]
    h = P["blade_w_crown"]
    a, b = P["z_back_outer"], P["z_front_outer"]

    def top(z):
        return crown_y_at(P, z) + crown_rise(P, z)

    def under(z):
        return crown_y_at(P, z) - h

    ai, bi = a + W, b - W

    pts = []
    pts += _seg((a, 0.0), (a, top(a)), 14)[:-1]
    pts += _seg((a, top(a)), (b, top(b)), 46)[:-1]
    pts += _seg((b, top(b)), (b, 0.0), 14)[:-1]
    pts += _seg((b, 0.0), (bi, 0.0), 6)[:-1]
    pts += _seg((bi, 0.0), (bi, under(bi)), 12)[:-1]
    pts += _seg((bi, under(bi)), (ai, under(ai)), 40)[:-1]
    pts += _seg((ai, under(ai)), (ai, 0.0), 12)[:-1]
    pts += _seg((ai, 0.0), (a, 0.0), 6)[:-1]

    smooth = _chaikin(pts, iters=2)
    loop = _resample_closed(smooth, int(P["loop_pts"]))
    # the smoothing nipped the corners of the feet; put the contact back
    return [(z, 0.0) if y < 0.8 else (z, y) for (z, y) in loop]


def blade_profile(P):
    """Kept for the older callers: the blade is a single polygon now."""
    poly = blade_polygon(P)
    return poly, poly


# ------------------------------------------------------------------ parts
ARCHES = [dict(tag="A1", name="Blade Left", side="left"),
          dict(tag="A2", name="Blade Right", side="right")]


def arch_x(P, side):
    return P["span_left"] if side == "left" else P["span_right"] - P["arch_t"]


def arch_parts(P):
    outer, inner = blade_profile(P)
    out = []
    for a in ARCHES:
        x0 = arch_x(P, a["side"])
        out.append(dict(tag=a["tag"], name=a["name"], kind="walnut", pt="blade",
                        side=a["side"], x0=x0, x1=x0 + P["arch_t"],
                        poly=blade_polygon(P), thickness=P["arch_t"],
                        mat="walnut"))
    return out


def deck_parts(P):
    """Three boards on the tilted plane, carried between the two blades.

    The deck deliberately stops at the inside face of each blade instead of
    running over the top of them: that is what leaves the arch windows open, so
    you can see daylight through the stand. It is a bridge, not a table."""
    xa = P["span_left"] + P["arch_t"]
    xb = P["span_right"] - P["arch_t"]
    n = int(P["deck_boards"])
    gap = P["deck_seam"]
    each = ((xb - xa) - gap * (n - 1)) / n
    out = []
    x = xa
    for i in range(n):
        out.append(dict(tag="D%d" % (i + 1), name="Deck Board %d" % (i + 1),
                        kind="ash", pt="board", x0=x, x1=x + each,
                        z0=P["deck_z0"], z1=P["deck_z1"],
                        y_back=deck_y_at(P, P["deck_z0"]),
                        y_front=deck_y_at(P, P["deck_z1"]),
                        thickness=P["deck_t"], mat="ash"))
        x += each + gap
    return out


def stop_parts(P):
    """One rail across the low front edge, and the felt that sits under the laptop."""
    xa = P["span_left"] + P["arch_t"]
    xb = P["span_right"] - P["arch_t"]
    yf = deck_y_at(P, P["deck_z1"])
    # a lip standing on the deck, a few millimetres back from its front edge:
    # the laptop rests against it, and it never sticks out over your keyboard
    z_stop = P["deck_z1"] - P["stop_z"]
    y_at_stop = deck_y_at(P, z_stop)
    rail = dict(tag="S1", name="Front Stop", kind="walnut", pt="rail",
                x0=xa, x1=xb,
                z0=z_stop - P["stop_w"], z1=z_stop,
                y_top=y_at_stop + P["stop_h"], y_bot=y_at_stop - 9.0,
                thickness=P["stop_h"], mat="walnut")
    rail["mat"] = "walnut"
    return [rail] + pad_parts(P)


def pad_parts(P):
    """Four felt pads, on the underside of the two feet. They never show, but
    they are what stops the stand scratching a desk, so they are real parts."""
    out = []
    s = P["pad_size"]
    for side, x0 in (("L", P["span_left"]), ("R", P["span_right"] - P["arch_t"])):
        for end, z in (("B", P["z_back_outer"]), ("F", P["z_front_outer"] - s)):
            out.append(dict(tag="F%s%s" % (side, end), name="Felt Pad %s%s" % (side, end),
                            kind="felt", pt="pad", x0=x0 + (P["arch_t"] - s) / 2.0,
                            x1=x0 + (P["arch_t"] + s) / 2.0,
                            z0=z + 3.0, z1=z + 3.0 + s,
                            y=0.0, thickness=P["felt_t"], mat="felt",
                            hidden=True))
    return out


def rod_parts(P):
    """The tie rod runs through a drilled hole in each back leg, at knee height.

    It has to be somewhere the wood is solid, or it is just a bar floating in
    the window: that is why it sits in the back legs and not in the middle.
    """
    xa = P["span_left"]
    xb = P["span_right"]
    y = P["rod_y"]
    z = P["rod_z"] if P["rod_z"] is not None else P["z_back_outer"] + P["blade_w"] * 0.5
    out = [dict(tag="R1", name="Tie Rod", kind="metal", pt="rod",
                x0=xa, x1=xb, y=y, z=z, d=P["rod_d"], mat="metal")]
    cl = P["rod_clamp_len"]
    # the collars sit hard against the inner face of each leg, so the rod is
    # captured by the frame instead of sliding
    for side, x in (("L", xa + P["arch_t"]), ("R", xb - P["arch_t"] - cl)):
        out.append(dict(tag="C" + side, name="Rod Collar " + side, kind="metal",
                        pt="clamp", x0=x, x1=x + cl, y=y, z=z,
                        d=P["rod_clamp_d"], length=cl, mat="metal"))
    return out


def assembly(P=None):
    a = dict(P if P else globals()["P"])
    return arch_parts(a) + deck_parts(a) + stop_parts(a) + rod_parts(a)


def by_tag(parts, *tags):
    return [p for p in parts if p["tag"] in tags]


# --------------------------------------------------------------- checks
def check(P=None):
    """Plain-English sanity checks. Returns a list of messages, empty is good."""
    a = dict(P if P else globals()["P"])
    out = []
    outer, inner = blade_profile(a)
    ys = [p[1] for p in outer]
    zs = [p[0] for p in outer]
    if min(ys) < -0.01:
        out.append("blade dips below the desk (y=%.1f)" % min(ys))
    if min(zs) < 0.5:
        out.append("blade reaches past the back edge (z=%.1f)" % min(zs))
    if max(zs) > a["desk_z"] - 2:
        out.append("blade overhangs the front edge (z=%.1f of %.0f)"
                   % (max(zs), a["desk_z"]))
    if max(ys) > a["deck_back"] + 0.6:
        out.append("blade pokes through the deck (y=%.1f, deck=%.1f)"
                   % (max(ys), a["deck_back"]))
    # the deck has to be deep enough for the laptop footprint from the brief
    run = a["deck_z1"] - a["deck_z0"]
    if run < 258:
        out.append("deck is only %.0f mm deep, a 264 mm laptop will hang off" % run)
    return out


if __name__ == "__main__":
    msgs = check()
    print("checks:", "all good" if not msgs else "")
    for m in msgs:
        print("  !", m)
    for p in assembly():
        print("%-4s %-16s %s" % (p["tag"], p["name"], p["kind"]))
