# -*- coding: utf-8 -*-
"""
Product 1 — AeroBridge G16 Cantilevered Riser + MagPivot S24+ Cockpit Wing
===========================================================================
Designed for a compact 630 x 280 x 18 mm desk (+ 3 mm full-surface mat):
  - Elevates the ASUS ROG Strix G16 (354 x 264 x 30.4 mm, 2.5 kg) at a
    pinned ergonomic tilt (`laptop_tilt_deg = 18 deg`, 3-pin adjustable
    16 / 18 / 22 deg) with open bottom intake + full rear exhaust clearance.
  - Provides a `332 mm` wide x `62 mm` high front cantilevered garage so the
    AULA F75 (323 x 143.2 x 43.1 mm) operates cleanly underneath the front
    half of the laptop without overflowing the 280 mm desk depth, while
    preserving a full `175 x 280 mm` right-side mouse pad for the Kreo Chimera V2.
  - Integrates a left `DT-30` dovetail socket carrying the `MagPivot S24+`
    articulated phone wing (M4 Revolute pivot + 90-deg magnet detents + 8x N52
    MagSafe pitch-circle magnet array for Samsung S24+ in MagSafe case).
  - Every printable part fits inside a `200 x 200 x 200 mm` college FDM bed.

Follows `ku2503u0279-tech/autodesk-fusion-mcp` patterns:
  - `guides/fusion-design-guide.md` §§4, 5, 6, 7, 8, 11, 12
  - `AutodeskFusionMCP.manifest` & `lib/fusionAddInUtils/general_utils.py`
"""

import math
import traceback
import adsk.core
import adsk.fusion


# ---------------------------------------------------------------------------
# Coordinate & Parametric Helpers (Fusion internal length unit = cm)
# ---------------------------------------------------------------------------

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
        p1 = pts_3d_mm[i]
        p2 = pts_3d_mm[(i + 1) % n]
        lines.addByTwoPoints(pt_sk(sketch, *p1), pt_sk(sketch, *p2))


def register_parameters(design: adsk.fusion.Design) -> dict:
    v = {}
    v["table_length"] = ensure_param(design, "table_length", "630.0 mm", "mm", "Desk width X (matches 63 cm mat)")
    v["table_depth"] = ensure_param(design, "table_depth", "280.0 mm", "mm", "Desk depth Z (matches 28 cm mat)")
    v["table_thickness"] = ensure_param(design, "table_thickness", "18.0 mm", "mm", "Solid wood tabletop thickness")
    v["mat_thickness"] = ensure_param(design, "mat_thickness", "3.0 mm", "mm", "Desk mat thickness on top of wood")
    v["fit_clearance"] = ensure_param(design, "fit_clearance", "0.25 mm", "mm", "Nominal 3D-print assembly clearance")
    v["laptop_width"] = ensure_param(design, "laptop_width", "354.0 mm", "mm", "ASUS ROG Strix G16 width")
    v["laptop_depth"] = ensure_param(design, "laptop_depth", "264.0 mm", "mm", "ASUS ROG Strix G16 depth")
    v["kb_width"] = ensure_param(design, "kb_width", "323.0 mm", "mm", "AULA F75 width")
    v["kb_height"] = ensure_param(design, "kb_height", "43.1 mm", "mm", "AULA F75 max height with knob")
    v["riser_x_left"] = ensure_param(design, "riser_x_left", "88.0 mm", "mm", "Left X coordinate of AeroBridge G16")
    v["riser_inner_span"] = ensure_param(design, "riser_inner_span", "332.0 mm", "mm", "Clear keyboard garage span (>kb_width)")
    v["riser_blade_t"] = ensure_param(design, "riser_blade_t", "14.0 mm", "mm", "Truss side-blade thickness")
    v["riser_z_rear"] = ensure_param(design, "riser_z_rear", "12.0 mm", "mm", "Rear wall clearance for lid & exhaust")
    v["riser_base_depth"] = ensure_param(design, "riser_base_depth", "184.0 mm", "mm", "Footprint depth on mat (<200 mm bed)")
    v["garage_clear_h"] = ensure_param(design, "garage_clear_h", "62.0 mm", "mm", "Clear height under front bridge (>43.1 mm F75)")
    v["laptop_tilt_deg"] = ensure_param(design, "laptop_tilt_deg", "18.0 deg", "deg", "Ergonomic laptop deck angle (16/18/22 deg)")
    v["front_lip_h"] = ensure_param(design, "front_lip_h", "18.0 mm", "mm", "Padded laptop front-edge retention lip")
    v["dt30_width"] = ensure_param(design, "dt30_width", "30.0 mm", "mm", "Shared DT-30 dovetail root width")
    v["dt30_depth"] = ensure_param(design, "dt30_depth", "6.0 mm", "mm", "Shared DT-30 dovetail depth")
    v["magnet_dia"] = ensure_param(design, "magnet_dia", "6.0 mm", "mm", "N52 disc magnet diameter")
    v["magnet_h"] = ensure_param(design, "magnet_h", "3.0 mm", "mm", "N52 disc magnet thickness")
    v["magnet_clear"] = ensure_param(design, "magnet_clear", "0.15 mm", "mm", "Press-fit magnet diametral allowance")
    v["m3_insert_od"] = ensure_param(design, "m3_insert_od", "4.0 mm", "mm", "M3 brass heat-set pilot bore")
    v["m4_bolt_clear"] = ensure_param(design, "m4_bolt_clear", "4.3 mm", "mm", "M4 pin/axle clearance hole")
    v["magsafe_ring_pcd"] = ensure_param(design, "magsafe_ring_pcd", "54.0 mm", "mm", "MagSafe magnet array pitch circle diameter")
    return v


