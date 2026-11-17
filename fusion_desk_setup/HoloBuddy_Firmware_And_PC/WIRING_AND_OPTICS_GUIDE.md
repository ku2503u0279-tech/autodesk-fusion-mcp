# Product 5 (`HoloBuddy`) — Electronics BOM, Wiring, Optical Cube Orientation & Flash Guide

---

## 1. Exact Electronics & Hardware BOM (~₹1,150 / ~$14 Total in India)

All component pockets in `Product5_HoloBuddy.py` are driven by Fusion User Parameters (`prism_size`, `oled_pcb_w`, `oled_pcb_d`, `mcu_length`, `mcu_width`, `touch_skin_t`), so if your vendor's PCB differs by `0.5–1.0 mm`, update one number in **Modify → Change Parameters**.

| Component | Exact Spec to Order (Robu.in / Amazon.in / QuartzComponents) | Measured Size (`mm`) | Est. Cost (`₹`) |
|---|---|---|---|
| **Beam-Splitter Cube** | `25.4 × 25.4 × 25.4 mm` (`1 inch`) **50:50 Optical K9 Glass Beam-Splitter Prism** *(25.0 mm cube also fits with 0.4 mm black tape shim)* | `25.4 × 25.4 × 25.4` | ₹450 – ₹650 |
| **OLED Display** | `0.96"` **I2C 128×64 `SSD1306` 4-Pin Monochrome OLED** (White or Ice-Cyan; pins: `GND, VCC, SCL, SDA` or `VCC, GND, SCL, SDA` — check silkscreen!) | PCB `27.3 × 27.8 × 4.1` · Active `21.7 × 10.9` | ₹160 – ₹220 |
| **Microcontroller** | **`ESP32-C3 SuperMini`** (onboard USB-C, Wi-Fi + BLE) | `22.5 × 18.0 × 3.8` | ₹240 – ₹290 |
| **Touch "Head-Pat" Sensor**| **`TTP223` Capacitive Touch Switch Module** (red PCB, `VCC, I/O, GND`) | `15.0 × 11.5 × 2.0` | ₹20 – ₹35 |
| **Room Beat-Sync Mic** | **`INMP441` Omnidirectional I2S MEMS Microphone Module** | `Ø14.0 × 3.0` | ₹140 – ₹180 |
| **Mechanical Hardware** | `1× 608-2RS` bearing *(uses spare from 4-pack already in main BOM!)*, `2× 6×3 mm` N52 magnets *(for glare visor)*, `4× M3` brass inserts + `M3×8` bolts, 30 AWG silicone hookup wire | — | ₹0 *(from main BOM packs)* |

---

## 2. Pin-by-Pin Wiring Table (`ESP32-C3 SuperMini`)

Use thin `28–30 AWG` flexible silicone wire (`60–80 mm` leads) so everything tucks effortlessly into `P5B_Electronics_Base_Tray`:

| Module & Pin | Connect To (`ESP32-C3 SuperMini`) | Notes |
|---|---|---|
| **0.96" SSD1306 OLED `VCC`** | `3V3` | *(Check OLED silkscreen: some modules put `GND` first, others put `VCC` first!)* |
| **0.96" SSD1306 OLED `GND`** | `GND` | Common ground bus |
| **0.96" SSD1306 OLED `SDA`** | **`GPIO 8`** | Hardware Fast-I2C (`800 kHz`) |
| **0.96" SSD1306 OLED `SCL`** | **`GPIO 9`** | Hardware Fast-I2C (`800 kHz`) |
| **TTP223 Touch `VCC` / `GND`**| `3V3` / `GND` | Leave `A` and `B` solder jumpers open (active-HIGH momentary mode) |
| **TTP223 Touch `I/O`** | **`GPIO 3`** | Glue/tape flat against ceiling of `P5A` pocket (`1.2 mm` top skin) |
| **INMP441 Mic `VDD` / `GND`** | `3V3` / `GND` | **Never** connect `INMP441` to `5V` (`3.3V` max!) |
| **INMP441 Mic `L/R`** | `GND` | Selects Left I2S channel |
| **INMP441 Mic `SCK`** | **`GPIO 4`** | I2S Bit Clock (`BCLK`) |
| **INMP441 Mic `WS`** | **`GPIO 5`** | I2S Word Select (`LRCK`) |
| **INMP441 Mic `SD`** | **`GPIO 6`** | I2S Serial Data Out (`DOUT`) |

