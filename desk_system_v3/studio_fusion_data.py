"""Regenerate the generated block inside the Fusion script.

The Fusion script has to build the same bodies as the renders and the STLs, from
the same numbers. Rather than keep two copies of the section, this module writes
the numbers out of `studio_shell` into the script, between two marker lines.

Run it after ANY change to studio_shell.py or studio_common.py:

    python studio_fusion_data.py

Everything between the BEGIN/END markers is replaced; everything outside them is
hand-written script code and is left alone.

Why a marker block and not a bracket match
    An earlier version found the `PARAMS` dict by counting brackets from the
    word PARAMS. It silently ate the `import adsk` lines below it and the script
    built zero bodies. Markers cannot drift.
"""
import os

import studio_common as S
import studio_shell as SH

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "Product1_AeroBridgeStudio", "AeroBridge_Studio.py")

BEGIN = "# ---- BEGIN GENERATED (studio_fusion_data.py) ----"
END = "# ---- END GENERATED ----"


def _fmt(v):
    if isinstance(v, str):
        return repr(v)
    if isinstance(v, bool):
        return "True" if v else "False"
    if isinstance(v, int):
        return "%d" % v
    if isinstance(v, (list, tuple)):
        return "[" + ", ".join("(%.3f, %.3f)" % (a, b) for (a, b) in v) + "]"
    return "%.4f" % v


def build_block(P=None):
    """The text that goes between the markers."""
    p = P or S.P
    st = SH.seat_line()
    lines = [BEGIN, "PARAMS = dict("]
    for k, v in sorted(p.items()):
        if k == "wall":            # written once, below, from studio_shell
            continue
        lines.append("    %s=%s," % (k, _fmt(v)))
    lines.append("    seat=dict(z0=%.3f, z1=%.3f, y0=%.3f, y1=%.3f)," %
                 (st["z0"], st["z1"], st["y0"], st["y1"]))
    lines.append("    shoulder=%.4f," % SH.SHELL["shoulder"])
    lines.append("    shoulder_z=%.4f," % SH.SHELL["shoulder_z"])
    lines.append("    lift_end=0.0,")
    if "n_lam" not in p:
        lines.append("    n_lam=%d," % SH.SHELL["n"])
    if "lam_gap" not in p:
        lines.append("    lam_gap=%.3f," % SH.SHELL["gap"])
    lines.append(")")

    # the section, and the deformation applied to it for each lamination
    lines.append("SECTION = [")
    sec = SH.section()
    for (z, y) in sec:
        lines.append("    (%.4f, %.4f)," % (z, y))
    lines.append("]")

    # Each lamination's DEFORMED section, written out in full rather than as a
    # scale factor. The renders deform the path by a wave that varies along it,
    # not by a uniform scale, so re-deriving it in Fusion from one number would
    # build a different solid — which is precisely the drift the whole pipeline
    # exists to prevent. Eleven times eighty-four points is cheap.
    lines.append("LAMINATIONS = [")
    for lam in SH.lamination_profiles(p):
        lines.append("    dict(i=%d, x0=%.4f, x1=%.4f, poly=[" %
                     (lam["i"], lam["x0"], lam["x1"]))
        row = []
        for (z, y) in lam["poly"]:
            row.append("(%.4f, %.4f)," % (z, y))
            if len(row) == 3:
                lines.append("        " + " ".join(row))
                row = []
        if row:
            lines.append("        " + " ".join(row))
        lines.append("    ]),")
    lines.append("]")

    lines.append("RODS = [")
    for r in SH.RODS:
        lines.append("    dict(tag=%r, y=%.3f, z=%.3f, r=%.3f,"
                     % (r["tag"], r["y"], r["z"], r["r"]))
        x0, x1 = r_span(p, r)
        lines.append("         x0=%.3f, x1=%.3f)," % (x0, x1))
    lines.append("]")
    lines.append("COLLAR = dict(len=%.3f, r=%.3f)" % (SH.COLLAR["len"], SH.COLLAR["r"]))

    stp = SH.stop_parts(p)[0]
    lines.append("STOP = dict(x0=%.3f, x1=%.3f, poly=%s)"
                 % (stp["x0"], stp["x1"], _fmt(stp["poly"])))

    pads = SH.pad_parts(p)
    lines.append("PADS = [")
    for q in pads:
        lines.append("    dict(tag=%r, x0=%.3f, x1=%.3f, z0=%.3f, z1=%.3f, "
                     "y=%.3f, t=%.3f)," %
                     (q["tag"], q["x0"], q["x1"], q["z0"], q["z1"], q["y"],
                      q["thickness"]))
    lines.append("]")
    lines.append(END)
    return "\n".join(lines)


def r_span(p, r):
    """(x0, x1) of a rod, as the part list has it."""
    for q in SH.rod_parts(p):
        if q["tag"] == r["tag"]:
            return (q["x0"], q["x1"])
    raise KeyError(r["tag"])


def apply(path=None):
    path = path or SCRIPT
    with open(path) as fh:
        src = fh.read()
    i = src.find(BEGIN)
    j = src.find(END)
    if i < 0 or j < 0:
        raise SystemExit("markers not found in %s" % path)
    block = build_block()
    with open(path, "w") as fh:
        fh.write(src[:i] + block + src[j + len(END):])
    return block


if __name__ == "__main__":
    b = apply()
    print("wrote %d lines into %s" % (len(b.splitlines()),
                                      os.path.relpath(SCRIPT, HERE)))
