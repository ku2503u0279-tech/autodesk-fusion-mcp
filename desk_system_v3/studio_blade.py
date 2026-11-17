"""The blade, built from lines and tangent-continuous arcs.

The shape is one closed C. Every junction between a straight run and a curve
is filleted with a quadratic that shares its tangent with both sides, which
means the outline is smooth by construction. That matters: earlier attempts
smoothed a sharp polygon after the fact, and the smoothing pulled spikes out of
the corners. If the curve is right when it is built, nothing needs fixing later.

    outside, floor to floor:  back foot -> up the back leg -> fillet -> crown
                              -> fillet -> down the front leg -> front foot
    inside, floor to floor:   front foot -> up the inside front leg -> fillet
                              -> swept belly -> fillet -> down the inside back
                              leg -> back foot

The crown is a dead-straight line on the underside of the deck, because that is
what the deck beds onto. The blade leans back at the top (the "beak") so it
looks like it is holding the deck rather than propping it up.
"""
import math

DEFAULTS = dict(
    z_back=13.0,
    z_front=266.0,
    deck_t=12.0,
    deck_back=204.0,
    deck_front=144.0,
    deck_z0=13.0,
    deck_z1=274.0,
    # the design
    rake=24.0,          # how far the leg is set in at the crown vs the foot
    leg_w=52.0,         # square width of each leg (constant, so it reads solid)
    crown_h=26.0,       # wood left between the window and the deck
    belly=4.0,          # how far the window's ceiling sags under the middle
    top_beak=0.0,       # >0 breaks the top edge forward; 0 keeps it crisp
    foot_splay=3.0,     # the foot runs a little wider than the leg
    knee_r=20.0,        # radius where a leg meets the crown: crisp, not bulbous
    crest=150.0,        # how far the fin rises above the deck at the back
    crest_end=86.0,     # depth at which it sweeps back down to the deck line
    crest_peak=44.0,    # where the fin is at its highest
    # The slot through the fin. This is the piece's signature: the fin is not a
    # solid wedge, it is a tall opening with a curved head, so you see through
    # the back of the stand to the wall behind. It also takes a lot of weight
    # out of what would otherwise be a heavy block.
    fin_win=True,
    fin_z0=32.0,
    fin_z1=88.0,
    fin_y0=44.0,
    fin_y1=194.0,
    fin_head=0.07,      # how much the arched head lifts in the middle
    loop_pts=260,
    thickness=28.0,     # how deep the blade is, front to back of the board
    chamfer=3.0,        # the small bevel round every edge
)


# ------------------------------------------------------------------ maths
def _lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def line(a, b, n=12, skip_last=False, skip_first=False):
    out = [_lerp(a, b, k / float(n - 1)) for k in range(n - (1 if skip_last else 0))]
    return out[1:] if skip_first else out


def quad(p0, p1, p2, n=16, skip_first=False):
    """Quadratic Bezier. Its tangent at p0 points at p1 and at p2 points from p1."""
    out = []
    for k in range(n):
        t = k / float(n - 1)
        a, b, c = (1 - t) ** 2, 2 * (1 - t) * t, t * t
        out.append((a * p0[0] + b * p1[0] + c * p2[0],
                    a * p0[1] + b * p1[1] + c * p2[1]))
    return out[1:] if skip_first else out


