"""AeroBridge Studio, product 1 — every parameter and every part in one place.

One dict `P` holds every dimension in millimetres. Every part is described by a
small dict, so the renderer, the Fusion script, the DXF writer and the BOM all
read the same numbers and cannot drift apart.

Coordinates
    X  0 .. 630   left to right across the desk
    Y  0          top of the desk mat, positive is up
    Z  0          back edge of the desk (against the wall), positive toward you
"""
import math

import studio_blade as BL

# ------------------------------------------------------------------ params
P = dict(
    # the desk it stands on, from the brief
    desk_x=630.0, desk_z=280.0, slab_t=18.0, mat_t=3.0,

    # ---- the blade. These are the design.
    blade_t=30.0,            # how deep the board is, front to back
    blade_chamfer=2.6,       # the bevel that runs round every edge
    blade_rake=34.0,         # the leg is set in this far at the crown
    blade_leg_w=76.0,        # square width of each leg. Wider than it needs to be
                             # for strength, because the fin has to carry the slot
    blade_crown_h=26.0,      # wood left between the window and the deck top
    blade_belly=4.0,         # the window's ceiling sags this much in the middle
    blade_knee_r=20.0,       # fillet where a leg meets the crown

    # ---- the fin: the blade rises above the deck at the back into a fin with
    #      a tall slot through it. The two blades stand outside the deck in X,
    #      so they can rise without ever touching the top.
    crest=150.0,             # how far the fin stands above the deck
    crest_end=86.0,          # where it has swept back down to the deck
    crest_peak=44.0,         # the depth at which it is tallest. Further back
                             # than the fin's front edge, so the fin keeps a
                             # broad body instead of tapering to a spike.
    blade_leg_w_fin=66.0,    # the fin needs a wider leg to carry the slot
    fin_slot_on=True,
    fin_z0=28.0, fin_z1=50.0,     # the slot, back..front
    fin_y0=200.0, fin_y1=316.0,   # the slot: tall and narrow, like the fins

    # ---- where the two blades stand
    span_left=96.0, span_right=536.0,

    # ---- the deck: one board on a tilted plane, sunk into the blades
    deck_t=13.0,
    gutter=4.0,              # the recess the deck sits down into. It leaves a
                             # shadow line and a real walnut rim round the panel
    gutter_w=8.0,            # width of that recess
    deck_back=204.0,         # top surface height at the back edge
    deck_front=144.0,        # top surface height at the front edge
    # The deck starts in FRONT of the fins and runs to the front edge. The fins
    # then rise behind it like a backrest: you can see through them, they cradle
    # the back of the laptop, and the two parts never fight for the same space.
    deck_z0=62.0,
    deck_z1=266.0,
    # how far the window's ceiling sits below the deck's underside
    deck_headroom=13.0,
    deck_chamfer=2.4,

    # ---- the front stop: a brass bar, the one accent in the whole thing
    stop_h=9.0, stop_w=11.0, stop_z=26.0,

    # ---- the tie rod, through a drilled hole in each back leg
    rod_d=10.0, rod_y=52.0, rod_z=40.0, rod_clamp_len=26.0, rod_clamp_d=18.0,

    # ---- felt pads under the feet
    felt_t=2.0, pad_size=30.0,
)

BLADE = dict(
    z_back=13.0, z_front=266.0,
    deck_t=0.0,        # the blade crown finishes flush with the deck's top deck_back=204.0, deck_front=144.0,
    deck_z0=6.0, deck_z1=274.0,
    rake=24.0, leg_w=52.0, crown_h=26.0, belly=4.0,
    knee_r=20.0, top_beak=0.0, foot_splay=3.0, loop_pts=260,
)


def blade_params(P=None):
    """The blade's own parameters, pulled from the master dict."""
    p = P or globals()["P"]
    d = dict(BLADE)
    d.update(dict(
        z_back=13.0, z_front=266.0,
        deck_t=p["deck_t"], deck_back=p["deck_back"], deck_front=p["deck_front"],
        deck_z0=p["deck_z0"], deck_z1=p["deck_z1"],
        rake=p["blade_rake"], leg_w=p["blade_leg_w"],
        crown_h=p["blade_crown_h"], belly=p["blade_belly"],
        knee_r=p["blade_knee_r"], loop_pts=260,
        crest=p["crest"], crest_end=p["crest_end"], crest_peak=p["crest_peak"],
        fin_win=p["fin_slot_on"],
        fin_z0=p["fin_z0"], fin_z1=p["fin_z1"],
        fin_y0=p["fin_y0"], fin_y1=p["fin_y1"],
    ))
    return d


