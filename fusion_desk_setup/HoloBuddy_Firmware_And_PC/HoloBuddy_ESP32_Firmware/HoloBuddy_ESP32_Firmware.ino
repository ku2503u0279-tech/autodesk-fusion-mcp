/*
 * ============================================================================
 * HoloBuddy ESP32 Firmware — Beam-Splitter OLED Hologram Desk Companion
 * ============================================================================
 * Target Hardware (fits inside Product5_HoloBuddy Fusion CAD enclosure):
 *   - MCU:     ESP32-C3 SuperMini (USB-C) [also works on ESP32-S3 / DevKit V1]
 *   - Display: 0.96" 128x64 I2C SSD1306 Monochrome OLED (4-pin: VCC,GND,SCL,SDA)
 *   - Optics:  25.4 x 25.4 x 25.4 mm 50:50 K9 Beam-Splitting Prism Cube
 *   - Touch:   TTP223 Capacitive Touch Pad inside 1.2 mm top helmet pocket
 *   - Audio:   INMP441 Omnidirectional I2S MEMS Microphone behind front grille
 *
 * Libraries Required (install via Arduino Library Manager):
 *   1. "Adafruit SSD1306" by Adafruit
 *   2. "Adafruit GFX Library" by Adafruit
 *
 * Optical Reflection Math:
 *   The OLED sits face-up (+Y) beneath a 45-deg diagonal mirror sloping from
 *   (Z_rear, Y_bottom) up-and-forward to (Z_front, Y_top), reflecting rays +Z
 *   toward your eyes. Single-mirror reflection inverts the vertical axis
 *   (row -> 63 - row) while preserving left-to-right X. `presentToHologram()`
 *   automatically mirror-flips every frame before pushing over 800 kHz Fast-I2C!
 * ============================================================================
 */

#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <driver/i2s.h>

#ifdef ESP32
  #include <WiFi.h>
  #include <WiFiUdp.h>
#endif

// ------------------------- USER CONFIGURATION -------------------------------
// Optional Wi-Fi credentials for wireless UDP lyric/video/telemetry streaming
// (USB-C Serial @ 921600 baud ALWAYS works even with Wi-Fi left blank!)
const char* WIFI_SSID     = "";
const char* WIFI_PASSWORD = "";
const uint16_t UDP_PORT   = 4210;

// Optical mirror orientation flags (toggle if you mount OLED rotated 180 deg)
static bool MIRROR_VERTICAL   = true;   // Required for 45-deg beam-splitter!
static bool MIRROR_HORIZONTAL = false;

// Pinout for ESP32-C3 SuperMini (change if using ESP32-WROOM-32 DevKit)
#define PIN_OLED_SDA   8
#define PIN_OLED_SCL   9
#define PIN_TOUCH_PAD  3    // TTP223 I/O pin (active HIGH)
#define PIN_I2S_SCK    4    // INMP441 SCK / BCLK
#define PIN_I2S_WS     5    // INMP441 WS  / LRCK
#define PIN_I2S_SD     6    // INMP441 SD  / DOUT (connect INMP441 L/R to GND)

#define SCREEN_W       128
#define SCREEN_H       64
#define OLED_ADDR      0x3C

// ------------------------- GLOBALS & STATE ----------------------------------
Adafruit_SSD1306 rawDisplay(SCREEN_W, SCREEN_H, &Wire, -1);
GFXcanvas1 canvas(SCREEN_W, SCREEN_H);  // Draw normally here; blitted mirrored!
WiFiUDP udp;

enum BuddyMode : uint8_t {
  MODE_BUDDY = 0,          // Autonomous animated Mecha Pet + Audio Bounce
  MODE_LYRIC_STREAM = 1,   // USB-C / UDP 128x64 Video & Synced Lyric Streamer
  MODE_SPECTRUM = 2,       // Standalone 16-Band INMP441 Holographic Visualizer
  MODE_ROG_HUD = 3         // ROG Strix G16 Telemetry HUD + 25m Study Pomodoro
};

static BuddyMode currentMode = MODE_BUDDY;
static bool i2sReady = false;

