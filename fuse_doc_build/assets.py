"""Render every illustration the portfolio needs into fuse_doc_build/out."""
import os

from PIL import Image

import geometry as G

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
os.makedirs(OUT, exist_ok=True)


def save(img, name):
    p = os.path.join(OUT, name + ".png")
    img.save(p, optimize=True)
    return p


def scene_centre(s):
    xs = [p for f in s.faces for p in f["pts"]]
    lo = [min(p[i] for p in xs) for i in range(3)]
    hi = [max(p[i] for p in xs) for i in range(3)]
    return tuple((lo[i] + hi[i]) / 2 for i in range(3))


VIEWS = {
    "p0": dict(az=34, el=30),
    "p1": dict(az=34, el=24),
    "p2": dict(az=-58, el=25),
    "p3": dict(az=34, el=17),
    "p4": dict(az=40, el=14),
    "p5": dict(az=34, el=24),
    "p5d": dict(az=32, el=26),
    "p5m": dict(az=-32, el=16),
}


def hero():
    s = G.scene_full()
    return save(s.render(s.fit(az=40, el=30, w=1500, h=880, margin=0.97, target=(300, 20, 150)), aa=2,
                         shadow=0.40), "hero")


def hero_dark():
    s = G.scene_full()
    return save(s.render(s.fit(az=36, el=26, w=1500, h=880, margin=0.97, target=(300, 20, 150)), aa=2,
                         shadow=0.55, bg_top="#141B24", bg_bot="#0C1015",
                         edge_color="#7E94AD", vig_color="#0E1319", shadow_color="#05080B"), "hero_dark")


def product(which, w=1000, h=700, margin=0.94):
    s = G.scene_product(which)
    v = VIEWS.get(which, {})
    cam = s.fit(az=v.get("az", 38), el=v.get("el", 28), w=w, h=h, margin=margin,
                target=scene_centre(s))
    return save(s.render(cam, aa=2, shadow=0.34), "prod_" + which)


def build_all():
    out = {"hero": hero(), "hero_dark": hero_dark()}
    for w in VIEWS:
        out[w] = product(w)
    return out


if __name__ == "__main__":
    for k, v in build_all().items():
        print(k, os.path.basename(v), os.path.getsize(v) // 1024, "KB")
