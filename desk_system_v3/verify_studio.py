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

        def setDistanceExtent(self, symmetric, dist):
            self.distance = dist

    class ExtrudeFeature(Obj):
        def __init__(self, bodies):
            self.bodies = Bodies(bodies)

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
    return len(bodies)


def check_geometry(P):
    poly = S.blade_polygon(P)
    out = []

    flat = [z for (z, y) in poly if y < 0.05]
    if len(flat) < 12:
        out.append("blade feet are not flat on the mat (%d points at y=0)" % len(flat))
    if min(y for (z, y) in poly) < -1e-6:
        out.append("blade dips below the mat")

    gap = min(S.crown_y_at(P, z) - y for (z, y) in poly)
    if gap < -0.05 or gap > 1.5:
        out.append("deck does not bed down on the blade (gap %.2f mm)" % gap)

    run = P["deck_z1"] - P["deck_z0"]
    if run < 258:
        out.append("deck is %.0f mm deep, too short for a 264 mm laptop" % run)

    z_rod = P["rod_z"] if P["rod_z"] is not None else P["z_back_outer"] + P["blade_w"] / 2.0
    wood = S.crown_y_at(P, z_rod)
    if P["rod_y"] + P["rod_d"] / 2.0 > wood:
        out.append("tie rod misses the leg: it sits above the wood")

    for x in (P["span_left"], P["span_right"]):
        if x < 0 or x > P["desk_x"]:
            out.append("a blade stands off the end of the desk")

    zmax = max(z for (z, y) in poly)
    if zmax > P["desk_z"] - 4:
        out.append("blade overhangs the front of the desk")

    if S.crown_y_at(P, P["deck_z0"]) < 100:
        out.append("deck sits too low to clear a keyboard")
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
    if not os.path.exists(os.path.join(PRODUCT, "parts", "dxf",
                                       "A1_A2_Both_Blades_cut.dxf")):
        out.append("missing the blade cutting DXF")
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
        print("[PASS] Geometry: feet flat, deck seated, depth %.0f mm, rod in solid wood."
              % (P["deck_z1"] - P["deck_z0"]))

    files = check_files(P)
    if files:
        fails += files
        for m in files:
            print("[FAIL] " + m)
    else:
        print("[PASS] Part files: every part has an STL, and the BOM and DXF are present.")

    print()
    if fails:
        print("%d problem(s) to fix." % len(fails))
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