// Touch ("Head-Pat") tracking
static bool touchPrev = false;
static uint32_t touchDownMs = 0;
static bool patReactionTriggered = false;
static uint32_t happyUntilMs = 0;

// Audio beat & band state
static float audioLevel = 0.0f;
static float bandLevels[16] = {0};
static float bandPeaks[16]  = {0};

// Procedural Buddy Eye state
static float eyeX = 0.0f, eyeY = 0.0f;
static float targetEyeX = 0.0f, targetEyeY = 0.0f;
static uint32_t nextSaccadeMs = 0;
static uint32_t nextBlinkMs = 2000;
static bool isBlinking = false;
static uint32_t blinkStartMs = 0;

// Live Stream & ROG Telemetry state
static uint8_t streamFrame[1024];        // 128 * 64 / 8 bytes
static uint32_t lastStreamFrameMs = 0;
static uint8_t rogCpuPct = 0, rogGpuTemp = 0, rogRamPct = 0;
static char lyricLine1[32] = " HoloBuddy Ready ";
static char lyricLine2[32] = "Stream 'My Way'!";

// Study Pomodoro state (25 minutes)
static int32_t pomoRemainingSec = 25 * 60;
static uint32_t lastPomoTickMs = 0;
static bool pomoRunning = true;

// ------------------------- OPTICAL MIRROR BLITTER ---------------------------
void presentToHologram() {
  rawDisplay.clearDisplay();
  const uint8_t* src = canvas.getBuffer();
  uint8_t* dst = rawDisplay.getBuffer();
  memset(dst, 0, 1024);

  // Fast bitwise remap from GFXcanvas1 (row-major 16 bytes/row) into
  // SSD1306 page-major buffer with vertical/horizontal optical mirror flip!
  for (int y = 0; y < SCREEN_H; y++) {
    int outY = MIRROR_VERTICAL ? (SCREEN_H - 1 - y) : y;
    int dstPage = (outY >> 3) * SCREEN_W;
    uint8_t dstMask = (1 << (outY & 7));
    const uint8_t* srcRow = src + (y * (SCREEN_W >> 3));

    for (int x = 0; x < SCREEN_W; x++) {
      if (srcRow[x >> 3] & (0x80 >> (x & 7))) {
        int outX = MIRROR_HORIZONTAL ? (SCREEN_W - 1 - x) : x;
        dst[dstPage + outX] |= dstMask;
      }
    }
  }
  rawDisplay.display();
}

// ------------------------- I2S MEMS MIC (INMP441) ---------------------------
void setupI2SMic() {
  i2s_config_t cfg = {};
  cfg.mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX);
  cfg.sample_rate = 16000;
  cfg.bits_per_sample = I2S_BITS_PER_SAMPLE_32BIT;
  cfg.channel_format = I2S_CHANNEL_FMT_ONLY_LEFT;
  cfg.communication_format = I2S_COMM_FORMAT_STAND_I2S;
  cfg.intr_alloc_flags = ESP_INTR_FLAG_LEVEL1;
  cfg.dma_buf_count = 4;
  cfg.dma_buf_len = 128;
  cfg.use_apll = false;

  i2s_pin_config_t pins = {};
  pins.bck_io_num = PIN_I2S_SCK;
  pins.ws_io_num = PIN_I2S_WS;
  pins.data_out_num = I2S_PIN_NO_CHANGE;
  pins.data_in_num = PIN_I2S_SD;

  if (i2s_driver_install(I2S_NUM_0, &cfg, 0, NULL) == ESP_OK) {
    if (i2s_set_pin(I2S_NUM_0, &pins) == ESP_OK) {
      i2sReady = true;
    }
  }
}

