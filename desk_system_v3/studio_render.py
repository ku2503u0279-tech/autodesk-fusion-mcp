"""Render the Studio Line product 1 — clean studio product shots."""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import studio_common as S          # noqa: E402
import studio3d as R               # noqa: E402

OUT = os.path.join(HERE, "Product1_AeroBridgeStudio", "parts", "renders")
os.makedirs(OUT, exist_ok=True)

BG_TOP = (0.960, 0.968, 0.978)
BG_BOT = (0.845, 0.866, 0.898)
FLOOR_Y = -0.0

# The desk itself is part of the picture, not part of the product.
DESK = dict(x0=-95.0, x1=725.0, z0=-58.0, z1=352.0, y=-14.0)


def deck_outline(x0, x1, z0, z1, r=30.0, steps=8):
    """Plan outline of the deck: square at the back, round at the front."""
    r = max(0.0, min(r, (x1 - x0) * 0.5 - 1.0, (z1 - z0) * 0.5 - 1.0))
    pts = [(x0, z0), (x1, z0)]                     # back edge
    # front-right corner, sweeping from the right side round to the front
    for k in range(steps + 1):
        a = (math.pi / 2.0) * k / steps
        pts.append((x1 - r + r * math.cos(a), z1 - r + r * math.sin(a)))
    for k in range(1, steps + 1):                  # front edge, right to left
        pts.append((x1 - r - (x1 - x0 - 2 * r) * k / steps, z1))
    for k in range(steps + 1):                     # front-left corner
        a = (math.pi / 2.0) * (steps - k) / steps
        pts.append((x0 + r - r * math.cos(a), z1 - r + r * math.sin(a)))
    return pts


# --------------------------------------------------------------- geometry
def parts_to_meshes(parts, P, lift=None):
    """Turn part dicts into triangle meshes. Every solid is a loft, so a
    chamfer is just an extra set of rings rather than a special case."""
    lift = lift or {}
    out = []
    for p in parts:
        if p.get("hidden"):
            continue
        dz = lift.get(p["pt"], (0.0, 0.0, 0.0))
        m = None
        if p["pt"] == "blade":
            # ONE solid with a hole in it. Drawing a solid prism and then a
            # separate ring on top leaves the inside of the blade visible
            # through the slot, which is exactly the bug that was there.
            if p.get("slot"):
                m = R.prism_with_hole(p["poly"], p["slot"], p["x0"], p["x1"],
                                      plane="x", mat=p["mat"],
                                      chamfer=p["chamfer"])
            else:
                m = R.prism_axis(p["poly"], p["x0"], p["x1"], plane="x",
                                 mat=p["mat"], chamfer=p["chamfer"])
        elif p["pt"] == "board":
            # two hundredths of a millimetre up: the deck and the blade crown
            # are meant to touch, and two coplanar surfaces make the renderer
            # fight over which one is in front. Invisible, and well inside any
            # real tolerance.
            yb, yf = p["y_back"] - 0.02, p["y_front"] - 0.02
            z0, z1 = p["z0"], p["z1"]

            def y_of(u, v, yb=yb, yf=yf, z0=z0, z1=z1):
                return yb + (yf - yb) * (v - z0) / (z1 - z0)

            # The deck is not a rectangle: its front corners are drawn round,
            # so it reads as a shaped part rather than a shelf with cut ends.
            outline = deck_outline(p["x0"], p["x1"], z0, z1,
                                    r=p.get("corner", 30.0))
            m = R.board(outline, y_of, p["thickness"], mat=p["mat"],
                        chamfer=p.get("chamfer", 0.0))
        elif p["pt"] == "rail":
            h = p["y_top"] - p["y_bot"]
            outline = [(p["x0"], p["z0"]), (p["x1"], p["z0"]),
                       (p["x1"], p["z1"]), (p["x0"], p["z1"])]

            def y_of(u, v, y=p["y_top"]):
                return y

            m = R.board(outline, y_of, h, mat=p["mat"], chamfer=1.6)
        elif p["pt"] == "pad":
            outlined = [(p["x0"], p["z0"]), (p["x1"], p["z0"]),
                        (p["x1"], p["z1"]), (p["x0"], p["z1"])]
            m = R.board(outlined, lambda u, v: p["y"], p["thickness"],
                        mat=p["mat"], chamfer=0.8)
        elif p["pt"] in ("rod", "clamp"):
            m = R.tube(p["x0"], p["x1"], p["y"], p["z"], p["d"] / 2.0,
                       mat=p["mat"], seg=40)
        if m is None:
            continue
        if any(dz):
            m.v = [(x + dz[0], y + dz[1], z + dz[2]) for (x, y, z) in m.v]
        out.append(m)
    return out


