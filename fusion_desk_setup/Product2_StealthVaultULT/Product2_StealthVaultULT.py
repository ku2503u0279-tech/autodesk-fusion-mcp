# -*- coding: utf-8 -*-
"""
Product 2 — StealthVault 280 + SideDock ULT (Left-Edge Zero-Screw Station)
==========================================================================
Clamps to the left edge (`X = 0`) of your 630 x 280 x 18 mm desk (+ 3 mm mat)
using soft 2 mm non-marring pads and M4 thumbscrews (zero screws in desk,
zero rear-wall gap required):
  - Sub-Assembly A (`StealthVault 280`, Z = 14..210 mm, 196 mm < 200 mm bed):
    Fully encloses and hides the 280W ROG Strix G16 power brick (180 x 82 x 26 mm)
    and slack cords behind an angled matte-black sightline shroud with hidden
    bottom/inner convective cooling slots + a snap-on magnetic service door +
    an enclosed vertical rear-left cable raceway up to the G16's left DC port.
  - Sub-Assembly B (`SideDock ULT`, Z = 212..262 mm):
    Houses a press-fit `608` ball bearing (8 x 22 x 7 mm) + N52 magnet detents
    supporting a swing-under boom with a 38 mm wide contoured saddle for the
    Sony ULT WEAR (255 g) headphones + magnetic USB-C cable park.

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
    v["table_thickness"] = ensure_param(design, "table_thickness", "18.0 mm", "mm", "Wood tabletop thickness")
    v["mat_thickness"] = ensure_param(design, "mat_thickness", "3.0 mm", "mm", "Desk mat thickness")
    v["clamp_pad_t"] = ensure_param(design, "clamp_pad_t", "2.0 mm", "mm", "Protective non-marring jaw pad thickness")
    v["clamp_jaw_reach"] = ensure_param(design, "clamp_jaw_reach", "22.0 mm", "mm", "Inward clamp jaw reach on edge")
    v["fit_clearance"] = ensure_param(design, "fit_clearance", "0.25 mm", "mm", "Nominal 3D-print assembly gap")
    v["brick_length"] = ensure_param(design, "brick_length", "180.0 mm", "mm", "ROG 280W power brick length")
    v["brick_width"] = ensure_param(design, "brick_width", "82.0 mm", "mm", "ROG 280W power brick width")
    v["brick_thick"] = ensure_param(design, "brick_thick", "26.0 mm", "mm", "ROG 280W power brick thickness")
    v["vault_z_start"] = ensure_param(design, "vault_z_start", "14.0 mm", "mm", "Distance from back wall to StealthVault")
    v["vault_length"] = ensure_param(design, "vault_length", "196.0 mm", "mm", "Total Z length of StealthVault (<200 mm bed)")
    v["ult_band_w"] = ensure_param(design, "ult_band_w", "38.0 mm", "mm", "Contoured saddle width for Sony ULT WEAR")
    v["bearing_od"] = ensure_param(design, "bearing_od", "22.0 mm", "mm", "608 bearing outer diameter")
    v["bearing_id"] = ensure_param(design, "bearing_id", "8.0 mm", "mm", "608 bearing inner diameter")
    v["bearing_w"] = ensure_param(design, "bearing_w", "7.0 mm", "mm", "608 bearing width")
    v["bearing_bore_clear"] = ensure_param(design, "bearing_bore_clear", "0.15 mm", "mm", "Press-fit bore allowance for 608")
    v["magnet_dia"] = ensure_param(design, "magnet_dia", "6.0 mm", "mm", "N52 magnet nominal diameter")
    v["magnet_h"] = ensure_param(design, "magnet_h", "3.0 mm", "mm", "N52 magnet nominal height")
    v["magnet_clear"] = ensure_param(design, "magnet_clear", "0.15 mm", "mm", "Press-fit allowance for N52 magnets")
    v["m4_insert_od"] = ensure_param(design, "m4_insert_od", "5.6 mm", "mm", "M4 brass heat-set pilot bore")
    return v


def _build_stealth_vault_chassis(assy_comp: adsk.fusion.Component, v: dict) -> tuple:
    """Build P2A StealthVault Clamped Housing + P2B Magnetic Sightline Shroud + P2C Cable Spine."""
    z0 = v["vault_z_start"]                                   # 14.0 mm
    v_len = v["vault_length"]                                 # 196.0 mm (< 200 mm bed!)
    y_top_pad = v["mat_thickness"] + v["clamp_pad_t"]         # +5.0 mm inner top jaw
    y_bot_pad = -v["table_thickness"] - v["clamp_pad_t"] - 4.0# -24.0 mm inner lower jaw (space for swivel shoe)
    jaw_reach = v["clamp_jaw_reach"]                          # 22.0 mm
    spine_t = 9.0

    # Brick cavity (stands vertically: 26 mm thick + 8 mm convective air channel = 34 mm X, 88 mm Y)
    cav_x_min = -18.0
    cav_x_max = 38.0   # 56 mm total internal width (34 mm brick + 22 mm hidden cord-spool channel!)
    cav_y_top = -32.0
    cav_y_bot = -118.0 # 86 mm tall cavity for 82 mm brick + airflow
    wall = 4.2

    # ---- P2A: Main Clamped Stealth Housing ----
    occ_v = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp_v = occ_v.component
    comp_v.name = "P2A_StealthVault_Chassis"
    p_z0 = make_offset_plane(comp_v, comp_v.xYConstructionPlane, "vault_z_start", "Plane_Vault_Rear")

    sk_outer = comp_v.sketches.add(p_z0)
    sk_outer.name = "Sk_Vault_Clamp_And_Box"
    # Outer silhouette combining Left-Edge C-Clamp + Under-Desk Shrouded Vault (open on -X side for door!)
    outer_pts = [
        (-spine_t, y_top_pad + 6.5),
        (jaw_reach, y_top_pad + 6.5),
        (jaw_reach, y_top_pad),
        (0.0, y_top_pad),
        (0.0, y_bot_pad),
        (jaw_reach, y_bot_pad),
        (jaw_reach, cav_y_top),
        (cav_x_max + wall, cav_y_top),
        (cav_x_max + wall, cav_y_bot - wall),
        (cav_x_min, cav_y_bot - wall),
        (cav_x_min, cav_y_bot),
        (cav_x_max, cav_y_bot),
        (cav_x_max, cav_y_top - wall),
        (-spine_t, cav_y_top - wall),
    ]
    draw_poly_3d(sk_outer, [(x, y, z0) for (x, y) in outer_pts])
    ext_v = add_extrude(
        comp_v,
        sk_outer,
        "vault_length",
        (0, 0, 1),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
        "Ext_StealthVault_Chassis",
    )
    v_body = ext_v.bodies.item(0)
    v_body.name = "Body_P2A_Vault_Chassis"

    # End bulkheads (rear Z = z0..z0+4, front sightline armor Z = z0+v_len-4..z0+v_len)
    for b_name, z_expr, z_val in [
        ("RearBulkhead", "vault_z_start", z0),
        ("FrontSightlineBulkhead", "vault_z_start + vault_length - 4.0 mm", z0 + v_len - 4.0),
    ]:
        pb = make_offset_plane(comp_v, comp_v.xYConstructionPlane, z_expr, f"Plane_{b_name}")
        sk_b = comp_v.sketches.add(pb)
        sk_b.name = f"Sk_{b_name}"
        draw_poly_3d(
            sk_b,
            [
                (cav_x_min, cav_y_bot - wall, z_val),
                (cav_x_max + wall, cav_y_bot - wall, z_val),
                (cav_x_max + wall, cav_y_top, z_val),
                (cav_x_min, cav_y_top, z_val),
            ],
        )
        add_extrude(
            comp_v, sk_b, "4.0 mm", (0, 0, 1), adsk.fusion.FeatureOperations.JoinFeatureOperation, f"Ext_{b_name}", v_body
        )

    # Hidden passive convection chimney slots on bottom & inner (+X) wall (zero brick visibility from front/left!)
    p_bot = make_offset_plane(comp_v, comp_v.xZConstructionPlane, f"{cav_y_bot - wall - 0.5} mm", "Plane_Vault_BottomVents")
    sk_vents = comp_v.sketches.add(p_bot)
    sk_vents.name = "Sk_Hidden_Convection_Slots"
    for idx in range(5):
        zs = z0 + 20.0 + idx * 32.0
        draw_poly_3d(
            sk_vents,
            [
                (-8.0, cav_y_bot - wall - 0.5, zs),
                (28.0, cav_y_bot - wall - 0.5, zs),
                (28.0, cav_y_bot - wall - 0.5, zs + 20.0),
                (-8.0, cav_y_bot - wall - 0.5, zs + 20.0),
            ],
        )
    add_extrude(
        comp_v,
        sk_vents,
        "10.0 mm",
        (0, 1, 0),
        adsk.fusion.FeatureOperations.CutFeatureOperation,
        "Ext_Cut_Bottom_Airflow_Slots",
        v_body,
    )

    # Dual M4 Heat-Set Clamp Screw Bores through lower jaw (Z = z0 + 35 and z0 + v_len - 35)
    p_jaw = make_offset_plane(comp_v, comp_v.xZConstructionPlane, f"{y_bot_pad} mm", "Plane_Clamp_M4_Bores")
    sk_m4 = comp_v.sketches.add(p_jaw)
    sk_m4.name = "Sk_Vault_Dual_M4_Insert_Bores"
    r_m4 = 0.5 * v["m4_insert_od"]
    sk_m4.sketchCurves.sketchCircles.addByCenterRadius(pt_sk(sk_m4, 11.0, y_bot_pad, z0 + 35.0), mm(r_m4))
    sk_m4.sketchCurves.sketchCircles.addByCenterRadius(pt_sk(sk_m4, 11.0, y_bot_pad, z0 + v_len - 35.0), mm(r_m4))
    add_extrude(
        comp_v,
        sk_m4,
        "12.0 mm",
        (0, -1, 0),
        adsk.fusion.FeatureOperations.CutFeatureOperation,
        "Ext_Cut_Dual_M4_Bores",
        v_body,
    )

    # ---- P2B: Angled Stealth Outer Sightline Door (completely hides brick from left/chair view) ----
    occ_d = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp_d = occ_d.component
    comp_d.name = "P2B_Stealth_Sightline_Door"
    p_door = make_offset_plane(comp_d, comp_d.xYConstructionPlane, "vault_z_start", "Plane_Stealth_Door")
    sk_d = comp_d.sketches.add(p_door)
    sk_d.name = "Sk_Stealth_Faceted_Door"
    door_pts = [
        (cav_x_min - 4.0, cav_y_bot - wall, z0),
        (cav_x_min, cav_y_bot - wall, z0),
        (cav_x_min, cav_y_top - wall, z0),
        (-spine_t, cav_y_top - wall, z0),
        (-spine_t - 5.0, cav_y_top - 12.0, z0),
        (cav_x_min - 4.0, cav_y_bot + 14.0, z0),
    ]
    draw_poly_3d(sk_d, door_pts)
    ext_d = add_extrude(
        comp_d, sk_d, "vault_length", (0, 0, 1), adsk.fusion.FeatureOperations.NewBodyFeatureOperation, "Ext_Stealth_Door"
    )
    ext_d.bodies.item(0).name = "Body_P2B_Stealth_Door"

    # ---- P2C: Enclosed Rear-Left Vertical Cable Spine (guides ROG DC plug cleanly up to G16!) ----
    occ_sp = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp_sp = occ_sp.component
    comp_sp.name = "P2C_Vertical_Cable_Spine"
    p_sp = make_offset_plane(comp_sp, comp_sp.xZConstructionPlane, f"{y_top_pad + 6.5} mm", "Plane_Cable_Spine_Base")
    sk_sp = comp_sp.sketches.add(p_sp)
    sk_sp.name = "Sk_Cable_Spine_Channel"
    yb = y_top_pad + 6.5
    # Hollow C-duct hugging X = -spine_t .. +10 mm at rear corner Z = z0 .. z0 + 28 mm
    draw_poly_3d(
        sk_sp,
        [
            (-spine_t, yb, z0),
            (10.0, yb, z0),
            (10.0, yb, z0 + 28.0),
            (6.0, yb, z0 + 28.0),
            (6.0, yb, z0 + 4.0),
            (-spine_t + 3.5, yb, z0 + 4.0),
            (-spine_t + 3.5, yb, z0 + 24.0),
            (2.0, yb, z0 + 24.0),
            (2.0, yb, z0 + 28.0),
            (-spine_t, yb, z0 + 28.0),
        ],
    )
    ext_sp = add_extrude(
        comp_sp, sk_sp, "72.0 mm", (0, 1, 0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation, "Ext_Cable_Spine"
    )
    ext_sp.bodies.item(0).name = "Body_P2C_Cable_Spine"

    return occ_v, occ_d, occ_sp


def _build_sidedock_ult(assy_comp: adsk.fusion.Component, v: dict) -> tuple:
    """Build P2D Front-Left Clamp Bearing Hub + P2E 608-Bearing Swing-Under Sony ULT WEAR Arm."""
    z_hub = v["vault_z_start"] + v["vault_length"] + 2.0      # 212.0 mm
    hub_len = 50.0                                            # Z = 212..262 mm (fits 280 mm desk!)
    y_top_pad = v["mat_thickness"] + v["clamp_pad_t"]         # +5.0 mm
    y_bot_pad = -v["table_thickness"] - v["clamp_pad_t"] - 4.0# -24.0 mm
    jaw_reach = v["clamp_jaw_reach"]                          # 22.0 mm
    piv_x = -14.0
    piv_z = z_hub + 0.5 * hub_len                             # 237.0 mm

    # ---- P2D: Front-Left Padded C-Clamp + 608 Bearing Housing ----
    occ_hub = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp_hub = occ_hub.component
    comp_hub.name = "P2D_ULT_Clamp_Bearing_Hub"
    p_hub = make_offset_plane(comp_hub, comp_hub.xYConstructionPlane, f"{z_hub} mm", "Plane_ULT_Hub")
    sk_hub = comp_hub.sketches.add(p_hub)
    sk_hub.name = "Sk_ULT_Clamp_Profile"
    draw_poly_3d(
        sk_hub,
        [
            (-28.0, y_top_pad + 6.5, z_hub),
            (jaw_reach, y_top_pad + 6.5, z_hub),
            (jaw_reach, y_top_pad, z_hub),
            (0.0, y_top_pad, z_hub),
            (0.0, y_bot_pad, z_hub),
            (jaw_reach, y_bot_pad, z_hub),
            (jaw_reach, y_bot_pad - 12.0, z_hub),
            (-28.0, y_bot_pad - 12.0, z_hub),
        ],
    )
    ext_hub = add_extrude(
        comp_hub, sk_hub, f"{hub_len} mm", (0, 0, 1), adsk.fusion.FeatureOperations.NewBodyFeatureOperation, "Ext_ULT_Hub"
    )
    hub_body = ext_hub.bodies.item(0)
    hub_body.name = "Body_P2D_ULT_Bearing_Hub"

    # Press-fit 608 Bearing Bore in bottom face of hub (Y = y_bot_pad - 12.0 = -36.0 mm)
    y_brg_face = y_bot_pad - 12.0
    p_brg = make_offset_plane(comp_hub, comp_hub.xZConstructionPlane, f"{y_brg_face} mm", "Plane_ULT_608_Bore")
    sk_brg = comp_hub.sketches.add(p_brg)
    sk_brg.name = "Sk_ULT_608_Bearing_Pocket"
    brg_r = 0.5 * (v["bearing_od"] + v["bearing_bore_clear"])
    sk_brg.sketchCurves.sketchCircles.addByCenterRadius(pt_sk(sk_brg, piv_x, y_brg_face, piv_z), mm(brg_r))
    add_extrude(
        comp_hub,
        sk_brg,
        "bearing_w + 0.3 mm",
        (0, 1, 0),
        adsk.fusion.FeatureOperations.CutFeatureOperation,
        "Ext_Cut_ULT_608_Pocket",
        hub_body,
    )

    # M4 Heat-Set Clamp Bore on lower jaw
    sk_hm4 = comp_hub.sketches.add(p_brg)
    sk_hm4.name = "Sk_ULT_Clamp_M4_Bore"
    sk_hm4.sketchCurves.sketchCircles.addByCenterRadius(
        pt_sk(sk_hm4, 11.0, y_brg_face, piv_z), mm(0.5 * v["m4_insert_od"])
    )
    add_extrude(
        comp_hub,
        sk_hm4,
        "13.0 mm",
        (0, 1, 0),
        adsk.fusion.FeatureOperations.CutFeatureOperation,
        "Ext_Cut_ULT_Clamp_M4",
        hub_body,
    )

    # ---- P2E: Swing-Under Contoured Sony ULT WEAR Saddle Arm (38 mm wide arch) ----
    occ_arm = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp_arm = occ_arm.component
    comp_arm.name = "P2E_ULT_Swing_Arm_Cradle"
    y_arm_top = y_brg_face - 0.5  # 0.5 mm washer clearance below bearing hub

    # Side profile on XY plane centered around Z = piv_z (extruded symmetrically by ult_band_w = 38 mm)
    p_arm = make_offset_plane(
        comp_arm, comp_arm.xYConstructionPlane, f"{piv_z} - 0.5 * ult_band_w", "Plane_ULT_Saddle_Start"
    )
    sk_arm = comp_arm.sketches.add(p_arm)
    sk_arm.name = "Sk_ULT_Contoured_Saddle"
    z_s = piv_z - 0.5 * v["ult_band_w"]
    # Smooth multi-segment parabolic saddle supporting 35 mm ULT WEAR headband + end retention lip
    arm_pts = [
        (piv_x + 12.0, y_arm_top, z_s),
        (piv_x + 12.0, y_arm_top - 14.0, z_s),
        (piv_x - 24.0, y_arm_top - 22.0, z_s),
        (piv_x - 52.0, y_arm_top - 24.0, z_s),
        (piv_x - 78.0, y_arm_top - 18.0, z_s),
        (piv_x - 88.0, y_arm_top - 6.0, z_s),
        (piv_x - 82.0, y_arm_top - 4.0, z_s),
        (piv_x - 74.0, y_arm_top - 13.0, z_s),
        (piv_x - 52.0, y_arm_top - 16.0, z_s),
        (piv_x - 28.0, y_arm_top - 13.0, z_s),
        (piv_x - 12.0, y_arm_top, z_s),
    ]
    draw_poly_3d(sk_arm, arm_pts)
    ext_arm = add_extrude(
        comp_arm,
        sk_arm,
        "ult_band_w",
        (0, 0, 1),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
        "Ext_ULT_Contoured_Arm",
    )
    arm_body = ext_arm.bodies.item(0)
    arm_body.name = "Body_P2E_ULT_Saddle_Arm"

    # Integral Ø7.88 mm 608-bearing axle boss rising up into the bearing inner race!
    p_axle = make_offset_plane(comp_arm, comp_arm.xZConstructionPlane, f"{y_arm_top} mm", "Plane_ULT_Axle_Base")
    sk_ax = comp_arm.sketches.add(p_axle)
    sk_ax.name = "Sk_ULT_608_Shaft_Boss"
    sk_ax.sketchCurves.sketchCircles.addByCenterRadius(
        pt_sk(sk_ax, piv_x, y_arm_top, piv_z), mm(0.5 * (v["bearing_id"] - 0.12))
    )
    add_extrude(
        comp_arm,
        sk_ax,
        "bearing_w + 0.5 mm",
        (0, 1, 0),
        adsk.fusion.FeatureOperations.JoinFeatureOperation,
        "Ext_Join_ULT_608_Shaft",
        arm_body,
    )

    return occ_hub, occ_arm, (piv_x, y_arm_top, piv_z)


def build_product(design: adsk.fusion.Design, parent_comp: adsk.fusion.Component = None) -> adsk.fusion.Occurrence:
    """Build Product 2 assembly (StealthVault 280 + SideDock ULT) with Joints."""
    if parent_comp is None:
        parent_comp = design.rootComponent

    v = register_parameters(design)

    assy_occ = parent_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    assy_comp = assy_occ.component
    assy_comp.name = "Product2_StealthVaultULT"

    occ_vault, occ_door, occ_spine = _build_stealth_vault_chassis(assy_comp, v)
    occ_hub, occ_arm, piv_xyz = _build_sidedock_ult(assy_comp, v)

    ab_joints = assy_comp.asBuiltJoints
    for child_occ, jname in [
        (occ_door, "Joint_Rigid_StealthDoor_to_Vault"),
        (occ_spine, "Joint_Rigid_CableSpine_to_Vault"),
        (occ_hub, "Joint_Rigid_ULTHub_Aligned_LeftEdge"),
    ]:
        ji = ab_joints.createInput(child_occ, occ_vault, None)
        ji.setAsRigidJointMotion()
        j = ab_joints.add(ji)
        j.name = jname

    # Revolute Joint (0..90 deg swing-under) for the 608-bearing Sony ULT WEAR arm
    px, py, pz = piv_xyz
    sk_rev = occ_hub.component.sketches.add(occ_hub.component.xYConstructionPlane)
    sk_rev.name = "Sk_ULT_608_Revolute_Axis"
    rev_line = sk_rev.sketchCurves.sketchLines.addByTwoPoints(
        pt_sk(sk_rev, px, py, pz), pt_sk(sk_rev, px, py + 8.0, pz)
    )
    rev_proxy = rev_line.createForAssemblyContext(occ_hub)
    rev_geom = adsk.fusion.JointGeometry.createByCurve(rev_proxy, adsk.fusion.JointKeyPointTypes.StartKeyPoint)
    rev_in = ab_joints.createInput(occ_arm, occ_hub, rev_geom)
    rev_in.setAsRevoluteJointMotion(adsk.fusion.JointDirections.CustomJointDirection, rev_proxy)
    rev_j = ab_joints.add(rev_in)
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

        app.executeTextCommand('PTransaction.Start "Build Product 2 StealthVault ULT"')
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
            "[Product2_StealthVaultULT] Built shrouded 280W brick vault + 608-bearing ULT hanger.",
            adsk.core.LogLevels.InfoLogLevel,
            adsk.core.LogTypes.ConsoleLogType,
        )
    except Exception:
        err = traceback.format_exc()
        if app:
            app.log(err, adsk.core.LogLevels.ErrorLogLevel, adsk.core.LogTypes.ConsoleLogType)
        if ui:
            ui.messageBox(f"Product2_StealthVaultULT failed:\n{err}")
