"""DraftShelf — the assembly. The single source of truth for every solid.

Every solid comes from params.py. Renders, STLs and the Fusion script all read
this module, so there is exactly one set of numbers in the product.

Coordinates: Y is up, X runs across the desk with -X on your left, Z runs front
to back with +Z pointing AWAY from you.

    PYTHONPATH=..:.. ../../.venv/bin/python build.py
"""
import math

import studio3d as R
import params as PR

ROD_R = PR.ROD_R
SHELF_T, SHELF_D, SHELF_W = PR.SHELF_T, PR.SHELF_D, PR.SHELF_W
C = PR.COMB
SHELF_Y = PR.SHELF_Y
Z0 = -(PR.N_RODS - 1) * PR.PITCH / 2.0
Z1 = (PR.N_RODS - 1) * PR.PITCH / 2.0


# ------------------------------------------------------------------- J01 comb
def comb_outline(zc):
    """J01's outline in (z, y): a solid web with six U-cradles in its top edge.

    Walk it anticlockwise from the front-bottom corner: up the front face,
    then east along the top edge cutting a U for each dowel, then down the back
    face and back along the base. Each U is a half-circle of radius R11.2 whose
    centre sits at top - R, so the lips of the U come up exactly to the top
    edge and each tooth between two cradles is the 16 mm gap that is left
    between two 22 mm dowels on a 38 mm pitch.
    """
    t = C["top"]
    r = C["scallop"]
    yc = t - r                      # centre height of the scallop arcs
    half = C["w"] / 2.0
    zs = [zc + (k - (PR.N_RODS - 1) / 2.0) * PR.PITCH
          for k in range(PR.N_RODS)]
    base = C["pad_dep"]          # the comb stands on its pad, not on the desk
    pts = [(zc - half, base), (zc - half, t)]
    for k, z in enumerate(zs):
        # the U: from this cradle's front lip, round the bottom, to its back
        # lip. pi -> 2*pi sweeps BELOW the centre line, which is the half of
        # the circle that is the cradle. Sweeping a full turn (which is what
        # this did at first) runs the edge 11 mm back up past the lip and off
        # the end of the part.
        for j in range(0, 33):
            a = math.pi + math.pi * j / 32.0
            pts.append((z + r * math.cos(a), yc + r * math.sin(a)))
        # the tooth: flat along the top edge to the next cradle's front lip
        if k < len(zs) - 1:
            pts.append((zs[k + 1] - r, t))
    pts.append((zc + half, t))
    pts.append((zc + half, base))
    return pts


def _clean(p):
    out = [p[0]]
    for q in p[1:]:
        if math.hypot(q[0] - out[-1][0], q[1] - out[-1][1]) > 1e-7:
            out.append(q)
    return out


def comb_window(zc, r=26.0):
    """The opening through J01.

    Without this the comb is a 228 x 111 solid slab, which is both ugly and
    wrong: it closes the space the keyboard lives in. Cut this out and what is
    left is a scalloped rail on two slim legs, with the machine work visible
    from the front and the six dowels reading as one dark line above it.
    """
    # The window's straight edges must not land on a point of the scallop arcs.
    # At +/-92 the top corners sat exactly on the cradle arcs and left 22
    # T-junctions in the cap triangulation; -88.4 / +88.4 is 22.8 mm clear of
    # the nearest scallop lip at 114 and keeps the legs symmetric.
    z0, z1 = zc - 88.4, zc + 88.4
    # The window's top edge has to stay clear of the cradle arcs. At 10 mm below
    # the cradle floor it passed 0.16 mm from a scallop and earcut collapsed the
    # sliver, dropping six boundary vertices and leaving 26 loose edges in the
    # STL. 24 mm below the floor is 14 mm of real clearance.
    y0, y1 = C["pad_dep"] + 5.0, C["top"] - C["scallop"] - 24.0
    pts = []
    def arc(cx, cy, a0, a1, n=10):
        for k in range(n + 1):
            a = a0 + (a1 - a0) * k / n
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    arc(z0 + r, y0 + r, math.pi, 1.5 * math.pi)
    arc(z1 - r, y0 + r, 1.5 * math.pi, 2 * math.pi)
    arc(z1 - r, y1 - r, 0.0, 0.5 * math.pi)
    arc(z0 + r, y1 - r, 0.5 * math.pi, math.pi)
    return _clean(pts)


