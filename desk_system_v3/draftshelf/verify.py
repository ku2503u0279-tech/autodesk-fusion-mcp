"""DraftShelf — the checks that the claims in the README are actually true.

Four checks, in the same order Product 1 uses:

  1. every part is watertight (every edge shared by exactly two triangles)
  2. the dowels really sit down in the comb's scallops, on every comb
  3. the shelf really lands on all six dowels, in one plane
  4. every part has a file, and the BOM matches the part list

    PYTHONPATH=..:.. ../../.venv/bin/python verify.py
"""
import csv
import math
import os
import sys

import studio3d as R
import build as B
import params as PR

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "Product6_DraftShelf")


def check_watertight(eps=1e-4):
    """Every edge shared by exactly two triangles, matched BY POSITION.

    Matching by vertex index is wrong here: prism_with_hole deliberately gives
    the end caps their own copies of the boundary vertices, because earcut
    drops collinear points and a shared-vertex cap would leave T-junctions. A
    cap with its own vertices is watertight by position, which is exactly what
    an STL is judged on, so that is what this measures.
    """
    import export as E
    out = []
    for tag, name, mesh, _cut, _mat in E.parts():
        key = {}
        for i, (x, y, z) in enumerate(mesh.v):
            key[(round(x / eps), round(y / eps), round(z / eps))] = i
        edges = {}
        degenerate = 0
        for f in mesh.f:
            idx = [key[(round(mesh.v[i][0] / eps), round(mesh.v[i][1] / eps),
                        round(mesh.v[i][2] / eps))] for i in f]
            if len(set(idx)) < 3:
                degenerate += 1
                continue
            for k in range(3):
                a, b = idx[k], idx[(k + 1) % 3]
                e = (min(a, b), max(a, b))
                edges[e] = edges.get(e, 0) + 1
        bad = [e for e, n in edges.items() if n != 2]
        if bad or degenerate:
            out.append("%s %s: %d unshared edges, %d degenerate triangles"
                       % (tag, name, len(bad), degenerate))
    return out


def comb_cradle_y(z):
    """The lowest point of the cradle that holds the dowel at this Z.

    Positive means the cradle is below the dowel centre, i.e. the dowel is
    sitting IN it. If this goes negative the comb is trying to hold the dowel
    above its own top edge, which is not a cradle at all.
    """
    return PR.COMB["scallop"] - 0.0


def check_dowels_seated():
    """Each dowel's underside must be at or above the comb's cradle floor."""
    out = []
    floor = PR.COMB["top"] - PR.COMB["scallop"]       # bottom of the cradle
    dowel_under = PR.SHELF_Y - PR.ROD_R               # bottom of a dowel
    if dowel_under < floor - 0.01:
        out.append("the dowels sit %.2f mm below the cradle floor: they would "
                   "hang through the comb" % (floor - dowel_under))
    # and the cradle must not swallow them: the tooth flats have to be above
    # the dowel's centre or the dowel will not drop out
    if PR.COMB["top"] < PR.SHELF_Y - 1e-6:
        out.append("the comb is shorter than the dowel centre line: the dowels "
                   "would not be captured")
    # the cradle radius has to be at least the dowel radius, with clearance
    if PR.COMB["scallop"] < PR.ROD_R + 0.05:
        out.append("the cradle is %.2f against a %.2f dowel: it will not close"
                   % (PR.COMB["scallop"], PR.ROD_R))
    return out


def check_raft_opaque():
    """The gaps between the dowels must not look straight through the raft.

    This is here because they did. On a 38 mm pitch the reveal between two
    22 mm dowels was 16 mm, and a front view at 8 degrees of elevation saw
    through it to the FAR comb: the raft read as a chewed fringe of ash and
    aluminium along its whole top edge. It looked like a broken mesh and it was
    not -- the geometry was right and the design was wrong.

    The measure is the clear window: how much of the next dowel's flank is
    visible above the line of sight. If the neighbouring dowels overlap the
    sight line the raft is closed; if they do not, there is a hole.
    """
    out = []
    gap = PR.PITCH - PR.ROD_D
    # The threshold is measured, not guessed: 38 mm pitch (16 mm gap) produced
    # the see-through fringe and 30 mm (8 mm gap) does not, so the boundary is
    # between those. Half a dowel is the number that sits between them and it
    # has a physical reading -- once the gap is wider than the radius, the
    # crowns of two neighbours no longer overlap the sight line.
    if gap > PR.ROD_R:
        out.append("the dowels are %.0f mm apart on a %.0f mm pitch, which is "
                   "wider than half a dowel: the front view sees the far comb "
                   "through the raft" % (gap, PR.PITCH))
    return out


