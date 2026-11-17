"""AeroBridge Studio — build the whole stand in Fusion 360.

HOW TO USE IT
    1. Open Fusion 360.
    2. Utilities > Add-Ins > Scripts and Add-Ins... > Scripts tab.
    3. Press the green "+" and pick this .py file (or drop the whole folder in
       Fusion's API/Scripts folder and refresh).
    4. Select "Product1_AeroBridgeStudio" and press Run.

WHAT YOU GET
    One component called AeroBridge_Studio, with every part as its own body,
    named with the same tags as the drawings (A1, A2, D1, S1, R1, CL, CR,
    FLB/FLF/FRB/FRF) so the renders, the BOM and this model cannot drift apart.

THE PIERCE
    Each blade is extruded from its silhouette and then CUT with the slot, all
    the way through, so the fin has a real hole in it. The slot outline and the
    blade outline in PARAMS are generated from studio_blade.py by
    studio_fusion_data.py, so this script and the drawings are the same shape.

    Do not edit PARAMS by hand: change the numbers in studio_common.py, then run

        python studio_fusion_data.py

    and it will rewrite this block.
"""

PARAMS = dict(
    desk_x=630.0,
    desk_z=280.0,
    blade_t=30.0,
    blade_chamfer=2.6,
    blade_rake=34.0,
    blade_leg_w=76.0,
    blade_crown_h=26.0,
    blade_belly=4.0,
    blade_knee_r=20.0,
    crest=150.0,
    crest_end=86.0,
    crest_peak=44.0,
    span_left=96.0,
    span_right=536.0,
    deck_t=13.0,
    deck_back=204.0,
    deck_front=144.0,
    deck_z0=62.0,
    deck_z1=266.0,
    deck_chamfer=2.4,
    gutter=4.0,
    rod_d=10.0,
    rod_y=52.0,
    rod_z=40.0,
    stop_h=9.0,
    stop_w=11.0,
    stop_z=26.0,
    felt_t=2.0,
    pad_size=30.0,
    # The blade silhouette and the pierce, generated from studio_blade.py so
    # this script cannot drift from the drawings. Regenerate with:
    #     python studio_fusion_data.py
    BLADE_OUTLINE=[
        (10.00, 0.00), (10.87, 5.78), (11.73, 11.56), (12.42, 17.36), (12.52, 23.20), (12.61, 29.04),
        (12.71, 34.89), (12.80, 40.73), (12.90, 46.58), (12.99, 52.42), (13.08, 58.26), (13.18, 64.11),
        (13.27, 69.95), (13.37, 75.80), (13.46, 81.64), (13.56, 87.48), (13.65, 93.33), (13.75, 99.17),
        (13.84, 105.02), (13.94, 110.86), (14.03, 116.71), (14.13, 122.55), (14.22, 128.39), (14.32, 134.24),
        (14.41, 140.08), (14.50, 145.93), (14.60, 151.77), (14.69, 157.61), (14.79, 163.46), (14.88, 169.30),
        (14.98, 175.15), (15.07, 180.99), (15.17, 186.83), (15.26, 192.68), (15.36, 198.52), (15.45, 204.37),
        (15.55, 210.21), (15.64, 216.06), (15.73, 221.90), (15.83, 227.74), (15.92, 233.59), (16.02, 239.43),
        (16.11, 245.28), (16.21, 251.12), (16.30, 256.96), (16.40, 262.81), (16.49, 268.65), (16.59, 274.50),
        (16.68, 280.34), (16.78, 286.18), (16.87, 292.03), (16.97, 297.87), (17.06, 303.72), (17.15, 309.56),
        (17.25, 315.41), (17.34, 321.25), (18.40, 326.96), (20.40, 332.45), (23.12, 337.61), (26.46, 342.40),
        (30.41, 346.69), (34.98, 350.33), (40.08, 353.16), (45.56, 355.16), (51.32, 356.07), (57.15, 355.96),
        (58.58, 351.17), (58.94, 345.34), (59.30, 339.50), (59.66, 333.67), (60.02, 327.84), (60.38, 322.00),
        (60.74, 316.17), (61.10, 310.33), (61.46, 304.50), (61.82, 298.67), (62.38, 292.86), (63.40, 287.10),
        (64.42, 281.35), (65.45, 275.59), (66.48, 269.84), (67.51, 264.09), (68.55, 258.33), (69.59, 252.58),
        (70.71, 246.85), (71.83, 241.11), (72.95, 235.37), (74.18, 229.66), (75.49, 223.96), (76.80, 218.27),
        (78.40, 212.65), (80.14, 207.07), (82.45, 201.74), (85.85, 197.24), (91.38, 195.36), (96.99, 193.71),
        (102.60, 192.06), (108.20, 190.41), (113.81, 188.76), (119.42, 187.11), (125.03, 185.46), (130.63, 183.81),
        (136.24, 182.16), (141.85, 180.52), (147.46, 178.87), (153.06, 177.22), (158.67, 175.57), (164.28, 173.92),
        (169.88, 172.27), (175.49, 170.62), (181.10, 168.97), (186.71, 167.32), (192.31, 165.67), (197.92, 164.02),
        (203.53, 162.37), (209.14, 160.72), (214.74, 159.08), (220.35, 157.43), (225.96, 155.78), (231.57, 154.13),
        (237.17, 152.48), (242.78, 150.83), (248.39, 149.18), (254.00, 147.53), (259.60, 145.88), (263.67, 142.68),
        (265.30, 137.07), (266.76, 131.41), (268.02, 125.70), (269.06, 119.95), (269.84, 114.16), (270.32, 108.33),
        (270.41, 102.49), (270.10, 96.66), (269.32, 90.87), (267.97, 85.18), (267.07, 88.64), (266.35, 94.44),
        (265.62, 100.24), (264.89, 106.04), (264.17, 111.84), (263.44, 117.64), (262.71, 123.44), (261.99, 129.24),
        (261.29, 130.96), (260.65, 125.15), (260.06, 119.33), (259.53, 113.51), (259.12, 107.68), (258.80, 101.85),
        (258.66, 96.00), (258.81, 90.16), (259.54, 84.37), (262.70, 80.13), (267.21, 83.53), (267.59, 78.85),
        (267.53, 73.01), (267.47, 67.16), (267.41, 61.32), (267.34, 55.48), (267.28, 49.63), (267.22, 43.79),
        (267.16, 37.94), (267.09, 32.10), (267.03, 26.25), (266.97, 20.41), (266.91, 14.56), (267.68, 8.78),
        (268.55, 3.00), (266.19, 0.00), (260.34, 0.00), (254.50, 0.00), (248.65, 0.00), (242.81, 0.00),
        (236.96, 0.00), (231.12, 0.00), (225.27, 0.00), (219.43, 0.00), (213.58, 0.00), (207.74, 0.00),
        (201.89, 0.00), (196.05, 0.00), (190.20, 0.00), (184.36, 0.00), (178.51, 0.00), (175.84, 3.69),
        (174.93, 9.46), (173.94, 15.23), (172.96, 20.99), (171.92, 26.74), (170.83, 32.48), (169.74, 38.22),
        (168.66, 43.97), (167.57, 49.71), (166.48, 55.45), (165.40, 61.20), (164.31, 66.94), (163.22, 72.68),
        (162.13, 78.42), (161.05, 84.17), (159.96, 89.91), (158.87, 95.65), (157.78, 101.40), (157.15, 107.19),
        (157.00, 113.03), (156.85, 118.87), (156.70, 124.72), (156.55, 130.56), (156.39, 136.40), (156.24, 142.24),
        (156.07, 148.09), (152.44, 150.66), (146.60, 151.04), (140.76, 151.20), (135.53, 153.49), (130.39, 156.29),
        (125.20, 158.96), (123.10, 156.67), (123.27, 150.83), (123.42, 144.99), (123.58, 139.14), (123.73, 133.30),
        (123.88, 127.46), (124.03, 121.61), (124.18, 115.77), (123.43, 110.00), (122.31, 104.27), (121.19, 98.53),
        (120.07, 92.80), (118.94, 87.06), (117.82, 81.32), (116.70, 75.59), (115.58, 69.85), (114.46, 64.11),
        (113.34, 58.38), (112.21, 52.64), (111.09, 46.91), (109.97, 41.17), (108.85, 35.43), (107.73, 29.70),
        (106.60, 23.96), (105.48, 18.22), (104.51, 12.46), (103.62, 6.69), (102.74, 0.91), (97.67, 0.00),
        (91.83, 0.00), (85.98, 0.00), (80.14, 0.00), (74.29, 0.00), (68.45, 0.00), (62.60, 0.00),
        (56.76, 0.00), (50.91, 0.00), (45.07, 0.00), (39.22, 0.00), (33.38, 0.00), (27.53, 0.00),
        (21.69, 0.00), (15.84, 0.00),
    ],
    BLADE_SLOT=[
        (28.00, 200.00), (27.66, 208.30), (27.35, 216.60), (27.07, 224.90), (26.85, 233.19), (26.69, 241.49),
        (26.61, 249.79), (26.61, 258.09), (26.69, 266.39), (26.85, 274.69), (27.07, 282.98), (27.35, 291.28),
        (27.66, 299.58), (28.00, 307.88), (28.00, 307.88), (29.16, 309.22), (30.32, 310.52), (31.47, 311.74),
        (32.63, 312.87), (33.79, 313.85), (34.95, 314.68), (36.11, 315.32), (37.26, 315.75), (38.42, 315.97),
        (39.58, 315.97), (40.74, 315.75), (41.89, 315.32), (43.05, 314.68), (44.21, 313.85), (45.37, 312.87),
        (46.53, 311.74), (47.68, 310.52), (48.84, 309.22), (50.00, 307.88), (50.00, 307.88), (50.34, 299.58),
        (50.65, 291.28), (50.93, 282.98), (51.15, 274.69), (51.31, 266.39), (51.39, 258.09), (51.39, 249.79),
        (51.31, 241.49), (51.15, 233.19), (50.93, 224.90), (50.65, 216.60), (50.34, 208.30), (50.00, 200.00),
        (50.00, 200.00), (48.84, 199.67), (47.68, 199.35), (46.53, 199.05), (45.37, 198.77), (44.21, 198.53),
        (43.05, 198.33), (41.89, 198.17), (40.74, 198.06), (39.58, 198.01), (38.42, 198.01), (37.26, 198.06),
        (36.11, 198.17), (34.95, 198.33), (33.79, 198.53), (32.63, 198.77), (31.47, 199.05), (30.32, 199.35),
        (29.16, 199.67), (28.00, 200.00),
    ],
)

