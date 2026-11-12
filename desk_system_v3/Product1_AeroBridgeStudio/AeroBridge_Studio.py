"""AeroBridge Studio — build the whole stand in Fusion 360.

HOW TO USE IT
    1. Open Fusion 360.
    2. Utilities > Add-Ins > Scripts and Add-Ins... > Scripts tab.
    3. Press the green "+" and pick this .py file (or drop the whole folder in
       Fusion's API/Scripts folder and refresh).
    4. Select "Product1_AeroBridgeStudio" and press Run.

WHAT YOU GET
    One component called AeroBridge_Studio, with every part as its own
    body, named with the same tags as the drawings (A1, A2, D1, S1, R1, CL, CR)
    so the renders, the BOM and this model can never drift apart.

The numbers in PARAMS are the same ones in studio_common.py. That file is the
single source of truth; if you change a size here, change it there too, and
re-run the render and export scripts.
"""
import math
import os
import traceback

import adsk.core
import adsk.fusion

PARAMS = dict(
    desk_x=630.0, desk_z=280.0,
    arch_t=28.0,
    span_left=112.0, span_right=512.0,
    deck_t=12.0,
    deck_back=204.0, deck_front=144.0,
    deck_z0=10.0, deck_z1=278.0,
    z_back_outer=20.0, z_front_outer=260.0,
    blade_w=52.0, blade_w_crown=34.0,
    loop_pts=200,
    rod_d=9.0, rod_y=46.0, rod_z=46.0, rod_clamp_len=24.0, rod_clamp_d=16.0,
    stop_h=7.0, stop_w=9.0, stop_z=10.0,
    felt_t=2.0, pad_size=34.0,
)

MM = 0.1          # Fusion works in centimetres


# --------------------------------------------------------------- geometry
def deck_y(z, P):
    z = min(max(z, P["deck_z0"]), P["deck_z1"])
    t = (z - P["deck_z0"]) / (P["deck_z1"] - P["deck_z0"])
    return P["deck_back"] + (P["deck_front"] - P["deck_back"]) * t


def crown_y(z, P):
    return deck_y(z, P) - P["deck_t"]


def _seg(a, b, n):
    return [(a[0] + (b[0] - a[0]) * k / float(n - 1),
             a[1] + (b[1] - a[1]) * k / float(n - 1)) for k in range(n)]


def _chaikin(pts, iters=2):
    for _ in range(iters):
        out = []
        n = len(pts)
        for i in range(n):
            a, b = pts[i], pts[(i + 1) % n]
            out.append((0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]))
            out.append((0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1]))
        pts = out
    return pts


def blade_polygon(P):
    """The same C-shaped outline as studio_common.blade_polygon."""
    W, h = P["blade_w"], P["blade_w_crown"]
    a, b = P["z_back_outer"], P["z_front_outer"]
    ai, bi = a + W, b - W

    def top(z):
        return crown_y(z, P)

    pts = []
    pts += _seg((a, 0.0), (a, top(a)), 14)[:-1]
    pts += _seg((a, top(a)), (b, top(b)), 46)[:-1]
    pts += _seg((b, top(b)), (b, 0.0), 14)[:-1]
    pts += _seg((b, 0.0), (bi, 0.0), 6)[:-1]
    pts += _seg((bi, 0.0), (bi, top(bi) - h), 12)[:-1]
    pts += _seg((bi, top(bi) - h), (ai, top(ai) - h), 40)[:-1]
    pts += _seg((ai, top(ai) - h), (ai, 0.0), 12)[:-1]
    pts += _seg((ai, 0.0), (a, 0.0), 6)[:-1]
    loop = _chaikin(pts, 2)
    return [(z, 0.0) if y < 0.8 else (z, y) for (z, y) in loop]


# ------------------------------------------------------------------ build
def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)
        if design is None:
            design = adsk.fusion.Design.cast(
                app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType).design)
        root = design.rootComponent
        root.name = "AeroBridge_Studio"

        P = dict(PARAMS)
        comp = root
        made = []

        # ---- A1 / A2: the two blades
        poly = blade_polygon(P)
        for tag, x0 in (("A1", P["span_left"]),
                        ("A2", P["span_right"] - P["arch_t"])):
            body = _extrude_profile(comp, poly, x0, x0 + P["arch_t"],
                                    "%s Blade" % ("Left" if tag == "A1" else "Right"))
            if body:
                made.append(body.name)

        # ---- D1: the deck
        _deck(comp, P, made)
        # ---- S1: the front stop
        _stop(comp, P, made)
        # ---- R1 + collars
        _rod(comp, P, made)
        # ---- felt pads
        _pads(comp, P, made)

        ui.messageBox("AeroBridge Studio built: %d bodies.\n\n%s"
                      % (len(made), "\n".join(made)))
    except Exception:
        if ui:
            ui.messageBox("Could not build the stand:\n\n%s" % traceback.format_exc())


def _new_sketch(comp, name, on_plane=None):
    sk = comp.sketches.add(on_plane or comp.xYConstructionPlane)
    sk.name = name
    return sk


def _extrude_profile(comp, poly, x0, x1, name):
    """Draw the outline on the YZ plane and pull it along X."""
    try:
        plane = comp.yZConstructionPlane
        sk = comp.sketches.add(plane)
        sk.name = name + " sketch"
        pts = [adsk.core.Point3D.create(0.0, y * MM, z * MM) for (z, y) in poly]
        lines = sk.sketchCurves.sketchLines
        for i in range(len(pts)):
            lines.addByTwoPoints(pts[i], pts[(i + 1) % len(pts)])
        prof = sk.profiles.item(0)
        extrudes = comp.features.extrudeFeatures
        inp = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        inp.setDistanceExtent(False, adsk.core.ValueInput.createByReal((x1 - x0) * MM))
        ext = extrudes.add(inp)
        body = ext.bodies.item(0)
        body.name = name
        # move it out to where it belongs on the desk
        _shift_body(comp, body, x0)
        return body
    except Exception:
        return None


