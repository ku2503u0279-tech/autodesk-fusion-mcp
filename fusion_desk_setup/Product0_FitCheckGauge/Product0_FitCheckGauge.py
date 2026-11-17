# -*- coding: utf-8 -*-
"""
Product 0 — 6-in-1 College Lab Fit-Check Calibration Gauge
===========================================================
Print this ~14g (~22-minute) coupon FIRST at your college 3D printing lab before
committing filament to Products 1–4.

Verifies 6 critical manufacturing interfaces in one compact test block:
  1. Desk + Mat Edge Jaw (`table_thickness + mat_thickness + 2*clamp_pad_t`)
  2. Shared `DT-30` (30 mm, 60 deg) Female Dovetail + Detachable Male Test Slider
  3. `608` Ball Bearing Press-Fit Bore (`22.0 + bearing_bore_clear` mm) + Axle Pin
  4. `6 x 3 mm` N52 Neodymium Magnet Press Pocket (`6.0 + magnet_clear` mm)
  5. `M3` (`4.0 mm` bore) & `M4` (`5.6 mm` bore) Brass Heat-Set Insert Bosses
  6. `2.4 GHz` USB-A Receiver Slip Slot (`12.4 x 4.8 mm`)

Architecture follows `ku2503u0279-tech/autodesk-fusion-mcp`:
  - `guides/fusion-design-guide.md` §§4, 5, 6, 7, 8, 11, 12
  - `AutodeskFusionMCP.manifest` & `lib/fusionAddInUtils/general_utils.py`
"""

import math
import traceback
import adsk.core
import adsk.fusion


# ---------------------------------------------------------------------------
# Shared Parametric & Coordinate Helpers (Internal Fusion API unit = cm)
# ---------------------------------------------------------------------------

def mm(val_mm: float) -> float:
    """Convert millimeters to Fusion internal centimeters."""
    return float(val_mm) * 0.1


def ensure_param(design: adsk.fusion.Design, name: str, expr: str, unit: str, comment: str) -> float:
    """Idempotently add or update a named UserParameter and return its value in mm (or deg)."""
    params = design.userParameters
    existing = params.itemByName(name)
    if existing:
        existing.expression = expr
        existing.comment = comment
        p = existing
    else:
        p = params.add(name, adsk.core.ValueInput.createByString(expr), unit, comment)
    if unit == "mm":
        return p.value * 10.0
    if unit == "deg":
        return math.degrees(p.value)
    return p.value


def pt_sk(sketch: adsk.fusion.Sketch, x_mm: float, y_mm: float, z_mm: float) -> adsk.core.Point3D:
    """Map a 3D point (in mm) into the given sketch's local 2D coordinate space."""
    return sketch.modelToSketchSpace(adsk.core.Point3D.create(mm(x_mm), mm(y_mm), mm(z_mm)))


def extrude_sign(sketch: adsk.fusion.Sketch, dx: float, dy: float, dz: float) -> int:
    """Return +1 if sketch normal aligns with (dx, dy, dz), else -1."""
    n = sketch.xDirection.crossProduct(sketch.yDirection)
    dot = n.x * dx + n.y * dy + n.z * dz
    return 1 if dot >= 0.0 else -1


def collect_all_profiles(sketch: adsk.fusion.Sketch) -> adsk.core.ObjectCollection:
    """Collect every closed profile in a sketch into an ObjectCollection."""
    col = adsk.core.ObjectCollection.create()
    for i in range(sketch.profiles.count):
        col.add(sketch.profiles.item(i))
    return col