void sampleAudioBands() {
  if (!i2sReady) return;
  int32_t samples[128];
  size_t bytesRead = 0;
  if (i2s_read(I2S_NUM_0, samples, sizeof(samples), &bytesRead, 0) != ESP_OK || bytesRead == 0) {
    return;
  }
  int count = bytesRead / sizeof(int32_t);
  float sumAbs = 0.0f;

  // Lightweight 16-bucket time/zero-crossing energy analyzer for crisp 60 FPS response
  float bucketAcc[16] = {0};
  for (int i = 0; i < count; i++) {
    float v = (float)(samples[i] >> 14);
    float av = fabsf(v);
    sumAbs += av;
    int b = (i * 16) / count;
    // Weight higher buckets with first-difference high-frequency energy
    if (i > 0 && b >= 8) {
      av = fabsf(v - (float)(samples[i - 1] >> 14)) * 1.4f;
    }
    bucketAcc[b] += av;
  }

  float norm = (sumAbs / (float)count) / 1800.0f;
  if (norm > 1.0f) norm = 1.0f;
  audioLevel = audioLevel * 0.65f + norm * 0.35f;

  for (int b = 0; b < 16; b++) {
    float bv = (bucketAcc[b] / (float)(count / 16)) / 1600.0f;
    if (bv > 1.0f) bv = 1.0f;
    bandLevels[b] = bandLevels[b] * 0.55f + bv * 0.45f;
    if (bandLevels[b] > bandPeaks[b]) {
      bandPeaks[b] = bandLevels[b];
    } else {
      bandPeaks[b] = max(0.0f, bandPeaks[b] - 0.025f);
    }
  }
}

// ------------------------- TOUCH "HEAD-PAT" HANDLER -------------------------
void updateHeadPat() {
  bool touched = (digitalRead(PIN_TOUCH_PAD) == HIGH);
  uint32_t now = millis();

  if (touched && !touchPrev) {
    touchDownMs = now;
    patReactionTriggered = false;
  } else if (touched && touchPrev) {
    // Holding/patting >= 650 ms triggers affectionate pet reaction!
    if (!patReactionTriggered && (now - touchDownMs >= 650)) {
      patReactionTriggered = true;
      happyUntilMs = now + 3800;
      if (currentMode == MODE_ROG_HUD) {
        pomoRunning = !pomoRunning;  // Long-pat pauses/resumes Pomodoro in HUD mode
      }
    }
  } else if (!touched && touchPrev) {
    // Short tap (< 650 ms) cycles to the next holographic mode!
    if (!patReactionTriggered && (now - touchDownMs >= 35)) {
      currentMode = (BuddyMode)(((uint8_t)currentMode + 1) % 4);
    }
  }
  touchPrev = touched;
}

// ------------------------- SERIAL & UDP PACKET PARSER -----------------------
// Packet Protocol (both USB-C Serial @ 921600 and Wi-Fi UDP port 4210):
//   1. Full 128x64 Frame:  "HOLO" (4B) + 1024B row-major 1-bit packed bitmap
//   2.ROG Telemetry + Text:"STAT" (4B) + cpu(1B) + gpuTemp(1B) + ram(1B) + line1(31B) + line2(31B)
void pollIncomingStream() {
  // 1. Check Wi-Fi UDP packets
  if (WiFi.status() == WL_CONNECTED) {
    int pktSize = udp.parsePacket();
    if (pktSize >= 1028) {
      char hdr[4];
      udp.read(hdr, 4);
      if (memcmp(hdr, "HOLO", 4) == 0) {
        udp.read(streamFrame, 1024);
        lastStreamFrameMs = millis();
        currentMode = MODE_LYRIC_STREAM;
      }
    } else if (pktSize >= 7) {
      uint8_t buf[72] = {0};
      int n = udp.read(buf, sizeof(buf) - 1);
      if (n >= 7 && memcmp(buf, "STAT", 4) == 0) {
        rogCpuPct = buf[4];
        rogGpuTemp = buf[5];
        rogRamPct = buf[6];
        if (n >= 38) memcpy(lyricLine1, buf + 7, 31);
        if (n >= 69) memcpy(lyricLine2, buf + 38, 31);
      }
    }
  }

  // 2. Check high-speed USB-C Serial stream
  static uint8_t hdrMatch = 0;
  const char magic[4] = {'H', 'O', 'L', 'O'};
  while (Serial.available() > 0) {
    uint8_t c = (uint8_t)Serial.read();
    if (c == (uint8_t)magic[hdrMatch]) {
      hdrMatch++;
      if (hdrMatch == 4) {
        size_t got = Serial.readBytes(streamFrame, 1024);
        if (got == 1024) {
          lastStreamFrameMs = millis();
          currentMode = MODE_LYRIC_STREAM;
        }
        hdrMatch = 0;
      }
    } else {
      hdrMatch = (c == 'H') ? 1 : 0;
    }
  }
}

