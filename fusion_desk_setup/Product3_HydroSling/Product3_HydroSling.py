# -*- coding: utf-8 -*-
"""
Product 3 — HydroSling Outrigger (Right-Edge Bottle Cage + Under-Desk Notebook Sling)
=====================================================================================
Clamps to the front-right edge (`X = table_length = 630 mm`, `Z = 142..268 mm`)
of your 630 x 280 x 18 mm desk (+ 3 mm mat) with soft 2 mm protective pads and
dual M4 thumbscrews (zero screws in desk):
  - Sub-Component A (`P3A_RightClamp_BottleCage`):
    Low-profile beveled top clamp jaw (`20 mm` reach) paired with an outboard
    cylindrical bottle cage (`X = 630..732 mm`) featuring 3 compliant PETG
    centering ribs (`65..84 mm` bottle grip, `76 mm` nominal) and a slotted
    coaster base—keeping condensation and spills 100% outside the tabletop.
  - Sub-Component B (`P3B_UnderDesk_Notebook_Tray`):
    Slides onto an integrated under-clamp `DT-30` dovetail (`SliderJoint`),
    creating a low-profile (`36 mm` drop) open-left C-channel bay (`180 x 184 mm`,
    `< 200 mm` print bed) that accepts both A5 and A4 notebooks under the right side.

Follows `ku2503u0279-tech/autodesk-fusion-mcp` patterns:
  - `guides/fusion-design-guide.md` §§4, 5, 6, 7, 8, 11, 12
  - `AutodeskFusionMCP.manifest` & `lib/fusionAddInUtils/general_utils.py`
"""

import math
import traceback
import adsk.core
import adsk.fusion


def mm(val_mm: float) -> float:
    return float(val_mm) * 0.1


def ensure_param(design: adsk.fusion.Design, name: str, expr: str, unit: str, comment: str) -> float:
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
    return sketch.modelToSketchSpace(adsk.core.Point3D.create(mm(x_mm), mm(y_mm), mm(z_mm)))


def extrude_sign(sketch: adsk.fusion.Sketch, dx: float, dy: float, dz: float) -> int:
    n = sketch.xDirection.crossProduct(sketch.yDirection)
    return 1 if (n.x * dx + n.y * dy + n.z * dz) >= 0.0 else -1


def collect_all_profiles(sketch: adsk.fusion.Sketch) -> adsk.core.ObjectCollection:
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
    planes = comp.constructionPlanes
    p_in = planes.createInput()
    p_in.setByOffset(base_plane, adsk.core.ValueInput.createByString(offset_expr))
    plane = planes.add(p_in)
    plane.name = name
    return plane


def draw_poly_3d(sketch: adsk.fusion.Sketch, pts_3d_mm: list):
    lines = sketch.sketchCurves.sketchLines
    n = len(pts_3d_mm)
    for i in range(n):
        lines.addByTwoPoints(pt_sk(sketch, *pts_3d_mm[i]), pt_sk(sketch, *pts_3d_mm[(i + 1) % n]))


def register_parameters(design: adsk.fusion.Design) -> dict:
    v = {}
    v["table_length"] = ensure_param(design, "table_length", "630.0 mm", "mm", "Desk width X")
    v["table_thickness"] = ensure_param(design, "table_thickness", "18.0 mm", "mm", "Wood tabletop thickness")
    v["mat_thickness"] = ensure_param(design, "mat_thickness", "3.0 mm", "mm", "Desk mat thickness")
    v["clamp_pad_t"] = ensure_param(design, "clamp_pad_t", "2.0 mm", "mm", "Soft non-marring pad thickness")
    v["fit_clearance"] = ensure_param(design, "fit_clearance", "0.25 mm", "mm", "Nominal 3D-print clearance")
    v["bottle_max_dia"] = ensure_param(design, "bottle_max_dia", "86.0 mm", "mm", "Bottle cage inner bore (grips 65-84 mm)")
    v["bottle_cage_h"] = ensure_param(design, "bottle_cage_h", "96.0 mm", "mm", "Bottle cage side-wall height")
    v["hydro_z_start"] = ensure_param(design, "hydro_z_start", "142.0 mm", "mm", "Front-right clamp Z start")
    v["hydro_clamp_len"] = ensure_param(design, "hydro_clamp_len", "124.0 mm", "mm", "Front-right clamp Z span")
    v["notebook_slot_h"] = ensure_param(design, "notebook_slot_h", "24.0 mm", "mm", "Clear vertical slot for A5/A4 notebook")
    v["notebook_tray_w"] = ensure_param(design, "notebook_tray_w", "178.0 mm", "mm", "Under-desk notebook tray X width (<200 mm)")
    v["notebook_tray_d"] = ensure_param(design, "notebook_tray_d", "184.0 mm", "mm", "Under-desk notebook tray Z depth (<200 mm)")
    v["dt30_width"] = ensure_param(design, "dt30_width", "30.0 mm", "mm", "Shared DT-30 dovetail root width")
    v["dt30_depth"] = ensure_param(design, "dt30_depth", "6.0 mm", "mm", "Shared DT-30 dovetail depth")
    v["m4_insert_od"] = ensure_param(design, "m4_insert_od", "5.6 mm", "mm", "M4 brass heat-set pilot bore")
    return v