def R_INSET(loop, d):
    """A closed loop pulled `d` inward, used to describe the deck's recess."""
    n = len(loop)
    area = sum(loop[i][0] * loop[(i + 1) % n][1] - loop[(i + 1) % n][0] * loop[i][1]
               for i in range(n))
    cw = area < 0
    out = []
    for i in range(n):
        p, c, q = loop[(i - 1) % n], loop[i], loop[(i + 1) % n]
        e1 = _unit2(c[0] - p[0], c[1] - p[1])
        e2 = _unit2(q[0] - c[0], q[1] - c[1])
        n1 = (e1[1], -e1[0]) if cw else (-e1[1], e1[0])
        n2 = (e2[1], -e2[0]) if cw else (-e2[1], e2[0])
        dot = max(-1.0, min(1.0, n1[0] * n2[0] + n1[1] * n2[1]))
        den = 1.0 + dot
        if den < 0.3:
            mx, my = n1
        else:
            mx, my = (n1[0] + n2[0]) / den, (n1[1] + n2[1]) / den
            ln = math.hypot(mx, my) or 1.0
            if ln > 2.6:
                mx, my, ln = mx / ln, my / ln, 2.6
        out.append((c[0] + mx * d, c[1] + my * d))
    return out


def _unit2(x, y):
    ln = math.hypot(x, y) or 1.0
    return x / ln, y / ln


# ------------------------------------------------------------------ helpers
def deck_y_at(P, z):
    """Height of the deck's top surface at depth z."""
    z = min(max(z, P["deck_z0"]), P["deck_z1"])
    t = (z - P["deck_z0"]) / (P["deck_z1"] - P["deck_z0"])
    return P["deck_back"] + (P["deck_front"] - P["deck_back"]) * t


def crown_y_at(P, z):
    """Height of the blade's top edge.

    This is the deck's TOP surface, not its underside: the deck is housed into
    the blades, so the two finish flush. That is what turns the top into a pale
    panel inside a dark frame instead of a board sitting on a table.
    """
    return deck_y_at(P, z)


# ------------------------------------------------------------------ parts
ARCHES = [dict(tag="A1", name="Blade Left", side="left"),
          dict(tag="A2", name="Blade Right", side="right")]


def arch_x(P, side):
    return P["span_left"] if side == "left" else P["span_right"] - P["blade_t"]


def arch_parts(P):
    """The two blades. Solid walnut, chamfered on every edge, faced the same way."""
    bp = blade_params(P)
    poly = BL.blade_polygon(bp)
    slot = BL.fin_slot(bp) if P["fin_slot_on"] else None
    out = []
    for a in ARCHES:
        x0 = arch_x(P, a["side"])
        out.append(dict(tag=a["tag"], name=a["name"], kind="walnut", pt="blade",
                        side=a["side"], x0=x0, x1=x0 + P["blade_t"],
                        poly=poly, slot=slot, thickness=P["blade_t"],
                        chamfer=P["blade_chamfer"], mat="walnut"))
    return out


def deck_parts(P):
    """One board, carried between the blades, with a chamfer round the edge.

    The deck lands on both blade crowns and stops short of the outside face, so
    a slim band of dark walnut frames the pale ash from above. That frame is the
    whole reason the top does not read as a table.
    """
    # it drops in between the blades and lands on the crowns
    xa = P["span_left"] + P["blade_t"]
    xb = P["span_right"] - P["blade_t"]
    z0, z1 = P["deck_z0"], P["deck_z1"]
    return [dict(tag="D1", name="Deck", kind="ash", pt="board",
                 x0=xa, x1=xb, z0=z0, z1=z1,
                 y_back=deck_y_at(P, z0) - P["gutter"],
                 y_front=deck_y_at(P, z1) - P["gutter"],
                 thickness=P["deck_t"], chamfer=P["deck_chamfer"],
                 corner=34.0,
                 mat="ash")]


def stop_parts(P):
    """The front stop: a brass bar inset into the deck, near the low edge.

    Brass, not walnut, and not on the very edge: set in from the edge it reads
    as a detail rather than a lip, and the single warm metal note is what stops
    an all-wood object looking like a shop-class project.
    """
    xa = P["span_left"] + P["blade_t"] + 26.0
    xb = P["span_right"] - P["blade_t"] - 26.0
    z = P["deck_z1"] - P["stop_z"]
    y = deck_y_at(P, z)
    return [dict(tag="S1", name="Front Stop", kind="brass", pt="rail",
                 x0=xa, x1=xb, z0=z - P["stop_w"] / 2.0, z1=z + P["stop_w"] / 2.0,
                 y_top=y + P["stop_h"], y_bot=y - 6.0,
                 thickness=P["stop_h"], mat="brass")]