// ------------------------- RENDERERS FOR ALL 4 MODES ------------------------
void drawHappyEyeArc(int cx, int cy) {
  for (int t = -2; t <= 2; t++) {
    canvas.drawLine(cx - 14, cy + 4 + t, cx, cy - 8 + t, SSD1306_WHITE);
    canvas.drawLine(cx, cy - 8 + t, cx + 14, cy + 4 + t, SSD1306_WHITE);
  }
}

void renderBuddyMode(uint32_t now) {
  if (now >= nextSaccadeMs) {
    targetEyeX = (float)random(-12, 13);
    targetEyeY = (float)random(-6, 7);
    nextSaccadeMs = now + random(1200, 3400);
  }
  eyeX += (targetEyeX - eyeX) * 0.18f;
  eyeY += (targetEyeY - eyeY) * 0.18f;

  if (!isBlinking && now >= nextBlinkMs) {
    isBlinking = true;
    blinkStartMs = now;
  }
  if (isBlinking && (now - blinkStartMs > 130)) {
    isBlinking = false;
    nextBlinkMs = now + random(2400, 5600);
  }

  int beatBounce = (int)(audioLevel * 6.0f);
  int lx = 38 + (int)eyeX;
  int rx = 90 + (int)eyeX;
  int cy = 28 + (int)eyeY - beatBounce;

  if (now < happyUntilMs) {
    // Happy squinted ^ ^ eyes + floating holographic music notes / heart!
    drawHappyEyeArc(lx, cy);
    drawHappyEyeArc(rx, cy);
    int floatY = 12 - ((now / 90) % 10);
    canvas.setCursor(58, max(0, floatY));
    canvas.setTextSize(1);
    canvas.setTextColor(SSD1306_WHITE);
    canvas.print("<3");
  } else if (isBlinking) {
    canvas.fillRoundRect(lx - 15, cy - 2, 30, 4, 2, SSD1306_WHITE);
    canvas.fillRoundRect(rx - 15, cy - 2, 30, 4, 2, SSD1306_WHITE);
  } else {
    int eyeH = 24 + (int)(audioLevel * 8.0f);
    canvas.fillRoundRect(lx - 14, cy - eyeH / 2, 28, eyeH, 7, SSD1306_WHITE);
    canvas.fillRoundRect(rx - 14, cy - eyeH / 2, 28, eyeH, 7, SSD1306_WHITE);
    // Specular cyber-glint cutout inside eyes
    canvas.fillCircle(lx - 5, cy - 4, 3, SSD1306_BLACK);
    canvas.fillCircle(rx - 5, cy - 4, 3, SSD1306_BLACK);
  }

  // Subtle audio-reactive mouth waveform along chin
  for (int i = 0; i < 12; i++) {
    int h = 1 + (int)(bandLevels[i + 2] * 10.0f);
    canvas.fillRect(40 + i * 4, 56 - h / 2, 2, h, SSD1306_WHITE);
  }
}

void renderLyricStreamMode(uint32_t now) {
  if (now - lastStreamFrameMs < 2500) {
    memcpy(canvas.getBuffer(), streamFrame, 1024);
    return;
  }
  // Offline holographic lyric card demo ("My Way" tribute stage)
  canvas.drawRoundRect(2, 2, 124, 60, 5, SSD1306_WHITE);
  canvas.setTextColor(SSD1306_WHITE);
  canvas.setTextSize(1);
  canvas.setCursor(14, 10);
  canvas.print("HOLO LYRIC STAGE");
  canvas.drawFastHLine(10, 21, 108, SSD1306_WHITE);
  canvas.setCursor(10, 28);
  canvas.print(lyricLine1);
  canvas.setCursor(10, 40);
  canvas.print(lyricLine2);

  // Beat-reactive bottom progress/equalizer dots
  for (int b = 0; b < 16; b++) {
    int w = (bandLevels[b] > 0.15f) ? 5 : 2;
    canvas.fillRect(8 + b * 7, 54, w, 3, SSD1306_WHITE);
  }
}

