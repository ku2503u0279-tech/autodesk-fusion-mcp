"""DraftShelf — the render set.

Same camera and lighting recipe as Product 1 so the two products photograph the
same. The only change is the background, which is a shade warmer here to keep
the pale ash from going blue against a cool grey.

    PYTHONPATH=..:.. ../../.venv/bin/python render.py
"""
import os

import studio3d as R
import build as B
import export as E

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "Product6_DraftShelf", "parts", "renders")
os.makedirs(OUT, exist_ok=True)

BG_TOP = (0.965, 0.967, 0.972)
BG_BOT = (0.855, 0.862, 0.878)


def shot(meshes, az, el, w, h, path, margin=1.03, fov=26.0, exposure=1.02,
         vignette=0.13, shadow=True):
    cam = R.fit_camera(R.scene_points(meshes), az, el, fov=fov, w=w, h=h,
                       margin=margin)
    img = R.render(meshes, cam, w=w, h=h, aa=2, bg_top=BG_TOP, bg_bot=BG_BOT,
                   shadow=shadow, exposure=exposure, vignette=vignette,
                   grain=0.004)
    img.save(path, optimize=True)
    return path


def exploded():
    """Every part, pulled apart along the axis it comes off on.

    The combs lift, the dowels run out sideways, the shelf comes off the top,
    and the caps pull off the dowel ends. Nothing is rotated, because an
    exploded view should show the assembly order and not a puzzle.
    """
    ms = []
    for x in B.PR.LEG_XS:
        c = B.comb(x)
        c.v = [(vx + 0, vy + 150.0, vz) for (vx, vy, vz) in c.v]
        ms.append(c)
    for k, z in enumerate(B.PR.rod_zs()):
        d = B.dowel(z)
        d.v = [(vx, vy + 26.0 + 7.0 * k, vz) for (vx, vy, vz) in d.v]
        ms.append(d)
        for cx in (B.PR.ROD_X0 - 34.0 - 8.0 * k, B.PR.ROD_X1 + 34.0 + 8.0 * k):
            c = B.cap(cx, z)
            c.v = [(vx, vy + 26.0 + 7.0 * k, vz) for (vx, vy, vz) in c.v]
            ms.append(c)
    s = B.shelf()
    s.v = [(vx, vy + 210.0, vz) for (vx, vy, vz) in s.v]
    ms.append(s)
    return ms


def build_all():
    made = {}
    ms = B.scene()
    made["hero"] = shot(ms, 36, 16, 1520, 950, os.path.join(OUT, "hero.png"))
    made["hero_side"] = shot(ms, -42, 12, 1520, 950,
                             os.path.join(OUT, "hero_side.png"))
    made["front"] = shot(ms, 70, 8, 1520, 950, os.path.join(OUT, "front.png"))
    made["detail"] = shot(ms, 24, 24, 1300, 900, os.path.join(OUT, "detail.png"),
                          margin=0.72)
    made["exploded"] = shot(exploded(), 34, 18, 1520, 1050,
                            os.path.join(OUT, "exploded.png"), exposure=0.99)
    for tag, name, mesh, _c, _m in E.parts():
        made[tag] = shot([mesh], 34, 22, 950, 680,
                         os.path.join(OUT, tag.lower() + ".png"),
                         margin=0.94, vignette=0.10)
    return made


if __name__ == "__main__":
    for k, v in build_all().items():
        print("%-10s %-16s %5d KB" % (k, os.path.basename(v),
                                      os.path.getsize(v) // 1024))
