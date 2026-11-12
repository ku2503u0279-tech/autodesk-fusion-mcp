"""Write every part of the product out as a real file you can open.

This is the step that turns the design into things you can actually make:

  * an STL for every single part, so you can look at it in any 3D viewer or
    send it to a printer;
  * a DXF of the blade outline, for a CNC router or a laser cutter;
  * a BOM (bill of materials) as a CSV, and a cutting list for the timber.

Run it from this folder:

    ../.venv/bin/python studio_export.py

Everything lands in Product1_AeroBridgeStudio/parts/.
"""
import csv
import math
import os
import struct

import studio_common as S
import studio3d as R

HERE = os.path.dirname(os.path.abspath(__file__))
PRODUCT = "Product1_AeroBridgeStudio"
OUT = os.path.join(HERE, PRODUCT)
PARTS = os.path.join(OUT, "parts")


# ------------------------------------------------------------------- STL
def write_stl(path, mesh, name=None):
    """Binary STL, the format every viewer and slicer reads."""
    v, f = mesh.arrays()
    with open(path, "wb") as fh:
        header = (name or os.path.basename(path))[:70].encode("ascii", "replace")
        fh.write(header.ljust(80, b" "))
        fh.write(struct.pack("<I", len(f)))
        for a, b, c in f:
            p = v[[a, b, c]]
            n = _normal(p[0], p[1], p[2])
            fh.write(struct.pack("<3f", *n))
            for q in p:
                fh.write(struct.pack("<3f", *q))
            fh.write(b"\x00\x00")
    return path


def _normal(a, b, c):
    u = [b[i] - a[i] for i in range(3)]
    w = [c[i] - a[i] for i in range(3)]
    n = [u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2],
         u[0] * w[1] - u[1] * w[0]]
    ln = math.sqrt(sum(k * k for k in n)) or 1.0
    return [k / ln for k in n]


# ------------------------------------------------------------------- DXF
def write_dxf(path, loops, layer="OUTLINE", note=None):
    """A minimal DXF (AutoCAD 2000) with one or more closed polylines.

    `loops` is a list of point lists, each in millimetres. This is what a CNC
    shop wants: the exact outline, already to size, no scaling needed.
    """
    out = []
    add = out.append

    def g(code, value):
        add(str(code))
        add(str(value))

    g(0, "SECTION"); g(2, "HEADER")
    g(9, "$ACADVER"); g(1, "AC1015")
    g(9, "$INSUNITS"); g(70, 4)          # 4 = millimetres
    g(0, "ENDSEC")

    g(0, "SECTION"); g(2, "TABLES")
    g(0, "TABLE"); g(2, "LAYER"); g(70, 1)
    g(0, "LAYER"); g(2, layer); g(70, 0); g(62, 7); g(6, "CONTINUOUS")
    g(0, "ENDTAB"); g(0, "ENDSEC")

    g(0, "SECTION"); g(2, "ENTITIES")
    for loop in loops:
        g(0, "LWPOLYLINE")
        g(8, layer)
        g(90, len(loop))
        g(70, 1)                          # 1 = closed
        for x, y in loop:
            g(10, "%.4f" % x)
            g(20, "%.4f" % y)
    g(0, "ENDSEC")
    if note:
        g(0, "SECTION"); g(2, "OBJECTS"); g(0, "ENDSEC")
    g(0, "EOF")

    with open(path, "w", newline="\r\n") as fh:
        fh.write("\n".join(out) + "\n")
    return path


# ------------------------------------------------------------------ meshes
def mesh_for(p, P):
    """The same geometry the renders use, as one mesh."""
    if p["pt"] == "blade":
        return R.prism(p["poly"], p["x0"], p["x1"], mat=p["mat"])
    if p["pt"] == "board":
        return R.slab(p["x0"], p["x1"], p["z0"], p["z1"],
                      p["y_back"], p["y_front"], p["thickness"], mat=p["mat"])
    if p["pt"] == "rail":
        return R.slab(p["x0"], p["x1"], p["z0"], p["z1"],
                      p["y_top"], p["y_top"], p["y_top"] - p["y_bot"], mat=p["mat"])
    if p["pt"] == "pad":
        return R.slab(p["x0"], p["x1"], p["z0"], p["z1"],
                      p["y"], p["y"], p["thickness"], mat=p["mat"])
    if p["pt"] in ("rod", "clamp"):
        return R.tube(p["x0"], p["x1"], p["y"], p["z"], p["d"] / 2.0, mat=p["mat"])
    raise ValueError(p["pt"])