void renderSpectrumMode() {
  canvas.setTextColor(SSD1306_WHITE);
  canvas.setTextSize(1);
  canvas.setCursor(22, 0);
  canvas.print("LIVE HOLO AUDIO");

  for (int b = 0; b < 16; b++) {
    int barH = (int)(bandLevels[b] * 48.0f);
    int peakY = 62 - (int)(bandPeaks[b] * 48.0f);
    int x = 4 + b * 7 + (b / 4);
    if (barH > 0) {
      canvas.fillRect(x, 62 - barH, 5, barH, SSD1306_WHITE);
    }
    canvas.drawFastHLine(x, max(12, peakY), 5, SSD1306_WHITE);
  }
}

void renderRogHudMode(uint32_t now) {
  if (pomoRunning && (now - lastPomoTickMs >= 1000)) {
    lastPomoTickMs = now;
    if (pomoRemainingSec > 0) pomoRemainingSec--;
  }

  canvas.setTextColor(SSD1306_WHITE);
  canvas.setTextSize(1);
  canvas.setCursor(6, 2);
  canvas.print("ROG G16 HUD | FOCUS");
  canvas.drawFastHLine(0, 12, 128, SSD1306_WHITE);

  char buf[32];
  snprintf(buf, sizeof(buf), "CPU:%2u%% GPU:%2uC", rogCpuPct, rogGpuTemp);
  canvas.setCursor(6, 17);
  canvas.print(buf);

  // CPU & GPU Holographic Bars
  canvas.drawRect(6, 28, 54, 6, SSD1306_WHITE);
  canvas.fillRect(6, 28, (min((int)rogCpuPct, 100) * 54) / 100, 6, SSD1306_WHITE);
  canvas.drawRect(68, 28, 54, 6, SSD1306_WHITE);
  canvas.fillRect(68, 28, (min((int)rogGpuTemp, 100) * 54) / 100, 6, SSD1306_WHITE);

  // Large Floating Pomodoro Timer at bottom
  int mmLeft = pomoRemainingSec / 60;
  int ssLeft = pomoRemainingSec % 60;
  snprintf(buf, sizeof(buf), "%02d:%02d", mmLeft, ssLeft);
  canvas.setTextSize(2);
  canvas.setCursor(34, 42);
  canvas.print(buf);
}

// ------------------------- ARDUINO ENTRYPOINTS ------------------------------
void setup() {
  Serial.begin(921600);
  pinMode(PIN_TOUCH_PAD, INPUT);

  Wire.begin(PIN_OLED_SDA, PIN_OLED_SCL);
  Wire.setClock(800000);  // 800 kHz Fast-I2C+ for smooth ~60 FPS hologram updates!

  rawDisplay.begin(SSD1306_SWITCHCAPVCC, OLED_ADDR);
  rawDisplay.clearDisplay();
  rawDisplay.display();

  setupI2SMic();

  if (strlen(WIFI_SSID) > 0) {
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    uint32_t t0 = millis();
    while (WiFi.status() != WL_CONNECTED && (millis() - t0 < 4000)) {
      delay(100);
    }
    if (WiFi.status() == WL_CONNECTED) {
      udp.begin(UDP_PORT);
    }
  }
  lastPomoTickMs = millis();
}

void loop() {
  uint32_t now = millis();
  updateHeadPat();
  pollIncomingStream();
  sampleAudioBands();

  canvas.fillScreen(SSD1306_BLACK);  // Pure black OLED = 100% invisible background in prism!

  switch (currentMode) {
    case MODE_BUDDY:        renderBuddyMode(now); break;
    case MODE_LYRIC_STREAM: renderLyricStreamMode(now); break;
    case MODE_SPECTRUM:     renderSpectrumMode(); break;
    case MODE_ROG_HUD:      renderRogHudMode(now); break;
  }

  presentToHologram();
  delay(14);  // ~60 FPS loop target
}
