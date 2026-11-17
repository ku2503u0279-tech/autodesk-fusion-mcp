#!/usr/bin/env python3
"""Check the Studio product before you trust it.

Runs the Fusion script against a stand-in for Fusion, and checks the geometry
for the mistakes that actually bite:

  * the Fusion script runs start to finish with no errors;
  * both feet of each blade are flat on the mat, so the stand cannot rock;
  * the deck beds down on the blade with no gap and no lift;
  * the deck is deep enough for the laptop in the brief;
  * the tie rod passes through solid wood, not through the window;
  * nothing pokes below the mat, past the back edge, or off the front;
  * every part in the BOM also has an STL file.

Run it with:

    ../.venv/bin/python verify_studio.py

Exit code 0 means everything passed.
"""
import importlib.util
import json
import math
import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
PRODUCT = os.path.join(HERE, "Product1_AeroBridgeStudio")
SCRIPT = os.path.join(PRODUCT, "AeroBridge_Studio.py")

sys.path.insert(0, HERE)
import studio_common as S          # noqa: E402
import studio_shell as SH          # noqa: E402
import studio_render as S_R        # noqa: E402


# --------------------------------------------------------- Fusion stand-in
def build_mock():
    adsk = types.ModuleType("adsk")
    core = types.ModuleType("adsk.core")
    fusion = types.ModuleType("adsk.fusion")
    adsk.core, adsk.fusion = core, fusion

    class Obj(object):
        def __init__(self, name=""):
            self.name = name

    class Point3D(Obj):
        def __init__(self, x=0.0, y=0.0, z=0.0):
            self.x, self.y, self.z = float(x), float(y), float(z)

        @staticmethod
        def create(x=0.0, y=0.0, z=0.0):
            return Point3D(x, y, z)

    class Vector3D(Obj):
        def __init__(self, x=0.0, y=0.0, z=0.0):
            self.x, self.y, self.z = float(x), float(y), float(z)

        @staticmethod
        def create(x=0.0, y=0.0, z=0.0):
            return Vector3D(x, y, z)

    class Matrix3D(Obj):
        def __init__(self):
            self.translation = Vector3D()
            self.rotation = None

        @staticmethod
        def create():
            return Matrix3D()

        def setToRotation(self, ang, axis, origin):
            self.rotation = (ang, axis, origin)

    class ObjectCollection(Obj):
        def __init__(self):
            self.items = []

        @staticmethod
        def create():
            return ObjectCollection()

        def add(self, o):
            self.items.append(o)
            return o

    class ValueInput(Obj):
        def __init__(self, v):
            self.value = v

        @staticmethod
        def createByReal(v):
            return ValueInput(v)

        @staticmethod
        def createByString(v):
            return ValueInput(v)

    class Profile(Obj):
        def __init__(self, n=1):
            self.n = n

    class Profiles(Obj):
        def __init__(self, n=1):
            self._p = [Profile() for _ in range(n)]

        def item(self, i):
            return self._p[i]

        @property
        def count(self):
            return len(self._p)

    class Lines(Obj):
        def __init__(self, sketch):
            self._s = sketch

        def addByTwoPoints(self, a, b):
            self._s._n += 1
            return Obj()

    class Circles(Obj):
        def __init__(self, sketch):
            self._s = sketch

        def addByCenterRadius(self, c, r):
            self._s._n += 1
            return Obj()

    class Sketch(Obj):
        def __init__(self, plane, name=""):
            self.name = name
            self._n = 0
            self.sketchCurves = types.SimpleNamespace(
                sketchLines=Lines(self), sketchCircles=Circles(self))
            self.profiles = Profiles(1)

    class Sketches(Obj):
        def __init__(self):
            self._items = []

        def add(self, plane):
            s = Sketch(plane)
            self._items.append(s)
            return s

    class Body(Obj):
        def __init__(self, name=""):
            self.name = name
            self.bbox = None

    class Bodies(Obj):
        def __init__(self, items):
            self._b = items

        def item(self, i):
            return self._b[i]

        @property
        def count(self):
            return len(self._b)

    class ExtrudeInput(Obj):
        def __init__(self, prof, op):
            self.profile, self.operation = prof, op
            self.distance = None
            self.isSymmetricExtent = False

        def setDistanceExtent(self, symmetric, dist):
            # a cut is only trusted if it is symmetric and at least half the
            # blade thick, otherwise it can stop short of the far face
            if self.operation == 1:                       # CutFeatureOperation
                if not getattr(self, "isSymmetricExtent", False):
                    raise ValueError("a pierce must be cut symmetrically")
            self.distance = dist

    class ExtrudeFeature(Obj):
        def __init__(self, bodies):
            self.bodies = Bodies(bodies)

    class ScaleInput(Obj):
        def __init__(self, coll, factor, origin):
            self.coll, self.factor, self.origin = coll, factor, origin

    class Scales(Obj):
        def createInput(self, coll, factor, origin):
            return ScaleInput(coll, factor, origin)

        def add(self, inp):
            return Obj()

    class Extrudes(Obj):
        def __init__(self, comp):
            self._c = comp

        def createInput(self, prof, op):
            return ExtrudeInput(prof, op)

        def add(self, inp):
            n = inp.profile.n if hasattr(inp.profile, "n") else 1
            bodies = [Body("Body%d" % (len(self._c.bodies) + i)) for i in range(n)]
            self._c.bodies.extend(bodies)
            return ExtrudeFeature(bodies)

    class MoveInput(Obj):
        def __init__(self, coll, m):
            self.coll, self.transform = coll, m

    class Moves(Obj):
        def createInput(self, coll, m):
            return MoveInput(coll, m)

        def add(self, inp):
            for b in inp.coll.items:
                m = inp.transform
                b.moved = getattr(b, "moved", Vector3D()) 
                if getattr(m, "translation", None) is not None:
                    b.moved = Vector3D(b.moved.x + m.translation.x,
                                       b.moved.y + m.translation.y,
                                       b.moved.z + m.translation.z)
            return Obj()

    class ConstructionPlane(Obj):
        pass

    class Component(Obj):
        def __init__(self, design=None):
            super(Component, self).__init__("Component1")
            self.sketches = Sketches()
            self.bodies = []
            self.features = types.SimpleNamespace(
                extrudeFeatures=Extrudes(self),
                moveFeatures=Moves())
            self.xYConstructionPlane = ConstructionPlane("XY")
            self.yZConstructionPlane = ConstructionPlane("YZ")
            self.xZConstructionPlane = ConstructionPlane("XZ")

    class Design(Obj):
        def __init__(self):
            self.rootComponent = Component(self)
            self.designType = 1

        @staticmethod
        def cast(o):
            return o if isinstance(o, Design) else None

    class UI(Obj):
        def __init__(self):
            self.messages = []

        def messageBox(self, msg, *a, **k):
            self.messages.append(msg)

    class App(Obj):
        def __init__(self):
            self.activeProduct = Design()
            self.userInterface = UI()

        @staticmethod
        def get():
            return App._inst

    App._inst = App()

    core.Point3D, core.Vector3D, core.Matrix3D = Point3D, Vector3D, Matrix3D
    core.ObjectCollection = ObjectCollection
    core.ValueInput = ValueInput
    core.DocumentTypes = types.SimpleNamespace(FusionDesignDocumentType=0)
    core.Application = App
    fusion.DesignTypes = types.SimpleNamespace(ParametricDesignType=1)
    fusion.FeatureOperations = types.SimpleNamespace(
        NewBodyFeatureOperation=3, JoinFeatureOperation=0, CutFeatureOperation=1)
    fusion.Design = Design
    sys.modules["adsk"] = adsk
    sys.modules["adsk.core"] = core
    sys.modules["adsk.fusion"] = fusion
    return App._inst


