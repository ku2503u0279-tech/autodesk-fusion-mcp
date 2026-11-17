"""DraftShelf — write one STL per part, plus DXF for the flat parts, plus a BOM.

Every part ships as its own real file. Nothing here is a runtime-only export:
the STLs are the same triangles the renderer draws, generated from build.py,
which is generated from params.py.

    PYTHONPATH=..:.. ../../.venv/bin/python export.py
"""
import csv
import math
import os
import struct

import studio3d as R
import build as B
import params as PR

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "Product6_DraftShelf")
STL = os.path.join(OUT, "parts", "stl")
DXF = os.path.join(OUT, "parts", "dxf")


# ------------------------------------------------------------------ STL
def write_stl(path, mesh, name=None):
    tris = []
    for f in mesh.f:
        if len(f) == 3:
            tris.append(f)
    with open(path, "wb") as fh:
        fh.write((name or "part").encode()[:80].ljust(80, b" "))
        fh.write(struct.pack("<I", len(tris)))
        for (a, b, c) in tris:
            p, q, r = mesh.v[a], mesh.v[b], mesh.v[c]
            u = [q[i] - p[i] for i in range(3)]
            w = [r[i] - p[i] for i in range(3)]
            n = [u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2],
                 u[0] * w[1] - u[1] * w[0]]
            L = math.sqrt(sum(k * k for k in n)) or 1.0
            n = [k / L for k in n]
            fh.write(struct.pack("<3f", *n))
            for pt in (p, q, r):
                fh.write(struct.pack("<3f", *[float(k) for k in pt]))
            fh.write(struct.pack("<H", 0))


# ------------------------------------------------------------------ DXF
def write_dxf(path, loops, layer="OUTLINE"):
    out = []

    def g(code, val):
        out.append(str(code))
        out.append(str(val))

    g(0, "SECTION"); g(2, "HEADER"); g(9, "$ACADVER"); g(1, "AC1009")
    g(0, "ENDSEC")
    g(0, "SECTION"); g(2, "TABLES"); g(0, "ENDSEC")
    g(0, "SECTION"); g(2, "ENTITIES")
    for loop in loops:
        for k in range(len(loop)):
            a = loop[k]
            b = loop[(k + 1) % len(loop)]
            g(0, "LINE"); g(8, layer)
            g(10, "%.4f" % a[0]); g(20, "%.4f" % a[1]); g(30, "0.0")
            g(11, "%.4f" % b[0]); g(21, "%.4f" % b[1]); g(31, "0.0")
    g(0, "ENDSEC"); g(0, "EOF")
    with open(path, "w") as fh:
        fh.write("\n".join(out) + "\n")


# ------------------------------------------------------------------ parts
def parts():
    """(tag, name, mesh, cuttable, material) for every distinct part."""
    out = []
    out.append(("J01", "Comb", B.comb(0.0), False, PR.STOCK["alum"]))
    out.append(("R01", "Dowel", B.dowel(0.0), False, PR.STOCK["rod"]))
    out.append(("S01", "Shelf", B.shelf(), True, PR.STOCK["shelf"]))
    out.append(("C01", "End Cap", B.cap(0.0, 0.0), False, PR.STOCK["brass"]))
    out.append(("F01", "Pad", B.pad(0.0), True, PR.STOCK["tpu"]))
    return out


QTY = dict(J01=3, R01=6, S01=1, C01=12, F01=3)


def main():
    os.makedirs(STL, exist_ok=True)
    os.makedirs(DXF, exist_ok=True)
    made = []
    for tag, name, mesh, cuttable, mat in parts():
        fn = "%s_%s.stl" % (tag, name.replace(" ", "_"))
        write_stl(os.path.join(STL, fn), mesh, name)
        made.append(fn)
        if cuttable:
            # DXF in the part's own working plane
            if tag == "S01":
                loop = [(-PR.SHELF_W / 2, -PR.SHELF_D / 2), (PR.SHELF_W / 2, -PR.SHELF_D / 2),
                        (PR.SHELF_W / 2, PR.SHELF_D / 2), (-PR.SHELF_W / 2, PR.SHELF_D / 2)]
            else:
                w = PR.COMB["w"] / 2.0
                loop = [(-PR.COMB["t"] / 2 + 8, -w + 10), (PR.COMB["t"] / 2 - 8, -w + 10),
                        (PR.COMB["t"] / 2 - 8, w - 10), (-PR.COMB["t"] / 2 + 8, w - 10)]
            dfn = "%s_%s_cut.dxf" % (tag, name.replace(" ", "_"))
            write_dxf(os.path.join(DXF, dfn), [loop], layer=tag)
            made.append(dfn)

    # BOM
    with open(os.path.join(OUT, "parts", "BOM.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["tag", "part", "qty", "material", "file"])
        for tag, name, mesh, cuttable, mat in parts():
            w.writerow([tag, name, QTY[tag], mat,
                        "%s_%s.stl" % (tag, name.replace(" ", "_"))])

    # cutting list: the stock you actually buy
    with open(os.path.join(OUT, "parts", "CUTTING_LIST.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["stock", "size", "qty", "note"])
        w.writerow(["ash dowel", "22 mm dia x %d mm" % (PR.ROD_X1 - PR.ROD_X0),
                    PR.N_RODS, "six lengths, ends capped"])
        w.writerow(["ash board", "%d x %d x %d mm" % (PR.SHELF_W, PR.SHELF_D, PR.SHELF_T),
                    1, "S01, one piece"])
        w.writerow(["6061-T6 billet", "%d x %d x %d mm" % (PR.COMB["t"], PR.COMB["w"], PR.COMB["top"]),
                    PR.LEG_XS.__len__(), "J01, one setup each"])
        w.writerow(["CZ121 brass", "%d mm dia x 6 mm" % (2 * PR.CAP["r"]),
                    PR.N_RODS * 2, "C01, turned"])

    print("%d files" % len(made))
    for m in made:
        print("  " + m)


if __name__ == "__main__":
    main()