def _build_truss_blade(
    assy_comp: adsk.fusion.Component,
    comp_name: str,
    body_name: str,
    x_plane_expr: str,
    x_val_mm: float,
    v: dict,
    include_left_features: bool,
) -> adsk.fusion.Occurrence:
    """Create a 14 mm thick cantilevered open-truss side blade (< 190 x 160 mm)."""
    occ = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp = occ.component
    comp.name = comp_name

    y_mat = v["mat_thickness"]                       # 3.0 mm
    z0 = v["riser_z_rear"]                           # 12.0 mm
    z_foot_end = z0 + 152.0                          # 164.0 mm (recessed foot clears wrists)
    z_cantilever = z0 + v["riser_base_depth"]        # 196.0 mm
    y_front_top = y_mat + v["garage_clear_h"] + 12.0 # 77.0 mm deck support nose
    y_front_bot = y_mat + v["garage_clear_h"]        # 65.0 mm clear garage ceiling
    tilt_rad = math.radians(v["laptop_tilt_deg"])
    y_rear_top = y_front_top + (z_cantilever - z0) * math.tan(tilt_rad)  # ~136.8 mm

    blade_plane = make_offset_plane(comp, comp.yZConstructionPlane, x_plane_expr, f"Plane_{comp_name}")

    # 1. Outer cantilevered C-truss silhouette (creates open keyboard garage under front nose!)
    sk_outer = comp.sketches.add(blade_plane)
    sk_outer.name = f"Sk_{comp_name}_Silhouette"
    pts = [
        (x_val_mm, y_mat, z0),
        (x_val_mm, y_mat, z_foot_end),
        (x_val_mm, y_mat + 14.0, z_foot_end),
        (x_val_mm, y_mat + 14.0, z0 + 48.0),
        (x_val_mm, y_front_bot, z0 + 96.0),
        (x_val_mm, y_front_bot, z_cantilever),
        (x_val_mm, y_front_top, z_cantilever),
        (x_val_mm, y_rear_top, z0),
    ]
    draw_poly_3d(sk_outer, pts)
    ext_blade = add_extrude(
        comp,
        sk_outer,
        "riser_blade_t",
        (1, 0, 0),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
        f"Ext_{comp_name}_Body",
    )
    body = ext_blade.bodies.item(0)
    body.name = body_name

    # 2. Triangular truss lightening cutout in rear upright (reduces filament & opens side airflow)
    sk_truss = comp.sketches.add(blade_plane)
    sk_truss.name = f"Sk_{comp_name}_TrussWindow"
    win_pts = [
        (x_val_mm, y_mat + 28.0, z0 + 16.0),
        (x_val_mm, y_mat + 52.0, z0 + 54.0),
        (x_val_mm, y_rear_top - 22.0, z0 + 16.0),
    ]
    draw_poly_3d(sk_truss, win_pts)
    add_extrude(
        comp,
        sk_truss,
        "riser_blade_t + 1 mm",
        (1, 0, 0),
        adsk.fusion.FeatureOperations.CutFeatureOperation,
        f"Ext_Cut_{comp_name}_TrussWindow",
        body,
    )

    # 3. Three-angle M4 detent pin holes (16 / 18 / 22 deg) + front pivot hole
    sk_pins = comp.sketches.add(blade_plane)
    sk_pins.name = f"Sk_{comp_name}_AngleDetentPins"
    pin_r = 0.5 * v["m4_bolt_clear"]
    # Front hinge axis near (z_cantilever - 10, y_front_top - 6)
    hinge_z = z_cantilever - 10.0
    hinge_y = y_front_top - 6.0
    sk_pins.sketchCurves.sketchCircles.addByCenterRadius(pt_sk(sk_pins, x_val_mm, hinge_y, hinge_z), mm(pin_r))
    arc_r = 152.0
    for deg in (16.0, 18.0, 22.0):
        rad = math.radians(deg)
        pz = hinge_z - arc_r * math.cos(rad)
        py = hinge_y + arc_r * math.sin(rad)
        sk_pins.sketchCurves.sketchCircles.addByCenterRadius(pt_sk(sk_pins, x_val_mm, py, pz), mm(pin_r))
    add_extrude(
        comp,
        sk_pins,
        "riser_blade_t + 1 mm",
        (1, 0, 0),
        adsk.fusion.FeatureOperations.CutFeatureOperation,
        f"Ext_Cut_{comp_name}_PinHoles",
        body,
    )

    # 4. Left-blade exclusive features: Vertical DT-30 female socket for MagPivot S24+ + ROG cable clips
    if include_left_features:
        # Vertical DT-30 slot cut into outer face (X = x_val_mm .. x_val_mm + dt30_depth)
        dt_top_plane = make_offset_plane(comp, comp.xZConstructionPlane, "132.0 mm", "Plane_LeftBlade_DT30_Top")
        sk_dt = comp.sketches.add(dt_top_plane)
        sk_dt.name = "Sk_LeftBlade_DT30_Socket"
        dt_d = v["dt30_depth"]
        half_base = 0.5 * (v["dt30_width"] + 2.0 * v["fit_clearance"])
        half_neck = half_base - dt_d / math.tan(math.radians(60.0))
        z_mid = z0 + 34.0
        draw_poly_3d(
            sk_dt,
            [
                (x_val_mm - 0.5, 132.0, z_mid - half_neck),
                (x_val_mm + dt_d, 132.0, z_mid - half_base),
                (x_val_mm + dt_d, 132.0, z_mid + half_base),
                (x_val_mm - 0.5, 132.0, z_mid + half_neck),
            ],
        )
        add_extrude(
            comp,
            sk_dt,
            "46.0 mm",
            (0, -1, 0),
            adsk.fusion.FeatureOperations.CutFeatureOperation,
            "Ext_Cut_LeftBlade_DT30",
            body,
        )

        # Integrated C-clips along rear spine for ROG DC barrel, HDMI & USB-C cords
        clip_plane = make_offset_plane(comp, comp.xZConstructionPlane, "42.0 mm", "Plane_ROG_CableClips")
        sk_clip = comp.sketches.add(clip_plane)
        sk_clip.name = "Sk_LeftBlade_CableClips"
        draw_poly_3d(
            sk_clip,
            [
                (x_val_mm - 9.0, 42.0, z0 + 2.0),
                (x_val_mm, 42.0, z0 + 2.0),
                (x_val_mm, 42.0, z0 + 30.0),
                (x_val_mm - 9.0, 42.0, z0 + 30.0),
                (x_val_mm - 9.0, 42.0, z0 + 24.0),
                (x_val_mm - 4.0, 42.0, z0 + 24.0),
                (x_val_mm - 4.0, 42.0, z0 + 18.0),
                (x_val_mm - 9.0, 42.0, z0 + 18.0),
            ],
        )
        add_extrude(
            comp,
            sk_clip,
            "18.0 mm",
            (0, 1, 0),
            adsk.fusion.FeatureOperations.JoinFeatureOperation,
            "Ext_Join_ROG_CableClip",
            body,
        )
    else:
        # Symmetric Right-Blade vertical DT-30 female socket on outer +X face for Product 5 (HoloBuddy)!
        x_outer_r = x_val_mm + v["riser_blade_t"]  # 448.0 mm
        dt_top_plane = make_offset_plane(comp, comp.xZConstructionPlane, "132.0 mm", "Plane_RightBlade_DT30_Top")
        sk_dt_r = comp.sketches.add(dt_top_plane)
        sk_dt_r.name = "Sk_RightBlade_DT30_Socket"
        dt_d = v["dt30_depth"]
        half_base = 0.5 * (v["dt30_width"] + 2.0 * v["fit_clearance"])
        half_neck = half_base - dt_d / math.tan(math.radians(60.0))
        z_mid = z0 + 34.0
        draw_poly_3d(
            sk_dt_r,
            [
                (x_outer_r + 0.5, 132.0, z_mid - half_neck),
                (x_outer_r - dt_d, 132.0, z_mid - half_base),
                (x_outer_r - dt_d, 132.0, z_mid + half_base),
                (x_outer_r + 0.5, 132.0, z_mid + half_neck),
            ],
        )
        add_extrude(
            comp,
            sk_dt_r,
            "46.0 mm",
            (0, -1, 0),
            adsk.fusion.FeatureOperations.CutFeatureOperation,
            "Ext_Cut_RightBlade_DT30",
            body,
        )

    return occ