def size_of(p):
    """Overall size of one part, as (length, height, thickness) in mm."""
    if p["pt"] == "blade":
        zs = [z for z, _ in p["poly"]]
        ys = [y for _, y in p["poly"]]
        return (max(zs) - min(zs), max(ys) - min(ys), p["x1"] - p["x0"])
    if p["pt"] in ("board", "rail", "pad"):
        zt = abs(p["y_back"] - p["y_front"]) if p["pt"] == "board" else 0.0
        if p["pt"] == "rail":
            t = p["y_top"] - p["y_bot"]
            return (p["x1"] - p["x0"], p["z1"] - p["z0"], t)
        return (p["x1"] - p["x0"], abs(p["z1"] - p["z0"]),
                p.get("thickness", p.get("t", 0.0)) + zt * 0.0)
    if p["pt"] in ("rod", "clamp"):
        return (p["x1"] - p["x0"], p["d"], p["d"])
    return (0, 0, 0)


# ------------------------------------------------------------------- main
def main(P=None):
    P = dict(P or S.P)
    for sub in ("stl", "dxf"):
        os.makedirs(os.path.join(PARTS, sub), exist_ok=True)

    parts = S.assembly(P)
    made = []
    for p in parts:
        m = mesh_for(p, P)
        fn = "%s_%s.stl" % (p["tag"], p["name"].replace(" ", "_"))
        write_stl(os.path.join(PARTS, "stl", fn), m, name="%s %s" % (p["tag"], p["name"]))
        made.append(fn)
        if p["pt"] == "blade":
            dxf = "%s_%s_cut.dxf" % (p["tag"], p["name"].replace(" ", "_"))
            write_dxf(os.path.join(PARTS, "dxf", dxf),
                      [[(z, y) for (z, y) in p["poly"]]], note=True)
            made.append(dxf)

    # one combined DXF: both blades side by side, so a shop can nest them
    both = []
    for p in parts:
        if p["pt"] == "blade":
            dx = 0.0 if p["side"] == "left" else 0.0
            both.append([(z + dx, y) for (z, y) in p["poly"]])
    write_dxf(os.path.join(PARTS, "dxf", "A1_A2_Both_Blades_cut.dxf"), both, note=True)

    bom = os.path.join(PARTS, "BOM.csv")
    with open(bom, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["tag", "part", "material", "qty",
                    "length_mm", "height_mm", "thickness_mm"])
        for p in parts:
            l, h, t = size_of(p)
            w.writerow([p["tag"], p["name"], p["mat"], 1,
                        "%.1f" % l, "%.1f" % h, "%.1f" % t])

    cut = os.path.join(PARTS, "CUTTING_LIST.csv")
    with open(cut, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["material", "part", "tag", "size_mm", "qty", "notes"])
        for p in parts:
            if p["mat"] not in ("walnut", "ash"):
                continue
            l, h, t = size_of(p)
            note = ""
            if p["pt"] == "blade":
                note = "cut 2 identical, mirror not required - the profile is the same both sides"
            if p["pt"] == "board":
                note = "single board, grain runs front to back"
            if p["pt"] == "rail":
                note = "grain runs left to right"
            w.writerow([p["mat"], p["name"], p["tag"],
                        "%d x %d x %d" % (round(l), round(h), round(t)), 1, note])
    made += [os.path.basename(bom), os.path.basename(cut)]
    return made


if __name__ == "__main__":
    files = main()
    print("wrote %d files into %s" % (len(files), PARTS))
    for f in files:
        print("  ", f)
