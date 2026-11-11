# -*- coding: utf-8 -*-
"""
Product 5 — HoloBuddy: Designer Hybrid Optical Companion (v2)
=============================================================
Upgrades HoloBuddy into a boutique Teenage-Engineering / Grovemade style
desktop companion with squircle-rounded Stealth Matte-Black optical geometry,
Warm Walnut side cheek panels (`W5A_Left`/`W5A_Right`), a floating Cyber-Red
magnetic brow hood (`P5C`), a swept cantilever `DT-30` right-wing arm (`P5D`,
mated cleanly to `P1E_Right_DT30_Collar` at `X = 459.0 mm`), and a freestanding
Warm Walnut + `608` coaster dock (`W5B` + `P5E`).

Individual Pieces Created as Separate Named Components:
  - `P5A_Squircle_Optical_Core`     (3D-Printed Matte-Black PETG, prism + OLED + light-trap)
  - `W5A_Left_Walnut_Cheek_Panel`   (6 mm Warm Walnut Wood side inlay, 30 x 34 x 6 mm)
  - `W5A_Right_Walnut_Cheek_Panel`  (6 mm Warm Walnut Wood side inlay, 30 x 34 x 6 mm)
  - `P5B_Sculpted_Electronics_Base` (3D-Printed Matte-Black PETG, ESP32-C3 + INMP441 + 608 pin)
  - `P5C_Floating_Magnetic_Visor`   (3D-Printed Cyber-Red PETG, curved N52 snap glare hood)
  - `P5D_Sculpted_Right_Wing_Arm`   (3D-Printed Matte-Black PETG, DT-30 + 608 swivel arm)
  - `W5B_Walnut_Pedestal_Coaster`   (6 mm Warm Walnut Wood freestanding coaster, Ø72 x 6 mm)
  - `P5E_Pedestal_608_Hub`          (3D-Printed Matte-Black PETG 608 hub for W5B coaster)
  - `G5_K9_BeamSplitter_Cube`       (Purchased 25.4 mm 50:50 K9 glass optical cube)
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
    v["wood_thick_panel"] = ensure_param(design, "wood_thick_panel", "6.0 mm", "mm", "6 mm Warm Walnut wood thickness")
    v["dovetail_w"] = ensure_param(design, "dovetail_w", "30.0 mm", "mm", "DT-30 dovetail root width")
    v["dovetail_depth"] = ensure_param(design, "dovetail_depth", "6.0 mm", "mm", "DT-30 dovetail engagement depth")
    v["fit_clearance"] = ensure_param(design, "fit_clearance", "0.25 mm", "mm", "3D-print sliding clearance")
    v["bearing_od"] = ensure_param(design, "bearing_od", "22.0 mm", "mm", "608 bearing outer diameter")
    v["bearing_id"] = ensure_param(design, "bearing_id", "8.0 mm", "mm", "608 bearing inner diameter")
    v["bearing_w"] = ensure_param(design, "bearing_w", "7.0 mm", "mm", "608 bearing width")
    v["bearing_bore_clear"] = ensure_param(design, "bearing_bore_clear", "0.15 mm", "mm", "608 press-fit allowance")
    v["magnet_d"] = ensure_param(design, "magnet_d", "6.0 mm", "mm", "6x3 mm N52 magnet OD")
    v["magnet_h"] = ensure_param(design, "magnet_h", "3.0 mm", "mm", "6x3 mm N52 magnet height")
    v["magnet_clear"] = ensure_param(design, "magnet_clear", "0.20 mm", "mm", "Magnet pocket clearance")
    v["prism_size"] = ensure_param(design, "prism_size", "25.4 mm", "mm", "1-inch K9 beam-splitter cube size")
    v["prism_clear"] = ensure_param(design, "prism_clear", "0.40 mm", "mm", "Prism pocket total clearance")
    v["holo_wing_x_collar"] = ensure_param(design, "holo_wing_x_collar", "459.0 mm", "mm", "Right DT-30 collar outer face X")
    v["holo_piv_x"] = ensure_param(design, "holo_piv_x", "504.0 mm", "mm", "HoloBuddy 608 swivel axis X")
    v["holo_piv_y"] = ensure_param(design, "holo_piv_y", "92.0 mm", "mm", "HoloBuddy wing deck top Y (52mm above mouse!)")
    v["holo_piv_z"] = ensure_param(design, "holo_piv_z", "86.0 mm", "mm", "HoloBuddy 608 swivel axis Z")
    return v


def _build_wing_arm(assy_comp: adsk.fusion.Component, v: dict) -> adsk.fusion.Occurrence:
    """Build P5D Sculpted Right-Wing Cantilever Arm mating to P1E_Right_DT30_Collar at X=459.0 mm."""
    occ = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp = occ.component
    comp.name = "P5D_Sculpted_Right_Wing_Arm"

    x_face = v["holo_wing_x_collar"]                           # 459.0 mm
    px = v["holo_piv_x"]                                       # 504.0 mm
    py = v["holo_piv_y"]                                       # 92.0 mm
    pz = v["holo_piv_z"]                                       # 86.0 mm
    dt_z_mid = 46.0
    dt_d = v["dovetail_depth"] - v["fit_clearance"]            # 5.75 mm
    half_root = 0.5 * v["dovetail_w"] - v["fit_clearance"]     # 14.75 mm
    flare = dt_d / math.tan(math.radians(60.0))
    half_mouth = half_root - flare

    # 1. Male DT-30 Tongue (Y = 88..131 mm -> 43 mm engagement)
    p_dt = make_offset_plane(comp, comp.xZConstructionPlane, "88.0 mm", "Plane_P5D_DT30")
    sk_dt = comp.sketches.add(p_dt)
    sk_dt.name = "Sk_P5D_DT30_Tongue"
    draw_poly_3d(
        sk_dt,
        [
            (x_face, 88.0, dt_z_mid - half_mouth),
            (x_face - dt_d, 88.0, dt_z_mid - half_root),
            (x_face - dt_d, 88.0, dt_z_mid + half_root),
            (x_face, 88.0, dt_z_mid + half_mouth),
        ],
    )
    ext_dt = add_extrude(
        comp, sk_dt, "43.0 mm", (0, 1, 0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation, "Ext_P5D_Tongue"
    )
    arm_body = ext_dt.bodies.item(0)
    arm_body.name = "Body_P5D_Wing_Arm"

    # 2. Swept Organic Cantilever Deck + Rounded 608 Hub (Y = 80..92 mm)
    p_arm = make_offset_plane(comp, comp.xZConstructionPlane, f"{py - 12.0} mm", "Plane_P5D_Deck")
    sk_arm = comp.sketches.add(p_arm)
    sk_arm.name = "Sk_P5D_Swept_Arm"
    arm_xz = sample_rounded_poly_2d(
        [
            (x_face, dt_z_mid - 16.0),
            (x_face + 14.0, dt_z_mid - 16.0),
            (px + 20.0, pz - 20.0),
            (px + 20.0, pz + 20.0),
            (px - 18.0, pz + 20.0),
            (x_face, dt_z_mid + 16.0),
        ],
        radius=12.0,
        segs_per_corner=6,
    )
    draw_poly_3d(sk_arm, [(xx, py - 12.0, zz) for (xx, zz) in arm_xz])
    add_extrude(
        comp, sk_arm, "12.0 mm", (0, 1, 0), adsk.fusion.FeatureOperations.JoinFeatureOperation, "Ext_Join_P5D_Deck", arm_body
    )

    # Vertical root gusset against X=459 collar face
    p_gus = make_offset_plane(comp, comp.yZConstructionPlane, f"{x_face} mm", "Plane_P5D_RootGusset")
    sk_gus = comp.sketches.add(p_gus)
    sk_gus.name = "Sk_P5D_RootGusset"
    draw_poly_3d(
        sk_gus,
        [
            (x_face, py, dt_z_mid - 15.0),
            (x_face, 131.0, dt_z_mid - 15.0),
            (x_face, 131.0, dt_z_mid + 15.0),
            (x_face, py, dt_z_mid + 15.0),
        ],
    )
    add_extrude(
        comp, sk_gus, "8.0 mm", (1, 0, 0), adsk.fusion.FeatureOperations.JoinFeatureOperation, "Ext_Join_P5D_Gusset", arm_body
    )

    # 608 Bearing Bore in top of P5D Swivel Hub
    p_brg = make_offset_plane(comp, comp.xZConstructionPlane, f"{py} mm", "Plane_P5D_608Bore")
    sk_brg = comp.sketches.add(p_brg)
    sk_brg.name = "Sk_P5D_608Bore"
    sk_brg.sketchCurves.sketchCircles.addByCenterRadius(
        pt_sk(sk_brg, px, py, pz), mm(0.5 * (v["bearing_od"] + v["bearing_bore_clear"]))
    )
    add_extrude(
        comp, sk_brg, "bearing_w + 0.3 mm", (0, -1, 0), adsk.fusion.FeatureOperations.CutFeatureOperation, "Ext_Cut_P5D_608", arm_body
    )

    return occ


def _build_holo_head_and_walnut_cheeks(assy_comp: adsk.fusion.Component, v: dict) -> tuple:
    """Build P5B Base + P5A Squircle Optical Core + W5A Left/Right Walnut Cheeks + P5C Visor + G5 Cube."""
    px = v["holo_piv_x"]                                       # 504.0 mm
    py = v["holo_piv_y"]                                       # 92.0 mm
    pz = v["holo_piv_z"]                                       # 86.0 mm
    y_base0 = py + 1.0                                         # 93.0 mm
    base_h = 22.0                                              # Y = 93..115 mm
    core_w = 38.0                                              # Matte-black optical core width (X = 485..523 mm)
    core_d = 42.0                                              # Z = 65..107 mm
    core_h = 40.0                                              # Y = 115..155 mm
    ps = v["prism_size"] + v["prism_clear"]                    # 25.8 mm prism pocket

    # 1. P5B: Sculpted Squircle Electronics Base (ESP32-C3 + INMP441 + 608 Axle Pin)
    occ_base = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp_base = occ_base.component
    comp_base.name = "P5B_Sculpted_Electronics_Base"
    p_b0 = make_offset_plane(comp_base, comp_base.xZConstructionPlane, f"{y_base0} mm", "Plane_P5B_Bot")
    sk_b0 = comp_base.sketches.add(p_b0)
    sk_b0.name = "Sk_P5B_Squircle"
    base_xz = sample_rounded_poly_2d(
        [
            (px - 22.0, pz - 0.5 * core_d),
            (px + 22.0, pz - 0.5 * core_d),
            (px + 22.0, pz + 0.5 * core_d),
            (px - 22.0, pz + 0.5 * core_d),
        ],
        radius=9.0,
        segs_per_corner=5,
    )
    draw_poly_3d(sk_b0, [(xx, y_base0, zz) for (xx, zz) in base_xz])
    ext_b = add_extrude(
        comp_base, sk_b0, f"{base_h} mm", (0, 1, 0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation, "Ext_P5B_Base"
    )
    b_body = ext_b.bodies.item(0)
    b_body.name = "Body_P5B_Electronics_Base"

    # Bottom Ø7.88 mm 608 Swivel Pin
    sk_pin = comp_base.sketches.add(p_b0)
    sk_pin.name = "Sk_P5B_608Pin"
    sk_pin.sketchCurves.sketchCircles.addByCenterRadius(
        pt_sk(sk_pin, px, y_base0, pz), mm(0.5 * (v["bearing_id"] - 0.12))
    )
    add_extrude(
        comp_base, sk_pin, "bearing_w + 1.0 mm", (0, -1, 0), adsk.fusion.FeatureOperations.JoinFeatureOperation, "Ext_Join_P5B_Pin", b_body
    )

    # Internal MCU Cavity + Rear USB-C Pill Cut + Front INMP441 Acoustic Port
    y_btop = y_base0 + base_h
    p_btop = make_offset_plane(comp_base, comp_base.xZConstructionPlane, f"{y_btop} mm", "Plane_P5B_Top")
    sk_bcav = comp_base.sketches.add(p_btop)
    sk_bcav.name = "Sk_P5B_MCU_Bay"
    draw_poly_3d(
        sk_bcav,
        [(px - 15.0, y_btop, pz - 16.0), (px + 15.0, y_btop, pz - 16.0), (px + 15.0, y_btop, pz + 16.0), (px - 15.0, y_btop, pz + 16.0)],
    )
    add_extrude(
        comp_base, sk_bcav, "17.5 mm", (0, -1, 0), adsk.fusion.FeatureOperations.CutFeatureOperation, "Ext_Cut_P5B_MCU", b_body
    )

    p_bf = make_offset_plane(comp_base, comp_base.xYConstructionPlane, f"{pz + 0.5 * core_d} mm", "Plane_P5B_Front")
    sk_mic = comp_base.sketches.add(p_bf)
    sk_mic.name = "Sk_P5B_MicHole"
    sk_mic.sketchCurves.sketchCircles.addByCenterRadius(pt_sk(sk_mic, px, y_base0 + 11.0, pz + 0.5 * core_d), mm(2.0))
    add_extrude(
        comp_base, sk_mic, "6.0 mm", (0, 0, -1), adsk.fusion.FeatureOperations.CutFeatureOperation, "Ext_Cut_P5B_Mic", b_body
    )

    # 2. P5A: Squircle Stealth Matte-Black Optical Core (Y = 115..155 mm)
    occ_core = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp_core = occ_core.component
    comp_core.name = "P5A_Squircle_Optical_Core"
    y_c0 = y_btop
    p_c0 = make_offset_plane(comp_core, comp_core.xZConstructionPlane, f"{y_c0} mm", "Plane_P5A_Bot")
    sk_c0 = comp_core.sketches.add(p_c0)
    sk_c0.name = "Sk_P5A_Squircle"
    core_xz = sample_rounded_poly_2d(
        [
            (px - 0.5 * core_w, pz - 0.5 * core_d),
            (px + 0.5 * core_w, pz - 0.5 * core_d),
            (px + 0.5 * core_w, pz + 0.5 * core_d),
            (px - 0.5 * core_w, pz + 0.5 * core_d),
        ],
        radius=7.0,
        segs_per_corner=5,
    )
    draw_poly_3d(sk_c0, [(xx, y_c0, zz) for (xx, zz) in core_xz])
    ext_c = add_extrude(
        comp_core, sk_c0, f"{core_h} mm", (0, 1, 0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation, "Ext_P5A_Core"
    )
    c_body = ext_c.bodies.item(0)
    c_body.name = "Body_P5A_Optical_Core"

    # Front Squircle Optical Window + Prism Chamber
    y_prism_bot = y_c0 + 6.5                                   # 121.5 mm
    z_front = pz + 0.5 * core_d                                # 107.0 mm
    p_cf = make_offset_plane(comp_core, comp_core.xYConstructionPlane, f"{z_front} mm", "Plane_P5A_Front")
    sk_win = comp_core.sketches.add(p_cf)
    sk_win.name = "Sk_P5A_Prism_Bay"
    draw_poly_3d(
        sk_win,
        [
            (px - 0.5 * ps, y_prism_bot, z_front),
            (px + 0.5 * ps, y_prism_bot, z_front),
            (px + 0.5 * ps, y_prism_bot + ps, z_front),
            (px - 0.5 * ps, y_prism_bot + ps, z_front),
        ],
    )
    add_extrude(
        comp_core, sk_win, f"{ps + 3.0} mm", (0, 0, -1), adsk.fusion.FeatureOperations.CutFeatureOperation, "Ext_Cut_P5A_Prism", c_body
    )

    # Bottom 0.96" OLED Optical Aperture
    sk_oled = comp_core.sketches.add(p_c0)
    sk_oled.name = "Sk_P5A_OLED_Aperture"
    draw_poly_3d(
        sk_oled,
        [(px - 13.0, y_c0, pz - 6.0), (px + 13.0, y_c0, pz - 6.0), (px + 13.0, y_c0, pz + 10.0), (px - 13.0, y_c0, pz + 10.0)],
    )
    add_extrude(
        comp_core, sk_oled, "8.0 mm", (0, 1, 0), adsk.fusion.FeatureOperations.CutFeatureOperation, "Ext_Cut_P5A_OLED", c_body
    )

    # Top TTP223 Head-Pat Sensor Pocket inside top cap
    p_ctop = make_offset_plane(comp_core, comp_core.xZConstructionPlane, f"{y_c0 + core_h - 1.5} mm", "Plane_P5A_Touch")
    sk_tch = comp_core.sketches.add(p_ctop)
    sk_tch.name = "Sk_P5A_TTP223"
    draw_poly_3d(
        sk_tch,
        [
            (px - 8.0, y_c0 + core_h - 1.5, pz - 6.0),
            (px + 8.0, y_c0 + core_h - 1.5, pz - 6.0),
            (px + 8.0, y_c0 + core_h - 1.5, pz + 6.0),
            (px - 8.0, y_c0 + core_h - 1.5, pz + 6.0),
        ],
    )
    add_extrude(
        comp_core, sk_tch, "3.2 mm", (0, -1, 0), adsk.fusion.FeatureOperations.CutFeatureOperation, "Ext_Cut_P5A_Touch", c_body
    )

    # 3. W5A_Left & W5A_Right: 6 mm Warm Walnut Rounded Side Cheek Panels!
    cheeks = []
    cheek_yz = sample_rounded_poly_2d(
        [(y_c0 + 3.0, pz - 15.0), (y_c0 + 3.0, pz + 15.0), (y_c0 + core_h - 3.0, pz + 15.0), (y_c0 + core_h - 3.0, pz - 15.0)],
        radius=6.0,
        segs_per_corner=5,
    )
    for cname, bname, x_pl, dir_x in [
        ("W5A_Left_Walnut_Cheek_Panel", "Body_W5A_Left_Walnut_Cheek", px - 0.5 * core_w - 6.0, 1),
        ("W5A_Right_Walnut_Cheek_Panel", "Body_W5A_Right_Walnut_Cheek", px + 0.5 * core_w, 1),
    ]:
        occ_ck = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        comp_ck = occ_ck.component
        comp_ck.name = cname
        pl_ck = make_offset_plane(comp_ck, comp_ck.yZConstructionPlane, f"{x_pl} mm", f"Plane_{cname}")
        sk_ck = comp_ck.sketches.add(pl_ck)
        sk_ck.name = f"Sk_{cname}"
        draw_poly_3d(sk_ck, [(x_pl, yy, zz) for (yy, zz) in cheek_yz])
        ext_ck = add_extrude(
            comp_ck, sk_ck, "wood_thick_panel", (dir_x, 0, 0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation, f"Ext_{cname}"
        )
        ext_ck.bodies.item(0).name = bname
        cheeks.append(occ_ck)

    # 4. P5C: Floating Sculpted Cyber-Red Magnetic Brow Visor
    occ_vis = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp_vis = occ_vis.component
    comp_vis.name = "P5C_Floating_Magnetic_Visor"
    p_vis = make_offset_plane(comp_vis, comp_vis.yZConstructionPlane, f"{px - 0.5 * core_w} mm", "Plane_P5C_Visor")
    sk_vis = comp_vis.sketches.add(p_vis)
    sk_vis.name = "Sk_P5C_BrowVisor"
    vis_yz = sample_rounded_poly_2d(
        [
            (y_c0 + core_h - 6.0, z_front),
            (y_c0 + core_h + 1.0, z_front),
            (y_c0 + core_h + 1.0, z_front + 13.0),
            (y_c0 + core_h - 9.0, z_front + 15.0),
            (y_c0 + core_h - 9.0, z_front + 11.0),
            (y_c0 + core_h - 2.5, z_front + 9.5),
            (y_c0 + core_h - 2.5, z_front),
        ],
        radius=2.0,
        segs_per_corner=4,
    )
    draw_poly_3d(sk_vis, [(px - 0.5 * core_w, yy, zz) for (yy, zz) in vis_yz])
    ext_vis = add_extrude(
        comp_vis, sk_vis, f"{core_w} mm", (1, 0, 0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation, "Ext_P5C_Visor"
    )
    ext_vis.bodies.item(0).name = "Body_P5C_Magnetic_Visor"

    # 5. G5: 25.4 mm 50:50 K9 Optical Beam-Splitter Cube Reference
    occ_cube = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp_cube = occ_cube.component
    comp_cube.name = "G5_K9_BeamSplitter_Cube"
    cube_s = v["prism_size"]
    z_cube_f = z_front - 1.5
    p_cb = make_offset_plane(comp_cube, comp_cube.xYConstructionPlane, f"{z_cube_f} mm", "Plane_G5_Cube")
    sk_cb = comp_cube.sketches.add(p_cb)
    sk_cb.name = "Sk_G5_Cube"
    draw_poly_3d(
        sk_cb,
        [
            (px - 0.5 * cube_s, y_prism_bot + 0.2, z_cube_f),
            (px + 0.5 * cube_s, y_prism_bot + 0.2, z_cube_f),
            (px + 0.5 * cube_s, y_prism_bot + 0.2 + cube_s, z_cube_f),
            (px - 0.5 * cube_s, y_prism_bot + 0.2 + cube_s, z_cube_f),
        ],
    )
    ext_cb = add_extrude(
        comp_cube, sk_cb, "prism_size", (0, 0, -1), adsk.fusion.FeatureOperations.NewBodyFeatureOperation, "Ext_G5_Cube"
    )
    ext_cb.bodies.item(0).name = "Body_G5_K9_Glass_Cube"

    return occ_base, occ_core, cheeks[0], cheeks[1], occ_vis, occ_cube


def _build_walnut_coaster_dock(assy_comp: adsk.fusion.Component, v: dict) -> tuple:
    """Build W5B 6 mm Warm Walnut Coaster + P5E 608 Hub.

    The pedestal is a *freestanding* option, so it must physically rest on the desk mat.
    It parks in the rear-right docking bay beside the AeroBridge W1B arch:
    the Ø70 mm coaster spans X 436..506 / Z 18..88 - behind the mouse sweep (Z >= 90),
    right of the AULA F75 (X >= 429.5) and clear of every clamp that touches the desk.
    """
    cx = 471.0
    cz = 53.0
    y0 = 3.0

    # W5B: Ø70 x 6 mm Warm Walnut Coaster Disc
    occ_wc = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp_wc = occ_wc.component
    comp_wc.name = "W5B_Walnut_Pedestal_Coaster"
    p_wc = make_offset_plane(comp_wc, comp_wc.xZConstructionPlane, f"{y0} mm", "Plane_W5B_Coaster")
    sk_wc = comp_wc.sketches.add(p_wc)
    sk_wc.name = "Sk_W5B_CoasterDisc"
    sk_wc.sketchCurves.sketchCircles.addByCenterRadius(pt_sk(sk_wc, cx, y0, cz), mm(35.0))
    ext_wc = add_extrude(
        comp_wc, sk_wc, "wood_thick_panel", (0, 1, 0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation, "Ext_W5B_Coaster"
    )
    ext_wc.bodies.item(0).name = "Body_W5B_Walnut_Coaster"

    # P5E: Matte-Black 608 Swivel Hub Insert centered on W5B
    occ_hb = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp_hb = occ_hb.component
    comp_hb.name = "P5E_Pedestal_608_Hub"
    y_hb = y0 + v["wood_thick_panel"]
    p_hb = make_offset_plane(comp_hb, comp_hb.xZConstructionPlane, f"{y_hb} mm", "Plane_P5E_Hub")
    sk_hb = comp_hb.sketches.add(p_hb)
    sk_hb.name = "Sk_P5E_HubRing"
    sk_hb.sketchCurves.sketchCircles.addByCenterRadius(pt_sk(sk_hb, cx, y_hb, cz), mm(18.0))
    ext_hb = add_extrude(
        comp_hb, sk_hb, "9.0 mm", (0, 1, 0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation, "Ext_P5E_Hub"
    )
    hb_body = ext_hb.bodies.item(0)
    hb_body.name = "Body_P5E_Pedestal_Hub"

    p_hbrg = make_offset_plane(comp_hb, comp_hb.xZConstructionPlane, f"{y_hb + 9.0} mm", "Plane_P5E_608")
    sk_hbrg = comp_hb.sketches.add(p_hbrg)
    sk_hbrg.name = "Sk_P5E_608Bore"
    sk_hbrg.sketchCurves.sketchCircles.addByCenterRadius(
        pt_sk(sk_hbrg, cx, y_hb + 9.0, cz), mm(0.5 * (v["bearing_od"] + v["bearing_bore_clear"]))
    )
    add_extrude(
        comp_hb, sk_hbrg, "bearing_w + 0.3 mm", (0, -1, 0), adsk.fusion.FeatureOperations.CutFeatureOperation, "Ext_Cut_P5E_608", hb_body
    )

    return occ_wc, occ_hb


def build_product(design: adsk.fusion.Design, parent_comp: adsk.fusion.Component = None) -> adsk.fusion.Occurrence:
    if parent_comp is None:
        parent_comp = design.rootComponent

    v = register_parameters(design)

    assy_occ = parent_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    assy_comp = assy_occ.component
    assy_comp.name = "Product5_HoloBuddy"

    occ_wing = _build_wing_arm(assy_comp, v)
    occ_base, occ_core, occ_ck_l, occ_ck_r, occ_vis, occ_cube = _build_holo_head_and_walnut_cheeks(assy_comp, v)
    occ_wc, occ_hb = _build_walnut_coaster_dock(assy_comp, v)

    ab = assy_comp.asBuiltJoints
    for c_occ, p_occ, jn in [
        (occ_core, occ_base, "Joint_Rigid_OpticalCore_to_Base"),
        (occ_ck_l, occ_core, "Joint_Rigid_LeftWalnutCheek_to_Core"),
        (occ_ck_r, occ_core, "Joint_Rigid_RightWalnutCheek_to_Core"),
        (occ_vis, occ_core, "Joint_Rigid_MagneticVisor_to_Core"),
        (occ_cube, occ_core, "Joint_Rigid_K9Prism_in_Core"),
        (occ_hb, occ_wc, "Joint_Rigid_608Hub_on_WalnutCoaster"),
        (occ_wc, occ_wing, "Joint_Rigid_CoasterDock_Reference"),
    ]:
        ji = ab.createInput(c_occ, p_occ, None)
        ji.setAsRigidJointMotion()
        j = ab.add(ji)
        j.name = jn

    px, py, pz = v["holo_piv_x"], v["holo_piv_y"], v["holo_piv_z"]
    sk_rev = occ_wing.component.sketches.add(occ_wing.component.xYConstructionPlane)
    sk_rev.name = "Sk_HoloBuddy_Swivel_Axis"
    rev_line = sk_rev.sketchCurves.sketchLines.addByTwoPoints(pt_sk(sk_rev, px, py, pz), pt_sk(sk_rev, px, py + 12.0, pz))
    rev_proxy = rev_line.createForAssemblyContext(occ_wing)
    rev_geom = adsk.fusion.JointGeometry.createByCurve(rev_proxy, adsk.fusion.JointKeyPointTypes.StartKeyPoint)
    rev_in = ab.createInput(occ_base, occ_wing, rev_geom)
    rev_in.setAsRevoluteJointMotion(adsk.fusion.JointDirections.CustomJointDirection, rev_proxy)
    rev_j = ab.add(rev_in)
    rev_j.name = "Joint_Revolute_HoloBuddy_Swivel"

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
        app.executeTextCommand('PTransaction.Start "Build Product 5 HoloBuddy Hybrid"')
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
            ui.messageBox(f"Product5_HoloBuddy failed:\n{err}")