def add_extrude(
    comp: adsk.fusion.Component,
    sketch: adsk.fusion.Sketch,
    expr: str,
    direction_xyz: tuple,
    operation: int,
    name: str,
    target_body: adsk.fusion.BRepBody = None,
) -> adsk.fusion.ExtrudeFeature:
    """Create a named parametric one-sided extrusion along `direction_xyz`."""
    profiles = collect_all_profiles(sketch)
    ext_feats = comp.features.extrudeFeatures
    ext_input = ext_feats.createInput(profiles, operation)
    sign = extrude_sign(sketch, *direction_xyz)
    signed_expr = expr if sign > 0 else f"-({expr})"
    ext_input.setDistanceExtent(False, adsk.core.ValueInput.createByString(signed_expr))
    if target_body is not None:
        ext_input.participantBodies = [target_body]
    feat = ext_feats.add(ext_input)
    feat.name = name
    return feat


def make_offset_plane(
    comp: adsk.fusion.Component, base_plane, offset_expr: str, name: str
) -> adsk.fusion.ConstructionPlane:
    """Create a named parametric offset ConstructionPlane."""
    planes = comp.constructionPlanes
    p_in = planes.createInput()
    p_in.setByOffset(base_plane, adsk.core.ValueInput.createByString(offset_expr))
    plane = planes.add(p_in)
    plane.name = name
    return plane


def draw_polygon_xy(sketch: adsk.fusion.Sketch, pts_xy_mm: list, z_mm: float = 0.0):
    """Draw a closed polygon on an XY-parallel sketch using 3D-mapped coordinates."""
    lines = sketch.sketchCurves.sketchLines
    n = len(pts_xy_mm)
    for i in range(n):
        x1, y1 = pts_xy_mm[i]
        x2, y2 = pts_xy_mm[(i + 1) % n]
        lines.addByTwoPoints(pt_sk(sketch, x1, y1, z_mm), pt_sk(sketch, x2, y2, z_mm))


def register_parameters(design: adsk.fusion.Design) -> dict:
    """Register all parametric variables used by the Fit-Check Gauge."""
    v = {}
    v["table_thickness"] = ensure_param(design, "table_thickness", "18.0 mm", "mm", "Measured wood tabletop thickness")
    v["mat_thickness"] = ensure_param(design, "mat_thickness", "3.0 mm", "mm", "Full-surface desk mat thickness")
    v["clamp_pad_t"] = ensure_param(design, "clamp_pad_t", "2.0 mm", "mm", "Soft non-marring pad thickness per jaw")
    v["fit_clearance"] = ensure_param(design, "fit_clearance", "0.25 mm", "mm", "Sliding dovetail & assembly gap")
    v["bearing_od"] = ensure_param(design, "bearing_od", "22.0 mm", "mm", "608 ball bearing outer diameter")
    v["bearing_id"] = ensure_param(design, "bearing_id", "8.0 mm", "mm", "608 ball bearing bore diameter")
    v["bearing_w"] = ensure_param(design, "bearing_w", "7.0 mm", "mm", "608 ball bearing width")
    v["bearing_bore_clear"] = ensure_param(design, "bearing_bore_clear", "0.15 mm", "mm", "Press-fit diametral allowance for 608 bore")
    v["magnet_dia"] = ensure_param(design, "magnet_dia", "6.0 mm", "mm", "N52 disc magnet nominal diameter")
    v["magnet_h"] = ensure_param(design, "magnet_h", "3.0 mm", "mm", "N52 disc magnet nominal thickness")
    v["magnet_clear"] = ensure_param(design, "magnet_clear", "0.15 mm", "mm", "Press-fit diametral allowance for magnets")
    v["m3_insert_od"] = ensure_param(design, "m3_insert_od", "4.0 mm", "mm", "M3 brass heat-set insert pilot hole dia")
    v["m4_insert_od"] = ensure_param(design, "m4_insert_od", "5.6 mm", "mm", "M4 brass heat-set insert pilot hole dia")
    v["dt30_width"] = ensure_param(design, "dt30_width", "30.0 mm", "mm", "Shared DT-30 dovetail root width")
    v["dt30_depth"] = ensure_param(design, "dt30_depth", "6.0 mm", "mm", "Shared DT-30 dovetail engagement depth")
    v["gauge_length"] = ensure_param(design, "gauge_length", "58.0 mm", "mm", "Overall X length of Fit-Check Gauge")
    v["gauge_depth"] = ensure_param(design, "gauge_depth", "38.0 mm", "mm", "Overall Z extrusion depth of Gauge")
    return v