def _build_split_spreader(
    assy_comp: adsk.fusion.Component, v: dict
) -> tuple:
    """Build Left & Right Rear Spreader halves (< 178 mm each) with center lap joint."""
    x_inner_l = v["riser_x_left"] + v["riser_blade_t"]        # 102.0 mm
    span = v["riser_inner_span"]                              # 332.0 mm
    x_mid = x_inner_l + 0.5 * span                            # 268.0 mm
    x_inner_r = x_inner_l + span                              # 434.0 mm
    z_rear = v["riser_z_rear"] + 8.0                          # 20.0 mm
    y_bar = v["mat_thickness"] + v["garage_clear_h"] + 14.0   # 79.0 mm

    # Left Spreader Half (includes +12 mm lower lap tongue)
    occ_l = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp_l = occ_l.component
    comp_l.name = "P1E_Rear_Spreader_Left"
    p_l = make_offset_plane(comp_l, comp_l.xYConstructionPlane, f"{z_rear} mm", "Plane_Spreader_L")
    sk_l = comp_l.sketches.add(p_l)
    sk_l.name = "Sk_Spreader_Left_Lap"
    gap = v["fit_clearance"]
    draw_poly_3d(
        sk_l,
        [
            (x_inner_l, y_bar, z_rear),
            (x_mid + 12.0, y_bar, z_rear),
            (x_mid + 12.0, y_bar + 9.0 - gap, z_rear),
            (x_mid - gap, y_bar + 9.0 - gap, z_rear),
            (x_mid - gap, y_bar + 18.0, z_rear),
            (x_inner_l, y_bar + 18.0, z_rear),
        ],
    )
    ext_l = add_extrude(
        comp_l, sk_l, "18.0 mm", (0, 0, 1), adsk.fusion.FeatureOperations.NewBodyFeatureOperation, "Ext_Spreader_Left"
    )
    ext_l.bodies.item(0).name = "Body_P1E_Spreader_Left"

    # Right Spreader Half (includes -12 mm upper lap tongue)
    occ_r = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp_r = occ_r.component
    comp_r.name = "P1F_Rear_Spreader_Right"
    p_r = make_offset_plane(comp_r, comp_r.xYConstructionPlane, f"{z_rear} mm", "Plane_Spreader_R")
    sk_r = comp_r.sketches.add(p_r)
    sk_r.name = "Sk_Spreader_Right_Lap"
    draw_poly_3d(
        sk_r,
        [
            (x_mid + gap, y_bar, z_rear),
            (x_inner_r, y_bar, z_rear),
            (x_inner_r, y_bar + 18.0, z_rear),
            (x_mid - 12.0, y_bar + 18.0, z_rear),
            (x_mid - 12.0, y_bar + 9.0 + gap, z_rear),
            (x_mid + gap, y_bar + 9.0 + gap, z_rear),
        ],
    )
    ext_r = add_extrude(
        comp_r, sk_r, "18.0 mm", (0, 0, 1), adsk.fusion.FeatureOperations.NewBodyFeatureOperation, "Ext_Spreader_Right"
    )
    ext_r.bodies.item(0).name = "Body_P1F_Spreader_Right"
    return occ_l, occ_r