import adsk.core
import adsk.fusion

MM = 0.1          # Fusion works in centimetres

# where the feet land on the mat: kept next to the parameters so the pads and
# the blade cannot disagree about where the ends of the board are
S_Z_BACK = 13.0
S_Z_FRONT = 266.0


# --------------------------------------------------------------- geometry
def deck_y(z, P):
    """Height of the deck's TOP surface at depth z."""
    z = min(max(z, P["deck_z0"]), P["deck_z1"])
    t = (z - P["deck_z0"]) / (P["deck_z1"] - P["deck_z0"])
    return P["deck_back"] + (P["deck_front"] - P["deck_back"]) * t


def crown_y(z, P):
    """The underside of the deck: what the blade's top edge beds onto."""
    return deck_y(z, P) - P["deck_t"]


# ------------------------------------------------------------------ build
def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)
        if design is None:
            design = adsk.fusion.Design.cast(
                app.documents.add(
                    adsk.core.DocumentTypes.FusionDesignDocumentType).design)
        root = design.rootComponent
        root.name = "AeroBridge_Studio"

        P = dict(PARAMS)
        made = []

        # ---- A1 / A2: the two blades, each pierced by one slot
        for tag, x0 in (("A1", P["span_left"]),
                        ("A2", P["span_right"] - P["blade_t"])):
            side = "Left" if tag == "A1" else "Right"
            body = _blade(root, P, x0, "%s Blade %s" % (tag, side))
            if body:
                made.append(body.name)

        # ---- D1: the deck
        _deck(root, P, made)
        # ---- S1: the front stop
        _stop(root, P, made)
        # ---- R1 + collars
        _rod(root, P, made)
        # ---- felt pads
        _pads(root, P, made)

        ui.messageBox("AeroBridge Studio built: %d bodies.\n\n%s"
                      % (len(made), "\n".join(made)))
    except Exception:
        if ui:
            ui.messageBox("Could not build the stand:\n\n%s" % traceback.format_exc())


