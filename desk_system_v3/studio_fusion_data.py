"""Regenerate the numbers embedded in Product1_AeroBridgeStudio/AeroBridge_Studio.py.

The Fusion script has to run inside Fusion, where `studio_blade` is not
importable, so it carries the blade silhouette and the pierce with it. Those
numbers are generated from the model here rather than typed by hand, so the
Fusion build can never drift from the drawings and the renders.

    python studio_fusion_data.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import studio_blade as BL          # noqa: E402
import studio_common as S          # noqa: E402

OUT = os.path.join(HERE, "Product1_AeroBridgeStudio", "AeroBridge_Studio.py")

KEEP = [
    "desk_x", "desk_z", "blade_t", "blade_chamfer", "blade_rake",
    "blade_leg_w", "blade_crown_h", "blade_belly", "blade_knee_r",
    "crest", "crest_end", "crest_peak", "span_left", "span_right",
    "deck_t", "deck_back", "deck_front", "deck_z0", "deck_z1",
    "deck_chamfer", "gutter", "rod_d", "rod_y", "rod_z",
    "stop_h", "stop_w", "stop_z", "felt_t", "pad_size",
]


def fmt_pts(pts, per=6):
    rows = []
    for i in range(0, len(pts), per):
        rows.append("        " + " ".join("(%.2f, %.2f)," % (a, b)
                                          for a, b in pts[i:i + per]))
    return "\n".join(rows)


def build_block():
    P = S.P
    bp = S.blade_params(P)
    outline = BL.blade_polygon(bp)
    slot = BL.fin_slot(bp)
    param_lines = ["    %s=%.1f," % (k, P[k]) for k in KEEP if k in P]
    return (
        "PARAMS = dict(\n"
        + "\n".join(param_lines) + "\n"
        + "    # The blade silhouette and the pierce, generated from "
          "studio_blade.py so\n"
        + "    # this script cannot drift from the drawings. Regenerate with:\n"
        + "    #     python studio_fusion_data.py\n"
        + "    BLADE_OUTLINE=[\n" + fmt_pts(outline) + "\n    ],\n"
        + "    BLADE_SLOT=[\n" + fmt_pts(slot) + "\n    ],\n"
        + ")\n"
    )


def main():
    block = build_block()
    src = open(OUT).read()
    a = src.index("PARAMS = dict(")
    # find the closing bracket of the dict, so nothing after it is touched
    depth, i = 0, src.index("(", a)
    while i < len(src):
        if src[i] == "(":
            depth += 1
        elif src[i] == ")":
            depth -= 1
            if depth == 0:
                break
        i += 1
    src = src[:a] + block.rstrip("\n") + src[i + 1:]
    open(OUT, "w").write(src)
    P = S.P
    print("updated %s" % OUT)
    print("  %d params, %d outline points, %d slot points"
          % (len([k for k in KEEP if k in P]),
             len(BL.blade_polygon(S.blade_params(P))),
             len(BL.fin_slot(S.blade_params(P)))))


if __name__ == "__main__":
    main()
