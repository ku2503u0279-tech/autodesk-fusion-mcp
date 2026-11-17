# Overengineered 630 × 280 mm Modular Desk Setup — Autodesk Fusion Script Suite

All scripts in this directory are **standalone Autodesk Fusion Python Script bundles** (`<ScriptName>/<ScriptName>.py` + `<ScriptName>.manifest`), architected using the conventions in this repository (`guides/fusion-design-guide.md`, `AutodeskFusionMCP.manifest`, `fusion_bridge/viewport.py`, `lib/fusionAddInUtils/general_utils.py`).

## Included Script Bundles

| Folder | Role | Printable Parts | Max Part Envelope |
|---|---|---|---|
| `Product0_FitCheckGauge/` | **Print First (~14 g, 22 min):** 6-in-1 tolerance coupon testing the `21 mm` desk+mat jaw, `DT-30` dovetail, `608` bearing bore, `6×3 mm` magnet pocket, `M3`/`M4` heat-set bores, and `USB-A` dongle slot | 2 (`P0A`, `P0B`) | `58.0 × 45.4 × 38.0 mm` |
| `Product1_AeroBridgeG16/` | Cantilevered open-truss ROG Strix G16 riser (`16°/18°/22°` pinned tilt) + `332 × 62 mm` AULA F75 garage + left `DT-30` `MagPivot S24+` MagSafe wing (`RevoluteJoint`) | 8 (`P1A`–`P1H`) | `190.6 × 179.8 × 63.2 mm` |
| `Product2_StealthVaultULT/` | Left-edge padded dual C-clamp + **shrouded hidden 280W ROG brick enclosure** + rear-left cable spine + `608`-bearing swing-under Sony ULT WEAR saddle (`RevoluteJoint`) | 5 (`P2A`–`P2E`) | `196.0 × 133.7 × 60.2 mm` |
| `Product3_HydroSling/` | Front-right padded C-clamp + outboard `65–84 mm` compliant bottle cage + under-desk `DT-30` sliding open-C A5/A4 notebook tray (`SliderJoint`) | 2 (`P3A`–`P3B`) | `185.0 × 184.0 × 34.2 mm` |
| `Product4_HexWingSpire/` | Rear-right padded C-clamp + outboard `DT-30` 6-pen & 2.4G dongle caddy + magnetic micro-drawer (`SliderJoint`) + `608`-bearing `Chimera Spire` mouse bungee (`RevoluteJoint`) | 4 (`P4A`–`P4D`) | `120.0 × 90.0 × 78.0 mm` |
| `Product5_HoloBuddy/` | **Stealth Mecha Hologram Companion:** `25.4 mm` `50:50` K9 prism + `45°` light-trap + magnetic glare visor + `0.96"` OLED + `ESP32-C3 SuperMini` + `TTP223` head-pat touch + `INMP441` mic + `608`-bearing right `DT-30` wing & freestanding dock | 5 (`P5A`–`P5E`) | `65.8 × 58.0 × 34.0 mm` |
| `Master_FullDeskSetup/` | Builds the `630 × 280 × 18 mm` dark walnut desk + `3 mm` mat + reference device models + **all 5 products** with `AsBuiltJoints` + Stealth ROG Render appearances + optional batch `.3mf`/`.stl` exporter | All 24 (`Body_P1*`..`Body_P5*`) | `≤ 196.0 mm` (fits `200³ mm` college FDM beds) |
| `HoloBuddy_Firmware_And_PC/` | Complete Arduino/ESP32-C3 C++ firmware (`HoloBuddy_ESP32_Firmware.ino`), Python PC lyric-video/telemetry streamer (`pc_holo_streamer.py`), and `WIRING_AND_OPTICS_GUIDE.md` | — | — |

## Quick Install & Run in Autodesk Fusion

1. Copy the desired script subfolder(s) (or copy the entire `fusion_desk_setup` folder and pick any subfolder inside it) into your Fusion `Scripts` directory (or link directly from anywhere):
   - **Windows:** `%APPDATA%\Autodesk\Autodesk Fusion 360\API\Scripts\`
   - **macOS:** `~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/Scripts/`
2. In Autodesk Fusion, press **`Shift + S`** (**Utilities → Scripts and Add-Ins**), stay on the **Scripts** tab, click the green **`+`** next to **My Scripts**, select e.g. `fusion_desk_setup/Product1_AeroBridgeG16` (or `Master_FullDeskSetup`), and click **Run**.
3. To tweak any dimension live, open **Modify → Change Parameters** (`Solid` tab) and edit any User Parameter (such as `fit_clearance`, `table_thickness`, `mat_thickness`, `laptop_tilt_deg`, or `bottle_max_dia`).

## Local Verification (Outside Fusion)

```bash
python3 fusion_desk_setup/verify_fusion_scripts.py
```