---

## 3. Critical Optical Cube Orientation (Read Before Closing the Helmet!)

A `50:50` beam-splitter cube is made of two `45°` right-angle glass prisms cemented along a semi-reflective diagonal plane. You can see this faint diagonal line when looking at the **left/right side faces** of the cube.

**Insert the cube from the bottom of `P5A_HoloBuddy_Head_Shell` oriented like this (Side View):**

```text
                  [ TTP223 Touch Pad in 1.2 mm Top Skin ]
             +-----------------------------------------------+
             |   Rear 45° Matte    |        / |              |--- [ P5C Magnetic
    REAR     |   Black Light-Trap  |      /   |   FRONT      |      Glare Visor ]
   (-Z)      |   (Absorbs Stray    |    / 45° |   WINDOW  =====>  Rays reflect +Z
             |    Room Light!)     |  / Mirror|   (+Z)       |    straight to YOUR EYES!
             |                     |/_________|              |
             +-------------------------[  ^  ]---------------+
                                       [  |  ]  22.4 x 12.0 mm Knife-Edge Optical Mask
                                   [ 0.96" OLED ]  (Face-UP in P5B Tray)
```

- **Rule of Thumb:** Looking into the **front window**, you should see the reflection of the bottom OLED screen! If you see the ceiling instead of the OLED, rotate the glass cube `90°` or `180°` before bolting `P5B` underneath.
- **Handling Tip:** Hold the glass cube by its corners using a microfiber cloth so fingerprints never touch the front, bottom, or rear optical faces, and paint/print the interior of `P5A` in **Matte Black** filament!

---

## 4. Flashing ESP32 & Streaming *"My Way"* Lyric Videos

1. Install **Arduino IDE 2.x**, add ESP32 board support (`esp32 by Espressif Systems`), and select:
   - **Board:** `ESP32C3 Dev Module`
   - **USB CDC On Boot:** **`Enabled`** *(Important on ESP32-C3 SuperMini so USB-C Serial works!)*
2. In **Tools → Manage Libraries**, install **`Adafruit SSD1306`** and **`Adafruit GFX Library`**.
3. Open `HoloBuddy_ESP32_Firmware/HoloBuddy_ESP32_Firmware.ino`, optionally enter your `WIFI_SSID` / `WIFI_PASSWORD` for wireless UDP streaming, and click **Upload**.
4. **Controls on Your Desk:**
   - **Quick Pat (< 0.6 s) on `HoloBuddy`'s helmet:** Cycles `Cyber Pet Buddy` → `Holo Lyric/Video Stage` → `16-Band Live Audio Visualizer` → `ROG G16 HUD & 25:00 Pomodoro`.
   - **Long Head-Pat (hold > 0.65 s):** Triggers happy `^ ^` eyes + floating holographic `<3` reaction (or pauses/resumes your Pomodoro timer in HUD mode!).
5. **Stream Any Lyric Video (e.g., *"My Way"*) or Live ROG Strix G16 Stats:**
   ```bash
   pip install pillow opencv-python pyserial psutil
   # Stream an MP4 lyric video over USB-C:
   python pc_holo_streamer.py --video my_way_lyrics.mp4 --serial COM5
   # Or stream live ROG Strix G16 CPU% + NVIDIA GPU Temp over Wi-Fi:
   python pc_holo_streamer.py --telemetry --udp 192.168.1.50
   ```
