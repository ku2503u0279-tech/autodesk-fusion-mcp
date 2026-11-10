# Overengineered 630 × 280 mm Modular Desk System — Full Engineering Manual

![Orthographic CAD Layout Blueprint](./DESK_LAYOUT_BLUEPRINT.svg)

All dimensions throughout this manual and all 6 Autodesk Fusion scripts are in **millimeters (`mm`)** (angles in `deg`).

---

## 1. Concept Plan & Spatial Architecture (`630 × 280 × (18+3) mm` Desk)

Your tabletop (`630 × 280 × 18 mm` dark wood, pushed flush against the back wall at `Z = 0 mm`) is covered edge-to-edge by your `630 × 280 × 3 mm` desk mat (`21.0 mm` total edge thickness). Because your **ASUS ROG Strix G16 (`264 mm` deep)** + **AULA F75 (`143.2 mm` deep)** = `407.2 mm > 280 mm`, all 4 products work together via a shared **`DT-30` (`30 mm`, `60°`) dovetail standard** and **padded zero-screw side-edge C-clamps**:

1. **Product 1 — `AeroBridge G16` + `MagPivot S24+` Wing (`Product1_AeroBridgeG16/`):**
   - Cantilevered open-truss laptop riser (`X = 88..448 mm`, `Z = 12..202 mm`) elevating the `2.5 kg` ROG Strix G16 at **`18°`** (`16° / 18° / 22°` M4 pin-selectable) with 78% open intake lattice and `12 mm` rear exhaust/hinge wall clearance.
   - Provides a **`332 mm` wide × `62 mm` tall front garage** so your **AULA F75 (`323 × 143.2 × 43.1 mm`)** operates directly underneath the front overhang (`18.9 mm` vertical finger gap) while leaving a **100% clear `175 × 280 mm` right-side mouse pad** (`X = 448..623 mm`) for your **Kreo Chimera V2**.
   - Left `DT-30` socket holds the **`MagPivot S24+` Wing**, floating your **Samsung Galaxy S24+ (MagSafe case)** beside the G16 display on a `90°` `Revolute` rotor with an embedded `8× 6×3 mm` N52 (`Ø54 mm` PCD) MagSafe magnet ring.
2. **Product 2 — `StealthVault 280 + SideDock ULT` (`Product2_StealthVaultULT/`):**
   - Left-edge (`X = 0 mm`) dual padded C-clamp (`2 mm` EVA/TPU pads + `M4` brass heat-set thumbscrews).
   - **`StealthVault 280` (`Z = 14..210 mm`, `196 mm` long):** Completely **hides your `180 × 82 × 26 mm` 280W ROG power brick** and coiled cords behind a faceted sightline door (`4× N52` magnets) with hidden bottom convective vents + an enclosed rear-left vertical cable spine up to the G16's left DC port. Leaves **`330+ mm` of central knee clearance**.
   - **`SideDock ULT` (`Z = 212..262 mm`):** Press-fit **`608` ball bearing** + N52 magnet detents supporting a `38 mm` wide contoured saddle for your **Sony ULT WEAR (`255 g`)** that swings `90°` outboard left or tucks under the desk.
3. **Product 3 — `HydroSling Outrigger` (`Product3_HydroSling/`):**
   - Front-right (`X = 630 mm`, `Z = 142..266 mm`) beveled low-profile C-clamp holding your water bottle (`65–84 mm` via 3 compliant PETG centering ribs) **100% outside the tabletop (`X = 640..735 mm`)** + an under-desk `DT-30` sliding open-left C-tray (`185 × 184 × 34 mm`) fitting **both A5 and A4 notebooks**.
4. **Product 4 — `HexWing Outrigger + Chimera Spire` (`Product4_HexWingSpire/`):**
   - Rear-right (`X = 630 mm`, `Z = 10..130 mm`) beveled C-clamp carrying an outboard quick-detach `DT-30` caddy (`X = 640..718 mm` — **0% mat loss**) with **6 hex pen silos**, **2× USB-A 2.4G dongle slots** (AULA F75 + Chimera V2 receivers), **2× USB-C slots**, a pull-out **magnetic micro-drawer**, and a top **`608`-bearing `Chimera Spire` mouse bungee & magnetic USB-C cable park**.

---

## 2. Master Parametric Variables (`Solid → Modify → Change Parameters`)

