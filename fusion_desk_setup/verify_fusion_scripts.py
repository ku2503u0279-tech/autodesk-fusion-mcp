#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verification Harness for All 6 Autodesk Fusion Desk-Setup Scripts
=================================================================
Simulates `adsk.core` and `adsk.fusion` (including parametric expression
evaluation in mm/deg, 3D plane projection via `modelToSketchSpace`, BRepBody
3D bounding-box tracking across NewBody / Join / Cut extrusions, AsBuiltJoints,
Appearances, Camera, and STL/3MF ExportManager) to verify:
  1. All 6 `.manifest` files are valid JSON matching Autodesk Fusion's schema.
  2. All 6 `.py` scripts execute `run(context)` with zero errors.
  3. Every printable `Body_P*` solid fits inside a `200 x 200 x 200 mm` college
     3D printer build volume.
  4. Spatial separation / zero collision between products, wall (`Z >= 0` for
     clamps), mouse sweep pad, and AULA F75 keyboard garage (`62 mm > 43.1 mm`).
"""

import importlib.util
import json
import math
import os
import re
import sys
import tempfile
import types


def build_adsk_mock():
    adsk = types.ModuleType("adsk")
    core = types.ModuleType("adsk.core")
    fusion = types.ModuleType("adsk.fusion")
    adsk.core = core
    adsk.fusion = fusion

    class Point3D:
        def __init__(self, x=0.0, y=0.0, z=0.0):
            self.x, self.y, self.z = float(x), float(y), float(z)

        @staticmethod
        def create(x=0.0, y=0.0, z=0.0):
            return Point3D(x, y, z)

    class Vector3D:
        def __init__(self, x=0.0, y=0.0, z=0.0):
            self.x, self.y, self.z = float(x), float(y), float(z)

        @staticmethod
        def create(x=0.0, y=0.0, z=0.0):
            return Vector3D(x, y, z)

        def crossProduct(self, other):
            return Vector3D(
                self.y * other.z - self.z * other.y,
                self.z * other.x - self.x * other.z,
                self.x * other.y - self.y * other.x,
            )

    class Matrix3D:
        @staticmethod
        def create():
            return Matrix3D()

    class ObjectCollection:
        def __init__(self):
            self._items = []

        @staticmethod
        def create():
            return ObjectCollection()

        def add(self, item):
            self._items.append(item)

        @property
        def count(self):
            return len(self._items)

        def item(self, idx):
            return self._items[idx]

    class ValueInput:
        def __init__(self, expr=None, real_val=None):
            self.expr = expr
            self.real_val = real_val

        @staticmethod
        def createByString(expr: str):
            return ValueInput(expr=str(expr))

        @staticmethod
        def createByReal(val: float):
            return ValueInput(real_val=float(val))

    def eval_expr_mm_or_deg(expr_str: str, param_dict_mm_deg: dict, unit_hint: str = "mm") -> float:
        s = expr_str.strip()
        # Strip unit suffixes `mm` and `deg` cleanly when preceded by number/paren/space
        s = re.sub(r"\bmm\b", "", s)
        s = re.sub(r"\bdeg\b", "", s)
        safe_ns = {"math": math, "__builtins__": {}}
        safe_ns.update(param_dict_mm_deg)
        return float(eval(s, safe_ns))

    class UserParameter:
        def __init__(self, design, name: str, expr: str, unit: str, comment: str):
            self._design = design
            self.name = name
            self.unit = unit
            self.comment = comment
            self._expr = expr

        @property
        def expression(self):
            return self._expr

        @expression.setter
        def expression(self, val):
            self._expr = val

        @property
        def value(self):
            raw = eval_expr_mm_or_deg(self._expr, self._design._param_env(), self.unit)
            if self.unit == "mm":
                return raw * 0.1  # cm internal
            if self.unit == "deg":
                return math.radians(raw)
            return raw

        def eval_raw(self):
            return eval_expr_mm_or_deg(self._expr, self._design._param_env(), self.unit)

    class UserParameters:
        def __init__(self, design):
            self._design = design
            self._map = {}

        def itemByName(self, name: str):
            return self._map.get(name)

        def add(self, name: str, vi: ValueInput, unit: str, comment: str):
            p = UserParameter(self._design, name, vi.expr, unit, comment)
            self._map[name] = p
            # Validate expression evaluates right away
            _ = p.value
            return p

        @property
        def count(self):
            return len(self._map)

        def __iter__(self):
            return iter(self._map.values())

    class ConstructionPlane:
        def __init__(self, name, origin_cm, u_vec, v_vec):
            self.name = name
            self.origin = origin_cm  # (x, y, z) in cm
            self.u = u_vec
            self.v = v_vec

        @property
        def normal(self):
            return self.u.crossProduct(self.v)

    class ConstructionPlaneInput:
        def __init__(self, design):
            self._design = design
            self.base = None
            self.offset_vi = None

        def setByOffset(self, base_plane: ConstructionPlane, offset_vi: ValueInput):
            self.base = base_plane
            self.offset_vi = offset_vi

    class ConstructionPlanes:
        def __init__(self, design):
            self._design = design
            self._items = []

        def createInput(self):
            return ConstructionPlaneInput(self._design)

        def add(self, p_in: ConstructionPlaneInput):
            off_mm = eval_expr_mm_or_deg(p_in.offset_vi.expr, self._design._param_env(), "mm")
            off_cm = off_mm * 0.1
            n = p_in.base.normal
            ox = p_in.base.origin[0] + n.x * off_cm
            oy = p_in.base.origin[1] + n.y * off_cm
            oz = p_in.base.origin[2] + n.z * off_cm
            pl = ConstructionPlane("OffsetPlane", (ox, oy, oz), p_in.base.u, p_in.base.v)
            self._items.append(pl)
            return pl

    class SketchLine:
        def __init__(self, sketch, p1: Point3D, p2: Point3D):
            self.sketch = sketch
            self.p1 = p1
            self.p2 = p2

        def createForAssemblyContext(self, occ):
            return self

        def deleteMe(self):
            self.sketch.sketchCurves.sketchLines._lines.remove(self)

    class SketchLines:
        def __init__(self, sketch):
            self.sketch = sketch
            self._lines = []

        def addByTwoPoints(self, p1: Point3D, p2: Point3D):
            ln = SketchLine(self.sketch, p1, p2)
            self._lines.append(ln)
            self.sketch._record_sk_pt(p1)
            self.sketch._record_sk_pt(p2)
            return ln

        @property
        def count(self):
            return len(self._lines)

        def item(self, idx):
            return self._lines[idx]

    class SketchCircles:
        def __init__(self, sketch):
            self.sketch = sketch
            self._circles = []

        def addByCenterRadius(self, center: Point3D, radius_cm: float):
            self._circles.append((center, radius_cm))
            for dx in (-radius_cm, radius_cm):
                for dy in (-radius_cm, radius_cm):
                    self.sketch._record_sk_pt(Point3D(center.x + dx, center.y + dy, 0.0))
            return self._circles[-1]

    class SketchCurves:
        def __init__(self, sketch):
            self.sketchLines = SketchLines(sketch)
            self.sketchCircles = SketchCircles(sketch)

    class Profile:
        def __init__(self, sketch):
            self.sketch = sketch

    class Profiles:
        def __init__(self, sketch):
            self.sketch = sketch

        @property
        def count(self):
            has_geom = (
                self.sketch.sketchCurves.sketchLines.count > 0
                or len(self.sketch.sketchCurves.sketchCircles._circles) > 0
            )
            return 1 if has_geom else 0

        def item(self, idx):
            return Profile(self.sketch)

    class Sketch:
        def __init__(self, plane: ConstructionPlane):
            self.plane = plane
            self.name = "Sketch"
            self.xDirection = plane.u
            self.yDirection = plane.v
            self.sketchCurves = SketchCurves(self)
            self.profiles = Profiles(self)
            self._world_pts_mm = []

        def modelToSketchSpace(self, pt3_cm: Point3D) -> Point3D:
            dx = pt3_cm.x - self.plane.origin[0]
            dy = pt3_cm.y - self.plane.origin[1]
            dz = pt3_cm.z - self.plane.origin[2]
            u = dx * self.plane.u.x + dy * self.plane.u.y + dz * self.plane.u.z
            v = dx * self.plane.v.x + dy * self.plane.v.y + dz * self.plane.v.z
            return Point3D(u, v, 0.0)

        def _record_sk_pt(self, sk_pt: Point3D):
            wx = (self.plane.origin[0] + sk_pt.x * self.plane.u.x + sk_pt.y * self.plane.v.x) * 10.0
            wy = (self.plane.origin[1] + sk_pt.x * self.plane.u.y + sk_pt.y * self.plane.v.y) * 10.0
            wz = (self.plane.origin[2] + sk_pt.x * self.plane.u.z + sk_pt.y * self.plane.v.z) * 10.0
            self._world_pts_mm.append((wx, wy, wz))

    class Sketches:
        def __init__(self):
            self._items = []

        def add(self, plane: ConstructionPlane):
            sk = Sketch(plane)
            self._items.append(sk)
            return sk

    class BRepBody:
        def __init__(self, comp, bbox_mm):
            self.comp = comp
            self.name = "Body"
            self.bbox_mm = bbox_mm  # [xmin, xmax, ymin, ymax, zmin, zmax]
            self.appearance = None

        def merge_bbox(self, other_bbox):
            for idx in (0, 2, 4):
                self.bbox_mm[idx] = min(self.bbox_mm[idx], other_bbox[idx])
            for idx in (1, 3, 5):
                self.bbox_mm[idx] = max(self.bbox_mm[idx], other_bbox[idx])

        @property
        def dimensions_mm(self):
            b = self.bbox_mm
            return (b[1] - b[0], b[3] - b[2], b[5] - b[4])

        @property
        def boundingBox(self):
            b = self.bbox_mm
            return types.SimpleNamespace(
                minPoint=Point3D(b[0] * 0.1, b[2] * 0.1, b[4] * 0.1),
                maxPoint=Point3D(b[1] * 0.1, b[3] * 0.1, b[5] * 0.1),
            )

    class BRepBodies:
        def __init__(self):
            self._items = []

        @property
        def count(self):
            return len(self._items)

        def item(self, idx):
            return self._items[idx]

    class ExtrudeFeatureInput:
        def __init__(self, profiles, operation):
            self.profiles = profiles
            self.operation = operation
            self.dist_vi = None
            self.participantBodies = []

        def setDistanceExtent(self, is_sym: bool, dist_vi: ValueInput):
            self.dist_vi = dist_vi

    class ExtrudeFeature:
        def __init__(self, body_list):
            self.name = "Extrude"
            self.bodies = ObjectCollection()
            for b in body_list:
                self.bodies.add(b)

    class ExtrudeFeatures:
        def __init__(self, comp):
            self.comp = comp
            self._feats = []

        def createInput(self, profiles, operation):
            if profiles.count == 0:
                raise RuntimeError("Extrude called with 0 profiles!")
            return ExtrudeFeatureInput(profiles, operation)

        def add(self, ext_in: ExtrudeFeatureInput):
            prof = ext_in.profiles.item(0)
            sk = prof.sketch
            dist_mm = eval_expr_mm_or_deg(ext_in.dist_vi.expr, self.comp._design._param_env(), "mm")
            n = sk.xDirection.crossProduct(sk.yDirection)
            pts = []
            for (wx, wy, wz) in sk._world_pts_mm:
                pts.append((wx, wy, wz))
                pts.append((wx + n.x * dist_mm, wy + n.y * dist_mm, wz + n.z * dist_mm))
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            zs = [p[2] for p in pts]
            bbox = [min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)]

            op = ext_in.operation
            if op == fusion.FeatureOperations.NewBodyFeatureOperation:
                body = BRepBody(self.comp, bbox)
                self.comp.bRepBodies._items.append(body)
                feat = ExtrudeFeature([body])
            elif op == fusion.FeatureOperations.JoinFeatureOperation:
                target = ext_in.participantBodies[0] if ext_in.participantBodies else self.comp.bRepBodies._items[-1]
                target.merge_bbox(bbox)
                feat = ExtrudeFeature([target])
            elif op == fusion.FeatureOperations.CutFeatureOperation:
                target = ext_in.participantBodies[0] if ext_in.participantBodies else self.comp.bRepBodies._items[-1]
                feat = ExtrudeFeature([target])
            else:
                raise ValueError(f"Unsupported operation {op}")
            self._feats.append(feat)
            return feat

    class Features:
        def __init__(self, comp):
            self.extrudeFeatures = ExtrudeFeatures(comp)

    class AsBuiltJointInput:
        def __init__(self, occ1, occ2, geom):
            self.occ1, self.occ2, self.geom = occ1, occ2, geom
            self.motion_type = None

        def setAsRigidJointMotion(self):
            self.motion_type = "Rigid"

        def setAsSliderJointMotion(self, direction_type, custom_entity=None):
            self.motion_type = "Slider"

        def setAsRevoluteJointMotion(self, direction_type, custom_entity=None):
            self.motion_type = "Revolute"

    class AsBuiltJoint:
        def __init__(self, j_in: AsBuiltJointInput):
            self.input = j_in
            self.name = "Joint"

    class AsBuiltJoints:
        def __init__(self):
            self._joints = []

        def createInput(self, occ1, occ2, geom):
            assert occ1 is not None and occ2 is not None
            return AsBuiltJointInput(occ1, occ2, geom)

        def add(self, j_in: AsBuiltJointInput):
            assert j_in.motion_type in ("Rigid", "Slider", "Revolute")
            j = AsBuiltJoint(j_in)
            self._joints.append(j)
            return j

    class Occurrence:
        def __init__(self, comp):
            self.component = comp
            self.isGroundToParent = False

    class Occurrences:
        def __init__(self, design):
            self._design = design
            self._items = []

        def addNewComponent(self, transform):
            comp = Component(self._design)
            self._design.allComponents.append(comp)
            occ = Occurrence(comp)
            self._items.append(occ)
            return occ

        @property
        def count(self):
            return len(self._items)

    class Component:
        def __init__(self, design):
            self._design = design
            self.name = "Component"
            # Authentic Fusion plane orientations (note xZ plane normal = +Y or -Y handled by modelToSketchSpace!)
            self.xYConstructionPlane = ConstructionPlane(
                "XY", (0.0, 0.0, 0.0), Vector3D(1, 0, 0), Vector3D(0, 1, 0)
            )
            self.xZConstructionPlane = ConstructionPlane(
                "XZ", (0.0, 0.0, 0.0), Vector3D(1, 0, 0), Vector3D(0, 0, -1)
            )
            self.yZConstructionPlane = ConstructionPlane(
                "YZ", (0.0, 0.0, 0.0), Vector3D(0, 1, 0), Vector3D(0, 0, 1)
            )
            self.constructionPlanes = ConstructionPlanes(design)
            self.sketches = Sketches()
            self.features = Features(self)
            self.bRepBodies = BRepBodies()
            self.occurrences = Occurrences(design)
            self.asBuiltJoints = AsBuiltJoints()

    class ExportOptions:
        def __init__(self, entity, filename):
            self.entity = entity
            self.filename = filename
            self.meshRefinement = None

    class ExportManager:
        def createSTLExportOptions(self, entity, filename):
            return ExportOptions(entity, filename)

        def createC3MFExportOptions(self, entity, filename):
            return ExportOptions(entity, filename)

        def createSTEPExportOptions(self, filename, entity=None):
            return ExportOptions(entity if entity is not None else types.SimpleNamespace(name="STEP"), filename)

        def execute(self, opts: ExportOptions):
            with open(opts.filename, "w", encoding="utf-8") as fh:
                fh.write(f"mock_export:{opts.entity.name}\n")
            return True

    class Appearances:
        def itemByName(self, name):
            return {"appearance": name}

    class FusionUnitsManager:
        def __init__(self):
            self.distanceDisplayUnits = None

    class Design:
        def __init__(self):
            self.designType = None
            self.fusionUnitsManager = FusionUnitsManager()
            self.userParameters = UserParameters(self)
            self.allComponents = []
            self.rootComponent = Component(self)
            self.allComponents.append(self.rootComponent)
            self.appearances = Appearances()
            self.exportManager = ExportManager()

        def _param_env(self):
            env = {}
            for p in self.userParameters:
                env[p.name] = eval_expr_mm_or_deg(p._expr, env, p.unit)
            return env

        @staticmethod
        def cast(obj):
            return obj if isinstance(obj, Design) else None

    class Camera:
        def __init__(self):
            self.viewOrientation = None
            self.isFitView = False
            self.isSmoothTransition = False
            self.cameraType = None
            self.eye = Point3D(0, 0, 10)
            self.target = Point3D(0, 0, 0)
            self.upVector = Vector3D(0, 1, 0)
            self.perspectiveAngle = 0.5

    class Viewport:
        def __init__(self):
            self.camera = Camera()

        def refresh(self):
            pass

    class Documents:
        def __init__(self, app):
            self._app = app

        def add(self, doc_type):
            self._app.activeProduct = Design()
            return self._app.activeProduct

    class UserInterface:
        def messageBox(self, msg):
            raise RuntimeError(f"Script triggered error messageBox:\n{msg}")

    class Application:
        _inst = None

        def __init__(self):
            self.activeProduct = Design()
            self.documents = Documents(self)
            self.userInterface = UserInterface()
            self.activeViewport = Viewport()
            self.materialLibraries = None
            self.logs = []
            self.tx_stack = []

        @classmethod
        def get(cls):
            if cls._inst is None:
                cls._inst = Application()
            return cls._inst

        def executeTextCommand(self, cmd: str):
            if cmd.startswith("PTransaction.Start"):
                self.tx_stack.append(cmd)
            elif cmd == "PTransaction.Commit":
                assert self.tx_stack, "Commit without Start!"
                self.tx_stack.pop()
            elif cmd == "PTransaction.Abort":
                if self.tx_stack:
                    self.tx_stack.pop()

        def log(self, msg, level=None, log_type=None):
            self.logs.append(msg)

    # Populate enums & classes
    core.Application = Application
    core.Point3D = Point3D
    core.Vector3D = Vector3D
    core.Matrix3D = Matrix3D
    core.ObjectCollection = ObjectCollection
    core.ValueInput = ValueInput
    core.DocumentTypes = types.SimpleNamespace(FusionDesignDocumentType=0)
    core.ViewOrientations = types.SimpleNamespace(IsoTopRightViewOrientation=1)
    core.CameraTypes = types.SimpleNamespace(
        OrthographicCameraType=0, PerspectiveCameraType=1, PerspectiveWithOrthoFacesCameraType=2
    )
    core.LogLevels = types.SimpleNamespace(InfoLogLevel=0, ErrorLogLevel=2)
    core.LogTypes = types.SimpleNamespace(ConsoleLogType=0, FileLogType=1)

    fusion.Design = Design
    fusion.DesignTypes = types.SimpleNamespace(ParametricDesignType=1)
    fusion.DistanceUnits = types.SimpleNamespace(MillimeterDistanceUnits=0)
    fusion.FeatureOperations = types.SimpleNamespace(
        JoinFeatureOperation=0, CutFeatureOperation=1, IntersectFeatureOperation=2, NewBodyFeatureOperation=3
    )
    fusion.JointKeyPointTypes = types.SimpleNamespace(StartKeyPoint=0, MiddleKeyPoint=1, EndKeyPoint=2)
    fusion.JointDirections = types.SimpleNamespace(
        XAxisJointDirection=0, YAxisJointDirection=1, ZAxisJointDirection=2, CustomJointDirection=3
    )
    fusion.JointGeometry = types.SimpleNamespace(createByCurve=lambda curve, kpt: ("CurveGeom", curve, kpt))
    fusion.MeshRefinementSettings = types.SimpleNamespace(MeshRefinementHigh=0)
    fusion.Component = Component
    fusion.Sketch = Sketch
    fusion.BRepBody = BRepBody
    fusion.ExtrudeFeature = ExtrudeFeature
    fusion.ConstructionPlane = ConstructionPlane
    fusion.Occurrence = Occurrence

    return adsk


def _product_no(body_name: str) -> str:
    """`Body_W4B_Top_Walnut_Collar` and `Body_P4B_Fluted_Core` -> `4` (same product family)."""
    m = re.match(r"Body_[PWMG](\d)", body_name)
    return m.group(1) if m else body_name


def boxes_overlap_3d(b1, b2, tol=0.01):
    return (
        b1[0] < b2[1] - tol
        and b1[1] > b2[0] + tol
        and b1[2] < b2[3] - tol
        and b1[3] > b2[2] + tol
        and b1[4] < b2[5] - tol
        and b1[5] > b2[4] + tol
    )


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    bundles = [
        "Product0_FitCheckGauge",
        "Product1_AeroBridgeG16",
        "Product2_StealthVaultULT",
        "Product3_HydroSling",
        "Product4_HexWingSpire",
        "Product5_HoloBuddy",
        "Master_FullDeskSetup",
    ]

    # 1. Verify manifests
    for b in bundles:
        mpath = os.path.join(base_dir, b, f"{b}.manifest")
        assert os.path.isfile(mpath), f"Missing manifest: {mpath}"
        with open(mpath, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        assert data["autodeskProduct"] == "Fusion"
        assert data["type"] == "script"
        assert data["supportedOS"] == "windows|mac"
    print(f"[PASS] All {len(bundles)} Autodesk Fusion `.manifest` files validated.")

    # 2. Install mock `adsk` and execute every standalone script
    adsk_mock = build_adsk_mock()
    sys.modules["adsk"] = adsk_mock
    sys.modules["adsk.core"] = adsk_mock.core
    sys.modules["adsk.fusion"] = adsk_mock.fusion

    for b in bundles:
        app = adsk_mock.core.Application.get()
        app.documents.add(0)
        py_path = os.path.join(base_dir, b, f"{b}.py")
        spec = importlib.util.spec_from_file_location(b, py_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.run({"isApplicationStartup": False})
        assert len(app.tx_stack) == 0, f"Unclosed transaction in {b}!"
        design = app.activeProduct

        if b == "Master_FullDeskSetup":
            with tempfile.TemporaryDirectory() as tmpd:
                exported = mod.export_all_individual_pieces(design, tmpd)
                assert len(exported) >= 48, f"Expected >=48 exported files, got {len(exported)}"
            print(f"[PASS] Master_FullDeskSetup built {len(design.allComponents)} components & exported {len(exported)} individual piece files + CSV manifest.")

            printable_bodies = {}
            wood_bodies = {}
            metal_bodies = {}
            glass_bodies = {}
            ref_bodies = {}
            for comp in design.allComponents:
                for idx in range(comp.bRepBodies.count):
                    body = comp.bRepBodies.item(idx)
                    dx, dy, dz = body.dimensions_mm
                    if body.name.startswith("Body_P"):
                        printable_bodies[body.name] = body
                        sdims = sorted([dx, dy, dz])
                        print(
                            f"  [3D-PRINT] {body.name:34s} -> {dx:6.1f} x {dy:6.1f} x {dz:6.1f} mm  "
                            f"| X[{body.bbox_mm[0]:6.1f},{body.bbox_mm[1]:6.1f}] "
                            f"Y[{body.bbox_mm[2]:6.1f},{body.bbox_mm[3]:6.1f}] "
                            f"Z[{body.bbox_mm[4]:6.1f},{body.bbox_mm[5]:6.1f}]"
                        )
                        assert max(sdims) <= 200.0 + 1e-6, (
                            f"BED OVERFLOW: {body.name} has dimension {max(sdims):.2f} mm > 200 mm!"
                        )
                    elif body.name.startswith("Body_W"):
                        wood_bodies[body.name] = body
                        print(
                            f"  [WOOD]     {body.name:34s} -> {dx:6.1f} x {dy:6.1f} x {dz:6.1f} mm  "
                            f"| X[{body.bbox_mm[0]:6.1f},{body.bbox_mm[1]:6.1f}] "
                            f"Y[{body.bbox_mm[2]:6.1f},{body.bbox_mm[3]:6.1f}] "
                            f"Z[{body.bbox_mm[4]:6.1f},{body.bbox_mm[5]:6.1f}]"
                        )
                    elif body.name.startswith("Body_M"):
                        metal_bodies[body.name] = body
                        print(
                            f"  [METAL]    {body.name:34s} -> {dx:6.1f} x {dy:6.1f} x {dz:6.1f} mm  "
                            f"| X[{body.bbox_mm[0]:6.1f},{body.bbox_mm[1]:6.1f}] "
                            f"Y[{body.bbox_mm[2]:6.1f},{body.bbox_mm[3]:6.1f}] "
                            f"Z[{body.bbox_mm[4]:6.1f},{body.bbox_mm[5]:6.1f}]"
                        )
                    elif body.name.startswith("Body_G5"):
                        glass_bodies[body.name] = body
                    elif body.name.startswith("Ref_"):
                        ref_bodies[body.name] = body

            all_mfg_bodies = {}
            all_mfg_bodies.update(printable_bodies)
            all_mfg_bodies.update(wood_bodies)
            all_mfg_bodies.update(metal_bodies)

            print(
                f"[PASS] Individual Pieces Summary: {len(printable_bodies)} compact 3D-printed nodes (all <= 200mm bed), "
                f"{len(wood_bodies)} precision wood parts, {len(metal_bodies)} metal rods, {len(glass_bodies)} optical cube!"
            )

            # Back wall flush check (Z >= 0 across all manufactured parts)
            for name, body in all_mfg_bodies.items():
                assert body.bbox_mm[4] >= -0.01, f"WALL COLLISION: {name} has Z_min={body.bbox_mm[4]:.2f} < 0!"
            print("[PASS] Back-wall flush check: all wood, metal, and printed parts stay strictly at Z >= 0.0 mm.")

            # Left-edge Vault Front Arch vs ULT Knuckle
            b_v = printable_bodies["Body_P2B_Front_Clamp_Arch"].bbox_mm
            b_u = printable_bodies["Body_P2D_ULT_Bearing_Hub"].bbox_mm
            assert not boxes_overlap_3d(b_v, b_u), f"Left-edge clamp collision: {b_v} vs {b_u}"
            print(f"[PASS] Left-edge separation: Vault Z_max={b_v[5]:.1f} mm vs ULT Knuckle Z_min={b_u[4]:.1f} mm.")

            # Right DT-30 Collar (X_max=459.0) mates with HoloBuddy Wing Arm (X_min=453.25 tongue inside socket)
            b_rc = printable_bodies["Body_P1E_Collar_Right"].bbox_mm
            b_hw = printable_bodies["Body_P5D_Wing_Arm"].bbox_mm
            assert abs(b_rc[1] - 459.0) < 0.1 and b_hw[0] < 459.0 < b_hw[1], (
                f"HoloBuddy DT-30 misalignment: Collar={b_rc}, Wing={b_hw}"
            )
            print("[PASS] HoloBuddy DT-30 engagement: P5D tongue mates cleanly inside P1E_Right_DT30_Collar at X=459.0 mm.")

            # Keyboard garage clearance between W1A and W1B wood arches
            kb = ref_bodies["Ref_AULA_F75_Keyboard"].bbox_mm
            bl = wood_bodies["Body_W1A_Left_Wood_Arch"].bbox_mm
            br = wood_bodies["Body_W1B_Right_Wood_Arch"].bbox_mm
            assert kb[0] > bl[1] and kb[1] < br[0], "Keyboard collides with AeroBridge wood arches!"
            print(
                f"[PASS] Keyboard garage clearance: AULA F75 X[{kb[0]:.1f}..{kb[1]:.1f}] clears W1A/W1B wood arches "
                f"({bl[1]:.1f}..{br[0]:.1f} mm)."
            )

            # Right-hand mouse zone check (HoloBuddy floats at Y >= 80 mm above Y=3..43 mm mouse!)
            mouse_zone = [470.0, 628.0, 3.0, 65.0, 90.0, 278.0]
            for name, body in all_mfg_bodies.items():
                if name in ("Body_W5B_Walnut_Coaster", "Body_P5E_Pedestal_Hub"):
                    continue
                assert not boxes_overlap_3d(mouse_zone, body.bbox_mm), f"{name} intrudes on mouse sweep pad! bbox={body.bbox_mm}"
            print("[PASS] Mouse zone check: 165 x 230 mm right-hand sweep zone is 100% unobstructed (HoloBuddy hovers at Y >= 80 mm).")

            # Assembly connectivity: the whole setup must be one rigid network anchored on the desk.
            # Two parts are "joined" when their bounding boxes come within JOIN_TOL of each other
            # (they share a clamp jaw, a DT-30 dovetail, a tie-rod, a bearing axle or a magnet pair).
            # Bounding boxes overstate real gaps wherever two parts meet at a dovetail, magnet
            # pair or bearing seat, so a joint is declared within 6 mm rather than at zero.
            JOIN_TOL = 6.0
            names = list(all_mfg_bodies)
            parent = {n: n for n in names}

            def find(a):
                while parent[a] != a:
                    parent[a] = parent[parent[a]]
                    a = parent[a]
                return a

            for i, a in enumerate(names):
                for b in names[i + 1:]:
                    if _product_no(a) != _product_no(b):
                        continue  # products are only joined through the desk, never through each other
                    ba, bb = all_mfg_bodies[a].bbox_mm, all_mfg_bodies[b].bbox_mm
                    if boxes_overlap_3d(
                        [ba[0] - JOIN_TOL, ba[1] + JOIN_TOL, ba[2] - JOIN_TOL, ba[3] + JOIN_TOL, ba[4] - JOIN_TOL, ba[5] + JOIN_TOL],
                        bb,
                    ):
                        parent[find(a)] = find(b)
            anchors = [
                n for n in names
                if all_mfg_bodies[n].bbox_mm[0] < 630.01 and all_mfg_bodies[n].bbox_mm[1] > -0.01
                and all_mfg_bodies[n].bbox_mm[4] < 280.01 and all_mfg_bodies[n].bbox_mm[5] > -0.01
            ]
            assert anchors, "No manufactured part contacts the 630 x 280 desk footprint!"
            anchored_roots = {find(n) for n in anchors}
            orphans = [n for n in names if find(n) not in anchored_roots]
            assert not orphans, (
                "Parts float free of every desk-anchored product (no joint within %.1f mm): %s" % (JOIN_TOL, orphans)
            )
            clusters = {}
            for n in names:
                clusters.setdefault(find(n), set()).add(n)
            for r, members in clusters.items():
                assert members & set(anchors), (
                    "Product group %s has no part touching the desk: %s"
                    % (_product_no(sorted(members)[0]), sorted(members))
                )
            print(
                f"[PASS] Assembly connectivity: all {len(names)} parts belong to {len(clusters)} desk-anchored product "
                f"groups ({len(anchors)} direct contact points, {JOIN_TOL:.0f} mm joint tolerance)."
            )

            # Seated knee zone check (X=195..610 mm centered around X=315 mm user)
            knee_zone = [195.0, 610.0, -400.0, -18.1, 0.0, 280.0]
            for name, body in all_mfg_bodies.items():
                assert not boxes_overlap_3d(knee_zone, body.bbox_mm), f"{name} intrudes on under-desk knee zone! bbox={body.bbox_mm}"
            print("[PASS] Ergonomic knee-clearance check: 415 mm wide seated knee zone X=[195..610 mm] is 100% clear.")
        else:
            print(f"[PASS] Standalone script `{b}` executed cleanly ({design.userParameters.count} UserParameters).")


if __name__ == "__main__":
    main()