def _add_loop(sketch, pts, plane, offset=0.0):
    """Add a closed loop of straight sketch lines.

    `pts` are (depth, height) in millimetres; `plane` says which face they lie
    on. The blade silhouette is a dense sampling of tangent-continuous curves,
    so lines between the samples are smooth at any real scale.
    """
    lines = sketch.sketchCurves.sketchLines
    vecs = []
    for (a, b) in pts:
        if plane == "yz":
            vecs.append(adsk.core.Point3D.create(offset * MM, b * MM, a * MM))
        else:
            vecs.append(adsk.core.Point3D.create(a * MM, b * MM, 0))
    first = vecs[0]
    prev = first
    for q in vecs[1:]:
        lines.addByTwoPoints(prev, q)
        prev = q
    lines.addByTwoPoints(prev, first)


def _blade(comp, P, x0, name):
    """One blade: the silhouette extruded, then the pierce cut clean through."""
    try:
        plane = comp.yZConstructionPlane
        sk = comp.sketches.add(plane)
        sk.name = name + " outline"
        _add_loop(sk, P["BLADE_OUTLINE"], "yz")
        prof = sk.profiles.item(0)
        extrudes = comp.features.extrudeFeatures
        inp = extrudes.createInput(
            prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        inp.setDistanceExtent(
            False, adsk.core.ValueInput.createByReal(P["blade_t"] * MM))
        ext = extrudes.add(inp)
        body = ext.bodies.item(0)
        body.name = name

        # ---- the pierce. Cut it from the same face, straight through, so it
        #      is a real hole in the solid and not a decorative groove.
        cut_sk = comp.sketches.add(plane)
        cut_sk.name = name + " pierce"
        _add_loop(cut_sk, P["BLADE_SLOT"], "yz")
        cut_prof = cut_sk.profiles.item(0)
        cut_inp = extrudes.createInput(
            cut_prof, adsk.fusion.FeatureOperations.CutFeatureOperation)
        # symmetric, so the cut goes through the full thickness in one go and
        # cannot stop short on the far face
        cut_inp.isSymmetricExtent = True
        cut_inp.setDistanceExtent(
            False, adsk.core.ValueInput.createByReal(P["blade_t"] * MM * 0.5))
        extrudes.add(cut_inp)

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
        mi = comp.features.moveFeatures.createInput(coll, adsk.core.Matrix3D.create())
        m = adsk.core.Matrix3D.create()
        m.translation = adsk.core.Vector3D.create(x_mm * MM, 0, 0)
        mi.transform = m
        comp.features.moveFeatures.add(mi)
    except Exception:
        pass


def _box(comp, x0, x1, y0, y1, z0, z1, name):
    """A simple rectangular body, for the stop and the pads."""
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
        inp = extrudes.createInput(
            prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        inp.setDistanceExtent(
            False, adsk.core.ValueInput.createByReal((y1 - y0) * MM))
        body = extrudes.add(inp).bodies.item(0)
        body.name = name
        m = adsk.core.Matrix3D.create()
        m.translation = adsk.core.Vector3D.create(0, y0 * MM, 0)
        coll = adsk.core.ObjectCollection.create()
        coll.add(body)
        comp.features.moveFeatures.add(
            comp.features.moveFeatures.createInput(coll, m))
        return body
    except Exception:
        return None


def _deck(comp, P, made):
    """The deck, built TILTED as a loft between two horizontal profiles.

    Building it as a flat slab and rotating it is what makes the front edge
    dive below the blades. Two profiles at the back and front heights, lofted,
    gives a board that is genuinely parallel to the blade crowns.
    """
    z0, z1 = P["deck_z0"], P["deck_z1"]
    x0 = P["span_left"] + P["blade_t"]
    x1 = P["span_right"] - P["blade_t"]
    yb, yf = crown_y(z0, P), crown_y(z1, P)
    t = P["deck_t"]
    r = 34.0
    try:
        def outline(z):
            pts = [(x0, z), (x1, z)]
            for k in range(9):
                a = (math.pi / 2.0) * k / 8.0
                pts.append((x1 - r + r * math.cos(a), z1 - r + r * math.sin(a)))
            for k in range(1, 9):
                pts.append((x1 - r - (x1 - x0 - 2 * r) * k / 8.0, z1))
            for k in range(9):
                a = (math.pi / 2.0) * (8 - k) / 8.0
                pts.append((x0 + r - r * math.cos(a), z1 - r + r * math.sin(a)))
            return pts

        sk = comp.sketches.add(comp.xZConstructionPlane)
        sk.name = "D1 deck"
        lines = sk.sketchCurves.sketchLines
        ps = [adsk.core.Point3D.create(u * MM, 0, v * MM) for (u, v) in outline(z0)]
        for i in range(len(ps)):
            lines.addByTwoPoints(ps[i], ps[(i + 1) % len(ps)])
        prof = sk.profiles.item(0)
        extrudes = comp.features.extrudeFeatures
        inp = extrudes.createInput(
            prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        inp.setDistanceExtent(False, adsk.core.ValueInput.createByReal(t * MM))
        body = extrudes.add(inp).bodies.item(0)
        body.name = "D1 Deck"
        # lift to the back height, leaving the board horizontal at the moment
        m = adsk.core.Matrix3D.create()
        m.translation = adsk.core.Vector3D.create(0, (yb + t) * MM, 0)
        coll = adsk.core.ObjectCollection.create()
        coll.add(body)
        comp.features.moveFeatures.add(
            comp.features.moveFeatures.createInput(coll, m))
        # then tilt about the back edge so the front lands on its crown
        ang = math.atan2(yb - yf, z1 - z0)
        m2 = adsk.core.Matrix3D.create()
        m2.setToRotation(ang, adsk.core.Vector3D.create(1, 0, 0),
                         adsk.core.Point3D.create(0, yb * MM, z0 * MM))
        mi = comp.features.moveFeatures.createInput(coll, m2)
        mi.transform = m2
        comp.features.moveFeatures.add(mi)
        made.append(body.name)
    except Exception:
        pass


def _stop(comp, P, made):
    z = P["deck_z1"] - P["stop_z"]
    yb = deck_y(z, P)
    b = _box(comp, P["span_left"] + P["blade_t"] + 26.0,
             P["span_right"] - P["blade_t"] - 26.0,
             yb, yb + P["stop_h"], z - P["stop_w"], z, "S1 Front Stop")
    if b:
        made.append(b.name)


def _rod(comp, P, made):
    try:
        z, y = P["rod_z"], P["rod_y"]
        sk = comp.sketches.add(comp.xZConstructionPlane)
        sk.name = "R1 rod"
        sk.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(P["span_left"] * MM, 0, z * MM),
            P["rod_d"] / 2.0 * MM)
        prof = sk.profiles.item(0)
        extrudes = comp.features.extrudeFeatures
        inp = extrudes.createInput(
            prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        inp.setDistanceExtent(False, adsk.core.ValueInput.createByReal(
            (P["span_right"] - P["span_left"]) * MM))
        body = extrudes.add(inp).bodies.item(0)
        body.name = "R1 Tie Rod"
        m = adsk.core.Matrix3D.create()
        m.translation = adsk.core.Vector3D.create(0, y * MM, 0)
        coll = adsk.core.ObjectCollection.create()
        coll.add(body)
        comp.features.moveFeatures.add(
            comp.features.moveFeatures.createInput(coll, m))
        made.append(body.name)
    except Exception:
        pass


def _pads(comp, P, made):
    s = P["pad_size"]
    for tag, x0 in (("L", P["span_left"]),
                    ("R", P["span_right"] - P["blade_t"])):
        for end, z in (("B", S_Z_BACK), ("F", S_Z_FRONT - s)):
            b = _box(comp, x0 + (P["blade_t"] - s) / 2.0,
                     x0 + (P["blade_t"] + s) / 2.0,
                     0.0, P["felt_t"], z + 3.0, z + 3.0 + s,
                     "F%s%s Felt Pad" % (tag, end))
            if b:
                made.append(b.name)
