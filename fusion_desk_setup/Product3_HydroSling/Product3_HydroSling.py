# -*- coding: utf-8 -*-
"""
Product 3 — HydroSling Bottle Chalice + Walnut Notebook Slide Tray (Designer Hybrid v2)
======================================================================================
Replaces the large 178 x 165 mm 3D-printed drawer bed with a sleek 6 mm Warm
Walnut / Birch wood slide tray (`W3B`) featuring a smooth crescent thumb-scoop,
and upgrades the bottle holder (`P3A`) into a sculpted chalice with a 6 mm
Warm Walnut coaster inlay (`W3A`)!

Individual Pieces Created as Separate Named Components:
  - `P3A_Sculpted_Bottle_Chalice`   (3D-Printed Matte-Black PETG, tulip ring + C-clamp)
  - `W3A_Walnut_Coaster_Inlay`      (6 mm Warm Walnut Wood Disc, Ø82 x 6 mm)
  - `P3B_Left_DT30_Clamp_Runner`    (3D-Printed Matte-Black PETG, 24 x 42 x 52 mm)
  - `P3B_Right_DT30_Clamp_Runner`   (3D-Printed Matte-Black PETG, 24 x 42 x 52 mm)
  - `P3C_Left_DT30_Slide_Cleat`     (3D-Printed Cyber-Red PETG, 18 x 150 x 10 mm)
  - `P3C_Right_DT30_Slide_Cleat`    (3D-Printed Cyber-Red PETG, 18 x 150 x 10 mm)
  - `W3B_Walnut_Notebook_Tray`      (6 mm Wood, 172 x 162 x 6 mm, crescent scoop)
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


def sample_rounded_poly_2d(corners_uv: list, radius: float, segs_per_corner: int = 5) -> list:
    out = []
    n = len(corners_uv)
    for i in range(n):
        u_prev, v_prev = corners_uv[(i - 1) % n]
        u_cur, v_cur = corners_uv[i]
        u_next, v_next = corners_uv[(i + 1) % n]
        d1u, d1v = u_prev - u_cur, v_prev - v_cur
        d2u, d2v = u_next - u_cur, v_next - v_cur
        l1, l2 = math.hypot(d1u, d1v), math.hypot(d2u, d2v)
        if l1 < 1e-3 or l2 < 1e-3:
            out.append((u_cur, v_cur))
            continue
        d1u, d1v, d2u, d2v = d1u / l1, d1v / l1, d2u / l2, d2v / l2
        dot = max(-0.999, min(0.999, d1u * d2u + d1v * d2v))
        half_ang = 0.5 * math.acos(dot)
        if half_ang < 0.08 or abs(half_ang - 0.5 * math.pi) < 1e-4:
            out.append((u_cur, v_cur))
            continue
        tan_h = math.tan(half_ang)
        trim = min(radius / tan_h, 0.38 * l1, 0.38 * l2)
        eff_r = trim * tan_h
        p_start = (u_cur + d1u * trim, v_cur + d1v * trim)
        p_end = (u_cur + d2u * trim, v_cur + d2v * trim)
        bis_u, bis_v = d1u + d2u, d1v + d2v
        bl = math.hypot(bis_u, bis_v)
        if bl < 1e-6:
            out.append((u_cur, v_cur))
            continue
        bis_u, bis_v = bis_u / bl, bis_v / bl
        c_dist = eff_r / math.sin(half_ang)
        cu, cv = u_cur + bis_u * c_dist, v_cur + bis_v * c_dist
        a1 = math.atan2(p_start[1] - cv, p_start[0] - cu)
        a2 = math.atan2(p_end[1] - cv, p_end[0] - cu)
        da = (a2 - a1 + math.pi) % (2.0 * math.pi) - math.pi
        for s in range(segs_per_corner + 1):
            ang = a1 + da * (s / float(segs_per_corner))
            out.append((cu + eff_r * math.cos(ang), cv + eff_r * math.sin(ang)))
    return out


def register_parameters(design: adsk.fusion.Design) -> dict:
    v = {}
    v["table_depth"] = ensure_param(design, "table_depth", "280.0 mm", "mm", "Wood tabletop depth")
    v["table_thickness"] = ensure_param(design, "table_thickness", "18.0 mm", "mm", "Wood tabletop thickness")
    v["mat_thickness"] = ensure_param(design, "mat_thickness", "3.0 mm", "mm", "Desk mat thickness")
    v["wood_thick_panel"] = ensure_param(design, "wood_thick_panel", "6.0 mm", "mm", "6 mm Warm Walnut / Birch wood thickness")
    v["clamp_pad_t"] = ensure_param(design, "clamp_pad_t", "2.0 mm", "mm", "Non-marring clamp pad allowance")
    v["fit_clearance"] = ensure_param(design, "fit_clearance", "0.25 mm", "mm", "Sliding fit clearance")
    v["bottle_max_od"] = ensure_param(design, "bottle_max_od", "88.0 mm", "mm", "1L insulated bottle bore")
    v["bottle_drop_y"] = ensure_param(design, "bottle_drop_y", "92.0 mm", "mm", "Chalice rim drop below desk")
    v["tray_x_start"] = ensure_param(design, "tray_x_start", "16.0 mm", "mm", "Notebook slide tray X start")
    v["tray_width"] = ensure_param(design, "tray_width", "172.0 mm", "mm", "6 mm Wood notebook tray width")
    v["tray_depth"] = ensure_param(design, "tray_depth", "162.0 mm", "mm", "6 mm Wood notebook tray depth")
    return v


def _build_chalice_and_walnut_coaster(assy_comp: adsk.fusion.Component, v: dict) -> tuple:
    """Build P3A Sculpted Bottle Chalice + W3A 6 mm Warm Walnut Coaster Inlay."""
    z_front = v["table_depth"]                                 # 280.0 mm
    y_top_pad = v["mat_thickness"] + v["clamp_pad_t"]          # +5.0 mm
    y_bot_pad = -v["table_thickness"] - v["clamp_pad_t"] - 4.0 # -24.0 mm
    r_in = 0.5 * v["bottle_max_od"]                            # 44.0 mm
    r_out = r_in + 5.5                                         # 49.5 mm
    cx = 40.0
    cz = z_front + 54.0                                        # 334.0 mm
    y_rim = -v["bottle_drop_y"]                                # -92.0 mm
    cage_h = 84.0                                              # Y = -176..-92 mm

    occ_ch = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp_ch = occ_ch.component
    comp_ch.name = "P3A_Sculpted_Bottle_Chalice"

    # 1. Sculpted Rounded Front-Left C-Clamp Spine
    p_sp = make_offset_plane(comp_ch, comp_ch.yZConstructionPlane, f"{cx - 18.0} mm", "Plane_Chalice_Spine")
    sk_sp = comp_ch.sketches.add(p_sp)
    sk_sp.name = "Sk_Sculpted_Chalice_Clamp"
    spine_yz = sample_rounded_poly_2d(
        [
            (y_top_pad + 5.5, z_front - 18.0),
            (y_top_pad + 5.5, z_front + 10.0),
            (y_rim, z_front + 12.0),
            (y_rim - 22.0, z_front + 12.0),
            (y_rim - 22.0, z_front + 2.0),
            (y_bot_pad - 8.0, z_front + 2.0),
            (y_bot_pad - 8.0, z_front - 18.0),
            (y_bot_pad, z_front - 18.0),
            (y_bot_pad, z_front),
            (y_top_pad, z_front),
            (y_top_pad, z_front - 18.0),
        ],
        radius=3.5,
        segs_per_corner=4,
    )
    draw_poly_3d(sk_sp, [(cx - 18.0, yy, zz) for (yy, zz) in spine_yz])
    ext_sp = add_extrude(
        comp_ch, sk_sp, "36.0 mm", (1, 0, 0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation, "Ext_Chalice_Clamp"
    )
    ch_body = ext_sp.bodies.item(0)
    ch_body.name = "Body_P3A_Sculpted_Chalice"

    # 2. Chalice Base Cup + Cylindrical Wall
    p_bot = make_offset_plane(comp_ch, comp_ch.xZConstructionPlane, f"{y_rim - cage_h} mm", "Plane_Chalice_Bot")
    sk_bot = comp_ch.sketches.add(p_bot)
    sk_bot.name = "Sk_Chalice_CupBase"
    sk_bot.sketchCurves.sketchCircles.addByCenterRadius(pt_sk(sk_bot, cx, y_rim - cage_h, cz), mm(r_out))
    sk_bot.sketchCurves.sketchCircles.addByCenterRadius(pt_sk(sk_bot, cx, y_rim - cage_h, cz), mm(18.0))
    add_extrude(
        comp_ch, sk_bot, "6.0 mm", (0, 1, 0), adsk.fusion.FeatureOperations.JoinFeatureOperation, "Ext_Join_Chalice_Base", ch_body
    )

    p_wall = make_offset_plane(comp_ch, comp_ch.xZConstructionPlane, f"{y_rim - cage_h + 6.0} mm", "Plane_Chalice_Wall")
    sk_wall = comp_ch.sketches.add(p_wall)
    sk_wall.name = "Sk_Chalice_Annulus"
    sk_wall.sketchCurves.sketchCircles.addByCenterRadius(pt_sk(sk_wall, cx, y_rim - cage_h + 6.0, cz), mm(r_out))
    sk_wall.sketchCurves.sketchCircles.addByCenterRadius(pt_sk(sk_wall, cx, y_rim - cage_h + 6.0, cz), mm(r_in))
    add_extrude(
        comp_ch, sk_wall, f"{cage_h - 6.0} mm", (0, 1, 0), adsk.fusion.FeatureOperations.JoinFeatureOperation, "Ext_Join_Chalice_Wall", ch_body
    )

    # Tulip Side Sightline Window Cutouts (shows off the bottle & saves 35% plastic!)
    p_win = make_offset_plane(comp_ch, comp_ch.xYConstructionPlane, f"{cz - 60.0} mm", "Plane_Chalice_Windows")
    sk_win = comp_ch.sketches.add(p_win)
    sk_win.name = "Sk_Chalice_Pill_Windows"
    for dx_off in (-22.0, 22.0):
        win_xy = sample_rounded_poly_2d(
            [
                (cx + dx_off - 10.0, y_rim - cage_h + 18.0),
                (cx + dx_off + 10.0, y_rim - cage_h + 18.0),
                (cx + dx_off + 12.0, y_rim - 12.0),
                (cx + dx_off - 12.0, y_rim - 12.0),
            ],
            radius=8.0,
            segs_per_corner=5,
        )
        draw_poly_3d(sk_win, [(xx, yy, cz - 60.0) for (xx, yy) in win_xy])
    add_extrude(
        comp_ch, sk_win, "120.0 mm", (0, 0, 1), adsk.fusion.FeatureOperations.CutFeatureOperation, "Ext_Cut_Chalice_Windows", ch_body
    )

    # W3A: 6 mm Warm Walnut Coaster Disc Inlay inside the chalice base!
    occ_wc = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp_wc = occ_wc.component
    comp_wc.name = "W3A_Walnut_Coaster_Inlay"
    y_wc = y_rim - cage_h + 6.0
    p_wc = make_offset_plane(comp_wc, comp_wc.xZConstructionPlane, f"{y_wc} mm", "Plane_W3A_Coaster")
    sk_wc = comp_wc.sketches.add(p_wc)
    sk_wc.name = "Sk_W3A_WalnutDisc"
    sk_wc.sketchCurves.sketchCircles.addByCenterRadius(pt_sk(sk_wc, cx, y_wc, cz), mm(r_in - 2.0))
    sk_wc.sketchCurves.sketchCircles.addByCenterRadius(pt_sk(sk_wc, cx, y_wc, cz), mm(8.0))
    ext_wc = add_extrude(
        comp_wc, sk_wc, "wood_thick_panel", (0, 1, 0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation, "Ext_W3A_Walnut_Coaster"
    )
    ext_wc.bodies.item(0).name = "Body_W3A_Walnut_Coaster"

    return occ_ch, occ_wc


def _build_walnut_notebook_slide(assy_comp: adsk.fusion.Component, v: dict) -> tuple:
    """Build P3B Left/Right Clamp Runners + P3C Slide Cleats + W3B 6 mm Walnut Wood Tray."""
    x0 = v["tray_x_start"]                                     # 16.0 mm
    tw = v["tray_width"]                                       # 172.0 mm
    td = v["tray_depth"]                                       # 162.0 mm
    z_front = v["table_depth"]                                 # 280.0 mm
    y_top_pad = v["mat_thickness"] + v["clamp_pad_t"]          # +5.0 mm
    y_bot_pad = -v["table_thickness"] - v["clamp_pad_t"] - 4.0 # -24.0 mm
    run_w = 24.0

    runners = []
    for cname, bname, rx in [
        ("P3B_Left_DT30_Clamp_Runner", "Body_P3B_Left_Runner", x0),
        ("P3B_Right_DT30_Clamp_Runner", "Body_P3B_Right_Runner", x0 + tw - run_w),
    ]:
        occ = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        comp = occ.component
        comp.name = cname
        pl = make_offset_plane(comp, comp.yZConstructionPlane, f"{rx} mm", f"Plane_{cname}")
        sk = comp.sketches.add(pl)
        sk.name = f"Sk_{cname}_Curve"
        r_yz = sample_rounded_poly_2d(
            [
                (y_top_pad + 5.0, z_front - 18.0),
                (y_top_pad + 5.0, z_front + 6.0),
                (-48.0, z_front + 6.0),
                (-48.0, z_front - 42.0),
                (-38.0, z_front - 42.0),
                (-38.0, z_front - 6.0),
                (y_bot_pad, z_front - 6.0),
                (y_bot_pad, z_front),
                (y_top_pad, z_front),
                (y_top_pad, z_front - 18.0),
            ],
            radius=3.0,
            segs_per_corner=4,
        )
        draw_poly_3d(sk, [(rx, yy, zz) for (yy, zz) in r_yz])
        ext = add_extrude(
            comp, sk, f"{run_w} mm", (1, 0, 0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation, f"Ext_{cname}"
        )
        ext.bodies.item(0).name = bname
        runners.append(occ)

    # P3C: Twin Compact Slide Cleats attached to underside edges of W3B wood tray
    z_tray_start = z_front - td - 4.0                          # 114.0 mm
    y_wood_bot = -37.0
    cleats = []
    for cname, bname, cx_start in [
        ("P3C_Left_DT30_Slide_Cleat", "Body_P3C_Left_Cleat", x0 + 2.0),
        ("P3C_Right_DT30_Slide_Cleat", "Body_P3C_Right_Cleat", x0 + tw - 16.0),
    ]:
        occ = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        comp = occ.component
        comp.name = cname
        pl = make_offset_plane(comp, comp.xYConstructionPlane, f"{z_tray_start + 8.0} mm", f"Plane_{cname}")
        sk = comp.sketches.add(pl)
        sk.name = f"Sk_{cname}"
        draw_poly_3d(
            sk,
            [
                (cx_start, y_wood_bot - 6.0, z_tray_start + 8.0),
                (cx_start + 14.0, y_wood_bot - 6.0, z_tray_start + 8.0),
                (cx_start + 14.0, y_wood_bot, z_tray_start + 8.0),
                (cx_start, y_wood_bot, z_tray_start + 8.0),
            ],
        )
        ext = add_extrude(
            comp, sk, f"{td - 16.0} mm", (0, 0, 1), adsk.fusion.FeatureOperations.NewBodyFeatureOperation, f"Ext_{cname}"
        )
        ext.bodies.item(0).name = bname
        cleats.append(occ)

    # W3B: 6 mm Warm Walnut / Birch Wood Notebook Slide Tray (172 x 162 x 6 mm with ergonomic crescent scoop!)
    occ_wtray = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp_wtray = occ_wtray.component
    comp_wtray.name = "W3B_Walnut_Notebook_Tray"
    p_wt = make_offset_plane(comp_wtray, comp_wtray.xZConstructionPlane, f"{y_wood_bot} mm", "Plane_W3B_WoodTray")
    sk_wt = comp_wtray.sketches.add(p_wt)
    sk_wt.name = "Sk_W3B_Crescent_Wood_Tray"
    mid_x = x0 + 0.5 * tw
    tray_xz = sample_rounded_poly_2d(
        [
            (x0, z_tray_start),
            (x0 + tw, z_tray_start),
            (x0 + tw, z_tray_start + td),
            (mid_x + 34.0, z_tray_start + td),
            (mid_x + 22.0, z_tray_start + td - 18.0),
            (mid_x - 22.0, z_tray_start + td - 18.0),
            (mid_x - 34.0, z_tray_start + td),
            (x0, z_tray_start + td),
        ],
        radius=10.0,
        segs_per_corner=5,
    )
    draw_poly_3d(sk_wt, [(xx, y_wood_bot, zz) for (xx, zz) in tray_xz])
    ext_wt = add_extrude(
        comp_wtray, sk_wt, "wood_thick_panel", (0, 1, 0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation, "Ext_W3B_Wood_Tray"
    )
    ext_wt.bodies.item(0).name = "Body_W3B_Walnut_Notebook_Tray"

    return runners[0], runners[1], cleats[0], cleats[1], occ_wtray, (mid_x, y_wood_bot, z_tray_start)


def build_product(design: adsk.fusion.Design, parent_comp: adsk.fusion.Component = None) -> adsk.fusion.Occurrence:
    if parent_comp is None:
        parent_comp = design.rootComponent

    v = register_parameters(design)

    assy_occ = parent_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    assy_comp = assy_occ.component
    assy_comp.name = "Product3_HydroSling"

    occ_ch, occ_wc = _build_chalice_and_walnut_coaster(assy_comp, v)
    occ_rl, occ_rr, occ_cl, occ_cr, occ_wt, slide_xyz = _build_walnut_notebook_slide(assy_comp, v)

    ab = assy_comp.asBuiltJoints
    for c_occ, p_occ, jn in [
        (occ_wc, occ_ch, "Joint_Rigid_WalnutCoaster_in_Chalice"),
        (occ_rl, occ_ch, "Joint_Rigid_LeftRunner_to_Chalice"),
        (occ_rr, occ_rl, "Joint_Rigid_RightRunner_to_LeftRunner"),
        (occ_cl, occ_wt, "Joint_Rigid_LeftCleat_to_WoodTray"),
        (occ_cr, occ_wt, "Joint_Rigid_RightCleat_to_WoodTray"),
    ]:
        ji = ab.createInput(c_occ, p_occ, None)
        ji.setAsRigidJointMotion()
        j = ab.add(ji)
        j.name = jn

    sx, sy, sz = slide_xyz
    sk_sl = occ_rl.component.sketches.add(occ_rl.component.xZConstructionPlane)
    sk_sl.name = "Sk_Tray_Slider_Axis"
    sl_line = sk_sl.sketchCurves.sketchLines.addByTwoPoints(pt_sk(sk_sl, sx, sy, sz), pt_sk(sk_sl, sx, sy, sz + 110.0))
    sl_proxy = sl_line.createForAssemblyContext(occ_rl)
    sl_geom = adsk.fusion.JointGeometry.createByCurve(sl_proxy, adsk.fusion.JointKeyPointTypes.StartKeyPoint)
    sl_in = ab.createInput(occ_wt, occ_rl, sl_geom)
    sl_in.setAsSliderJointMotion(adsk.fusion.JointDirections.CustomJointDirection, sl_proxy)
    sl_j = ab.add(sl_in)
    sl_j.name = "Joint_Slider_Walnut_Notebook_Tray"

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
        app.executeTextCommand('PTransaction.Start "Build Product 3 Designer Hybrid"')
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
    except Exception:
        err = traceback.format_exc()
        if app:
            app.log(err, adsk.core.LogLevels.ErrorLogLevel, adsk.core.LogTypes.ConsoleLogType)
        if ui:
            ui.messageBox(f"Product3_HydroSling failed:\n{err}")