def _unit(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    ln = math.hypot(dx, dy) or 1.0
    return dx / ln, dy / ln


def fillet(p_prev, p_corner, p_next, radius, n=14):
    """A quadratic arc that meets both incoming and outgoing edges tangentially.

    Returns the arc from the point where it leaves the incoming edge to where it
    joins the outgoing one. Because it is tangent to both, joining it to the
    straight runs leaves no kink and no spike.
    """
    d1 = _unit(p_prev, p_corner)
    d2 = _unit(p_corner, p_next)
    # distance to pull back from the corner, capped by both edge lengths
    t1 = min(radius, 0.45 * math.hypot(p_corner[0] - p_prev[0], p_corner[1] - p_prev[1]))
    t2 = min(radius, 0.45 * math.hypot(p_next[0] - p_corner[0], p_next[1] - p_corner[1]))
    a = (p_corner[0] - d1[0] * t1, p_corner[1] - d1[1] * t1)
    b = (p_corner[0] + d2[0] * t2, p_corner[1] + d2[1] * t2)
    return a, quad(a, p_corner, b, n), b


def fin_slot(P=None):
    """The tall opening through the fin: a rectangle with an arched head.

    Straight sides, a flat-ish foot and a gently arched top. It repeats the
    arch of the main window at a smaller scale, which is what makes the two
    openings read as a family rather than as holes.
    """
    Q = dict(DEFAULTS)
    if P:
        Q.update({k: v for k, v in P.items() if k in DEFAULTS})
    z0, z1 = Q["fin_z0"], Q["fin_z1"]
    y0, y1 = Q["fin_y0"], Q["fin_y1"]
    head = Q["fin_head"] * (y1 - y0)
    n, m = 14, 20
    out = []
    for k in range(n):                      # left edge, rising
        t = k / float(n - 1)
        out.append((z0 - 1.4 * math.sin(math.pi * t), y0 + (y1 - y0 - head) * t))
    for k in range(m):                      # arched head
        t = k / float(m - 1)
        out.append((z0 + (z1 - z0) * t,
                    y1 - head + head * math.sin(math.pi * t)))
    for k in range(n):                      # right edge, falling
        t = 1.0 - k / float(n - 1)
        out.append((z1 + 1.4 * math.sin(math.pi * t), y0 + (y1 - y0 - head) * t))
    for k in range(m):                      # foot, slightly bowed
        t = 1.0 - k / float(m - 1)
        out.append((z0 + (z1 - z0) * t, y0 - 2.0 * math.sin(math.pi * t)))
    return out


def lens(z0, z1, y0, y1, bow=0.06, taper=0.30, n=22):
    """A lens-shaped window: straight-ish bottom, tapered top.

    Windows like this are everywhere in mid-century casework, and they read as
    designed rather than punched. Both edges are curved, which also means the
    opening looks different from every angle you walk past it.
    """
    out = []
    for k in range(n):
        t = k / float(n - 1)
        z = z0 + (z1 - z0) * t
        mid = abs(0.5 - t) * 2.0
        out.append((z, y0 + (y1 - y0) * bow * mid))
    for k in range(n):
        t = 1.0 - k / float(n - 1)
        z = z0 + (z1 - z0) * t
        mid = abs(0.5 - t) * 2.0
        out.append((z, y1 - (y1 - y0) * taper * mid ** 1.5))
    return out


def resample_closed(loop, n):
    m = len(loop)
    seg = [math.hypot(loop[(i + 1) % m][0] - loop[i][0],
                      loop[(i + 1) % m][1] - loop[i][1]) for i in range(m)]
    total = sum(seg) or 1.0
    step = total / float(n)
    out, acc, i = [], 0.0, 0
    for k in range(n):
        target = k * step
        while acc + seg[i] < target and i < m - 1:
            acc += seg[i]
            i += 1
        f = 0.0 if seg[i] < 1e-9 else (target - acc) / seg[i]
        a, b = loop[i], loop[(i + 1) % m]
        out.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
    return out


# ------------------------------------------------------------- the shape
def _deck_y(z, P):
    z = min(max(z, P["deck_z0"]), P["deck_z1"])
    t = (z - P["deck_z0"]) / (P["deck_z1"] - P["deck_z0"])
    return P["deck_back"] + (P["deck_front"] - P["deck_back"]) * t


def _crown_y(z, P):
    return _deck_y(z, P) - P["deck_t"]


def _top_y(z, P):
    """The blade's top edge: the deck line, plus the fin behind it.

    The two blades stand outside the deck in X, so they are free to rise above
    it without touching it. The fin is built as a SAIL: full height from the
    back edge to `crest_peak`, then a tangent sweep down onto the deck line at
    `crest_end`. A plain power-law taper over a short run reads as a spike;
    this holds a tall, broad body first, which is what makes the pierce read.
    """
    base = _deck_y(z, P)     # the deck's TOP surface: the blade finishes flush
    h, end, peak = P["crest"], P["crest_end"], P["crest_peak"]
    zb = P["z_back"]
    if h <= 0.5 or z >= end:
        return base
    if z <= peak:
        # a whisper of rake so the leading edge is not a dead vertical
        t = (z - zb) / max(1e-6, (peak - zb))
        shape = 0.90 + 0.10 * min(1.0, max(0.0, t))
    else:
        # smoothstep: zero slope where it leaves the sail AND where it lands,
        # so the fin meets the deck without a kink in either direction
        u = (end - z) / max(1e-6, (end - peak))
        u = min(1.0, max(0.0, u))
        shape = u * u * (3.0 - 2.0 * u)
    return base + h * shape


def blade_polygon(P=None):
    """One blade as a closed (z, y) polygon, anticlockwise, feet on the mat."""
    Q = dict(DEFAULTS)
    if P:
        Q.update({k: v for k, v in P.items() if k in DEFAULTS})
    zb, zf = Q["z_back"], Q["z_front"]
    rake, lw = Q["rake"], Q["leg_w"]
    crown_h, belly = Q["crown_h"], Q["belly"]
    beak, splay, kr = Q["top_beak"], Q["foot_splay"], Q["knee_r"]

    def seat(z):
        """The blade's top edge, including the crest."""
        return _top_y(z, Q)

    # outside faces of the two legs, measured at the crowned top
    at, bt = zb + rake, zf - rake
    # inside faces: a constant square width, so a leg reads the same all the way
    ai, bi = at + lw, bt - lw
    # at the floor the inside face sits further out, keeping the leg square
    ai0, bi0 = ai - rake * 0.60, bi + rake * 0.60

    pts = []

    # --- outside of the back leg, splayed foot up to the crown
    foot_a = (zb - splay, 0.0)
    pts += line(foot_a, (zb - splay * 0.2, 16.0), 3)
    # The back leg runs the full height of the fin, then turns forward into the
    # top edge. The turn is a real arc, so the tip of the fin is a crescent.
    tip_r = min(kr * 2.2, (seat(at) - seat(bt)) * 0.85)
    tip_c = (at + tip_r * 0.15, seat(at) - tip_r * 0.9)
    for k in range(1, 15):
        t = math.pi * 0.92 - (math.pi * 0.46) * (k - 1) / 13.0
        pts.append((tip_c[0] + tip_r * math.cos(t) * 0.85,
                    tip_c[1] + tip_r * math.sin(t)))
    p1 = pts[-1]

    # --- THE TOP EDGE. One continuous run from the fin's shoulder all the way
    #     to where the front leg begins, following the seat line exactly. This
    #     single loop is what guarantees the deck has something to sit on: it is
    #     not approximated by an arc or a chord anywhere along the front.
    z_a, z_b = p1[0], zf - splay
    steps = 54
    for k in range(1, steps + 1):
        z = z_a + (z_b - z_a) * k / steps
        pts.append((z, seat(z)))

    # --- the front shoulder. The top edge ends at the very front of the board,
    #     then ONE tangent arc turns from heading forward into heading down the
    #     outside of the front leg. Built as a single quadratic, so it cannot
    #     loop back on itself: an earlier three-point fillet here doubled back
    #     and left the outline self-intersecting.
    top_end = (z_b, seat(z_b))
    p1b = top_end
    drop = min(74.0, seat(z_b) * 0.42)
    leg_y = seat(z_b) - drop
    ctrl = (z_b + 12.0, seat(z_b) - drop * 0.62)
    leg_top = (zf + splay * 0.55, leg_y)
    pts += quad(p1b, ctrl, leg_top, 14, skip_first=True)

    foot_b = (zf + splay, 0.0)
    leg_top_b = leg_top
    if beak > 0.5:
        break_pt = (p1b[0] + beak * 0.55, p1b[1] - beak * 0.75)
        pts += quad(p1b, (p1b[0] + beak * 0.2, p1b[1] - beak * 0.08), break_pt, 8,
                    skip_first=True)
        leg_top_b = _lerp(break_pt, foot_b, 0.16)
    # a gentle S down the outside of the front leg: the leg bows in slightly
    # under the crown, then straightens to the foot
    pts += quad(p1b, (bt + (foot_b[0] - bt) * 0.55, p1b[1] * 0.44),
                leg_top_b, 14, skip_first=True)
    pts += line(leg_top_b, (zf + splay * 0.3, 14.0), 12, skip_last=True)
    pts += line((zf + splay * 0.3, 14.0), foot_b, 3, skip_last=True)

    # --- across the front foot (this is the contact patch)
    pts += line((zf + splay, 0.0), (bi0, 0.0), 7, skip_last=True)

    # --- inside of the front leg. It is the outside mirrored, so the leg keeps
    #     the same square width from the floor all the way up.
    # the ceiling of the window follows the crest, so the fin stays a band and
    # not a solid block: wood thickens toward the back, exactly as it should
    inner_top_b = (bi, seat(bi) - crown_h)
    dx_in = inner_top_b[0] - bi0
    pts += line((bi0, 0.0), (bi0 + dx_in * 0.12, 16.0), 3, skip_last=True)
    # a near-straight climb, then a tight turn into the window's ceiling
    pts += line((bi0 + dx_in * 0.12, 16.0), (inner_top_b[0] - dx_in * 0.06,
                                             inner_top_b[1] - 46.0), 13, skip_first=True)
    pts += quad((inner_top_b[0] - dx_in * 0.06, inner_top_b[1] - 46.0),
                (inner_top_b[0] - dx_in * 0.01, inner_top_b[1] - 6.0),
                inner_top_b, 8, skip_first=True)

    # --- inside of the crown: one long sweep that sags under the middle
    mid_z = (ai + bi) * 0.5
    sag = (mid_z, seat(mid_z) - crown_h - belly)
    pts += quad(inner_top_b,
                (bi + (mid_z - bi) * 0.55, seat(bi + (mid_z - bi) * 0.55) - crown_h - belly * 0.45),
                sag, 12, skip_first=True)
    inner_top_a = (ai, seat(ai) - crown_h)
    pts += quad(sag,
                (ai - (ai - mid_z) * 0.55, seat(ai - (ai - mid_z) * 0.55) - crown_h - belly * 0.45),
                inner_top_a, 12, skip_first=True)

    # --- inside of the back leg, back down to the foot
    dx_in = inner_top_a[0] - ai0
    pts += quad(inner_top_a,
                (inner_top_a[0] + dx_in * 0.01, inner_top_a[1] - 6.0),
                (inner_top_a[0] + dx_in * 0.06, inner_top_a[1] - 46.0), 8, skip_first=True)
    pts += line((inner_top_a[0] + dx_in * 0.06, inner_top_a[1] - 46.0),
                (ai0 + dx_in * 0.12, 16.0), 13, skip_first=True)
    pts += line((ai0 + dx_in * 0.12, 16.0), (ai0, 0.0), 3, skip_first=True)

    # --- back foot, closing the loop
    pts += line((ai0, 0.0), foot_a, 7, skip_last=True)

    pts = [(z, max(0.0, y)) for (z, y) in pts]
    return resample_closed(pts, int(Q["loop_pts"]))


def blade_loops(P=None):
    """Kept for callers that want (outer, inner). The blade is one outline."""
    poly = blade_polygon(P)
    return poly, poly
