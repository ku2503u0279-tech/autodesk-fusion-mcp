"""Render the Studio Line product 1 — clean studio product shots."""
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


# --------------------------------------------------------------- geometry
def parts_to_meshes(parts, P, lift=None):
    """Turn part dicts into triangle meshes for the renderer."""
    lift = lift or {}
    out = []
    for p in parts:
        dz = lift.get(p["pt"], (0.0, 0.0, 0.0))
        if p["pt"] == "blade":
            out.append(R.prism(p["poly"], p["x0"] + dz[0], p["x1"] + dz[0],
                               mat=p["mat"]))
            out[-1].v = [(x, y + dz[1], z + dz[2]) for (x, y, z) in out[-1].v]
        elif p["pt"] == "board":
            out.append(R.slab(p["x0"], p["x1"], p["z0"], p["z1"],
                              p["y_back"] + dz[1], p["y_front"] + dz[1],
                              p["thickness"], mat=p["mat"]))
            out[-1].v = [(x + dz[0], y, z + dz[2]) for (x, y, z) in out[-1].v]
        elif p["pt"] == "rail":
            out.append(R.slab(p["x0"], p["x1"], p["z0"], p["z1"],
                              p["y_top"] + dz[1], p["y_top"] + dz[1],
                              p["y_top"] - p["y_bot"], mat=p["mat"]))
            out[-1].v = [(x + dz[0], y, z + dz[2]) for (x, y, z) in out[-1].v]
        elif p["pt"] == "pad":
            if p.get("hidden"):
                continue
            out.append(R.slab(p["x0"], p["x1"], p["z0"], p["z1"],
                              p["y"] + dz[1], p["y"] + dz[1],
                              p["thickness"], mat=p["mat"]))
            out[-1].v = [(x + dz[0], y, z + dz[2]) for (x, y, z) in out[-1].v]
        elif p["pt"] in ("rod", "clamp"):
            out.append(R.tube(p["x0"] + dz[0], p["x1"] + dz[0],
                              p["y"] + dz[1], p["z"] + dz[2],
                              p["d"] / 2.0, mat=p["mat"]))
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
    cam = frame(ms, 30.0, 14.0, 1520, 950, margin=1.00, fov=27.0)
    return shoot(ms, cam, 1520, 950, path or os.path.join(OUT, "hero.png"),
                 shadow=True, exposure=1.0, vignette=0.13)


def render_hero_q(P, path=None):
    ms = scene(P)
    cam = frame(ms, -30.0, 16.0, 1520, 950, margin=1.00, fov=27.0)
    return shoot(ms, cam, 1520, 950, path or os.path.join(OUT, "hero_side.png"))


def render_exploded(P, path=None):
    ms = scene(P, exploded=True)
    cam = frame(ms, 32.0, 20.0, 1520, 1050, margin=1.00, fov=27.0)
    return shoot(ms, cam, 1520, 1050, path or os.path.join(OUT, "exploded.png"),
                 shadow=True, exposure=0.98)


SINGLES = {
    "blade_left": dict(tags=["A1"], az=30, el=6, shadow=False),
    "blade_right": dict(tags=["A2"], az=-30, el=6, shadow=False),
    "deck": dict(tags=["D1", "D2", "D3"], az=42, el=34, shadow=False),
    "rod": dict(tags=["R1", "CL", "CR"], az=14, el=11, shadow=False),
    "stop": dict(tags=["S1", "F1"], az=40, el=36, shadow=False),
    "blade_pair": dict(tags=["A1", "A2"], az=0, el=2, shadow=False),
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
