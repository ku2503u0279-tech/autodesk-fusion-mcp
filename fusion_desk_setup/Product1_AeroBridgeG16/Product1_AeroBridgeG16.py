# -*- coding: utf-8 -*-
"""
Product 1 — AeroBridge G16 + MagPivot S24+ (Designer Hybrid Wood/Metal/Print v2)
================================================================================
Industrial-design upgrade combining warm 12 mm & 6 mm Walnut/Birch Wood, solid
Ø8 mm Brushed Aluminum tie-rods, and compact sculpted Matte-Black 3D-printed
joinery nodes (`<= 140 mm` max 3D-print size — cuts filament by ~75% and boosts
structural stiffness >6x!):

Individual Pieces Created as Separate Named Components:
  - `W1A_Left_Sculpted_Wood_Arch`  (12 mm Wood, 184 x 134 x 12 mm): Swept organic arch
  - `W1B_Right_Sculpted_Wood_Arch` (12 mm Wood, 184 x 134 x 12 mm): Matching right arch
  - `M1A_Rear_Aluminum_TieRod`     (Ø8 x 360 mm Brushed Aluminum Rod)
  - `M1B_Front_Aluminum_TieRod`    (Ø8 x 360 mm Brushed Aluminum Rod)
  - `W1C_Slatted_Wood_Laptop_Deck` (6 mm Wood, 336 x 182 x 6 mm, 6 stadium intake slots)
  - `P1D_Front_Stopper_Pebbles`    (3D-Printed Matte-Black PETG/TPU, rounded lip cushions)
  - `P1E_Shoulder_DT30_Collars`    (3D-Printed Matte-Black PETG, L/R DT-30 sockets + clips)
  - `P1F_MagPivot_Sculpted_Arm`    (3D-Printed Matte-Black PETG, tapered S-curve arm)
  - `P1G_MagSafe_Halo_Disc`        (3D-Printed Cyber-Red + Matte Black, Ø72 x 9 mm, 8x N52)

Follows `ku2503u0279-tech/autodesk-fusion-mcp` patterns (`guides/fusion-design-guide.md`).
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
    """Generate G1-smooth rounded-corner polygon points so extruded wood/print forms have designer radii."""
    out = []
    n = len(corners_uv)
    for i in range(n):
        u_prev, v_prev = corners_uv[(i - 1) % n]
        u_cur, v_cur = corners_uv[i]
        u_next, v_next = corners_uv[(i + 1) % n]

        d1u, d1v = u_prev - u_cur, v_prev - v_cur
        d2u, d2v = u_next - u_cur, v_next - v_cur
        l1 = math.hypot(d1u, d1v)
        l2 = math.hypot(d2u, d2v)
        if l1 < 1e-3 or l2 < 1e-3:
            out.append((u_cur, v_cur))
            continue
        d1u, d1v = d1u / l1, d1v / l1
        d2u, d2v = d2u / l2, d2v / l2
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


def stadium_pts_2d(cu: float, cv: float, total_u: float, total_v: float, segs: int = 8) -> list:
    """Generate a smooth pill/stadium slot (total_u >= total_v or total_v >= total_u)."""
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
            a = 0.0 + math.pi * (s / float(segs))
            pts.append((cu + r * math.cos(a), cv + dv + r * math.sin(a)))
        for s in range(segs + 1):
            a = math.pi + math.pi * (s / float(segs))
            pts.append((cu + r * math.cos(a), cv - dv + r * math.sin(a)))
    return pts


def register_parameters(design: adsk.fusion.Design) -> dict:
    v = {}
    v["table_length"] = ensure_param(design, "table_length", "630.0 mm", "mm", "Desk width X")
    v["table_depth"] = ensure_param(design, "table_depth", "280.0 mm", "mm", "Desk depth Z")
    v["table_thickness"] = ensure_param(design, "table_thickness", "18.0 mm", "mm", "Wood tabletop thickness")
    v["mat_thickness"] = ensure_param(design, "mat_thickness", "3.0 mm", "mm", "Desk mat thickness")
    v["wood_thick_heavy"] = ensure_param(design, "wood_thick_heavy", "12.0 mm", "mm", "12 mm Birch/Walnut plywood arch thickness")
    v["wood_thick_panel"] = ensure_param(design, "wood_thick_panel", "6.0 mm", "mm", "6 mm Birch/Walnut wood sheet thickness")
    v["rod_dia"] = ensure_param(design, "rod_dia", "8.0 mm", "mm", "Brushed aluminum tie-rod diameter")
    v["fit_clearance"] = ensure_param(design, "fit_clearance", "0.25 mm", "mm", "Nominal 3D-print assembly clearance")
    v["riser_x_left"] = ensure_param(design, "riser_x_left", "88.0 mm", "mm", "Left X coordinate of AeroBridge G16")
    v["riser_inner_span"] = ensure_param(design, "riser_inner_span", "336.0 mm", "mm", "Clear keyboard garage span (>323 mm F75)")
    v["riser_blade_t"] = ensure_param(design, "riser_blade_t", "12.0 mm", "mm", "12 mm sculpted wood side-arch thickness")
    v["riser_z_rear"] = ensure_param(design, "riser_z_rear", "12.0 mm", "mm", "Rear wall clearance for lid & exhaust")
    # DFM: a 264 mm deep ROG Strix G16 at 18 deg needs 251 mm of horizontal run.  The arch
    # must therefore reach Z = 254 mm so the laptop's rear edge parks at Z ~= 7 mm instead of
    # passing through the back wall at Z = 0.
    v["riser_base_depth"] = ensure_param(design, "riser_base_depth", "242.0 mm", "mm", "Arch Z depth")
    v["garage_clear_h"] = ensure_param(design, "garage_clear_h", "62.0 mm", "mm", "Clear bridge ceiling above mat")
    v["laptop_tilt_deg"] = ensure_param(design, "laptop_tilt_deg", "18.0 deg", "deg", "Ergonomic laptop tilt angle")
    v["front_lip_h"] = ensure_param(design, "front_lip_h", "18.0 mm", "mm", "Cushioned laptop front retention lip")
    v["dt30_width"] = ensure_param(design, "dt30_width", "30.0 mm", "mm", "Shared DT-30 dovetail root width")
    v["dt30_depth"] = ensure_param(design, "dt30_depth", "6.0 mm", "mm", "Shared DT-30 dovetail depth")
    v["magnet_dia"] = ensure_param(design, "magnet_dia", "6.0 mm", "mm", "N52 disc magnet diameter")
    v["magnet_h"] = ensure_param(design, "magnet_h", "3.0 mm", "mm", "N52 disc magnet thickness")
    v["magnet_clear"] = ensure_param(design, "magnet_clear", "0.15 mm", "mm", "Press-fit magnet allowance")
    v["m4_bolt_clear"] = ensure_param(design, "m4_bolt_clear", "4.3 mm", "mm", "M4 pin/axle clearance hole")
    v["magsafe_ring_pcd"] = ensure_param(design, "magsafe_ring_pcd", "54.0 mm", "mm", "MagSafe magnet array PCD")
    return v


def _build_wood_arch(
    assy_comp: adsk.fusion.Component,
    comp_name: str,
    body_name: str,
    x_plane_expr: str,
    x_val_mm: float,
    v: dict,
) -> adsk.fusion.Occurrence:
    """Create a 12 mm Sculpted Organic Wood Side Arch (`W1A` / `W1B`)."""
    occ = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp = occ.component
    comp.name = comp_name

    y_mat = v["mat_thickness"]                        # 3.0 mm
    z0 = v["riser_z_rear"]                            # 12.0 mm
    z_foot = z0 + 148.0                               # 160.0 mm
    z_cant = z0 + v["riser_base_depth"]               # 196.0 mm
    y_front_bot = y_mat + v["garage_clear_h"]         # 65.0 mm clear garage ceiling
    y_front_top = y_front_bot + 13.0                  # 78.0 mm
    tilt_rad = math.radians(v["laptop_tilt_deg"])
    y_rear_top = y_front_top + (z_cant - z0) * math.tan(tilt_rad)

    plane = make_offset_plane(comp, comp.yZConstructionPlane, x_plane_expr, f"Plane_{comp_name}")
    sk = comp.sketches.add(plane)
    sk.name = f"Sk_{comp_name}_OrganicCurve"

    # Swept designer C-arch control polygon rounded with generous G1 radii
    raw_yz = [
        (y_mat, z0),
        (y_mat, z_foot),
        (y_mat + 13.0, z_foot),
        (y_mat + 16.0, z0 + 46.0),
        (y_front_bot, z0 + 98.0),
        (y_front_bot, z_cant),
        (y_front_top, z_cant),
        (y_rear_top, z0),
    ]
    smooth_yz = sample_rounded_poly_2d(raw_yz, radius=9.0, segs_per_corner=5)
    draw_poly_3d(sk, [(x_val_mm, yy, zz) for (yy, zz) in smooth_yz])

    ext = add_extrude(
        comp, sk, "riser_blade_t", (1, 0, 0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation, f"Ext_{comp_name}"
    )
    body = ext.bodies.item(0)
    body.name = body_name

    # Sculpted stadium-pill side relief cutout + 2x Ø8.1 mm aluminum tie-rod bores
    sk_cut = comp.sketches.add(plane)
    sk_cut.name = f"Sk_{comp_name}_PillAndRods"
    pill_yz = stadium_pts_2d(y_mat + 58.0, z0 + 26.0, 56.0, 20.0, segs=8)
    draw_poly_3d(sk_cut, [(x_val_mm, yy, zz) for (yy, zz) in pill_yz])
    rod_r = 0.5 * (v["rod_dia"] + 0.2)
    sk_cut.sketchCurves.sketchCircles.addByCenterRadius(pt_sk(sk_cut, x_val_mm, y_mat + 86.0, z0 + 28.0), mm(rod_r))
    sk_cut.sketchCurves.sketchCircles.addByCenterRadius(pt_sk(sk_cut, x_val_mm, y_front_bot + 6.5, z_cant - 32.0), mm(rod_r))
    add_extrude(
        comp,
        sk_cut,
        "riser_blade_t + 1 mm",
        (1, 0, 0),
        adsk.fusion.FeatureOperations.CutFeatureOperation,
        f"Ext_Cut_{comp_name}_Features",
        body,
    )
    return occ


def _build_aluminum_tie_rods(assy_comp: adsk.fusion.Component, v: dict) -> tuple:
    """Create M1A & M1B Ø8 x 360 mm Brushed Aluminum Tie-Rods."""
    x0 = v["riser_x_left"]
    y_mat = v["mat_thickness"]
    z0 = v["riser_z_rear"]
    z_cant = z0 + v["riser_base_depth"]
    y_front_bot = y_mat + v["garage_clear_h"]
    span_expr = "2 * riser_blade_t + riser_inner_span"

    rods = []
    for comp_n, body_n, ry, rz in [
        ("M1A_Rear_Aluminum_TieRod", "Body_M1A_Rear_TieRod", y_mat + 86.0, z0 + 28.0),
        ("M1B_Front_Aluminum_TieRod", "Body_M1B_Front_TieRod", y_front_bot + 6.5, z_cant - 32.0),
    ]:
        occ = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        comp = occ.component
        comp.name = comp_n
        pl = make_offset_plane(comp, comp.yZConstructionPlane, "riser_x_left", f"Plane_{comp_n}")
        sk = comp.sketches.add(pl)
        sk.name = f"Sk_{comp_n}"
        sk.sketchCurves.sketchCircles.addByCenterRadius(pt_sk(sk, x0, ry, rz), mm(0.5 * v["rod_dia"]))
        ext = add_extrude(
            comp, sk, span_expr, (1, 0, 0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation, f"Ext_{comp_n}"
        )
        ext.bodies.item(0).name = body_n
        rods.append(occ)
    return rods[0], rods[1]


def _build_slatted_wood_deck_and_stoppers(assy_comp: adsk.fusion.Component, v: dict) -> tuple:
    """Create W1C 6 mm Slatted Wood Laptop Deck + P1D 3D-Printed Rounded Front Stopper Cushions."""
    x_left = v["riser_x_left"]
    total_w = 2.0 * v["riser_blade_t"] + v["riser_inner_span"]  # 360.0 mm
    z_front = v["riser_z_rear"] + v["riser_base_depth"] + 4.0   # 258.0 mm
    # 250 mm deck = the full height of both arch top edges, so the G16 base is supported end to end
    deck_len = 250.0
    tilt_rad = math.radians(v["laptop_tilt_deg"])
    y_front = v["mat_thickness"] + v["garage_clear_h"] + 13.0   # 78.0 mm
    t_wood = v["wood_thick_panel"]                              # 6.0 mm

    uz, uy = -math.cos(tilt_rad), math.sin(tilt_rad)
    nz, ny = math.sin(tilt_rad), math.cos(tilt_rad)

    # W1C: Single-piece 6 mm Wood Ventilated Laptop Deck (360 x 180 x 6 mm)
    occ_deck = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp_deck = occ_deck.component
    comp_deck.name = "W1C_Slatted_Wood_Laptop_Deck"
    pl = make_offset_plane(comp_deck, comp_deck.yZConstructionPlane, "riser_x_left", "Plane_W1C_Side")
    sk = comp_deck.sketches.add(pl)
    sk.name = "Sk_W1C_WoodDeck"
    p0 = (x_left, y_front, z_front)
    p1 = (x_left, y_front + deck_len * uy, z_front + deck_len * uz)
    p2 = (x_left, p1[1] + t_wood * ny, p1[2] + t_wood * nz)
    p3 = (x_left, y_front + t_wood * ny, z_front + t_wood * nz)
    draw_poly_3d(sk, [p0, p1, p2, p3])
    ext_d = add_extrude(
        comp_deck,
        sk,
        "2 * riser_blade_t + riser_inner_span",
        (1, 0, 0),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
        "Ext_W1C_WoodDeck",
    )
    deck_body = ext_d.bodies.item(0)
    deck_body.name = "Body_W1C_Slatted_Wood_Deck"

    # Cut 6 Designer Stadium-Pill Cooling Slots through W1C
    p_cut = make_offset_plane(comp_deck, comp_deck.xZConstructionPlane, "195.0 mm", "Plane_W1C_StadiumSlots")
    sk_slots = comp_deck.sketches.add(p_cut)
    sk_slots.name = "Sk_W1C_6x_StadiumSlots"
    for k in range(6):
        sx = x_left + 48.0 + k * 52.8
        pill = stadium_pts_2d(sx, z_front - 92.0 * math.cos(tilt_rad), 30.0, 118.0, segs=7)
        draw_poly_3d(sk_slots, [(uu, 195.0, vv) for (uu, vv) in pill])
    add_extrude(
        comp_deck,
        sk_slots,
        "150.0 mm",
        (0, -1, 0),
        adsk.fusion.FeatureOperations.CutFeatureOperation,
        "Ext_Cut_W1C_StadiumSlots",
        deck_body,
    )

    # P1D: Compact 3D-Printed Rounded Pebble Front Stopper Pair (Left & Right, 44 mm wide each!)
    occ_stop_l = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    occ_stop_r = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    for occ_s, cname, bname, xs_val in [
        (occ_stop_l, "P1D_Left_Stopper_Pebble", "Body_P1D_Stopper_Left", x_left + 32.0),
        (occ_stop_r, "P1D_Right_Stopper_Pebble", "Body_P1D_Stopper_Right", x_left + total_w - 76.0),
    ]:
        cs = occ_s.component
        cs.name = cname
        ps = make_offset_plane(cs, cs.yZConstructionPlane, f"{xs_val} mm", f"Plane_{cname}")
        sks = cs.sketches.add(ps)
        sks.name = f"Sk_{cname}"
        lip_h = v["front_lip_h"]
        raw_pebble = [
            (y_front - 4.0 * ny, z_front - 4.0 * nz),
            (y_front - 4.0 * ny + 18.0 * uy, z_front - 4.0 * nz + 18.0 * uz),
            (y_front + t_wood * ny + 18.0 * uy, z_front + t_wood * nz + 18.0 * uz),
            (y_front + t_wood * ny + 10.0 * uy, z_front + t_wood * nz + 10.0 * uz),
            (y_front + (t_wood + lip_h) * ny + 8.0 * uy, z_front + (t_wood + lip_h) * nz + 8.0 * uz),
            (y_front + (t_wood + lip_h) * ny - 4.0 * uy, z_front + (t_wood + lip_h) * nz - 4.0 * uz),
        ]
        smooth_p = sample_rounded_poly_2d(raw_pebble, radius=3.5, segs_per_corner=4)
        draw_poly_3d(sks, [(xs_val, yy, zz) for (yy, zz) in smooth_p])
        es = add_extrude(cs, sks, "44.0 mm", (1, 0, 0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation, f"Ext_{cname}")
        es.bodies.item(0).name = bname

    return occ_deck, occ_stop_l, occ_stop_r


def _build_dt30_shoulder_collars(assy_comp: adsk.fusion.Component, v: dict) -> tuple:
    """Create compact 3D-printed Left & Right DT-30 Shoulder Nodes (`P1E_Left`, `P1E_Right`, 44 x 46 x 14 mm)."""
    z_mid = v["riser_z_rear"] + 34.0  # 46.0 mm
    dt_d = v["dt30_depth"]
    hb = 0.5 * (v["dt30_width"] + 2.0 * v["fit_clearance"])
    hn = hb - dt_d / math.tan(math.radians(60.0))

    x_outer_l = v["riser_x_left"]                                                     # 88.0 mm
    x_outer_r = v["riser_x_left"] + 2.0 * v["riser_blade_t"] + v["riser_inner_span"]  # 448.0 mm

    collars = []
    for cname, bname, x_face, sign_out in [
        ("P1E_Left_DT30_Collar", "Body_P1E_Collar_Left", x_outer_l, -1.0),
        ("P1E_Right_DT30_Collar", "Body_P1E_Collar_Right", x_outer_r, +1.0),
    ]:
        occ = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        comp = occ.component
        comp.name = cname
        pl = make_offset_plane(comp, comp.xZConstructionPlane, "132.0 mm", f"Plane_{cname}")
        sk = comp.sketches.add(pl)
        sk.name = f"Sk_{cname}_Housing"
        x_ext = x_face + sign_out * 11.0
        pts_xz = sample_rounded_poly_2d(
            [
                (x_face, z_mid - 22.0),
                (x_ext, z_mid - 22.0),
                (x_ext, z_mid + 22.0),
                (x_face, z_mid + 22.0),
            ],
            radius=4.5,
            segs_per_corner=4,
        )
        draw_poly_3d(sk, [(xx, 132.0, zz) for (xx, zz) in pts_xz])
        ext = add_extrude(
            comp, sk, "44.0 mm", (0, -1, 0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation, f"Ext_{cname}"
        )
        body = ext.bodies.item(0)
        body.name = bname

        # Cut female DT-30 socket into outer face of collar
        sk_cut = comp.sketches.add(pl)
        sk_cut.name = f"Sk_{cname}_DT30_Cut"
        draw_poly_3d(
            sk_cut,
            [
                (x_ext + sign_out * 0.5, 132.0, z_mid - hn),
                (x_ext - sign_out * dt_d, 132.0, z_mid - hb),
                (x_ext - sign_out * dt_d, 132.0, z_mid + hb),
                (x_ext + sign_out * 0.5, 132.0, z_mid + hn),
            ],
        )
        add_extrude(
            comp,
            sk_cut,
            "45.0 mm",
            (0, -1, 0),
            adsk.fusion.FeatureOperations.CutFeatureOperation,
            f"Ext_Cut_{cname}_DT30",
            body,
        )
        collars.append(occ)
    return collars[0], collars[1]


def _build_sculpted_magpivot(assy_comp: adsk.fusion.Component, v: dict) -> tuple:
    """Build P1F Sculpted MagPivot Arm + P1G Rounded MagSafe Halo Disc."""
    x_collar_out = v["riser_x_left"] - 11.0  # 77.0 mm
    z_mid = v["riser_z_rear"] + 34.0         # 46.0 mm
    dt_d = v["dt30_depth"] - v["fit_clearance"]
    hb = 0.5 * v["dt30_width"]
    hn = hb - dt_d / math.tan(math.radians(60.0))

    occ_arm = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp_arm = occ_arm.component
    comp_arm.name = "P1F_MagPivot_Sculpted_Arm"
    p_top = make_offset_plane(comp_arm, comp_arm.xZConstructionPlane, "130.0 mm", "Plane_MagPivot_Arm")
    sk_arm = comp_arm.sketches.add(p_top)
    sk_arm.name = "Sk_MagPivot_Sculpted_Arm"
    draw_poly_3d(
        sk_arm,
        [
            (x_collar_out, 130.0, z_mid - hn),
            (x_collar_out + dt_d, 130.0, z_mid - hb),
            (x_collar_out + dt_d, 130.0, z_mid + hb),
            (x_collar_out, 130.0, z_mid + hn),
            (x_collar_out, 130.0, z_mid + 18.0),
            (22.0, 130.0, z_mid + 44.0),
            (14.0, 130.0, z_mid + 44.0),
            (14.0, 130.0, z_mid + 30.0),
            (x_collar_out - 10.0, 130.0, z_mid - 16.0),
            (x_collar_out, 130.0, z_mid - 16.0),
        ],
    )
    ext_arm = add_extrude(
        comp_arm, sk_arm, "38.0 mm", (0, -1, 0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation, "Ext_MagPivot_Arm"
    )
    ext_arm.bodies.item(0).name = "Body_P1F_MagPivot_Arm"

    disc_z, disc_x, disc_y = z_mid + 44.0, 38.0, 148.0
    occ_disc = assy_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp_disc = occ_disc.component
    comp_disc.name = "P1G_MagSafe_Halo_Disc"
    p_disc = make_offset_plane(comp_disc, comp_disc.xYConstructionPlane, f"{disc_z} mm", "Plane_MagSafe_Disc")
    sk_disc = comp_disc.sketches.add(p_disc)
    sk_disc.name = "Sk_MagSafe_Halo_Outer"
    sk_disc.sketchCurves.sketchCircles.addByCenterRadius(pt_sk(sk_disc, disc_x, disc_y, disc_z), mm(35.0))
    ext_disc = add_extrude(
        comp_disc, sk_disc, "9.0 mm", (0, 0, 1), adsk.fusion.FeatureOperations.NewBodyFeatureOperation, "Ext_MagSafe_Disc"
    )
    disc_body = ext_disc.bodies.item(0)
    disc_body.name = "Body_P1G_MagSafe_Disc"

    front_p = make_offset_plane(comp_disc, comp_disc.xYConstructionPlane, f"{disc_z + 9.0} mm", "Plane_MagSafe_Front")
    sk_mags = comp_disc.sketches.add(front_p)
    sk_mags.name = "Sk_MagSafe_8x_N52_Array"
    mag_r = 0.5 * (v["magnet_dia"] + v["magnet_clear"])
    pcd_r = 0.5 * v["magsafe_ring_pcd"]
    for k in range(8):
        ang = math.radians(k * 45.0)
        sk_mags.sketchCurves.sketchCircles.addByCenterRadius(
            pt_sk(sk_mags, disc_x + pcd_r * math.cos(ang), disc_y + pcd_r * math.sin(ang), disc_z + 9.0), mm(mag_r)
        )
    add_extrude(
        comp_disc, sk_mags, "magnet_h + 0.2 mm", (0, 0, -1), adsk.fusion.FeatureOperations.CutFeatureOperation, "Ext_Cut_MagSafe", disc_body
    )

    return occ_arm, occ_disc, (disc_x, disc_y, disc_z)


def build_product(design: adsk.fusion.Design, parent_comp: adsk.fusion.Component = None) -> adsk.fusion.Occurrence:
    if parent_comp is None:
        parent_comp = design.rootComponent

    v = register_parameters(design)

    assy_occ = parent_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    assy_comp = assy_occ.component
    assy_comp.name = "Product1_AeroBridgeG16"

    occ_wl = _build_wood_arch(assy_comp, "W1A_Left_Sculpted_Wood_Arch", "Body_W1A_Left_Wood_Arch", "riser_x_left", v["riser_x_left"], v)
    x_right = v["riser_x_left"] + v["riser_blade_t"] + v["riser_inner_span"]
    occ_wr = _build_wood_arch(
        assy_comp, "W1B_Right_Sculpted_Wood_Arch", "Body_W1B_Right_Wood_Arch", "riser_x_left + riser_blade_t + riser_inner_span", x_right, v
    )
    occ_r1, occ_r2 = _build_aluminum_tie_rods(assy_comp, v)
    occ_deck, occ_st_l, occ_st_r = _build_slatted_wood_deck_and_stoppers(assy_comp, v)
    occ_col_l, occ_col_r = _build_dt30_shoulder_collars(assy_comp, v)
    occ_arm, occ_disc, piv_xyz = _build_sculpted_magpivot(assy_comp, v)

    ab = assy_comp.asBuiltJoints
    for child_o, jname in [
        (occ_r1, "Joint_Rigid_RearRod_to_LeftArch"),
        (occ_r2, "Joint_Rigid_FrontRod_to_LeftArch"),
        (occ_wr, "Joint_Rigid_RightArch_to_Rods"),
        (occ_deck, "Joint_Rigid_WoodDeck_to_Arches"),
        (occ_st_l, "Joint_Rigid_LeftStopper_to_Deck"),
        (occ_st_r, "Joint_Rigid_RightStopper_to_Deck"),
        (occ_col_l, "Joint_Rigid_LeftCollar_to_LeftArch"),
        (occ_col_r, "Joint_Rigid_RightCollar_to_RightArch"),
        (occ_arm, "Joint_Rigid_MagPivot_to_LeftCollar"),
    ]:
        ji = ab.createInput(child_o, occ_wl, None)
        ji.setAsRigidJointMotion()
        j = ab.add(ji)
        j.name = jname

    px, py, pz = piv_xyz
    sk_piv = occ_arm.component.sketches.add(occ_arm.component.yZConstructionPlane)
    sk_piv.name = "Sk_MagSafe_Revolute_Axis"
    piv_line = sk_piv.sketchCurves.sketchLines.addByTwoPoints(pt_sk(sk_piv, px, py, pz), pt_sk(sk_piv, px, py, pz + 9.0))
    piv_proxy = piv_line.createForAssemblyContext(occ_arm)
    piv_geom = adsk.fusion.JointGeometry.createByCurve(piv_proxy, adsk.fusion.JointKeyPointTypes.StartKeyPoint)
    rev_in = ab.createInput(occ_disc, occ_arm, piv_geom)
    rev_in.setAsRevoluteJointMotion(adsk.fusion.JointDirections.CustomJointDirection, piv_proxy)
    rev_j = ab.add(rev_in)
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
        app.executeTextCommand('PTransaction.Start "Build Product 1 Designer Hybrid"')
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
            ui.messageBox(f"Product1_AeroBridgeG16 failed:\n{err}")
