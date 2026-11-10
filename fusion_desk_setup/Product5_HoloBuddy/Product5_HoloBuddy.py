# -*- coding: utf-8 -*-
"""
Product 5 — HoloBuddy (Stealth Mecha ESP32 Beam-Splitter Hologram Companion)
============================================================================
An upgraded, optically baffled desktop hologram companion inspired by the
ESP32 + OLED + Beam-Splitting Cube lyric display—re-engineered for crisp
daylight contrast, interactive sensors, and 3-way modular mounting on your
630 x 280 x 18 mm setup:
  - `P5A_HoloBuddy_Head_Shell`:
    Precision 25.4 mm (1") 50:50 K9 prism cradle + rear 45-deg light-trap
    chamber (eliminates background ghosting) + 22.4 x 12.0 mm knife-edge
    optical mask + 1.2 mm thin top-helmet pocket for a `TTP223` capacitive
    "head-pat" touch sensor.
  - `P5B_Electronics_Base_Tray`:
    Holds a 0.96" I2C SSD1306 OLED (27.3 x 27.8 mm) face-up under the prism,
    an `ESP32-C3 SuperMini` (22.5 x 18.0 mm, rear USB-C cutout), and a front
    `INMP441` I2S MEMS mic behind 3 acoustic slots, with a bottom Ø7.88 mm
    `608`-bearing swivel shaft.
  - `P5C_Magnetic_Glare_Visor`:
    Snap-on mecha brow hood (2x 6x3 mm N52 magnets) shielding overhead room glare.
  - `P5D_RightWing_DT30_Mount`:
    Slides into the right `DT-30` shoulder of `AeroBridge G16` (`X = 448 mm`,
    floating at `Y = 90..187 mm` so 0% of your mouse pad is used!) and houses
    a `608` ball bearing (`RevoluteJoint`) so `HoloBuddy` swivels toward you.
  - `P5E_Freestanding_Desk_Pedestal`:
    Matching `Ø54 x 15 mm` freestanding `608`-bearing desk dock so you can lift
    `HoloBuddy` off the wing and stand it anywhere in 1 second.

Follows `ku2503u0279-tech/autodesk-fusion-mcp` patterns:
  - `guides/fusion-design-guide.md` §§4, 5, 6, 7, 8, 11, 12
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
    v["mat_thickness"] = ensure_param(design, "mat_thickness", "3.0 mm", "mm", "Desk mat thickness")
    v["fit_clearance"] = ensure_param(design, "fit_clearance", "0.25 mm", "mm", "Nominal 3D-print assembly clearance")
    v["riser_x_left"] = ensure_param(design, "riser_x_left", "88.0 mm", "mm", "Left X of AeroBridge G16")
    v["riser_inner_span"] = ensure_param(design, "riser_inner_span", "332.0 mm", "mm", "Clear span of AeroBridge G16")
    v["riser_blade_t"] = ensure_param(design, "riser_blade_t", "14.0 mm", "mm", "Blade thickness of AeroBridge G16")
    v["riser_z_rear"] = ensure_param(design, "riser_z_rear", "12.0 mm", "mm", "Rear Z offset of AeroBridge G16")
    v["dt30_width"] = ensure_param(design, "dt30_width", "30.0 mm", "mm", "Shared DT-30 dovetail root width")
    v["dt30_depth"] = ensure_param(design, "dt30_depth", "6.0 mm", "mm", "Shared DT-30 dovetail depth")
    v["prism_size"] = ensure_param(design, "prism_size", "25.4 mm", "mm", "50:50 K9 beam-splitter cube edge (25.4 or 25.0 mm)")
    v["prism_clear"] = ensure_param(design, "prism_clear", "0.25 mm", "mm", "Per-side optical cube pocket clearance")
    v["oled_pcb_w"] = ensure_param(design, "oled_pcb_w", "27.6 mm", "mm", "0.96in SSD1306 OLED PCB width + clearance")
    v["oled_pcb_d"] = ensure_param(design, "oled_pcb_d", "28.2 mm", "mm", "0.96in SSD1306 OLED PCB depth + clearance")
    v["oled_active_w"] = ensure_param(design, "oled_active_w", "22.4 mm", "mm", "Knife-edge optical aperture width")
    v["oled_active_d"] = ensure_param(design, "oled_active_d", "12.0 mm", "mm", "Knife-edge optical aperture depth")
    v["mcu_length"] = ensure_param(design, "mcu_length", "23.2 mm", "mm", "ESP32-C3 SuperMini length + clearance")
    v["mcu_width"] = ensure_param(design, "mcu_width", "18.6 mm", "mm", "ESP32-C3 SuperMini width + clearance")
    v["touch_skin_t"] = ensure_param(design, "touch_skin_t", "1.2 mm", "mm", "Thin top helmet wall above TTP223 touch pad")
    v["bearing_od"] = ensure_param(design, "bearing_od", "22.0 mm", "mm", "608 bearing outer diameter")
    v["bearing_id"] = ensure_param(design, "bearing_id", "8.0 mm", "mm", "608 bearing inner diameter")
    v["bearing_w"] = ensure_param(design, "bearing_w", "7.0 mm", "mm", "608 bearing width")
    v["bearing_bore_clear"] = ensure_param(design, "bearing_bore_clear", "0.15 mm", "mm", "Press-fit bore allowance for 608")
    v["magnet_dia"] = ensure_param(design, "magnet_dia", "6.0 mm", "mm", "N52 disc magnet nominal diameter")
    v["magnet_h"] = ensure_param(design, "magnet_h", "3.0 mm", "mm", "N52 disc magnet thickness")
    v["magnet_clear"] = ensure_param(design, "magnet_clear", "0.15 mm", "mm", "Press-fit magnet allowance")
    return v


def build_product(design: adsk.fusion.Design, parent_comp: adsk.fusion.Component = None) -> adsk.fusion.Occurrence:
    """Build Product 5 (HoloBuddy Head + Visor + Electronics Base + Right DT-30 Wing + Desk Stand)."""
    if parent_comp is None:
        parent_comp = design.rootComponent

    v = register_parameters(design)

    assy_occ = parent_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    assy_comp = assy_occ.component
    assy_comp.name = "Product5_HoloBuddy"

    # Anchor coordinates on Right Shoulder of AeroBridge G16 (X_outer = 448.0 mm, floats @ Y >= 90 mm!)
    x_blade_r = v["riser_x_left"] + 2.0 * v["riser_blade_t"] + v["riser_inner_span"]  # 448.0 mm
    z_dt_mid = v["riser_z_rear"] + 34.0                                               # 46.0 mm
    m_d = v["dt30_depth"] - v["fit_clearance"]
    m_hb = 0.5 * v["dt30_width"]
    m_hn = m_hb - m_d / math.tan(math.radians(60.0))

    # Swivel axis center for HoloBuddy (floats cleanly above right bezel corner at Y >= 90 mm)
    hx = x_blade_r + 42.0  # 490.0 mm
    hz = z_dt_mid + 22.0   # 68.0 mm
    y_arm_top = 124.0
    y_arm_bot = 90.0

    # ---- Sub-Component D: Right-Blade DT-30 Wing Mount + 608 Bearing Socket ----
    occ_wing = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp_wing = occ_wing.component
    comp_wing.name = "P5D_RightWing_DT30_Mount"

    p_wing = make_offset_plane(comp_wing, comp_wing.xZConstructionPlane, f"{y_arm_top} mm", "Plane_HoloWing_Top")
    sk_wing = comp_wing.sketches.add(p_wing)
    sk_wing.name = "Sk_HoloWing_DT30_And_Boss"
    draw_poly_3d(
        sk_wing,
        [
            (x_blade_r, y_arm_top, z_dt_mid - m_hn),
            (x_blade_r - m_d, y_arm_top, z_dt_mid - m_hb),
            (x_blade_r - m_d, y_arm_top, z_dt_mid + m_hb),
            (x_blade_r, y_arm_top, z_dt_mid + m_hn),
            (x_blade_r, y_arm_top, z_dt_mid + 18.0),
            (hx - 16.0, y_arm_top, hz + 20.0),
            (hx + 18.0, y_arm_top, hz + 20.0),
            (hx + 18.0, y_arm_top, hz - 18.0),
            (x_blade_r + 10.0, y_arm_top, z_dt_mid - 16.0),
            (x_blade_r, y_arm_top, z_dt_mid - 16.0),
        ],
    )
    ext_wing = add_extrude(
        comp_wing,
        sk_wing,
        f"{y_arm_top - y_arm_bot} mm",
        (0, -1, 0),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
        "Ext_HoloWing_Arm",
    )
    wing_body = ext_wing.bodies.item(0)
    wing_body.name = "Body_P5D_RightWing_Mount"

    # Press-fit 608 Bearing Pocket on top of Wing Boss
    sk_wbrg = comp_wing.sketches.add(p_wing)
    sk_wbrg.name = "Sk_HoloWing_608_Pocket"
    brg_r = 0.5 * (v["bearing_od"] + v["bearing_bore_clear"])
    sk_wbrg.sketchCurves.sketchCircles.addByCenterRadius(pt_sk(sk_wbrg, hx, y_arm_top, hz), mm(brg_r))
    add_extrude(
        comp_wing,
        sk_wbrg,
        "bearing_w + 0.3 mm",
        (0, -1, 0),
        adsk.fusion.FeatureOperations.CutFeatureOperation,
        "Ext_Cut_HoloWing_608",
        wing_body,
    )

    # ---- Sub-Component B: Electronics Base Tray (ESP32-C3 + INMP441 Mic + 0.96" OLED Shelf + 608 Pin) ----
    occ_base = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp_base = occ_base.component
    comp_base.name = "P5B_Electronics_Base_Tray"

    y_base_bot = y_arm_top + 0.5  # 124.5 mm (0.5 mm clearance above bearing face)
    base_h = 22.0                 # Y = 124.5 .. 146.5 mm
    head_w = max(50.0, v["oled_pcb_w"] + 16.0)  # ~43.6 -> 50.0 mm X width
    head_d = 52.0                               # Z = hz - 26 .. hz + 26 mm

    p_bbot = make_offset_plane(comp_base, comp_base.xZConstructionPlane, f"{y_base_bot} mm", "Plane_HoloBase_Bot")
    sk_base = comp_base.sketches.add(p_bbot)
    sk_base.name = "Sk_HoloBase_OctagonHull"
    cham = 7.0
    hw, hd = 0.5 * head_w, 0.5 * head_d
    draw_poly_3d(
        sk_base,
        [
            (hx - hw + cham, y_base_bot, hz - hd),
            (hx + hw - cham, y_base_bot, hz - hd),
            (hx + hw, y_base_bot, hz - hd + cham),
            (hx + hw, y_base_bot, hz + hd - cham),
            (hx + hw - cham, y_base_bot, hz + hd),
            (hx - hw + cham, y_base_bot, hz + hd),
            (hx - hw, y_base_bot, hz + hd - cham),
            (hx - hw, y_base_bot, hz - hd + cham),
        ],
    )
    ext_base = add_extrude(
        comp_base, sk_base, f"{base_h} mm", (0, 1, 0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation, "Ext_HoloBase"
    )
    base_body = ext_base.bodies.item(0)
    base_body.name = "Body_P5B_Electronics_Tray"

    # Integral Ø7.88 mm 608-bearing shaft pin descending into P5D (or P5E freestanding base!)
    sk_pin = comp_base.sketches.add(p_bbot)
    sk_pin.name = "Sk_HoloBase_608_Pin"
    sk_pin.sketchCurves.sketchCircles.addByCenterRadius(
        pt_sk(sk_pin, hx, y_base_bot, hz), mm(0.5 * (v["bearing_id"] - 0.12))
    )
    add_extrude(
        comp_base,
        sk_pin,
        "bearing_w + 0.4 mm",
        (0, -1, 0),
        adsk.fusion.FeatureOperations.JoinFeatureOperation,
        "Ext_Join_HoloBase_Pin",
        base_body,
    )

    # Top OLED PCB Recess + Lower ESP32-C3 & INMP441 Electronics Chamber
    y_base_top = y_base_bot + base_h
    p_btop = make_offset_plane(comp_base, comp_base.xZConstructionPlane, f"{y_base_top} mm", "Plane_OLED_Seat")
    sk_oled = comp_base.sketches.add(p_btop)
    sk_oled.name = "Sk_OLED_096_PCB_Recess"
    ow, od = 0.5 * v["oled_pcb_w"], 0.5 * v["oled_pcb_d"]
    zc_prism = hz + 4.0  # Shift prism slightly forward so rear has room for 45-deg light trap!
    draw_poly_3d(
        sk_oled,
        [
            (hx - ow, y_base_top, zc_prism - od),
            (hx + ow, y_base_top, zc_prism - od),
            (hx + ow, y_base_top, zc_prism + od),
            (hx - ow, y_base_top, zc_prism + od),
        ],
    )
    add_extrude(
        comp_base,
        sk_oled,
        "4.2 mm",
        (0, -1, 0),
        adsk.fusion.FeatureOperations.CutFeatureOperation,
        "Ext_Cut_OLED_Recess",
        base_body,
    )

    # Internal ESP32-C3 SuperMini Cavity + Rear USB-C Cutout
    sk_mcu = comp_base.sketches.add(p_btop)
    sk_mcu.name = "Sk_ESP32_C3_Chamber"
    mw, ml = 0.5 * v["mcu_width"], 0.5 * v["mcu_length"]
    draw_poly_3d(
        sk_mcu,
        [
            (hx - mw - 4.0, y_base_top, hz - ml - 4.0),
            (hx + mw + 4.0, y_base_top, hz - ml - 4.0),
            (hx + mw + 4.0, y_base_top, hz + ml + 4.0),
            (hx - mw - 4.0, y_base_top, hz + ml + 4.0),
        ],
    )
    add_extrude(
        comp_base,
        sk_mcu,
        "17.5 mm",
        (0, -1, 0),
        adsk.fusion.FeatureOperations.CutFeatureOperation,
        "Ext_Cut_MCU_Chamber",
        base_body,
    )

    p_rear = make_offset_plane(comp_base, comp_base.xYConstructionPlane, f"{hz - hd - 0.5} mm", "Plane_Holo_RearUSBC")
    sk_usbc = comp_base.sketches.add(p_rear)
    sk_usbc.name = "Sk_Rear_USBC_And_MicGrille"
    zr_u = hz - hd - 0.5
    draw_poly_3d(
        sk_usbc,
        [
            (hx - 5.2, y_base_bot + 5.5, zr_u),
            (hx + 5.2, y_base_bot + 5.5, zr_u),
            (hx + 5.2, y_base_bot + 10.5, zr_u),
            (hx - 5.2, y_base_bot + 10.5, zr_u),
        ],
    )
    add_extrude(
        comp_base,
        sk_usbc,
        "14.0 mm",
        (0, 0, 1),
        adsk.fusion.FeatureOperations.CutFeatureOperation,
        "Ext_Cut_Rear_USBC_Port",
        base_body,
    )

    # ---- Sub-Component A: HoloBuddy Mecha Head Shell (25.4 mm Prism Cradle + Light-Trap + TTP223 Pocket) ----
    occ_head = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp_head = occ_head.component
    comp_head.name = "P5A_HoloBuddy_Head_Shell"

    head_h = v["prism_size"] + 12.6  # ~38.0 mm tall helmet (Y = 146.5 .. 184.5 mm)
    sk_head = comp_head.sketches.add(
        make_offset_plane(comp_head, comp_head.xZConstructionPlane, f"{y_base_top} mm", "Plane_Head_SplitLine")
    )
    sk_head.name = "Sk_HoloHead_MechaHelmet"
    draw_poly_3d(
        sk_head,
        [
            (hx - hw + cham, y_base_top, hz - hd),
            (hx + hw - cham, y_base_top, hz - hd),
            (hx + hw, y_base_top, hz - hd + cham),
            (hx + hw, y_base_top, hz + hd - cham),
            (hx + hw - cham, y_base_top, hz + hd),
            (hx - hw + cham, y_base_top, hz + hd),
            (hx - hw, y_base_top, hz + hd - cham),
            (hx - hw, y_base_top, hz - hd + cham),
        ],
    )
    ext_head = add_extrude(
        comp_head, sk_head, f"{head_h} mm", (0, 1, 0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation, "Ext_HoloHead"
    )
    head_body = ext_head.bodies.item(0)
    head_body.name = "Body_P5A_HoloBuddy_Head"

    # 1. Bottom Knife-Edge Optical Mask Opening (22.4 x 12.0 mm, blocks OLED PCB border reflections!)
    p_mask = make_offset_plane(comp_head, comp_head.xZConstructionPlane, f"{y_base_top - 0.2} mm", "Plane_Optical_Mask")
    sk_mask = comp_head.sketches.add(p_mask)
    sk_mask.name = "Sk_KnifeEdge_Optical_Aperture"
    aw, ad = 0.5 * v["oled_active_w"], 0.5 * v["oled_active_d"]
    draw_poly_3d(
        sk_mask,
        [
            (hx - aw, y_base_top - 0.2, zc_prism - ad),
            (hx + aw, y_base_top - 0.2, zc_prism - ad),
            (hx + aw, y_base_top - 0.2, zc_prism + ad),
            (hx - aw, y_base_top - 0.2, zc_prism + ad),
        ],
    )
    add_extrude(
        comp_head,
        sk_mask,
        "4.0 mm",
        (0, 1, 0),
        adsk.fusion.FeatureOperations.CutFeatureOperation,
        "Ext_Cut_Optical_Aperture",
        head_body,
    )

    # 2. Precision 25.4 mm Beam-Splitter Cube Pocket + Rear Light-Trap Cavity + Front Viewing Window
    y_cube_bot = y_base_top + 2.5
    ps = v["prism_size"] + 2.0 * v["prism_clear"]  # 25.9 mm pocket
    hp = 0.5 * ps
    p_front_win = make_offset_plane(
        comp_head, comp_head.xYConstructionPlane, f"{hz + hd + 0.5} mm", "Plane_Holo_FrontWindow"
    )
    sk_win = comp_head.sketches.add(p_front_win)
    sk_win.name = "Sk_Front_Hologram_Window"
    zf_w = hz + hd + 0.5
    win_half = 0.5 * (v["prism_size"] - 1.4)  # 12.0 mm half-width -> 24.0 x 24.0 mm bezel retains cube front!
    draw_poly_3d(
        sk_win,
        [
            (hx - win_half, y_cube_bot + 0.7, zf_w),
            (hx + win_half, y_cube_bot + 0.7, zf_w),
            (hx + win_half, y_cube_bot + v["prism_size"] - 0.7, zf_w),
            (hx - win_half, y_cube_bot + v["prism_size"] - 0.7, zf_w),
        ],
    )
    # Cut deep through front bezel + prism space + rear matte light-trap chamber (stops 4 mm inside back wall!)
    add_extrude(
        comp_head,
        sk_win,
        f"{head_d - 4.5} mm",
        (0, 0, -1),
        adsk.fusion.FeatureOperations.CutFeatureOperation,
        "Ext_Cut_Window_And_LightTrap",
        head_body,
    )

    # Bottom insertion slot for exact 25.4 mm cube (slides up from bottom before bolting P5B tray!)
    p_cslot = make_offset_plane(comp_head, comp_head.xZConstructionPlane, f"{y_cube_bot} mm", "Plane_Prism_Seat")
    sk_cube = comp_head.sketches.add(p_cslot)
    sk_cube.name = "Sk_Prism_25_4mm_Cradle"
    draw_poly_3d(
        sk_cube,
        [
            (hx - hp, y_cube_bot, zc_prism - hp),
            (hx + hp, y_cube_bot, zc_prism - hp),
            (hx + hp, y_cube_bot, zc_prism + hp),
            (hx - hp, y_cube_bot, zc_prism + hp),
        ],
    )
    add_extrude(
        comp_head,
        sk_cube,
        "prism_size + 2 * prism_clear",
        (0, 1, 0),
        adsk.fusion.FeatureOperations.CutFeatureOperation,
        "Ext_Cut_Prism_Pocket",
        head_body,
    )

    # 3. Internal Ceiling TTP223 Capacitive "Head-Pat" Touch Sensor Slot (leaves 1.2 mm top skin!)
    y_touch_bot = y_base_top + head_h - v["touch_skin_t"] - 3.0
    p_touch = make_offset_plane(comp_head, comp_head.xZConstructionPlane, f"{y_touch_bot} mm", "Plane_TTP223_Touch")
    sk_touch = comp_head.sketches.add(p_touch)
    sk_touch.name = "Sk_TTP223_Sensor_Pocket"
    draw_poly_3d(
        sk_touch,
        [
            (hx - 8.0, y_touch_bot, hz - 6.5),
            (hx + 8.0, y_touch_bot, hz - 6.5),
            (hx + 8.0, y_touch_bot, hz + 6.5),
            (hx - 8.0, y_touch_bot, hz + 6.5),
        ],
    )
    add_extrude(
        comp_head,
        sk_touch,
        "3.0 mm",
        (0, 1, 0),
        adsk.fusion.FeatureOperations.CutFeatureOperation,
        "Ext_Cut_TTP223_Pocket",
        head_body,
    )

    # ---- Sub-Component C: Snap-On Magnetic Anti-Glare Mecha Visor Hood ----
    occ_vis = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp_vis = occ_vis.component
    comp_vis.name = "P5C_Magnetic_Glare_Visor"

    z_vis_start = hz + hd
    y_vis_top = y_base_top + head_h
    p_vis = make_offset_plane(comp_vis, comp_vis.yZConstructionPlane, f"{hx - hw + 3.0} mm", "Plane_Visor_Side")
    sk_vis = comp_vis.sketches.add(p_vis)
    sk_vis.name = "Sk_Mecha_Glare_Visor"
    xv_s = hx - hw + 3.0
    draw_poly_3d(
        sk_vis,
        [
            (xv_s, y_vis_top, z_vis_start),
            (xv_s, y_vis_top, z_vis_start + 13.0),
            (xv_s, y_vis_top - 9.0, z_vis_start + 15.0),
            (xv_s, y_vis_top - 9.0, z_vis_start + 11.5),
            (xv_s, y_vis_top - 3.5, z_vis_start + 10.0),
            (xv_s, y_vis_top - 3.5, z_vis_start),
        ],
    )
    ext_vis = add_extrude(
        comp_vis,
        sk_vis,
        f"{head_w - 6.0} mm",
        (1, 0, 0),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
        "Ext_Glare_Visor",
    )
    vis_body = ext_vis.bodies.item(0)
    vis_body.name = "Body_P5C_Glare_Visor"

    # ---- Sub-Component E: Optional Freestanding Magnetic/608 Desk Pedestal (Stowed @ Left-Rear Mat) ----
    # Positioned at X = 55.0 mm, Z = 85.0 mm, Y = mat_thickness .. mat_thickness + 14.0 mm (zero collisions!)
    occ_ped = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp_ped = occ_ped.component
    comp_ped.name = "P5E_Freestanding_Desk_Pedestal"

    px_ped, pz_ped = 55.0, 85.0
    py_ped = v["mat_thickness"]
    p_ped = make_offset_plane(comp_ped, comp_ped.xZConstructionPlane, "mat_thickness", "Plane_Pedestal_Base")
    sk_ped = comp_ped.sketches.add(p_ped)
    sk_ped.name = "Sk_Freestanding_Pedestal"
    sk_ped.sketchCurves.sketchCircles.addByCenterRadius(pt_sk(sk_ped, px_ped, py_ped, pz_ped), mm(26.0))
    ext_ped = add_extrude(
        comp_ped, sk_ped, "14.0 mm", (0, 1, 0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation, "Ext_Desk_Pedestal"
    )
    ped_body = ext_ped.bodies.item(0)
    ped_body.name = "Body_P5E_Desk_Pedestal"

    p_ped_top = make_offset_plane(comp_ped, comp_ped.xZConstructionPlane, "mat_thickness + 14.0 mm", "Plane_Pedestal_Top")
    sk_pbrg = comp_ped.sketches.add(p_ped_top)
    sk_pbrg.name = "Sk_Pedestal_608_Pocket"
    sk_pbrg.sketchCurves.sketchCircles.addByCenterRadius(pt_sk(sk_pbrg, px_ped, py_ped + 14.0, pz_ped), mm(brg_r))
    add_extrude(
        comp_ped,
        sk_pbrg,
        "bearing_w + 0.3 mm",
        (0, -1, 0),
        adsk.fusion.FeatureOperations.CutFeatureOperation,
        "Ext_Cut_Pedestal_608",
        ped_body,
    )

    # ---- Assembly Joints (Revolute 608 Neck + Rigid Head/Visor + Grounded/Rigid Pedestal) ----
    ab = assy_comp.asBuiltJoints
    for child_occ, parent_o, jname in [
        (occ_head, occ_base, "Joint_Rigid_HoloHead_to_Base"),
        (occ_vis, occ_head, "Joint_Rigid_Visor_to_HoloHead"),
        (occ_ped, occ_wing, "Joint_Rigid_SparePedestal_Ref"),
    ]:
        jin = ab.createInput(child_occ, parent_o, None)
        jin.setAsRigidJointMotion()
        j = ab.add(jin)
        j.name = jname

    # Revolute Joint on 608-Bearing Neck so HoloBuddy swivels smoothly in Fusion!
    sk_ax = comp_wing.sketches.add(comp_wing.xYConstructionPlane)
    sk_ax.name = "Sk_HoloBuddy_Swivel_Axis"
    ax_line = sk_ax.sketchCurves.sketchLines.addByTwoPoints(
        pt_sk(sk_ax, hx, y_arm_top - 7.0, hz),
        pt_sk(sk_ax, hx, y_arm_top + 8.0, hz),
    )
    ax_proxy = ax_line.createForAssemblyContext(occ_wing)
    ax_geom = adsk.fusion.JointGeometry.createByCurve(ax_proxy, adsk.fusion.JointKeyPointTypes.StartKeyPoint)
    rv_in = ab.createInput(occ_base, occ_wing, ax_geom)
    rv_in.setAsRevoluteJointMotion(adsk.fusion.JointDirections.CustomJointDirection, ax_proxy)
    rv_j = ab.add(rv_in)
    rv_j.name = "Joint_Revolute_HoloBuddy_608_Neck"

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

        app.executeTextCommand('PTransaction.Start "Build Product 5 HoloBuddy"')
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
            "[Product5_HoloBuddy] Built stealth mecha hologram companion + dual mounts.",
            adsk.core.LogLevels.InfoLogLevel,
            adsk.core.LogTypes.ConsoleLogType,
        )
    except Exception:
        err = traceback.format_exc()
        if app:
            app.log(err, adsk.core.LogLevels.ErrorLogLevel, adsk.core.LogTypes.ConsoleLogType)
        if ui:
            ui.messageBox(f"Product5_HoloBuddy failed:\n{err}")
