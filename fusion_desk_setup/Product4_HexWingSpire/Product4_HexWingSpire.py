# -*- coding: utf-8 -*-
"""
Product 4 — HexWing Outrigger + Chimera Spire (Rear-Right Zero-Footprint Station)
=================================================================================
Clamps to the rear-right edge (`X = table_length = 630 mm`, `Z = 10..130 mm`)
of your 630 x 280 x 18 mm desk (+ 3 mm mat) with soft 2 mm non-marring pads and
dual M4 thumbscrews—stealing 0% of your mouse pad surface:
  - Sub-Component A (`P4A_RearRight_Clamp_Bracket`):
    Beveled low-profile right-rear C-clamp with an outboard `DT-30` male rail,
    dual M4 heat-set bores, and a top `608` bearing pocket (`22.15 x 7.2 mm`).
  - Sub-Component B (`P4B_HexWing_Caddy_Body`):
    Slides onto the outboard `DT-30` rail (`X = 638..718 mm`) outside the desk:
    6 hexagonal pen/driver silos, 2x USB-A 2.4 GHz dongle slots (for AULA F75 &
    Kreo Chimera V2 receivers), 2x USB-C slots, and a lower drawer bay.
  - Sub-Component C (`P4C_Magnetic_Micro_Drawer`):
    Pull-out micro-parts tray (`SliderJoint` + `6x3 mm` N52 magnetic latch) for
    spare switches, skates, SD cards, and SIM tools.
  - Sub-Component D (`P4D_Chimera_Spire_Boom`):
    Pivots on the `608` ball bearing (`RevoluteJoint`) at the rear-right corner
    to guide a charging cable during wired play and magnetically park your
    USB-C charging tip when gaming wirelessly on the Kreo Chimera V2.

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
    v["hexwing_z_start"] = ensure_param(design, "hexwing_z_start", "10.0 mm", "mm", "Rear-right clamp Z start")
    v["hexwing_len"] = ensure_param(design, "hexwing_len", "120.0 mm", "mm", "Rear-right clamp & caddy Z length")
    v["caddy_outboard_w"] = ensure_param(design, "caddy_outboard_w", "78.0 mm", "mm", "Outboard stationery caddy X width")
    v["dt30_width"] = ensure_param(design, "dt30_width", "30.0 mm", "mm", "Shared DT-30 dovetail root width")
    v["dt30_depth"] = ensure_param(design, "dt30_depth", "6.0 mm", "mm", "Shared DT-30 dovetail depth")
    v["bearing_od"] = ensure_param(design, "bearing_od", "22.0 mm", "mm", "608 bearing outer diameter")
    v["bearing_id"] = ensure_param(design, "bearing_id", "8.0 mm", "mm", "608 bearing inner diameter")
    v["bearing_w"] = ensure_param(design, "bearing_w", "7.0 mm", "mm", "608 bearing width")
    v["bearing_bore_clear"] = ensure_param(design, "bearing_bore_clear", "0.15 mm", "mm", "Press-fit bore allowance for 608")
    v["magnet_dia"] = ensure_param(design, "magnet_dia", "6.0 mm", "mm", "N52 magnet nominal diameter")
    v["magnet_h"] = ensure_param(design, "magnet_h", "3.0 mm", "mm", "N52 magnet nominal height")
    v["magnet_clear"] = ensure_param(design, "magnet_clear", "0.15 mm", "mm", "Press-fit allowance for N52 magnets")
    v["m4_insert_od"] = ensure_param(design, "m4_insert_od", "5.6 mm", "mm", "M4 brass heat-set pilot bore")
    return v


def build_product(design: adsk.fusion.Design, parent_comp: adsk.fusion.Component = None) -> adsk.fusion.Occurrence:
    """Build Product 4 (HexWing Outboard Caddy + Drawer + Chimera Spire Mouse Bungee)."""
    if parent_comp is None:
        parent_comp = design.rootComponent

    v = register_parameters(design)

    assy_occ = parent_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    assy_comp = assy_occ.component
    assy_comp.name = "Product4_HexWingSpire"

    xr = v["table_length"]                                     # 630.0 mm
    z0 = v["hexwing_z_start"]                                  # 10.0 mm
    hlen = v["hexwing_len"]                                    # 120.0 mm (Z = 10..130 mm, clears HydroSling @ 142!)
    y_top_pad = v["mat_thickness"] + v["clamp_pad_t"]          # +5.0 mm
    y_bot_pad = -v["table_thickness"] - v["clamp_pad_t"] - 4.0 # -24.0 mm
    jaw_in = 20.0                                              # X = 610..630 mm

    # ---- Sub-Component A: Rear-Right Beveled C-Clamp + Top 608 Bearing Boss + Outboard DT-30 Male Rail ----
    occ_brkt = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp_brkt = occ_brkt.component
    comp_brkt.name = "P4A_RearRight_Clamp_Bracket"

    p_z0 = make_offset_plane(comp_brkt, comp_brkt.xYConstructionPlane, "hexwing_z_start", "Plane_HexWing_Rear")
    sk_c = comp_brkt.sketches.add(p_z0)
    sk_c.name = "Sk_RearRight_Clamp_Profile"
    y_top_deck = y_top_pad + 10.5  # +15.5 mm thick enough at rear corner for 608 bearing pocket!
    draw_poly_3d(
        sk_c,
        [
            (xr - jaw_in, y_top_pad, z0),
            (xr, y_top_pad, z0),
            (xr, y_bot_pad, z0),
            (xr - jaw_in, y_bot_pad, z0),
            (xr - jaw_in, y_bot_pad - 10.0, z0),
            (xr + 10.0, y_bot_pad - 10.0, z0),
            (xr + 10.0, y_top_deck, z0),
            (xr - jaw_in + 8.0, y_top_deck, z0),
            (xr - jaw_in, y_top_pad + 3.0, z0),
        ],
    )
    ext_c = add_extrude(
        comp_brkt,
        sk_c,
        "hexwing_len",
        (0, 0, 1),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
        "Ext_RearRight_Clamp",
    )
    brkt_body = ext_c.bodies.item(0)
    brkt_body.name = "Body_P4A_Clamp_Bracket"

    # Outboard Vertical DT-30 Male Rail on X = xr + 10.0 mm (Z = z0 + 60 mm centered)
    dt_zc = z0 + 0.5 * hlen  # 70.0 mm
    m_d = v["dt30_depth"] - v["fit_clearance"]
    m_hb = 0.5 * v["dt30_width"]
    m_hn = m_hb - m_d / math.tan(math.radians(60.0))
    p_rail = make_offset_plane(comp_brkt, comp_brkt.xZConstructionPlane, f"{y_bot_pad - 10.0} mm", "Plane_Outboard_DT30")
    sk_rail = comp_brkt.sketches.add(p_rail)
    sk_rail.name = "Sk_Outboard_DT30_Male"
    yb_r = y_bot_pad - 10.0
    draw_poly_3d(
        sk_rail,
        [
            (xr + 10.0, yb_r, dt_zc - m_hn),
            (xr + 10.0 + m_d, yb_r, dt_zc - m_hb),
            (xr + 10.0 + m_d, yb_r, dt_zc + m_hb),
            (xr + 10.0, yb_r, dt_zc + m_hn),
        ],
    )
    add_extrude(
        comp_brkt,
        sk_rail,
        f"{y_top_deck - yb_r} mm",
        (0, 1, 0),
        adsk.fusion.FeatureOperations.JoinFeatureOperation,
        "Ext_Join_Outboard_DT30",
        brkt_body,
    )

    # Top 608 Bearing Bore at rear corner (X = xr - 2.0 = 628.0 mm, Z = z0 + 20.0 = 30.0 mm)
    piv_x = xr - 2.0
    piv_z = z0 + 20.0
    p_top = make_offset_plane(comp_brkt, comp_brkt.xZConstructionPlane, f"{y_top_deck} mm", "Plane_Spire_608_Top")
    sk_brg = comp_brkt.sketches.add(p_top)
    sk_brg.name = "Sk_Spire_608_Pocket"
    sk_brg.sketchCurves.sketchCircles.addByCenterRadius(
        pt_sk(sk_brg, piv_x, y_top_deck, piv_z), mm(0.5 * (v["bearing_od"] + v["bearing_bore_clear"]))
    )
    add_extrude(
        comp_brkt,
        sk_brg,
        "bearing_w + 0.3 mm",
        (0, -1, 0),
        adsk.fusion.FeatureOperations.CutFeatureOperation,
        "Ext_Cut_Spire_608_Pocket",
        brkt_body,
    )

    # Dual M4 Heat-Set Clamp Bores
    sk_m4 = comp_brkt.sketches.add(p_rail)
    sk_m4.name = "Sk_HexWing_Dual_M4_Bores"
    r_m4 = 0.5 * v["m4_insert_od"]
    sk_m4.sketchCurves.sketchCircles.addByCenterRadius(pt_sk(sk_m4, xr - 10.0, yb_r, z0 + 22.0), mm(r_m4))
    sk_m4.sketchCurves.sketchCircles.addByCenterRadius(pt_sk(sk_m4, xr - 10.0, yb_r, z0 + hlen - 22.0), mm(r_m4))
    add_extrude(
        comp_brkt,
        sk_m4,
        "12.0 mm",
        (0, 1, 0),
        adsk.fusion.FeatureOperations.CutFeatureOperation,
        "Ext_Cut_HexWing_M4_Bores",
        brkt_body,
    )

    # ---- Sub-Component B: Outboard HexWing Stationery & 2.4G Dongle Caddy (X = 640..718 mm) ----
    occ_cad = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp_cad = occ_cad.component
    comp_cad.name = "P4B_HexWing_Caddy_Body"

    cx0 = xr + 10.0
    cw = v["caddy_outboard_w"]  # 78.0 mm (X = 640..718 mm — 100% outside mat!)
    cy_bot = -48.0
    cy_top = 42.0               # 90.0 mm total height

    p_cad_bot = make_offset_plane(comp_cad, comp_cad.xZConstructionPlane, f"{cy_bot} mm", "Plane_Caddy_Base")
    sk_cad = comp_cad.sketches.add(p_cad_bot)
    sk_cad.name = "Sk_HexWing_Faceted_Hull"
    draw_poly_3d(
        sk_cad,
        [
            (cx0, cy_bot, z0),
            (cx0 + cw - 12.0, cy_bot, z0),
            (cx0 + cw, cy_bot, z0 + 12.0),
            (cx0 + cw, cy_bot, z0 + hlen - 12.0),
            (cx0 + cw - 12.0, cy_bot, z0 + hlen),
            (cx0, cy_bot, z0 + hlen),
        ],
    )
    ext_cad = add_extrude(
        comp_cad, sk_cad, f"{cy_top - cy_bot} mm", (0, 1, 0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation, "Ext_Caddy_Hull"
    )
    cad_body = ext_cad.bodies.item(0)
    cad_body.name = "Body_P4B_HexWing_Caddy"

    # Cut Female DT-30 slot on inner face (X = cx0)
    dt_d = v["dt30_depth"]
    dt_hb = 0.5 * (v["dt30_width"] + 2.0 * v["fit_clearance"])
    dt_hn = dt_hb - dt_d / math.tan(math.radians(60.0))
    sk_cfem = comp_cad.sketches.add(p_cad_bot)
    sk_cfem.name = "Sk_Caddy_DT30_Female"
    draw_poly_3d(
        sk_cfem,
        [
            (cx0 - 0.5, cy_bot, dt_zc - dt_hn),
            (cx0 + dt_d, cy_bot, dt_zc - dt_hb),
            (cx0 + dt_d, cy_bot, dt_zc + dt_hb),
            (cx0 - 0.5, cy_bot, dt_zc + dt_hn),
        ],
    )
    add_extrude(
        comp_cad,
        sk_cfem,
        "72.0 mm",
        (0, 1, 0),
        adsk.fusion.FeatureOperations.CutFeatureOperation,
        "Ext_Cut_Caddy_DT30_Female",
        cad_body,
    )

    # Cut 6 Hexagonal Pen Silos + 2x USB-A 2.4G Dongle Slots + 2x USB-C Slots from Top Face (Y = cy_top)
    p_cad_top = make_offset_plane(comp_cad, comp_cad.xZConstructionPlane, f"{cy_top} mm", "Plane_Caddy_Top")
    sk_silos = comp_cad.sketches.add(p_cad_top)
    sk_silos.name = "Sk_6x_Hex_Pen_Silos"
    hex_r = 7.5
    pen_centers = [
        (cx0 + 24.0, z0 + 20.0),
        (cx0 + 46.0, z0 + 20.0),
        (cx0 + 64.0, z0 + 32.0),
        (cx0 + 24.0, z0 + 44.0),
        (cx0 + 46.0, z0 + 44.0),
        (cx0 + 64.0, z0 + 56.0),
    ]
    for (px_c, pz_c) in pen_centers:
        hpts = [
            (px_c + hex_r * math.cos(math.radians(60 * k)), cy_top, pz_c + hex_r * math.sin(math.radians(60 * k)))
            for k in range(6)
        ]
        draw_poly_3d(sk_silos, hpts)
    add_extrude(
        comp_cad,
        sk_silos,
        "56.0 mm",
        (0, -1, 0),
        adsk.fusion.FeatureOperations.CutFeatureOperation,
        "Ext_Cut_6x_Hex_Silos",
        cad_body,
    )

    # Dedicated 2x USB-A (AULA F75 + Chimera V2 dongles) & 2x USB-C slots in front zone
    sk_dongles = comp_cad.sketches.add(p_cad_top)
    sk_dongles.name = "Sk_Dongle_Vault_Slots"
    for idx in range(2):
        zu = z0 + 82.0 + idx * 14.0
        # USB-A 12.4 x 4.8 mm
        draw_poly_3d(
            sk_dongles,
            [
                (cx0 + 18.0, cy_top, zu),
                (cx0 + 30.4, cy_top, zu),
                (cx0 + 30.4, cy_top, zu + 4.8),
                (cx0 + 18.0, cy_top, zu + 4.8),
            ],
        )
        # USB-C 8.8 x 3.0 mm
        draw_poly_3d(
            sk_dongles,
            [
                (cx0 + 42.0, cy_top, zu + 0.9),
                (cx0 + 50.8, cy_top, zu + 0.9),
                (cx0 + 50.8, cy_top, zu + 3.9),
                (cx0 + 42.0, cy_top, zu + 3.9),
            ],
        )
    add_extrude(
        comp_cad,
        sk_dongles,
        "13.0 mm",
        (0, -1, 0),
        adsk.fusion.FeatureOperations.CutFeatureOperation,
        "Ext_Cut_Dongle_Slots",
        cad_body,
    )

    # Cut Front Micro-Drawer Cavity into lower front face (Z = z0 + hlen)
    z_front_cad = z0 + hlen
    p_cad_front = make_offset_plane(comp_cad, comp_cad.xYConstructionPlane, f"{z_front_cad} mm", "Plane_Caddy_Front")
    sk_dcav = comp_cad.sketches.add(p_cad_front)
    sk_dcav.name = "Sk_MicroDrawer_Bay"
    drw_x1, drw_x2 = cx0 + 12.0, cx0 + cw - 14.0  # 52.0 mm wide
    drw_y1, drw_y2 = cy_bot + 5.0, cy_bot + 29.0  # 24.0 mm high
    draw_poly_3d(
        sk_dcav,
        [
            (drw_x1, drw_y1, z_front_cad),
            (drw_x2, drw_y1, z_front_cad),
            (drw_x2, drw_y2, z_front_cad),
            (drw_x1, drw_y2, z_front_cad),
        ],
    )
    add_extrude(
        comp_cad,
        sk_dcav,
        "52.0 mm",
        (0, 0, -1),
        adsk.fusion.FeatureOperations.CutFeatureOperation,
        "Ext_Cut_MicroDrawer_Bay",
        cad_body,
    )

    # ---- Sub-Component C: Pull-Out Magnetic Micro-Drawer ----
    occ_drw = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp_drw = occ_drw.component
    comp_drw.name = "P4C_Magnetic_Micro_Drawer"
    gap = v["fit_clearance"]
    p_drw = make_offset_plane(comp_drw, comp_drw.xYConstructionPlane, f"{z_front_cad - 50.0} mm", "Plane_Drawer_Back")
    sk_drw = comp_drw.sketches.add(p_drw)
    sk_drw.name = "Sk_Drawer_OuterBox"
    zb_d = z_front_cad - 50.0
    draw_poly_3d(
        sk_drw,
        [
            (drw_x1 + gap, drw_y1 + gap, zb_d),
            (drw_x2 - gap, drw_y1 + gap, zb_d),
            (drw_x2 - gap, drw_y2 - gap, zb_d),
            (drw_x1 + gap, drw_y2 - gap, zb_d),
        ],
    )
    ext_drw = add_extrude(
        comp_drw, sk_drw, "54.0 mm", (0, 0, 1), adsk.fusion.FeatureOperations.NewBodyFeatureOperation, "Ext_Drawer_Shell"
    )
    drw_body = ext_drw.bodies.item(0)
    drw_body.name = "Body_P4C_Micro_Drawer"

    # Hollow interior of micro-drawer
    p_drw_top = make_offset_plane(comp_drw, comp_drw.xZConstructionPlane, f"{drw_y2 - gap} mm", "Plane_Drawer_Rim")
    sk_din = comp_drw.sketches.add(p_drw_top)
    sk_din.name = "Sk_Drawer_InnerTray"
    yt_d = drw_y2 - gap
    draw_poly_3d(
        sk_din,
        [
            (drw_x1 + 3.0, yt_d, zb_d + 3.0),
            (drw_x2 - 3.0, yt_d, zb_d + 3.0),
            (drw_x2 - 3.0, yt_d, z_front_cad - 3.0),
            (drw_x1 + 3.0, yt_d, z_front_cad - 3.0),
        ],
    )
    add_extrude(
        comp_drw,
        sk_din,
        "19.5 mm",
        (0, -1, 0),
        adsk.fusion.FeatureOperations.CutFeatureOperation,
        "Ext_Cut_Drawer_Interior",
        drw_body,
    )

    # ---- Sub-Component D: Chimera Spire 608-Bearing Mouse Bungee & Magnetic USB-C Dock ----
    occ_sp = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp_sp = occ_sp.component
    comp_sp.name = "P4D_Chimera_Spire_Boom"
    y_sp_base = y_top_deck + 0.5  # 0.5 mm clearance above 608 bearing pocket

    # Side silhouette on YZ plane centered around X = piv_x (width 14 mm)
    p_sp = make_offset_plane(comp_sp, comp_sp.yZConstructionPlane, f"{piv_x - 7.0} mm", "Plane_Spire_Side")
    sk_sp = comp_sp.sketches.add(p_sp)
    sk_sp.name = "Sk_Chimera_Spire_Arm"
    xs = piv_x - 7.0
    # Swept forward-and-up mouse bungee horn + front USB-C plug parking cradle
    draw_poly_3d(
        sk_sp,
        [
            (xs, y_sp_base, piv_z - 9.0),
            (xs, y_sp_base, piv_z + 18.0),
            (xs, y_sp_base + 14.0, piv_z + 24.0),
            (xs, y_sp_base + 54.0, piv_z + 36.0),
            (xs, y_sp_base + 58.0, piv_z + 28.0),
            (xs, y_sp_base + 22.0, piv_z + 10.0),
            (xs, y_sp_base + 12.0, piv_z - 9.0),
        ],
    )
    ext_sp = add_extrude(
        comp_sp, sk_sp, "14.0 mm", (1, 0, 0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation, "Ext_Chimera_Spire"
    )
    sp_body = ext_sp.bodies.item(0)
    sp_body.name = "Body_P4D_Chimera_Spire"

    # Integral Ø7.88 mm 608-bearing shaft pin descending into the 608 inner race!
    p_pin = make_offset_plane(comp_sp, comp_sp.xZConstructionPlane, f"{y_sp_base} mm", "Plane_Spire_Axle")
    sk_pin = comp_sp.sketches.add(p_pin)
    sk_pin.name = "Sk_Spire_608_Pin"
    sk_pin.sketchCurves.sketchCircles.addByCenterRadius(
        pt_sk(sk_pin, piv_x, y_sp_base, piv_z), mm(0.5 * (v["bearing_id"] - 0.12))
    )
    add_extrude(
        comp_sp,
        sk_pin,
        "bearing_w + 0.5 mm",
        (0, -1, 0),
        adsk.fusion.FeatureOperations.JoinFeatureOperation,
        "Ext_Join_Spire_608_Pin",
        sp_body,
    )

    # ---- Assembly Joints (Rigid Caddy, Slider Drawer, Revolute 608 Mouse Spire) ----
    ab_joints = assy_comp.asBuiltJoints

    j_cad_in = ab_joints.createInput(occ_cad, occ_brkt, None)
    j_cad_in.setAsRigidJointMotion()
    j_cad = ab_joints.add(j_cad_in)
    j_cad.name = "Joint_Rigid_HexWingCaddy_DT30"

    # Slider Joint on Magnetic Micro-Drawer
    sk_drw_ax = comp_cad.sketches.add(comp_cad.yZConstructionPlane)
    sk_drw_ax.name = "Sk_Drawer_Slider_Axis"
    d_line = sk_drw_ax.sketchCurves.sketchLines.addByTwoPoints(
        pt_sk(sk_drw_ax, 0.5 * (drw_x1 + drw_x2), drw_y1, zb_d),
        pt_sk(sk_drw_ax, 0.5 * (drw_x1 + drw_x2), drw_y1, zb_d + 40.0),
    )
    d_proxy = d_line.createForAssemblyContext(occ_cad)
    d_geom = adsk.fusion.JointGeometry.createByCurve(d_proxy, adsk.fusion.JointKeyPointTypes.StartKeyPoint)
    sl_in = ab_joints.createInput(occ_drw, occ_cad, d_geom)
    sl_in.setAsSliderJointMotion(adsk.fusion.JointDirections.CustomJointDirection, d_proxy)
    sl_j = ab_joints.add(sl_in)
    sl_j.name = "Joint_Slider_MicroDrawer"

    # Revolute Joint on 608-Bearing Chimera Spire
    sk_sp_ax = comp_brkt.sketches.add(comp_brkt.xYConstructionPlane)
    sk_sp_ax.name = "Sk_Spire_Revolute_Axis"
    r_line = sk_sp_ax.sketchCurves.sketchLines.addByTwoPoints(
        pt_sk(sk_sp_ax, piv_x, y_top_deck - 7.0, piv_z),
        pt_sk(sk_sp_ax, piv_x, y_top_deck + 5.0, piv_z),
    )
    r_proxy = r_line.createForAssemblyContext(occ_brkt)
    r_geom = adsk.fusion.JointGeometry.createByCurve(r_proxy, adsk.fusion.JointKeyPointTypes.StartKeyPoint)
    rv_in = ab_joints.createInput(occ_sp, occ_brkt, r_geom)
    rv_in.setAsRevoluteJointMotion(adsk.fusion.JointDirections.CustomJointDirection, r_proxy)
    rv_j = ab_joints.add(rv_in)
    rv_j.name = "Joint_Revolute_ChimeraSpire_608"

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

        app.executeTextCommand('PTransaction.Start "Build Product 4 HexWing Spire"')
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
            "[Product4_HexWingSpire] Built outboard caddy + magnetic drawer + 608 mouse spire.",
            adsk.core.LogLevels.InfoLogLevel,
            adsk.core.LogTypes.ConsoleLogType,
        )
    except Exception:
        err = traceback.format_exc()
        if app:
            app.log(err, adsk.core.LogLevels.ErrorLogLevel, adsk.core.LogTypes.ConsoleLogType)
        if ui:
            ui.messageBox(f"Product4_HexWingSpire failed:\n{err}")
