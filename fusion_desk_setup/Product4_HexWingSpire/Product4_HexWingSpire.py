# -*- coding: utf-8 -*-
"""
Product 4 — Walnut Fluted Wing Caddy + Airfoil Chimera Spire (Designer Hybrid v2)
=================================================================================
Transforms the right-edge organizer (`X >= 630 mm`, zero mouse-pad intrusion!)
into a luxury studio desk piece: twin 6 mm Warm Walnut stadium-rounded plates
(`W4A` base + `W4B` pen bezel) sandwiching a sculpted Matte-Black fluted pen
core (`P4B`), a magnetic micro-drawer with a Warm Walnut front faceplate
(`W4C` + `P4C`), and a swept aerodynamic Cyber-Red airfoil mouse bungee (`P4D`).

Individual Pieces Created as Separate Named Components:
  - `P4A_Sculpted_Right_CClamp`      (3D-Printed Matte-Black PETG, right-edge clamp)
  - `W4A_Bottom_Walnut_Stadium_Deck` (6 mm Warm Walnut Wood, 76 x 124 x 6 mm)
  - `P4B_Fluted_Pen_Organizer_Core`  (3D-Printed Matte-Black PETG, 6-cup + drawer bay)
  - `W4B_Top_Walnut_Pen_Collar`      (6 mm Warm Walnut Wood, 76 x 124 x 6 mm, 6 holes)
  - `P4C_Magnetic_Micro_Drawer_Box`  (3D-Printed Cyber-Red PETG, SD/USB/dongle tray)
  - `W4C_Walnut_Drawer_Faceplate`    (6 mm Warm Walnut Wood, 54 x 24 x 6 mm)
  - `P4D_Airfoil_Chimera_Spire`      (3D-Printed Cyber-Red PETG, swept mouse bungee)
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
    v["table_length"] = ensure_param(design, "table_length", "630.0 mm", "mm", "Wood tabletop length")
    v["table_thickness"] = ensure_param(design, "table_thickness", "18.0 mm", "mm", "Wood tabletop thickness")
    v["mat_thickness"] = ensure_param(design, "mat_thickness", "3.0 mm", "mm", "Desk mat thickness")
    v["wood_thick_panel"] = ensure_param(design, "wood_thick_panel", "6.0 mm", "mm", "6 mm Warm Walnut wood thickness")
    v["clamp_pad_t"] = ensure_param(design, "clamp_pad_t", "2.0 mm", "mm", "Soft pad allowance")
    v["fit_clearance"] = ensure_param(design, "fit_clearance", "0.25 mm", "mm", "Sliding fit clearance")
    v["wing_z_start"] = ensure_param(design, "wing_z_start", "16.0 mm", "mm", "Z start of right-edge wing")
    v["wing_z_len"] = ensure_param(design, "wing_z_len", "124.0 mm", "mm", "Z length of stadium walnut plates")
    v["wing_outboard_w"] = ensure_param(design, "wing_outboard_w", "76.0 mm", "mm", "Outboard width past X=630 mm")
    v["magnet_d"] = ensure_param(design, "magnet_d", "6.0 mm", "mm", "6x3 mm N52 magnet OD")
    v["magnet_h"] = ensure_param(design, "magnet_h", "3.0 mm", "mm", "6x3 mm N52 magnet height")
    v["magnet_clear"] = ensure_param(design, "magnet_clear", "0.20 mm", "mm", "Magnet press/glue allowance")
    v["bungee_height"] = ensure_param(design, "bungee_height", "96.0 mm", "mm", "Airfoil Chimera Spire height")
    return v


def _build_walnut_wing_caddy(assy_comp: adsk.fusion.Component, v: dict) -> tuple:
    """Build P4A Right C-Clamp + W4A Bottom Walnut Deck + P4B Fluted Core + W4B Top Walnut Collar."""
    x_edge = v["table_length"]                                 # 630.0 mm
    z0 = v["wing_z_start"]                                     # 16.0 mm
    z_len = v["wing_z_len"]                                    # 124.0 mm
    out_w = v["wing_outboard_w"]                               # 76.0 mm
    tw = v["wood_thick_panel"]                                 # 6.0 mm
    y_top_pad = v["mat_thickness"] + v["clamp_pad_t"]          # +5.0 mm
    y_bot_pad = -v["table_thickness"] - v["clamp_pad_t"] - 4.0 # -24.0 mm

    # 1. P4A: Sculpted Right-Edge C-Clamp Bracket tucked at far rear (Z = 16..52 mm -> leaves Z = 52..280 mm 100% lip-free!)
    occ_cl = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp_cl = occ_cl.component
    comp_cl.name = "P4A_Sculpted_Right_CClamp"
    z_cl = z0
    p_cl = make_offset_plane(comp_cl, comp_cl.xYConstructionPlane, f"{z_cl} mm", "Plane_P4A_Clamp")
    sk_cl = comp_cl.sketches.add(p_cl)
    sk_cl.name = "Sk_P4A_Sculpted_Clamp"
    cl_xy = sample_rounded_poly_2d(
        [
            (x_edge - 16.0, y_top_pad + 5.0),
            (x_edge + 12.0, y_top_pad + 5.0),
            (x_edge + 16.0, -34.0),
            (x_edge + out_w - 8.0, -34.0),
            (x_edge + out_w - 8.0, -42.0),
            (x_edge - 18.0, -42.0),
            (x_edge - 18.0, y_bot_pad),
            (x_edge, y_bot_pad),
            (x_edge, y_top_pad),
            (x_edge - 16.0, y_top_pad),
        ],
        radius=3.5,
        segs_per_corner=4,
    )
    draw_poly_3d(sk_cl, [(xx, yy, z_cl) for (xx, yy) in cl_xy])
    ext_cl = add_extrude(
        comp_cl, sk_cl, "36.0 mm", (0, 0, 1), adsk.fusion.FeatureOperations.NewBodyFeatureOperation, "Ext_P4A_Clamp"
    )
    ext_cl.bodies.item(0).name = "Body_P4A_Right_CClamp"

    # Shared stadium outline for W4A & W4B 6 mm Warm Walnut plates
    stadium_xz = sample_rounded_poly_2d(
        [
            (x_edge + 4.0, z0),
            (x_edge + out_w, z0),
            (x_edge + out_w, z0 + z_len),
            (x_edge + 4.0, z0 + z_len),
        ],
        radius=22.0,
        segs_per_corner=6,
    )

    # 2. W4A: 6 mm Bottom Warm Walnut Stadium Deck (Y = -34..-28 mm)
    occ_wbot = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp_wbot = occ_wbot.component
    comp_wbot.name = "W4A_Bottom_Walnut_Stadium_Deck"
    p_wb = make_offset_plane(comp_wbot, comp_wbot.xZConstructionPlane, "-34.0 mm", "Plane_W4A_Deck")
    sk_wb = comp_wbot.sketches.add(p_wb)
    sk_wb.name = "Sk_W4A_Stadium_Wood"
    draw_poly_3d(sk_wb, [(xx, -34.0, zz) for (xx, zz) in stadium_xz])
    ext_wb = add_extrude(
        comp_wbot, sk_wb, "wood_thick_panel", (0, 1, 0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation, "Ext_W4A_Deck"
    )
    ext_wb.bodies.item(0).name = "Body_W4A_Bottom_Walnut_Deck"

    # 3. P4B: Sculpted Matte-Black Fluted Pen & Micro-Drawer Core (Y = -28..+44 mm, 72 mm tall)
    occ_core = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp_core = occ_core.component
    comp_core.name = "P4B_Fluted_Pen_Organizer_Core"
    p_cr = make_offset_plane(comp_core, comp_core.xZConstructionPlane, "-28.0 mm", "Plane_P4B_Core")
    sk_cr = comp_core.sketches.add(p_cr)
    sk_cr.name = "Sk_P4B_Core_Outline"
    core_xz = sample_rounded_poly_2d(
        [
            (x_edge + 8.0, z0 + 4.0),
            (x_edge + out_w - 4.0, z0 + 4.0),
            (x_edge + out_w - 4.0, z0 + z_len - 4.0),
            (x_edge + 8.0, z0 + z_len - 4.0),
        ],
        radius=18.0,
        segs_per_corner=6,
    )
    draw_poly_3d(sk_cr, [(xx, -28.0, zz) for (xx, zz) in core_xz])
    ext_cr = add_extrude(
        comp_core, sk_cr, "72.0 mm", (0, 1, 0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation, "Ext_P4B_Core"
    )
    core_body = ext_cr.bodies.item(0)
    core_body.name = "Body_P4B_Fluted_Core"

    # 6 Cylindrical Pen/Tool Wells cut down into P4B
    pen_centers = [
        (x_edge + 26.0, z0 + 28.0),
        (x_edge + 56.0, z0 + 28.0),
        (x_edge + 26.0, z0 + 58.0),
        (x_edge + 56.0, z0 + 58.0),
        (x_edge + 26.0, z0 + 88.0),
        (x_edge + 56.0, z0 + 88.0),
    ]
    p_ctop = make_offset_plane(comp_core, comp_core.xZConstructionPlane, "44.0 mm", "Plane_P4B_Top")
    sk_pens = comp_core.sketches.add(p_ctop)
    sk_pens.name = "Sk_P4B_PenWells"
    for px, pz in pen_centers:
        sk_pens.sketchCurves.sketchCircles.addByCenterRadius(pt_sk(sk_pens, px, 44.0, pz), mm(11.5))
    add_extrude(
        comp_core, sk_pens, "44.0 mm", (0, -1, 0), adsk.fusion.FeatureOperations.CutFeatureOperation, "Ext_Cut_P4B_PenWells", core_body
    )

    # Lower Front Micro-Drawer Bay cut into P4B (Z = z0+z_len-4 forward)
    z_front_core = z0 + z_len - 4.0
    p_dbay = make_offset_plane(comp_core, comp_core.xYConstructionPlane, f"{z_front_core} mm", "Plane_P4B_DrawerBay")
    sk_dbay = comp_core.sketches.add(p_dbay)
    sk_dbay.name = "Sk_P4B_DrawerCavity"
    draw_poly_3d(
        sk_dbay,
        [
            (x_edge + 16.0, -24.0, z_front_core),
            (x_edge + out_w - 12.0, -24.0, z_front_core),
            (x_edge + out_w - 12.0, -2.0, z_front_core),
            (x_edge + 16.0, -2.0, z_front_core),
        ],
    )
    add_extrude(
        comp_core, sk_dbay, "68.0 mm", (0, 0, -1), adsk.fusion.FeatureOperations.CutFeatureOperation, "Ext_Cut_P4B_DrawerBay", core_body
    )

    # 4. W4B: 6 mm Top Warm Walnut Pen Collar Plate (Y = +44..+50 mm)
    occ_wtop = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp_wtop = occ_wtop.component
    comp_wtop.name = "W4B_Top_Walnut_Pen_Collar"
    p_wt = make_offset_plane(comp_wtop, comp_wtop.xZConstructionPlane, "44.0 mm", "Plane_W4B_Collar")
    sk_wt = comp_wtop.sketches.add(p_wt)
    sk_wt.name = "Sk_W4B_Walnut_Bezel"
    draw_poly_3d(sk_wt, [(xx, 44.0, zz) for (xx, zz) in stadium_xz])
    for px, pz in pen_centers:
        sk_wt.sketchCurves.sketchCircles.addByCenterRadius(pt_sk(sk_wt, px, 44.0, pz), mm(11.5))
    ext_wt = add_extrude(
        comp_wtop, sk_wt, "wood_thick_panel", (0, 1, 0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation, "Ext_W4B_Collar"
    )
    ext_wt.bodies.item(0).name = "Body_W4B_Top_Walnut_Collar"

    return occ_cl, occ_wbot, occ_core, occ_wtop


def _build_walnut_micro_drawer_and_spire(assy_comp: adsk.fusion.Component, v: dict) -> tuple:
    """Build P4C Cyber-Red Micro-Drawer + W4C Walnut Drawer Faceplate + P4D Airfoil Spire."""
    x_edge = v["table_length"]
    z0 = v["wing_z_start"]
    z_len = v["wing_z_len"]
    out_w = v["wing_outboard_w"]
    clr = v["fit_clearance"]
    z_front_core = z0 + z_len - 4.0

    # P4C: Cyber-Red Magnetic Micro-Drawer Box
    occ_drw = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp_drw = occ_drw.component
    comp_drw.name = "P4C_Magnetic_Micro_Drawer_Box"
    dx0 = x_edge + 16.0 + clr
    dx1 = x_edge + out_w - 12.0 - clr
    dy0 = -24.0 + clr
    dy1 = -2.0 - clr
    dz0 = z_front_core - 66.0

    p_d = make_offset_plane(comp_drw, comp_drw.xZConstructionPlane, f"{dy0} mm", "Plane_P4C_Drawer")
    sk_d = comp_drw.sketches.add(p_d)
    sk_d.name = "Sk_P4C_Box"
    draw_poly_3d(sk_d, [(dx0, dy0, dz0), (dx1, dy0, dz0), (dx1, dy0, z_front_core), (dx0, dy0, z_front_core)])
    ext_d = add_extrude(
        comp_drw, sk_d, f"{dy1 - dy0} mm", (0, 1, 0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation, "Ext_P4C_Box"
    )
    d_body = ext_d.bodies.item(0)
    d_body.name = "Body_P4C_Drawer_Box"

    p_dcav = make_offset_plane(comp_drw, comp_drw.xZConstructionPlane, f"{dy1} mm", "Plane_P4C_TrayCut")
    sk_dcav = comp_drw.sketches.add(p_dcav)
    sk_dcav.name = "Sk_P4C_TrayCut"
    draw_poly_3d(
        sk_dcav,
        [(dx0 + 2.5, dy1, dz0 + 4.0), (dx1 - 2.5, dy1, dz0 + 4.0), (dx1 - 2.5, dy1, z_front_core - 2.5), (dx0 + 2.5, dy1, z_front_core - 2.5)],
    )
    add_extrude(
        comp_drw, sk_dcav, f"{(dy1 - dy0) - 3.0} mm", (0, -1, 0), adsk.fusion.FeatureOperations.CutFeatureOperation, "Ext_Cut_P4C_Tray", d_body
    )

    # W4C: 6 mm Warm Walnut Front Drawer Faceplate (flush designer detail!)
    occ_wf = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp_wf = occ_wf.component
    comp_wf.name = "W4C_Walnut_Drawer_Faceplate"
    p_wf = make_offset_plane(comp_wf, comp_wf.xYConstructionPlane, f"{z_front_core} mm", "Plane_W4C_Face")
    sk_wf = comp_wf.sketches.add(p_wf)
    sk_wf.name = "Sk_W4C_RoundedFace"
    face_xy = sample_rounded_poly_2d(
        [(dx0 - 2.0, dy0 - 1.0), (dx1 + 2.0, dy0 - 1.0), (dx1 + 2.0, dy1 + 1.0), (dx0 - 2.0, dy1 + 1.0)],
        radius=4.5,
        segs_per_corner=4,
    )
    draw_poly_3d(sk_wf, [(xx, yy, z_front_core) for (xx, yy) in face_xy])
    ext_wf = add_extrude(
        comp_wf, sk_wf, "wood_thick_panel", (0, 0, 1), adsk.fusion.FeatureOperations.NewBodyFeatureOperation, "Ext_W4C_Face"
    )
    ext_wf.bodies.item(0).name = "Body_W4C_Walnut_Drawer_Face"

    # P4D: Swept Aerodynamic Cyber-Red Airfoil Mouse Bungee Spire mounted on top rear of W4B
    occ_sp = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp_sp = occ_sp.component
    comp_sp.name = "P4D_Airfoil_Chimera_Spire"
    y_sp_base = 50.0                                           # Top of W4B Walnut Collar
    bh = v["bungee_height"]                                    # 96.0 mm
    p_sp = make_offset_plane(comp_sp, comp_sp.xYConstructionPlane, f"{z0 + 4.0} mm", "Plane_P4D_Airfoil")
    sk_sp = comp_sp.sketches.add(p_sp)
    sk_sp.name = "Sk_P4D_Swept_Airfoil"
    airfoil_xy = sample_rounded_poly_2d(
        [
            (x_edge + 24.0, y_sp_base),
            (x_edge + 56.0, y_sp_base),
            (x_edge + 36.0, y_sp_base + 0.55 * bh),
            (x_edge + 6.0, y_sp_base + bh),
            (x_edge + 2.0, y_sp_base + bh - 8.0),
            (x_edge + 24.0, y_sp_base + 0.50 * bh),
        ],
        radius=5.0,
        segs_per_corner=5,
    )
    draw_poly_3d(sk_sp, [(xx, yy, z0 + 4.0) for (xx, yy) in airfoil_xy])
    ext_sp = add_extrude(
        comp_sp, sk_sp, "14.0 mm", (0, 0, 1), adsk.fusion.FeatureOperations.NewBodyFeatureOperation, "Ext_P4D_Airfoil"
    )
    ext_sp.bodies.item(0).name = "Body_P4D_Airfoil_Spire"

    return occ_drw, occ_wf, occ_sp, (0.5 * (dx0 + dx1), 0.5 * (dy0 + dy1), dz0)


def build_product(design: adsk.fusion.Design, parent_comp: adsk.fusion.Component = None) -> adsk.fusion.Occurrence:
    if parent_comp is None:
        parent_comp = design.rootComponent

    v = register_parameters(design)

    assy_occ = parent_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    assy_comp = assy_occ.component
    assy_comp.name = "Product4_HexWingSpire"

    occ_cl, occ_wb, occ_cr, occ_wt = _build_walnut_wing_caddy(assy_comp, v)
    occ_drw, occ_wf, occ_sp, d_xyz = _build_walnut_micro_drawer_and_spire(assy_comp, v)

    ab = assy_comp.asBuiltJoints
    for c_occ, p_occ, jn in [
        (occ_wb, occ_cl, "Joint_Rigid_BottomWalnut_to_Clamp"),
        (occ_cr, occ_wb, "Joint_Rigid_FlutedCore_to_BottomWalnut"),
        (occ_wt, occ_cr, "Joint_Rigid_TopWalnut_to_FlutedCore"),
        (occ_wf, occ_drw, "Joint_Rigid_WalnutFace_to_DrawerBox"),
        (occ_sp, occ_wt, "Joint_Rigid_AirfoilSpire_to_TopWalnut"),
    ]:
        ji = ab.createInput(c_occ, p_occ, None)
        ji.setAsRigidJointMotion()
        j = ab.add(ji)
        j.name = jn

    dx, dy, dz = d_xyz
    sk_sl = occ_cr.component.sketches.add(occ_cr.component.xZConstructionPlane)
    sk_sl.name = "Sk_MicroDrawer_Slider_Axis"
    sl_line = sk_sl.sketchCurves.sketchLines.addByTwoPoints(pt_sk(sk_sl, dx, dy, dz), pt_sk(sk_sl, dx, dy, dz + 55.0))
    sl_proxy = sl_line.createForAssemblyContext(occ_cr)
    sl_geom = adsk.fusion.JointGeometry.createByCurve(sl_proxy, adsk.fusion.JointKeyPointTypes.StartKeyPoint)
    sl_in = ab.createInput(occ_drw, occ_cr, sl_geom)
    sl_in.setAsSliderJointMotion(adsk.fusion.JointDirections.CustomJointDirection, sl_proxy)
    sl_j = ab.add(sl_in)
    sl_j.name = "Joint_Slider_Walnut_MicroDrawer"

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
        app.executeTextCommand('PTransaction.Start "Build Product 4 Designer Hybrid"')
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
            ui.messageBox(f"Product4_HexWingSpire failed:\n{err}")
