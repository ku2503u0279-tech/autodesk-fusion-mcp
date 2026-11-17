"""Acceptance render: the stand, with a laptop to scale, actually resting on it.

This exists because a section can pass every geometry check and still not hold
a laptop. It seats a 340 x 240 x 16 mm machine against the stop and proves the
whole footprint lands on the deck with nothing overhanging.

    PYTHONPATH=. ../.venv/bin/python look_laptop.py
"""
import math
import numpy as np
import studio3d as S3
import studio_render as R
import studio_shell as SH
import studio_common as S

LAPTOP = dict(w=340.0, d=240.0, t=16.0)


def _laptop_mesh(stop_z, ang):
    """A slab resting on the deck, its low edge bearing on the stop.

    Built in the section's own (z, y) coordinates and extruded along X, the
    same way every lamination is. That way the laptop and the deck are the
    same maths and the machine cannot end up standing on edge.
    """
    st = SH.seat_line()
    t, d, w = LAPTOP["t"], LAPTOP["d"], LAPTOP["w"]
    x0 = (630.0 - w) / 2.0
    # the deck plane's outward normal, in (z, y): up and toward the user
    nz, ny = math.sin(ang), math.cos(ang)
    # walk back up the slope from the stop by the machine's depth
    zf, yf = stop_z, SH._seat_y(stop_z)
    zb = zf - d * math.cos(ang)
    yb = yf + d * math.sin(ang)
    prof = [(zf, yf), (zb, yb),
            (zb + nz * t, yb + ny * t), (zf + nz * t, yf + ny * t)]
    return S3.prism(prof, x0, x0 + w, mat="black")


def build():
    ms = []
    for p in SH.assembly():
        if p["pt"] == "lam":
            ms.append(S3.prism_with_holes(p["poly"], p["bores"], p["x0"], p["x1"],
                                          plane="x", mat="ash", chamfer=1.2))
        elif p["pt"] in ("rod", "clamp"):
            ms.append(S3.tube(p["x0"], p["x1"], p["y"], p["z"], p["d"] / 2.0,
                              mat=p["mat"]))
        elif p["pt"] == "stop":
            ms.append(S3.prism_with_holes(p["poly"], [], p["x0"], p["x1"],
                                          plane="x", mat="brass", chamfer=0.6))
        elif p["pt"] == "pad":
            ms.append(S3.box(p["x0"], p["x1"], p["y"], p["y"] + 1.0, p["z0"],
                             p["z1"], mat="felt"))
    return ms


def main():
    st = SH.seat_line()
    ang = math.atan2(st["y0"] - st["y1"], st["z1"] - st["z0"])
    s = SH.stop_parts()[0]
    stop_z = min(q[0] for q in s["poly"])
    # measure the fit before drawing it
    face = math.hypot(st["z1"] - st["z0"], st["y0"] - st["y1"])
    room = face - (st["z1"] - stop_z)
    print("deck face      %.1f mm" % face)
    print("stop backs onto z %.0f, occupies %.0f mm"
          % (stop_z, st["z1"] - stop_z))
    print("room for laptop %.1f mm ; machine needs %.0f -> %s"
          % (room, LAPTOP["d"], "RESTS" if room >= LAPTOP["d"] else "OVERHANG"))
    print("laptop back edge z %.1f ; deck back edge z %.0f -> spare %.1f mm"
          % (stop_z - LAPTOP["d"] * math.cos(ang), st["z0"],
             (stop_z - LAPTOP["d"] * math.cos(ang)) - st["z0"]))
    ms = build() + [_laptop_mesh(stop_z, ang)]
    for name, (az, el) in {"hero": (38, 16), "front": (90, 8),
                           "side": (0, 4)}.items():
        cam = R.frame(ms, az, el, 1300, 900, margin=1.02, fov=25.0)
        R.shoot(ms, cam, 1300, 900, "/tmp/lap_%s.png" % name)
    print("rendered /tmp/lap_hero.png /tmp/lap_front.png /tmp/lap_side.png")


if __name__ == "__main__":
    main()