def comb(x, mat="metal"):
    """J01: one solid, swept along X, with the scallops cut into its top edge
    and a window through the middle.

    The outline is reversed before it goes in. Walked front-to-back and then
    down the back face it comes out CLOCKWISE, and prism_with_hole only
    normalises the winding of the rings it skins, not the winding it hands to
    the cap triangulator. A clockwise outline made earcut produce
    inside-out caps: the skin looked right and the part had 1002 loose edges in
    the STL.
    """
    prof = _clean(comb_outline(0.0))[::-1]
    hole = comb_window(0.0)
    return R.prism_with_hole(prof, hole, x - C["t"] / 2.0, x + C["t"] / 2.0,
                             plane="x", mat=mat, chamfer=0.6)


# ------------------------------------------------------------------- the raft
def dowel(z, mat="ash"):
    """R01: one 22 mm ash dowel, running across the desk."""
    r = ROD_R
    ring = lambda x: [(x, r * math.cos(2 * math.pi * k / 36.0) + SHELF_Y - r,
                       z + r * math.sin(2 * math.pi * k / 36.0))
                      for k in range(36)]
    return R.loft([ring(PR.ROD_X0), ring(PR.ROD_X1)], mat=mat)


def cap(x, z, mat="brass"):
    """C01: a turned brass plug let INTO the end of the dowel.

    It runs from x = x_end - depth to x = x_end - 0.15, i.e. it stops 0.15 mm
    SHORT of the sawn end face. That recess is deliberate: a plug flush with the
    dowel end leaves two coplanar discs at exactly the same plane, the depth
    buffer has no answer for it, and the render shows a sawtooth fringe of ash
    and brass where the dowel meets the cap. Sunk 0.15 it reads as flush and
    there is nothing to fight.
    """
    r = ROD_R - 0.15
    ring = lambda xx: [(xx, SHELF_Y - ROD_R + r * math.cos(2 * math.pi * k / 32.0),
                        z + r * math.sin(2 * math.pi * k / 32.0))
                       for k in range(32)]
    return R.loft([ring(x), ring(x + 6.0)], mat=mat)


def shelf(mat="ash"):
    """S01. It sits 0.3 mm ABOVE the comb teeth, not on them.

    That 0.3 is not sloppiness, it is the fix for a render bug that was pointing
    at a real modelling problem: the board's underside and the comb's tooth tops
    were both at exactly y = 111.00, 228 mm of perfectly coplanar surface. The
    depth buffer has no way to order two surfaces at the same depth, so the
    front view showed a sawtooth fringe of ash and aluminium along the whole
    top edge. Two surfaces that are meant to touch need a gap or an overlap, and
    a 0.3 mm shim of rubber is what a real cabinetmaker would put there anyway.
    """
    return R.slab(-SHELF_W / 2.0, SHELF_W / 2.0, -SHELF_D / 2.0, SHELF_D / 2.0,
                  SHELF_Y + 0.3, SHELF_Y + 0.3 + SHELF_T, SHELF_T, mat=mat)


def pad(x, mat="felt"):
    """F01: a TPU pad let into the comb's base."""
    w = C["w"] / 2.0
    # slab() puts the board BELOW y_back/y_front, so the pad's top is
    # pad_dep and the board hangs down to 0: onto the desk, flush with the
    # comb's recessed base.
    return R.slab(x - C["t"] / 2.0 + 8.0, x + C["t"] / 2.0 - 8.0,
                  -w + 10.0, w - 10.0, PR.COMB["pad_dep"], PR.COMB["pad_dep"],
                  PR.COMB["pad_dep"], mat=mat)


def scene():
    ms = []
    for x in PR.LEG_XS:
        ms.append(comb(x))
        ms.append(pad(x))
    for z in PR.rod_zs():
        ms.append(dowel(z))
        # Each plug is 6 long and stops 1.2 mm short of the sawn end face, so
        # 4.8 mm of it is buried and 1.2 mm stands proud as the brass disc you
        # see. Sunk flush it vanished, because the dowel's own end cap covered
        # it: the plug has to lead the sawn face to be visible at all.
        ms.append(cap(PR.ROD_X0 - 1.2, z))
        ms.append(cap(PR.ROD_X1 - 4.8, z))
    ms.append(shelf())
    return ms


def main():
    ms = scene()
    pts = R.scene_points(ms)
    print("solids %d" % len(ms))
    print("x %.0f..%.0f  y %.0f..%.0f  z %.0f..%.0f"
          % (pts[:, 0].min(), pts[:, 0].max(),
             pts[:, 1].min(), pts[:, 1].max(),
             pts[:, 2].min(), pts[:, 2].max()))
    for k, v in PR.summary().items():
        print("  %-11s %s" % (k, v))


if __name__ == "__main__":
    main()
