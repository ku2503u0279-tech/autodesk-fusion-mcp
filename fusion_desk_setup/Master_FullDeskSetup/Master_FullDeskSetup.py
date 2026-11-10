# -*- coding: utf-8 -*-
"""
Master Full Desk Setup — Complete Assembly, Render Scene & Batch 3MF/STL Exporter
=================================================================================
Builds the entire 630 x 280 x 18 mm desk ecosystem in one parametric document:
  1. Environment Component (`Env_Table_Mat_And_Devices`):
     - 630 x 280 x 18 mm Dark Walnut Tabletop + 630 x 280 x 3 mm Stealth Desk Mat
     - Reference envelopes for ASUS ROG Strix G16 (open), 280W Brick (inside vault),
       AULA F75, Kreo Chimera V2, Sony ULT WEAR, Samsung S24+, 76 mm Bottle, A5 Notebook
  2. Imports & builds Products 1, 2, 3, and 4 as sub-assemblies and joins them to
     the tabletop with Fusion `AsBuiltJoints`.
  3. Applies Stealth Matte Black, Gunmetal Grey, Cyber-Red Accent, and Dark Walnut
     appearances from Fusion's Appearance Library for immediate photoreal rendering.
  4. Configures a Perspective Hero Camera and includes `export_printable_meshes()`
     (`AUTO_EXPORT_MESHES = False` by default; set `True` to batch-export all `.3mf`
     and `.stl` files to `~/Desktop/FusionDeskSetup_Exports/`).

Follows `ku2503u0279-tech/autodesk-fusion-mcp` patterns:
  - `guides/fusion-design-guide.md` §§4–15
  - `fusion_bridge/viewport.py` (camera pose & perspective setup)
"""

import importlib.util
import math
import os
import traceback
import adsk.core
import adsk.fusion

# Toggle True if you want running Master_FullDeskSetup to immediately export all
# printable bodies as .3mf and .stl into ~/Desktop/FusionDeskSetup_Exports/
AUTO_EXPORT_MESHES = False


def mm(val_mm: float) -> float:
    return float(val_mm) * 0.1