def build_product(design: adsk.fusion.Design, parent_comp: adsk.fusion.Component = None) -> adsk.fusion.Occurrence:
    """Build Product 0 (Fit-Check Gauge + Male DT-30 Test Plug) inside a new Component."""
    if parent_comp is None:
        parent_comp = design.rootComponent

    v = register_parameters(design)

    # Create top-level assembly component for Product 0
    assy_occ = parent_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    assy_comp = assy_occ.component
    assy_comp.name = "Product0_FitCheckGauge"

    # ---- Sub-Component A: Main Gauge Block (58 x 43 x 38 mm) ----
    body_occ = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    body_comp = body_occ.component
    body_comp.name = "P0A_Gauge_Main_Block"

    jaw_gap = v["table_thickness"] + v["mat_thickness"] + 2.0 * v["clamp_pad_t"] + 0.4
    wall = 8.0
    total_h = jaw_gap + 2.0 * wall  # ~41.4 mm
    gx = v["gauge_length"]          # 58.0 mm
    jaw_reach = 18.0

    # 1. C-shaped main block profile on XY plane (extruded along +Z by gauge_depth)
    sk_base = body_comp.sketches.add(body_comp.xYConstructionPlane)
    sk_base.name = "Sk_Gauge_CClamp_Profile"
    clean_c_pts = [
        (0.0, 0.0),
        (gx, 0.0),
        (gx, wall),
        (gx - jaw_reach, wall),
        (gx - jaw_reach, wall + jaw_gap),
        (gx, wall + jaw_gap),
        (gx, total_h),
        (0.0, total_h),
    ]
    draw_polygon_xy(sk_base, clean_c_pts, 0.0)
    # Add parametric height & width reference dimensions
    ext_main = add_extrude(
        body_comp,
        sk_base,
        "gauge_depth",
        (0, 0, 1),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
        "Ext_Gauge_Main_Block",
    )
    main_body = ext_main.bodies.item(0)
    main_body.name = "Body_P0A_Gauge_Block"

    # 2. Cut Female DT-30 Dovetail along left face (X = 0..dt30_depth, centered at Y = total_h/2)
    dt_d = v["dt30_depth"]                   # 6.0 mm
    dt_half_base = 0.5 * (v["dt30_width"] + 2.0 * v["fit_clearance"])
    dt_flare = dt_d / math.tan(math.radians(60.0))  # 60-deg dovetail side wall
    dt_half_neck = dt_half_base - dt_flare
    ymid = 0.5 * total_h

    sk_dt_fem = body_comp.sketches.add(body_comp.xYConstructionPlane)
    sk_dt_fem.name = "Sk_DT30_Female_Slot"
    draw_polygon_xy(
        sk_dt_fem,
        [
            (-0.5, ymid - dt_half_neck),
            (dt_d, ymid - dt_half_base),
            (dt_d, ymid + dt_half_base),
            (-0.5, ymid + dt_half_neck),
        ],
        0.0,
    )
    add_extrude(
        body_comp,
        sk_dt_fem,
        "gauge_depth + 1 mm",
        (0, 0, 1),
        adsk.fusion.FeatureOperations.CutFeatureOperation,
        "Ext_Cut_DT30_Female",
        main_body,
    )

    # 3. Cut 608 Bearing Bore, 6x3 Magnet Pocket, M3/M4 Heat-Set Holes & USB-A Slot on Front Face (Z = gauge_depth)
    front_plane = make_offset_plane(body_comp, body_comp.xYConstructionPlane, "gauge_depth", "Plane_Front_Test_Face")

    # 3a. 608 Bearing Pocket (depth = bearing_w + 0.2 mm)
    sk_brg = body_comp.sketches.add(front_plane)
    sk_brg.name = "Sk_608_Bearing_Pocket"
    brg_r = 0.5 * (v["bearing_od"] + v["bearing_bore_clear"])
    sk_brg.sketchCurves.sketchCircles.addByCenterRadius(pt_sk(sk_brg, 23.0, 26.5, v["gauge_depth"]), mm(brg_r))
    add_extrude(
        body_comp,
        sk_brg,
        "bearing_w + 0.2 mm",
        (0, 0, -1),
        adsk.fusion.FeatureOperations.CutFeatureOperation,
        "Ext_Cut_608_Pocket",
        main_body,
    )

    # 3b. Concentric 608 Axle Test Pin rising back out from bottom of pocket
    pin_plane = make_offset_plane(
        body_comp, body_comp.xYConstructionPlane, "gauge_depth - bearing_w - 0.2 mm", "Plane_608_Pin_Base"
    )
    sk_pin = body_comp.sketches.add(pin_plane)
    sk_pin.name = "Sk_608_Axle_Pin"
    pin_r = 0.5 * (v["bearing_id"] - 0.12)
    sk_pin.sketchCurves.sketchCircles.addByCenterRadius(
        pt_sk(sk_pin, 23.0, 26.5, v["gauge_depth"] - v["bearing_w"] - 0.2), mm(pin_r)
    )
    add_extrude(
        body_comp,
        sk_pin,
        "bearing_w + 1.5 mm",
        (0, 0, 1),
        adsk.fusion.FeatureOperations.JoinFeatureOperation,
        "Ext_Join_608_Axle_Pin",
        main_body,
    )

    # 3c. 6x3 mm Magnet Press-Fit Pocket
    sk_mag = body_comp.sketches.add(front_plane)
    sk_mag.name = "Sk_Magnet_6x3_Pocket"
    mag_r = 0.5 * (v["magnet_dia"] + v["magnet_clear"])
    sk_mag.sketchCurves.sketchCircles.addByCenterRadius(pt_sk(sk_mag, 12.0, 8.5, v["gauge_depth"]), mm(mag_r))
    add_extrude(
        body_comp,
        sk_mag,
        "magnet_h + 0.15 mm",
        (0, 0, -1),
        adsk.fusion.FeatureOperations.CutFeatureOperation,
        "Ext_Cut_Magnet_Pocket",
        main_body,
    )

    # 3d. M3 and M4 Heat-Set Insert Pilot Holes (8 mm deep)
    sk_ins = body_comp.sketches.add(front_plane)
    sk_ins.name = "Sk_M3_M4_Insert_Bores"
    sk_ins.sketchCurves.sketchCircles.addByCenterRadius(
        pt_sk(sk_ins, 23.0, 8.5, v["gauge_depth"]), mm(0.5 * v["m3_insert_od"])
    )
    sk_ins.sketchCurves.sketchCircles.addByCenterRadius(
        pt_sk(sk_ins, 33.5, 8.5, v["gauge_depth"]), mm(0.5 * v["m4_insert_od"])
    )
    add_extrude(
        body_comp,
        sk_ins,
        "8.5 mm",
        (0, 0, -1),
        adsk.fusion.FeatureOperations.CutFeatureOperation,
        "Ext_Cut_HeatSet_Bores",
        main_body,
    )

    # 3e. USB-A 2.4G Dongle Slip-Fit Test Pocket (12.4 x 4.8 x 11 mm)
    sk_usb = body_comp.sketches.add(front_plane)
    sk_usb.name = "Sk_USBA_Dongle_Slot"
    draw_polygon_xy(
        sk_usb,
        [
            (16.8, 39.2),
            (29.2, 39.2),
            (29.2, 34.4),
            (16.8, 34.4),
        ],
        v["gauge_depth"],
    )
    add_extrude(
        body_comp,
        sk_usb,
        "11.0 mm",
        (0, 0, -1),
        adsk.fusion.FeatureOperations.CutFeatureOperation,
        "Ext_Cut_USBA_Slot",
        main_body,
    )

    # ---- Sub-Component B: Detachable Male DT-30 Test Slider ----
    plug_occ = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    plug_comp = plug_occ.component
    plug_comp.name = "P0B_DT30_Male_Slider"

    m_d = dt_d - v["fit_clearance"]
    m_half_base = 0.5 * v["dt30_width"]
    m_half_neck = m_half_base - (m_d / math.tan(math.radians(60.0)))

    sk_plug = plug_comp.sketches.add(plug_comp.xYConstructionPlane)
    sk_plug.name = "Sk_DT30_Male_Slider"
    draw_polygon_xy(
        sk_plug,
        [
            (-10.0, ymid - 16.0),
            (0.0, ymid - 16.0),
            (0.0, ymid - m_half_neck),
            (m_d, ymid - m_half_base),
            (m_d, ymid + m_half_base),
            (0.0, ymid + m_half_neck),
            (0.0, ymid + 16.0),
            (-10.0, ymid + 16.0),
        ],
        0.0,
    )
    ext_plug = add_extrude(
        plug_comp,
        sk_plug,
        "24.0 mm",
        (0, 0, 1),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
        "Ext_DT30_Male_Slider",
    )
    plug_body = ext_plug.bodies.item(0)
    plug_body.name = "Body_P0B_DT30_Slider"

    # ---- Slider Joint between Male DT-30 Plug and Main Gauge Block ----
    sk_jref = body_comp.sketches.add(body_comp.yZConstructionPlane)
    sk_jref.name = "Sk_Slider_Joint_Axis"
    j_line = sk_jref.sketchCurves.sketchLines.addByTwoPoints(
        pt_sk(sk_jref, 0.0, ymid, 0.0), pt_sk(sk_jref, 0.0, ymid, 24.0)
    )
    j_line_proxy = j_line.createForAssemblyContext(body_occ)
    j_geom = adsk.fusion.JointGeometry.createByCurve(
        j_line_proxy, adsk.fusion.JointKeyPointTypes.StartKeyPoint
    )
    ab_in = assy_comp.asBuiltJoints.createInput(plug_occ, body_occ, j_geom)
    ab_in.setAsSliderJointMotion(adsk.fusion.JointDirections.CustomJointDirection, j_line_proxy)
    slider_joint = assy_comp.asBuiltJoints.add(ab_in)
    slider_joint.name = "Joint_Slider_DT30_Test"

    return assy_occ


