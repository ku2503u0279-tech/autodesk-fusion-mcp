"""AeroBridge Studio, product 1 — every parameter and every part in one place.

One dict `P` holds every dimension in millimetres. Every part is described by a
small dict, so the renderer, the Fusion script, the DXF writer and the BOM all
read the same numbers and cannot drift apart.

The product itself is defined in `studio_shell`: a stack of eleven ply
laminations split from one continuous arch. This module is the desk it stands
on, the master parameters, and the assembly list that the rest of the chain
consumes.

Coordinates
    X  0 .. 630   left to right across the desk
    Y  0          top of the desk mat, positive is up
    Z  0          back edge of the desk (against the wall), positive toward you
"""
import math

import studio_shell as SH

# ------------------------------------------------------------------ params
P = dict(
    # the desk it stands on, from the brief
    desk_x=630.0, desk_z=280.0, slab_t=18.0, mat_t=3.0, mat_inset=34.0,
    slab_x0=40.0, slab_x1=590.0, slab_z0=24.0, slab_z1=256.0,

    # ---- the stand. The section itself lives in studio_shell; these are the
    #      numbers the rest of the chain quotes.
    span=SH.SHELL["span"],
    n_lam=SH.SHELL["n"],
    lam_gap=SH.SHELL["gap"],
    wall=SH.WALL,
    section_pts=len(SH.section()),

    # ---- felt pads
    felt_t=2.0, pad_size=32.0,
)


# ------------------------------------------------------------------ parts
def assembly(P=None):
    """Every part, in the order the BOM lists them."""
    a = dict(P if P else globals()["P"])
    return SH.assembly(a)


def by_tag(parts, *tags):
    return [p for p in parts if p["tag"] in tags]


# ------------------------------------------------------------------ checks
def check(P=None):
    """Plain-English sanity checks. Returns messages; empty means good."""
    a = dict(P if P else globals()["P"])
    out = list(SH.check(a))

    parts = assembly(a)
    tags = [p["tag"] for p in parts]
    if len(set(tags)) != len(tags):
        out.append("two parts share a tag")
    xs, zs, ys = [], [], []
    for p in parts:
        if p["pt"] == "lam":
            xs += [p["x0"], p["x1"]]
            for (z, y) in p["poly"]:
                zs.append(z)
                ys.append(y)
    if xs and (min(xs) < 0 or max(xs) > a["desk_x"]):
        out.append("the stack runs off the end of the desk")
    if zs and (min(zs) < 2 or max(zs) > a["desk_z"] - 2):
        out.append("the stack runs off the front or back of the desk")
    if not parts:
        out.append("no parts")
    return out


if __name__ == "__main__":
    msgs = check()
    print("checks:", "all good" if not msgs else "")
    for m in msgs:
        print("  !", m)
    print("%d parts" % len(assembly()))
    for p in assembly():
        print("  %-4s %-22s %-6s %-6s" % (p["tag"], p["name"], p["kind"], p["pt"]))