def _load_sibling_module(folder_name: str, module_name: str):
    here = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(os.path.dirname(here), folder_name, f"{module_name}.py")
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        raise FileNotFoundError(f"Could not locate sibling script at: {script_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _pt_sk(sketch: adsk.fusion.Sketch, x_mm: float, y_mm: float, z_mm: float) -> adsk.core.Point3D:
    return sketch.modelToSketchSpace(adsk.core.Point3D.create(mm(x_mm), mm(y_mm), mm(z_mm)))


def _extrude_box(
    comp: adsk.fusion.Component,
    body_name: str,
    x1: float,
    x2: float,
    y1: float,
    y2: float,
    z1: float,
    z2: float,
) -> adsk.fusion.BRepBody:
    planes = comp.constructionPlanes
    p_in = planes.createInput()
    p_in.setByOffset(comp.xZConstructionPlane, adsk.core.ValueInput.createByString(f"{y1} mm"))
    plane = planes.add(p_in)
    plane.name = f"Plane_{body_name}"

    sk = comp.sketches.add(plane)
    sk.name = f"Sk_{body_name}"
    lines = sk.sketchCurves.sketchLines
    pts = [(x1, y1, z1), (x2, y1, z1), (x2, y1, z2), (x1, y1, z2)]
    for i in range(4):
        lines.addByTwoPoints(_pt_sk(sk, *pts[i]), _pt_sk(sk, *pts[(i + 1) % 4]))

    col = adsk.core.ObjectCollection.create()
    for i in range(sk.profiles.count):
        col.add(sk.profiles.item(i))

    n = sk.xDirection.crossProduct(sk.yDirection)
    sign = 1 if n.y >= 0.0 else -1
    h_mm = y2 - y1
    expr = f"{h_mm} mm" if sign > 0 else f"-({h_mm} mm)"
    ext_in = comp.features.extrudeFeatures.createInput(col, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ext_in.setDistanceExtent(False, adsk.core.ValueInput.createByString(expr))
    feat = comp.features.extrudeFeatures.add(ext_in)
    feat.name = f"Ext_{body_name}"
    body = feat.bodies.item(0)
    body.name = body_name
    return body


def build_environment_and_devices(design: adsk.fusion.Design, root: adsk.fusion.Component) -> adsk.fusion.Occurrence:
    """Create the 630x280x18 mm Wood Tabletop, 3 mm Mat, and accurate Reference Devices."""
    env_occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    env_comp = env_occ.component
    env_comp.name = "Env_Table_Mat_And_Devices"

    # 1. Wood Tabletop (X=0..630, Y=-18..0, Z=0..280) + Full-Surface Desk Mat (Y=0..3)
    _extrude_box(env_comp, "Ref_Wood_Tabletop_630x280x18", 0.0, 630.0, -18.0, 0.0, 0.0, 280.0)
    _extrude_box(env_comp, "Ref_Desk_Mat_630x280x3", 0.0, 630.0, 0.0, 3.0, 0.0, 280.0)

    # 2. Reference Devices (in their exact collision-free operating positions!)
    # AULA F75 Keyboard (323 x 143.2 x 43.1 mm) positioned in active typing/gaming zone
    _extrude_box(env_comp, "Ref_AULA_F75_Keyboard", 106.5, 429.5, 3.0, 46.1, 132.0, 275.2)
    # Kreo Chimera V2 Wireless Mouse (64 x 125 x 40 mm) on open right mouse zone
    _extrude_box(env_comp, "Ref_Kreo_Chimera_V2_Mouse", 506.0, 570.0, 3.0, 43.0, 125.0, 250.0)
    # ROG 280W Power Brick (26 x 82 x 180 mm) completely hidden inside Product 2 StealthVault!
    _extrude_box(env_comp, "Ref_ROG_280W_Power_Brick", -12.0, 14.0, -116.0, -34.0, 22.0, 202.0)
    # Samsung Galaxy S24+ in MagSafe Case (80 x 163 x 12 mm) docked on MagPivot Wing
    _extrude_box(env_comp, "Ref_Samsung_S24_Plus", -2.0, 78.0, 68.0, 231.0, 99.5, 111.5)
    # A5 Notebook (148 x 210 x 15 mm) stowed inside Product 3 Under-Desk Sling
    _extrude_box(env_comp, "Ref_A5_Notebook", 468.0, 616.0, -56.0, -41.0, 60.0, 270.0)
    # 25.4 mm K9 Optical 50:50 Beam-Splitter Cube seated inside Product 5 (HoloBuddy)!
    _extrude_box(env_comp, "Ref_K9_BeamSplitter_Cube_25_4mm", 477.3, 502.7, 149.0, 174.4, 59.3, 84.7)

    # Water Bottle (Ø76 x 220 mm) resting inside Product 3 Outboard Bottle Cage
    planes = env_comp.constructionPlanes
    p_in = planes.createInput()
    p_in.setByOffset(env_comp.xZConstructionPlane, adsk.core.ValueInput.createByString("-56.0 mm"))
    b_plane = planes.add(p_in)
    b_plane.name = "Plane_Ref_Bottle"
    sk_bot = env_comp.sketches.add(b_plane)
    sk_bot.name = "Sk_Ref_Bottle_76mm"
    sk_bot.sketchCurves.sketchCircles.addByCenterRadius(_pt_sk(sk_bot, 687.5, -56.0, 204.0), mm(38.0))
    col = adsk.core.ObjectCollection.create()
    col.add(sk_bot.profiles.item(0))
    n = sk_bot.xDirection.crossProduct(sk_bot.yDirection)
    expr = "220.0 mm" if n.y >= 0.0 else "-(220.0 mm)"
    b_ext_in = env_comp.features.extrudeFeatures.createInput(col, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    b_ext_in.setDistanceExtent(False, adsk.core.ValueInput.createByString(expr))
    b_feat = env_comp.features.extrudeFeatures.add(b_ext_in)
    b_feat.name = "Ext_Ref_WaterBottle"
    b_feat.bodies.item(0).name = "Ref_Water_Bottle_76mm"

    # Tilted ASUS ROG Strix G16 (354 x 264 x 24 mm base + open screen) on Product 1 @ 18 deg
    p_g16_in = planes.createInput()
    p_g16_in.setByOffset(env_comp.yZConstructionPlane, adsk.core.ValueInput.createByString("91.0 mm"))
    g_plane = planes.add(p_g16_in)
    g_plane.name = "Plane_Ref_ROG_Strix_G16"
    sk_g = env_comp.sketches.add(g_plane)
    sk_g.name = "Sk_Ref_ROG_Strix_G16_Open"
    tilt = math.radians(18.0)
    uz, uy = -math.cos(tilt), math.sin(tilt)
    nz, ny = math.sin(tilt), math.cos(tilt)
    zf, yf = 200.0, 85.0
    # Base chassis + 112-deg open 16" display silhouette
    scr_ang = math.radians(110.0 - 18.0)
    sz, sy = -math.cos(scr_ang), math.sin(scr_ang)
    zr, yr = zf + 264.0 * uz, yf + 264.0 * uy
    g_pts = [
        (91.0, yf, zf),
        (91.0, yr, zr),
        (91.0, yr + 245.0 * sy, zr + 245.0 * sz),
        (91.0, yr + 245.0 * sy + 7.0 * sz, zr + 245.0 * sz - 7.0 * sy),
        (91.0, yr + 24.0 * ny, zr + 24.0 * nz),
        (91.0, yf + 22.6 * ny, zf + 22.6 * nz),
    ]
    glines = sk_g.sketchCurves.sketchLines
    for i in range(len(g_pts)):
        glines.addByTwoPoints(_pt_sk(sk_g, *g_pts[i]), _pt_sk(sk_g, *g_pts[(i + 1) % len(g_pts)]))
    gcol = adsk.core.ObjectCollection.create()
    for i in range(sk_g.profiles.count):
        gcol.add(sk_g.profiles.item(i))
    gn = sk_g.xDirection.crossProduct(sk_g.yDirection)
    gexpr = "354.0 mm" if gn.x >= 0.0 else "-(354.0 mm)"
    g_in = env_comp.features.extrudeFeatures.createInput(gcol, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    g_in.setDistanceExtent(False, adsk.core.ValueInput.createByString(gexpr))
    g_feat = env_comp.features.extrudeFeatures.add(g_in)
    g_feat.name = "Ext_Ref_ROG_Strix_G16"
    g_feat.bodies.item(0).name = "Ref_ASUS_ROG_Strix_G16"

    if hasattr(env_occ, "isGroundToParent"):
        env_occ.isGroundToParent = True

    return env_occ


def _find_appearance(app: adsk.core.Application, design: adsk.fusion.Design, candidates: list):
    """Locate a Fusion Appearance by candidate names across the document and loaded libraries."""
    for name in candidates:
        existing = design.appearances.itemByName(name)
        if existing:
            return existing
    libs = app.materialLibraries
    if libs:
        for i in range(libs.count):
            lib = libs.item(i)
            for name in candidates:
                try:
                    found = lib.appearances.itemByName(name)
                    if found:
                        return found
                except Exception:
                    continue
    return None


def apply_stealth_rog_appearances(app: adsk.core.Application, design: adsk.fusion.Design):
    """Assign Stealth Matte Black, Gunmetal, Cyber-Red Accent & Walnut appearances for Render workspace."""
    ap_matte_black = _find_appearance(
        app, design, ["Plastic - Matte (Black)", "ABS (White)", "Paint - Enamel Matte (Black)"]
    )
    ap_gunmetal = _find_appearance(
        app, design, ["Aluminum - Anodized Rough (Grey)", "Aluminum - Satin", "Steel - Satin"]
    )
    ap_cyber_red = _find_appearance(
        app, design, ["Aluminum - Anodized Glossy (Red)", "Plastic - Glossy (Red)", "Paint - Metallic (Red)"]
    )
    ap_walnut = _find_appearance(
        app, design, ["Wood - Walnut", "3D Walnut - Glossy", "Cherry"]
    )
    ap_fabric = _find_appearance(
        app, design, ["Fabric (Black)", "Rubber - Soft", "Leather - Matte (Black)"]
    )
    ap_glass = _find_appearance(
        app, design, ["Glass - Heavy Color (Blue)", "Glass (Clear)", "Glass - Smooth"]
    )

    for comp in design.allComponents:
        for j in range(comp.bRepBodies.count):
            body = comp.bRepBodies.item(j)
            bname = body.name
            try:
                if "BeamSplitter_Cube" in bname and ap_glass:
                    body.appearance = ap_glass
                elif "Wood_Tabletop" in bname and ap_walnut:
                    body.appearance = ap_walnut
                elif "Desk_Mat" in bname and ap_fabric:
                    body.appearance = ap_fabric
                elif any(k in bname for k in ("MagSafe_Disc", "Spire", "ULT_Saddle", "Glare_Visor")) and ap_cyber_red:
                    body.appearance = ap_cyber_red
                elif any(k in bname for k in ("Spreader", "Door", "Drawer", "Notebook_Tray", "Desk_Pedestal")) and ap_gunmetal:
                    body.appearance = ap_gunmetal
                elif ap_matte_black:
                    body.appearance = ap_matte_black
            except Exception:
                pass


def configure_hero_camera(app: adsk.core.Application):
    """Configure a 3/4 Perspective Hero Camera framing the full 630x280 mm battle station."""
    vp = app.activeViewport
    if not vp:
        return
    cam = vp.camera
    cam.isSmoothTransition = False
    cam.cameraType = adsk.core.CameraTypes.PerspectiveCameraType
    # Fusion camera coordinates are in cm: center target near middle of elevated setup
    cam.target = adsk.core.Point3D.create(31.5, 6.5, 14.0)
    cam.eye = adsk.core.Point3D.create(-32.0, 48.0, 78.0)
    cam.upVector = adsk.core.Vector3D.create(0.0, 1.0, 0.0)
    cam.perspectiveAngle = math.radians(34.0)
    vp.camera = cam
    vp.refresh()


def export_printable_meshes(design: adsk.fusion.Design, export_dir: str = None) -> list:
    """Batch-export every printable `Body_P*` solid as both `.3mf` and high-refinement `.stl`."""
    if export_dir is None:
        export_dir = os.path.join(os.path.expanduser("~"), "Desktop", "FusionDeskSetup_Exports")
    os.makedirs(export_dir, exist_ok=True)

    exp_mgr = design.exportManager
    exported_files = []

    for comp in design.allComponents:
        for i in range(comp.bRepBodies.count):
            body = comp.bRepBodies.item(i)
            if not body.name.startswith("Body_P"):
                continue

            # 1. High-resolution STL export
            stl_path = os.path.join(export_dir, f"{body.name}.stl")
            stl_opts = exp_mgr.createSTLExportOptions(body, stl_path)
            stl_opts.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
            exp_mgr.execute(stl_opts)
            exported_files.append(stl_path)

            # 2. Modern 3MF export (preserves millimeter units automatically for Bambu/Prusa/OrcaSlicer)
            if hasattr(exp_mgr, "createC3MFExportOptions"):
                tmf_path = os.path.join(export_dir, f"{body.name}.3mf")
                tmf_opts = exp_mgr.createC3MFExportOptions(body, tmf_path)
                exp_mgr.execute(tmf_opts)
                exported_files.append(tmf_path)

    return exported_files


def build_full_setup(app: adsk.core.Application, design: adsk.fusion.Design):
    root = design.rootComponent

    p1 = _load_sibling_module("Product1_AeroBridgeG16", "Product1_AeroBridgeG16")
    p2 = _load_sibling_module("Product2_StealthVaultULT", "Product2_StealthVaultULT")
    p3 = _load_sibling_module("Product3_HydroSling", "Product3_HydroSling")
    p4 = _load_sibling_module("Product4_HexWingSpire", "Product4_HexWingSpire")
    p5 = _load_sibling_module("Product5_HoloBuddy", "Product5_HoloBuddy")

    env_occ = build_environment_and_devices(design, root)
    occ1 = p1.build_product(design, root)
    occ2 = p2.build_product(design, root)
    occ3 = p3.build_product(design, root)
    occ4 = p4.build_product(design, root)
    occ5 = p5.build_product(design, root)

    # Lock all 5 modular product assemblies into place with Rigid AsBuiltJoints
    ab = root.asBuiltJoints
    for prod_occ, anchor_occ, jname in [
        (occ1, env_occ, "Joint_Master_AeroBridgeG16_to_Desk"),
        (occ2, env_occ, "Joint_Master_StealthVaultULT_to_LeftEdge"),
        (occ3, env_occ, "Joint_Master_HydroSling_to_RightFrontEdge"),
        (occ4, env_occ, "Joint_Master_HexWingSpire_to_RightRearEdge"),
        (occ5, occ1, "Joint_Master_HoloBuddy_to_AeroBridge_RightWing"),
    ]:
        jin = ab.createInput(prod_occ, anchor_occ, None)
        jin.setAsRigidJointMotion()
        j = ab.add(jin)
        j.name = jname

    apply_stealth_rog_appearances(app, design)
    configure_hero_camera(app)

    if AUTO_EXPORT_MESHES:
        export_printable_meshes(design)


def run(context):
    app = adsk.core.Application.get()
    ui = app.userInterface if app else None
    try:
        app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = adsk.fusion.Design.cast(app.activeProduct)
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        if hasattr(design, "fusionUnitsManager"):
            design.fusionUnitsManager.distanceDisplayUnits = adsk.fusion.DistanceUnits.MillimeterDistanceUnits

        app.executeTextCommand('PTransaction.Start "Build Master Full Desk Setup"')
        try:
            build_full_setup(app, design)
            app.executeTextCommand("PTransaction.Commit")
        except Exception:
            app.executeTextCommand("PTransaction.Abort")
            raise

        app.log(
            "[Master_FullDeskSetup] Complete 630x280mm 4-product modular setup generated.",
            adsk.core.LogLevels.InfoLogLevel,
            adsk.core.LogTypes.ConsoleLogType,
        )
    except Exception:
        err = traceback.format_exc()
        if app:
            app.log(err, adsk.core.LogLevels.ErrorLogLevel, adsk.core.LogTypes.ConsoleLogType)
        if ui:
            ui.messageBox(f"Master_FullDeskSetup failed:\n{err}")