def run(context):
    """Standalone Fusion Script entrypoint (Utilities -> Scripts and Add-Ins)."""
    app = adsk.core.Application.get()
    ui = app.userInterface if app else None
    try:
        design = adsk.fusion.Design.cast(app.activeProduct)
        if not design:
            app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            design = adsk.fusion.Design.cast(app.activeProduct)

        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        if hasattr(design, "fusionUnitsManager"):
            design.fusionUnitsManager.distanceDisplayUnits = adsk.fusion.DistanceUnits.MillimeterDistanceUnits

        app.executeTextCommand('PTransaction.Start "Build Product 0 FitCheckGauge"')
        try:
            build_product(design, design.rootComponent)
            app.executeTextCommand("PTransaction.Commit")
        except Exception:
            app.executeTextCommand("PTransaction.Abort")
            raise

        vp = app.activeViewport
        if vp:
            cam = vp.camera
            cam.viewOrientation = adsk.core.ViewOrientations.IsoTopRightViewOrientation
            cam.isFitView = True
            vp.camera = cam
            vp.refresh()

        app.log(
            "[Product0_FitCheckGauge] Built parametric 6-in-1 calibration gauge successfully.",
            adsk.core.LogLevels.InfoLogLevel,
            adsk.core.LogTypes.ConsoleLogType,
        )
    except Exception:
        err = traceback.format_exc()
        if app:
            app.log(err, adsk.core.LogLevels.ErrorLogLevel, adsk.core.LogTypes.ConsoleLogType)
        if ui:
            ui.messageBox(f"Product0_FitCheckGauge failed:\n{err}")