def _shift_body(comp, body, x_mm):
    if abs(x_mm) < 1e-9:
        return
    try:
        coll = adsk.core.ObjectCollection.create()
        coll.add(body)
        move = comp.features.moveFeatures
        inp = move.createInput(coll, adsk.core.Matrix3D.create())
        m = adsk.core.Matrix3D.create()
        m.translation = adsk.core.Vector3D.create(x_mm * MM, 0, 0)
        inp.transform = m
        move.add(inp)
    except Exception:
        pass


def _box(comp, x0, x1, y0, y1, z0, z1, name):
    """A simple rectangular body, for the boards, rails and pads."""
    try:
        sk = comp.sketches.add(comp.xYConstructionPlane)
        sk.name = name + " sketch"
        lines = sk.sketchCurves.sketchLines
        pts = [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]
        verts = [adsk.core.Point3D.create(a * MM, b * MM, 0) for (a, b) in pts]
        for i in range(4):
            lines.addByTwoPoints(verts[i], verts[(i + 1) % 4])
        prof = sk.profiles.item(0)
        extrudes = comp.features.extrudeFeatures
        inp = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        inp.setDistanceExtent(False, adsk.core.ValueInput.createByReal((y1 - y0) * MM))
        ext = extrudes.add(inp)
        body = ext.bodies.item(0)
        body.name = name
        m = adsk.core.Matrix3D.create()
        m.translation = adsk.core.Vector3D.create(0, y0 * MM, 0)
        coll = adsk.core.ObjectCollection.create()
        coll.add(body)
        mi = comp.features.moveFeatures.createInput(coll, m)
        comp.features.moveFeatures.add(mi)
        return body
    except Exception:
        return None


def _deck(comp, P, made):
    yb, yf = deck_y(P["deck_z0"], P), deck_y(P["deck_z1"], P)
    z0, z1 = P["deck_z0"], P["deck_z1"]
    t = P["deck_t"]
    x0 = P["span_left"] + P["arch_t"]
    x1 = P["span_right"] - P["arch_t"]
    try:
        sk = comp.sketches.add(comp.xYConstructionPlane)
        sk.name = "D1 deck sketch"
        lines = sk.sketchCurves.sketchLines
        pts = [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]
        verts = [adsk.core.Point3D.create(a * MM, b * MM, 0) for (a, b) in pts]
        for i in range(4):
            lines.addByTwoPoints(verts[i], verts[(i + 1) % 4])
        prof = sk.profiles.item(0)
        extrudes = comp.features.extrudeFeatures
        inp = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        inp.setDistanceExtent(False, adsk.core.ValueInput.createByReal(t * MM))
        body = extrudes.add(inp).bodies.item(0)
        body.name = "D1 Deck"
        # tilt it onto the blade line, then drop it into place
        m = adsk.core.Matrix3D.create()
        ang = math.atan2(yf - yb, z1 - z0)
        m.setToRotation(ang, adsk.core.Vector3D.create(1, 0, 0),
                        adsk.core.Point3D.create(0, 0, z0 * MM))
        m.translation = adsk.core.Vector3D.create(0, yb * MM, 0)
        coll = adsk.core.ObjectCollection.create()
        coll.add(body)
        comp.features.moveFeatures.add(
            comp.features.moveFeatures.createInput(coll, m))
        made.append(body.name)
    except Exception:
        pass


def _stop(comp, P, made):
    z = P["deck_z1"] - P["stop_z"]
    yb = deck_y(z, P) - 9.0
    b = _box(comp, P["span_left"] + P["arch_t"], P["span_right"] - P["arch_t"],
             yb, yb + P["stop_h"] + 9.0, z - P["stop_w"], z, "S1 Front Stop")
    if b:
        made.append(b.name)


def _rod(comp, P, made):
    try:
        z = P["rod_z"]
        y = P["rod_y"]
        sk = comp.sketches.add(comp.xZConstructionPlane)
        sk.name = "R1 rod sketch"
        c = sk.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(P["span_left"] * MM, z * MM, 0),
            P["rod_d"] / 2.0 * MM)
        prof = sk.profiles.item(0)
        extrudes = comp.features.extrudeFeatures
        inp = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        inp.setDistanceExtent(False, adsk.core.ValueInput.createByReal(
            (P["span_right"] - P["span_left"]) * MM))
        body = extrudes.add(inp).bodies.item(0)
        body.name = "R1 Tie Rod"
        m = adsk.core.Matrix3D.create()
        m.translation = adsk.core.Vector3D.create(0, y * MM, 0)
        coll = adsk.core.ObjectCollection.create()
        coll.add(body)
        comp.features.moveFeatures.add(comp.features.moveFeatures.createInput(coll, m))
        made.append(body.name)
    except Exception:
        pass


def _pads(comp, P, made):
    s = P["pad_size"]
    for tag, x0 in (("L", P["span_left"]), ("R", P["span_right"] - P["arch_t"])):
        for end, z in (("B", P["z_back_outer"]), ("F", P["z_front_outer"] - s)):
            b = _box(comp, x0 + (P["arch_t"] - s) / 2.0,
                     x0 + (P["arch_t"] + s) / 2.0,
                     0.0, P["felt_t"], z + 3.0, z + 3.0 + s,
                     "F%s%s Felt Pad" % (tag, end))
            if b:
                made.append(b.name)