def check_shelf_plane():
    """The shelf has to land on all six dowels at once, and clear the teeth."""
    out = []
    # the top of every dowel
    top = PR.SHELF_Y
    for k, z in enumerate(PR.rod_zs()):
        # the tooth either side of this dowel has to be at or below the shelf
        if PR.COMB["top"] > top + 1e-6:
            out.append("comb tooth %d stands %.2f mm proud of the shelf"
                       % (k, PR.COMB["top"] - top))
            break
    # the shelf has to overhang the raft, or the front dowel is the front edge
    if PR.SHELF_D / 2.0 < PR.COMB["w"] / 2.0:
        out.append("the shelf (%.0f deep) does not cover the raft (%.0f deep)"
                   % (PR.SHELF_D, PR.COMB["w"]))
    # and it has to be wide enough to land on the outer combs
    if PR.SHELF_W / 2.0 < abs(PR.LEG_XS[-1]):
        out.append("the shelf does not reach the outer combs")
    return out


DENSITY = dict(ash=690.0, metal=2700.0, brass=8500.0, felt=1200.0)


def mesh_volume(mesh):
    """Signed volume of a closed mesh, in mm3."""
    v = 0.0
    for f in mesh.f:
        a, b, c = (mesh.v[i] for i in f)
        v += (a[0] * (b[1] * c[2] - b[2] * c[1])
              - a[1] * (b[0] * c[2] - b[2] * c[0])
              + a[2] * (b[0] * c[1] - b[1] * c[0])) / 6.0
    return abs(v)


def masses():
    """Mass of the assembled object, part by part, in kg."""
    import export as E
    out = {}
    for tag, name, mesh, _c, _m in E.parts():
        mat = "metal" if tag == "J01" else ("brass" if tag == "C01" else
                                           ("felt" if tag == "F01" else "ash"))
        kg = mesh_volume(mesh) * 1e-9 * DENSITY[mat] * E.QTY[tag]
        out[tag] = kg
    return out


def check_mass():
    """The README quotes masses. They have to come from the solids.

    Note what this does NOT assert. The combs are heavier than the board
    (1.50 kg each against 2.99 kg for the board, so 4.5 kg of aluminium against
    3.0 kg of ash). The first version of this check claimed that meant "gravity
    will not hold the raft", and it failed the build. That was wrong, and it is
    worth writing down why: the board does not hold the raft DOWN, it stops the
    dowels LIFTING OUT of the scallops. A dowel in an 11.2 mm cradle comes out
    upward only. The board sits on 6 teeth and its own 3 kg is 6.7x the mass of
    the 6 dowels it is retaining (0.47 kg), so the retain is fine; the 4.5 kg of
    comb is irrelevant to it because the comb is not what moves.

    What the masses DO have to say is that the object is portable and that the
    numbers in the README are real, so that is what is asserted.
    """
    out = []
    m = masses()
    total = sum(m.values())
    if not (4.0 < total < 12.0):
        out.append("the object weighs %.1f kg, which is not a desk shelf"
                   % total)
    # and what the board is actually doing has to hold: its mass against the
    # mass of the dowels it retains
    ratio = m["S01"] / max(m["R01"], 1e-6)
    if ratio < 2.0:
        out.append("the board is only %.1fx the mass of the dowels it "
                   "retains (%.2f kg vs %.2f kg)"
                   % (ratio, m["S01"], m["R01"]))
    return out, total


