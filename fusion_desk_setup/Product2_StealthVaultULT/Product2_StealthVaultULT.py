# -*- coding: utf-8 -*-
"""
Product 2 — StealthVault 280 + SideDock ULT (Designer Hybrid Wood/Print v2)
===========================================================================
Replaces heavy 196 mm printed plastic walls with twin sculpted Matte-Black
3D-printed C-clamp arches (`P2A`, `P2B`, only 28 mm wide each!) joined by
6 mm Warm Walnut/Birch wood panels (`W2A`, `W2B`) and a curved Wood Headphone
Saddle (`W2C`)—slashing 3D filament by ~70% while looking like luxury studio
furniture!

Individual Pieces Created as Separate Named Components:
  - `P2A_Rear_Sculpted_Clamp_Arch`  (3D-Printed Matte-Black PETG, 58 x 132 x 28 mm)
  - `P2B_Front_Sculpted_Clamp_Arch` (3D-Printed Matte-Black PETG, 58 x 132 x 28 mm)
  - `W2A_Bottom_Vent_Wood_Tray`     (6 mm Wood, 188 x 54 x 6 mm, stadium vents)
  - `W2B_Outer_Walnut_Shield_Panel` (6 mm Wood, 188 x 86 x 6 mm, hides 280W brick!)
  - `P2C_Sculpted_Cable_Spine`      (3D-Printed Matte-Black PETG, rounded raceway)
  - `P2D_ULT_608_Clamp_Knuckle`     (3D-Printed Matte-Black PETG, 608 bearing hub)
  - `P2E_ULT_Axle_Collar`           (3D-Printed Cyber-Red PETG, Ø7.88 mm 608 pin)
  - `W2C_Walnut_ULT_Saddle_Arch`    (Wood parabolic 38 mm wide Sony ULT WEAR cradle)
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


def stadium_pts_2d(cu: float, cv: float, total_u: float, total_v: float, segs: int = 7) -> list:
    pts = []
    if total_u >= total_v:
        r = 0.5 * total_v
        du = 0.5 * total_u - r
        for s in range(segs + 1):
            a = -0.5 * math.pi + math.pi * (s / float(segs))
            pts.append((cu + du + r * math.cos(a), cv + r * math.sin(a)))
        for s in range(segs + 1):
            a = 0.5 * math.pi + math.pi * (s / float(segs))
            pts.append((cu - du + r * math.cos(a), cv + r * math.sin(a)))
    else:
        r = 0.5 * total_u
        dv = 0.5 * total_v - r
        for s in range(segs + 1):
            a = math.pi * (s / float(segs))
            pts.append((cu + r * math.cos(a), cv + dv + r * math.sin(a)))
        for s in range(segs + 1):
            a = math.pi + math.pi * (s / float(segs))
            pts.append((cu + r * math.cos(a), cv - dv + r * math.sin(a)))
    return pts


def register_parameters(design: adsk.fusion.Design) -> dict:
    v = {}
    v["table_thickness"] = ensure_param(design, "table_thickness", "18.0 mm", "mm", "Wood tabletop thickness")
    v["mat_thickness"] = ensure_param(design, "mat_thickness", "3.0 mm", "mm", "Desk mat thickness")
    v["wood_thick_panel"] = ensure_param(design, "wood_thick_panel", "6.0 mm", "mm", "6 mm Walnut/Birch sheet thickness")
    v["clamp_pad_t"] = ensure_param(design, "clamp_pad_t", "2.0 mm", "mm", "Soft non-marring pad thickness")
    v["clamp_jaw_reach"] = ensure_param(design, "clamp_jaw_reach", "22.0 mm", "mm", "Inward clamp jaw reach")
    v["fit_clearance"] = ensure_param(design, "fit_clearance", "0.25 mm", "mm", "Nominal 3D-print assembly clearance")
    v["vault_z_start"] = ensure_param(design, "vault_z_start", "14.0 mm", "mm", "Rear wall clearance to StealthVault")
    v["vault_length"] = ensure_param(design, "vault_length", "196.0 mm", "mm", "Total Z length of StealthVault")
    v["ult_band_w"] = ensure_param(design, "ult_band_w", "38.0 mm", "mm", "Contoured wood saddle width for Sony ULT WEAR")
    v["bearing_od"] = ensure_param(design, "bearing_od", "22.0 mm", "mm", "608 bearing outer diameter")
    v["bearing_id"] = ensure_param(design, "bearing_id", "8.0 mm", "mm", "608 bearing inner diameter")
    v["bearing_w"] = ensure_param(design, "bearing_w", "7.0 mm", "mm", "608 bearing width")
    v["bearing_bore_clear"] = ensure_param(design, "bearing_bore_clear", "0.15 mm", "mm", "Press-fit bore allowance for 608")
    v["m4_insert_od"] = ensure_param(design, "m4_insert_od", "5.6 mm", "mm", "M4 brass heat-set pilot bore")
    return v


def _build_hybrid_stealth_vault(assy_comp: adsk.fusion.Component, v: dict) -> tuple:
    """Build Twin Sculpted 28 mm Clamp Arches (P2A, P2B) + 6 mm Wood Panels (W2A, W2B) + Cable Spine (P2C)."""
    z0 = v["vault_z_start"]                                    # 14.0 mm
    v_len = v["vault_length"]                                  # 196.0 mm
    arch_w = 28.0                                              # Compact 28 mm 3D-printed end arches!
    y_top_pad = v["mat_thickness"] + v["clamp_pad_t"]          # +5.0 mm
    y_bot_pad = -v["table_thickness"] - v["clamp_pad_t"] - 4.0 # -24.0 mm
    jaw_reach = v["clamp_jaw_reach"]                           # 22.0 mm
    tw = v["wood_thick_panel"]                                 # 6.0 mm wood

    # Sculpted rounded C-clamp + under-desk cradle rib profile
    raw_arch_xy = [
        (-18.0, y_top_pad + 6.5),
        (jaw_reach - 5.0, y_top_pad + 6.5),
        (jaw_reach, y_top_pad + 2.5),
        (jaw_reach, y_top_pad),
        (0.0, y_top_pad),
        (0.0, y_bot_pad),
        (jaw_reach, y_bot_pad),
        (jaw_reach, -34.0),
        (40.0, -38.0),
        (40.0, -122.0),
        (-18.0, -122.0),
        (-18.0, -114.0),
        (32.0, -114.0),
        (32.0, -40.0),
        (-12.0, -40.0),
        (-18.0, -34.0),
    ]
    smooth_arch_xy = sample_rounded_poly_2d(raw_arch_xy, radius=4.0, segs_per_corner=4)

    arches = []
    for cname, bname, z_expr, z_val in [
        ("P2A_Rear_Sculpted_Clamp_Arch", "Body_P2A_Rear_Clamp_Arch", "vault_z_start", z0),
        ("P2B_Front_Sculpted_Clamp_Arch", "Body_P2B_Front_Clamp_Arch", f"vault_z_start + vault_length - {arch_w} mm", z0 + v_len - arch_w),
    ]:
        occ = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        comp = occ.component
        comp.name = cname
        pl = make_offset_plane(comp, comp.xYConstructionPlane, z_expr, f"Plane_{cname}")
        sk = comp.sketches.add(pl)
        sk.name = f"Sk_{cname}_Curve"
        draw_poly_3d(sk, [(xx, yy, z_val) for (xx, yy) in smooth_arch_xy])
        ext = add_extrude(
            comp, sk, f"{arch_w} mm", (0, 0, 1), adsk.fusion.FeatureOperations.NewBodyFeatureOperation, f"Ext_{cname}"
        )
        body = ext.bodies.item(0)
        body.name = bname

        # M4 Heat-Set Clamp Bore
        p_m4 = make_offset_plane(comp, comp.xZConstructionPlane, f"{y_bot_pad} mm", f"Plane_{cname}_M4")
        sk_m4 = comp.sketches.add(p_m4)
        sk_m4.name = f"Sk_{cname}_M4_Bore"
        sk_m4.sketchCurves.sketchCircles.addByCenterRadius(
            pt_sk(sk_m4, 11.0, y_bot_pad, z_val + 0.5 * arch_w), mm(0.5 * v["m4_insert_od"])
        )
        add_extrude(
            comp, sk_m4, "12.0 mm", (0, -1, 0), adsk.fusion.FeatureOperations.CutFeatureOperation, f"Ext_Cut_{cname}_M4", body
        )
        arches.append(occ)

    # W2A: 6 mm Wood Slotted Bottom Tray (184 x 52 x 6 mm) bridging P2A and P2B
    occ_wbot = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp_wbot = occ_wbot.component
    comp_wbot.name = "W2A_Bottom_Vent_Wood_Tray"
    p_wb = make_offset_plane(comp_wbot, comp_wbot.xZConstructionPlane, "-120.0 mm", "Plane_W2A_Base")
    sk_wb = comp_wbot.sketches.add(p_wb)
    sk_wb.name = "Sk_W2A_WoodTray"
    draw_poly_3d(
        sk_wb,
        [
            (-16.0, -120.0, z0 + 6.0),
            (36.0, -120.0, z0 + 6.0),
            (36.0, -120.0, z0 + v_len - 6.0),
            (-16.0, -120.0, z0 + v_len - 6.0),
        ],
    )
    ext_wb = add_extrude(
        comp_wbot, sk_wb, "wood_thick_panel", (0, 1, 0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation, "Ext_W2A_WoodTray"
    )
    wb_body = ext_wb.bodies.item(0)
    wb_body.name = "Body_W2A_Bottom_Wood_Tray"

    sk_wvents = comp_wbot.sketches.add(p_wb)
    sk_wvents.name = "Sk_W2A_StadiumVents"
    for idx in range(4):
        zv = z0 + 36.0 + idx * 38.0
        pill = stadium_pts_2d(10.0, zv, 28.0, 22.0, segs=6)
        draw_poly_3d(sk_wvents, [(xx, -120.0, zz) for (xx, zz) in pill])
    add_extrude(
        comp_wbot, sk_wvents, "wood_thick_panel + 1 mm", (0, 1, 0), adsk.fusion.FeatureOperations.CutFeatureOperation, "Ext_Cut_W2A_Vents", wb_body
    )

    # W2B: 6 mm Warm Walnut Outer Sightline Shield Panel (184 x 84 x 6 mm — completely hides 280W brick!)
    occ_wside = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp_wside = occ_wside.component
    comp_wside.name = "W2B_Outer_Walnut_Shield_Panel"
    p_ws = make_offset_plane(comp_wside, comp_wside.yZConstructionPlane, "-24.0 mm", "Plane_W2B_Side")
    sk_ws = comp_wside.sketches.add(p_ws)
    sk_ws.name = "Sk_W2B_Rounded_Shield"
    shield_yz = sample_rounded_poly_2d(
        [
            (-120.0, z0 + 6.0),
            (-120.0, z0 + v_len - 6.0),
            (-36.0, z0 + v_len - 6.0),
            (-36.0, z0 + 6.0),
        ],
        radius=10.0,
        segs_per_corner=5,
    )
    draw_poly_3d(sk_ws, [(-24.0, yy, zz) for (yy, zz) in shield_yz])
    ext_ws = add_extrude(
        comp_wside, sk_ws, "wood_thick_panel", (1, 0, 0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation, "Ext_W2B_Walnut_Shield"
    )
    ext_ws.bodies.item(0).name = "Body_W2B_Walnut_Shield"

    # P2C: Sculpted Pill-Profile Vertical Cable Spine
    occ_sp = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp_sp = occ_sp.component
    comp_sp.name = "P2C_Sculpted_Cable_Spine"
    yb = y_top_pad + 6.5
    p_sp = make_offset_plane(comp_sp, comp_sp.xZConstructionPlane, f"{yb} mm", "Plane_CableSpine")
    sk_sp = comp_sp.sketches.add(p_sp)
    sk_sp.name = "Sk_Sculpted_CableSpine"
    sp_xz = sample_rounded_poly_2d(
        [
            (-14.0, z0),
            (8.0, z0),
            (8.0, z0 + 26.0),
            (4.0, z0 + 26.0),
            (4.0, z0 + 4.0),
            (-10.0, z0 + 4.0),
            (-10.0, z0 + 22.0),
            (0.0, z0 + 22.0),
            (0.0, z0 + 26.0),
            (-14.0, z0 + 26.0),
        ],
        radius=2.5,
        segs_per_corner=3,
    )
    draw_poly_3d(sk_sp, [(xx, yb, zz) for (xx, zz) in sp_xz])
    ext_sp = add_extrude(
        comp_sp, sk_sp, "70.0 mm", (0, 1, 0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation, "Ext_CableSpine"
    )
    ext_sp.bodies.item(0).name = "Body_P2C_Cable_Spine"

    return arches[0], arches[1], occ_wbot, occ_wside, occ_sp


def _build_hybrid_sidedock_ult(assy_comp: adsk.fusion.Component, v: dict) -> tuple:
    """Build P2D Sculpted 608 Clamp Knuckle + P2E Axle Collar + W2C Carved Walnut ULT Saddle Arch."""
    z_hub = v["vault_z_start"] + v["vault_length"] + 2.0      # 212.0 mm
    hub_len = 48.0                                            # Z = 212..260 mm
    y_top_pad = v["mat_thickness"] + v["clamp_pad_t"]         # +5.0 mm
    y_bot_pad = -v["table_thickness"] - v["clamp_pad_t"] - 4.0# -24.0 mm
    jaw_reach = v["clamp_jaw_reach"]                          # 22.0 mm
    piv_x = -14.0
    piv_z = z_hub + 0.5 * hub_len                             # 236.0 mm

    occ_hub = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp_hub = occ_hub.component
    comp_hub.name = "P2D_ULT_608_Clamp_Knuckle"
    p_hub = make_offset_plane(comp_hub, comp_hub.xYConstructionPlane, f"{z_hub} mm", "Plane_ULT_Knuckle")
    sk_hub = comp_hub.sketches.add(p_hub)
    sk_hub.name = "Sk_ULT_Sculpted_Knuckle"
    knuckle_xy = sample_rounded_poly_2d(
        [
            (-28.0, y_top_pad + 6.5),
            (jaw_reach - 5.0, y_top_pad + 6.5),
            (jaw_reach, y_top_pad + 2.5),
            (jaw_reach, y_top_pad),
            (0.0, y_top_pad),
            (0.0, y_bot_pad),
            (jaw_reach, y_bot_pad),
            (jaw_reach, y_bot_pad - 12.0),
            (-28.0, y_bot_pad - 12.0),
        ],
        radius=4.5,
        segs_per_corner=4,
    )
    draw_poly_3d(sk_hub, [(xx, yy, z_hub) for (xx, yy) in knuckle_xy])
    ext_hub = add_extrude(
        comp_hub, sk_hub, f"{hub_len} mm", (0, 0, 1), adsk.fusion.FeatureOperations.NewBodyFeatureOperation, "Ext_ULT_Knuckle"
    )
    hub_body = ext_hub.bodies.item(0)
    hub_body.name = "Body_P2D_ULT_Bearing_Hub"

    y_brg_face = y_bot_pad - 12.0
    p_brg = make_offset_plane(comp_hub, comp_hub.xZConstructionPlane, f"{y_brg_face} mm", "Plane_ULT_608_Bore")
    sk_brg = comp_hub.sketches.add(p_brg)
    sk_brg.name = "Sk_ULT_608_Pocket"
    sk_brg.sketchCurves.sketchCircles.addByCenterRadius(
        pt_sk(sk_brg, piv_x, y_brg_face, piv_z), mm(0.5 * (v["bearing_od"] + v["bearing_bore_clear"]))
    )
    add_extrude(
        comp_hub, sk_brg, "bearing_w + 0.3 mm", (0, 1, 0), adsk.fusion.FeatureOperations.CutFeatureOperation, "Ext_Cut_ULT_608", hub_body
    )

    # P2E: Compact 3D-Printed Cyber-Red 608 Shaft Collar
    y_arm_top = y_brg_face - 0.5
    occ_col = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp_col = occ_col.component
    comp_col.name = "P2E_ULT_Axle_Collar"
    p_col = make_offset_plane(comp_col, comp_col.xZConstructionPlane, f"{y_arm_top - 6.0} mm", "Plane_ULT_Collar")
    sk_col = comp_col.sketches.add(p_col)
    sk_col.name = "Sk_ULT_Collar_Disc"
    sk_col.sketchCurves.sketchCircles.addByCenterRadius(pt_sk(sk_col, piv_x, y_arm_top - 6.0, piv_z), mm(12.0))
    ext_col = add_extrude(
        comp_col, sk_col, "6.0 mm", (0, 1, 0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation, "Ext_ULT_Collar"
    )
    col_body = ext_col.bodies.item(0)
    col_body.name = "Body_P2E_ULT_Axle_Collar"

    p_pin = make_offset_plane(comp_col, comp_col.xZConstructionPlane, f"{y_arm_top} mm", "Plane_ULT_Pin")
    sk_pin = comp_col.sketches.add(p_pin)
    sk_pin.name = "Sk_ULT_608_Pin"
    sk_pin.sketchCurves.sketchCircles.addByCenterRadius(
        pt_sk(sk_pin, piv_x, y_arm_top, piv_z), mm(0.5 * (v["bearing_id"] - 0.12))
    )
    add_extrude(
        comp_col, sk_pin, "bearing_w + 0.4 mm", (0, 1, 0), adsk.fusion.FeatureOperations.JoinFeatureOperation, "Ext_Join_ULT_Pin", col_body
    )

    # W2C: Carved Warm Walnut Wood Parabolic Headphone Saddle (38 mm wide organic arch!)
    occ_wood = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp_wood = occ_wood.component
    comp_wood.name = "W2C_Walnut_ULT_Saddle_Arch"
    z_s = piv_z - 0.5 * v["ult_band_w"]
    p_arm = make_offset_plane(comp_wood, comp_wood.xYConstructionPlane, f"{z_s} mm", "Plane_W2C_WoodArch")
    sk_arm = comp_wood.sketches.add(p_arm)
    sk_arm.name = "Sk_W2C_Organic_Saddle"
    saddle_xy = sample_rounded_poly_2d(
        [
            (piv_x + 12.0, y_arm_top - 6.0),
            (piv_x + 12.0, y_arm_top - 16.0),
            (piv_x - 26.0, y_arm_top - 24.0),
            (piv_x - 54.0, y_arm_top - 25.0),
            (piv_x - 80.0, y_arm_top - 18.0),
            (piv_x - 88.0, y_arm_top - 5.0),
            (piv_x - 80.0, y_arm_top - 5.0),
            (piv_x - 72.0, y_arm_top - 13.0),
            (piv_x - 50.0, y_arm_top - 16.0),
            (piv_x - 10.0, y_arm_top - 6.0),
        ],
        radius=5.0,
        segs_per_corner=5,
    )
    draw_poly_3d(sk_arm, [(xx, yy, z_s) for (xx, yy) in saddle_xy])
    ext_w = add_extrude(
        comp_wood, sk_arm, "ult_band_w", (0, 0, 1), adsk.fusion.FeatureOperations.NewBodyFeatureOperation, "Ext_W2C_WoodSaddle"
    )
    ext_w.bodies.item(0).name = "Body_W2C_Walnut_ULT_Saddle"

    return occ_hub, occ_col, occ_wood, (piv_x, y_arm_top, piv_z)


def build_product(design: adsk.fusion.Design, parent_comp: adsk.fusion.Component = None) -> adsk.fusion.Occurrence:
    if parent_comp is None:
        parent_comp = design.rootComponent

    v = register_parameters(design)

    assy_occ = parent_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    assy_comp = assy_occ.component
    assy_comp.name = "Product2_StealthVaultULT"

    occ_a1, occ_a2, occ_wb, occ_ws, occ_sp = _build_hybrid_stealth_vault(assy_comp, v)
    occ_hub, occ_col, occ_wsad, piv_xyz = _build_hybrid_sidedock_ult(assy_comp, v)

    ab = assy_comp.asBuiltJoints
    for child_o, parent_o, jname in [
        (occ_a2, occ_a1, "Joint_Rigid_FrontArch_to_RearArch"),
        (occ_wb, occ_a1, "Joint_Rigid_BottomWood_to_Vault"),
        (occ_ws, occ_a1, "Joint_Rigid_WalnutShield_to_Vault"),
        (occ_sp, occ_a1, "Joint_Rigid_CableSpine_to_Vault"),
        (occ_hub, occ_a2, "Joint_Rigid_ULTKnuckle_LeftEdge"),
        (occ_wsad, occ_col, "Joint_Rigid_WoodSaddle_to_Collar"),
    ]:
        ji = ab.createInput(child_o, parent_o, None)
        ji.setAsRigidJointMotion()
        j = ab.add(ji)
        j.name = jname

    px, py, pz = piv_xyz
    sk_rev = occ_hub.component.sketches.add(occ_hub.component.xYConstructionPlane)
    sk_rev.name = "Sk_ULT_608_Revolute_Axis"
    rev_line = sk_rev.sketchCurves.sketchLines.addByTwoPoints(pt_sk(sk_rev, px, py, pz), pt_sk(sk_rev, px, py + 8.0, pz))
    rev_proxy = rev_line.createForAssemblyContext(occ_hub)
    rev_geom = adsk.fusion.JointGeometry.createByCurve(rev_proxy, adsk.fusion.JointKeyPointTypes.StartKeyPoint)
    rev_in = ab.createInput(occ_col, occ_hub, rev_geom)
    rev_in.setAsRevoluteJointMotion(adsk.fusion.JointDirections.CustomJointDirection, rev_proxy)
    rev_j = ab.add(rev_in)
    rev_j.name = "Joint_Revolute_ULT_SwingArm"

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
        app.executeTextCommand('PTransaction.Start "Build Product 2 Designer Hybrid"')
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
            ui.messageBox(f"Product2_StealthVaultULT failed:\n{err}")