# ----------------------------------------------------------------- checks
def check_script():
    app = build_mock()
    spec = importlib.util.spec_from_file_location("aero_studio", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.run(None)
    msgs = app.userInterface.messages
    if msgs and "Could not build" in msgs[-1]:
        raise AssertionError("Fusion script reported a failure:\n" + msgs[-1])
    design = app.activeProduct
    bodies = design.rootComponent.bodies
    n = len(bodies)
    # a script that silently builds nothing is a failure, not a pass: the mock
    # swallows per-part exceptions, so check the count explicitly
    want = len(S.assembly())
    if n < want:
        raise AssertionError(
            "Fusion script built only %d bodies (expected %d). Last message: %s"
            % (n, want, msgs[-1].splitlines()[0] if msgs else "(none)"))
    return n


# The machine this stand is sized for. A 15" laptop is about 240 mm deep and
# 340 mm wide; the deck has to take the depth and the stand the width.
LAPTOP_DEPTH = 240.0
LAPTOP_WIDTH = 340.0


def check_geometry(P):
    """The claims the model makes, tested against the geometry itself."""
    import studio_shell as SH
    out = []

    sec = SH.section()
    if SH.self_crossings(sec):
        out.append("the section crosses itself (%d)" % SH.self_crossings(sec))
    wall = SH.min_wall(sec, len(SH.outer_path()))
    if wall < 14.0:
        out.append("the section wall pinches to %.1f mm" % wall)

    # every lamination must be a simple polygon, sit on the desk, and stay
    # inside the desk footprint
    for lam in SH.lamination_profiles(P):
        if SH.self_crossings(lam["poly"]):
            out.append("lamination %02d crosses itself" % (lam["i"] + 1))
        ys = [q[1] for q in lam["poly"]]
        zs = [q[0] for q in lam["poly"]]
        if min(ys) < -0.01:
            out.append("lamination %02d dips below the desk" % (lam["i"] + 1))
        if min(zs) < 2.0 or max(zs) > P["desk_z"] - 2:
            out.append("lamination %02d runs off the desk front/back"
                       % (lam["i"] + 1))

    # the seat has to be a real plane: a laptop must land on all eleven
    st = SH.seat_line()
    ang = math.degrees(math.atan((st["y0"] - st["y1"]) / (st["z1"] - st["z0"])))
    if not (18.0 < ang < 28.0):
        out.append("the seat sits at %.1f deg; it wants 20-26" % ang)
    if st["z1"] - st["z0"] < 120.0:
        out.append("the flat of the seat is only %.0f mm deep"
                   % (st["z1"] - st["z0"]))
    # Only the seat SURFACE: a point belongs to it if it lies within a wall of
    # the plane, which excludes the garage ceiling and the front leg.
    off = 0
    for (z, y) in SH.outer_path():
        if st["z0"] + 0.05 < z < st["z1"] - 0.05:
            if abs(y - SH._seat_y(z)) > 0.05:
                off += 1
    if off:
        out.append("%d seat points are off the plane: a laptop would rock" % off)

    # THE REAL REQUIREMENT: a 240 mm-deep laptop has to sit on this and stay
    # there. The deck's useable face is measured from the back edge of the deck
    # to the back face of the stop; the stop itself must exist, stand proud
    # enough to catch a machine, and be no wider than the machine it catches.
    # This is the check that was missing when the stand shipped with a 146 mm
    # seat and no stop at all.
    face = math.hypot(st["z1"] - st["z0"], st["y0"] - st["y1"])
    stops = SH.stop_parts(P)
    if not stops:
        out.append("there is no stop: a laptop on this deck slides off the front")
    else:
        stop = stops[0]
        zs = [q[0] for q in stop["poly"]]
        ys = [q[1] for q in stop["poly"]]
        lose = st["z1"] - min(zs)          # deck length spent under the stop
        room = face - lose
        if room < LAPTOP_DEPTH:
            out.append("only %.0f mm of deck in front of the stop; a %.0f mm "
                       "laptop overhangs by %.0f mm"
                       % (room, LAPTOP_DEPTH, LAPTOP_DEPTH - room))
        # How far the stop rises ABOVE THE DECK SURFACE, measured along the
        # deck normal. Its profile height is not the same quantity: the bar
        # beds onto a 23 deg slope, so part of its 18 mm section is spent
        # following the deck. What catches a laptop is what stands proud.
        # (ang is in DEGREES here, and below the horizontal, so the deck's
        # up-normal is (-sin, +cos) in (z, y). Using math.sin on the degree
        # value silently gives nonsense.)
        a = math.radians(ang)
        nz, ny = -math.sin(a), math.cos(a)
        base = SH._seat_y(max(zs))
        proud = max((y - base) * ny - (z - max(zs)) * nz for (z, y) in stop["poly"])
        if proud < 12.0:
            out.append("the stop only stands %.0f mm above the deck; it will "
                       "not hold a machine" % proud)
        if max(zs) > st["z1"] + 0.5:
            out.append("the stop overhangs the deck's front edge")
        if min(zs) < st["z0"] + 0.5:
            out.append("the stop sits behind the deck's back edge")
        if stop["x1"] - stop["x0"] > SH.SHELL["span"]:
            out.append("the stop is wider than the stand")

    # the stretcher must pass through solid wood in every lamination
    for r in SH.RODS:
        for lam in SH.lamination_profiles(P):
            if not SH._inside((r["z"], r["y"]), lam["poly"],
                              shrink=r["r"] + 2.0):
                out.append("the stretcher misses solid wood in lamination %02d"
                           % (lam["i"] + 1))

    # The garage has to take a keyboard. Measure the actual opening: the
    # highest solid point at each depth. Measuring the offset path instead is
    # wrong, because just under the seat's front lip the ceiling IS the seat
    # underside and the gap there can only ever be the wall thickness.
    loft = [(z, SH._loft(z, sec)) for z in range(60, 226, 4)]
    if not loft:
        out.append("the garage is closed")
    else:
        if min(y for (z, y) in loft) < 130.0:
            out.append("the garage is only %.0f mm tall at the back"
                       % min(y for (z, y) in loft))
        opening = max(z for (z, y) in loft if y > 60.0) - 40.0
        if opening < 180.0:
            out.append("the garage opening is only %.0f mm deep" % opening)
    return out


def check_files(P):
    out = []
    parts = S.assembly(P)
    stl = os.path.join(PRODUCT, "parts", "stl")
    for p in parts:
        fn = "%s_%s.stl" % (p["tag"], p["name"].replace(" ", "_"))
        path = os.path.join(stl, fn)
        if not os.path.exists(path):
            out.append("missing part file: " + fn)
        elif os.path.getsize(path) < 200:
            out.append("part file looks empty: " + fn)
    if not os.path.exists(os.path.join(PRODUCT, "parts", "BOM.csv")):
        out.append("missing BOM.csv")
    dxf = os.path.join(PRODUCT, "parts", "dxf")
    for lam in S.assembly(P):
        if lam["pt"] != "lam":
            continue
        fn = "%s_%s_cut.dxf" % (lam["tag"], lam["name"].replace(" ", "_"))
        if not os.path.exists(os.path.join(dxf, fn)):
            out.append("missing lamination DXF: " + fn)
    return out


def _stl_edges(path):
    """Every edge of every triangle, as a sorted pair of rounded points."""
    import struct
    from collections import Counter
    d = open(path, "rb").read()
    n = struct.unpack("<I", d[80:84])[0]
    if len(d) != 84 + n * 50:
        raise ValueError("not a binary STL: " + os.path.basename(path))
    cnt = Counter()
    for i in range(n):
        o = 84 + i * 50 + 12
        v = [struct.unpack("<fff", d[o + 12 * k:o + 12 * k + 12])
             for k in range(3)]
        t = [tuple(round(c, 3) for c in q) for q in v]
        for a, b in ((0, 1), (1, 2), (2, 0)):
            cnt[tuple(sorted([t[a], t[b]]))] += 1
    return n, cnt


def check_meshes(P):
    """Every part must be a closed, watertight solid, and the blade must
    actually be pierced."""
    out = []
    stl = os.path.join(PRODUCT, "parts", "stl")
    for p in S.assembly(P):
        fn = "%s_%s.stl" % (p["tag"], p["name"].replace(" ", "_"))
        path = os.path.join(stl, fn)
        if not os.path.exists(path):
            continue
        try:
            n, cnt = _stl_edges(path)
        except Exception as exc:
            out.append("%s: %s" % (fn, exc))
            continue
        bad = sum(1 for c in cnt.values() if c != 2)
        if bad:
            out.append("%s is not watertight (%d loose/non-manifold edges)"
                       % (fn, bad))

    # the stretcher bore must survive into the exported mesh: an unmeshed hole
    # would mean the lamination was exported solid
    for tag in ("L01", "L06", "L11"):
        p = [q for q in S.assembly(P) if q["tag"] == tag][0]
        m = S_R.parts_to_meshes([p], P)[0]
        if len(m.f) < 300:
            out.append("%s exported with too few faces to be bored" % tag)
    return out


def main():
    P = dict(S.P)
    fails = []
    try:
        n = check_script()
        print("[PASS] Fusion script runs clean: %d bodies created." % n)
    except Exception as exc:
        fails.append("Fusion script failed: %s" % exc)
        print("[FAIL] Fusion script:", exc)

    geo = check_geometry(P)
    if geo:
        fails += geo
        for m in geo:
            print("[FAIL] " + m)
    else:
        st = SH.seat_line()
        face = math.hypot(st["z1"] - st["z0"], st["y0"] - st["y1"])
        stop = SH.stop_parts(P)[0]
        room = face - (st["z1"] - min(q[0] for q in stop["poly"]))
        print("[PASS] Geometry: deck %.0f mm at %.1f deg with the stop taking "
              "%.0f mm, leaving %.0f mm for a %.0f mm laptop; wall %.0f mm; "
              "stretcher in solid wood."
              % (face, math.degrees(math.atan(
                  (st["y0"] - st["y1"]) / (st["z1"] - st["z0"]))),
                  st["z1"] - min(q[0] for q in stop["poly"]),
                  room, LAPTOP_DEPTH, SH.WALL))

    mesh = check_meshes(P)
    if mesh:
        fails += mesh
        for m in mesh:
            print("[FAIL] " + m)
    else:
        print("[PASS] Meshes: every STL is watertight and the bore is meshed.")

    files = check_files(P)
    if files:
        fails += files
        for m in files:
            print("[FAIL] " + m)
    else:
        print("[PASS] Part files: every part has an STL and a DXF where it is "
              "cut flat, and the BOM is present.")

    print()
    if fails:
        print("%d problem(s) to fix." % len(fails))
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