def rod_parts(P):
    """The tie rod, through a drilled hole in each back leg, with two collars."""
    z = P["rod_z"]
    out = [dict(tag="R1", name="Tie Rod", kind="metal", pt="rod",
                x0=P["span_left"], x1=P["span_right"],
                y=P["rod_y"], z=z, d=P["rod_d"], mat="metal")]
    cl = P["rod_clamp_len"]
    for side, x in (("L", P["span_left"] + P["blade_t"]),
                    ("R", P["span_right"] - P["blade_t"] - cl)):
        out.append(dict(tag="C" + side, name="Rod Collar " + side, kind="metal",
                        pt="clamp", x0=x, x1=x + cl, y=P["rod_y"], z=z,
                        d=P["rod_clamp_d"], length=cl, mat="metal"))
    return out


def pad_parts(P):
    """Four felt pads under the feet. Hidden, but real, and they are why the
    stand does not scratch a desk."""
    out = []
    s = P["pad_size"]
    for side, x0 in (("L", P["span_left"]), ("R", P["span_right"] - P["blade_t"])):
        for end, z in (("B", 20.0), ("F", 246.0 - s)):
            out.append(dict(tag="F%s%s" % (side, end), name="Felt Pad %s%s" % (side, end),
                            kind="felt", pt="pad",
                            x0=x0 + (P["blade_t"] - s) / 2.0,
                            x1=x0 + (P["blade_t"] + s) / 2.0,
                            z0=z, z1=z + s, y=0.0,
                            thickness=P["felt_t"], mat="felt", hidden=True))
    return out


def assembly(P=None):
    a = dict(P if P else globals()["P"])
    return arch_parts(a) + deck_parts(a) + stop_parts(a) + rod_parts(a) + pad_parts(a)


def by_tag(parts, *tags):
    return [p for p in parts if p["tag"] in tags]


# --------------------------------------------------------------- checks
def _inside(pt, loop):
    """Point-in-polygon, used only by the checks."""
    x, y = pt
    c = False
    n = len(loop)
    for i in range(n):
        x1, y1 = loop[i]
        x2, y2 = loop[(i + 1) % n]
        if ((y1 > y) != (y2 > y)) and (x < (x2 - x1) * (y - y1) / (y2 - y1) + x1):
            c = not c
    return c


def check(P=None):
    """Plain-English sanity checks. Returns messages; empty means good."""
    a = dict(P if P else globals()["P"])
    out = []
    poly = BL.blade_polygon(blade_params(a))

    ys = [p[1] for p in poly]
    zs = [p[0] for p in poly]
    if min(ys) < -0.01:
        out.append("blade dips below the desk (y=%.1f)" % min(ys))
    if min(zs) < 0.5:
        out.append("blade reaches past the back edge (z=%.1f)" % min(zs))
    if max(zs) > a["desk_z"] - 2:
        out.append("blade overhangs the front edge (z=%.1f of %.0f)"
                   % (max(zs), a["desk_z"]))
    # The deck beds onto the blade wherever the deck runs. The fin is meant to
    # stand tall behind it, but it must also land back ON the deck line at
    # crest_end, or the blade is a floating wedge.
    over = [(z, y) for (z, y) in poly if z >= a["crest_end"]]
    if over:
        gap = min(crown_y_at(a, z) - y for (z, y) in over)
        if gap < -0.6:
            out.append("blade pokes up through the deck by %.1f mm" % -gap)
        if gap > 1.0:
            out.append("the deck does not sit down on the blade (%.1f mm gap)" % gap)

    if a["fin_slot_on"]:
        sbp = blade_params(a)
        slot = BL.fin_slot(sbp)
        poly2 = BL.blade_polygon(sbp)
        for (z, y) in slot:
            if not _inside((z, y), poly2):
                out.append("the slot breaks out through the side of the fin")
                break
        m = min(min(math.hypot(p[0] - q[0], p[1] - q[1]) for q in poly2) for p in slot)
        if m < 10.0:
            out.append("only %.0f mm of wood round the slot; keep at least 10" % m)

    run = a["deck_z1"] - a["deck_z0"]
    if run < 188:
        out.append("deck is only %.0f mm deep; it needs at least 188" % run)

    z_rod = a["rod_z"]
    if a["rod_y"] + a["rod_d"] / 2.0 > crown_y_at(a, z_rod):
        out.append("the tie rod misses solid wood where it enters the leg")

    if a["span_right"] <= a["span_left"]:
        out.append("the two blades are in the wrong order")
    if not (0 <= a["span_left"] and a["span_right"] <= a["desk_x"]):
        out.append("a blade stands off the end of the desk")

    # the deck must clear a laptop's own thickness over a keyboard
    if crown_y_at(a, a["deck_z1"]) < 60:
        out.append("the front of the deck is too low to clear a keyboard")
    return out


if __name__ == "__main__":
    msgs = check()
    print("checks:", "all good" if not msgs else "")
    for m in msgs:
        print("  !", m)
    for p in assembly():
        print("%-4s %-16s %-8s %s" % (p["tag"], p["name"], p["kind"], p["pt"]))