| Parameter | Default | Unit | Role |
|---|---|---|---|
| `table_length` / `table_depth` | `630.0 mm` / `280.0 mm` | `mm` | Desk & mat footprint |
| `table_thickness` / `mat_thickness` | `18.0 mm` / `3.0 mm` | `mm` | Clamped edge stack (`21.0 mm` total) |
| `clamp_pad_t` | `2.0 mm` | `mm` | Soft protective pad allowance per clamp jaw |
| `fit_clearance` | `0.25 mm` | `mm` | Sliding `DT-30` dovetail, lap-joint & drawer clearance |
| `riser_x_left` / `riser_inner_span` | `88.0 mm` / `332.0 mm` | `mm` | Keyboard garage span (`> 323 mm` AULA F75) |
| `riser_blade_t` | `14.0 mm` | `mm` | Truss side-blade thickness |
| `riser_z_rear` / `riser_base_depth` | `12.0 mm` / `184.0 mm` | `mm` | Wall gap & `< 200 mm` bed-safe base depth |
| `garage_clear_h` | `62.0 mm` | `mm` | Clear bridge height (`> 43.1 mm` AULA F75) |
| `laptop_tilt_deg` | `18.0 deg` | `deg` | Active G16 tilt (`16 / 18 / 22 deg` pin holes) |
| `magsafe_ring_pcd` | `54.0 mm` | `mm` | `8× N52` MagSafe pitch circle diameter |
| `brick_length` / `width` / `thick` | `180 / 82 / 26 mm` | `mm` | ROG 280W brick envelope |
| `vault_length` | `196.0 mm` | `mm` | `StealthVault 280` outer length (`< 200 mm` bed) |
| `ult_band_w` | `38.0 mm` | `mm` | Contoured Sony ULT WEAR saddle width |
| `bottle_max_dia` / `bottle_cage_h` | `86.0 mm` / `96.0 mm` | `mm` | Compliant `65–84 mm` bottle cage |
| `notebook_slot_h` / `tray_w` / `tray_d`| `24 / 178 / 184 mm` | `mm` | Under-desk A5/A4 sliding sling (`< 200 mm` bed) |
| `dt30_width` / `dt30_depth` | `30.0 mm` / `6.0 mm` | `mm` | Shared `60°` self-supporting dovetail |
| `bearing_od` / `id` / `w` / `bore_clear`| `22 / 8 / 7 / 0.15 mm` | `mm` | `608-2RS` bearing press-fit geometry |
| `magnet_dia` / `h` / `magnet_clear` | `6.0 / 3.0 / 0.15 mm` | `mm` | N52 magnet press-fit pockets |
| `m3_insert_od` / `m4_insert_od` | `4.0 mm` / `5.6 mm` | `mm` | Brass heat-set insert pilot holes |

---

## 3. Bill of Materials (Zero RGB — Under ₹1,200 / $16 Hardware)

1. **`608-2RS` Ball Bearings (`8 × 22 × 7 mm`):** `2 pcs` (`P2D` ULT pivot, `P4A` Chimera Spire) — ~₹140
2. **`6 × 3 mm` N52 Neodymium Disc Magnets:** `22 pcs` (pack of 30: `8×` MagSafe ring, `4×` 90° phone detents, `4×` brick shroud door, `3×` ULT arm detents/cable park, `3×` HexWing drawer/USB-C park) — ~₹280
3. **`M4 × L 6 mm × OD 6.0 mm` Brass Heat-Set Inserts:** `7 pcs` (lower clamp jaws) — ~₹160
4. **`M4 × 25 mm` Knurled Thumbscrews:** `7 pcs` (zero-screw edge clamps) — ~₹180
5. **`M4 × 20 mm` Socket Bolts + Nyloc Nuts + Washers:** `5 sets` (`AeroBridge` deck pivots/angle pins + `MagPivot` friction axle) — ~₹90
6. **`M3 × L 5 mm` Brass Heat-Set Inserts + `M3 × 12 mm` Bolts:** `8 sets` (`AeroBridge` center deck & spreader splices) — ~₹160
7. **`2 mm` Adhesive EVA Foam / Neoprene Sheet (`200 × 200 mm`):** `1 sheet` (non-marring clamp pads, laptop lip & base feet) — ~₹120
8. **Medium Cyanoacrylate Superglue:** `1 tube` — ~₹50
9. **Filament (College 3D Lab, `0.4 mm` Nozzle):** `~920 g` Black/Gunmetal **PETG** + `~160 g` Red/Black **PLA or PETG** (all 21 parts verified `≤ 196.0 mm` max dimension).

---

## 4. Print Settings, Rendering, Export & Assembly Quick Reference

- **Step 0 — Print `Product0_FitCheckGauge` First (`~14 g`, `22 min`, `0.20 mm` layer height, 4 walls, 25% gyroid, no supports):** Verify your real `21 mm` desk+mat stack with `2 mm` foam pads, `DT-30` sliding fit (`fit_clearance`), `608` bearing press-fit, `6×3 mm` magnet fit, and `M3`/`M4` soldering-iron heat-set bores before printing Products 1–4.
- **Structural Print Settings (`P1A`–`P1G`, `P2A`–`P2D`, `P3A`–`P3B`, `P4A`):** **PETG**, `0.20 mm` layer height, **4–5 wall loops**, **5 top/bottom shells**, **30–40% Gyroid infill**. Every part prints cleanly inside a **`200 × 200 × 200 mm`** build volume.
- **Batch `.3MF` & `.STL` Export:** Set `AUTO_EXPORT_MESHES = True` at the top of `Master_FullDeskSetup/Master_FullDeskSetup.py` and run it in Fusion (`Shift+S`) to export all 19 `Body_P*` solids into `~/Desktop/FusionDeskSetup_Exports/`.
- **2D PDF Drawings:** Right-click any component in Fusion's Browser → **Create Drawing** (`ISO`, `mm`, `A3`) → place Base, Projected & Section views → **Export PDF**.
- **Photoreal Rendering:** Run `Master_FullDeskSetup`, switch from **Design → Render**, open **Scene Settings** (`#11141A` background, `Rim Highlights` HDRI @ `950 lux`, `65 mm` Perspective lens), and run **Local Render (`3840 × 2160`)**.