def _build_tilted_deck_halves(assy_comp: adsk.fusion.Component, v: dict) -> tuple:
    """Build Left & Right Open-Airflow Tilted Laptop Cradle Halves (< 186 x 192 mm each)."""
    x_left = v["riser_x_left"]                                # 88.0 mm
    total_w = 2.0 * v["riser_blade_t"] + v["riser_inner_span"]# 360.0 mm
    x_mid = x_left + 0.5 * total_w                            # 268.0 mm
    x_right = x_left + total_w                                # 448.0 mm

    z_front = v["riser_z_rear"] + v["riser_base_depth"] + 6.0 # 202.0 mm front lip plane
    deck_len = 180.0                                          # 192 mm total flat length (< 200 mm printer limit!)
    tilt_rad = math.radians(v["laptop_tilt_deg"])
    y_front = v["mat_thickness"] + v["garage_clear_h"] + 12.0 # 77.0 mm
    t_deck = 8.0
    lip_h = v["front_lip_h"]                                  # 18.0 mm

    def make_half(comp_name: str, body_name: str, x_start: float, x_span_expr: str):
        occ = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        comp = occ.component
        comp.name = comp_name
        p_side = make_offset_plane(comp, comp.yZConstructionPlane, f"{x_start} mm", f"Plane_{comp_name}")
        sk = comp.sketches.add(p_side)
        sk.name = f"Sk_{comp_name}_SideProfile"

        # Tilted deck beam + perpendicular front retention lip along YZ
        uz = -math.cos(tilt_rad)
        uy = math.sin(tilt_rad)
        nz = math.sin(tilt_rad)
        ny = math.cos(tilt_rad)

        p0 = (x_start, y_front, z_front)
        p1 = (x_start, y_front + deck_len * uy, z_front + deck_len * uz)
        p2 = (x_start, p1[1] + t_deck * ny, p1[2] + t_deck * nz)
        p3 = (x_start, y_front + t_deck * ny - 12.0 * uy, z_front + t_deck * nz - 12.0 * uz)
        p4 = (x_start, y_front + (t_deck + lip_h) * ny - 12.0 * uy, z_front + (t_deck + lip_h) * nz - 12.0 * uz)
        p5 = (x_start, y_front + (t_deck + lip_h) * ny, z_front + (t_deck + lip_h) * nz)

        draw_poly_3d(sk, [p0, p1, p2, p3, p4, p5])
        ext = add_extrude(
            comp, sk, x_span_expr, (1, 0, 0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation, f"Ext_{comp_name}"
        )
        body = ext.bodies.item(0)
        body.name = body_name

        # Cut huge central airflow window so ROG Strix G16 intake fans breathe 100% freely!
        vent_x0 = x_start + 22.0
        p_vent = make_offset_plane(comp, comp.xZConstructionPlane, "200.0 mm", f"Plane_{comp_name}_Airflow")
        sk_v = comp.sketches.add(p_vent)
        sk_v.name = f"Sk_{comp_name}_IntakeWindow"
        z_v1 = z_front - 165.0 * math.cos(tilt_rad)
        z_v2 = z_front - 34.0 * math.cos(tilt_rad)
        draw_poly_3d(
            sk_v,
            [
                (vent_x0, 200.0, z_v1),
                (x_start + 0.5 * total_w - 18.0, 200.0, z_v1),
                (x_start + 0.5 * total_w - 18.0, 200.0, z_v2),
                (vent_x0, 200.0, z_v2),
            ],
        )
        add_extrude(
            comp,
            sk_v,
            "160.0 mm",
            (0, -1, 0),
            adsk.fusion.FeatureOperations.CutFeatureOperation,
            f"Ext_Cut_{comp_name}_Airflow",
            body,
        )
        return occ

    occ_dl = make_half("P1C_Tilt_Deck_Left", "Body_P1C_Deck_Left", x_left, "0.5 * (2 * riser_blade_t + riser_inner_span) - fit_clearance")
    occ_dr = make_half("P1D_Tilt_Deck_Right", "Body_P1D_Deck_Right", x_mid + v["fit_clearance"], "0.5 * (2 * riser_blade_t + riser_inner_span) - fit_clearance")
    return occ_dl, occ_dr


def _build_magpivot_wing(assy_comp: adsk.fusion.Component, v: dict) -> tuple:
    """Build P1G MagPivot Arm (DT-30 male slide) + P1H MagSafe Rotor Disc (8x N52 magnets)."""
    x_blade = v["riser_x_left"]                # 88.0 mm
    z_mid = v["riser_z_rear"] + 34.0           # 46.0 mm
    dt_d = v["dt30_depth"] - v["fit_clearance"]
    half_base = 0.5 * v["dt30_width"]
    half_neck = half_base - dt_d / math.tan(math.radians(60.0))

    # P1G: Cantilever Wing Arm extending from X = 88 mm out to X = 8 mm (clears left desk clamp!)
    occ_arm = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp_arm = occ_arm.component
    comp_arm.name = "P1G_MagPivot_Wing_Arm"
    p_top = make_offset_plane(comp_arm, comp_arm.xZConstructionPlane, "130.0 mm", "Plane_MagPivot_Arm")
    sk_arm = comp_arm.sketches.add(p_top)
    sk_arm.name = "Sk_MagPivot_Arm_DT30"
    draw_poly_3d(
        sk_arm,
        [
            (x_blade, 130.0, z_mid - half_neck),
            (x_blade + dt_d, 130.0, z_mid - half_base),
            (x_blade + dt_d, 130.0, z_mid + half_base),
            (x_blade, 130.0, z_mid + half_neck),
            (x_blade, 130.0, z_mid + 18.0),
            (12.0, 130.0, z_mid + 44.0),
            (12.0, 130.0, z_mid + 28.0),
            (x_blade - 12.0, 130.0, z_mid - 16.0),
            (x_blade, 130.0, z_mid - 16.0),
        ],
    )
    ext_arm = add_extrude(
        comp_arm, sk_arm, "40.0 mm", (0, -1, 0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation, "Ext_MagPivot_Arm"
    )
    arm_body = ext_arm.bodies.item(0)
    arm_body.name = "Body_P1G_MagPivot_Arm"

    # P1H: Circular MagSafe Rotor Plate at front face of arm (Z = z_mid + 44..54 mm, centered at X = 38, Y = 148)
    disc_z = z_mid + 44.0
    disc_x = 38.0
    disc_y = 148.0
    occ_disc = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp_disc = occ_disc.component
    comp_disc.name = "P1H_MagSafe_Rotor_Disc"
    p_disc = make_offset_plane(comp_disc, comp_disc.xYConstructionPlane, f"{disc_z} mm", "Plane_MagSafe_Disc")
    sk_disc = comp_disc.sketches.add(p_disc)
    sk_disc.name = "Sk_MagSafe_Disc_Outer"
    sk_disc.sketchCurves.sketchCircles.addByCenterRadius(pt_sk(sk_disc, disc_x, disc_y, disc_z), mm(36.0))
    ext_disc = add_extrude(
        comp_disc, sk_disc, "9.0 mm", (0, 0, 1), adsk.fusion.FeatureOperations.NewBodyFeatureOperation, "Ext_MagSafe_Disc"
    )
    disc_body = ext_disc.bodies.item(0)
    disc_body.name = "Body_P1H_MagSafe_Disc"

    # Cut 8x N52 magnet pockets on MagSafe 54 mm PCD + central M4 pivot bore
    front_disc_p = make_offset_plane(comp_disc, comp_disc.xYConstructionPlane, f"{disc_z + 9.0} mm", "Plane_MagSafe_Front")
    sk_mags = comp_disc.sketches.add(front_disc_p)
    sk_mags.name = "Sk_MagSafe_8x_N52_Array"
    mag_r = 0.5 * (v["magnet_dia"] + v["magnet_clear"])
    pcd_r = 0.5 * v["magsafe_ring_pcd"]
    for k in range(8):
        ang = math.radians(k * 45.0)
        mx = disc_x + pcd_r * math.cos(ang)
        my = disc_y + pcd_r * math.sin(ang)
        sk_mags.sketchCurves.sketchCircles.addByCenterRadius(pt_sk(sk_mags, mx, my, disc_z + 9.0), mm(mag_r))
    add_extrude(
        comp_disc,
        sk_mags,
        "magnet_h + 0.2 mm",
        (0, 0, -1),
        adsk.fusion.FeatureOperations.CutFeatureOperation,
        "Ext_Cut_MagSafe_Array",
        disc_body,
    )

    sk_bore = comp_disc.sketches.add(front_disc_p)
    sk_bore.name = "Sk_MagSafe_Center_M4_Bore"
    sk_bore.sketchCurves.sketchCircles.addByCenterRadius(
        pt_sk(sk_bore, disc_x, disc_y, disc_z + 9.0), mm(0.5 * v["m4_bolt_clear"])
    )
    add_extrude(
        comp_disc,
        sk_bore,
        "10.0 mm",
        (0, 0, -1),
        adsk.fusion.FeatureOperations.CutFeatureOperation,
        "Ext_Cut_MagSafe_PivotBore",
        disc_body,
    )

    return occ_arm, occ_disc, (disc_x, disc_y, disc_z)


def build_product(design: adsk.fusion.Design, parent_comp: adsk.fusion.Component = None) -> adsk.fusion.Occurrence:
    """Build Product 1 assembly with parametric UserParameters, named Components, and Joints."""
    if parent_comp is None:
        parent_comp = design.rootComponent

    v = register_parameters(design)

    assy_occ = parent_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    assy_comp = assy_occ.component
    assy_comp.name = "Product1_AeroBridgeG16"

    occ_bl = _build_truss_blade(
        assy_comp,
        "P1A_Left_Truss_Blade",
        "Body_P1A_Left_Blade",
        "riser_x_left",
        v["riser_x_left"],
        v,
        include_left_features=True,
    )
    x_right_blade = v["riser_x_left"] + v["riser_blade_t"] + v["riser_inner_span"]
    occ_br = _build_truss_blade(
        assy_comp,
        "P1B_Right_Truss_Blade",
        "Body_P1B_Right_Blade",
        "riser_x_left + riser_blade_t + riser_inner_span",
        x_right_blade,
        v,
        include_left_features=False,
    )
    occ_sl, occ_sr = _build_split_spreader(assy_comp, v)
    occ_dl, occ_dr = _build_tilted_deck_halves(assy_comp, v)
    occ_arm, occ_disc, pivot_xyz = _build_magpivot_wing(assy_comp, v)

    # Assemble structural frame with AsBuilt Rigid Joints + Revolute Joint on MagSafe Rotor
    ab_joints = assy_comp.asBuiltJoints
    for child_occ, jname in [
        (occ_sl, "Joint_Rigid_SpreaderL_to_BladeL"),
        (occ_sr, "Joint_Rigid_SpreaderR_to_SpreaderL"),
        (occ_br, "Joint_Rigid_BladeR_to_SpreaderR"),
        (occ_dl, "Joint_Rigid_DeckL_to_BladeL"),
        (occ_dr, "Joint_Rigid_DeckR_to_BladeR"),
        (occ_arm, "Joint_Rigid_MagPivotArm_to_BladeL"),
    ]:
        ji = ab_joints.createInput(child_occ, occ_bl, None)
        ji.setAsRigidJointMotion()
        j = ab_joints.add(ji)
        j.name = jname

    # Revolute Joint (0..90 deg Portrait <-> Landscape) for S24+ MagSafe Rotor Disc
    px, py, pz = pivot_xyz
    sk_piv = occ_arm.component.sketches.add(occ_arm.component.yZConstructionPlane)
    sk_piv.name = "Sk_MagSafe_Revolute_Axis"
    piv_line = sk_piv.sketchCurves.sketchLines.addByTwoPoints(
        pt_sk(sk_piv, px, py, pz), pt_sk(sk_piv, px, py, pz + 9.0)
    )
    piv_proxy = piv_line.createForAssemblyContext(occ_arm)
    piv_geom = adsk.fusion.JointGeometry.createByCurve(piv_proxy, adsk.fusion.JointKeyPointTypes.StartKeyPoint)
    rev_in = ab_joints.createInput(occ_disc, occ_arm, piv_geom)
    rev_in.setAsRevoluteJointMotion(adsk.fusion.JointDirections.CustomJointDirection, piv_proxy)
    rev_j = ab_joints.add(rev_in)
    rev_j.name = "Joint_Revolute_MagSafe_90deg"

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

        app.executeTextCommand('PTransaction.Start "Build Product 1 AeroBridge G16"')
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
            "[Product1_AeroBridgeG16] Built cantilevered riser + MagPivot S24+ wing successfully.",
            adsk.core.LogLevels.InfoLogLevel,
            adsk.core.LogTypes.ConsoleLogType,
        )
    except Exception:
        err = traceback.format_exc()
        if app:
            app.log(err, adsk.core.LogLevels.ErrorLogLevel, adsk.core.LogTypes.ConsoleLogType)
        if ui:
            ui.messageBox(f"Product1_AeroBridgeG16 failed:\n{err}")