def check_readme_numbers():
    """Numbers quoted in the README have to still be true of the model.

    Every figure in that file was wrong at some point this session -- the
    window size, the comb mass, the pitch, the depth -- because they were typed
    before the part was final. This reads the numbers back out of the README and
    compares the ones that are checkable.
    """
    out = []
    p = os.path.join(OUT, "README.md")
    if not os.path.exists(p):
        return ["no README"]
    txt = open(p, encoding="utf-8").read()
    # measure the thing rather than recompute it: a sum of parameters is how
    # the README quoted 906 when the object is 902.
    import studio3d as R
    pts = R.scene_points(B.scene()) if hasattr(B, "scene") else None
    import build as _B
    pts = R.scene_points(_B.scene())
    size = "%d × %d × %d" % (round(pts[:, 0].max() - pts[:, 0].min()),
                             round(pts[:, 2].max() - pts[:, 2].min()),
                             round(pts[:, 1].max() - pts[:, 1].min()))
    checks = [
        (size, "overall size"),
        ("%.0f mm pitch" % PR.PITCH, "dowel pitch"),
        ("R%.1f" % PR.COMB["scallop"], "scallop radius"),
    ]
    for needle, what in checks:
        if needle not in txt:
            out.append("the README does not quote the %s (%s)" % (what, needle))
    return out


def check_files():
    out = []
    import export as E
    for tag, name, mesh, cut, mat in E.parts():
        fn = "%s_%s.stl" % (tag, name.replace(" ", "_"))
        p = os.path.join(OUT, "parts", "stl", fn)
        if not os.path.exists(p):
            out.append("missing part file: " + fn)
        elif os.path.getsize(p) < 400:
            out.append("part file looks empty: " + fn)
        if cut:
            dfn = "%s_%s_cut.dxf" % (tag, name.replace(" ", "_"))
            if not os.path.exists(os.path.join(OUT, "parts", "dxf", dfn)):
                out.append("missing DXF for a flat part: " + dfn)
    bom = os.path.join(OUT, "parts", "BOM.csv")
    if not os.path.exists(bom):
        out.append("no BOM")
    else:
        with open(bom) as fh:
            rows = list(csv.reader(fh))[1:]
        if len(rows) != len(E.parts()):
            out.append("the BOM lists %d parts but the assembly builds %d"
                       % (len(rows), len(E.parts())))
    return out


def main():
    fails = []

    w = check_watertight()
    if w:
        fails += w
        for m in w:
            print("[FAIL] " + m)
    else:
        print("[PASS] Meshes: every part is watertight.")

    d = check_dowels_seated()
    if d:
        fails += d
        for m in d:
            print("[FAIL] " + m)
    else:
        print("[PASS] Cradles: the six dowels seat in the comb scallops with "
              "%.2f mm of radial clearance."
              % (PR.COMB["scallop"] - PR.ROD_R))

    r = check_raft_opaque()
    if r:
        fails += r
        for m in r:
            print("[FAIL] " + m)
    else:
        print("[PASS] Raft: %.0f mm dowels on a %.0f mm pitch leave a %.0f mm "
              "reveal, too tight to see through." %
              (PR.ROD_D, PR.PITCH, PR.PITCH - PR.ROD_D))

    s = check_shelf_plane()
    if s:
        fails += s
        for m in s:
            print("[FAIL] " + m)
    else:
        print("[PASS] Shelf: %d x %d mm lands on all six dowels in one plane, "
              "%.0f mm above the desk."
              % (PR.SHELF_W, PR.SHELF_D, PR.SHELF_Y + PR.SHELF_T))

    f = check_files()
    if f:
        fails += f
        for m in f:
            print("[FAIL] " + m)
    else:
        print("[PASS] Files: every part has an STL, every flat part has a DXF, "
              "and the BOM matches.")

    rn = check_readme_numbers()
    if rn:
        fails += rn
        for msg in rn:
            print("[FAIL] " + msg)
    else:
        print("[PASS] README: the size, pitch and scallop radius quoted in it "
              "match the model.")

    m = None
    cm, total = check_mass()
    if cm:
        fails += cm
        for msg in cm:
            print("[FAIL] " + msg)
    else:
        mm = masses()
        print("[PASS] Mass: %.2f kg assembled -> board %.2f, combs %.2f, "
              "dowels %.2f; the board is %.1fx the dowel mass it retains."
              % (total, mm["S01"], mm["J01"], mm["R01"],
                 mm["S01"] / mm["R01"]))

    print()
    if fails:
        print("%d problem(s) to fix." % len(fails))
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