def desk_mesh(P):
    d = DESK
    return R.slab(d["x0"], d["x1"], d["z0"], d["z1"], d["y"] + P["slab_t"],
                  d["y"] + P["slab_t"], P["slab_t"], mat="oak")


def mat_mesh(P):
    """The leather desk mat, drawn a fraction above the desk so it never z-fights."""
    ins = P["mat_inset"]
    y = DESK["y"] + P["slab_t"] + 0.2
    return R.slab(ins, P["desk_x"] - ins, ins, P["desk_z"] - ins, y, y,
                  P["mat_t"], mat="graphite")


def scene(P, exploded=False, only=None):
    parts = S.assembly(P)
    if only is not None:
        parts = [p for p in parts if p["tag"] in only]
    lift = {}
    if exploded:
        lift = dict(board=(0.0, 118.0, -26.0), rail=(0.0, 196.0, -104.0),
                    felt=(0.0, 156.0, -62.0), rod=(0.0, -86.0, 54.0),
                    clamp=(0.0, -86.0, 54.0))
    return parts_to_meshes(parts, P, lift)


def frame(meshes, az, el, w, h, margin=1.06, fov=24.0, target=None):
    pts = R.scene_points(meshes)
    if target is not None:
        pts = np.vstack([pts, np.array([target], dtype=float)])
    cam = R.fit_camera(pts, az, el, fov=fov, w=w, h=h, margin=margin)
    if target is not None:
        cam.target = np.asarray(target, dtype=float)
        cam.eye = np.asarray(R.orbit(cam.target, np.linalg.norm(cam.eye - cam.target),
                                     az, el))
    return cam


def shoot(meshes, cam, w, h, path, shadow=True, exposure=1.0, vignette=0.16):
    img = R.render(meshes, cam, w=w, h=h, aa=2, bg_top=BG_TOP, bg_bot=BG_BOT,
                   floor_y=FLOOR_Y, shadow=shadow,
                   shadow_blur=int(max(6, w / 130)), exposure=exposure,
                   vignette=vignette, grain=0.004)
    img.save(path, optimize=True)
    return path


# ------------------------------------------------------------------ shots
HERO_KEYS = None


def render_hero(P, path=None):
    ms = scene(P)
    cam = frame(ms, 52.0, 12.0, 1520, 950, margin=1.00, fov=26.0)
    return shoot(ms, cam, 1520, 950, path or os.path.join(OUT, "hero.png"),
                 shadow=True, exposure=1.0, vignette=0.13)


def render_hero_q(P, path=None):
    ms = scene(P)
    cam = frame(ms, -26.0, 20.0, 1520, 950, margin=1.00, fov=27.0)
    return shoot(ms, cam, 1520, 950, path or os.path.join(OUT, "hero_side.png"))


def render_exploded(P, path=None):
    ms = scene(P, exploded=True)
    cam = frame(ms, 32.0, 20.0, 1520, 1050, margin=1.00, fov=27.0)
    return shoot(ms, cam, 1520, 1050, path or os.path.join(OUT, "exploded.png"),
                 shadow=True, exposure=0.98)


SINGLES = {
    "blade_left": dict(tags=["A1"], az=88, el=2, shadow=False),
    "blade_right": dict(tags=["A2"], az=-88, el=2, shadow=False),
    "deck": dict(tags=["D1", "D2", "D3"], az=42, el=34, shadow=False),
    "rod": dict(tags=["R1", "CL", "CR"], az=14, el=11, shadow=False),
    "stop": dict(tags=["S1", "F1"], az=40, el=36, shadow=False),
    "blade_pair": dict(tags=["A1", "A2"], az=0, el=0, shadow=False),
}


def render_single(key, P, path=None):
    cfg = SINGLES[key]
    ms = scene(P, only=cfg["tags"])
    cam = frame(ms, cfg["az"], cfg["el"], 950, 680, margin=0.97, fov=27.0)
    return shoot(ms, cam, 950, 680, path or os.path.join(OUT, key + ".png"),
                 shadow=cfg["shadow"], vignette=0.10)


def build_all():
    P = dict(S.P)
    made = dict(hero=render_hero(P), hero_side=render_hero_q(P),
                exploded=render_exploded(P))
    for k in SINGLES:
        made[k] = render_single(k, P)
    return made


if __name__ == "__main__":
    for k, v in build_all().items():
        print("%-12s %-20s %5d KB" % (k, os.path.basename(v),
                                      os.path.getsize(v) // 1024))