def build_product(design: adsk.fusion.Design, parent_comp: adsk.fusion.Component = None) -> adsk.fusion.Occurrence:
    """Build Product 3 (HydroSling Outboard Bottle Cage + Under-Desk Notebook Sling)."""
    if parent_comp is None:
        parent_comp = design.rootComponent

    v = register_parameters(design)

    assy_occ = parent_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    assy_comp = assy_occ.component
    assy_comp.name = "Product3_HydroSling"

    xr = v["table_length"]                                     # 630.0 mm
    z0 = v["hydro_z_start"]                                    # 142.0 mm
    clen = v["hydro_clamp_len"]                                # 124.0 mm (Z = 142..266 mm)
    y_top_pad = v["mat_thickness"] + v["clamp_pad_t"]          # +5.0 mm
    y_bot_pad = -v["table_thickness"] - v["clamp_pad_t"] - 4.0 # -24.0 mm
    jaw_in = 20.0                                              # X = 610..630 mm

    # ---- Sub-Component A: Right-Edge Beveled C-Clamp + Outboard Bottle Cage ----
    occ_cage = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp_cage = occ_cage.component
    comp_cage.name = "P3A_RightClamp_BottleCage"

    p_clamp = make_offset_plane(comp_cage, comp_cage.xYConstructionPlane, "hydro_z_start", "Plane_Hydro_Clamp")
    sk_c = comp_cage.sketches.add(p_clamp)
    sk_c.name = "Sk_RightEdge_Beveled_Clamp"
    # Beveled low-profile top jaw so mouse hand never touches a sharp step!
    clamp_pts = [
        (xr - jaw_in, y_top_pad, z0),
        (xr, y_top_pad, z0),
        (xr, y_bot_pad, z0),
        (xr - jaw_in, y_bot_pad, z0),
        (xr - jaw_in, y_bot_pad - 11.0, z0),
        (xr + 12.0, y_bot_pad - 11.0, z0),
        (xr + 12.0, y_top_pad + 6.0, z0),
        (xr - jaw_in + 6.0, y_top_pad + 6.0, z0),
        (xr - jaw_in, y_top_pad + 2.5, z0),
    ]
    draw_poly_3d(sk_c, clamp_pts)
    ext_c = add_extrude(
        comp_cage,
        sk_c,
        "hydro_clamp_len",
        (0, 0, 1),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
        "Ext_RightEdge_Clamp",
    )
    cage_body = ext_c.bodies.item(0)
    cage_body.name = "Body_P3A_Clamp_BottleCage"

    # Female DT-30 Dovetail along bottom of lower jaw (Y = y_bot_pad - 11 = -35.0 mm) for Notebook Tray!
    y_jaw_bot = y_bot_pad - 11.0
    dt_d = v["dt30_depth"]
    dt_hb = 0.5 * (v["dt30_width"] + 2.0 * v["fit_clearance"])
    dt_hn = dt_hb - dt_d / math.tan(math.radians(60.0))
    dt_xc = xr - 8.0
    sk_dt = comp_cage.sketches.add(p_clamp)
    sk_dt.name = "Sk_UnderJaw_DT30_Female"
    draw_poly_3d(
        sk_dt,
        [
            (dt_xc - dt_hn, y_jaw_bot - 0.5, z0),
            (dt_xc - dt_hb, y_jaw_bot + dt_d, z0),
            (dt_xc + dt_hb, y_jaw_bot + dt_d, z0),
            (dt_xc + dt_hn, y_jaw_bot - 0.5, z0),
        ],
    )
    add_extrude(
        comp_cage,
        sk_dt,
        "hydro_clamp_len + 1 mm",
        (0, 0, 1),
        adsk.fusion.FeatureOperations.CutFeatureOperation,
        "Ext_Cut_UnderJaw_DT30",
        cage_body,
    )

    # Outboard Cylindrical Bottle Cup (100% outside desk X > 630 mm!)
    r_in = 0.5 * v["bottle_max_dia"]        # 43.0 mm
    r_out = r_in + 4.5                      # 47.5 mm
    bx = xr + 10.0 + r_out                  # 687.5 mm
    bz = z0 + 0.5 * clen                    # 204.0 mm
    by_bot = -62.0

    p_cup = make_offset_plane(comp_cage, comp_cage.xZConstructionPlane, f"{by_bot} mm", "Plane_BottleCup_Floor")
    # Solid coaster floor + connecting gusset bridge to clamp spine (X = xr+6 .. bx)
    sk_floor = comp_cage.sketches.add(p_cup)
    sk_floor.name = "Sk_BottleCup_BaseAndBridge"
    sk_floor.sketchCurves.sketchCircles.addByCenterRadius(pt_sk(sk_floor, bx, by_bot, bz), mm(r_out))
    draw_poly_3d(
        sk_floor,
        [
            (xr + 8.0, by_bot, bz - 26.0),
            (bx, by_bot, bz - 26.0),
            (bx, by_bot, bz + 26.0),
            (xr + 8.0, by_bot, bz + 26.0),
        ],
    )
    add_extrude(
        comp_cage,
        sk_floor,
        "bottle_cage_h",
        (0, 1, 0),
        adsk.fusion.FeatureOperations.JoinFeatureOperation,
        "Ext_Join_BottleCup_Cylinder",
        cage_body,
    )

    # Hollow inner bottle bore (leaves 6 mm coaster base at bottom)
    p_bore = make_offset_plane(comp_cage, comp_cage.xZConstructionPlane, f"{by_bot + 6.0} mm", "Plane_BottleCup_Bore")
    sk_bore = comp_cage.sketches.add(p_bore)
    sk_bore.name = "Sk_BottleCup_InnerBore"
    sk_bore.sketchCurves.sketchCircles.addByCenterRadius(pt_sk(sk_bore, bx, by_bot + 6.0, bz), mm(r_in))
    add_extrude(
        comp_cage,
        sk_bore,
        "bottle_cage_h",
        (0, 1, 0),
        adsk.fusion.FeatureOperations.CutFeatureOperation,
        "Ext_Cut_Bottle_InnerBore",
        cage_body,
    )

    # 3 Compliant Centering Ribs (gently grip 65..84 mm bottles rattle-free!) + Coaster Drain Hole
    sk_ribs = comp_cage.sketches.add(p_bore)
    sk_ribs.name = "Sk_Bottle_3x_CompliantRibs"
    for k in range(3):
        ang = math.radians(60.0 + k * 120.0)
        rx = bx + (r_in - 2.0) * math.cos(ang)
        rz = bz + (r_in - 2.0) * math.sin(ang)
        sk_ribs.sketchCurves.sketchCircles.addByCenterRadius(pt_sk(sk_ribs, rx, by_bot + 6.0, rz), mm(5.5))
    add_extrude(
        comp_cage,
        sk_ribs,
        "bottle_cage_h - 14.0 mm",
        (0, 1, 0),
        adsk.fusion.FeatureOperations.JoinFeatureOperation,
        "Ext_Join_Compliant_Ribs",
        cage_body,
    )

    # Dual M4 Heat-Set Clamp Bores
    sk_m4 = comp_cage.sketches.add(p_cup)
    sk_m4.name = "Sk_Hydro_Dual_M4_Bores"
    r_m4 = 0.5 * v["m4_insert_od"]
    sk_m4.sketchCurves.sketchCircles.addByCenterRadius(pt_sk(sk_m4, xr - 10.0, by_bot, z0 + 22.0), mm(r_m4))
    sk_m4.sketchCurves.sketchCircles.addByCenterRadius(pt_sk(sk_m4, xr - 10.0, by_bot, z0 + clen - 22.0), mm(r_m4))
    add_extrude(
        comp_cage,
        sk_m4,
        "48.0 mm",
        (0, 1, 0),
        adsk.fusion.FeatureOperations.CutFeatureOperation,
        "Ext_Cut_Hydro_M4_Bores",
        cage_body,
    )

    # ---- Sub-Component B: Under-Desk Open-Left Sliding Notebook Sling (< 200 x 200 mm!) ----
    occ_tray = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp_tray = occ_tray.component
    comp_tray.name = "P3B_UnderDesk_Notebook_Tray"

    z_tray = z0 - 60.0                                 # Z = 82..266 mm (184 mm total depth!)
    tw = v["notebook_tray_w"]                          # 178.0 mm
    sh = v["notebook_slot_h"]                          # 24.0 mm clear notebook height
    m_d = dt_d - v["fit_clearance"]
    m_hb = 0.5 * v["dt30_width"]
    m_hn = m_hb - m_d / math.tan(math.radians(60.0))

    p_tray = make_offset_plane(comp_tray, comp_tray.xYConstructionPlane, f"{z_tray} mm", "Plane_NotebookTray_Rear")
    sk_tray = comp_tray.sketches.add(p_tray)
    sk_tray.name = "Sk_NotebookTray_OpenC_DT30"
    # Open-left C-tray + integral male DT-30 rail on top-right so A5 fits inside AND A4 overhangs cleanly left!
    tray_pts = [
        (xr - tw, y_jaw_bot - sh - 4.5, z_tray),
        (xr - 2.0, y_jaw_bot - sh - 4.5, z_tray),
        (xr - 2.0, y_jaw_bot, z_tray),
        (dt_xc + m_hn, y_jaw_bot, z_tray),
        (dt_xc + m_hb, y_jaw_bot + m_d, z_tray),
        (dt_xc - m_hb, y_jaw_bot + m_d, z_tray),
        (dt_xc - m_hn, y_jaw_bot, z_tray),
        (xr - 22.0, y_jaw_bot, z_tray),
        (xr - 22.0, y_jaw_bot - 4.0, z_tray),
        (xr - 6.5, y_jaw_bot - 4.0, z_tray),
        (xr - 6.5, y_jaw_bot - sh, z_tray),
        (xr - tw + 4.5, y_jaw_bot - sh, z_tray),
        (xr - tw + 4.5, y_jaw_bot - sh + 7.0, z_tray),
        (xr - tw, y_jaw_bot - sh + 7.0, z_tray),
    ]
    draw_poly_3d(sk_tray, tray_pts)
    ext_tray = add_extrude(
        comp_tray,
        sk_tray,
        "notebook_tray_d",
        (0, 0, 1),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
        "Ext_UnderDesk_Notebook_Tray",
    )
    tray_body = ext_tray.bodies.item(0)
    tray_body.name = "Body_P3B_Notebook_Tray"

    # Slider Joint along Z between Notebook Tray and Right-Edge Clamp
    sk_sl = comp_cage.sketches.add(comp_cage.yZConstructionPlane)
    sk_sl.name = "Sk_Notebook_DT30_Slider_Axis"
    sl_line = sk_sl.sketchCurves.sketchLines.addByTwoPoints(
        pt_sk(sk_sl, dt_xc, y_jaw_bot, z0), pt_sk(sk_sl, dt_xc, y_jaw_bot, z0 + 60.0)
    )
    sl_proxy = sl_line.createForAssemblyContext(occ_cage)
    sl_geom = adsk.fusion.JointGeometry.createByCurve(sl_proxy, adsk.fusion.JointKeyPointTypes.StartKeyPoint)
    ab_in = assy_comp.asBuiltJoints.createInput(occ_tray, occ_cage, sl_geom)
    ab_in.setAsSliderJointMotion(adsk.fusion.JointDirections.CustomJointDirection, sl_proxy)
    sl_j = assy_comp.asBuiltJoints.add(ab_in)
    sl_j.name = "Joint_Slider_NotebookTray_DT30"

    return assy_occ


def run(context):
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

        app.executeTextCommand('PTransaction.Start "Build Product 3 HydroSling"')
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
            "[Product3_HydroSling] Built right-edge outboard bottle cage + sliding notebook tray.",
            adsk.core.LogLevels.InfoLogLevel,
            adsk.core.LogTypes.ConsoleLogType,
        )
    except Exception:
        err = traceback.format_exc()
        if app:
            app.log(err, adsk.core.LogLevels.ErrorLogLevel, adsk.core.LogTypes.ConsoleLogType)
        if ui:
            ui.messageBox(f"Product3_HydroSling failed:\n{err}")
